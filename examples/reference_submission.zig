const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

fn emit(writer: *std.Io.Writer, sqe: *const linux.io_uring_sqe) !void {
    try writer.print("{{\"tag\":{d},\"operation\":\"{s}\",\"length\":{d},\"flags\":{d},\"buffer_index\":{d}}}\n", .{
        sqe.user_data, @tagName(sqe.opcode), sqe.len, sqe.flags, sqe.buf_index,
    });
}

const DeadlineName = enum { expired, ready, failed, orphan };
const DeadlineDescriptor = enum { pipe, invalid, unused };
const DeadlineTime = struct { sec: i64, nsec: i64 };
const DeadlineRequest = struct {
    tag: u64,
    operation: linux.IORING_OP,
    descriptor: DeadlineDescriptor,
    length: u32,
    offset: u64,
    flags: u8,
    rw_flags: u32,
    address_present: bool,
    timeout: ?DeadlineTime,
};
const DeadlineStage = struct {
    name: DeadlineName,
    requests: []const DeadlineRequest,
    completions: []const linux.io_uring_cqe,
    storage: [8]u8,
    sq_ready: u32,
    cq_ready: u32,
};

fn deadlineRequest(sqe: *const linux.io_uring_sqe, pipe: linux.fd_t) !DeadlineRequest {
    const descriptor: DeadlineDescriptor = switch (sqe.opcode) {
        .READ => if (sqe.fd == pipe) .pipe else if (sqe.fd == -1) .invalid else return error.InvalidDeadlineReadDescriptor,
        .LINK_TIMEOUT => if (sqe.fd == -1) .unused else return error.InvalidDeadlineTimerDescriptor,
        else => return error.UnexpectedDeadlineOperation,
    };
    const time: ?DeadlineTime = if (sqe.opcode == .LINK_TIMEOUT) blk: {
        if (sqe.addr == 0) return error.MissingDeadlineTimespec;
        const ts: *const linux.kernel_timespec = @ptrFromInt(sqe.addr);
        break :blk .{ .sec = ts.sec, .nsec = ts.nsec };
    } else null;
    return .{
        .tag = sqe.user_data,
        .operation = sqe.opcode,
        .descriptor = descriptor,
        .length = sqe.len,
        .offset = sqe.off,
        .flags = sqe.flags,
        .rw_flags = sqe.rw_flags,
        .address_present = sqe.addr != 0,
        .timeout = time,
    };
}

fn deadlineCompletions(ring: *linux.IoUring, first_tag: u64, results: []linux.io_uring_cqe) !void {
    const guard: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
    var seen = [_]bool{ false, false };
    for (results) |_| {
        try raw.wait_with_timeout(ring, 1, &guard, null);
        const cqe = try ring.copy_cqe();
        if (cqe.user_data < first_tag or cqe.user_data - first_tag >= results.len)
            return error.UnexpectedDeadlineCompletion;
        const index: usize = @intCast(cqe.user_data - first_tag);
        if (seen[index]) return error.DuplicateDeadlineCompletion;
        if (cqe.flags != 0) return error.UnexpectedDeadlineCompletionFlags;
        seen[index] = true;
        results[index] = cqe;
    }
    if (ring.sq_ready() != 0 or ring.cq_ready() != 0) return error.DeadlineQueueNotDrained;
}

fn deadlineClose(fd: linux.fd_t, open: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.DeadlinePipeCloseFailed;
    open.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.DeadlinePipeStillOpen;
    return true;
}

