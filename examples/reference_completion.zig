const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

const QueueStep = struct {
    capacity: u32,
    before: u32,
    count: u32,
    after: u32,
    head_before: u32,
    head_after: u32,
};

const QueueReport = struct {
    sq_capacity: u32,
    cq_capacity: u32,
    pending_before: u32,
    full_rejected: bool,
    pending_after: u32,
    sq_tail_before: u32,
    sq_tail_after: u32,
    submitted: u32,
    sq_after_submit: u32,
    cq_before: u32,
    head_before: u32,
    steps: []const QueueStep,
    copied: [8]u64,
    drained: u32,
    head_after: u32,
};

fn nonblocking(ring: *linux.IoUring, capacities: []const u32, steps: []QueueStep) !QueueReport {
    if (ring.sq.sqes.len != 8 or ring.sq_ready() != 0 or ring.cq_ready() != 0)
        return error.UnexpectedInitialQueueState;
    for (10..18) |tag| _ = try ring.nop(tag);
    const pending_before = ring.sq_ready();
    const tail_before = ring.sq.sqe_tail;
    const full_rejected = blk: {
        _ = ring.nop(18) catch |err| {
            if (err != error.SubmissionQueueFull) return err;
            break :blk true;
        };
        return error.FullQueueAcceptedRequest;
    };
    const pending_after = ring.sq_ready();
    const tail_after = ring.sq.sqe_tail;
    if (pending_after != pending_before or tail_after != tail_before)
        return error.FullQueueRejectionChangedState;
    const submitted = try ring.submit_and_wait(8);
    const sq_after_submit = ring.sq_ready();
    const cq_before = ring.cq_ready();
    const head_before = ring.cq.head.*;
    if (cq_before != 8) return error.NonblockingCompletionsMissing;
    var batch: [8]linux.io_uring_cqe = undefined;
    var tags: [8]u64 = undefined;
    var used: usize = 0;
    for (capacities, 0..) |capacity, index| {
        const before = ring.cq_ready();
        const head = ring.cq.head.*;
        const count = try ring.copy_cqes(batch[0..capacity], 0);
        steps[index] = .{
            .capacity = capacity,
            .before = before,
            .count = count,
            .after = ring.cq_ready(),
            .head_before = head,
            .head_after = ring.cq.head.*,
        };
        if (count > capacity or used + count > tags.len) return error.NonblockingCopyOutOfBounds;
        for (batch[0..count]) |cqe| {
            if (cqe.res != 0 or cqe.flags != 0) return error.NonblockingNopFailed;
            tags[used] = cqe.user_data;
            used += 1;
        }
    }
    const drained = ring.cq_ready();
    if (used != tags.len or drained != 0) return error.CompletionPlanDidNotDrain;
    std.mem.sort(u64, &tags, {}, std.sort.asc(u64));
    return .{
        .sq_capacity = @intCast(ring.sq.sqes.len),
        .cq_capacity = @intCast(ring.cq.cqes.len),
        .pending_before = pending_before,
        .full_rejected = full_rejected,
        .pending_after = pending_after,
        .sq_tail_before = tail_before,
        .sq_tail_after = tail_after,
        .submitted = submitted,
        .sq_after_submit = sq_after_submit,
        .cq_before = cq_before,
        .head_before = head_before,
        .steps = steps[0..capacities.len],
        .copied = tags,
        .drained = drained,
        .head_after = ring.cq.head.*,
    };
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len > 33) return error.ExpectedCompletionCapacities;
    const defaults = [_]u32{ 0, 1, 3, 8, 1 };
    var capacity_storage: [32]u32 = undefined;
    const capacities: []const u32 = if (args.len == 1) &defaults else blk: {
        var total: u32 = 0;
        for (args[1..], 0..) |argument, index| {
            const capacity = std.fmt.parseInt(u32, argument, 10) catch return error.InvalidCompletionCapacity;
            if (capacity > 8) return error.CompletionCapacityOutOfRange;
            capacity_storage[index] = capacity;
            total += capacity;
        }
        if (total < 8) return error.CompletionPlanDoesNotDrain;
        break :blk capacity_storage[0 .. args.len - 1];
    };
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var batch: [4]linux.io_uring_cqe = undefined;
    const empty = try ring.copy_cqes(&batch, 0);
    for (1..5) |tag| _ = try ring.nop(tag);
    const pending = ring.sq_ready();
    const space = ring.sq.sqes.len - pending;
    _ = try ring.submit_and_wait(4);
    const first = try ring.copy_cqe();
    var tags: [4]u64 = undefined;
    if (first.res != 0) return error.NopFailed;
    tags[0] = first.user_data;
    var used: usize = 1;
    while (used < tags.len) {
        const count = try ring.copy_cqes(batch[0 .. tags.len - used], 1);
        for (batch[0..count]) |cqe| {
            if (cqe.res != 0) return error.NopFailed;
            tags[used] = cqe.user_data;
            used += 1;
        }
    }
    std.mem.sort(u64, &tags, {}, std.sort.asc(u64));
    for (5..9) |tag| _ = try ring.nop(tag);
    _ = try ring.submit_and_wait(4);
    const ready = ring.cq_ready();
    if (ready != 4) return error.CompletionsMissing;
    const head = ring.cq.head.*;
    var manual: [4]u64 = undefined;
    for (0..4) |i| {
        const entry = &ring.cq.cqes[(head +% @as(u32, @intCast(i))) & ring.cq.mask];
        if (entry.res != 0) return error.NopFailed;
        manual[i] = entry.user_data;
    }
    ring.cqe_seen(&ring.cq.cqes[head & ring.cq.mask]);
    ring.cq_advance(3);
    std.mem.sort(u64, &manual, {}, std.sort.asc(u64));
    const drained = ring.cq_ready();
    var mask = std.mem.zeroes(linux.sigset_t);
    const deadline: linux.kernel_timespec = .{ .sec = 0, .nsec = 1_000_000 };
    var timed_out = false;
    raw.wait_with_timeout(&ring, 1, &deadline, &mask) catch |err| {
        if (err != error.WaitTimedOut) return err;
        timed_out = true;
    };
    const duration: linux.kernel_timespec = .{ .sec = 0, .nsec = 1_000_000 };
    _ = try ring.timeout(9, &duration, 0, 0);
    _ = try ring.submit();
    const timer = try ring.copy_cqe();
    if (timer.user_data != 9 or timer.err() != .TIME) return error.TimeoutCompletionInvalid;
    var steps: [32]QueueStep = undefined;
    const queue = try nonblocking(&ring, capacities, &steps);
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try std.json.Stringify.value(.{
        .empty = empty,
        .pending = pending,
        .space = space,
        .copied = tags,
        .manual = manual,
        .drained = drained,
        .timed_out = timed_out,
        .timer_result = timer.res,
        .nonblocking = queue,
    }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
