const std = @import("std");
const linux = std.os.linux;
const current = std.math.maxInt(u64);
const unsupported: linux.kernel_rwf = 0x8000_0000;

const Role = enum { memory, invalid };
const Request = struct { operation: linux.IORING_OP, tag: u64, descriptor: Role, length: u32, offset: u64, flags: u8, operation_flags: u32 };
const Completion = struct { user_data: u64, result: i32, flags: u32 };
const Operation = struct { request: Request, cqe: Completion };
const Snapshot = struct { position: u64, size: u64, bytes_hex: []const u8, append: bool };
const Step = struct { request: Request, cqe: Completion, after: Snapshot };

fn position(fd: linux.fd_t, offset: linux.off_t, whence: u32) !u64 {
    const result = linux.lseek(fd, offset, whence);
    if (linux.errno(result) != .SUCCESS) return error.RwfPositionQueryFailed;
    return result;
}

fn readAll(fd: linux.fd_t, bytes: []u8) !void {
    var used: usize = 0;
    while (used < bytes.len) {
        const result = linux.pread(fd, bytes[used..].ptr, bytes.len - used, @intCast(used));
        switch (linux.errno(result)) {
            .SUCCESS => {},
            .INTR => continue,
            else => return error.RwfObservationReadFailed,
        }
        if (result == 0 or result > bytes.len - used) return error.RwfObservedSizeChanged;
        used += result;
    }
}

fn snapshot(init: std.process.Init, fd: linux.fd_t) !Snapshot {
    const allocator = init.arena.allocator();
    const stat = try (std.Io.File{ .handle = fd, .flags = .{ .nonblocking = false } }).stat(init.io);
    if (stat.size > 8196) return error.RwfObservedSizeOutOfBounds;
    const bytes = try allocator.alloc(u8, @intCast(stat.size));
    try readAll(fd, bytes);
    const hex = try allocator.alloc(u8, bytes.len * 2);
    const digits = "0123456789abcdef";
    for (bytes, 0..) |byte, index| {
        hex[index * 2] = digits[byte >> 4];
        hex[index * 2 + 1] = digits[byte & 15];
    }
    const status = linux.fcntl(fd, linux.F.GETFL, 0);
    if (linux.errno(status) != .SUCCESS) return error.RwfStatusQueryFailed;
    const append_mask: u32 = @bitCast(linux.O{ .APPEND = true });
    return .{ .position = try position(fd, 0, linux.SEEK.CUR), .size = stat.size, .bytes_hex = hex, .append = status & append_mask != 0 };
}

fn operation(ring: *linux.IoUring, fd: linux.fd_t, role: Role, tag: u64, bytes: []u8, offset: u64, flags: linux.kernel_rwf, read: bool) !Operation {
    const sqe = if (read) try ring.read(tag, fd, .{ .buffer = bytes }, offset) else try ring.write(tag, fd, bytes, offset);
    // These flags are per I/O. Do not put them in the u8 dependency bitmap.
    sqe.rw_flags = flags;
    const request: Request = .{ .operation = sqe.opcode, .tag = sqe.user_data, .descriptor = role, .length = sqe.len, .offset = sqe.off, .flags = sqe.flags, .operation_flags = sqe.rw_flags };
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedRwfSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedRwfCompletion;
    return .{ .request = request, .cqe = .{ .user_data = cqe.user_data, .result = cqe.res, .flags = cqe.flags } };
}

fn step(init: std.process.Init, ring: *linux.IoUring, fd: linux.fd_t, tag: u64, bytes: []u8, offset: u64, flags: linux.kernel_rwf) !Step {
    const completed = try operation(ring, fd, .memory, tag, bytes, offset, flags, false);
    if (completed.cqe.result != bytes.len) return error.RwfWriteIncomplete;
    return .{ .request = completed.request, .cqe = completed.cqe, .after = try snapshot(init, fd) };
}

