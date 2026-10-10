const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedOutputPath;
    const file = try std.Io.Dir.cwd().createFile(init.io, args[1], .{ .read = true });
    defer file.close(init.io);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    const first = "What is this life if, full of care,\n";
    const second = "We have no time to stand and stare.";
    var buffers: [4][512]u8 = undefined;
    var registered: [4]std.posix.iovec = undefined;
    for (&buffers, 0..) |*buffer, i| {
        @memset(buffer, 0);
        registered[i] = .{ .base = buffer, .len = buffer.len };
    }
    try ring.register_buffers(&registered);
    @memcpy(buffers[0][0..first.len], first);
    @memcpy(buffers[1][0..second.len], second);
    var requests = registered;
    requests[0].len = first.len;
    requests[1].len = second.len;
    requests[2].len = first.len;
    requests[3].len = second.len;
    _ = try ring.write_fixed(1, file.handle, &requests[0], 0, 0);
    _ = try ring.write_fixed(2, file.handle, &requests[1], first.len, 1);
    _ = try ring.submit();
    try checkCompletions(&ring, 1, first.len, second.len);
    _ = try ring.read_fixed(3, file.handle, &requests[2], 0, 2);
    _ = try ring.read_fixed(4, file.handle, &requests[3], first.len, 3);
    _ = try ring.submit();
    try checkCompletions(&ring, 3, first.len, second.len);
    try ring.unregister_buffers();
    try support.output(init.io, buffers[2][0..first.len]);
    try support.output(init.io, buffers[3][0..second.len]);
}

fn checkCompletions(ring: *linux.IoUring, start_id: u64, first: usize, second: usize) !void {
    var seen = [_]bool{ false, false };
    for (0..2) |_| {
        const cqe = try ring.copy_cqe();
        if (cqe.user_data < start_id or cqe.user_data >= start_id + 2) return error.UnexpectedCompletion;
        const id: usize = @intCast(cqe.user_data - start_id);
        if (seen[id]) return error.DuplicateCompletion;
        seen[id] = true;
        const expected = if (id == 0) first else second;
        if (try support.completedBytes(cqe) != expected) return error.FixedBufferOperationIncomplete;
    }
}
