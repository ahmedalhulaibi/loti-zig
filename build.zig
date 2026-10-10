const std = @import("std");
const builtin = @import("builtin");

comptime {
    if (!std.mem.eql(u8, builtin.zig_version_string, "0.17.0"))
        @compileError("This edition requires exactly Zig 0.17.0");
}

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    if (target.result.os.tag != .linux) @panic("io_uring examples require Linux");
    const names = .{
        .{ "readv", "readv" },
        .{ "raw-cat", "raw_cat" },
        .{ "cat", "cat" },
        .{ "cp", "cp" },
        .{ "probe", "probe" },
        .{ "link", "link" },
        .{ "fixed-buffers", "fixed_buffers" },
        .{ "sq-poll", "sq_poll" },
        .{ "register-eventfd", "register_eventfd" },
        .{ "webserver", "webserver" },
        .{ "reference-setup", "reference_setup" },
        .{ "reference-completion", "reference_completion" },
        .{ "reference-signals", "reference_signals" },
        .{ "reference-files", "reference_files" },
        .{ "reference-buffers", "reference_buffers" },
        .{ "reference-splice", "reference_splice" },
        .{ "reference-registration", "reference_registration" },
        .{ "reference-submission", "reference_submission" },
        .{ "reference-raw", "reference_raw" },
    };
    inline for (names) |entry| {
        const exe = b.addExecutable(.{
            .name = entry[0],
            .root_module = b.createModule(.{
                .root_source_file = b.path("examples/" ++ entry[1] ++ ".zig"),
                .target = target,
                .optimize = optimize,
            }),
        });
        b.installArtifact(exe);
    }
}
