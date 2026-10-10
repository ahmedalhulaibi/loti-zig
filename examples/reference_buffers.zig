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

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len < 2 or args.len > 34) return error.ExpectedInputAndBufferCommands;
    const plan = try parsePlan(args[2..], allocator);
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    const stat = try file.stat(init.io);
    if (stat.kind != .file or stat.size == 0) return error.ExpectedNonemptyRegularInput;
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
