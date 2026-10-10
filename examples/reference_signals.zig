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

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 1) return error.ExpectedNoSignalArguments;
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
    const observations = observe(&ring) catch |err| {
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
    try std.json.Stringify.value(.{
        .mask_bytes = linux.NSIG / 8,
        .initial_mask = maskValue(original_mask),
        .interrupted = observations.interrupted,
        .blocked_timeout = observations.blocked_timeout,
        .null_timeout = observations.null_timeout,
        .handler_masks = .{ maskValue(handler_masks[0]), maskValue(handler_masks[1]) },
        .released = observations.released,
        .submitted = observations.submitted,
        .nop = .{ .user_data = observations.nop.user_data, .result = observations.nop.res, .flags = observations.nop.flags },
        .sq_ready = ring.sq_ready(),
        .cq_ready = ring.cq_ready(),
        .original_action_restored = action_restored,
        .original_mask_restored = mask_restored,
    }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
