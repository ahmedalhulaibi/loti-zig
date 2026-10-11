"""All original MIME cases and exact size-limit boundary over owned default TCP peers."""

import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.test_http_close import census


def decoded(value):
    try:
        return json.loads(value)
    except ValueError as error:
        raise AssertionError("InvalidOwnedHttpPurposeJson") from error


def wire(port: int, target: str) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as peer:
        peer.sendall(f"GET /{target} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
        peer.shutdown(socket.SHUT_WR)
        deadline = time.monotonic() + 10
        output = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            assert remaining > 0, "OwnedHttpPurposeEofMissing"
            peer.settimeout(remaining)
            try:
                part = peer.recv(65536)
            except socket.timeout as error:
                raise AssertionError("OwnedHttpPurposeEofMissing") from error
            if not part:
                return bytes(output)
            output.extend(part)
            assert len(output) <= 4194304 + 512, "OwnedHttpPurposeResponseOutOfBounds"


def expected(status: int, reason: str, mime: str, body: bytes) -> bytes:
    return (f"HTTP/1.1 {status} {reason}\r\nServer: loti-zig\r\nContent-Type: {mime}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)


def main() -> None:
    contract = decoded((ROOT / "testdata/inputs/http-purpose-cases.json").read_bytes())
    payload = (ROOT / contract["payload_file"]).read_bytes()
    rows = []
    with tempfile.TemporaryDirectory(prefix="loti-http-purpose-") as directory:
        root = Path(directory)
        inputs = {}
        for filename, _ in contract["mime_cases"]:
            inputs[filename] = payload
        pattern = bytes(range(256)) * (contract["file_limit"] // 256) + bytes([165])
        for size, _ in contract["limit_cases"]:
            inputs[f"size-{size}.bin"] = pattern[:size]
        for filename, body in inputs.items():
            (root / filename).write_bytes(body)
        process = subprocess.Popen([str(ROOT / "zig-out/bin/webserver"), str(root), "0"],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            assert process.stdout is not None and process.stderr is not None
            assert select.select([process.stdout], [], [], 5)[0], "OwnedHttpPurposeReadinessMissing"
            ready = decoded(process.stdout.readline())
            port = ready["port"]
            assert type(port) is int and 1 <= port <= 65535
            assert ready == {"event": "loti.http.ready", "address": "127.0.0.1", "port": port}
            paths = [root / name for name in inputs]
            baseline, opened = census(process, paths)
            assert (len(baseline), opened) == (1, 0)
            cases = [(name, 200, "OK", mime, payload) for name, mime in contract["mime_cases"]]
            for size, status in contract["limit_cases"]:
                cases.append((f"size-{size}.bin", status,
                              "OK" if status == 200 else contract["too_large"]["reason"],
                              "application/octet-stream" if status == 200 else "text/plain",
                              inputs[f"size-{size}.bin"] if status == 200 else contract["too_large"]["body"].encode()))
            for filename, status, reason, mime, body in cases:
                actual = wire(port, filename)
                wanted = expected(status, reason, mime, body)
                assert actual == wanted, filename
                assert census(process, paths) == (baseline, 0), filename
                assert process.poll() is None
                rows.append({"file": filename, "status": status, "mime": mime,
                             "body_bytes": len(body), "wire_bytes": len(actual),
                             "wire_sha256": hashlib.sha256(actual).hexdigest(),
                             "tcp_eof_observed": True, "owned_file_descriptors": 0,
                             "only_original_listener_socket_retained": True})
            assert all((root / filename).read_bytes() == body for filename, body in inputs.items())
            assert process.poll() is None
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=2)
            assert process.stdout is not None and process.stderr is not None
            process.stdout.close()
            process.stderr.close()
    (ROOT / "conversion/http-purpose-native.json").write_text(json.dumps({
        "scope": "Finite owned real default-mode loopback HTTP: all nine original case-insensitive extension spellings plus fallback;4MiB-1/4MiB/4MiB+1; whole wire through EOF and child-only file/socket census. Not valid image decoding, generated PBT, all statuses, concurrency/races or physical storage failure.",
        "cases": rows, "source_files_unchanged": True,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
