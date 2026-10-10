import json
import os
import re
import selectors
import signal
import socket
import struct
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.test_examples import BIN, ROOT, run

FIXTURES = ROOT / "testdata/inputs"
MODES = {"none": 0, "nonblock": 2048, "cloexec": 524288, "both": 526336}


def endpoint(port):
    return {"family": 2, "address": [127, 0, 0, 1], "port": port}


def request(tag, role, capacity, flags):
    return {"operation": "ACCEPT", "tag": tag, "descriptor": role, "length": 0, "flags": 0,
            "operation_flags": flags, "address_supplied": capacity is not None,
            "length_supplied": capacity is not None, "capacity": capacity}


def failure(tag, role, result, flags=0):
    return {"request": request(tag, role, 16, flags), "cqe": {"tag": tag, "result": result, "flags": 0},
            "address_length": 16, "storage": [165] * 32}


def expected_report(capacity, mode, peer, local, fd):
    wire = struct.pack("=H", socket.AF_INET) + struct.pack("!H4s", peer, socket.inet_aton("127.0.0.1")) + bytes(8)
    stored = 0 if capacity is None else capacity
    flags = MODES[mode]
    return {"failures": [failure(10, "invalid", -9), failure(11, "ring", -88), failure(12, "listener", -22, 1)],
            "accepted": {"request": request(1, "listener", capacity, flags), "cqe": {"tag": 1, "result": fd, "flags": 0},
                         "address_length": 16 if capacity is not None else None,
                         "storage": list(wire[:stored]) + [165] * (32 - stored),
                         "peer": {"address": endpoint(peer), "length": 16},
                         "local": {"address": endpoint(local), "length": 16},
                         "flags": {"nonblocking": bool(flags & 2048), "cloexec": bool(flags & 524288)}},
            "listener_flags": {"nonblocking": True, "cloexec": True},
            "cleanup": {"listener_closed": True, "accepted_retained_after_listener_close": True,
                        "accepted_closed": True, "ring_still_open": True}}


def read_ready(process):
    data = bytearray()
    deadline = time.monotonic() + 2
    with selectors.DefaultSelector() as select:
        select.register(process.stdout, selectors.EVENT_READ)
        while len(data) < 512:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select(remaining):
                raise AssertionError("Accept readiness deadline expired")
            byte = os.read(process.stdout.fileno(), 1)
            if byte == b"":
                raise AssertionError("Accept process closed readiness stream")
            if byte == b"\n":
                try:
                    return json.loads(data)
                except ValueError as error:
                    raise AssertionError("Invalid accept readiness JSON") from error
            data.extend(byte)
    raise AssertionError("Accept readiness record exceeds 512 bytes")


def inspect_trace(text):
    submissions, rings, queries, closed, badf = 0, set(), {}, set(), []
    for line in text.splitlines():
        if re.match(r"(?:accept|accept4)\(", line):
            raise ValueError("SynchronousAcceptDetected")
        entered = re.fullmatch(r"io_uring_enter\((\d+), 1, 1, IORING_ENTER_GETEVENTS, NULL, 8\)\s+= 1", line)
        if entered:
            rings.add(int(entered[1])); submissions += 1
        query = re.fullmatch(r'(getsockname|getpeername)\((\d+), \{sa_family=AF_INET, sin_port=htons\((\d+)\), sin_addr=inet_addr\("127\.0\.0\.1"\)\}, \[16\]\)\s+= 0', line)
        if query:
            method, fd, port = query.groups(); key = (method, int(fd))
            if key in queries or not 1 <= int(port) <= 65535:
                raise ValueError("InvalidAcceptEndpointQuery")
            queries[key] = int(port)
        close = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if close:
            closed.add(int(close[1]))
        invalid = re.fullmatch(r"fcntl\((\d+), F_GETFD\)\s+= -1 EBADF \(Bad file descriptor\)", line)
        if invalid:
            if int(invalid[1]) not in closed:
                raise ValueError("AcceptCloseNotObservedBeforeQuery")
            badf.append(int(invalid[1]))
    peers = [(fd, port) for (method, fd), port in queries.items() if method == "getpeername"]
    if submissions != 4 or len(rings) != 1 or len(queries) != 3 or len(peers) != 1:
        raise ValueError("IncompleteAcceptKernelTrace")
    fd, peer = peers[0]
    local = queries.get(("getsockname", fd))
    listeners = [(other, port) for (method, other), port in queries.items() if method == "getsockname" and other != fd]
    if local is None or len(listeners) != 1 or listeners[0][1] != local or fd == listeners[0][0]:
        raise ValueError("WrongAcceptEndpointIdentity")
    if len(badf) != 2 or set(badf) != {fd, listeners[0][0]} or not rings.issubset(closed):
        raise ValueError("IncompleteAcceptQueriedCleanup")
    return {"submissions": 4, "rings": 1, "peer_port": peer, "local_port": local, "accepted_fd": fd,
            "listener_fd": listeners[0][0], "queried_closures": 2, "synchronous_accepts": 0}


