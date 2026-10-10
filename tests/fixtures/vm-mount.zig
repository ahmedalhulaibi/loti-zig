const std = @import("std");
const linux = std.os.linux;

pub fn main() !void {
    inline for (.{ .{ "devtmpfs", "/dev" }, .{ "proc", "/proc" }, .{ "sysfs", "/sys" } }) |mount| {
        if (linux.errno(linux.mount(mount[0], mount[1], mount[0], 0, 0)) != .SUCCESS)
            return error.GuestMountFailed;
    }
}