fn linkedTimeout(io: std.Io) !void {
    var pipes: [2]linux.fd_t = undefined;
    if (linux.errno(linux.pipe2(&pipes, .{ .NONBLOCK = true, .CLOEXEC = true })) != .SUCCESS)
        return error.DeadlinePipeCreationFailed;
    var read_open = true;
    var write_open = true;
    defer if (read_open) {
        _ = linux.close(pipes[0]);
    };
    defer if (write_open) {
        _ = linux.close(pipes[1]);
    };
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var stages: [4]DeadlineStage = undefined;
    var requests: [4][2]DeadlineRequest = undefined;
    var completions: [4][2]linux.io_uring_cqe = undefined;
    const names = [_]DeadlineName{ .expired, .ready, .failed, .orphan };
    for (names, 0..) |name, index| {
        var data: [8]u8 = @splat(165);
        const duration: linux.kernel_timespec = if (name == .expired)
            .{ .sec = 0, .nsec = 20_000_000 }
        else
            .{ .sec = 1, .nsec = 0 };
        const tag: u64 = 10 + index * 10;
        const count: usize = if (name == .orphan) 1 else 2;
        if (name == .ready) {
            const stimulus = [_]u8{90};
            const written = linux.write(pipes[1], &stimulus, stimulus.len);
            if (linux.errno(written) != .SUCCESS or written != stimulus.len)
                return error.DeadlineStimulusFailed;
        }
        if (name != .orphan) {
            const read = try ring.read(tag, if (name == .failed) -1 else pipes[0], .{ .buffer = data[0..1] }, std.math.maxInt(u64));
            read.flags |= linux.IOSQE_IO_LINK;
            requests[index][0] = try deadlineRequest(read, pipes[0]);
        }
        const timer = try ring.link_timeout(if (name == .orphan) tag else tag + 1, &duration, 0);
        requests[index][count - 1] = try deadlineRequest(timer, pipes[0]);
        if (try ring.submit() != count) return error.UnexpectedDeadlineSubmissionCount;
        try deadlineCompletions(&ring, tag, completions[index][0..count]);
        const target_result: i32 = switch (name) {
            .expired => -@as(i32, @backingInt(linux.E.CANCELED)),
            .ready => 1,
            .failed => -@as(i32, @backingInt(linux.E.BADF)),
            .orphan => -@as(i32, @backingInt(linux.E.INVAL)),
        };
        if (completions[index][0].res != target_result) return error.UnexpectedDeadlineTargetResult;
        if (name != .orphan) {
            const timer_result: i32 = if (name == .expired)
                -@as(i32, @backingInt(linux.E.TIME))
            else
                -@as(i32, @backingInt(linux.E.CANCELED));
            if (completions[index][1].res != timer_result) return error.UnexpectedLinkedTimerResult;
        }
        stages[index] = .{
            .name = name,
            .requests = requests[index][0..count],
            .completions = completions[index][0..count],
            .storage = data,
            .sq_ready = ring.sq_ready(),
            .cq_ready = ring.cq_ready(),
        };
    }
    const read_closed = try deadlineClose(pipes[0], &read_open);
    const write_closed = try deadlineClose(pipes[1], &write_open);
    if (linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) != .SUCCESS) return error.DeadlineClosedCallerRing;
    var buffer: [8192]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(io, &buffer);
    try std.json.Stringify.value(.{
        .stages = stages,
        .pipe_closed = [_]bool{ read_closed, write_closed },
        .ring_retained = true,
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedInputFile;
    if (std.mem.eql(u8, args[1], "--linked-timeout")) return linkedTimeout(init.io);
    const path = try init.arena.allocator().dupeSentinel(u8, args[1], 0);
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    var ring = try linux.IoUring.init(128, 0);
    defer ring.deinit();
    var memory: [4096]u8 align(std.heap.page_size_min) = undefined;
    var vecs = [_]std.posix.iovec{.{ .base = &memory, .len = memory.len }};
    const const_vecs = [_]std.posix.iovec_const{.{ .base = &memory, .len = memory.len }};
    var address: linux.sockaddr.in = .{ .port = std.mem.nativeToBig(u16, 8080), .addr = std.mem.nativeToBig(u32, 0x7f000001) };
    var address_len: linux.socklen_t = @sizeOf(linux.sockaddr.in);
    var receive_message = std.mem.zeroes(linux.msghdr);
    receive_message.iov = &vecs;
    receive_message.iovlen = vecs.len;
    var send_message = std.mem.zeroes(linux.msghdr_const);
    send_message.iov = &const_vecs;
    send_message.iovlen = const_vecs.len;
    var event: linux.epoll_event = .{ .events = linux.EPOLL.IN, .data = .{ .u64 = 1 } };
    var stat: linux.Statx = undefined;
    const how: raw.OpenHow = .{ .flags = @as(u32, @bitCast(linux.O{ .ACCMODE = .RDONLY, .CLOEXEC = true })) };
    const duration: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
    const files = [_]linux.fd_t{file.handle};
    var provided: [8192]u8 = undefined;
    var output_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &output_buffer);
    const out = &stdout.interface;

    // This mixed constructor reference must not submit these incompatible requests together.
    const nop = try ring.nop(1);
    nop.user_data = 1;
    nop.flags |= linux.IOSQE_IO_LINK;
    try emit(out, nop);
    try emit(out, try ring.read(2, file.handle, .{ .buffer = &memory }, 0));
    try emit(out, try ring.write(3, file.handle, &memory, 0));
    try emit(out, try ring.read(4, file.handle, .{ .iovecs = &vecs }, 0));
    try emit(out, try ring.writev(5, file.handle, &const_vecs, 0));
    try emit(out, try ring.fsync(6, file.handle, 0));
    try emit(out, try ring.close(7, file.handle));
    try emit(out, try ring.openat(8, linux.AT.FDCWD, path, .{ .ACCMODE = .RDONLY }, 0));
    try emit(out, try raw.openat2(&ring, 9, linux.AT.FDCWD, path, &how));
    try emit(out, try ring.fallocate(10, file.handle, 0, 0, 4096));
    try emit(out, try ring.statx(11, file.handle, "", linux.AT.EMPTY_PATH, .{ .SIZE = true }, &stat));
    try emit(out, try raw.fadvise(&ring, 12, file.handle, 0, memory.len, 0));
    try emit(out, try raw.madvise(&ring, 13, &memory, 0));
    try emit(out, try ring.splice(14, file.handle, 0, file.handle, 0, memory.len));
    try emit(out, try ring.accept(15, file.handle, @ptrCast(&address), &address_len, linux.SOCK.CLOEXEC));
    try emit(out, try ring.connect(16, file.handle, @ptrCast(&address), address_len));
    try emit(out, try ring.recv(17, file.handle, .{ .buffer = &memory }, 0));
    try emit(out, try ring.send(18, file.handle, &memory, linux.MSG.NOSIGNAL));
    try emit(out, try ring.recvmsg(19, file.handle, &receive_message, 0));
    try emit(out, try ring.sendmsg(20, file.handle, &send_message, linux.MSG.NOSIGNAL));
    try emit(out, try ring.epoll_ctl(21, file.handle, file.handle, linux.EPOLL.CTL_ADD, &event));
    try emit(out, try ring.poll_add(22, file.handle, linux.POLL.IN));
    try emit(out, try ring.poll_remove(23, 22));
    try emit(out, try ring.read_fixed(24, file.handle, &vecs[0], 0, 0));
    try emit(out, try ring.write_fixed(25, file.handle, &vecs[0], 0, 0));
    const update = try ring.get_sqe();
    update.prep_files_update(&files, 0);
    update.user_data = 26;
    try emit(out, update);
    try emit(out, try ring.provide_buffers(27, &provided, 4096, 2, 1, 0));
    try emit(out, try ring.remove_buffers(28, 2, 1));
    try emit(out, try ring.timeout(29, &duration, 0, 0));
    try emit(out, try ring.timeout_remove(30, 29, 0));
    const cancel = try ring.cancel(31, 22, 0);
    cancel.flags |= linux.IOSQE_IO_LINK;
    try emit(out, cancel);
    try emit(out, try ring.link_timeout(32, &duration, 0));
    try emit(out, try raw.sync_file_range(&ring, 33, file.handle, 8192, 4096, raw.sync_wait_before | raw.sync_write | raw.sync_wait_after));
    if (ring.sq_ready() != 33) return error.PreparedRequestCountInvalid;
    try stdout.interface.flush();
}
