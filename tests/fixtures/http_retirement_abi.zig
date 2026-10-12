const std = @import("std");
const linux = std.os.linux;

pub fn main(init: std.process.Init) !void {
    var buffer: [2048]u8 = undefined;
    var output = std.Io.File.stdout().writerStreaming(init.io, &buffer);
    try output.interface.print("{{\"sqe_size\":{d},\"cqe_size\":{d},\"sqe\":{{\"opcode\":{d},\"fd\":{d},\"addr\":{d},\"len\":{d},\"tag\":{d}}},\"cqe\":{{\"tag\":{d},\"res\":{d},\"flags\":{d}}},\"ops\":{{\"READ\":{d},\"SEND\":{d},\"ACCEPT\":{d},\"ASYNC_CANCEL\":{d},\"NOP\":{d}}}}}\n", .{
        @sizeOf(linux.io_uring_sqe),                @sizeOf(linux.io_uring_cqe),
        @offsetOf(linux.io_uring_sqe, "opcode"),    @offsetOf(linux.io_uring_sqe, "fd"),
        @offsetOf(linux.io_uring_sqe, "addr"),      @offsetOf(linux.io_uring_sqe, "len"),
        @offsetOf(linux.io_uring_sqe, "user_data"), @offsetOf(linux.io_uring_cqe, "user_data"),
        @offsetOf(linux.io_uring_cqe, "res"),       @offsetOf(linux.io_uring_cqe, "flags"),
        @backingInt(linux.IORING_OP.READ),          @backingInt(linux.IORING_OP.SEND),
        @backingInt(linux.IORING_OP.ACCEPT),        @backingInt(linux.IORING_OP.ASYNC_CANCEL),
        @backingInt(linux.IORING_OP.NOP),
    });
    try output.interface.flush();
}
