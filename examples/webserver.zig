const std = @import("std");
const linux = std.os.linux;

const client_limit = 32;
const file_limit = 4 * 1024 * 1024;

const raw = @import("raw_ops.zig");
pub const OpenHow = raw.OpenHow;
pub const resolve_no_symlinks = raw.resolve_no_symlinks;
pub const resolve_beneath = raw.resolve_beneath;

const Status = enum(u16) {
    ok = 200,
    bad_request = 400,
    forbidden = 403,
    not_found = 404,
    method_not_allowed = 405,
    content_too_large = 413,
    headers_too_large = 431,
    internal_error = 500,

    fn reason(self: Status) []const u8 {
        return switch (self) {
            .ok => "OK",
            .bad_request => "Bad Request",
            .forbidden => "Forbidden",
            .not_found => "Not Found",
            .method_not_allowed => "Method Not Allowed",
            .content_too_large => "Content Too Large",
            .headers_too_large => "Request Header Fields Too Large",
            .internal_error => "Internal Server Error",
        };
    }

    fn body(self: Status) []const u8 {
        return switch (self) {
            .ok => "",
            .bad_request => "Bad Request\n",
            .forbidden => "Forbidden\n",
            .not_found => "Not Found\n",
            .method_not_allowed => "Method Not Allowed\n",
            .content_too_large => "Content Too Large\n",
            .headers_too_large => "Request Header Fields Too Large\n",
            .internal_error => "Internal Server Error\n",
        };
    }
};

const Mode = enum { serve, observe_send };
const Phase = enum { idle, receiving, loading, sending_headers, sending_body };
const SendRequest = struct {
    operation: linux.IORING_OP,
    tag: u64,
    fd: linux.fd_t,
    phase: Phase,
    offset: usize,
    length: u32,
    flags: u8,
    rw_flags: u32,
};

const Client = struct {
    fd: linux.fd_t = -1,
    file_fd: linux.fd_t = -1,
    phase: Phase = .idle,
    request: [8192]u8 = undefined,
    request_len: usize = 0,
    filename: [1024:0]u8 = undefined,
    header: [512]u8 = undefined,
    header_len: usize = 0,
    owned: []u8 = &.{},
    body: []const u8 = "",
    progress: usize = 0,
    send_request: SendRequest = undefined,

    fn release(self: *Client, allocator: std.mem.Allocator) void {
        if (self.file_fd >= 0) _ = linux.close(self.file_fd);
        if (self.fd >= 0) _ = linux.close(self.fd);
        allocator.free(self.owned);
        self.* = .{};
    }
};

