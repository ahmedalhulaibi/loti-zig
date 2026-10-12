"""HTTP pre-exit ownership regression, qualified directly from the public contract.

Kill claim: fatal observer EIO must not leave an accepted late peer's socket
owned after the earlier ring/listener/root/client descriptors have retired.
This test makes no claim about memory retirement or CQ disposition.
"""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import subprocess
import sys
import time
import unittest
import uuid
from typing import Any, BinaryIO, ClassVar, cast


REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "testdata/inputs/http-lifecycle.json"
PYTHON = Path("/home/ahmed/workspace/va/loti-zig/.venv/bin/python")
ZIG = Path("/home/ahmed/.local/share/mise/installs/zig/0.17.0/zig")


class HarnessError(RuntimeError):
    """Missing evidence/capability is an error, never an expected regression."""


def require(condition, description):
    if not condition:
        raise HarnessError(description)


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounded_command(argv, directory, name, timeout):
    with (directory / (name + ".stdout")).open("wb") as out:
        with (directory / (name + ".stderr")).open("wb") as err:
            save_json(directory / (name + ".argv.json"), argv)
            process = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err,
                                       start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
                save_json(directory / (name + ".result.json"), {"timeout": True})
                raise HarnessError(name + " command timed out")
    save_json(directory / (name + ".result.json"), {"returncode": code})
    require(code == 0, name + " command failed: " + str(code))
    return (directory / (name + ".stdout")).read_text()


def tcp_table(pid) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in ("tcp", "tcp6"):
        text = Path(f"/proc/{pid}/net/{family}").read_text()
        for line in text.splitlines()[1:]:
            fields = line.split()
            if family == "tcp":
                def endpoint(value):
                    address, port = value.split(":")
                    return [socket.inet_ntoa(bytes.fromhex(address)[::-1]),
                            int(port, 16)]
                local, remote = endpoint(fields[1]), endpoint(fields[2])
            else:
                local, remote = fields[1], fields[2]
            rows.append({"family": family, "local": local, "remote": remote,
                         "state": fields[3], "inode": int(fields[9])})
    return rows


def census(pid) -> dict[str, Any]:
    rows = tcp_table(pid)
    descriptors: list[dict[str, Any]] = []
    for entry in sorted(Path(f"/proc/{pid}/fd").iterdir(), key=lambda p: int(p.name)):
        target = os.readlink(entry)
        match = re.fullmatch(r"socket:\[(\d+)\]", target)
        inode = int(match[1]) if match else None
        descriptors.append({"fd": int(entry.name), "target": target,
                            "fdinfo": Path(f"/proc/{pid}/fdinfo/{entry.name}").read_text(),
                            "socket_inode": inode,
                            "tcp": [row for row in rows if row["inode"] == inode]})
    return {"descriptors": descriptors, "tcp": rows}


def peer_descriptors(snapshot: Any, peer) -> list[Any]:
    local, remote = list(peer.getpeername()), list(peer.getsockname())
    return [fd for fd in snapshot["descriptors"]
            if any(row["local"] == local and row["remote"] == remote
                   for row in fd["tcp"])]


def accept_observation(pid, endpoint, trace, snapshot, peer):
    survivors = [fd for fd in snapshot["descriptors"]
                 if any(row["local"] == endpoint["local"] and row["remote"] == endpoint["remote"]
                        for row in fd["tcp"])]
    require(len(survivors) <= 1, "ambiguous owned peer descriptor")
    closed = False
    for line in trace.splitlines():
        event = re.fullmatch(
            r"(\d+)\s+\d+\.\d+\s+\[\s*\d+\]\s+close\(\d+<TCP:\[([0-9.]+):(\d+)->([0-9.]+):(\d+)\]>\)\s+= 0", line)
        if event and int(event[1]) == pid:
            closed = ([event[2], int(event[3])] == endpoint["local"]
                      and [event[4], int(event[5])] == endpoint["remote"])
            if closed:
                break
    require(bool(survivors) or closed, "ACCEPT_RESULT_NOT_OBSERVED")
    return {"ownership_evidence": "live_socket" if survivors else "closed_socket",
            "surviving_socket_inodes": [fd["socket_inode"] for fd in survivors],
            "peer": peer, "cleanup_satisfied": not survivors and peer == {"state": "eof", "wire_hex": ""}}


