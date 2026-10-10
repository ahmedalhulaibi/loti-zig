const std = @import("std");
const linux = std.os.linux;
const Mode = enum { none, nonblock, cloexec, both };
const Role = enum { listener, ring, invalid };
const Address = struct { family: u16, address: [4]u8, port: u16 };
const Query = struct { address: Address, length: linux.socklen_t };
const Flags = struct { nonblocking: bool, cloexec: bool };
const Request = struct { operation: linux.IORING_OP, tag: u64, descriptor: Role, length: u32, flags: u8, operation_flags: u32, address_supplied: bool, length_supplied: bool, capacity: ?u32 };
const Completion = struct { tag: u64, result: i32, flags: u32 };
const Operation = struct { request: Request, cqe: Completion, address_length: ?linux.socklen_t, storage: [32]u8 };
const Plan = struct {
    capacity: ?u32,
    mode: Mode,

    fn init(args: []const []const u8) !Plan {
        if (args.len != 3) return error.ExpectedAcceptCapacityAndFlags;
        var capacity: ?u32 = null;
        if (!std.mem.eql(u8, args[1], "null")) {
            if (args[1].len == 0) return error.InvalidAcceptCapacity;
            for (args[1]) |byte| if (!std.ascii.isDigit(byte)) return error.InvalidAcceptCapacity;
            const value = std.fmt.parseInt(u64, args[1], 10) catch return error.InvalidAcceptCapacity;
            if (value > @sizeOf(linux.sockaddr.in)) return error.AcceptCapacityOutOfRange;
            capacity = @intCast(value);
        }
        return .{ .capacity = capacity, .mode = std.meta.stringToEnum(Mode, args[2]) orelse return error.UnknownAcceptFlags };
    }

    fn flags(self: Plan) u32 {
        return switch (self.mode) {
            .none => 0,
            .nonblock => linux.SOCK.NONBLOCK,
            .cloexec => linux.SOCK.CLOEXEC,
            .both => linux.SOCK.NONBLOCK | linux.SOCK.CLOEXEC,
        };
    }
};

fn flags(fd: linux.fd_t) !Flags {
    const status = linux.fcntl(fd, linux.F.GETFL, 0);
    const descriptor = linux.fcntl(fd, linux.F.GETFD, 0);
    if (linux.errno(status) != .SUCCESS or linux.errno(descriptor) != .SUCCESS) return error.AcceptFlagsQueryFailed;
    return .{ .nonblocking = status & linux.SOCK.NONBLOCK != 0, .cloexec = descriptor & linux.FD_CLOEXEC != 0 };
}

fn close(fd: linux.fd_t, owned: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.AcceptSocketCloseFailed;
    owned.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.AcceptSocketStillOpen;
    return true;
}

fn query(fd: linux.fd_t, comptime peer: bool) !Query {
    var value: linux.sockaddr.in = std.mem.zeroes(linux.sockaddr.in);
    var length: linux.socklen_t = @sizeOf(linux.sockaddr.in);
    const result = if (peer) linux.getpeername(fd, @ptrCast(&value), &length) else linux.getsockname(fd, @ptrCast(&value), &length);
    if (linux.errno(result) != .SUCCESS or length != @sizeOf(linux.sockaddr.in) or value.family != linux.AF.INET) return error.AcceptEndpointQueryFailed;
    return .{ .address = .{ .family = value.family, .address = std.mem.toBytes(value.addr), .port = std.mem.bigToNative(u16, value.port) }, .length = length };
}

