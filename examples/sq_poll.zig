const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedOutputPath;
    const file = try std.Io.Dir.cwd().createFile(init.io, args[1], .{ .read = true });
    defer file.close(init.io);
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
    const first_sqe = try ring.write(1, 0, first, 0);
    first_sqe.flags |= linux.IOSQE_FIXED_FILE;
    _ = try ring.submit();
    const first_cqe = try ring.copy_cqe();
    if (first_cqe.user_data != 1 or try support.completedBytes(first_cqe) != first.len)
        return error.PollingWriteIncomplete;
    try std.Io.sleep(init.io, .fromMilliseconds(50), .awake);
    const second_sqe = try ring.write(2, 0, second, first.len);
    second_sqe.flags |= linux.IOSQE_FIXED_FILE;
    _ = try ring.submit();
    const second_cqe = try ring.copy_cqe();
    if (second_cqe.user_data != 2 or try support.completedBytes(second_cqe) != second.len)
        return error.PollingWriteIncomplete;
    var data: [first.len + second.len]u8 = undefined;
    const read_sqe = try ring.read(3, 0, .{ .buffer = &data }, 0);
    read_sqe.flags |= linux.IOSQE_FIXED_FILE;
    _ = try ring.submit();
    const read_cqe = try ring.copy_cqe();
    if (read_cqe.user_data != 3 or try support.completedBytes(read_cqe) != data.len)
        return error.PollingReadIncomplete;
    try ring.unregister_files();
    try support.output(init.io, &data);
}
