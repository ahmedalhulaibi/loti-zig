const std = @import("std");
const linux = std.os.linux;
const primary: u64 = 0x0102030405060708;
const secondary: u64 = 0xfedcba9876543210;
const current = std.math.maxInt(u64);
const Command = enum { add, modify, delete, write, wait, drain, close };
const defaults = [_]Command{ .wait, .add, .add, .write, .wait, .wait, .modify, .wait, .modify, .wait, .delete, .wait, .delete, .modify, .add, .wait, .drain, .wait, .write, .close, .wait };

const Plan = struct {
    commands: []const Command,

    fn init(allocator: std.mem.Allocator, args: []const []const u8) !Plan {
        if (args.len > 64) return error.EpollPlanTooLong;
        const commands = if (args.len == 0) &defaults else blk: {
            const parsed = try allocator.alloc(Command, args.len);
            for (args, parsed) |arg, *command| command.* = std.meta.stringToEnum(Command, arg) orelse return error.UnknownEpollCommand;
            break :blk parsed;
        };
        var closed = false;
        var queued: usize = 0;
        for (commands) |command| {
            if (command == .close and closed) return error.EpollPipeAlreadyClosed;
            if (closed and command != .wait) return error.EpollCommandNeedsOpenPipe;
            switch (command) {
                .write => queued += 1,
                .drain => {
                    if (queued == 0) return error.EpollDrainNeedsData;
                    queued = 0;
                },
                .close => {
                    closed = true;
                    queued = 0;
                },
                else => {},
            }
        }
        return .{ .commands = commands };
    }
};

// Wire snapshots are distinct from native kernel storage and live ownership.
const Event = struct { mask: u32, token: u64 };
const Snapshot = struct { registered: bool, mask: u32, token: ?u64, queued: usize, closed: bool };
const Completion = struct { tag: u64, result: i32, flags: u32 };
const Role = enum { epoll, pipe, retired, invalid };
const ControlRequest = struct { operation: linux.IORING_OP, tag: u64, epoll_descriptor: Role, target_descriptor: Role, control_operation: u32, flags: u8, event: ?Event };
const Control = struct { request: ControlRequest, cqe: Completion };
const ReadRequest = struct { operation: linux.IORING_OP, tag: u64, length: u32, offset: u64, flags: u8 };
const Read = struct {
    request: ReadRequest,
    cqe: Completion,
    data: []const u8,
};
const Step = struct { command: Command, tag: u64, before: Snapshot, after: Snapshot, control: ?Control = null, read: ?Read = null, write: []const u8 = &.{}, events: ?[]const Event = null };

const Descriptors = struct {
    epoll: linux.fd_t,
    pipe: linux.fd_t,
    retired: linux.fd_t,

    fn role(self: Descriptors, fd: linux.fd_t) !Role {
        if (fd < 0) return .invalid;
        if (fd == self.epoll) return .epoll;
        if (fd == self.pipe) return .pipe;
        if (fd == self.retired) return .retired;
        return error.UnexpectedEpollDescriptor;
    }
};

fn snapshot(watch: ?linux.epoll_event, queued: usize, closed: bool) Snapshot {
    return .{ .registered = watch != null, .mask = if (watch) |event| event.events else 0, .token = if (watch) |event| event.data.u64 else null, .queued = queued, .closed = closed };
}

fn completed(ring: *linux.IoUring, tag: u64) !Completion {
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedEpollSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedEpollCompletion;
    return .{ .tag = cqe.user_data, .result = cqe.res, .flags = cqe.flags };
}

