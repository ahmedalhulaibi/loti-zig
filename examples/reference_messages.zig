const std = @import("std");
const linux = std.os.linux;
const alignment = linux.cmsg_align;
const header_size = std.mem.alignForward(usize, @sizeOf(linux.cmsghdr), alignment);
const control_length = header_size + @sizeOf(linux.fd_t);
const control_space = std.mem.alignForward(usize, control_length, alignment);
const Control = [control_space]u8;
const Role = enum { socket, ring, invalid };
const Request = struct { operation: linux.IORING_OP, tag: u64, descriptor: Role, length: u32, offset: u64, flags: u8, operation_flags: u32, vector_lengths: [2]usize, control_capacity: usize, name_supplied: bool, name_length: linux.socklen_t };
const Completion = struct { tag: u64, result: i32, flags: u32 };
const Header = struct { length: usize, level: i32, type: i32 };
const Send = struct { request: Request, cqe: Completion, control: Header, input_unchanged: bool };
const Receive = struct { request: Request, cqe: Completion, message: struct { flags: u32, control_length: usize, name_length: linux.socklen_t }, storage: []u8, control: ?Header };

fn capacityArgument(args: []const []const u8) !usize {
    if (args.len != 3) return error.ExpectedMessageInputAndCapacity;
    if (args[2].len == 0) return error.InvalidMessageCapacity;
    for (args[2]) |byte| {
        if (!std.ascii.isDigit(byte)) return error.InvalidMessageCapacity;
    }
    const value = std.fmt.parseInt(usize, args[2], 10) catch return error.InvalidMessageCapacity;
    if (value > 4097) return error.MessageCapacityOutOfRange;
    return value;
}

fn descriptorCount(io: std.Io) !i64 {
    const directory = try std.Io.Dir.cwd().openDir(io, "/proc/self/fd", .{ .iterate = true });
    defer directory.close(io);
    var iterator = directory.iterate();
    var count: i64 = 0;
    while (try iterator.next(io)) |entry| {
        const fd = std.fmt.parseInt(linux.fd_t, entry.name, 10) catch return error.InvalidMessageProcDescriptor;
        if (fd != directory.handle) count += 1;
    }
    return count;
}

fn close(fd: linux.fd_t, owned: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.MessageDescriptorCloseFailed;
    owned.* = false;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.MessageDescriptorStillOpen;
    return true;
}

fn right(fd: linux.fd_t) Control {
    var memory: Control align(alignment) = @splat(0);
    const value: *linux.cmsghdr = @ptrCast(&memory);
    value.* = .{ .len = control_length, .level = linux.SOL.SOCKET, .type = linux.SCM.RIGHTS };
    std.mem.bytesAsValue(linux.fd_t, memory[header_size..][0..@sizeOf(linux.fd_t)]).* = fd;
    return memory;
}

fn header(memory: *align(alignment) const Control) Header {
    const value: *const linux.cmsghdr = @ptrCast(memory);
    return .{ .length = value.len, .level = value.level, .type = value.type };
}

fn completion(ring: *linux.IoUring, tag: u64) !Completion {
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedMessageSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedMessageCompletion;
    return .{ .tag = cqe.user_data, .result = cqe.res, .flags = cqe.flags };
}

fn prepared(sqe: *const linux.io_uring_sqe, role: Role, vectors: [2]usize, ctl: usize, name: bool, namelen: linux.socklen_t) Request {
    return .{ .operation = sqe.opcode, .tag = sqe.user_data, .descriptor = role, .length = sqe.len, .offset = sqe.off, .flags = sqe.flags, .operation_flags = sqe.rw_flags, .vector_lengths = vectors, .control_capacity = ctl, .name_supplied = name, .name_length = namelen };
}

fn send(ring: *linux.IoUring, fd: linux.fd_t, role: Role, tag: u64, payload: []const u8, control: *align(alignment) const Control) !Send {
    const split = payload.len / 2;
    // Linux checks iovec addresses even for zero lengths; an empty literal can have an invalid sentinel pointer.
    const empty = [_]u8{0};
    const data = if (payload.len == 0) empty[0..0] else payload;
    const vectors = [_]std.posix.iovec_const{ .{ .base = data.ptr, .len = split }, .{ .base = data[split..].ptr, .len = payload.len - split } };
    const message: linux.msghdr_const = .{ .name = null, .namelen = 0, .iov = &vectors, .iovlen = vectors.len, .control = control, .controllen = control.len, .flags = 0 };
    const before = control.*;
    const sqe = try ring.sendmsg(tag, fd, &message, linux.MSG.DONTWAIT | linux.MSG.NOSIGNAL);
    if (sqe.opcode != .SENDMSG or sqe.addr != @intFromPtr(&message) or sqe.fd != fd) return error.InvalidSendMessageRequest;
    const request = prepared(sqe, role, .{ vectors[0].len, vectors[1].len }, message.controllen, message.name != null, message.namelen);
    const cqe = try completion(ring, tag);
    const unchanged = std.mem.eql(u8, &before, control);
    if (!unchanged) return error.SendChangedControlInput;
    return .{ .request = request, .cqe = cqe, .control = header(control), .input_unchanged = unchanged };
}

