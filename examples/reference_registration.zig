const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 2) return error.ExpectedInputFile;
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var memory: [4096]u8 = undefined;
    const vectors = [_]std.posix.iovec{.{ .base = &memory, .len = memory.len }};
    try ring.register_buffers(&vectors);
    try ring.unregister_buffers();
    const files = [_]linux.fd_t{file.handle};
    try ring.register_files(&files);
    try ring.register_files_update(0, &files);
    try ring.unregister_files();
    const event_result = linux.eventfd(0, linux.EFD.CLOEXEC);
    if (linux.errno(event_result) != .SUCCESS) return error.EventFdCreationFailed;
    const event_fd: linux.fd_t = @intCast(event_result);
    defer _ = linux.close(event_fd);
    try ring.register_eventfd(event_fd);
    try ring.unregister_eventfd();
    try ring.register_eventfd_async(event_fd);
    const nop = try ring.nop(1);
    nop.flags |= linux.IOSQE_ASYNC;
    _ = try ring.submit();
    const completion = try ring.copy_cqe();
    if (completion.user_data != 1 or completion.res != 0) return error.AsyncNopFailed;
    var notifications: u64 = 0;
    const event_bytes = std.mem.asBytes(&notifications);
    const read = linux.read(event_fd, event_bytes.ptr, event_bytes.len);
    if (linux.errno(read) != .SUCCESS or read != event_bytes.len) return error.EventFdReadFailed;
    try ring.unregister_eventfd();
    const personality = try raw.register_personality(&ring);
    const credential_nop = try ring.nop(2);
    credential_nop.personality = personality;
    _ = try ring.submit();
    const credential_completion = try ring.copy_cqe();
    if (credential_completion.user_data != 2 or credential_completion.res != 0) return error.PersonalityNopFailed;
    try raw.unregister_personality(&ring, personality);
    var probe: linux.io_uring_probe = undefined;
    try raw.register_probe(&ring, &probe);
    const standalone = try raw.probe();
    var output_buffer: [512]u8 = undefined;
    var stdout = std.Io.File.stdout().writer(init.io, &output_buffer);
    try stdout.interface.print("{{\"buffers\":true,\"files_updated\":true,\"async_notifications\":{d},\"personality_result\":{d},\"probe_nop\":{s},\"standalone_probe_nop\":{s}}}\n", .{
        notifications,                                          credential_completion.res, if (probe.is_supported(.NOP)) "true" else "false",
        if (standalone.is_supported(.NOP)) "true" else "false",
    });
    try stdout.interface.flush();
}