fn control(ring: *linux.IoUring, ids: Descriptors, tag: u64, epfd: linux.fd_t, target: linux.fd_t, operation: u32, event: ?*linux.epoll_event) !Control {
    const sqe = try ring.epoll_ctl(tag, epfd, target, operation, event);
    if (sqe.opcode != .EPOLL_CTL or sqe.addr != @intFromPtr(event)) return error.InvalidEpollControlRequest;
    const encoded_target = std.math.cast(linux.fd_t, sqe.off) orelse return error.InvalidEpollTargetEncoding;
    const prepared: ControlRequest = .{
        .operation = sqe.opcode,
        .tag = sqe.user_data,
        .epoll_descriptor = try ids.role(sqe.fd),
        .target_descriptor = try ids.role(encoded_target),
        .control_operation = sqe.len,
        .flags = sqe.flags,
        .event = if (event) |value| .{ .mask = value.events, .token = value.data.u64 } else null,
    };
    const cqe = try completed(ring, tag);
    if (cqe.result > 0) return error.InvalidEpollControlResult;
    return .{ .request = prepared, .cqe = cqe };
}

fn events(allocator: std.mem.Allocator, epfd: linux.fd_t) ![]const Event {
    var memory: [1]linux.epoll_event = undefined;
    const result = linux.epoll_wait(epfd, &memory, memory.len, 0);
    if (linux.errno(result) != .SUCCESS) return error.EpollReadinessWaitFailed;
    if (result > memory.len) return error.EpollReadinessOutOfBounds;
    const out = try allocator.alloc(Event, result);
    for (out, memory[0..result]) |*item, event| item.* = .{ .mask = event.events, .token = event.data.u64 };
    return out;
}

fn read(allocator: std.mem.Allocator, ring: *linux.IoUring, fd: linux.fd_t, tag: u64, count: usize) !Read {
    var memory: [64]u8 = undefined;
    const sqe = try ring.read(tag, fd, .{ .buffer = memory[0..count] }, current);
    const prepared: ReadRequest = .{ .operation = sqe.opcode, .tag = sqe.user_data, .length = sqe.len, .offset = sqe.off, .flags = sqe.flags };
    const cqe = try completed(ring, tag);
    if (cqe.result != count) return error.EpollPipeReadIncomplete;
    return .{ .request = prepared, .cqe = cqe, .data = try allocator.dupe(u8, memory[0..count]) };
}

