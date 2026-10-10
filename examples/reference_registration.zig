const std = @import("std");
const linux = std.os.linux;
const raw = @import("raw_ops.zig");

const FileRead = struct {
    completion: linux.io_uring_cqe,
    slot: linux.fd_t,
    data: [64]u8,
};

const ReadReport = struct {
    tag: u64,
    slot: linux.fd_t,
    res: i32,
    flags: u32,
    bytes: []const u8,
};

fn readFixed(ring: *linux.IoUring, tag: u64, slot: linux.fd_t) !FileRead {
    var result: FileRead = undefined;
    const entry = try ring.read(tag, slot, .{ .buffer = &result.data }, 0);
    entry.flags |= linux.IOSQE_FIXED_FILE;
    result.slot = entry.fd;
    _ = try ring.submit();
    result.completion = try ring.copy_cqe();
    if (result.completion.user_data != tag) return error.UnexpectedReadCompletion;
    if (result.completion.res > result.data.len) return error.ReadResultOutOfBounds;
    return result;
}

fn readReport(result: *const FileRead) ReadReport {
    const length: usize = if (result.completion.res > 0) @intCast(result.completion.res) else 0;
    return .{
        .tag = result.completion.user_data,
        .slot = result.slot,
        .res = result.completion.res,
        .flags = result.completion.flags,
        .bytes = result.data[0..length],
    };
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 3) return error.ExpectedTwoInputFiles;
    const file = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer file.close(init.io);
    const replacement = try std.Io.Dir.cwd().openFile(init.io, args[2], .{});
    var replacement_open = true;
    defer if (replacement_open) replacement.close(init.io);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var memory: [4096]u8 = undefined;
    const vectors = [_]std.posix.iovec{.{ .base = &memory, .len = memory.len }};
    try ring.register_buffers(&vectors);
    try ring.unregister_buffers();

    const table = [_]linux.fd_t{ -1, file.handle };
    const original_files = [_]linux.fd_t{file.handle};
    const replacement_files = [_]linux.fd_t{replacement.handle};
    const empty_files = [_]linux.fd_t{-1};
    const bad_descriptor: i32 = -@as(i32, @backingInt(linux.E.BADF));
    try ring.register_files(&table);
    const before = try readFixed(&ring, 10, 1);
    if (before.completion.res < 0) return error.OriginalFixedReadFailed;
    const sparse = try readFixed(&ring, 11, 0);
    if (sparse.completion.res != bad_descriptor) return error.SparseEntryReadDidNotFail;

    try ring.register_files_update(1, &replacement_files);
    replacement.close(init.io);
    replacement_open = false;
    const replacement_closed = linux.errno(linux.fcntl(replacement.handle, linux.F.GETFD, 0)) == .BADF;
    if (!replacement_closed) return error.ReplacementDescriptorNotClosed;
    const after_sync = try readFixed(&ring, 12, 1);
    if (after_sync.completion.res < 0) return error.ReplacementFixedReadFailed;

    const update = try ring.get_sqe();
    update.prep_files_update(&original_files, 1);
    update.user_data = 13;
    _ = try ring.submit();
    const update_completion = try ring.copy_cqe();
    if (update_completion.user_data != 13 or update_completion.res != 1) return error.AsyncFileUpdateFailed;
    const after_async = try readFixed(&ring, 14, 1);
    if (after_async.completion.res < 0) return error.RestoredFixedReadFailed;

    try ring.register_files_update(1, &empty_files);
    const removed = try readFixed(&ring, 15, 1);
    if (removed.completion.res != bad_descriptor) return error.RemovedEntryReadDidNotFail;
    try ring.unregister_files();
    const unregistered = try readFixed(&ring, 16, 1);
    if (unregistered.completion.res != bad_descriptor) return error.UnregisteredTableReadDidNotFail;

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
    const report = .{
        .buffers = true,
        .files_updated = true,
        .fixed_files = .{
            .before = readReport(&before),
            .sparse = readReport(&sparse),
            .after_sync_update = readReport(&after_sync),
            .replacement_fd_closed = replacement_closed,
            .async_update = .{ .tag = update_completion.user_data, .res = update_completion.res, .flags = update_completion.flags },
            .after_async_update = readReport(&after_async),
            .removed = readReport(&removed),
            .unregistered = readReport(&unregistered),
        },
        .async_notifications = notifications,
        .personality_result = credential_completion.res,
        .probe_nop = probe.is_supported(.NOP),
        .standalone_probe_nop = standalone.is_supported(.NOP),
    };
    var output_buffer: [512]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &output_buffer);
    try std.json.Stringify.value(report, .{ .emit_strings_as_arrays = true }, &stdout.interface);
    try stdout.interface.writeByte('\n');
    try stdout.interface.flush();
}
