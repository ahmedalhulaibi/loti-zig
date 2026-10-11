const std = @import("std");
const linux = std.os.linux;

pub const OpenHow = extern struct {
    flags: u64,
    mode: u64 = 0,
    resolve: u64 = 0,
};
pub const resolve_no_symlinks: u64 = 0x04;
pub const resolve_beneath: u64 = 0x08;

pub fn openat2(ring: *linux.IoUring, tag: u64, fd: linux.fd_t, path: [*:0]const u8, how: *const OpenHow) !*linux.io_uring_sqe {
    const sqe = try ring.get_sqe();
    sqe.prep_rw(.OPENAT2, fd, @intFromPtr(path), @sizeOf(OpenHow), @intFromPtr(how));
    sqe.user_data = tag;
    return sqe;
}

pub const sync_wait_before: u32 = 1;
pub const sync_write: u32 = 2;
pub const sync_wait_after: u32 = 4;

pub fn sync_file_range(ring: *linux.IoUring, tag: u64, fd: linux.fd_t, offset: u64, length: u32, flags: u32) !*linux.io_uring_sqe {
    const sqe = try ring.get_sqe();
    sqe.prep_rw(.SYNC_FILE_RANGE, fd, 0, length, offset);
    sqe.rw_flags = flags;
    sqe.user_data = tag;
    return sqe;
}

pub fn fadvise(ring: *linux.IoUring, tag: u64, fd: linux.fd_t, offset: u64, length: u32, advice: u32) !*linux.io_uring_sqe {
    const sqe = try ring.get_sqe();
    sqe.prep_rw(.FADVISE, fd, 0, length, offset);
    sqe.rw_flags = advice;
    sqe.user_data = tag;
    return sqe;
}

pub fn madvise(ring: *linux.IoUring, tag: u64, memory: []u8, advice: u32) !*linux.io_uring_sqe {
    const sqe = try ring.get_sqe();
    sqe.prep_rw(.MADVISE, -1, @intFromPtr(memory.ptr), memory.len, 0);
    sqe.rw_flags = advice;
    sqe.user_data = tag;
    return sqe;
}

pub fn register_personality(ring: *linux.IoUring) !u16 {
    const result = linux.io_uring_register(ring.fd, .REGISTER_PERSONALITY, null, 0);
    if (linux.errno(result) != .SUCCESS) return error.PersonalityRegistrationFailed;
    return @intCast(result);
}

pub fn unregister_personality(ring: *linux.IoUring, id: u16) !void {
    const result = linux.io_uring_register(ring.fd, .UNREGISTER_PERSONALITY, null, id);
    if (linux.errno(result) != .SUCCESS) return error.PersonalityUnregistrationFailed;
}

pub fn probe() !linux.io_uring_probe {
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    return ring.get_probe();
}

pub fn register_probe(ring: *linux.IoUring, result: *linux.io_uring_probe) !void {
    result.* = std.mem.zeroes(linux.io_uring_probe);
    const status = linux.io_uring_register(ring.fd, .REGISTER_PROBE, result, result.ops.len);
    if (linux.errno(status) != .SUCCESS) return error.ProbeRegistrationFailed;
}

pub fn wait_with_timeout(ring: *linux.IoUring, minimum: u32, timeout: *const linux.kernel_timespec, mask: ?*const linux.sigset_t) !void {
    if (ring.cq_ready() >= minimum) return;
    const args: linux.io_uring_getevents_arg = .{
        .sigmask = @intFromPtr(mask),
        .sigmask_sz = if (mask == null) 0 else linux.NSIG / 8,
        .pad = 0,
        .ts = @intFromPtr(timeout),
    };
    const result = linux.syscall6(.io_uring_enter, @as(u32, @bitCast(ring.fd)), 0, minimum, linux.IORING_ENTER_GETEVENTS | linux.IORING_ENTER_EXT_ARG, @intFromPtr(&args), @sizeOf(linux.io_uring_getevents_arg));
    switch (linux.errno(result)) {
        .SUCCESS => {},
        .TIME => return error.WaitTimedOut,
        .INTR => return error.WaitInterrupted,
        else => return error.TimedWaitFailed,
    }
}
