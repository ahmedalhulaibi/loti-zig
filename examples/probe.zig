const std = @import("std");
const linux = std.os.linux;

const probe_size = 16 + 256 * 8;

comptime {
    if (@sizeOf(linux.io_uring_probe) != probe_size) @compileError("Unexpected probe ABI size");
}

fn rawProbe() ![probe_size]u8 {
    var params = std.mem.zeroes(linux.io_uring_params);
    const setup = linux.io_uring_setup(8, &params);
    if (linux.errno(setup) != .SUCCESS) return error.RawProbeRingSetupFailed;
    const fd: linux.fd_t = @intCast(setup);
    defer _ = linux.close(fd);
    var bytes: [probe_size]u8 = @splat(0);
    const status = linux.io_uring_register(fd, .REGISTER_PROBE, &bytes, 256);
    if (linux.errno(status) != .SUCCESS) return error.RawProbeRegistrationFailed;
    return bytes;
}

fn snapshot(init: std.process.Init, path: []const u8) !linux.io_uring_probe {
    const file = try std.Io.Dir.cwd().openFile(init.io, path, .{});
    defer file.close(init.io);
    const metadata = try file.stat(init.io);
    if (metadata.kind != .file) return error.ExpectedRegularProbeSnapshot;
    if (metadata.size != probe_size) return error.InvalidProbeSnapshotSize;
    var probe: linux.io_uring_probe = undefined;
    if (try file.readPositionalAll(init.io, std.mem.asBytes(&probe), 0) != probe_size)
        return error.ProbeSnapshotTruncated;
    return probe;
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    if (args.len == 2 and std.mem.eql(u8, args[1], "--raw")) {
        const bytes = try rawProbe();
        try stdout.interface.writeAll(&bytes);
        try stdout.interface.flush();
        return;
    }
    const probe = if (args.len == 1) blk: {
        var ring = try linux.IoUring.init(8, 0);
        defer ring.deinit();
        break :blk try ring.get_probe();
    } else if (args.len == 3 and std.mem.eql(u8, args[1], "--snapshot"))
        try snapshot(init, args[2])
    else
        return error.ExpectedProbeArguments;
    inline for (@typeInfo(linux.IORING_OP).@"enum".field_names) |name| {
        const op = @field(linux.IORING_OP, name);
        try stdout.interface.print("{{\"opcode\":{d},\"name\":\"{s}\",\"supported\":{s}}}\n", .{
            @backingInt(op), name, if (probe.is_supported(op)) "true" else "false",
        });
    }
    try stdout.interface.flush();
}