def peer_probe(peer, timeout):
    peer.settimeout(timeout)
    wire = bytearray()
    try:
        while True:
            data = peer.recv(65536)
            if not data:
                return {"state": "eof", "wire_hex": wire.hex()}
            wire.extend(data)
    except socket.timeout:
        return {"state": "open", "wire_hex": wire.hex()}
    except ConnectionResetError:
        return {"state": "reset", "wire_hex": wire.hex()}


def response_shape(wire):
    head, separator, body = wire.partition(b"\r\n\r\n")
    require(separator == b"\r\n\r\n", "incomplete HTTP response")
    lines = head.decode("ascii").split("\r\n")
    headers = {}
    for line in lines[1:]:
        key, separator, value = line.partition(": ")
        require(separator == ": " and key.lower() not in headers,
                "malformed or duplicate HTTP header")
        headers[key.lower()] = value
    return {"status_line": lines[0], "headers": headers, "body_hex": body.hex()}


class OwnedServer:
    def __init__(self, binary, fixture, directory, fatal, *, command=None):
        self.f = fixture
        self.d = directory
        self.fatal = fatal
        self.peers: list[socket.socket] = []
        self.stdout = bytearray()
        self.buffer = bytearray()
        self.records: list[Any] = []
        self.pid: Any = None
        self.checkpoint: Any = None
        self.result: dict[str, Any] = {"mode": "fatal" if fatal else "default", "verification": "direct-review"}
        directory.mkdir()
        self.root = directory / "root"
        self.root.mkdir()
        for name, content in fixture["document_files"].items():
            (self.root / name).write_bytes(content.encode("utf-8"))
        self.stderr_r, stderr_w = os.pipe()
        self.stderr_identity = f"pipe:[{os.fstat(self.stderr_r).st_ino}]"
        self.fill_size = 0
        fill_byte = bytes.fromhex(fixture["stderr_fill_byte_hex"])
        os.set_blocking(stderr_w, False)
        try:
            while True:
                self.fill_size += os.write(stderr_w, fill_byte * 4096)
        except BlockingIOError:
            pass
        os.set_blocking(stderr_w, True)
        self.result.update({"stderr_identity": self.stderr_identity,
                            "stderr_prefill_bytes": self.fill_size,
                            "stderr_pipe_capacity": fcntl.fcntl(stderr_w, fcntl.F_GETPIPE_SZ)})
        self.argv = ["/usr/bin/strace", "-f", "-yy", "-ttt", "-n", "-s", "8192",
                     "-o", str(directory / "trace.log")]
        if fatal and command is None:
            fault = fixture["fault"]
            injection = (f"inject={fault['syscall']}:error={fault['error']}:"
                         f"when={fault['when']}:delay_enter={fault['delay_enter']}")
            self.argv.extend(["-e", injection])
        target = command if command is not None else [str(binary), str(self.root), fixture["port_argument"]]
        self.executable = Path(target[0]).resolve()
        self.argv.extend(target)
        if fatal and command is None:
            self.argv.append(fixture["observer_argument"])
        save_json(directory / "argv.json", self.argv)
        try:
            self.process = subprocess.Popen(self.argv, cwd=REPO, stdout=subprocess.PIPE,
                                            stderr=stderr_w, start_new_session=True)
        except BaseException:
            os.close(self.stderr_r)
            raise
        finally:
            os.close(stderr_w)
        self.result["process_group"] = self.process.pid
        self.output = cast(BinaryIO, self.process.stdout)

    def wait(self, action, label) -> Any:
        deadline = time.monotonic() + self.f["timeout_seconds"]
        while time.monotonic() < deadline:
            require(self.process.poll() is None, label + ": server exited before observation")
            try:
                value = action()
            except FileNotFoundError:
                value = None
            if value:
                return value
            time.sleep(0.01)
        raise HarnessError(label + ": deadline expired")

    def pump_stdout(self, timeout=0):
        if select.select([self.output], [], [], timeout)[0]:
            data = os.read(self.output.fileno(), 65536)
            self.stdout.extend(data)
            self.buffer.extend(data)
            while True:
                end = self.buffer.find(b"\n")
                if end < 0:
                    break
                line = bytes(self.buffer[:end])
                del self.buffer[:end + 1]
                self.records.append(json.loads(line))

    def ready(self):
        def action():
            self.pump_stdout()
            return self.records[0] if self.records else None
        ready = self.wait(action, "readiness")
        require(type(ready.get("port")) is int and 0 < ready["port"] < 65536,
                "invalid dynamic readiness port")
        require(ready == {"event": self.f["expected_ready_event"],
                          "address": self.f["host"], "port": ready["port"]},
                "unexpected readiness shape")
        self.port = ready["port"]
        def child():
            children = Path(f"/proc/{self.process.pid}/task/{self.process.pid}/children").read_text().split()
            require(len(children) <= 1, "unexpected tracee process tree")
            return int(children[0]) if children else None
        self.pid = self.wait(child, "owned tracee identity")
        require(Path(f"/proc/{self.pid}/exe").resolve() == self.executable,
                "tracee executable identity mismatch")
        self.result.update({"tracee_pid": self.pid, "readiness": ready})
        snapshot = census(self.pid)
        save_json(self.d / "ready-census.json", snapshot)
        return snapshot

    def connect(self, name, request):
        peer = socket.create_connection((self.f["host"], self.port), self.f["timeout_seconds"])
        self.peers.append(peer)
        self.result[name + "_tuple"] = {"local": list(peer.getsockname()),
                                        "remote": list(peer.getpeername())}
        if request:
            peer.sendall(request.encode("ascii"))
        return peer

    def accepted(self, name, peer):
        def action():
            snapshot = census(self.pid)
            matches = peer_descriptors(snapshot, peer)
            require(len(matches) <= 1, "ambiguous owned peer descriptor")
            if matches:
                require(matches[0]["tcp"][0]["state"] == "01", "peer is not established")
                return snapshot
        snapshot = self.wait(action, name + " successful accepted socket")
        save_json(self.d / (name + "-accepted-census.json"), snapshot)
        self.result[name + "_accepted"] = peer_descriptors(snapshot, peer)
        return snapshot

    def idle_published(self):
        def action():
            text = (self.d / "trace.log").read_text()
            for line in text.splitlines():
                match = re.search(r"^\d+\s+\d+\.\d+\s+\[\s*\d+\]\s+io_uring_enter\(\d+<anon_inode:\[io_uring\]>, (\d+),.*\)\s+= (\d+)$", line)
                if match and int(match[1]) == 2 and int(match[2]) == 2:
                    return line
        self.result["idle_and_accept_publication_enter"] = self.wait(action, "idle RECV and next ACCEPT publication")

    def read_headers(self, active):
        active.settimeout(self.f["timeout_seconds"])
        wire = bytearray()
        while wire.find(b"\r\n\r\n") < 0:
            chunk = active.recv(65536)
            require(bool(chunk), "active response ended before stimulus checkpoint")
            wire.extend(chunk)
        (self.d / "active-wire-prefix.bin").write_bytes(wire)
        self.result["active_wire_prefix_bytes"] = len(wire)

    def error_checkpoint(self, retired_targets):
        samples: list[Any] = []
        def action():
            snapshot = census(self.pid)
            targets = [fd["target"] for fd in snapshot["descriptors"]]
            syscall = Path(f"/proc/{self.pid}/syscall").read_text().strip()
            wchan = Path(f"/proc/{self.pid}/wchan").read_text().strip()
            status = Path(f"/proc/{self.pid}/status").read_text()
            state = next(line.partition(":")[2].strip().split()[0]
                         for line in status.splitlines() if line.partition(":")[0] == "State")
            fields = syscall.split()
            sample = {"syscall": syscall, "wchan": wchan, "state": state,
                      "census": snapshot}
            samples.append(sample)
            if len(fields) < 2 or fields[0] == "running":
                return None
            descriptor = next((fd for fd in snapshot["descriptors"] if fd["fd"] == 2), None)
            if not (int(fields[1], 0) == 2 and state == "S" and descriptor
                    and descriptor["target"] == self.stderr_identity):
                return None
            trace = (self.d / "trace.log").read_text()
            pending = re.compile(r"^\d+\s+\d+\.\d+\s+\[\s*(\d+)\]\s+writev\(2<pipe:\[(\d+)\]>", re.MULTILINE)
            matches = list(pending.finditer(trace))
            if not matches or int(matches[-1][1]) != int(fields[0]):
                return None
            if f"pipe:[{matches[-1][2]}]" != self.stderr_identity:
                return None
            if any(target in targets for target in retired_targets):
                return None
            return sample
        try:
            first = self.wait(action, "blocked owned stderr after prior resource retirement")
            time.sleep(self.f["checkpoint_stability_seconds"])
            second = action()
            if second is None:
                raise HarnessError("error checkpoint did not remain blocked")
            require(first["census"]["descriptors"] == second["census"]["descriptors"], "live full census was unstable")
            self.checkpoint = second
            save_json(self.d / "checkpoint.json", second)
            return second["census"]
        finally:
            save_json(self.d / "checkpoint-polls.json", samples)

    def close(self):
        primary = sys.exception()
        errors: list[BaseException] = []
        stderr = bytearray()
        forced = False
        try:
            os.set_blocking(self.stderr_r, False)
            if not self.fatal or self.checkpoint is None:
                if self.process.poll() is None:
                    os.killpg(self.process.pid, signal.SIGTERM)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                try:
                    stderr.extend(os.read(self.stderr_r, 65536))
                except BlockingIOError:
                    pass
                self.pump_stdout()
                if self.process.poll() is not None:
                    break
                time.sleep(0.01)
        except BaseException as error:
            errors.append(error)
        finally:
            try:
                forced = self.process.poll() is None
                if forced:
                    os.killpg(self.process.pid, signal.SIGTERM)
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(self.process.pid, signal.SIGKILL)
                    self.process.wait(timeout=2)
                while True:
                    try:
                        data = os.read(self.stderr_r, 65536)
                    except BlockingIOError:
                        break
                    if not data:
                        break
                    stderr.extend(data)
                self.pump_stdout()
            except BaseException as error:
                errors.append(error)
            finally:
                for release in [self.output.close, lambda: os.close(self.stderr_r),
                                *(peer.close for peer in self.peers)]:
                    try:
                        release()
                    except BaseException as error:
                        errors.append(error)
        try:
            (self.d / "stdout.log").write_bytes(self.stdout)
            (self.d / "stderr.log").write_bytes(stderr)
            fill = bytes.fromhex(self.f["stderr_fill_byte_hex"]) * self.fill_size
            require(bytes(stderr[:self.fill_size]) == fill, "owned stderr prefill was not preserved")
            actual_error = bytes(stderr[self.fill_size:])
            (self.d / "application-stderr.log").write_bytes(actual_error)
            first = actual_error.split(b"\n", 1)[0].decode("ascii") if actual_error else ""
            self.result.update({"returncode": self.process.returncode, "forced_termination": forced,
                                "first_error_line": first, "stdout_records": self.records})
            save_json(self.d / "result.json", self.result)
            if not errors:
                require(not forced, "owned tracee failed to exit after stderr release")
        except BaseException as error:
            errors.append(error)
        if errors:
            if primary is not None:
                errors.insert(0, primary)
            if len(errors) == 1:
                raise errors[0]
            raise BaseExceptionGroup("HTTP harness collection/cleanup failed", errors)


