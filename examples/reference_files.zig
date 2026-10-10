const std = @import("std");
const linux = std.os.linux;
const stat_mask: linux.STATX = .{ .TYPE = true, .SIZE = true };

fn completion(ring: *linux.IoUring, tag: u64) !linux.io_uring_cqe {
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedFileCompletion;
    return cqe;
}

fn statFile(ring: *linux.IoUring, fd: linux.fd_t, tag: u64) !linux.Statx {
    var stat = std.mem.zeroes(linux.Statx);
    _ = try ring.statx(tag, fd, "", linux.AT.EMPTY_PATH, stat_mask, &stat);
    if ((try completion(ring, tag)).res != 0) return error.FileStatFailed;
    if (!stat.mask.SIZE or !stat.mask.TYPE) return error.RequiredStatFieldsMissing;
    return stat;
}

fn closeFile(ring: *linux.IoUring, fd: linux.fd_t, tag: u64) !bool {
    _ = try ring.close(tag, fd);
    if ((try completion(ring, tag)).res != 0) return error.FileCloseFailed;
    const closed = linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) == .BADF;
    if (!closed) return error.ClosedDescriptorStillOpen;
    return closed;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len != 3) return error.ExpectedInputAndNewOutput;
    const input_path = try allocator.dupeSentinel(u8, args[1], 0);
    const output_path = try allocator.dupeSentinel(u8, args[2], 0);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();

    _ = try ring.openat(1, linux.AT.FDCWD, input_path, .{ .ACCMODE = .RDONLY, .CLOEXEC = true, .NOFOLLOW = true, .NONBLOCK = true }, 0);
    const opened_input = try completion(&ring, 1);
    if (opened_input.res < 0) return error.InputOpenFailed;
    const input_fd: linux.fd_t = opened_input.res;
    var input_owned = true;
    defer if (input_owned) {
        _ = linux.close(input_fd);
    };
    const input_stat = try statFile(&ring, input_fd, 2);
    if (input_stat.mode & linux.S.IFMT != linux.S.IFREG) return error.ExpectedRegularInputFile;
    if (input_stat.size > std.math.maxInt(u64) - 4096) return error.InputFileTooLarge;

    _ = try ring.openat(3, linux.AT.FDCWD, output_path, .{ .ACCMODE = .RDWR, .CREAT = true, .EXCL = true, .CLOEXEC = true, .NOFOLLOW = true }, 0o600);
    const opened_output = try completion(&ring, 3);
    if (opened_output.res < 0) return error.ExclusiveOutputOpenFailed;
    const output_fd: linux.fd_t = opened_output.res;
    var output_owned = true;
    defer if (output_owned) {
        _ = linux.close(output_fd);
    };

    var memory: [4096]u8 = undefined;
    var read_vectors = [_]std.posix.iovec{
        .{ .base = memory[0..1024].ptr, .len = 1024 },
        .{ .base = memory[1024..].ptr, .len = 3072 },
    };
    var reads: std.ArrayList(i32) = .empty;
    var writes: std.ArrayList(i32) = .empty;
    var offset: u64 = 0;
    var read_vector_count: u32 = 0;
    var write_vector_count: u32 = 0;
    while (true) {
        const read_sqe = try ring.read(10, input_fd, .{ .iovecs = &read_vectors }, offset);
        read_vector_count = read_sqe.len;
        const read_cqe = try completion(&ring, 10);
        if (read_cqe.res < 0) return error.FileReadFailed;
        try reads.append(allocator, read_cqe.res);
        const count: usize = @intCast(read_cqe.res);
        if (count > memory.len) return error.ReadResultOutOfBounds;
        if (count == 0) break;
        if (offset > input_stat.size or count > input_stat.size - offset) return error.InputSizeChanged;
        var written: usize = 0;
        while (written < count) {
            const remaining = memory[written..count];
            const first = @min(1024, remaining.len);
            const vectors = [_]std.posix.iovec_const{
                .{ .base = remaining[0..first].ptr, .len = first },
                .{ .base = remaining[first..].ptr, .len = remaining.len - first },
            };
            const write_sqe = try ring.writev(11, output_fd, &vectors, offset + written);
            write_vector_count = write_sqe.len;
            const write_cqe = try completion(&ring, 11);
            if (write_cqe.res < 0) return error.FileWriteFailed;
            const progress: usize = @intCast(write_cqe.res);
            if (progress == 0 or progress > remaining.len) return error.InvalidWriteProgress;
            try writes.append(allocator, write_cqe.res);
            written += progress;
        }
        offset += count;
    }
    if (offset != input_stat.size) return error.InputSizeChanged;
    if (offset == 0) {
        const empty = [_]std.posix.iovec_const{
            .{ .base = &memory, .len = 0 }, .{ .base = &memory, .len = 0 },
        };
        const sqe = try ring.writev(11, output_fd, &empty, 0);
        write_vector_count = sqe.len;
        const cqe = try completion(&ring, 11);
        if (cqe.res != 0) return error.EmptyWriteFailed;
        try writes.append(allocator, cqe.res);
    }

    const allocated = try ring.fallocate(12, output_fd, 0, offset, 4096);
    const allocation_offset = allocated.off;
    const allocation_length = allocated.addr;
    const allocation_mode = allocated.len;
    const allocation_cqe = try completion(&ring, 12);
    if (allocation_cqe.res != 0) return error.FileAllocationFailed;
    const output_stat = try statFile(&ring, output_fd, 13);
    if (output_stat.size != offset + 4096) return error.FileAllocationSizeMismatch;

    const Sync = struct { operation: []const u8, tag: u64, flags: u32, result: i32 };
    var syncs: [2]Sync = undefined;
    for ([_]u32{ 0, linux.IORING_FSYNC_DATASYNC }, 0..) |flags, index| {
        const tag = 20 + index;
        const sqe = try ring.fsync(tag, output_fd, flags);
        const submitted_flags = sqe.rw_flags;
        const operation = @tagName(sqe.opcode);
        const cqe = try completion(&ring, tag);
        if (cqe.res != 0) return error.FileSyncFailed;
        syncs[index] = .{ .operation = operation, .tag = tag, .flags = submitted_flags, .result = cqe.res };
    }
    const closed_output = try closeFile(&ring, output_fd, 22);
    output_owned = false;
    const closed_input = try closeFile(&ring, input_fd, 23);
    input_owned = false;

    _ = try ring.openat(24, linux.AT.FDCWD, output_path, .{ .ACCMODE = .RDONLY, .CLOEXEC = true, .NOFOLLOW = true }, 0);
    const reopened = try completion(&ring, 24);
    if (reopened.res < 0) return error.OutputReopenFailed;
    const reopened_fd: linux.fd_t = reopened.res;
    var reopened_owned = true;
    defer if (reopened_owned) {
        _ = linux.close(reopened_fd);
    };
    var hash = std.crypto.hash.sha2.Sha256.init(.{});
    var read_back: u64 = 0;
    while (true) {
        _ = try ring.read(25, reopened_fd, .{ .iovecs = &read_vectors }, read_back);
        const cqe = try completion(&ring, 25);
        if (cqe.res < 0) return error.ReopenedReadFailed;
        const count: usize = @intCast(cqe.res);
        if (count > memory.len) return error.ReadResultOutOfBounds;
        if (count == 0) break;
        hash.update(memory[0..count]);
        read_back += count;
    }
    if (read_back != output_stat.size) return error.ReopenedSizeMismatch;
    var digest: [32]u8 = undefined;
    hash.final(&digest);
    const digest_hex = std.fmt.bytesToHex(digest, .lower);
    const closed_reopened = try closeFile(&ring, reopened_fd, 26);
    reopened_owned = false;

    const Failure = struct { operation: []const u8, tag: u64, result: i32, flags: u32 };
    var failures: [7]Failure = undefined;
    var invalid_stat = std.mem.zeroes(linux.Statx);
    const invalid_write = [_]std.posix.iovec_const{
        .{ .base = &memory, .len = 1024 }, .{ .base = &memory, .len = 3072 },
    };
    for ([_][]const u8{ "OPENAT", "READV", "WRITEV", "FALLOCATE", "STATX", "FSYNC", "CLOSE" }, 0..) |name, index| {
        const tag = 50 + index;
        _ = switch (index) {
            0 => try ring.openat(tag, -1, "relative", .{ .ACCMODE = .RDONLY }, 0),
            1 => try ring.read(tag, -1, .{ .iovecs = &read_vectors }, 0),
            2 => try ring.writev(tag, -1, &invalid_write, 0),
            3 => try ring.fallocate(tag, -1, 0, 0, 4096),
            4 => try ring.statx(tag, -1, "", linux.AT.EMPTY_PATH, stat_mask, &invalid_stat),
            5 => try ring.fsync(tag, -1, 0),
            6 => try ring.close(tag, -1),
            else => unreachable,
        };
        const cqe = try completion(&ring, tag);
        if (cqe.res != -@as(i32, @backingInt(linux.E.BADF))) return error.InvalidDescriptorDidNotFail;
        failures[index] = .{ .operation = name, .tag = tag, .result = cqe.res, .flags = cqe.flags };
    }

    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try std.json.Stringify.value(.{
        .opens = .{ opened_input.res >= 0, opened_output.res >= 0, reopened.res >= 0 },
        .closed = .{ closed_input, closed_output, closed_reopened },
        .input_size = input_stat.size,
        .readv = .{ .vectors = read_vector_count, .results = reads.items },
        .writev = .{ .vectors = write_vector_count, .results = writes.items },
        .allocation = .{ .offset = allocation_offset, .length = allocation_length, .mode = allocation_mode, .result = allocation_cqe.res },
        .statx = .{ .requested_mask = @as(u32, @bitCast(stat_mask)), .size_present = output_stat.mask.SIZE, .type_present = output_stat.mask.TYPE, .regular = output_stat.mode & linux.S.IFMT == linux.S.IFREG, .size = output_stat.size },
        .fsync = syncs,
        .reopened = .{ .bytes = read_back, .sha256 = digest_hex[0..] },
        .invalid_descriptors = failures,
    }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
