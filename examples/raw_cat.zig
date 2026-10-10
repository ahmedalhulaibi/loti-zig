const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");

pub const RawRing = struct {
    fd: linux.fd_t,
    shared: []align(std.heap.page_size_min) u8,
    entries: []align(std.heap.page_size_min) u8,
    sq_head: *u32,
    sq_tail: *u32,
    sq_mask: u32,
    sq_array: []u32,
    sqes: []linux.io_uring_sqe,
    cq_head: *u32,
    cq_tail: *u32,
    cq_mask: u32,
    cqes: []linux.io_uring_cqe,

    pub fn init(depth: u32) !RawRing {
        var params = std.mem.zeroes(linux.io_uring_params);
        const result = linux.io_uring_setup(depth, &params);
        switch (linux.errno(result)) {
            .SUCCESS => {},
            .PERM => return error.PermissionDenied,
            .NOSYS => return error.SystemOutdated,
            else => return error.RingSetupFailed,
        }
        const fd: linux.fd_t = @intCast(result);
        errdefer _ = linux.close(fd);
        return map(fd, params);
    }

    pub fn map(fd: linux.fd_t, params: linux.io_uring_params) !RawRing {
        if (params.features & linux.IORING_FEAT_SINGLE_MMAP == 0) return error.SingleMappingRequired;
        const shared_size = @max(
            params.sq_off.array + params.sq_entries * @sizeOf(u32),
            params.cq_off.cqes + params.cq_entries * @sizeOf(linux.io_uring_cqe),
        );
        const shared = try std.posix.mmap(
            null,
            shared_size,
            .{ .READ = true, .WRITE = true },
            .{ .TYPE = .SHARED, .POPULATE = true },
            fd,
            linux.IORING_OFF_SQ_RING,
        );
        errdefer std.posix.munmap(shared);
        const entries = try std.posix.mmap(
            null,
            params.sq_entries * @sizeOf(linux.io_uring_sqe),
            .{ .READ = true, .WRITE = true },
            .{ .TYPE = .SHARED, .POPULATE = true },
            fd,
            linux.IORING_OFF_SQES,
        );
        errdefer std.posix.munmap(entries);
        const array: [*]u32 = @ptrCast(@alignCast(&shared[params.sq_off.array]));
        const sqes: [*]linux.io_uring_sqe = @ptrCast(@alignCast(entries.ptr));
        const cqes: [*]linux.io_uring_cqe = @ptrCast(@alignCast(&shared[params.cq_off.cqes]));
        return .{
            .fd = fd,
            .shared = shared,
            .entries = entries,
            .sq_head = @ptrCast(@alignCast(&shared[params.sq_off.head])),
            .sq_tail = @ptrCast(@alignCast(&shared[params.sq_off.tail])),
            .sq_mask = @as(*u32, @ptrCast(@alignCast(&shared[params.sq_off.ring_mask]))).*,
            .sq_array = array[0..params.sq_entries],
            .sqes = sqes[0..params.sq_entries],
            .cq_head = @ptrCast(@alignCast(&shared[params.cq_off.head])),
            .cq_tail = @ptrCast(@alignCast(&shared[params.cq_off.tail])),
            .cq_mask = @as(*u32, @ptrCast(@alignCast(&shared[params.cq_off.ring_mask]))).*,
            .cqes = cqes[0..params.cq_entries],
        };
    }

    pub fn deinit(self: *RawRing) void {
        std.posix.munmap(self.entries);
        std.posix.munmap(self.shared);
        _ = linux.close(self.fd);
    }

    pub fn dontFork(self: *RawRing) !void {
        if (linux.errno(linux.madvise(self.shared.ptr, self.shared.len, linux.MADV.DONTFORK)) != .SUCCESS)
            return error.SharedMappingAdviceFailed;
        if (linux.errno(linux.madvise(self.entries.ptr, self.entries.len, linux.MADV.DONTFORK)) != .SUCCESS)
            return error.EntryMappingAdviceFailed;
    }

    pub fn readv(self: *RawRing, fd: linux.fd_t, vecs: []const std.posix.iovec, offset: u64) !linux.io_uring_cqe {
        const tail = self.sq_tail.*;
        const head = @atomicLoad(u32, self.sq_head, .acquire);
        if (tail -% head >= self.sqes.len) return error.SubmissionQueueFull;
        const index = tail & self.sq_mask;
        self.sqes[index].prep_readv(fd, vecs, offset);
        self.sqes[index].user_data = 1;
        self.sq_array[index] = index;
        @atomicStore(u32, self.sq_tail, tail +% 1, .release);
        while (true) {
            const completion_head = self.cq_head.*;
            const completion_tail = @atomicLoad(u32, self.cq_tail, .acquire);
            if (completion_head != completion_tail) {
                const cqe = self.cqes[completion_head & self.cq_mask];
                @atomicStore(u32, self.cq_head, completion_head +% 1, .release);
                return cqe;
            }
            const pending = self.sq_tail.* -% @atomicLoad(u32, self.sq_head, .acquire);
            const result = linux.io_uring_enter(self.fd, pending, 1, linux.IORING_ENTER_GETEVENTS, null);
            switch (linux.errno(result)) {
                .SUCCESS, .INTR => {},
                else => return error.RingEnterFailed,
            }
        }
    }
};

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len < 2) return error.ExpectedInputFiles;
    var ring = try RawRing.init(8);
    defer ring.deinit();
    for (args[1..]) |path| {
        const file = try std.Io.Dir.cwd().openFile(init.io, path, .{});
        defer file.close(init.io);
        var blocks: [2][2048]u8 = undefined;
        const vecs = [_]std.posix.iovec{
            .{ .base = &blocks[0], .len = blocks[0].len },
            .{ .base = &blocks[1], .len = blocks[1].len },
        };
        var offset: u64 = 0;
        while (true) {
            const cqe = try ring.readv(file.handle, &vecs, offset);
            if (cqe.user_data != 1) return error.UnexpectedCompletion;
            if (cqe.err() == .INTR or cqe.err() == .AGAIN) continue;
            const count = try support.completedBytes(cqe);
            if (count == 0) break;
            const first = @min(count, blocks[0].len);
            try support.output(init.io, blocks[0][0..first]);
            if (count > first) try support.output(init.io, blocks[1][0 .. count - first]);
            offset += count;
        }
    }
}
