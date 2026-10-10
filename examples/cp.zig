const std = @import("std");
const linux = std.os.linux;
const support = @import("support.zig");
// BLKGETSIZE64 encodes size_t in the request but writes a u64 result.
const blkgetsize64 = linux.IOCTL.IOR(0x12, 114, usize);

const Slot = struct {
    buffer: [16 * 1024]u8 = undefined,
    offset: u64 = 0,
    length: usize = 0,
    done: usize = 0,
    phase: enum { idle, reading, writing } = .idle,
};

fn sourceSize(file: std.Io.File, io: std.Io) !u64 {
    const metadata = try file.stat(io);
    switch (metadata.kind) {
        .file => return metadata.size,
        .block_device => {
            var bytes: u64 = undefined;
            while (true) {
                const result = linux.ioctl(file.handle, blkgetsize64, @intFromPtr(&bytes));
                switch (linux.errno(result)) {
                    .SUCCESS => return bytes,
                    .INTR => continue,
                    else => return error.BlockDeviceSizeQueryFailed,
                }
            }
        },
        else => return error.ExpectedRegularFileOrBlockDevice,
    }
}

fn queue(ring: *linux.IoUring, slot: *Slot, id: usize, input: linux.fd_t, output: linux.fd_t) !void {
    const buffer = slot.buffer[slot.done..slot.length];
    switch (slot.phase) {
        .reading => _ = try ring.read(id + 1, input, .{ .buffer = buffer }, slot.offset + slot.done),
        .writing => _ = try ring.write(id + 1, output, buffer, slot.offset + slot.done),
        .idle => unreachable,
    }
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len != 3) return error.ExpectedSourceAndDestination;
    const input = try std.Io.Dir.cwd().openFile(init.io, args[1], .{});
    defer input.close(init.io);
    const input_size = try sourceSize(input, init.io);
    const output = try std.Io.Dir.cwd().createFile(init.io, args[2], .{ .truncate = false });
    defer output.close(init.io);
    if ((try output.stat(init.io)).kind != .file) return error.ExpectedRegularOutputFile;
    if (try support.sameFile(input.handle, output.handle)) return error.SourceAndDestinationAreSameFile;
    try output.setLength(init.io, 0);
    var ring = try linux.IoUring.init(8, 0);
    defer ring.deinit();
    var slots = [_]Slot{ .{}, .{} };
    var next_offset: u64 = 0;
    var written: u64 = 0;
    while (written < input_size) {
        for (&slots, 0..) |*slot, id| {
            if (slot.phase != .idle or next_offset == input_size) continue;
            slot.offset = next_offset;
            slot.length = @intCast(@min(input_size - next_offset, slot.buffer.len));
            slot.done = 0;
            slot.phase = .reading;
            next_offset += slot.length;
            try queue(&ring, slot, id, input.handle, output.handle);
        }
        _ = try ring.submit();
        const cqe = try ring.copy_cqe();
        if (cqe.user_data == 0 or cqe.user_data > slots.len) return error.UnexpectedCompletion;
        const id: usize = @intCast(cqe.user_data - 1);
        const slot = &slots[id];
        if (cqe.err() != .INTR and cqe.err() != .AGAIN) {
            const count = try support.completedBytes(cqe);
            if (count == 0) return error.CopyMadeNoProgress;
            if (count > slot.length - slot.done) return error.CompletionLengthInvalid;
            slot.done += count;
            if (slot.done == slot.length) {
                if (slot.phase == .reading) {
                    slot.phase = .writing;
                    slot.done = 0;
                } else {
                    written += slot.length;
                    slot.phase = .idle;
                }
            }
        }
        if (slot.phase != .idle) try queue(&ring, slot, id, input.handle, output.handle);
    }
}
