const std = @import("std");
const linux = std.os.linux;

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len < 2 or args.len > 3) return error.ExpectedOutputPath;
    const fail_read = args.len == 3 and std.mem.eql(u8, args[2], "--fail-read");
    if (args.len == 3 and !fail_read) return error.UnknownOption;
    const file = try std.Io.Dir.cwd().createFile(init.io, args[1], .{ .read = !fail_read });
    var closed = false;
    defer if (!closed) {};
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    const message = "Hello, io_uring!";
    var data: [message.len]u8 = undefined;
    const write_sqe = try ring.write(1, file.handle, message, 0);
    write_sqe.flags |= linux.IOSQE_IO_LINK;
    const read_sqe = try ring.read(2, file.handle, .{ .buffer = &data }, 0);
    read_sqe.flags |= linux.IOSQE_IO_LINK;
    _ = try ring.close(3, file.handle);
    _ = try ring.submit();
    var results: [3]i32 = undefined;
    var seen = [_]bool{ false, false, false };
    for (0..3) |_| {
        const cqe = try ring.copy_cqe();
        if (cqe.user_data < 1 or cqe.user_data > 3) return error.UnexpectedCompletion;
        const id: usize = @intCast(cqe.user_data - 1);
        if (seen[id]) return error.DuplicateCompletion;
        seen[id] = true;
        results[id] = cqe.res;
        if (id == 2 and cqe.res == 0) closed = true;
    }
    if (!fail_read and (results[0] != message.len or results[1] != message.len or results[2] != 0))
        return error.LinkedOperationsFailed;
    var buffer: [4096]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &buffer);
    try stdout.interface.print("{{\"results\":[{d},{d},{d}],\"data\":\"{s}\"}}\n", .{
        results[0], results[1], results[2], if (fail_read) "" else data[0..],
    });
    try stdout.interface.flush();
}
