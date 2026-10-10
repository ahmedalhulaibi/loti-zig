const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len < 2) return error.ExpectedInputFiles;
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    for (args[1..]) |path| {
        const file = try std.Io.Dir.cwd().openFile(init.io, path, .{});
        defer file.close(init.io);
        var blocks: [2][2048]u8 = undefined;
        const vecs = [_]std.posix.iovec{
            .{ .base = &blocks[0], .len = blocks[0].len },
            .{ .base = &blocks[1], .len = blocks[1].len },
        };
        var offset: u64 = 0;
        while (true) {
            _ = try ring.read(1, file.handle, .{ .iovecs = &vecs }, offset);
            _ = try ring.submit();
            const cqe = try ring.copy_cqe();
            if (cqe.user_data != 1) return error.UnexpectedCompletion;
            if (cqe.err() == .INTR or cqe.err() == .AGAIN) continue;
            const count = try support.completedBytes(cqe);
            if (count == 0) break;
            const first = @min(count, blocks[0].len);
            try support.output(init.io, blocks[0][0..first]);
            if (count > first) try support.output(init.io, blocks[1][0 .. count - first]);
            offset += count;
        }
    }
}
