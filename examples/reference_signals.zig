const std = @import("std");
const builtin = @import("builtin");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

var deliveries: u32 = 0;
var handler_failed: bool = false;
var handler_masks: [2]linux.sigset_t = @splat(linux.sigemptyset());

fn handler(signal: linux.SIG) callconv(.c) void {
    const index = @atomicRmw(u32, &deliveries, .Add, 1, .seq_cst);
    if (signal != .USR1 or index >= handler_masks.len) {
        @atomicStore(bool, &handler_failed, true, .seq_cst);
        return;
    }
    if (linux.errno(linux.sigprocmask(0, null, &handler_masks[index])) != .SUCCESS)
        @atomicStore(bool, &handler_failed, true, .seq_cst);
}

fn mask(signals: []const linux.SIG) linux.sigset_t {
    var result = linux.sigemptyset();
    for (signals) |signal| linux.sigaddset(&result, signal);
    return result;
}

fn maskValue(set: linux.sigset_t) u128 {
    var value: u128 = 0;
    for (set, 0..) |word, index|
        value |= @as(u128, word) << @intCast(index * @bitSizeOf(@TypeOf(word)));
    return value;
}

fn currentMask() !linux.sigset_t {
    var result = linux.sigemptyset();
    if (linux.errno(linux.sigprocmask(0, null, &result)) != .SUCCESS)
        return error.SignalMaskQueryFailed;
    return result;
}

fn pending() !bool {
    var set = linux.sigemptyset();
    if (linux.errno(linux.syscall2(.rt_sigpending, @intFromPtr(&set), linux.NSIG / 8)) != .SUCCESS)
        return error.SignalPendingQueryFailed;
    return linux.sigismember(&set, .USR1);
}

fn changeMask(how: u32, set: *const linux.sigset_t) !void {
    if (linux.errno(linux.sigprocmask(how, set, null)) != .SUCCESS)
        return error.SignalMaskChangeFailed;
}

fn kernelAction(set: ?*const linux.k_sigaction, old: ?*linux.k_sigaction) !void {
    const status = switch (builtin.cpu.arch) {
        .sparc, .sparc64 => linux.syscall5(.rt_sigaction, @backingInt(linux.SIG.USR1), @intFromPtr(set), @intFromPtr(old), if (set) |action| @intFromPtr(action.restorer) else 0, linux.NSIG / 8),
        else => linux.syscall4(.rt_sigaction, @backingInt(linux.SIG.USR1), @intFromPtr(set), @intFromPtr(old), linux.NSIG / 8),
    };
    if (linux.errno(status) != .SUCCESS) return error.SignalActionChangeFailed;
}

fn send() !void {
    if (linux.errno(linux.tgkill(linux.getpid(), linux.gettid(), .USR1)) != .SUCCESS)
        return error.ThreadSignalSendFailed;
}

const State = struct {
    pending: bool,
    delivered: u32,
    mask: u128,
    sq_ready: u32,
    cq_ready: u32,
};

fn state(ring: *linux.IoUring) !State {
    return .{
        .pending = try pending(),
        .delivered = @atomicLoad(u32, &deliveries, .seq_cst),
        .mask = maskValue(try currentMask()),
        .sq_ready = ring.sq_ready(),
        .cq_ready = ring.cq_ready(),
    };
}

const WaitReport = struct {
    mask: ?u128,
    result: []const u8,
    before: State,
    after: State,
};

fn wait(ring: *linux.IoUring, temporary: ?*const linux.sigset_t, expected: anyerror) !WaitReport {
    const before = try state(ring);
    const timeout: linux.kernel_timespec = .{ .sec = 0, .nsec = 10_000_000 };
    var failure: ?anyerror = null;
    raw.wait_with_timeout(ring, 1, &timeout, temporary) catch |err| {
        failure = err;
    };
    const result = failure orelse return error.WaitUnexpectedlySucceeded;
    if (result != expected) return error.UnexpectedSignalWaitResult;
    return .{
        .mask = if (temporary) |set| maskValue(set.*) else null,
        .result = @errorName(result),
        .before = before,
        .after = try state(ring),
    };
}

const Observations = struct {
    interrupted: WaitReport,
    blocked_timeout: WaitReport,
    null_timeout: WaitReport,
    released: State,
    submitted: u32,
    nop: linux.io_uring_cqe,
};

