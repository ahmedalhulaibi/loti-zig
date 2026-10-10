const std = @import("std");
const linux = std.os.linux;

pub const Request = struct { operation: linux.IORING_OP, tag: u64, length: u32, offset: u64, flags: u8 };
pub const Failure = enum { none, read };
pub const Step = struct {
    request: Request,
    cqe: struct { tag: u64, result: i32, flags: u32 },
    done_before: usize,
    done_after: usize,
    phase_after: enum { idle, reading, writing },
    written: u64,
};

pub fn argument(args: []const []const u8) !?u64 {
    if (args.len == 3) return null;
    if (args.len != 5 and (args.len != 6 or !std.mem.eql(u8, args[5], "--fail-read"))) return error.ExpectedSourceAndDestination;
    if (!std.mem.eql(u8, args[3], "--short-write")) return error.UnknownCopyMode;
    if (args[4].len == 0) return error.InvalidShortWriteLimit;
    for (args[4]) |byte| if (!std.ascii.isDigit(byte)) return error.InvalidShortWriteLimit;
    const value = std.fmt.parseInt(u64, args[4], 10) catch return error.InvalidShortWriteLimit;
    if (value == 0) return error.InvalidShortWriteLimit;
    return value;
}

fn current() !linux.rlimit {
    var limit: linux.rlimit = undefined;
    if (linux.errno(linux.getrlimit(.FSIZE, &limit)) != .SUCCESS) return error.CopyFileLimitQueryFailed;
    return limit;
}

fn set(limit: *const linux.rlimit) !void {
    if (linux.errno(linux.setrlimit(.FSIZE, limit)) != .SUCCESS) return error.CopyFileLimitChangeFailed;
}

fn limits(value: linux.rlimit) struct { soft: u64, hard: u64 } {
    return .{ .soft = value.cur, .hard = value.max };
}

pub const Probe = struct {
    input_size: u64,
    limit: u64,
    original: linux.rlimit,
    verified: ?linux.rlimit = null,
    armed: bool = false,
    observed_write: bool = false,
    steps: [3]Step = undefined,
    used: usize = 0,

    pub fn init(size: u64, limit: u64) !Probe {
        if (size > 16 * 1024) return error.ShortWriteNeedsSingleBuffer;
        if (limit >= size) return error.ShortWriteLimitMustBeBelowInputSize;
        const original = try current();
        if (original.cur < size) return error.CopyLimitCannotPermitCompletion;
        return .{ .input_size = size, .limit = limit, .original = original };
    }

    pub fn arm(self: *Probe) !void {
        const limit: linux.rlimit = .{ .cur = self.limit, .max = self.original.max };
        try set(&limit);
        self.armed = true;
    }

    pub fn restore(self: *Probe) !void {
        if (self.armed) {
            try set(&self.original);
            self.armed = false;
        }
    }

    pub fn beforeProgress(self: *Probe, request: Request, cqe: linux.io_uring_cqe) !void {
        if (request.operation == .WRITE and !self.observed_write) {
            if (request.offset != 0 or request.length != self.input_size or cqe.res != self.limit) return error.ControlledShortWriteMissing;
            try self.restore();
            self.observed_write = true;
        }
    }

    pub fn record(self: *Probe, step: Step) !void {
        if (self.used == self.steps.len) return error.ShortWriteProbeStepOverflow;
        self.steps[self.used] = step;
        self.used += 1;
    }

    pub fn verifyRestored(self: *Probe) !void {
        const restored = try current();
        if (restored.cur != self.original.cur or restored.max != self.original.max) return error.CopyFileLimitNotRestored;
        self.verified = restored;
    }

    pub fn render(self: *Probe, written: u64, io: std.Io) !void {
        const restored = self.verified orelse return error.CopyFileLimitNotVerified;
        if (written != self.input_size or !self.observed_write or self.used != 3) return error.IncompleteShortCopy;
        var buffer: [4096]u8 = undefined;
        var output = std.Io.File.stdout().writerStreaming(io, &buffer);
        try std.json.Stringify.value(.{ .event = "loti.copy.short-write.checked", .input_size = self.input_size, .limit = self.limit, .steps = self.steps[0..self.used], .limits = .{ .original = limits(self.original), .armed = limits(.{ .cur = self.limit, .max = self.original.max }), .restored = limits(restored) }, .written = written }, .{}, &output.interface);
        try output.interface.writeByte('\n');
        try output.interface.flush();
    }
};