fn receive(allocator: std.mem.Allocator, ring: *linux.IoUring, fd: linux.fd_t, role: Role, tag: u64, capacity: usize, flags: u32, control: ?*align(alignment) Control) !Receive {
    const storage = try allocator.alloc(u8, capacity + 16);
    @memset(storage, 165);
    const split = capacity / 2;
    var vectors = [_]std.posix.iovec{ .{ .base = storage.ptr, .len = split }, .{ .base = storage[split..].ptr, .len = capacity - split } };
    var message: linux.msghdr = .{ .name = null, .namelen = 0, .iov = &vectors, .iovlen = vectors.len, .control = control, .controllen = if (control == null) 0 else control_space, .flags = 0 };
    const sqe = try ring.recvmsg(tag, fd, &message, flags);
    if (sqe.opcode != .RECVMSG or sqe.addr != @intFromPtr(&message) or sqe.fd != fd) return error.InvalidReceiveMessageRequest;
    const request = prepared(sqe, role, .{ vectors[0].len, vectors[1].len }, message.controllen, message.name != null, message.namelen);
    const cqe = try completion(ring, tag);
    if (message.controllen > (if (control == null) @as(usize, 0) else control_space)) return error.MessageControlLengthOutOfBounds;
    return .{ .request = request, .cqe = cqe, .message = .{ .flags = message.flags, .control_length = message.controllen, .name_length = message.namelen }, .storage = storage, .control = if (control != null and message.controllen >= control_length) header(control.?) else null };
}

