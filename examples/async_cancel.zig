const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

const target_a: u64 = 0x1234000000000001;
const target_b: u64 = 0x5678000000000001;
const Descriptor = enum { a, b, unused };
const Name = enum { canceled, missing, unknown, invalid_flags, ready, completed };
const Request = struct {
    tag: u64,
    operation: linux.IORING_OP,
    descriptor: Descriptor,
    length: u32,
    offset: u64,
    flags: u8,
    rw_flags: u32,
    target_tag: ?u64,
};
const Stage = struct {
    name: Name,
    requests: []const Request,
    completions: []const linux.io_uring_cqe,
    storage: [2][8]u8,
    sq_ready: u32,
    cq_ready: u32,
};

fn request(sqe: *const linux.io_uring_sqe, pipes: [2][2]linux.fd_t) !Request {
    const descriptor: Descriptor = switch (sqe.opcode) {
        .READ => if (sqe.fd == pipes[0][0]) .a else if (sqe.fd == pipes[1][0]) .b else return error.InvalidCancelReadDescriptor,
        .ASYNC_CANCEL => if (sqe.fd == -1) .unused else return error.InvalidCancelDescriptor,
        else => return error.UnexpectedCancelOperation,
    };
    return .{
        .tag = sqe.user_data,
        .operation = sqe.opcode,
        .descriptor = descriptor,
        .length = sqe.len,
        .offset = sqe.off,
        .flags = sqe.flags,
        .rw_flags = sqe.rw_flags,
        .target_tag = if (sqe.opcode == .ASYNC_CANCEL) sqe.addr else null,
    };
}

fn collect(ring: *linux.IoUring, tags: []const u64, results: []linux.io_uring_cqe) !void {
    const guard: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
    var seen = [_]bool{ false, false };
    for (results) |_| {
        try raw.wait_with_timeout(ring, 1, &guard, null);
        const cqe = try ring.copy_cqe();
        const index = std.mem.indexOfScalar(u64, tags, cqe.user_data) orelse return error.UnexpectedCancelCompletion;
        if (seen[index]) return error.DuplicateCancelCompletion;
        if (cqe.flags != 0) return error.UnexpectedCancelCompletionFlags;
        seen[index] = true;
        results[index] = cqe;
    }
    if (ring.sq_ready() != 0 or ring.cq_ready() != 0) return error.CancelQueueNotDrained;
}

fn close(fd: linux.fd_t, open: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.CancellationPipeCloseFailed;
    open.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.CancellationPipeStillOpen;
    return true;
}

pub fn run(io: std.Io) !void {
    var pipes: [2][2]linux.fd_t = undefined;
    var open: [2][2]bool = @splat(@splat(false));
    defer {
        for (0..2) |i| for (0..2) |j| {
            if (open[i][j]) _ = linux.close(pipes[i][j]);
        };
    }
    for (&pipes, 0..) |*pair, i| {
        if (linux.errno(linux.pipe2(pair, .{ .NONBLOCK = true, .CLOEXEC = true })) != .SUCCESS)
            return error.CancellationPipeCreationFailed;
        open[i] = .{ true, true };
    }
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var storage: [2][8]u8 = @splat(@splat(165));
    const reads = [_]Request{
        try request(try ring.read(target_a, pipes[0][0], .{ .buffer = storage[0][0..1] }, std.math.maxInt(u64)), pipes),
        try request(try ring.read(target_b, pipes[1][0], .{ .buffer = storage[1][0..1] }, std.math.maxInt(u64)), pipes),
    };
    if (try ring.submit() != 2) return error.UnexpectedCancelReadSubmissionCount;
    var stages: [6]Stage = undefined;
    var requests: [6][1]Request = undefined;
    var cqes: [6][2]linux.io_uring_cqe = undefined;
    const names = [_]Name{ .canceled, .missing, .unknown, .invalid_flags, .ready, .completed };
    for (names, 0..) |name, index| {
        const count: usize = if (name == .canceled) 2 else 1;
        const tag: u64 = if (name == .completed) 104 else 100 + index;
        if (name == .ready) {
            const stimulus = [_]u8{90};
            const written = linux.write(pipes[1][1], &stimulus, stimulus.len);
            if (linux.errno(written) != .SUCCESS or written != stimulus.len) return error.CancellationStimulusFailed;
            try collect(&ring, &.{target_b}, cqes[index][0..1]);
        } else {
            const target: u64 = switch (name) {
                .canceled, .missing => target_a,
                .unknown => std.math.maxInt(u64),
                .invalid_flags, .completed => target_b,
                .ready => unreachable,
            };
            const flags: u32 = if (name == .invalid_flags) 0x80000000 else 0;
            requests[index][0] = try request(try ring.cancel(tag, target, flags), pipes);
            if (try ring.submit() != 1) return error.UnexpectedCancelSubmissionCount;
            if (name == .canceled)
                try collect(&ring, &.{ target_a, tag }, cqes[index][0..2])
            else
                try collect(&ring, &.{tag}, cqes[index][0..1]);
        }
        const expected: i32 = switch (name) {
            .canceled => -@as(i32, @backingInt(linux.E.CANCELED)),
            .missing, .unknown, .completed => -@as(i32, @backingInt(linux.E.NOENT)),
            .invalid_flags => -@as(i32, @backingInt(linux.E.INVAL)),
            .ready => 1,
        };
        if (cqes[index][0].res != expected) return error.UnexpectedCancelResult;
        if (name == .canceled and cqes[index][1].res != 0) return error.CancellationRequestFailed;
        stages[index] = .{
            .name = name,
            .requests = requests[index][0..if (name == .ready) @as(usize, 0) else 1],
            .completions = cqes[index][0..count],
            .storage = storage,
            .sq_ready = ring.sq_ready(),
            .cq_ready = ring.cq_ready(),
        };
    }
    var closed: [4]bool = undefined;
    for (0..2) |i| for (0..2) |j| {
        closed[i * 2 + j] = try close(pipes[i][j], &open[i][j]);
    };
    if (linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) != .SUCCESS) return error.CancellationClosedCallerRing;
    var buffer: [8192]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(io, &buffer);
    try std.json.Stringify.value(.{ .reads = reads, .stages = stages, .pipe_closed = closed, .ring_retained = true }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