fn close(fd: linux.fd_t, owned: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.EpollDescriptorCloseFailed;
    owned.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.EpollDescriptorStillOpen;
    return true;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    const plan = try Plan.init(allocator, args[1..]);
    var pipe: [2]linux.fd_t = undefined;
    if (linux.errno(linux.pipe2(&pipe, .{ .NONBLOCK = true, .CLOEXEC = true })) != .SUCCESS) return error.EpollPipeCreationFailed;
    var pipe_owned = [_]bool{ true, true };
    defer {
        for (pipe, pipe_owned) |fd, owned| {
            if (owned) _ = linux.close(fd);
        }
    }
    const created = linux.epoll_create1(linux.EPOLL.CLOEXEC);
    if (linux.errno(created) != .SUCCESS) return error.EpollCreationFailed;
    const epfd: linux.fd_t = @intCast(created);
    var epoll_owned = true;
    defer {
        if (epoll_owned) _ = linux.close(epfd);
    }
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    // SDK target-FD preparation rejects negative values; retire an owned positive FD instead.
    const duplicate = linux.fcntl(pipe[0], linux.F.DUPFD_CLOEXEC, 0);
    if (linux.errno(duplicate) != .SUCCESS) return error.EpollProbeDescriptorCreationFailed;
    const retired: linux.fd_t = @intCast(duplicate);
    var retired_owned = true;
    defer {
        if (retired_owned) _ = linux.close(retired);
    }
    const retired_closed = try close(retired, &retired_owned);
    const ids: Descriptors = .{ .epoll = epfd, .pipe = pipe[0], .retired = retired };
    var event: linux.epoll_event = .{ .events = linux.EPOLL.IN, .data = .{ .u64 = primary } };
    const failures = [_]Control{
        try control(&ring, ids, 1000000, -1, pipe[0], linux.EPOLL.CTL_ADD, &event),
        try control(&ring, ids, 1000001, epfd, retired, linux.EPOLL.CTL_ADD, &event),
        try control(&ring, ids, 1000002, pipe[0], pipe[0], linux.EPOLL.CTL_ADD, &event),
        try control(&ring, ids, 1000003, epfd, pipe[0], 99, &event),
        try control(&ring, ids, 1000004, epfd, epfd, linux.EPOLL.CTL_ADD, &event),
        try control(&ring, ids, 1000005, epfd, pipe[0], linux.EPOLL.CTL_ADD, null),
    };
    for (failures, [_]i32{ -9, -9, -22, -22, -22, -14 }) |failure, expected| {
        if (failure.cqe.result != expected) return error.UnexpectedEpollFailureResult;
    }
    var watch: ?linux.epoll_event = null;
    var queued: usize = 0;
    var steps: std.ArrayList(Step) = .empty;
    for (plan.commands, 0..) |command, index| {
        const tag: u64 = index + 1;
        const before = snapshot(watch, queued, !pipe_owned[0]);
        var step: Step = .{ .command = command, .tag = tag, .before = before, .after = before };
        switch (command) {
            .add, .modify => {
                event = .{ .events = if (command == .modify and before.mask == linux.EPOLL.IN) linux.EPOLL.OUT else linux.EPOLL.IN, .data = .{ .u64 = if (command == .add) primary else secondary } };
                const result = try control(&ring, ids, tag, epfd, pipe[0], if (command == .add) linux.EPOLL.CTL_ADD else linux.EPOLL.CTL_MOD, &event);
                step.control = result;
                if (result.cqe.result == 0) watch = event;
            },
            .delete => {
                const result = try control(&ring, ids, tag, epfd, pipe[0], linux.EPOLL.CTL_DEL, null);
                step.control = result;
                if (result.cqe.result == 0) watch = null;
            },
            .write => {
                const byte = [_]u8{@intCast(index)};
                const result = linux.write(pipe[1], &byte, byte.len);
                if (linux.errno(result) != .SUCCESS or result != byte.len) return error.EpollPipeWriteFailed;
                queued += result;
                step.write = try allocator.dupe(u8, &byte);
            },
            .wait => step.events = try events(allocator, epfd),
            .drain => {
                step.read = try read(allocator, &ring, pipe[0], tag, queued);
                queued = 0;
            },
            .close => {
                _ = try close(pipe[0], &pipe_owned[0]);
                watch = null;
                queued = 0;
            },
        }
        step.after = snapshot(watch, queued, !pipe_owned[0]);
        try steps.append(allocator, step);
    }
    var cleanup_control: ?Control = null;
    if (watch != null) {
        cleanup_control = try control(&ring, ids, 1000010, epfd, pipe[0], linux.EPOLL.CTL_DEL, null);
        if (cleanup_control.?.cqe.result != 0) return error.EpollCleanupRemovalFailed;
    }
    const cleanup_read = if (queued > 0) try read(allocator, &ring, pipe[0], 1000011, queued) else null;
    const final_events = try events(allocator, epfd);
    if (final_events.len != 0) return error.EpollCleanupReadinessRemains;
    const read_closed = if (pipe_owned[0]) try close(pipe[0], &pipe_owned[0]) else linux.errno(linux.fcntl(pipe[0], linux.F.GETFD, 0)) == .BADF;
    const write_closed = try close(pipe[1], &pipe_owned[1]);
    const epoll_closed = try close(epfd, &epoll_owned);
    var output_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &output_buffer);
    try std.json.Stringify.value(.{
        .failures = failures,
        .steps = steps.items,
        .cleanup = .{ .control = cleanup_control, .read = cleanup_read, .events = final_events, .pipe_closed = .{ read_closed, write_closed }, .epoll_closed = epoll_closed },
        .retired_descriptor_closed = retired_closed,
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
