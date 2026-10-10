const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");
const Role = enum { client, probe, ring, invalid };
const Address = struct { family: u16, address: [4]u8, port: u16 };
const Query = struct { address: Address, length: linux.socklen_t };
const Request = struct { operation: linux.IORING_OP, tag: u64, descriptor: Role, length: u32, address_length: u64, address: Address, flags: u8 };
const Completion = struct { tag: u64, result: i32, flags: u32 };
const Operation = struct { request: Request, cqe: Completion };
const Failure = struct { request: Request, cqe: Completion, closed: ?bool = null, peer_error: ?u32 = null };

fn portArgument(args: []const []const u8) !u16 {
    if (args.len != 2) return error.ExpectedConnectPort;
    if (args[1].len == 0) return error.InvalidConnectPort;
    for (args[1]) |byte| {
        if (!std.ascii.isDigit(byte)) return error.InvalidConnectPort;
    }
    const port = std.fmt.parseInt(u16, args[1], 10) catch return error.InvalidConnectPort;
    if (port == 0) return error.InvalidConnectPort;
    return port;
}

fn address(value: linux.sockaddr.in) Address {
    return .{ .family = value.family, .address = std.mem.toBytes(value.addr), .port = std.mem.bigToNative(u16, value.port) };
}

fn socket() !linux.fd_t {
    const result = linux.socket(linux.AF.INET, linux.SOCK.STREAM | linux.SOCK.NONBLOCK | linux.SOCK.CLOEXEC, 0);
    if (linux.errno(result) != .SUCCESS) return error.ConnectSocketCreationFailed;
    return @intCast(result);
}

fn close(fd: linux.fd_t, owned: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.ConnectSocketCloseFailed;
    owned.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.ConnectSocketStillOpen;
    return true;
}

fn query(fd: linux.fd_t, comptime peer: bool) !Query {
    var value: linux.sockaddr.in = std.mem.zeroes(linux.sockaddr.in);
    var length: linux.socklen_t = @sizeOf(linux.sockaddr.in);
    const result = if (peer) linux.getpeername(fd, @ptrCast(&value), &length) else linux.getsockname(fd, @ptrCast(&value), &length);
    if (linux.errno(result) != .SUCCESS) return error.ConnectEndpointQueryFailed;
    if (length != @sizeOf(linux.sockaddr.in) or value.family != linux.AF.INET) return error.InvalidConnectEndpoint;
    return .{ .address = address(value), .length = length };
}

fn connect(ring: *linux.IoUring, fd: linux.fd_t, role: Role, tag: u64, peer: *const linux.sockaddr.in, length: linux.socklen_t) !Operation {
    const sqe = try ring.connect(tag, fd, @ptrCast(peer), length);
    if (sqe.opcode != .CONNECT or sqe.fd != fd or sqe.addr != @intFromPtr(peer)) return error.InvalidConnectRequest;
    const prepared: Request = .{ .operation = sqe.opcode, .tag = sqe.user_data, .descriptor = role, .length = sqe.len, .address_length = sqe.off, .address = address(peer.*), .flags = sqe.flags };
    if (try ring.submit() != 1) return error.UnexpectedConnectSubmissionCount;
    const timeout: linux.kernel_timespec = .{ .sec = 1, .nsec = 0 };
    try raw.wait_with_timeout(ring, 1, &timeout, null);
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedConnectCompletion;
    return .{ .request = prepared, .cqe = .{ .tag = cqe.user_data, .result = cqe.res, .flags = cqe.flags } };
}

fn failure(operation: Operation, expected: i32) !Failure {
    if (operation.cqe.result != expected) return error.UnexpectedConnectFailure;
    return .{ .request = operation.request, .cqe = operation.cqe };
}