fn expect(cqe: Completion, result: i32) !void {
    if (cqe.result != result) return error.UnexpectedMessageResult;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    const capacity = try capacityArgument(args);
    const initial_count = try descriptorCount(init.io);
    const path = try allocator.dupeSentinel(u8, args[1], 0);
    const opened = linux.open(path, .{ .ACCMODE = .RDONLY, .CLOEXEC = true, .NOFOLLOW = true, .NONBLOCK = true }, 0);
    if (linux.errno(opened) != .SUCCESS) return error.MessageInputOpenFailed;
    const source: linux.fd_t = @intCast(opened);
    var source_owned = true;
    defer {
        if (source_owned) _ = linux.close(source);
    }
    const file: std.Io.File = .{ .handle = source, .flags = .{ .nonblocking = true } };
    const stat = try file.stat(init.io);
    if (stat.kind != .file) return error.ExpectedRegularMessageInput;
    if (stat.size > 4097) return error.MessageInputTooLarge;
    const payload = try allocator.alloc(u8, @intCast(stat.size));
    var used: usize = 0;
    while (used < payload.len) {
        const result = linux.pread(source, payload[used..].ptr, payload.len - used, @intCast(used));
        switch (linux.errno(result)) {
            .SUCCESS => {},
            .INTR => continue,
            else => return error.MessageInputReadFailed,
        }
        if (result == 0 or result > payload.len - used) return error.MessageInputSizeChanged;
        used += result;
    }
    var sockets: [2]linux.fd_t = undefined;
    if (linux.errno(linux.socketpair(linux.AF.UNIX, linux.SOCK.DGRAM | linux.SOCK.NONBLOCK | linux.SOCK.CLOEXEC, 0, &sockets)) != .SUCCESS) return error.MessageSocketPairCreationFailed;
    var sockets_owned = [_]bool{ true, true };
    defer {
        for (sockets, sockets_owned) |fd, owned| {
            if (owned) _ = linux.close(fd);
        }
    }
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var send_control: Control align(alignment) = right(source);
    var receive_control: Control align(alignment) = @splat(0);
    const empty_before = try receive(allocator, &ring, sockets[1], .socket, 1, 1, linux.MSG.DONTWAIT, null);
    try expect(empty_before.cqe, -11);
    const sent = try send(&ring, sockets[0], .socket, 2, payload, &send_control);
    try expect(sent.cqe, @intCast(payload.len));
    const source_closed = try close(source, &source_owned);
    const received = try receive(allocator, &ring, sockets[1], .socket, 3, capacity, linux.MSG.DONTWAIT | linux.MSG.TRUNC | linux.MSG.CMSG_CLOEXEC, &receive_control);
    try expect(received.cqe, @intCast(payload.len));
    const observed = received.control orelse return error.MissingReceivedRight;
    if (observed.length != control_length or observed.level != linux.SOL.SOCKET or observed.type != linux.SCM.RIGHTS) return error.InvalidReceivedRight;
    const passed = std.mem.bytesAsValue(linux.fd_t, receive_control[header_size..][0..@sizeOf(linux.fd_t)]).*;
    if (passed < 0) return error.InvalidReceivedDescriptor;
    var passed_owned = true;
    defer {
        if (passed_owned) _ = linux.close(passed);
    }
    const flags = linux.fcntl(passed, linux.F.GETFD, 0);
    if (linux.errno(flags) != .SUCCESS) return error.ReceivedDescriptorFlagsQueryFailed;
    const empty_after = try receive(allocator, &ring, sockets[1], .socket, 4, 1, linux.MSG.DONTWAIT, null);
    try expect(empty_after.cqe, -11);
    const file_memory = try allocator.alloc(u8, payload.len + 17);
    @memset(file_memory, 165);
    const read = try ring.read(5, passed, .{ .buffer = file_memory[0 .. payload.len + 1] }, 0);
    const read_request = .{ .operation = read.opcode, .tag = read.user_data, .length = read.len, .offset = read.off, .flags = read.flags };
    const read_cqe = try completion(&ring, 5);
    try expect(read_cqe, @intCast(payload.len));
    const before_truncation = try descriptorCount(init.io);
    const marker = [_]u8{ 0, 255, 90 };
    send_control = right(passed);
    const truncation_sent = try send(&ring, sockets[0], .socket, 6, &marker, &send_control);
    try expect(truncation_sent.cqe, 3);
    const truncation_received = try receive(allocator, &ring, sockets[1], .socket, 7, 2, linux.MSG.DONTWAIT | linux.MSG.CMSG_CLOEXEC, null);
    try expect(truncation_received.cqe, 2);
    const after_truncation = try descriptorCount(init.io);
    if (after_truncation != before_truncation) return error.TruncatedControlDescriptorLeak;
    const truncation_empty = try receive(allocator, &ring, sockets[1], .socket, 8, 1, linux.MSG.DONTWAIT, null);
    try expect(truncation_empty.cqe, -11);
    const bad_send = try send(&ring, -1, .invalid, 10, &.{}, &send_control);
    try expect(bad_send.cqe, -9);
    const bad_receive = try receive(allocator, &ring, -1, .invalid, 11, 1, linux.MSG.DONTWAIT, null);
    try expect(bad_receive.cqe, -9);
    const nonsocket_send = try send(&ring, ring.fd, .ring, 12, &.{}, &send_control);
    try expect(nonsocket_send.cqe, -88);
    const nonsocket_receive = try receive(allocator, &ring, ring.fd, .ring, 13, 1, linux.MSG.DONTWAIT, null);
    try expect(nonsocket_receive.cqe, -88);
    var malformed: Control align(alignment) = right(passed);
    const bad_header: *linux.cmsghdr = @ptrCast(&malformed);
    bad_header.len = 8;
    const malformed_send = try send(&ring, sockets[0], .socket, 14, &.{}, &malformed);
    try expect(malformed_send.cqe, -22);
    var invalid_right: Control align(alignment) = right(-1);
    const invalid_send = try send(&ring, sockets[0], .socket, 15, &.{}, &invalid_right);
    try expect(invalid_send.cqe, -9);
    const passed_closed = try close(passed, &passed_owned);
    const after_received_close = try descriptorCount(init.io);
    if (after_received_close != after_truncation - 1) return error.ReceivedDescriptorCountMismatch;
    const socket_closures = .{ try close(sockets[0], &sockets_owned[0]), try close(sockets[1], &sockets_owned[1]) };
    const final_count = try descriptorCount(init.io);
    if (final_count != initial_count + 1) return error.MessageOwnedDescriptorLeak;
    const ring_open = linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) == .SUCCESS;
    if (!ring_open) return error.MessageCallerRingClosed;
    var output_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &output_buffer);
    try std.json.Stringify.value(.{
        .abi = .{ .header_size = @sizeOf(linux.cmsghdr), .control_length = control_length, .control_space = control_space, .alignment = alignment },
        .empty_before = empty_before,
        .sent = sent,
        .source_closed_after_send = source_closed,
        .received = received,
        .empty_after = empty_after,
        .passed_file = .{ .request = read_request, .cqe = read_cqe, .storage = file_memory, .cloexec = flags & linux.FD_CLOEXEC != 0 },
        .truncation = .{ .sent = truncation_sent, .received = truncation_received, .empty_after = truncation_empty, .descriptor_delta = after_truncation - before_truncation },
        .failures = .{ bad_send, bad_receive, nonsocket_send, nonsocket_receive, malformed_send, invalid_send },
        .cleanup = .{ .received_closed = passed_closed, .received_close_delta = after_received_close - after_truncation, .sockets_closed = socket_closures, .descriptor_delta_from_initial = final_count - initial_count, .ring_still_open = ring_open },
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
