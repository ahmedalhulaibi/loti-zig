const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");
const current = std.math.maxInt(u64);

const Command = enum { arm, write, wait, cancel, drain, missing, quiet };
const defaults = [_]Command{ .arm, .write, .wait, .write, .quiet, .arm, .wait, .drain, .arm, .cancel, .missing, .quiet };
const Plan = struct {
    commands: []const Command,

    fn init(allocator: std.mem.Allocator, args: []const []const u8) !Plan {
        if (args.len > 64) return error.PollPlanTooLong;
        const commands = if (args.len == 0) &defaults else blk: {
            const parsed = try allocator.alloc(Command, args.len);
            for (args, parsed) |arg, *command| command.* = std.meta.stringToEnum(Command, arg) orelse return error.UnknownPollCommand;
            break :blk parsed;
        };
        var armed = false;
        var queued: usize = 0;
        for (commands) |command| switch (command) {
            .arm => {
                if (armed) return error.PollAlreadyArmed;
                armed = true;
            },
            .write => queued += 1,
            .wait => {
                if (!armed or queued == 0) return error.PollWaitNeedsArmedReadyInput;
                armed = false;
            },
            .cancel => {
                if (!armed or queued != 0) return error.PollCancelNeedsArmedEmptyInput;
                armed = false;
            },
            .drain => {
                if (armed or queued == 0) return error.PollDrainNeedsUnarmedData;
                queued = 0;
            },
            .missing => if (armed) return error.PollRemoveMissingNeedsNoPoll,
            .quiet => if (armed) return error.PollQuietNeedsNoPoll,
        };
        if (armed) return error.PollPlanLeavesOutstandingPoll;
        return .{ .commands = commands };
    }
};

const Request = struct { operation: linux.IORING_OP, tag: u64, mask: ?u32, target: ?u64, length: u32, offset: u64, flags: u8 };
const Completion = struct { tag: u64, result: i32, flags: u32 };
const Step = struct { command: Command, tag: u64, poll_before: ?u64, poll_after: ?u64, queued_before: usize, queued_after: usize, request: ?Request = null, cqes: []const Completion = &.{}, data: []const u8 = &.{}, empty_timeout: bool = false };
const Read = struct { request: ?Request = null, cqes: []const Completion = &.{}, data: []const u8 = &.{} };

fn request(sqe: *const linux.io_uring_sqe) !Request {
    if (sqe.opcode != .POLL_ADD and sqe.opcode != .POLL_REMOVE and sqe.opcode != .READ) return error.UnexpectedPollOperation;
    return .{ .operation = sqe.opcode, .tag = sqe.user_data, .mask = if (sqe.opcode == .POLL_ADD) std.mem.littleToNative(u32, sqe.rw_flags) else null, .target = if (sqe.opcode == .POLL_REMOVE) sqe.addr else null, .length = sqe.len, .offset = sqe.off, .flags = sqe.flags };
}

fn submit(ring: *linux.IoUring) !void {
    if (try ring.submit() != 1) return error.UnexpectedPollSubmissionCount;
}

fn empty(ring: *linux.IoUring) !bool {
    const timeout: linux.kernel_timespec = .{ .sec = 0, .nsec = 1000000 };
    raw.wait_with_timeout(ring, 1, &timeout, null) catch |err| {
        if (err != error.WaitTimedOut) return err;
        if (ring.cq_ready() != 0) return error.UnexpectedPollReadiness;
        return true;
    };
    return error.UnexpectedPollReadiness;
}

fn take(allocator: std.mem.Allocator, ring: *linux.IoUring, count: usize) ![]Completion {
    const out = try allocator.alloc(Completion, count);
    const timeout: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
    for (out) |*item| {
        try raw.wait_with_timeout(ring, 1, &timeout, null);
        if (ring.cq_ready() == 0) return error.MissingPollCompletion;
        const cqe = try ring.copy_cqe();
        item.* = .{ .tag = cqe.user_data, .result = cqe.res, .flags = cqe.flags };
    }
    // Cancellation posts two CQEs; their arrival order is not the wire order.
    std.mem.sort(Completion, out, {}, struct {
        fn less(_: void, left: Completion, right: Completion) bool {
            return left.tag < right.tag;
        }
    }.less);
    return out;
}

fn expect(observed: Completion, tag: u64, result: i32) !void {
    if (observed.tag != tag or observed.result != result or observed.flags != 0) return error.UnexpectedPollCompletion;
}

fn read(allocator: std.mem.Allocator, ring: *linux.IoUring, fd: linux.fd_t, tag: u64, count: usize) !Read {
    var memory: [64]u8 = undefined;
    const prepared = try request(try ring.read(tag, fd, .{ .buffer = memory[0..count] }, current));
    try submit(ring);
    const cqes = try take(allocator, ring, 1);
    try expect(cqes[0], tag, @intCast(count));
    return .{ .request = prepared, .cqes = cqes, .data = try allocator.dupe(u8, memory[0..count]) };
}