fn accept(ring: *linux.IoUring, fd: linux.fd_t, role: Role, tag: u64, capacity: ?u32, operation_flags: u32) !Operation {
    var storage: [32]u8 align(@alignOf(linux.sockaddr.in)) = @splat(165);
    var length: linux.socklen_t = capacity orelse 0;
    const addr: ?*linux.sockaddr = if (capacity != null) @ptrCast(&storage) else null;
    const addrlen: ?*linux.socklen_t = if (capacity != null) &length else null;
    const sqe = try ring.accept(tag, fd, addr, addrlen, operation_flags);
    if (sqe.opcode != .ACCEPT or sqe.fd != fd or sqe.addr != @intFromPtr(addr) or sqe.off != @intFromPtr(addrlen)) return error.InvalidAcceptRequest;
    const request: Request = .{ .operation = sqe.opcode, .tag = sqe.user_data, .descriptor = role, .length = sqe.len, .flags = sqe.flags, .operation_flags = sqe.rw_flags, .address_supplied = sqe.addr != 0, .length_supplied = sqe.off != 0, .capacity = if (addrlen != null) length else null };
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedAcceptSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedAcceptCompletion;
    return .{ .request = request, .cqe = .{ .tag = cqe.user_data, .result = cqe.res, .flags = cqe.flags }, .address_length = if (addrlen != null) length else null, .storage = storage };
}

fn failure(operation: Operation, expected: i32) !Operation {
    if (operation.cqe.result != expected) return error.UnexpectedAcceptFailure;
    return operation;
}

pub fn main(init: std.process.Init) !void {
    const plan = try Plan.init(try init.minimal.args.toSlice(init.arena.allocator()));
    const created = linux.socket(linux.AF.INET, linux.SOCK.STREAM | linux.SOCK.NONBLOCK | linux.SOCK.CLOEXEC, 0);
    if (linux.errno(created) != .SUCCESS) return error.AcceptListenerCreationFailed;
    const listener: linux.fd_t = @intCast(created);
    var listener_owned = true;
    defer {
        if (listener_owned) _ = linux.close(listener);
    }
    var address: linux.sockaddr.in = .{ .port = 0, .addr = std.mem.nativeToBig(u32, 0x7f000001) };
    if (linux.errno(linux.bind(listener, @ptrCast(&address), @sizeOf(linux.sockaddr.in))) != .SUCCESS) return error.AcceptListenerBindFailed;
    if (linux.errno(linux.listen(listener, 1)) != .SUCCESS) return error.AcceptListenerListenFailed;
    const local = try query(listener, false);
    const listener_flags = try flags(listener);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    const failures = [_]Operation{
        try failure(try accept(&ring, -1, .invalid, 10, 16, 0), -9),
        try failure(try accept(&ring, ring.fd, .ring, 11, 16, 0), -88),
        try failure(try accept(&ring, listener, .listener, 12, 16, 1), -22),
    };
    var stdout_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &stdout_buffer);
    try std.json.Stringify.value(.{ .event = "loti.accept.ready", .address = "127.0.0.1", .port = local.address.port }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
    // Both optional pointers and all nested output storage remain live through the CQE.
    const operation = try accept(&ring, listener, .listener, 1, plan.capacity, plan.flags());
    if (operation.cqe.result < 0) return error.AcceptConnectionFailed;
    const accepted: linux.fd_t = operation.cqe.result;
    var accepted_owned = true;
    defer {
        if (accepted_owned) _ = linux.close(accepted);
    }
    const peer = try query(accepted, true);
    const endpoint = try query(accepted, false);
    const accepted_flags = try flags(accepted);
    const listener_closed = try close(listener, &listener_owned);
    const retained = linux.errno(linux.fcntl(accepted, linux.F.GETFD, 0)) == .SUCCESS;
    if (!retained) return error.AcceptedSocketClosedWithListener;
    const accepted_closed = try close(accepted, &accepted_owned);
    const ring_open = linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) == .SUCCESS;
    if (!ring_open) return error.AcceptClosedCallerRing;
    try std.json.Stringify.value(.{ .failures = failures, .accepted = .{
        .request = operation.request,
        .cqe = operation.cqe,
        .address_length = operation.address_length,
        .storage = operation.storage,
        .peer = peer,
        .local = endpoint,
        .flags = accepted_flags,
    }, .listener_flags = listener_flags, .cleanup = .{ .listener_closed = listener_closed, .accepted_retained_after_listener_close = retained, .accepted_closed = accepted_closed, .ring_still_open = ring_open } }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
