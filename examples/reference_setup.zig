const std = @import("std");
const linux = std.os.linux;
const RawRing = @import("raw_cat.zig").RawRing;
const support = @import("support.zig");
const Mapping = []align(std.heap.page_size_min) u8;

fn pagesHaveState(regions: [3]?Mapping, expected: linux.E, page_size: usize) bool {
    for (regions) |region| {
        const memory = region orelse continue;
        var offset: usize = 0;
        while (offset < memory.len) : (offset += page_size) {
            var state: [1]u8 = undefined;
            if (linux.errno(linux.mincore(memory.ptr + offset, page_size, &state)) != expected) return false;
        }
    }
    return true;
}

fn verifyForkExclusion(regions: [3]?Mapping, fd: linux.fd_t, page_size: usize) !void {
    const child = linux.fork();
    if (linux.errno(child) != .SUCCESS) return error.ForkFailed;
    if (child == 0) {
        // The post-fork child uses only raw syscalls: no inherited allocator or I/O locks.
        if (!pagesHaveState(regions, .NOMEM, page_size)) linux.exit(2);
        if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .SUCCESS) linux.exit(3);
        linux.exit(0);
    }
    var status: i32 = undefined;
    while (true) {
        const waited = linux.waitpid(@intCast(child), &status, 0);
        switch (linux.errno(waited)) {
            .SUCCESS => break,
            .INTR => continue,
            else => return error.ChildWaitFailed,
        }
    }
    if (status != 0) return error.ForkMappingInheritanceFailed;
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len < 2 or args.len > 3) return error.ExpectedInputFile;
    if (std.mem.eql(u8, args[1], "--mapping-failure")) {
        if (args.len != 3) return error.ExpectedMappingFailureStage;
        return @import("mapping_fault.zig").run(init, args[2]);
    }
    const separate = args.len == 3;
    if (separate and !std.mem.eql(u8, args[2], "--separate-mappings")) return error.UnknownMappingMode;
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    var params = std.mem.zeroInit(linux.io_uring_params, .{ .cq_entries = 32, .flags = linux.IORING_SETUP_CQSIZE });
    var ring = try linux.IoUring.init_params(8, &params);
    defer ring.deinit();
    const sq: *linux.IoUring.SubmissionQueue = &ring.sq;
    const cq: *linux.IoUring.CompletionQueue = &ring.cq;
    var raw_params = std.mem.zeroInit(linux.io_uring_params, .{ .cq_entries = 512, .flags = linux.IORING_SETUP_CQSIZE });
    const opened = linux.io_uring_setup(8, &raw_params);
    if (linux.errno(opened) != .SUCCESS) return error.RingSetupFailed;
    const fd: linux.fd_t = @intCast(opened);
    if (separate) raw_params.features &= ~@as(u32, linux.IORING_FEAT_SINGLE_MMAP);
    var mapped = RawRing.map(fd, raw_params) catch |err| {
        _ = linux.close(fd);
        return err;
    };
    var mapping_owned = true;
    defer if (mapping_owned) mapped.deinit();
    const regions = [3]?Mapping{ mapped.shared, mapped.completion, mapped.entries };
    const mapping_count: u32 = if (mapped.completion == null) 2 else 3;
    const page_size = std.heap.pageSize();
    const cq_memory = mapped.completion orelse mapped.shared;
    const cq_base = @intFromPtr(cq_memory.ptr);
    if (@intFromPtr(mapped.cq_head) != cq_base + raw_params.cq_off.head or
        @intFromPtr(mapped.cq_tail) != cq_base + raw_params.cq_off.tail or
        @intFromPtr(mapped.cqes.ptr) != cq_base + raw_params.cq_off.cqes)
        return error.CompletionPointerRegionMismatch;
    if (!pagesHaveState(regions, .SUCCESS, page_size)) return error.LiveMappingCheckFailed;
    try mapped.dontFork();
    try verifyForkExclusion(regions, fd, page_size);
    var data: [64]u8 = undefined;
    var vecs = [_]std.posix.iovec{.{ .base = &data, .len = data.len }};
    var hash = std.crypto.hash.sha2.Sha256.init(.{});
    var count: usize = 0;
    var total: usize = 0;
    for (0..1025) |iteration| {
        vecs[0].len = if (iteration % 2 == 0) 64 else 31;
        const offset: u64 = if (iteration % 2 == 0) 0 else 64;
        const cqe = try mapped.readv(file.handle, &vecs, offset);
        count = try support.completedBytes(cqe);
        if (cqe.user_data != 1) return error.UnexpectedCompletion;
        if (count > vecs[0].len) return error.CompletionLengthOutOfBounds;
        total += count;
        hash.update(data[0..count]);
    }
    var digest: [32]u8 = undefined;
    hash.final(&digest);
    const digest_hex = std.fmt.bytesToHex(digest, .lower);
    mapped.deinit();
    mapping_owned = false;
    if (!pagesHaveState(regions, .NOMEM, page_size)) return error.MappingNotReleased;
    if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.RingDescriptorNotClosed;
    var output_buffer: [256]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &output_buffer);
    try stdout.interface.print("{{\"sq_entries\":{d},\"cq_entries\":{d},\"sqe_size\":{d},\"cqe_size\":{d},\"raw_read\":{d},\"reads\":1025,\"raw_bytes\":{d},\"raw_sha256\":\"{s}\",\"raw_cq_entries\":{d},\"mapping_count\":{d},\"cq_region_matches\":true,\"dontfork\":true,\"fork_excluded\":true,\"fd_inherited\":true,\"released\":true}}\n", .{
        sq.sqes.len, cq.cqes.len, @sizeOf(linux.io_uring_sqe), @sizeOf(linux.io_uring_cqe), count,
        total,       digest_hex,  raw_params.cq_entries,       mapping_count,
    });
    try stdout.interface.writeAll(data[0..count]);
    try stdout.interface.flush();
}