fn freshFailure(ring: *linux.IoUring, tag: u64, peer: *const linux.sockaddr.in, length: linux.socklen_t, expected: i32, comptime refused: bool) !Failure {
    const fd = try socket();
    var owned = true;
    defer {
        if (owned) _ = linux.close(fd);
    }
    var out = try failure(try connect(ring, fd, .probe, tag, peer, length), expected);
    if (refused) {
        var memory: linux.sockaddr.in = undefined;
        var size: linux.socklen_t = @sizeOf(linux.sockaddr.in);
        const result = linux.getpeername(fd, @ptrCast(&memory), &size);
        const err = linux.errno(result);
        if (err != .NOTCONN) return error.RefusedSocketHasPeer;
        out.peer_error = @backingInt(err);
    }
    out.closed = try close(fd, &owned);
    return out;
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    const port = try portArgument(args);
    var peer: linux.sockaddr.in = .{ .port = std.mem.nativeToBig(u16, port), .addr = std.mem.nativeToBig(u32, 0x7f000001) };
    const original_peer = peer;
    const client = try socket();
    var client_owned = true;
    defer {
        if (client_owned) _ = linux.close(client);
    }
    const guard = try socket();
    var guard_owned = true;
    defer {
        if (guard_owned) _ = linux.close(guard);
    }
    var guard_address: linux.sockaddr.in = .{ .port = 0, .addr = std.mem.nativeToBig(u32, 0x7f000001) };
    if (linux.errno(linux.bind(guard, @ptrCast(&guard_address), @sizeOf(linux.sockaddr.in))) != .SUCCESS) return error.ConnectRefusalGuardBindFailed;
    var guard_length: linux.socklen_t = @sizeOf(linux.sockaddr.in);
    if (linux.errno(linux.getsockname(guard, @ptrCast(&guard_address), &guard_length)) != .SUCCESS) return error.ConnectRefusalAddressQueryFailed;
    if (guard_length != @sizeOf(linux.sockaddr.in) or guard_address.family != linux.AF.INET or guard_address.port == 0) return error.InvalidRefusalEndpoint;
    // The guard stays bound, but never listens. No unrelated process can acquire its port.
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var wrong_family = peer;
    wrong_family.family = linux.AF.UNIX;
    const invalid_fd = try failure(try connect(&ring, -1, .invalid, 1000000, &peer, @sizeOf(linux.sockaddr.in)), -9);
    const nonsocket = try failure(try connect(&ring, ring.fd, .ring, 1000001, &peer, @sizeOf(linux.sockaddr.in)), -88);
    // Failed socket state is unspecified: each negative socket request gets a new owned FD.
    const short = try freshFailure(&ring, 1000002, &peer, 1, -22, false);
    const wrong = try freshFailure(&ring, 1000003, &wrong_family, @sizeOf(linux.sockaddr.in), -97, false);
    const refused = try freshFailure(&ring, 1000004, &guard_address, @sizeOf(linux.sockaddr.in), -111, true);
    const connection = try connect(&ring, client, .client, 1, &peer, @sizeOf(linux.sockaddr.in));
    if (connection.cqe.result != 0) return error.RequestedPeerConnectionFailed;
    const local_query = try query(client, false);
    const peer_query = try query(client, true);
    const status_flags = linux.fcntl(client, linux.F.GETFL, 0);
    const descriptor_flags = linux.fcntl(client, linux.F.GETFD, 0);
    if (linux.errno(status_flags) != .SUCCESS or linux.errno(descriptor_flags) != .SUCCESS) return error.ConnectSocketFlagsQueryFailed;
    const repeated = try failure(try connect(&ring, client, .client, 1000005, &peer, @sizeOf(linux.sockaddr.in)), -106);
    const unchanged = std.mem.eql(u8, std.mem.asBytes(&original_peer), std.mem.asBytes(&peer));
    if (!unchanged) return error.ConnectChangedPeerInput;
    const client_closed = try close(client, &client_owned);
    const guard_closed = try close(guard, &guard_owned);
    const ring_open = linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) == .SUCCESS;
    if (!ring_open) return error.ConnectClosedCallerRing;
    var output_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &output_buffer);
    try std.json.Stringify.value(.{
        .connection = .{ .request = connection.request, .cqe = connection.cqe, .local = local_query, .peer = peer_query, .flags = .{ .nonblocking = status_flags & linux.SOCK.NONBLOCK != 0, .cloexec = descriptor_flags & linux.FD_CLOEXEC != 0 } },
        .failures = .{ invalid_fd, nonsocket, short, wrong, refused, repeated },
        .refusal_address = .{ .address = address(guard_address), .length = guard_length },
        .peer_unchanged = unchanged,
        .descriptors_closed = .{ .client = client_closed, .guard = guard_closed },
        .ring_still_open = ring_open,
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
