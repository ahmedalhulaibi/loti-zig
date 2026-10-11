const std = @import("std");
const linux = std.os.linux;
const Command = enum { read, provide, remove };
const default_plan = [_]Command{ .read, .read, .provide, .read, .provide, .remove, .read, .provide, .read };
const Cqe = struct { tag: u64, result: i32, flags: u32, buffer_id: ?u16, no_buffer_selected: bool };
const Step = struct { command: Command, cqe: Cqe, available: bool, storage: [64]u8 };

fn describe(cqe: linux.io_uring_cqe) Cqe {
    const identity: ?u16 = cqe.buffer_id() catch null;
    return .{ .tag = cqe.user_data, .result = cqe.res, .flags = cqe.flags, .buffer_id = identity, .no_buffer_selected = identity == null };
}

fn finish(ring: *linux.IoUring, tag: u64) !Cqe {
    if (try ring.submit_and_wait(1) != 1) return error.UnexpectedSubmissionCount;
    const cqe = try ring.copy_cqe();
    if (cqe.user_data != tag) return error.UnexpectedBufferCompletion;
    return describe(cqe);
}

fn expectPlain(cqe: Cqe, result: i32) !void {
    if (cqe.result != result or cqe.flags != 0 or cqe.buffer_id != null or !cqe.no_buffer_selected)
        return error.UnexpectedPlainBufferCompletion;
}

fn readSelected(ring: *linux.IoUring, tag: u64, fd: linux.fd_t, group: u16) !Cqe {
    _ = try ring.read(tag, fd, .{ .buffer_selection = .{ .group_id = group, .len = 64 } }, 0);
    return finish(ring, tag);
}

fn expectSelected(cqe: Cqe, identity: u16) !void {
    if (cqe.result <= 0 or cqe.result > 64 or cqe.buffer_id != identity or cqe.no_buffer_selected or
        cqe.flags != (@as(u32, identity) << 16) | linux.IORING_CQE_F_BUFFER)
        return error.UnexpectedSelectedBufferCompletion;
}

fn parsePlan(args: []const []const u8, allocator: std.mem.Allocator) ![]const Command {
    if (args.len == 0) return &default_plan;
    const plan = try allocator.alloc(Command, args.len);
    var available = true;
    for (args, plan) |arg, *command| {
        command.* = std.meta.stringToEnum(Command, arg) orelse return error.UnknownBufferCommand;
        switch (command.*) {
            .read => available = false,
            .provide => {
                if (available) return error.BufferAlreadyProvided;
                available = true;
            },
            .remove => {
                if (!available) return error.NoBufferToRemove;
                available = false;
            },
        }
    }
    return plan;
}

const ZeroName = enum { provide, eof, remove_consumed_eof, eof_exhausted, provide_for_zero_length, zero_length_read, remove_consumed_zero_length, zero_length_exhausted, provide_for_data, read, provide_for_cleanup, remove_final, eof_after_remove };
const ZeroRequest = struct { operation: linux.IORING_OP, tag: u64, descriptor: enum { input, count }, count: ?i32, offset: u64, length: u32, flags: u8, group: u16 };
const ZeroStep = struct { name: ZeroName, request: ZeroRequest, cqe: Cqe, storage: [64]u8 };

fn zeroPosition(fd: linux.fd_t) !u64 {
    const result = linux.lseek(fd, 0, linux.SEEK.CUR);
    if (linux.errno(result) != .SUCCESS) return error.BufferZeroPositionQueryFailed;
    return result;
}

fn zeroStep(ring: *linux.IoUring, sqe: *const linux.io_uring_sqe, fd: linux.fd_t, name: ZeroName, storage: *const [64]u8) !ZeroStep {
    const read = sqe.opcode == .READ;
    if (read and sqe.fd != fd) return error.InvalidBufferZeroReadDescriptor;
    const request: ZeroRequest = .{ .operation = sqe.opcode, .tag = sqe.user_data, .descriptor = if (read) .input else .count, .count = if (read) null else sqe.fd, .offset = sqe.off, .length = sqe.len, .flags = sqe.flags, .group = sqe.buf_index };
    const cqe = try finish(ring, request.tag);
    switch (name) {
        .eof => {
            if (cqe.result != 0 or cqe.flags != (@as(u32, 257) << 16) | linux.IORING_CQE_F_BUFFER or cqe.buffer_id != 257 or cqe.no_buffer_selected)
                return error.UnexpectedBufferZeroSelection;
        },
        .read, .zero_length_read => try expectSelected(cqe, 257),
        .eof_exhausted, .zero_length_exhausted, .eof_after_remove => try expectPlain(cqe, -@as(i32, @backingInt(linux.E.NOBUFS))),
        .remove_final => try expectPlain(cqe, 1),
        .provide, .provide_for_zero_length, .provide_for_data, .provide_for_cleanup, .remove_consumed_eof, .remove_consumed_zero_length => try expectPlain(cqe, 0),
    }
    return .{ .name = name, .request = request, .cqe = cqe, .storage = storage.* };
}

