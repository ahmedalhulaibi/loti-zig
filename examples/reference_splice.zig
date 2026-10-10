const std = @import("std");
const linux = std.os.linux;
const current = std.math.maxInt(u64);
const nonblock = 2; // Linux SPLICE_F_NONBLOCK; not an IOSQE flag.

const Pipe = struct {
    fd: [2]linux.fd_t,
    owned: [2]bool = .{ true, true },

    fn init() !Pipe {
        var pair: [2]linux.fd_t = undefined;
        if (linux.errno(linux.pipe2(&pair, .{ .CLOEXEC = true, .NONBLOCK = true })) != .SUCCESS) return error.SplicePipeCreationFailed;
        var pipe: Pipe = .{ .fd = pair };
        errdefer pipe.deinit();
        const capacity = linux.fcntl(pair[1], linux.F.SETPIPE_SZ, 4096);
        if (linux.errno(capacity) != .SUCCESS) return error.SplicePipeSizingFailed;
        if (capacity != 4096 or linux.fcntl(pair[0], linux.F.GETPIPE_SZ, 0) != 4096) return error.SpliceNeeds4096BytePipes;
        return pipe;
    }

    fn deinit(self: *Pipe) void {
        for (self.fd, self.owned) |fd, owned| {
            if (owned) _ = linux.close(fd);
        }
    }

    fn close(self: *Pipe) ![2]bool {
        for (self.fd, 0..) |fd, index| {
            if (linux.errno(linux.close(fd)) != .SUCCESS) return error.SplicePipeCloseFailed;
            self.owned[index] = false;
        }
        var closed: [2]bool = undefined;
        for (self.fd, 0..) |fd, index| {
            closed[index] = linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) == .BADF;
            if (!closed[index]) return error.SplicePipeDescriptorStillOpen;
        }
        return closed;
    }
};

const Phase = enum { fill, relay, eof, current, fill_output_explicit, output_explicit, fill_output_current, output_current, invalid_source, empty_pipe, input_offset, output_offset, same_pipe, no_pipe };
const Splice = struct { tag: u64, phase: Phase, input_offset: u64, output_offset: u64, requested: u32, operation_flags: u32, result: i32, flags: u32 };
const Read = struct { tag: u64, offset: u64, requested: u32, result: i32, flags: u32 };

fn completion(ring: *linux.IoUring, tag: u64) !linux.io_uring_cqe {
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedSpliceSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag or cqe.flags != 0) return error.UnexpectedSpliceCompletion;
    return cqe;
}

fn transfer(ring: *linux.IoUring, tag: u64, phase: Phase, fd_in: linux.fd_t, off_in: u64, fd_out: linux.fd_t, off_out: u64, length: usize) !Splice {
    const sqe = try ring.splice(tag, fd_in, off_in, fd_out, off_out, length);
    sqe.rw_flags = nonblock;
    if (sqe.opcode != .SPLICE) return error.ExpectedSpliceOpcode;
    var report: Splice = .{ .tag = sqe.user_data, .phase = phase, .input_offset = sqe.addr, .output_offset = sqe.off, .requested = sqe.len, .operation_flags = sqe.rw_flags, .result = 0, .flags = 0 };
    const cqe = try completion(ring, tag);
    report.result = cqe.res;
    report.flags = cqe.flags;
    return report;
}

fn drain(ring: *linux.IoUring, tag: u64, fd: linux.fd_t, buffer: []u8, read_offset: u64) !Read {
    const sqe = try ring.read(tag, fd, .{ .buffer = buffer }, read_offset);
    const requested = sqe.len;
    const offset = sqe.off;
    const cqe = try completion(ring, tag);
    if (cqe.res != buffer.len) return error.SpliceDrainIncomplete;
    return .{ .tag = cqe.user_data, .offset = offset, .requested = requested, .result = cqe.res, .flags = cqe.flags };
}