const Server = struct {
    io: std.Io,
    allocator: std.mem.Allocator,
    root: linux.fd_t,
    listener: linux.fd_t,
    ring: *linux.IoUring,
    clients: *[client_limit]Client,
    mode: Mode = .serve,

    fn emit(self: *Server, value: anytype) !void {
        if (self.mode != .observe_send) return;
        var buffer: [1024]u8 = undefined;
        var output = std.Io.File.stdout().writerStreaming(self.io, &buffer);
        try std.json.Stringify.value(value, .{}, &output.interface);
        try output.interface.writeByte('\n');
        try output.interface.flush();
    }

    fn sendBuffer(self: *Server, id: usize) !void {
        if (self.mode != .observe_send) return;
        const fd = self.clients[id].fd;
        const requested: i32 = 4096;
        if (linux.errno(linux.setsockopt(fd, linux.SOL.SOCKET, linux.SO.SNDBUF, std.mem.asBytes(&requested).ptr, @sizeOf(i32))) != .SUCCESS)
            return error.HttpSendBufferSetFailed;
        var effective: i32 = 0;
        var size: linux.socklen_t = @sizeOf(i32);
        if (linux.errno(linux.getsockopt(fd, linux.SOL.SOCKET, linux.SO.SNDBUF, std.mem.asBytes(&effective).ptr, &size)) != .SUCCESS)
            return error.HttpSendBufferQueryFailed;
        if (size != @sizeOf(i32) or effective != 8192) return error.HttpSendBufferNot8192;
        try self.emit(.{ .event = "loti.http.send-buffer", .tag = id + 1, .fd = fd, .requested = requested, .effective = effective });
    }

    fn closeClient(self: *Server, id: usize) !void {
        const fd = self.clients[id].fd;
        self.clients[id].release(self.allocator);
        if (self.mode != .observe_send) return;
        if (linux.errno(linux.fcntl(fd, linux.F.GETFD, 0)) != .BADF) return error.HttpClientSocketNotClosed;
        try self.emit(.{ .event = "loti.http.closed", .tag = id + 1, .fd = fd, .closed = true });
    }

    fn accept(self: *Server) !void {
        _ = try self.ring.accept(0, self.listener, null, null, linux.SOCK.CLOEXEC);
    }

    fn queue(self: *Server, id: usize) !void {
        const client = &self.clients[id];
        const tag = id + 1;
        switch (client.phase) {
            .receiving => _ = try self.ring.recv(tag, client.fd, .{ .buffer = client.request[client.request_len..] }, 0),
            .loading => _ = try self.ring.read(tag, client.file_fd, .{ .buffer = client.owned[client.progress..] }, client.progress),
            .sending_headers, .sending_body => {
                const buffer = if (client.phase == .sending_headers) client.header[0..client.header_len] else client.body;
                const sqe = try self.ring.send(tag, client.fd, buffer[client.progress..], linux.MSG.NOSIGNAL);
                const base = @intFromPtr(buffer.ptr);
                if (sqe.addr < base or sqe.addr - base > buffer.len or sqe.len > buffer.len - (sqe.addr - base))
                    return error.HttpPreparedSendOutsideStorage;
                client.send_request = .{
                    .operation = sqe.opcode,
                    .tag = sqe.user_data,
                    .fd = sqe.fd,
                    .phase = client.phase,
                    .offset = @intCast(sqe.addr - base),
                    .length = sqe.len,
                    .flags = sqe.flags,
                    .rw_flags = sqe.rw_flags,
                };
            },
            .idle => unreachable,
        }
    }

    fn response(self: *Server, id: usize, status: Status, mime: []const u8) !void {
        const client = &self.clients[id];
        if (client.file_fd >= 0) {
            _ = linux.close(client.file_fd);
            client.file_fd = -1;
        }
        const header = try std.fmt.bufPrint(&client.header, "HTTP/1.1 {d} {s}\r\nServer: loti-zig\r\nContent-Type: {s}\r\nContent-Length: {d}\r\nConnection: close\r\n\r\n", .{ @backingInt(status), status.reason(), mime, client.body.len });
        client.header_len = header.len;
        client.progress = 0;
        client.phase = .sending_headers;
        try self.queue(id);
    }

    fn errorResponse(self: *Server, id: usize, status: Status) !void {
        const client = &self.clients[id];
        self.allocator.free(client.owned);
        client.owned = &.{};
        client.body = status.body();
        try self.response(id, status, "text/plain");
    }

    fn prepare(self: *Server, id: usize) !void {
        const client = &self.clients[id];
        const first_line = std.mem.indexOf(u8, client.request[0..client.request_len], "\r\n") orelse
            return self.errorResponse(id, .bad_request);
        var words = std.mem.splitScalar(u8, client.request[0..first_line], ' ');
        const method = words.next() orelse return self.errorResponse(id, .bad_request);
        const target = words.next() orelse return self.errorResponse(id, .bad_request);
        const version = words.next() orelse return self.errorResponse(id, .bad_request);
        if (words.next() != null or (!std.mem.eql(u8, version, "HTTP/1.1") and !std.mem.eql(u8, version, "HTTP/1.0")))
            return self.errorResponse(id, .bad_request);
        if (!std.mem.eql(u8, method, "GET")) return self.errorResponse(id, .method_not_allowed);
        if (target.len == 0 or target[0] != '/' or target.len > 1000)
            return self.errorResponse(id, .bad_request);
        const query = std.mem.indexOfScalar(u8, target, '?') orelse target.len;
        const path = target[1..query];
        var used: usize = 0;
        var i: usize = 0;
        while (i < path.len) : (i += 1) {
            var byte = path[i];
            if (byte == '%') {
                if (i + 2 >= path.len) return self.errorResponse(id, .bad_request);
                const high = hex(path[i + 1]) catch return self.errorResponse(id, .bad_request);
                const low = hex(path[i + 2]) catch return self.errorResponse(id, .bad_request);
                byte = high * 16 + low;
                i += 2;
            }
            if (byte == 0 or byte < 0x20 or byte == 0x7f) return self.errorResponse(id, .bad_request);
            if (byte == '\\') return self.errorResponse(id, .forbidden);
            client.filename[used] = byte;
            used += 1;
        }
        if (used > 0 and client.filename[0] == '/') return self.errorResponse(id, .forbidden);
        var parts = std.mem.splitScalar(u8, client.filename[0..used], '/');
        while (parts.next()) |part| {
            if (std.mem.eql(u8, part, "..")) return self.errorResponse(id, .forbidden);
        }
        if (used == 0 or client.filename[used - 1] == '/') {
            const index = "index.html";
            @memcpy(client.filename[used..][0..index.len], index);
            used += index.len;
        }
        client.filename[used] = 0;
        const flags: linux.O = .{ .ACCMODE = .RDONLY, .CLOEXEC = true, .NONBLOCK = true };
        const how: OpenHow = .{
            .flags = @as(u32, @bitCast(flags)),
            .resolve = resolve_beneath | resolve_no_symlinks,
        };
        const opened = linux.syscall4(.openat2, @as(u32, @bitCast(self.root)), @intFromPtr(&client.filename), @intFromPtr(&how), @sizeOf(OpenHow));
        switch (linux.errno(opened)) {
            .SUCCESS => {},
            .NOENT, .NOTDIR => return self.errorResponse(id, .not_found),
            .LOOP, .XDEV, .ACCES, .PERM => return self.errorResponse(id, .forbidden),
            else => return self.errorResponse(id, .internal_error),
        }
        client.file_fd = @intCast(opened);
        const file: std.Io.File = .{ .handle = client.file_fd, .flags = .{ .nonblocking = true } };
        const stat = file.stat(self.io) catch return self.errorResponse(id, .internal_error);
        if (stat.kind != .file) return self.errorResponse(id, .not_found);
        if (stat.size > file_limit) return self.errorResponse(id, .content_too_large);
        client.owned = try self.allocator.alloc(u8, @intCast(stat.size));
        client.body = client.owned;
        client.progress = 0;
        if (client.owned.len == 0) return self.response(id, .ok, mimeType(client.filename[0..used]));
        client.phase = .loading;
        try self.queue(id);
    }

    fn complete(self: *Server, cqe: linux.io_uring_cqe) !void {
        if (cqe.user_data == 0) {
            if (cqe.res < 0) {
                if (cqe.err() == .INTR or cqe.err() == .AGAIN or cqe.err() == .CONNABORTED)
                    return self.accept();
                return error.AcceptFailed;
            }
            const fd: linux.fd_t = cqe.res;
            for (self.clients, 0..) |*client, id| {
                if (client.phase != .idle) continue;
                client.fd = fd;
                try self.sendBuffer(id);
                client.phase = .receiving;
                try self.queue(id);
                return self.accept();
            }
            _ = linux.close(fd);
            return self.accept();
        }
        if (cqe.user_data > client_limit) return error.UnexpectedCompletion;
        const id: usize = @intCast(cqe.user_data - 1);
        const client = &self.clients[id];
        if (client.phase == .sending_headers or client.phase == .sending_body) {
            try self.emit(.{ .event = "loti.http.send", .request = client.send_request, .completion = cqe });
            if (cqe.res > 0 and @as(u32, @intCast(cqe.res)) > client.send_request.length) return error.HttpSendResultOutOfBounds;
        }
        if (cqe.err() == .INTR or cqe.err() == .AGAIN) return self.queue(id);
        if (cqe.res < 0) {
            if (client.phase == .loading) return self.errorResponse(id, .internal_error);
            try self.closeClient(id);
            return;
        }
        const count: usize = @intCast(cqe.res);
        switch (client.phase) {
            .receiving => {
                if (count == 0) return self.closeClient(id);
                client.request_len += count;
                if (std.mem.indexOf(u8, client.request[0..client.request_len], "\r\n\r\n") != null)
                    return self.prepare(id);
                if (client.request_len == client.request.len) return self.errorResponse(id, .headers_too_large);
                try self.queue(id);
            },
            .loading => {
                if (count == 0) return self.errorResponse(id, .internal_error);
                client.progress += count;
                if (client.progress < client.owned.len) return self.queue(id);
                try self.response(id, .ok, mimeType(std.mem.sliceTo(&client.filename, 0)));
            },
            .sending_headers, .sending_body => {
                if (count == 0) return self.closeClient(id);
                client.progress += count;
                const length = if (client.phase == .sending_headers) client.header_len else client.body.len;
                if (client.progress < length) return self.queue(id);
                if (client.phase == .sending_headers and client.body.len > 0) {
                    client.phase = .sending_body;
                    client.progress = 0;
                    return self.queue(id);
                }
                try self.closeClient(id);
            },
            .idle => return error.CompletionForIdleClient,
        }
    }
};

