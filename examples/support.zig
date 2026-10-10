const std = @import("std");
const linux = std.os.linux;

pub fn output(io: std.Io, bytes: []const u8) !void {
    var buffer: [4096]u8 = undefined;
    var writer = std.Io.File.stdout().writer(io, &buffer);
    try writer.interface.writeAll(bytes);
    try writer.interface.flush();
}

pub fn completedBytes(cqe: linux.io_uring_cqe) !usize {
    if (cqe.res < 0) return error.IoCompletionFailed;
    return @intCast(cqe.res);
}

pub fn sameFile(a: linux.fd_t, b: linux.fd_t) !bool {
    var first: linux.Statx = undefined;
    var second: linux.Statx = undefined;
    if (linux.errno(linux.statx(a, "", linux.AT.EMPTY_PATH, .{ .INO = true }, &first)) != .SUCCESS)
        return error.FileIdentityQueryFailed;
    if (linux.errno(linux.statx(b, "", linux.AT.EMPTY_PATH, .{ .INO = true }, &second)) != .SUCCESS)
        return error.FileIdentityQueryFailed;
    if (!first.mask.INO or !second.mask.INO) return error.FileIdentityUnavailable;
    return first.ino == second.ino and first.dev_major == second.dev_major and first.dev_minor == second.dev_minor;
}