fn close(fd: linux.fd_t, owned: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.PollPipeCloseFailed;
    owned.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.PollPipeDescriptorStillOpen;
    return true;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    const plan = try Plan.init(allocator, args[1..]);
    var pipe: [2]linux.fd_t = undefined;
    if (linux.errno(linux.pipe2(&pipe, .{ .NONBLOCK = true, .CLOEXEC = true })) != .SUCCESS) return error.PollPipeCreationFailed;
    var owned = [_]bool{ true, true };
    defer {
        for (pipe, owned) |fd, live| {
            if (live) _ = linux.close(fd);
        }
    }
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var pending: ?u64 = null;
    var queued: usize = 0;
    var steps: std.ArrayList(Step) = .empty;
    for (plan.commands, 0..) |command, index| {
        const tag: u64 = index + 1;
        var step: Step = .{ .command = command, .tag = tag, .poll_before = pending, .poll_after = pending, .queued_before = queued, .queued_after = queued };
        switch (command) {
            .arm => {
                step.request = try request(try ring.poll_add(tag, pipe[0], linux.POLL.IN));
                try submit(&ring);
                pending = tag;
                if (queued == 0) step.empty_timeout = try empty(&ring);
            },
            .write => {
                const byte = [_]u8{@intCast(index)};
                const result = linux.write(pipe[1], &byte, byte.len);
                if (linux.errno(result) != .SUCCESS or result != byte.len) return error.PollStimulusWriteFailed;
                queued += result;
                step.data = try allocator.dupe(u8, &byte);
            },
            .wait => {
                step.cqes = try take(allocator, &ring, 1);
                try expect(step.cqes[0], pending.?, linux.POLL.IN);
                pending = null;
            },
            .cancel => {
                const target = pending.?;
                step.request = try request(try ring.poll_remove(tag, target));
                try submit(&ring);
                step.cqes = try take(allocator, &ring, 2);
                try expect(step.cqes[0], target, -@as(i32, @backingInt(linux.E.CANCELED)));
                try expect(step.cqes[1], tag, 0);
                pending = null;
            },
            .drain => {
                const observed = try read(allocator, &ring, pipe[0], tag, queued);
                step.request = observed.request;
                step.cqes = observed.cqes;
                step.data = observed.data;
                queued = 0;
            },
            .missing => {
                step.request = try request(try ring.poll_remove(tag, current));
                try submit(&ring);
                step.cqes = try take(allocator, &ring, 1);
                try expect(step.cqes[0], tag, -@as(i32, @backingInt(linux.E.NOENT)));
            },
            .quiet => step.empty_timeout = try empty(&ring),
        }
        step.poll_after = pending;
        step.queued_after = queued;
        try steps.append(allocator, step);
    }
    const cleanup = if (queued > 0) try read(allocator, &ring, pipe[0], 1000002, queued) else Read{};
    const bad_request = try request(try ring.poll_add(1000000, -1, linux.POLL.IN));
    try submit(&ring);
    const bad = (try take(allocator, &ring, 1))[0];
    try expect(bad, 1000000, -@as(i32, @backingInt(linux.E.BADF)));
    const missing_request = try request(try ring.poll_remove(1000001, current));
    try submit(&ring);
    const missing = (try take(allocator, &ring, 1))[0];
    try expect(missing, 1000001, -@as(i32, @backingInt(linux.E.NOENT)));
    const hup_request = try request(try ring.poll_add(1000003, pipe[0], linux.POLL.IN));
    try submit(&ring);
    const hup_empty = try empty(&ring);
    const write_closed = try close(pipe[1], &owned[1]);
    const hup = (try take(allocator, &ring, 1))[0];
    try expect(hup, 1000003, linux.POLL.HUP);
    var eof_memory = [_]u8{0xa5};
    const eof_request = try request(try ring.read(1000004, pipe[0], .{ .buffer = &eof_memory }, current));
    try submit(&ring);
    const eof = (try take(allocator, &ring, 1))[0];
    try expect(eof, 1000004, 0);
    if (eof_memory[0] != 0xa5) return error.PollEofChangedMemory;
    const read_closed = try close(pipe[0], &owned[0]);
    const final_empty = try empty(&ring);
    var output_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &output_buffer);
    try std.json.Stringify.value(.{
        .steps = steps.items,
        .cleanup = cleanup,
        .invalid_descriptor = .{ .request = bad_request, .cqe = bad },
        .absent_target = .{ .request = missing_request, .cqe = missing },
        .hup = .{ .request = hup_request, .empty_timeout = hup_empty, .cqe = hup, .eof = .{ .request = eof_request, .cqe = eof, .data = eof_memory[0..0] } },
        .pipe_closed = .{ read_closed, write_closed },
        .final_queue_empty = final_empty,
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