fn observe(ring: *linux.IoUring) !Observations {
    const usr1 = mask(&.{.USR1});
    const caller = mask(&.{ .USR1, .USR2 });
    try changeMask(linux.SIG.SETMASK, &caller);
    try send();
    const unblocked = mask(&.{ .USR2, .WINCH });
    const interrupted = try wait(ring, &unblocked, error.WaitInterrupted);
    _ = try ring.nop(1);
    try send();
    const blocked = mask(&.{ .USR1, .WINCH });
    const timed_out = try wait(ring, &blocked, error.WaitTimedOut);
    const null_mask = try wait(ring, null, error.WaitTimedOut);
    try changeMask(linux.SIG.UNBLOCK, &usr1);
    const released = try state(ring);
    try changeMask(linux.SIG.SETMASK, &caller);
    const submitted = try ring.submit_and_wait(1);
    const completion = try ring.copy_cqe();
    if (completion.user_data != 1 or completion.res != 0 or completion.flags != 0)
        return error.SignalRecoveryNopFailed;
    if (@atomicLoad(u32, &deliveries, .seq_cst) != 2 or @atomicLoad(bool, &handler_failed, .seq_cst))
        return error.SignalHandlerObservationFailed;
    return .{
        .interrupted = interrupted,
        .blocked_timeout = timed_out,
        .null_timeout = null_mask,
        .released = released,
        .submitted = submitted,
        .nop = completion,
    };
}

fn restore(action: *const linux.k_sigaction, original: *const linux.sigset_t) !void {
    // Restore the exact kernel action; the SDK installer adds a restorer flag.
    try kernelAction(action, null);
    try changeMask(linux.SIG.SETMASK, original);
}

const Completion = struct { user_data: u64, result: i32, flags: u32 };
const OrdinaryWait = struct {
    mask: ?u128,
    minimum: u32,
    errno: u16,
    submitted: u32,
    before: State,
    after: State,
};
const OrdinaryObservations = struct {
    interrupted: OrdinaryWait,
    cancellation: [2]Completion,
    blocked_wait: OrdinaryWait,
    null_wait: OrdinaryWait,
    timers: [2]Completion,
    released: State,
    submitted: u32,
    nop: Completion,
};
const Reports = union(enum) { deadline: Observations, ordinary: OrdinaryObservations };

fn ordinaryWait(ring: *linux.IoUring, temporary: ?*linux.sigset_t, minimum: u32, expected: linux.E) !OrdinaryWait {
    const before = try state(ring);
    // Basic sigset pointer + NSIG/8, not an EXT_ARG getevents structure.
    // Already-submitted timer SQEs bound these waits. No submission or CQ consumption here.
    const result = linux.io_uring_enter(ring.fd, 0, minimum, linux.IORING_ENTER_GETEVENTS, temporary);
    const errno = linux.errno(result);
    if (errno != expected) return error.UnexpectedOrdinaryEnterResult;
    return .{
        .mask = if (temporary) |set| maskValue(set.*) else null,
        .minimum = minimum,
        .errno = @backingInt(errno),
        .submitted = if (errno == .SUCCESS) @intCast(result) else 0,
        .before = before,
        .after = try state(ring),
    };
}

fn pair(ring: *linux.IoUring, first: Completion, second: Completion) ![2]Completion {
    var cqes: [2]linux.io_uring_cqe = undefined;
    if (try ring.copy_cqes(&cqes, 0) != 2) return error.MissingSignalTimerCompletions;
    // Correlate by tag, not arrival order; cancellation has two distinct CQEs.
    if (cqes[0].user_data > cqes[1].user_data) std.mem.swap(linux.io_uring_cqe, &cqes[0], &cqes[1]);
    const result: [2]Completion = .{
        .{ .user_data = cqes[0].user_data, .result = cqes[0].res, .flags = cqes[0].flags },
        .{ .user_data = cqes[1].user_data, .result = cqes[1].res, .flags = cqes[1].flags },
    };
    if (!std.meta.eql(result, [2]Completion{ first, second })) return error.UnexpectedSignalTimerCompletions;
    return result;
}