class HttpLifecycleContracts(unittest.TestCase):
    f: ClassVar[Any]
    directory: ClassVar[Path]
    binary: ClassVar[Path]
    @classmethod
    def setUpClass(cls):
        cls.f = json.loads(FIXTURE.read_text())
        require(Path(sys.executable).absolute() == PYTHON, "use the locked project Python")
        run = time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        cls.directory = REPO / "_build/verification" / ("http-lifecycle-" + run)
        cls.directory.mkdir(parents=True)
        print("Direct-review HTTP lifecycle artifacts: " + str(cls.directory), flush=True)
        (cls.directory / "fixture.json").write_bytes(FIXTURE.read_bytes())
        version = bounded_command([str(ZIG), "version"], cls.directory, "zig-version", 8).strip()
        require(version == "0.17.0", "exact Zig0.17.0 required")
        bounded_command(["/usr/bin/strace", "--help"], cls.directory, "strace-help", 8)
        bounded_command(["/usr/bin/strace", "--version"], cls.directory, "strace-version", 8)
        sources = bounded_command(["git", "ls-files", "*.zig"], cls.directory, "source-list", 8).splitlines()
        provenance = {"worktree": str(REPO), "python": str(PYTHON), "python_version": sys.version,
                      "base": bounded_command(["git", "rev-parse", "HEAD"], cls.directory, "base", 8).strip(),
                      "branch": bounded_command(["git", "branch", "--show-current"], cls.directory, "branch", 8).strip(),
                      "status": bounded_command(["git", "status", "--porcelain=v1"], cls.directory, "status", 8),
                      "source_sha256": {name: digest(REPO / name) for name in sources},
                      "tool_sha256": {str(path): digest(path) for path in (ZIG, PYTHON, Path("/usr/bin/strace"))},
                      "fixture_sha256": digest(FIXTURE), "test_sha256": digest(Path(__file__))}
        cls.binary = cls.directory / "webserver"
        argv = ["taskset", "-c", str(min(os.sched_getaffinity(0))), str(ZIG), "build-exe",
                "examples/webserver.zig", "-ODebug", "-femit-bin=" + str(cls.binary),
                "--cache-dir", str(cls.directory / "zig-cache"),
                "--global-cache-dir", str(cls.directory / "zig-global-cache")]
        bounded_command(argv, cls.directory, "compile", 120)
        provenance["binary_sha256"] = digest(cls.binary)
        save_json(cls.directory / "provenance.json", provenance)

    def expected_response(self):
        expected = self.f["expected_response"]
        body = self.f["document_files"][expected["body_file"]].encode("utf-8")
        return {"status_line": expected["status_line"],
                "headers": dict(expected["headers"], **{"content-length": str(len(body))}),
                "body_hex": body.hex()}

    def test_observer_evidence_cases(self):
        """Catch falsely accepting EOF/backlog,foreign closes or trace payloads as ownership proof."""
        for case in self.f["observer_cases"]:
            with self.subTest(case=case["name"]):
                if "expected_error" in case:
                    with self.assertRaises(HarnessError) as failure:
                        accept_observation(case["pid"], case["endpoint"], case["trace"], case["census"], case["peer"])
                    self.assertEqual(str(failure.exception), case["expected_error"])
                else:
                    self.assertEqual(accept_observation(case["pid"], case["endpoint"], case["trace"], case["census"], case["peer"]), case["expected"])

    def test_fast_close_observer_control(self):
        """Catch the observer timing out when correct cleanup closes ACCEPT before census."""
        command = [str(PYTHON), str(REPO / "tests/fixtures/http_lifecycle_control.py"), "fast-close"]
        server = OwnedServer(self.binary, self.f, self.directory / "fast-close", True, command=command)
        try:
            ready = server.ready()
            peer = server.connect("late", "")
            snapshot = server.error_checkpoint([fd["target"] for fd in ready["descriptors"] if fd["fd"] > 2])
            actual = accept_observation(server.pid, {"local": list(peer.getpeername()), "remote": list(peer.getsockname())},
                                        (server.d / "trace.log").read_text(), snapshot, peer_probe(peer, self.f["peer_probe_seconds"]))
            self.assertEqual(actual, self.f["observer_cases"][0]["expected"])
        finally:
            server.close()

    def test_collection_failure_always_reaps_owned_resources(self):
        """Catch malformed evidence leaving an owned child,pipes or peers alive;preserve primary failure."""
        def classes(error):
            if isinstance(error, BaseExceptionGroup):
                return [name for child in error.exceptions for name in classes(child)]
            return [type(error).__name__]
        for case in self.f["collection_failure_cases"]:
            with self.subTest(case=case["name"]):
                command = [str(PYTHON), str(REPO / "tests/fixtures/http_lifecycle_control.py"), "malformed-output"]
                server = OwnedServer(self.binary, self.f, self.directory / case["name"], False, command=command)
                pipe = server.stderr_r
                a, b = socket.socketpair()
                server.peers.extend([a, b])
                try:
                    require(bool(select.select([server.output], [], [], self.f["timeout_seconds"])[0]), "controlled malformed output missing")
                    children = Path(f"/proc/{server.process.pid}/task/{server.process.pid}/children").read_text().split()
                    require(len(children) == 1, "controlled tracee identity missing")
                    tracee = int(children[0])
                    with self.assertRaises(BaseException) as failure:
                        try:
                            if case["primary_message"] is not None:
                                raise HarnessError(case["primary_message"])
                        finally:
                            server.close()
                    self.assertEqual(classes(failure.exception), case["expected_raised"])
                    if case["expected_primary"] is not None:
                        self.assertIsInstance(failure.exception, BaseExceptionGroup)
                        grouped = cast(BaseExceptionGroup, failure.exception)
                        self.assertEqual((type(grouped.exceptions[0]).__name__, str(grouped.exceptions[0])),
                                         (case["expected_primary"], case["primary_message"]))
                    self.assertEqual(server.process.poll() is not None, True)
                    deadline = time.monotonic() + 3
                    while Path(f"/proc/{tracee}").exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertEqual(Path(f"/proc/{tracee}").exists(), False)
                    self.assertEqual((server.output.closed, a.fileno(), b.fileno()), (True, -1, -1))
                    with self.assertRaises(OSError) as closed:
                        os.fstat(pipe)
                    self.assertEqual(closed.exception.errno, 9)
                finally:
                    if server.process.poll() is None:
                        os.killpg(server.process.pid, signal.SIGKILL)
                        server.process.wait(timeout=2)
                    a.close()
                    b.close()

    def test_default_mode_control(self):
        """Kill: broken CLI/wire harness or a stalled peer blocking another client."""
        for attempt in range(self.f["repetitions"]):
            with self.subTest(attempt=attempt + 1):
                server = OwnedServer(self.binary, self.f, self.directory / f"control-{attempt + 1}", False)
                try:
                    server.ready()
                    idle = server.connect("idle", self.f["idle_request"])
                    server.accepted("idle", idle)
                    server.idle_published()
                    active = server.connect("active", self.f["request"])
                    active.settimeout(self.f["timeout_seconds"])
                    wire = bytearray()
                    while True:
                        chunk = active.recv(65536)
                        if not chunk:
                            break
                        wire.extend(chunk)
                    (server.d / "wire.bin").write_bytes(wire)
                    shape = response_shape(bytes(wire))
                    server.result["response_shape"] = shape
                    self.assertEqual(shape, self.expected_response())
                    snapshot = census(server.pid)
                    save_json(server.d / "completed-census.json", snapshot)
                    self.assertEqual(peer_descriptors(snapshot, active), [])
                    require(len(peer_descriptors(snapshot, idle)) == 1, "idle control descriptor vanished")
                    self.assertEqual(peer_probe(idle, self.f["peer_probe_seconds"]),
                                     {"state": "open", "wire_hex": ""})
                finally:
                    server.close()
                self.assertEqual(server.result["stdout_records"], [server.result["readiness"]])
                self.assertEqual(server.result["first_error_line"], "")

    def test_fatal_observer_releases_successful_late_accept_before_exit(self):
        """EXPECT CORRECT cleanup; current baseline must be specifically RED."""
        for attempt in range(self.f["repetitions"]):
            with self.subTest(attempt=attempt + 1):
                server = OwnedServer(self.binary, self.f, self.directory / f"fatal-{attempt + 1}", True)
                actual = None
                try:
                    ready = server.ready()
                    idle = server.connect("idle", self.f["idle_request"])
                    idle_snapshot = server.accepted("idle", idle)
                    server.idle_published()
                    active = server.connect("active", self.f["request"])
                    server.read_headers(active)
                    active_snapshot = server.accepted("active", active)
                    late = server.connect("late", self.f["late_request"])
                    initial = ready["descriptors"] + idle_snapshot["descriptors"] + active_snapshot["descriptors"]
                    retired = sorted({fd["target"] for fd in initial if fd["fd"] > 2})
                    save_json(server.d / "retired-identities.json", retired)
                    snapshot = server.error_checkpoint(retired)
                    server.pump_stdout()
                    records = server.records
                    require(len(records) == 3, "unexpected pre-EIO stdout event count")
                    for event, name in zip(records[1:], ("idle", "active")):
                        accepted = server.result[name + "_accepted"][0]
                        require(type(event.get("tag")) is int and event["tag"] > 0,
                                "invalid public client tag")
                        require(event == {"event": self.f["expected_send_buffer_event"],
                                          "tag": event["tag"], "fd": accepted["fd"],
                                          "requested": 4096, "effective": 8192},
                                "unexpected observer shape")
                    observed = accept_observation(server.pid, {"local": list(late.getpeername()), "remote": list(late.getsockname())},
                                                  (server.d / "trace.log").read_text(), snapshot, peer_probe(late, self.f["peer_probe_seconds"]))
                    server.result["late_ownership_evidence"] = observed
                    actual = {"late_accepted_socket_inodes": observed["surviving_socket_inodes"],
                              "late_peer": observed["peer"],
                              "idle_peer": peer_probe(idle, self.f["peer_probe_seconds"])}
                    server.result["pre_exit_observation"] = actual
                    save_json(server.d / "pre-exit-observation.json", actual)
                finally:
                    server.close()
                require(server.result["returncode"] == 1, "fault did not cause deterministic exit1")
                require(server.result["first_error_line"] == "error: " + self.f["expected_error_class"],
                        "fatal error class is not the specified observer-output failure")
                trace = (server.d / "trace.log").read_text()
                writev = [line for line in trace.splitlines()
                          if re.search(r"^\d+\s+\d+\.\d+\s+\[\s*\d+\]\s+writev\(", line)]
                fault = writev[self.f["fault"]["when"] - 1]
                require(re.fullmatch(r"\d+\s+\d+\.\d+\s+\[\s*\d+\]\s+writev\(1<pipe:\[\d+\]>, .*\)\s+= -1 EIO \(Input/output error\) \(INJECTED\) \(DELAYED\)", fault) is not None,
                        "injection was not exactly stdout writev4 EIO")
                self.assertEqual(actual, {"late_accepted_socket_inodes": [],
                                          "late_peer": {"state": "eof", "wire_hex": ""},
                                          "idle_peer": {"state": "eof", "wire_hex": ""}},
                                 "UNRELEASED_SUCCESSFUL_ACCEPT_PRE_EXIT: owned late tuple/inode must close while server is alive")


if __name__ == "__main__":
    unittest.main(verbosity=2)
