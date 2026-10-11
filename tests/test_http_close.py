"""Default-mode TCP EOF and owned descriptor retirement, not Connection header proxies."""

import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "zig-out/bin/webserver"
FIXTURE = ROOT / "testdata/inputs/http-close-contracts.json"


def census(process: subprocess.Popen, paths: list[Path]) -> tuple[set[str], int]:
    identities = {(path.stat().st_dev, path.stat().st_ino) for path in paths}
    sockets: set[str] = set()
    files = 0
    for fd in Path(f"/proc/{process.pid}/fd").iterdir():
        try:
            target = os.readlink(fd)
            if re.fullmatch(r"socket:\[\d+\]", target):
                sockets.add(target)
            metadata = fd.stat()
            if (metadata.st_dev, metadata.st_ino) in identities:
                files += 1
        except FileNotFoundError:
            continue
    return sockets, files


class DefaultHttpCloseContracts(unittest.TestCase):
    def test_default_responses_and_request_eof_retire_owned_descriptors(self):
        """Kills default-only socket leaks and shutdown-write masquerading as close."""
        contract = json.loads(FIXTURE.read_text())
        payload = (ROOT / contract["payload_file"]).read_bytes()
        self.assertEqual(len(payload), 37)
        with tempfile.TemporaryDirectory(prefix="loti-http-close-") as directory:
            root = Path(directory)
            probe, empty = root / "probe.bin", root / "empty.bin"
            probe.write_bytes(payload)
            empty.write_bytes(b"")
            process = subprocess.Popen([str(BIN), str(root), "0"], stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
            try:
                assert process.stdout is not None and process.stderr is not None
                self.assertTrue(select.select([process.stdout], [], [], 5)[0], "Owned HTTP readiness missing")
                ready = json.loads(process.stdout.readline())
                port = ready["port"]
                self.assertIs(type(port), int)
                self.assertTrue(1 <= port <= 65535)
                self.assertEqual(ready, {"event": "loti.http.ready", "address": "127.0.0.1", "port": port})
                baseline, files = census(process, [probe, empty])
                self.assertEqual((len(baseline), files), (1, 0))
                for case in contract["cases"]:
                    body = payload if case["body"] == "probe" else b"" if case["body"] == "empty" else case["body"].encode()
                    expected = case["header"].encode() + body
                    with socket.create_connection(("127.0.0.1", port), timeout=5) as peer:
                        peer.sendall(case["request"].encode())
                        peer.shutdown(socket.SHUT_WR)
                        deadline = time.monotonic() + 5
                        wire = bytearray()
                        while True:
                            remaining = deadline - time.monotonic()
                            self.assertGreater(remaining, 0, "Default HTTP failed to close before owned deadline")
                            peer.settimeout(remaining)
                            try:
                                part = peer.recv(65536)
                            except socket.timeout:
                                self.fail("Default HTTP failed to close before owned deadline")
                            if not part:
                                break
                            wire.extend(part)
                            self.assertLessEqual(len(wire), len(expected), "Unexpected bytes after complete HTTP response")
                        self.assertEqual(bytes(wire), expected, case["name"])
                        self.assertEqual(census(process, [probe, empty]), (baseline, 0), case["name"])
                    self.assertIsNone(process.poll(), "One connection stopped the server")
                # Recovery after both request-EOF plans proves listener/event-loop survival.
                with socket.create_connection(("127.0.0.1", port), timeout=5) as peer:
                    peer.sendall(contract["cases"][0]["request"].encode())
                    peer.shutdown(socket.SHUT_WR)
                    peer.settimeout(5)
                    recovered = bytearray()
                    while part := peer.recv(65536):
                        recovered.extend(part)
                    self.assertEqual(bytes(recovered), contract["cases"][0]["header"].encode() + payload)
                    self.assertEqual(census(process, [probe, empty]), (baseline, 0))
                self.assertEqual((probe.read_bytes(), empty.read_bytes()), (payload, b""))
                self.assertIsNone(process.poll())
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


if __name__ == "__main__":
    unittest.main()