fn hex(byte: u8) !u8 {
    return switch (byte) {
        '0'...'9' => byte - '0',
        'a'...'f' => byte - 'a' + 10,
        'A'...'F' => byte - 'A' + 10,
        else => error.InvalidEscape,
    };
}

fn mimeType(path: []const u8) []const u8 {
    const dot = std.mem.lastIndexOfScalar(u8, path, '.') orelse return "application/octet-stream";
    const extension = path[dot + 1 ..];
    const names = .{
        .{ "jpg", "image/jpeg" },            .{ "jpeg", "image/jpeg" },
        .{ "png", "image/png" },             .{ "gif", "image/gif" },
        .{ "htm", "text/html" },             .{ "html", "text/html" },
        .{ "js", "application/javascript" }, .{ "css", "text/css" },
        .{ "txt", "text/plain" },
    };
    inline for (names) |entry| {
        if (std.ascii.eqlIgnoreCase(extension, entry[0])) return entry[1];
    }
    return "application/octet-stream";
}

pub fn main(init: std.process.Init) !void {
    const args = try init.minimal.args.toSlice(init.arena.allocator());
    if (args.len < 3 or args.len > 4) return error.ExpectedDocumentRootAndPort;
    const mode: Mode = if (args.len == 3) .serve else if (std.mem.eql(u8, args[3], "--observe-send")) .observe_send else return error.UnknownServerMode;
    const port = try std.fmt.parseInt(u16, args[2], 10);
    const root = try std.Io.Dir.cwd().openDir(init.io, args[1], .{});
    defer root.close(init.io);
    const socket_result = linux.socket(linux.AF.INET, linux.SOCK.STREAM | linux.SOCK.CLOEXEC, 0);
    if (linux.errno(socket_result) != .SUCCESS) return error.ListenerCreationFailed;
    const listener: linux.fd_t = @intCast(socket_result);
    defer _ = linux.close(listener);
    const reuse: i32 = 1;
    if (linux.errno(linux.setsockopt(listener, linux.SOL.SOCKET, linux.SO.REUSEADDR, std.mem.asBytes(&reuse).ptr, @sizeOf(i32))) != .SUCCESS) return error.ListenerOptionFailed;
    var address: linux.sockaddr.in = .{
        .port = std.mem.nativeToBig(u16, port),
        .addr = std.mem.nativeToBig(u32, 0x7f000001),
    };
    if (linux.errno(linux.bind(listener, @ptrCast(&address), @sizeOf(linux.sockaddr.in))) != .SUCCESS)
        return error.ListenerBindFailed;
    if (linux.errno(linux.listen(listener, 128)) != .SUCCESS) return error.ListenerListenFailed;
    var address_len: linux.socklen_t = @sizeOf(linux.sockaddr.in);
    if (linux.errno(linux.getsockname(listener, @ptrCast(&address), &address_len)) != .SUCCESS)
        return error.ListenerAddressQueryFailed;
    var clients: [client_limit]Client = undefined;
    for (&clients) |*client| client.* = .{};
    defer for (&clients) |*client| client.release(init.gpa);
    var ring = try linux.IoUring.init(64, 0);
    defer ring.deinit();
    var server: Server = .{
        .io = init.io,
        .allocator = init.gpa,
        .root = root.handle,
        .listener = listener,
        .ring = &ring,
        .clients = &clients,
        .mode = mode,
    };
    var ready_buffer: [256]u8 = undefined;
    var stdout = std.Io.File.stdout().writerStreaming(init.io, &ready_buffer);
    try stdout.interface.print("{{\"event\":\"loti.http.ready\",\"address\":\"127.0.0.1\",\"port\":{d}}}\n", .{
        std.mem.bigToNative(u16, address.port),
    });
    try stdout.interface.flush();
    try server.accept();
    while (true) {
        _ = try ring.submit();
        const cqe = ring.copy_cqe() catch |err| {
            if (err == error.SignalInterrupt) continue;
            return err;
        };
        try server.complete(cqe);
    }
}
