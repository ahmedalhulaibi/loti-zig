const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len < 2) return error.ExpectedInputFiles;
    for (args[1..]) |path| {
        const file = try std.Io.Dir.cwd().openFile(init.io, path, .{});
        defer file.close(init.io);
        var blocks: [2][2048]u8 = undefined;
        const vecs = [_]std.posix.iovec{
            .{ .base = &blocks[0], .len = blocks[0].len },
            .{ .base = &blocks[1], .len = blocks[1].len },
        };
        while (true) {
            const result = linux.readv(file.handle, &vecs, vecs.len);
            switch (linux.errno(result)) {
                .SUCCESS => {},
                .INTR => continue,
                else => return error.FileReadFailed,
            }
            if (result == 0) break;
            const first = @min(result, blocks[0].len);
            try support.output(init.io, blocks[0][0..first]);
            if (result > first) try support.output(init.io, blocks[1][0 .. result - first]);
        }
    }
}
