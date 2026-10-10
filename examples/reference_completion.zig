const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

pub fn main(init: std.process.Init) !void {
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
    var buffer: [1024]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &buffer);
    try stdout.interface.print("{{\"empty\":{d},\"pending\":{d},\"space\":{d},\"copied\":[{d},{d},{d},{d}],\"manual\":[{d},{d},{d},{d}],\"drained\":{d},\"timed_out\":{s},\"timer_result\":{d}}}\n", .{
        empty,     pending,   space,     tags[0],   tags[1], tags[2],                            tags[3],
        manual[0], manual[1], manual[2], manual[3], drained, if (timed_out) "true" else "false", timer.res,
    });
    try stdout.interface.flush();
}
