const std = @import("std");
const builtin = @import("builtin");
const linux = std.os.linux;
const raw = @import("raw_ops");

pub fn main(init: std.process.Init) !void {
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try std.json.Stringify.value(.{
        .target = .{ .os = @tagName(builtin.os.tag), .arch = @tagName(builtin.cpu.arch), .word_bits = @bitSizeOf(usize), .libc = builtin.link_libc },
        .layouts = .{
            .ring = @tagName(@typeInfo(linux.IoUring).@"struct".layout),
            .sq = @tagName(@typeInfo(linux.IoUring.SubmissionQueue).@"struct".layout),
            .cq = @tagName(@typeInfo(linux.IoUring.CompletionQueue).@"struct".layout),
        },
        .sizes = .{
            .params = @sizeOf(linux.io_uring_params),
            .sq_offsets = @sizeOf(linux.io_sqring_offsets),
            .cq_offsets = @sizeOf(linux.io_cqring_offsets),
            .sqe = @sizeOf(linux.io_uring_sqe),
            .cqe = @sizeOf(linux.io_uring_cqe),
            .timespec = @sizeOf(linux.kernel_timespec),
            .sigset = @sizeOf(linux.sigset_t),
            .iovec = @sizeOf(std.posix.iovec),
            .iovec_const = @sizeOf(std.posix.iovec_const),
            .msghdr = @sizeOf(linux.msghdr),
            .msghdr_const = @sizeOf(linux.msghdr_const),
            .sockaddr = @sizeOf(linux.sockaddr),
            .ipv4 = @sizeOf(linux.sockaddr.in),
            .socklen = @sizeOf(linux.socklen_t),
            .statx = @sizeOf(linux.Statx),
            .open_how = @sizeOf(raw.OpenHow),
        },
        .integers = .{
            .off_t = @typeName(linux.off_t),
            .mode_t = @typeName(std.posix.mode_t),
            .statx_mode = @typeName(@FieldType(linux.Statx, "mode")),
            .sqe_offset = @typeName(@FieldType(linux.io_uring_sqe, "off")),
            .sqe_length = @typeName(@FieldType(linux.io_uring_sqe, "len")),
            .socklen = @typeName(linux.socklen_t),
            .timespec_sec = @typeName(@FieldType(linux.kernel_timespec, "sec")),
            .timespec_nsec = @typeName(@FieldType(linux.kernel_timespec, "nsec")),
            .vector_length = @typeName(@FieldType(std.posix.iovec, "len")),
        },
        .constness = .{
            .read_bytes = @typeInfo(@FieldType(std.posix.iovec, "base")).pointer.is_const,
            .write_bytes = @typeInfo(@FieldType(std.posix.iovec_const, "base")).pointer.is_const,
            .receive_vectors = @typeInfo(@FieldType(linux.msghdr, "iov")).pointer.is_const,
            .send_vectors = @typeInfo(@FieldType(linux.msghdr_const, "iov")).pointer.is_const,
        },
        .current_offset_bits = @as(u64, @bitCast(@as(i64, -1))),
    }, .{}, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
