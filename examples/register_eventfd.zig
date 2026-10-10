const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");

const Listener = struct {
    ring: *linux.IoUring,
    event_fd: linux.fd_t,
    notifications: u64 = 0,
    completion: ?linux.io_uring_cqe = null,
    failed: bool = false,

    fn listen(self: *Listener) void {
        while (true) {
            const bytes = std.mem.asBytes(&self.notifications);
            const result = linux.read(self.event_fd, bytes.ptr, bytes.len);
            if (linux.errno(result) == .INTR) continue;
            if (linux.errno(result) != .SUCCESS or result != bytes.len) {
                self.failed = true;
                return;
            }
            break;
        }
        self.completion = self.ring.copy_cqe() catch {
            self.failed = true;
            return;
        };
    }
};

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedInputFile;
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    const event_result = linux.eventfd(0, linux.EFD.CLOEXEC);
    if (linux.errno(event_result) != .SUCCESS) return error.EventFdCreationFailed;
    const event_fd: linux.fd_t = @intCast(event_result);
    defer _ = linux.close(event_fd);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    try ring.register_eventfd(event_fd);
    var buffer: [512]u8 = undefined;
    _ = try ring.read(1, file.handle, .{ .buffer = &buffer }, 0);
    _ = try ring.submit();
    var listener: Listener = .{ .ring = &ring, .event_fd = event_fd };
    const thread = try std.Thread.spawn(.{}, Listener.listen, .{&listener});
    thread.join();
    if (listener.failed) return error.CompletionListenerFailed;
    const cqe = listener.completion orelse return error.CompletionMissing;
    if (cqe.user_data != 1) return error.UnexpectedCompletion;
    const count = try support.completedBytes(cqe);
    try ring.unregister_eventfd();
    try support.output(init.io, buffer[0..count]);
    var stderr_buffer: [256]u8 = undefined;
    var stderr = std.Io.File.stderr().writer(init.io, &stderr_buffer);
    try stderr.interface.print("{{\"notifications\":{d},\"user_data\":{d},\"result\":{d}}}\n", .{
        listener.notifications, cqe.user_data, cqe.res,
    });
    try stderr.interface.flush();
}
