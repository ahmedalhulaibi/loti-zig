//! Private-descriptor mmap error injection. Not a security sandbox.
const std = @import("std");
const builtin = @import("builtin");
const linux = std.os.linux;
const RawRing = @import("raw_cat.zig").RawRing;

const Stage = enum { @"shared-sq", @"shared-sqes", @"separate-sq", @"separate-cq", @"separate-sqes" };
const Instruction = extern struct { code: u16, jt: u8 = 0, jf: u8 = 0, k: u32 };
const Program = extern struct { len: u16, filter: [*]const Instruction };

fn denyMapping(fd: linux.fd_t, offset: u32) !void {
    const bpf = linux.BPF;
    const data = linux.SECCOMP.data;
    const load = bpf.LD | bpf.W | bpf.ABS;
    const equal = bpf.JMP | bpf.JEQ | bpf.K;
    const finish = bpf.RET | bpf.K;
    // Native x86_64 only: check ABI and both words of fd/offset. Deny x32.
    const filter = [_]Instruction{
        .{ .code = load, .k = @offsetOf(data, "arch") },
        .{ .code = equal, .k = 0xc000003e, .jt = 1 },
        .{ .code = finish, .k = linux.SECCOMP.RET.KILL_PROCESS },
        .{ .code = load, .k = @offsetOf(data, "nr") },
        .{ .code = bpf.JMP | bpf.JSET | bpf.K, .k = 0x40000000, .jf = 1 },
        .{ .code = finish, .k = linux.SECCOMP.RET.KILL_PROCESS },
        .{ .code = equal, .k = @backingInt(linux.SYS.mmap), .jf = 9 },
        .{ .code = load, .k = @offsetOf(data, "arg4") + 4 },
        .{ .code = equal, .k = 0, .jf = 7 },
        .{ .code = load, .k = @offsetOf(data, "arg4") },
        .{ .code = equal, .k = @intCast(fd), .jf = 5 },
        .{ .code = load, .k = @offsetOf(data, "arg5") + 4 },
        .{ .code = equal, .k = 0, .jf = 3 },
        .{ .code = load, .k = @offsetOf(data, "arg5") },
        .{ .code = equal, .k = offset, .jf = 1 },
        .{ .code = finish, .k = linux.SECCOMP.RET.ERRNO | @as(u32, @backingInt(linux.E.NOMEM)) },
        .{ .code = finish, .k = linux.SECCOMP.RET.ALLOW },
    };
    const program = Program{ .len = filter.len, .filter = &filter };
    if (linux.errno(linux.prctl(@backingInt(linux.PR.SET_NO_NEW_PRIVS), 1, 0, 0, 0)) != .SUCCESS)
        return error.NoNewPrivilegesFailed;
    if (linux.errno(linux.seccomp(linux.SECCOMP.SET_MODE_FILTER, 0, &program)) != .SUCCESS)
        return error.MappingFilterInstallationFailed;
}

fn mappingCount(init: std.process.Init, identity: linux.Statx) !usize {
    const file = try std.Io.Dir.cwd().openFile(init.io, "/proc/self/maps", .{});
    defer file.close(init.io);
    var buffer: [4096]u8 = undefined;
    var reader = file.readerStreaming(init.io, &buffer);
    const allocator = init.arena.allocator();
    const contents = try reader.interface.allocRemaining(allocator, .limited(1024 * 1024));
    defer allocator.free(contents);
    var lines = std.mem.splitScalar(u8, contents, '\n');
    var count: usize = 0;
    while (lines.next()) |line| {
        if (line.len == 0) continue;
        var fields = std.mem.tokenizeScalar(u8, line, ' ');
        _ = fields.next() orelse return error.InvalidProcMapping;
        _ = fields.next() orelse return error.InvalidProcMapping;
        _ = fields.next() orelse return error.InvalidProcMapping;
        var device = std.mem.splitScalar(u8, fields.next() orelse return error.InvalidProcMapping, ':');
        const major = try std.fmt.parseInt(u32, device.next() orelse return error.InvalidProcMapping, 16);
        const minor = try std.fmt.parseInt(u32, device.next() orelse return error.InvalidProcMapping, 16);
        if (device.next() != null) return error.InvalidProcMapping;
        const inode = try std.fmt.parseInt(u64, fields.next() orelse return error.InvalidProcMapping, 10);
        if (major == identity.dev_major and minor == identity.dev_minor and inode == identity.ino) count += 1;
    }
    return count;
}

fn observe(init: std.process.Init, stage: Stage) !void {
    const single = stage == .@"shared-sq" or stage == .@"shared-sqes";
    const offset: u32 = switch (stage) {
        .@"shared-sq", .@"separate-sq" => linux.IORING_OFF_SQ_RING,
        .@"separate-cq" => linux.IORING_OFF_CQ_RING,
        .@"shared-sqes", .@"separate-sqes" => linux.IORING_OFF_SQES,
    };
    var params = std.mem.zeroInit(linux.io_uring_params, .{ .cq_entries = 512, .flags = linux.IORING_SETUP_CQSIZE });
    const opened = linux.io_uring_setup(8, &params);
    if (linux.errno(opened) != .SUCCESS) return error.RingSetupFailed;
    const fd: linux.fd_t = @intCast(opened);
    var owned = true;
    defer {
        if (owned) _ = linux.close(fd);
    }
    if (single and params.features & linux.IORING_FEAT_SINGLE_MMAP == 0) return error.SharedMappingUnavailable;
    if (!single) params.features &= ~@as(u32, linux.IORING_FEAT_SINGLE_MMAP);
    var identity = std.mem.zeroes(linux.Statx);
    if (linux.errno(linux.statx(fd, "", linux.AT.EMPTY_PATH, .{ .INO = true }, &identity)) != .SUCCESS or !identity.mask.INO)
        return error.RingIdentityUnavailable;
    const before = try mappingCount(init, identity);
    if (before != 0) return error.UnexpectedInitialRingMappings;
    try denyMapping(fd, offset);
    const mapping_error: []const u8 = failure: {
        var mapped = RawRing.map(fd, params) catch |err| break :failure @errorName(err);
        mapped.deinit();
        owned = false;
        return error.InjectedMappingFailureMissing;
    };
    if (!std.mem.eql(u8, mapping_error, "OutOfMemory")) return error.UnexpectedInjectedMappingError;
    const after = try mappingCount(init, identity);
    if (after != before) return error.PartialRingMappingNotReleased;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .SUCCESS) return error.CallerDescriptorNotRetained;
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.CallerDescriptorCloseFailed;
    owned = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.CallerDescriptorStillOpen;
    if (linux.prctl(@backingInt(linux.PR.GET_NO_NEW_PRIVS), 0, 0, 0, 0) != 1) return error.NoNewPrivilegesNotSet;
    var buffer: [1024]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try std.json.Stringify.value(.{
        .stage = @tagName(stage),
        .single_mapping = single,
        .failed_offset = offset,
        .mapping_error = mapping_error,
        .before = before,
        .after = after,
        .fd_retained = true,
        .fd_closed = true,
        .no_new_privs = true,
    }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}

pub fn run(init: std.process.Init, name: []const u8) !void {
    const stage = std.meta.stringToEnum(Stage, name) orelse return error.UnknownMappingFailureStage;
    if (comptime builtin.cpu.arch == .x86_64) {
        return observe(init, stage);
    } else return error.MappingFaultInjectionNeedsX86_64;
}
