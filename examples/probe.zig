const std = @import("std");
const linux = std.os.linux;

pub fn main(init: std.process.Init) !void {
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    const probe = try ring.get_probe();
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &buffer);
    inline for (@typeInfo(linux.IORING_OP).@"enum".field_names) |name| {
        const op = @field(linux.IORING_OP, name);
        try stdout.interface.print("{{\"opcode\":{d},\"name\":\"{s}\",\"supported\":{s}}}\n", .{
            @backingInt(op), name, if (probe.is_supported(op)) "true" else "false",
        });
    }
    try stdout.interface.flush();
}