fn close(fd: linux.fd_t, owned: *bool) !bool {
    if (linux.errno(linux.close(fd)) != .SUCCESS) return error.RwfDescriptorCloseFailed;
    owned.* = false;
    const closed = linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) == .BADF;
    if (!closed) return error.RwfDescriptorStillOpen;
    return closed;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len != 2) return error.ExpectedRwfInput;
    const path = try allocator.dupeSentinel(u8, args[1], 0);
    const opened = linux.open(path, .{ .ACCMODE = .RDONLY, .CLOEXEC = true, .NOFOLLOW = true, .NONBLOCK = true }, 0);
    if (linux.errno(opened) != .SUCCESS) return error.RwfInputOpenFailed;
    const source: linux.fd_t = @intCast(opened);
    var source_owned = true;
    defer if (source_owned) {
        _ = linux.close(source);
    };
    const input_stat = try (std.Io.File{ .handle = source, .flags = .{ .nonblocking = true } }).stat(init.io);
    if (input_stat.kind != .file) return error.ExpectedRegularRwfInput;
    if (input_stat.size == 0) return error.RwfInputEmpty;
    if (input_stat.size > 4097) return error.RwfInputTooLarge;
    const payload = try allocator.alloc(u8, @intCast(input_stat.size));
    try readAll(source, payload);

    const created = linux.memfd_create("loti-rwf", linux.MFD.CLOEXEC);
    if (linux.errno(created) != .SUCCESS) return error.RwfMemoryFileCreationFailed;
    const memory: linux.fd_t = @intCast(created);
    var memory_owned = true;
    defer if (memory_owned) {
        _ = linux.close(memory);
    };
    const memory_flags = linux.fcntl(memory, linux.F.GETFD, 0);
    if (linux.errno(memory_flags) != .SUCCESS or memory_flags & linux.FD_CLOEXEC == 0) return error.RwfMemoryFileNotCloexec;
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var marker = [_]u8{ 165, 90 };
    const seed = try step(init, &ring, memory, 1, &marker, 0, 0);
    if (try position(memory, 1, linux.SEEK.SET) != 1) return error.RwfPositionSetFailed;
    // APPEND ignores explicit offset zero but preserves the open-file-description cursor.
    const explicit_append = try step(init, &ring, memory, 2, payload, 0, linux.RWF.APPEND);
    // No persistent O_APPEND: the next ordinary positional write really overwrites.
    const ordinary = try step(init, &ring, memory, 3, payload, 0, 0);
    // All-ones offset requests current-position semantics; APPEND advances it to EOF.
    const current_append = try step(init, &ring, memory, 4, payload, current, linux.RWF.APPEND);
    const invalid_write = try operation(&ring, memory, .memory, 10, payload, 0, unsupported, false);
    var poison: [9]u8 = @splat(165);
    const invalid_read = try operation(&ring, memory, .memory, 11, &poison, 0, unsupported, true);
    const invalid_fd = try operation(&ring, -1, .invalid, 12, payload, 0, linux.RWF.APPEND, false);
    if (invalid_write.cqe.result != -95 or invalid_read.cqe.result != -95 or invalid_fd.cqe.result != -9) return error.UnexpectedRwfFailure;
    const after_failures = try snapshot(init, memory);
    const source_closed = try close(source, &source_owned);
    const memory_closed = try close(memory, &memory_owned);
    const ring_open = linux.errno(linux.fcntl(ring.fd, linux.F.GETFD, 0)) == .SUCCESS;
    if (!ring_open) return error.RwfClosedCallerRing;
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try std.json.Stringify.value(.{
        .seed = seed,
        .explicit_append = explicit_append,
        .ordinary = ordinary,
        .current_append = current_append,
        .failures = .{ invalid_write, invalid_read, invalid_fd },
        .failed_read_storage = poison,
        .after_failures = after_failures,
        .cleanup = .{ .memory_cloexec = true, .source_closed = source_closed, .memory_closed = memory_closed, .ring_still_open = ring_open },
    }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