fn position(fd: linux.fd_t, offset: linux.off_t, whence: u32) !u64 {
    const result = linux.lseek(fd, offset, whence);
    if (linux.errno(result) != .SUCCESS) return error.SplicePositionQueryFailed;
    return result;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len != 2) return error.ExpectedSpliceInput;
    const path = try allocator.dupeSentinel(u8, args[1], 0);
    const opened = linux.open(path, .{ .ACCMODE = .RDONLY, .CLOEXEC = true, .NOFOLLOW = true, .NONBLOCK = true }, 0);
    if (linux.errno(opened) != .SUCCESS) return error.SpliceInputOpenFailed;
    const fd: linux.fd_t = @intCast(opened);
    defer _ = linux.close(fd);
    const source: std.Io.File = .{ .handle = fd, .flags = .{ .nonblocking = true } };
    const stat = try source.stat(init.io);
    if (stat.kind != .file) return error.ExpectedRegularSpliceInput;
    if (stat.size > 1024 * 1024) return error.SpliceInputTooLarge;
    var first = try Pipe.init();
    defer first.deinit();
    var second = try Pipe.init();
    defer second.deinit();
    const memory_file = linux.memfd_create("loti-splice", linux.MFD.CLOEXEC);
    if (linux.errno(memory_file) != .SUCCESS) return error.SpliceMemoryFileCreationFailed;
    const regular_output: linux.fd_t = @intCast(memory_file);
    defer _ = linux.close(regular_output);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();

    const before = try position(fd, 7, linux.SEEK.SET);
    var splices: std.ArrayList(Splice) = .empty;
    var reads: std.ArrayList(Read) = .empty;
    var data: std.ArrayList(u8) = .empty;
    var memory: [4096]u8 = undefined;
    var offset: u64 = 0;
    var tag: u64 = 10;
    while (offset < stat.size) {
        const requested: usize = @intCast(@min(8192, stat.size - offset));
        const filled = try transfer(&ring, tag, .fill, fd, offset, first.fd[1], current, requested);
        if (filled.result <= 0 or filled.result > requested or filled.result > memory.len) return error.InvalidSpliceFillProgress;
        const count: usize = @intCast(filled.result);
        const relayed = try transfer(&ring, tag + 1, .relay, first.fd[0], current, second.fd[1], current, count);
        if (relayed.result != count) return error.SpliceRelayIncomplete;
        const observed = try drain(&ring, tag + 2, second.fd[0], memory[0..count], current);
        try splices.appendSlice(allocator, &.{ filled, relayed });
        try reads.append(allocator, observed);
        try data.appendSlice(allocator, memory[0..count]);
        offset += count;
        tag += 3;
    }
    const eof = try transfer(&ring, 1000000, .eof, fd, stat.size, first.fd[1], current, 1);
    if (eof.result != 0) return error.SpliceEofMissing;
    const after = try position(fd, 0, linux.SEEK.CUR);
    if (after != before) return error.ExplicitSpliceChangedPosition;
    const current_before = try position(fd, 0, linux.SEEK.SET);
    const current_splice = try transfer(&ring, 1000001, .current, fd, current, second.fd[1], current, 64);
    if (current_splice.result < 0 or current_splice.result > 64) return error.CurrentPositionSpliceFailed;
    var prefix: [64]u8 = undefined;
    const prefix_size: usize = @intCast(current_splice.result);
    const current_read = try drain(&ring, 1000002, second.fd[0], prefix[0..prefix_size], current);
    const current_after = try position(fd, 0, linux.SEEK.CUR);
    if (current_after != prefix_size) return error.CurrentSplicePositionMismatch;

    const destination_before = try position(regular_output, 7, linux.SEEK.SET);
    const output_fill_explicit = try transfer(&ring, 1000030, .fill_output_explicit, fd, 0, first.fd[1], current, 64);
    const output_explicit = try transfer(&ring, 1000031, .output_explicit, first.fd[0], current, regular_output, 11, prefix_size);
    const destination_after = try position(regular_output, 0, linux.SEEK.CUR);
    if (output_fill_explicit.result != prefix_size or output_explicit.result != prefix_size or destination_after != destination_before) return error.ExplicitSpliceOutputFailed;
    const destination_current_before = try position(regular_output, 0, linux.SEEK.SET);
    const output_fill_current = try transfer(&ring, 1000032, .fill_output_current, fd, 0, first.fd[1], current, 64);
    const output_current = try transfer(&ring, 1000033, .output_current, first.fd[0], current, regular_output, current, prefix_size);
    const destination_current_after = try position(regular_output, 0, linux.SEEK.CUR);
    if (output_fill_current.result != prefix_size or output_current.result != prefix_size or destination_current_after != prefix_size) return error.CurrentSpliceOutputFailed;
    const output_file: std.Io.File = .{ .handle = regular_output, .flags = .{ .nonblocking = false } };
    const output_stat = try output_file.stat(init.io);
    if (output_stat.size > 75) return error.SpliceOutputSizeOutOfBounds;
    var destination: [75]u8 = undefined;
    const destination_size: usize = @intCast(output_stat.size);
    const destination_read = try drain(&ring, 1000034, regular_output, destination[0..destination_size], 0);
    const destination_after_observation = try position(regular_output, 0, linux.SEEK.CUR);
    if (destination_after_observation != destination_current_after) return error.PositionalSpliceObservationChangedCursor;

    const failures = [_]Splice{
        try transfer(&ring, 1000010, .invalid_source, -1, 0, first.fd[1], current, 1),
        try transfer(&ring, 1000011, .empty_pipe, first.fd[0], current, second.fd[1], current, 1),
        try transfer(&ring, 1000012, .input_offset, first.fd[0], 0, second.fd[1], current, 1),
        try transfer(&ring, 1000013, .output_offset, fd, 0, first.fd[1], 0, 1),
        try transfer(&ring, 1000014, .same_pipe, first.fd[0], current, first.fd[1], current, 1),
        try transfer(&ring, 1000015, .no_pipe, fd, 0, regular_output, 0, 1),
    };
    const expected = [_]i32{ -9, -11, -29, -29, -22, -22 };
    for (failures, expected) |observed, result| {
        if (observed.result != result) return error.UnexpectedSpliceFailureResult;
    }
    const first_closed = try first.close();
    const second_closed = try second.close();
    const source_still_open = linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) == .SUCCESS;
    if (!source_still_open) return error.SpliceSourceDescriptorClosedEarly;
    var output_buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &output_buffer);
    try std.json.Stringify.value(.{
        .source_size = stat.size,
        .capacities = .{ @as(u32, 4096), @as(u32, 4096) },
        .explicit = .{ .position_before = before, .position_after = after, .splices = splices.items, .reads = reads.items, .data = data.items },
        .eof = eof,
        .current = .{ .position_before = current_before, .position_after = current_after, .splice = current_splice, .read = current_read, .data = prefix[0..prefix_size] },
        .destination = .{ .explicit_before = destination_before, .explicit_after = destination_after, .current_before = destination_current_before, .current_after = destination_current_after, .after_observation = destination_after_observation, .splices = .{ output_fill_explicit, output_explicit, output_fill_current, output_current }, .read = destination_read, .data = destination[0..destination_size] },
        .failures = failures,
        .pipes_closed = first_closed ++ second_closed,
        .source_still_open = source_still_open,
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
