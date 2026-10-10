const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

fn emit(writer: *std.Io.Writer, sqe: *const linux.io_uring_sqe) !void {
    try writer.print("{{\"tag\":{d},\"operation\":\"{s}\",\"length\":{d},\"flags\":{d},\"buffer_index\":{d}}}\n", .{
        sqe.user_data, @tagName(sqe.opcode), sqe.len, sqe.flags, sqe.buf_index,
    });
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedInputFile;
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
    if (ring.sq_ready() != 32) return error.PreparedRequestCountInvalid;
    try stdout.interface.flush();
}
