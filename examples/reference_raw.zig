const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");
const support = @import("support.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedInputFile;
    const path = try init.arena.allocator().dupeSentinel(u8, args[1], 0);
    const memory = try std.heap.page_allocator.alloc(u8, 4096);
    defer std.heap.page_allocator.free(memory);
    @memset(memory, 0xaa);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    const how: raw.OpenHow = .{
        .flags = @as(u32, @bitCast(linux.O{ .ACCMODE = .RDONLY, .CLOEXEC = true })),
        .resolve = raw.resolve_no_symlinks,
    };
    _ = try raw.openat2(&ring, 1, linux.AT.FDCWD, path, &how);
    _ = try ring.submit();
    const opened = try ring.copy_cqe();
    if (opened.user_data != 1 or opened.res < 0) return error.OpenAt2Failed;
    const fd: linux.fd_t = opened.res;
    defer _ = linux.close(fd);
    _ = try raw.fadvise(&ring, 2, fd, 0, 4096, 0);
    _ = try raw.madvise(&ring, 3, memory, linux.MADV.DONTNEED);
    _ = try ring.submit();
    var seen = [_]bool{ false, false };
    for (0..seen.len) |_| {
        const cqe = try ring.copy_cqe();
        if (cqe.user_data < 2 or cqe.user_data > 3 or cqe.res != 0) return error.AdviceFailed;
        const index: usize = @intCast(cqe.user_data - 2);
        if (seen[index]) return error.DuplicateAdviceCompletion;
        seen[index] = true;
    }
    for (memory) |byte| {
        if (byte != 0) return error.MemoryAdviceIneffective;
    }
    var data: [64]u8 = undefined;
    _ = try ring.read(4, fd, .{ .buffer = &data }, 0);
    _ = try ring.submit();
    const read = try ring.copy_cqe();
    if (read.user_data != 4) return error.ReadCompletionInvalid;
    const count = try support.completedBytes(read);
    var output_buffer: [1024]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &output_buffer);
    try stdout.interface.print("{{\"openat2\":true,\"fadvise_result\":0,\"madvise_result\":0,\"memory_zeroed\":true,\"read_result\":{d}}}\n", .{count});
    try stdout.interface.writeAll(data[0..count]);
    try stdout.interface.flush();
}
