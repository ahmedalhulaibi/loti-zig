const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");
const raw = @import("raw_ops.zig");

const State = struct { flags: u32, head: u32, tail: u32, queued: u32, cq_ready: u32 };
const Request = struct { operation: linux.IORING_OP, tag: u64, descriptor: i32, length: u32, offset: u64, flags: u8 };
const Completion = struct { user_data: u64, result: i32, flags: u32 };
const Operation = struct { request: Request, cqe: Completion };

fn state(ring: *linux.IoUring) State {
    return .{ .flags = @atomicLoad(u32, ring.sq.flags, .acquire), .head = @atomicLoad(u32, ring.sq.head, .acquire), .tail = @atomicLoad(u32, ring.sq.tail, .acquire), .queued = ring.sq_ready(), .cq_ready = ring.cq_ready() };
}

fn asleep(ring: *linux.IoUring, io: std.Io) !State {
    for (0..2000) |_| {
        const observed = state(ring);
        if (observed.flags & linux.IORING_SQ_NEED_WAKEUP != 0) {
            if (observed.head != observed.tail or observed.queued != 0 or observed.cq_ready != 0)
                return error.PollingSleepQueueNotEmpty;
            return observed;
        }
        try std.Io.sleep(io, .fromMilliseconds(1), .awake);
    }
    return error.PollingSleepNotObserved;
}

fn request(sqe: *const linux.io_uring_sqe) Request {
    return .{ .operation = sqe.opcode, .tag = sqe.user_data, .descriptor = sqe.fd, .length = sqe.len, .offset = sqe.off, .flags = sqe.flags };
}

fn completed(ring: *linux.IoUring, observe: bool) !linux.io_uring_cqe {
    if (observe) {
        const timeout: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
        try raw.wait_with_timeout(ring, 1, &timeout, null);
        if (ring.cq_ready() != 1) return error.PollingCompletionMissing;
    }
    const cqe = try ring.copy_cqe();
    if (cqe.flags != 0) return error.UnexpectedPollingCompletionFlags;
    return cqe;
}

fn operation(prepared: Request, cqe: linux.io_uring_cqe) Operation {
    return .{ .request = prepared, .cqe = .{ .user_data = cqe.user_data, .result = cqe.res, .flags = cqe.flags } };
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2 and args.len != 3) return error.ExpectedOutputPath;
    const observe = args.len == 3;
    if (observe and !std.mem.eql(u8, args[2], "--observe")) return error.UnknownPollingMode;
    const file = try std.Io.Dir.cwd().createFile(init.io, args[1], .{ .read = true });
    var file_open = true;
    defer if (file_open) file.close(init.io);
    var params = std.mem.zeroInit(linux.io_uring_params, .{
        .flags = linux.IORING_SETUP_SQPOLL,
        .sq_thread_idle = 10,
    });
    var ring = try linux.IoUring.init_params(8, &params);
    defer ring.deinit();
    const files = [_]linux.fd_t{file.handle};
    try ring.register_files(&files);
    const first = "Submission queue polling.\n";
    const second = "After the idle period.\n";
    var before: [3]State = undefined;
    if (observe) before[0] = try asleep(&ring, init.io);
    const first_sqe = try ring.write(1, 0, first, 0);
    first_sqe.flags |= linux.IOSQE_FIXED_FILE;
    const first_request = request(first_sqe);
    _ = try ring.submit();
    const first_cqe = try completed(&ring, observe);
    if (first_cqe.user_data != 1 or try support.completedBytes(first_cqe) != first.len)
        return error.PollingWriteIncomplete;
    if (observe) before[1] = try asleep(&ring, init.io) else try std.Io.sleep(init.io, .fromMilliseconds(50), .awake);
    const second_sqe = try ring.write(2, 0, second, first.len);
    second_sqe.flags |= linux.IOSQE_FIXED_FILE;
    const second_request = request(second_sqe);
    _ = try ring.submit();
    const second_cqe = try completed(&ring, observe);
    if (second_cqe.user_data != 2 or try support.completedBytes(second_cqe) != second.len)
        return error.PollingWriteIncomplete;
    var data: [first.len + second.len]u8 = undefined;
    if (observe) before[2] = try asleep(&ring, init.io);
    const read_sqe = try ring.read(3, 0, .{ .buffer = &data }, 0);
    read_sqe.flags |= linux.IOSQE_FIXED_FILE;
    const read_request = request(read_sqe);
    _ = try ring.submit();
    const read_cqe = try completed(&ring, observe);
    if (read_cqe.user_data != 3 or try support.completedBytes(read_cqe) != data.len)
        return error.PollingReadIncomplete;
    try ring.unregister_files();
    if (observe) {
        const after = state(&ring);
        if (linux.errno(linux.close(file.handle)) != .SUCCESS) return error.PollingFileCloseFailed;
        file_open = false;
        if (linux.errno(linux.fcntl(file.handle, linux.F.GETFD, 0)) != .BADF) return error.PollingFileStillOpen;
        if (linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) != .SUCCESS) return error.PollingCallerRingClosed;
        const hex = std.fmt.bytesToHex(data, .lower);
        var stdout = std.Io.File.stdout().writerStreaming(init.io, &.{});
        try std.json.Stringify.value(.{
            .setup = .{ .flags = params.flags, .idle_ms = params.sq_thread_idle },
            .before = before,
            .operations = [_]Operation{ operation(first_request, first_cqe), operation(second_request, second_cqe), operation(read_request, read_cqe) },
            .after = .{ .head = after.head, .tail = after.tail, .queued = after.queued, .cq_ready = after.cq_ready },
            .data_hex = hex[0..],
            .cleanup = .{ .file_closed = true, .ring_still_open = true },
        }, .{}, &stdout.interface);
        try stdout.interface.writeByte('\n');
        try stdout.interface.flush();
    } else try support.output(init.io, &data);
}