def observe(capacity, mode, path):
    process = subprocess.Popen(["strace", "-qq", "-e", "trace=accept,accept4,getsockname,getpeername,fcntl,close,io_uring_enter",
                                "-o", str(path), str(BIN / "reference-accept"), "null" if capacity is None else str(capacity), mode],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        ready = read_ready(process)
        if type(ready) is not dict or type(ready.get("port")) is not int or not 1 <= ready["port"] <= 65535:
            raise AssertionError("Invalid accept readiness shape")
        expected_ready = {"event": "loti.accept.ready", "address": "127.0.0.1", "port": ready["port"]}
        if ready != expected_ready:
            raise AssertionError("Unexpected accept readiness shape")
        with socket.create_connection(("127.0.0.1", ready["port"]), timeout=2) as client:
            host, peer = client.getsockname(); destination = client.getpeername()
            if host != "127.0.0.1" or destination != ("127.0.0.1", ready["port"]):
                raise AssertionError("Wrong externally observed accept endpoints")
            stdout, stderr = process.communicate(timeout=5)
            if process.returncode != 0 or stderr != b"":
                raise AssertionError(f"Accept exited {process.returncode}: {stderr!r}")
            if client.recv(1) != b"":
                raise AssertionError("Accepted socket did not close with empty EOF")
        try:
            trace = inspect_trace(path.read_text()); report = json.loads(stdout)
        except ValueError as error:
            raise AssertionError(f"Invalid public accept report/trace: {error}") from error
        if trace["peer_port"] != peer or trace["local_port"] != ready["port"]:
            raise AssertionError("Native trace disagrees with independent client")
        return report, peer, ready["port"], trace
    except (OSError, subprocess.SubprocessError) as error:
        raise AssertionError(f"Accept boundary runner failed: {error}") from error
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()


class AcceptContracts(unittest.TestCase):
    def test_all_address_capacities_and_descriptor_flag_plans(self):
        """All 72 plans kill truncated/output-pointer errors, inherited flags, wrong returned FD/endpoints and exit-only cleanup."""
        plans = json.loads((FIXTURES / "accept-plans.json").read_text())
        self.assertEqual([(row["capacity"], row["mode"]) for row in plans], [(capacity, mode) for capacity in [None, *range(17)] for mode in MODES])
        for case in plans:
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as directory:
                actual, peer, local, trace = observe(case["capacity"], case["mode"], Path(directory) / "accept.trace")
                self.assertEqual(actual, expected_report(case["capacity"], case["mode"], peer, local, trace["accepted_fd"]))
        original = (FIXTURES / "accept.trace").read_text()
        self.assertEqual(inspect_trace(original), {"submissions": 4, "rings": 1, "peer_port": 43123, "local_port": 41234,
                                                  "accepted_fd": 5, "listener_fd": 3, "queried_closures": 2, "synchronous_accepts": 0})
        for case in json.loads((FIXTURES / "accept-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(original.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])

    def test_independent_full_address_literal(self):
        """A separate symbolic literal pins the whole full-address shape without the table encoder."""
        template = json.loads((FIXTURES / "accept-report.json").read_text())
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                actual, peer, local, trace = observe(16, "both", Path(directory) / "accept.trace")
                family = struct.pack("=H", socket.AF_INET)
                values = {"$peer": peer, "$local": local, "$fd": trace["accepted_fd"], "$port_high": peer >> 8,
                          "$port_low": peer & 255, "$family0": family[0], "$family1": family[1]}
                def replace(value):
                    if isinstance(value, dict):
                        return {key: replace(item) for key, item in value.items()}
                    if isinstance(value, list):
                        return [replace(item) for item in value]
                    return values.get(value, value) if isinstance(value, str) else value
                self.assertEqual(actual, replace(template))

    def test_invalid_arguments_fail_before_any_ready_record_or_socket_setup(self):
        """Kills signed/out-of-range capacities, unknown modes, wrong arity and late validation."""
        for case in json.loads((FIXTURES / "accept-invalid-arguments.json").read_text()):
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "invalid.trace"
                result = subprocess.run(["strace", "-qq", "-e", "trace=socket,io_uring_setup", "-o", str(path),
                                         str(BIN / "reference-accept"), *case["arguments"]], capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.splitlines()[0], ("error: " + case["error"]).encode())
                self.assertEqual(path.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
