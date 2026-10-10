const std = @import("std");
const linux = std.os.linux;
const RawRing = @import("raw_cat.zig").RawRing;
const support = @import("support.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedInputFile;
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    var params = std.mem.zeroInit(linux.io_uring_params, .{ .cq_entries = 32, .flags = linux.IORING_SETUP_CQSIZE });
    var ring = try linux.IoUring.init_params(8, &params);
    defer ring.deinit();
    const sq: *linux.IoUring.SubmissionQueue = &ring.sq;
    const cq: *linux.IoUring.CompletionQueue = &ring.cq;
    var raw_params = std.mem.zeroes(linux.io_uring_params);
    const opened = linux.io_uring_setup(8, &raw_params);
    if (linux.errno(opened) != .SUCCESS) return error.RingSetupFailed;
    const fd: linux.fd_t = @intCast(opened);
    var mapped = RawRing.map(fd, raw_params) catch |err| {
        _ = linux.close(fd);
        return err;
    };
    defer mapped.deinit();
    try mapped.dontFork();
    var data: [64]u8 = undefined;
    const vecs = [_]std.posix.iovec{.{ .base = &data, .len = data.len }};
    const cqe = try mapped.readv(file.handle, &vecs, 0);
    const count = try support.completedBytes(cqe);
    var output_buffer: [256]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &output_buffer);
    try stdout.interface.print("{{\"sq_entries\":{d},\"cq_entries\":{d},\"sqe_size\":{d},\"cqe_size\":{d},\"raw_read\":{d},\"dontfork\":true}}\n", .{
        sq.sqes.len, cq.cqes.len, @sizeOf(linux.io_uring_sqe), @sizeOf(linux.io_uring_cqe), count,
    });
    try stdout.interface.flush();
}