fn ordinaryObserve(ring: *linux.IoUring) !OrdinaryObservations {
    const usr1 = mask(&.{.USR1});
    const caller = mask(&.{ .USR1, .USR2 });
    try changeMask(linux.SIG.SETMASK, &caller);
    const guard: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
    _ = try ring.timeout(10, &guard, 0, 0);
    if (try ring.submit() != 1) return error.SignalTimerSubmissionFailed;
    try send();
    var unblocked = mask(&.{ .USR2, .WINCH });
    const interrupted = try ordinaryWait(ring, &unblocked, 1, .INTR);
    _ = try ring.timeout_remove(11, 10, 0);
    if (try ring.submit_and_wait(2) != 1) return error.SignalTimerRemovalSubmissionFailed;
    const cancellation = try pair(ring, .{ .user_data = 10, .result = -125, .flags = 0 }, .{ .user_data = 11, .result = 0, .flags = 0 });

    const deadlines: [2]linux.kernel_timespec = .{ .{ .sec = 0, .nsec = 20_000_000 }, .{ .sec = 1, .nsec = 0 } };
    _ = try ring.timeout(20, &deadlines[0], 0, 0);
    _ = try ring.timeout(21, &deadlines[1], 0, 0);
    if (try ring.submit() != 2) return error.SignalTimerSubmissionFailed;
    _ = try ring.nop(1);
    try send();
    var blocked = mask(&.{ .USR1, .WINCH });
    const blocked_wait = try ordinaryWait(ring, &blocked, 1, .SUCCESS);
    // Leave the first CQE unconsumed: min_complete=2 waits for the other timer.
    const null_wait = try ordinaryWait(ring, null, 2, .SUCCESS);
    const timers = try pair(ring, .{ .user_data = 20, .result = -62, .flags = 0 }, .{ .user_data = 21, .result = -62, .flags = 0 });
    if (ring.sq_ready() != 1) return error.SignalWaitSubmittedQueuedNop;
    try changeMask(linux.SIG.UNBLOCK, &usr1);
    const released = try state(ring);
    try changeMask(linux.SIG.SETMASK, &caller);
    const submitted = try ring.submit_and_wait(1);
    const nop = try ring.copy_cqe();
    if (submitted != 1 or nop.user_data != 1 or nop.res != 0 or nop.flags != 0) return error.SignalRecoveryNopFailed;
    if (@atomicLoad(u32, &deliveries, .seq_cst) != 2 or @atomicLoad(bool, &handler_failed, .seq_cst)) return error.SignalHandlerObservationFailed;
    return .{
        .interrupted = interrupted,
        .cancellation = cancellation,
        .blocked_wait = blocked_wait,
        .null_wait = null_wait,
        .timers = timers,
        .released = released,
        .submitted = submitted,
        .nop = .{ .user_data = nop.user_data, .result = nop.res, .flags = nop.flags },
    };
}

fn observeMode(ring: *linux.IoUring, ordinary: bool) !Reports {
    if (ordinary) return .{ .ordinary = try ordinaryObserve(ring) };
    return .{ .deadline = try observe(ring) };
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    const ordinary = args.len == 2 and std.mem.eql(u8, args[1], "--ordinary");
    if (args.len != 1 and !ordinary) return error.ExpectedNoSignalArguments;
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    const original_mask = try currentMask();
    if (try pending()) return error.PreexistingUserSignal;
    var original_action = std.mem.zeroes(linux.k_sigaction);
    try kernelAction(null, &original_action);
    const action: linux.Sigaction = .{
        .handler = .{ .handler = &handler },
        .mask = linux.sigemptyset(),
        .flags = 0,
    };
    if (linux.errno(linux.sigaction(.USR1, &action, null)) != .SUCCESS)
        return error.SignalHandlerInstallFailed;
    const observations = observeMode(&ring, ordinary) catch |err| {
        const usr1 = mask(&.{.USR1});
        try changeMask(linux.SIG.UNBLOCK, &usr1);
        try restore(&original_action, &original_mask);
        return err;
    };
    try restore(&original_action, &original_mask);
    var final_action = std.mem.zeroes(linux.k_sigaction);
    try kernelAction(null, &final_action);
    const action_restored = std.meta.eql(original_action, final_action);
    const mask_restored = std.mem.eql(u8, std.mem.asBytes(&original_mask), std.mem.asBytes(&try currentMask()));
    if (!action_restored or !mask_restored) return error.SignalProcessStateNotRestored;
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    switch (observations) {
        .deadline => |value| try std.json.Stringify.value(.{
            .mask_bytes = linux.NSIG / 8,
            .initial_mask = maskValue(original_mask),
            .interrupted = value.interrupted,
            .blocked_timeout = value.blocked_timeout,
            .null_timeout = value.null_timeout,
            .handler_masks = .{ maskValue(handler_masks[0]), maskValue(handler_masks[1]) },
            .released = value.released,
            .submitted = value.submitted,
            .nop = .{ .user_data = value.nop.user_data, .result = value.nop.res, .flags = value.nop.flags },
            .sq_ready = ring.sq_ready(),
            .cq_ready = ring.cq_ready(),
            .original_action_restored = action_restored,
            .original_mask_restored = mask_restored,
        }, .{}, &stdout.interface),
        .ordinary => |value| try std.json.Stringify.value(.{
            .mask_bytes = linux.NSIG / 8,
            .initial_mask = maskValue(original_mask),
            .interrupted = value.interrupted,
            .cancellation = value.cancellation,
            .blocked_wait = value.blocked_wait,
            .null_wait = value.null_wait,
            .timers = value.timers,
            .handler_masks = .{ maskValue(handler_masks[0]), maskValue(handler_masks[1]) },
            .released = value.released,
            .submitted = value.submitted,
            .nop = value.nop,
            .sq_ready = ring.sq_ready(),
            .cq_ready = ring.cq_ready(),
            .original_action_restored = action_restored,
            .original_mask_restored = mask_restored,
        }, .{}, &stdout.interface),
    }
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