const ZeroMode = enum { observe, fail_eof };

fn zeroResults(io: std.Io, fd: linux.fd_t, size: u64, mode: ZeroMode) !void {
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var storage: [64]u8 = @splat(165);
    const before = try zeroPosition(fd);
    var steps: [13]ZeroStep = undefined;
    steps[0] = try zeroStep(&ring, try ring.provide_buffers(1, &storage, 64, 1, 7, 257), fd, .provide, &storage);
    const eof_fd = if (mode == .fail_eof) -1 else fd;
    steps[1] = try zeroStep(&ring, try ring.read(2, eof_fd, .{ .buffer_selection = .{ .group_id = 7, .len = 64 } }, size), eof_fd, .eof, &storage);
    steps[2] = try zeroStep(&ring, try ring.remove_buffers(3, 1, 7), fd, .remove_consumed_eof, &storage);
    steps[3] = try zeroStep(&ring, try ring.read(4, fd, .{ .buffer_selection = .{ .group_id = 7, .len = 64 } }, size), fd, .eof_exhausted, &storage);
    @memset(&storage, 165);
    steps[4] = try zeroStep(&ring, try ring.provide_buffers(5, &storage, 64, 1, 7, 257), fd, .provide_for_zero_length, &storage);
    steps[5] = try zeroStep(&ring, try ring.read(6, fd, .{ .buffer_selection = .{ .group_id = 7, .len = 0 } }, 0), fd, .zero_length_read, &storage);
    steps[6] = try zeroStep(&ring, try ring.remove_buffers(7, 1, 7), fd, .remove_consumed_zero_length, &storage);
    steps[7] = try zeroStep(&ring, try ring.read(8, fd, .{ .buffer_selection = .{ .group_id = 7, .len = 0 } }, 0), fd, .zero_length_exhausted, &storage);
    @memset(&storage, 165);
    steps[8] = try zeroStep(&ring, try ring.provide_buffers(9, &storage, 64, 1, 7, 257), fd, .provide_for_data, &storage);
    steps[9] = try zeroStep(&ring, try ring.read(10, fd, .{ .buffer_selection = .{ .group_id = 7, .len = 64 } }, 0), fd, .read, &storage);
    @memset(&storage, 165);
    steps[10] = try zeroStep(&ring, try ring.provide_buffers(11, &storage, 64, 1, 7, 257), fd, .provide_for_cleanup, &storage);
    steps[11] = try zeroStep(&ring, try ring.remove_buffers(12, 1, 7), fd, .remove_final, &storage);
    steps[12] = try zeroStep(&ring, try ring.read(13, fd, .{ .buffer_selection = .{ .group_id = 7, .len = 64 } }, size), fd, .eof_after_remove, &storage);
    const count: i32 = @intCast(@min(size, 64));
    const no_buffers = -@as(i32, @backingInt(linux.E.NOBUFS));
    const results = [_]i32{ 0, 0, 0, no_buffers, 0, count, 0, no_buffers, 0, count, 0, 1, no_buffers };
    for (steps, results, 0..) |step, result, index| {
        if (index == 1 or index == 5 or index == 9) {
            if (step.cqe.result != result or step.cqe.flags != (@as(u32, 257) << 16) | linux.IORING_CQE_F_BUFFER or step.cqe.buffer_id != 257 or step.cqe.no_buffer_selected)
                return error.UnexpectedBufferZeroSelection;
        } else {
            try expectPlain(step.cqe, result);
        }
    }
    const after = try zeroPosition(fd);
    if (before != 0 or after != before) return error.BufferZeroChangedFileCursor;
    if (ring.sq_ready() != 0 or ring.cq_ready() != 0) return error.BufferZeroQueueNotDrained;
    var output: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(io, &output);
    try std.json.Stringify.value(.{ .group = @as(u16, 7), .id = @as(u16, 257), .input_size = size, .cursor_before = before, .cursor_after = after, .steps = steps, .queued = ring.sq_ready(), .cq_ready = ring.cq_ready() }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len < 2 or args.len > 34) return error.ExpectedInputAndBufferCommands;
    const zero_mode = args.len >= 3 and std.mem.eql(u8, args[2], "--zero-result");
    const fail_eof = zero_mode and args.len == 4 and std.mem.eql(u8, args[3], "--fail-eof");
    if (zero_mode and args.len != 3 and !fail_eof) return error.BufferZeroModeNeedsNoCommands;
    const plan = if (zero_mode) &.{} else try parsePlan(args[2..], allocator);
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    const stat = try file.stat(init.io);
    if (stat.kind != .file or stat.size == 0) return error.ExpectedNonemptyRegularInput;
    if (zero_mode) {
        if (stat.size > 4097) return error.BufferZeroInputTooLarge;
        return zeroResults(init.io, file.handle, stat.size, if (fail_eof) .fail_eof else .observe);
    }
    var memory: [256]u8 = @splat(165);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();

    const provided = try ring.provide_buffers(1, memory[128..].ptr, 64, 2, 12, 1000);
    const provided_count = provided.fd;
    const provided_size = provided.len;
    const provided_group = provided.buf_index;
    const provided_first = provided.off;
    const multiple_provide = try finish(&ring, 1);
    try expectPlain(multiple_provide, 0);
    _ = try ring.remove_buffers(2, 3, 12);
    const multiple_remove = try finish(&ring, 2);
    try expectPlain(multiple_remove, 2);
    const after_remove = try readSelected(&ring, 3, file.handle, 12);
    try expectPlain(after_remove, -@as(i32, @backingInt(linux.E.NOBUFS)));
    const multiple_storage: [128]u8 = memory[128..256].*;

    _ = try ring.provide_buffers(4, memory[64..128].ptr, 64, 1, 9, 513);
    const isolated_provide = try finish(&ring, 4);
    try expectPlain(isolated_provide, 0);
    const wrong_group = try readSelected(&ring, 5, file.handle, 8);
    try expectPlain(wrong_group, -@as(i32, @backingInt(linux.E.NOBUFS)));
    const isolated_read = try readSelected(&ring, 6, file.handle, 9);
    try expectSelected(isolated_read, 513);
    const isolated_empty = try readSelected(&ring, 7, file.handle, 9);
    try expectPlain(isolated_empty, -@as(i32, @backingInt(linux.E.NOBUFS)));
    const isolated_storage: [64]u8 = memory[64..128].*;

    _ = try ring.provide_buffers(8, &memory, 64, 1, 7, 257);
    const initial = try finish(&ring, 8);
    try expectPlain(initial, 0);
    var available = true;
    const steps = try allocator.alloc(Step, plan.len);
    for (plan, steps, 0..) |command, *step, index| {
        const tag = 100 + index;
        const cqe = switch (command) {
            .read => blk: {
                const result = try readSelected(&ring, tag, file.handle, 7);
                if (available) {
                    try expectSelected(result, 257);
                } else {
                    try expectPlain(result, -@as(i32, @backingInt(linux.E.NOBUFS)));
                }
                available = false;
                break :blk result;
            },
            .provide => blk: {
                if (available) return error.BufferAlreadyProvided;
                @memset(memory[0..64], 165);
                _ = try ring.provide_buffers(tag, &memory, 64, 1, 7, 257);
                const result = try finish(&ring, tag);
                try expectPlain(result, 0);
                available = true;
                break :blk result;
            },
            .remove => blk: {
                if (!available) return error.NoBufferToRemove;
                _ = try ring.remove_buffers(tag, 1, 7);
                const result = try finish(&ring, tag);
                try expectPlain(result, 1);
                available = false;
                break :blk result;
            },
        };
        step.* = .{ .command = command, .cqe = cqe, .available = available, .storage = memory[0..64].* };
    }
    var cleanup: ?Cqe = null;
    if (available) {
        _ = try ring.remove_buffers(200, 1, 7);
        cleanup = try finish(&ring, 200);
        try expectPlain(cleanup.?, 1);
        available = false;
    }

    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try std.json.Stringify.value(.{
        .multiple = .{ .provide = multiple_provide, .remove = multiple_remove, .after_remove = after_remove, .count = provided_count, .size = provided_size, .group = provided_group, .first_id = provided_first, .storage = multiple_storage },
        .isolation = .{ .provide = isolated_provide, .wrong_group = wrong_group, .selected = isolated_read, .exhausted = isolated_empty, .storage = isolated_storage },
        .initial = initial,
        .selection_group = 7,
        .selection_id = 257,
        .steps = steps,
        .cleanup = cleanup,
        .final_available = available,
    }, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
