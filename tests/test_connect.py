import json
import re
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path

from hypothesis import given, settings, strategies as st
from tests.test_examples import BIN, CASES, ROOT, run

FIXTURES = ROOT / "testdata/inputs"


def endpoint(port, family=2):
    return {"family": family, "address": [127, 0, 0, 1], "port": port}


def request(tag, descriptor, port, length=16, family=2):
    return {"operation": "CONNECT", "tag": tag, "descriptor": descriptor, "length": 0,
            "address_length": length, "address": endpoint(port, family), "flags": 0}


def failure(tag, descriptor, port, result, length=16, family=2, closed=None, peer_error=None):
    return {"request": request(tag, descriptor, port, length, family),
            "cqe": {"tag": tag, "result": result, "flags": 0}, "closed": closed, "peer_error": peer_error}


def expected_report(peer, local, guard):
    return {"connection": {"request": request(1, "client", peer), "cqe": {"tag": 1, "result": 0, "flags": 0},
                           "local": {"address": endpoint(local), "length": 16},
                           "peer": {"address": endpoint(peer), "length": 16},
                           "flags": {"nonblocking": True, "cloexec": True}},
            "failures": [failure(1000000, "invalid", peer, -9), failure(1000001, "ring", peer, -88),
                         failure(1000002, "probe", peer, -22, length=1, closed=True),
                         failure(1000003, "probe", peer, -97, family=1, closed=True),
                         failure(1000004, "probe", guard, -111, closed=True, peer_error=107),
                         failure(1000005, "client", peer, -106)],
            "refusal_address": {"address": endpoint(guard), "length": 16},
            "peer_unchanged": True, "descriptors_closed": {"client": True, "guard": True}, "ring_still_open": True}


def literal(ports):
    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return ports.get(value, value) if isinstance(value, str) else value
    return replace(json.loads((FIXTURES / "connect-report.json").read_text()))


def inspect_trace(text):
    """External syscall/address oracle, not a native output decoder reused by the model."""
    sockets, live, rings, submissions, bound, addresses = 0, set(), set(), 0, None, {}
    for line in text.splitlines():
        if re.match(r"(?:connect|listen)\(", line):
            raise ValueError("UnexpectedSynchronousConnectOrListener")
        opened = re.fullmatch(r"socket\(AF_INET, SOCK_STREAM\|SOCK_CLOEXEC\|SOCK_NONBLOCK, IPPROTO_IP\)\s+= (\d+)", line)
        if opened:
            fd = int(opened[1])
            if fd in live:
                raise ValueError("ConnectDescriptorReusedWhileLive")
            live.add(fd)
            sockets += 1
        closed = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if closed:
            live.discard(int(closed[1]))
        submit = re.fullmatch(r"io_uring_enter\((\d+), 1, 0, 0, NULL, 8\)\s+= 1", line)
        if submit:
            rings.add(int(submit[1])); submissions += 1
        bind = re.fullmatch(r'bind\((\d+), \{sa_family=AF_INET, sin_port=htons\(0\), sin_addr=inet_addr\("127\.0\.0\.1"\)\}, 16\)\s+= 0', line)
        if bind:
            if bound is not None:
                raise ValueError("ExpectedOneRefusalGuard")
            bound = int(bind[1])
        query = re.fullmatch(r'(getsockname|getpeername)\((\d+), \{sa_family=AF_INET, sin_port=htons\((\d+)\), sin_addr=inet_addr\("127\.0\.0\.1"\)\}, \[16\]\)\s+= 0', line)
        if query:
            method, fd, port = query.groups()
            key = (method, int(fd))
            if key in addresses or not 1 <= int(port) <= 65535:
                raise ValueError("InvalidConnectAddressQuery")
            addresses[key] = int(port)
    if sockets != 5 or live or len(rings) != 1 or submissions != 7 or bound is None:
        raise ValueError("IncompleteConnectSyscallsOrCleanup")
    guard = addresses.pop(("getsockname", bound), None)
    peers = [(fd, port) for (method, fd), port in addresses.items() if method == "getpeername"]
    if guard is None or len(addresses) != 2 or len(peers) != 1:
        raise ValueError("IncompleteConnectEndpointQueries")
    fd, peer = peers[0]
    local = addresses.get(("getsockname", fd))
    if local is None:
        raise ValueError("IncompleteConnectEndpointQueries")
    return {"sockets": 5, "closed": 5, "submissions": 7, "rings": 1, "peer": peer, "local": local, "guard": guard,
            "synchronous_connects": 0, "listeners": 0}


invalid_ports = st.one_of(
    st.integers(min_value=65536, max_value=2**128).map(str),
    st.just("0"),
    st.tuples(st.text(alphabet="0123456789", max_size=40), st.sampled_from(["+", "-", "x", " ", "é", "_"]),
              st.text(alphabet="0123456789", max_size=40)).map(lambda parts: "".join(parts)),
)


class ConnectContracts(unittest.TestCase):
    def test_native_connection_matches_external_peer_and_syscalls(self):
        """Kills client/listener confusion, wrong length/byte order, fake success/query/cleanup and synchronous substitution."""
        for index in range(25):
            with self.subTest(process=index), socket.socket() as server, tempfile.TemporaryDirectory() as directory:
                server.bind(("127.0.0.1", 0)); server.listen(1); server.settimeout(2)
                peer = server.getsockname()[1]
                path = Path(directory) / "connect.trace"
                result = subprocess.run(["strace", "-qq", "-e", "trace=socket,bind,listen,connect,getsockname,getpeername,close,io_uring_enter",
                                         "-o", str(path), str(BIN / "reference-connect"), str(peer)], capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, b"")
                with server.accept()[0] as connected:
                    connected.settimeout(2)
                    self.assertEqual(connected.getsockname(), ("127.0.0.1", peer))
                    host, local = connected.getpeername()
                    self.assertEqual(host, "127.0.0.1")
                    self.assertEqual(connected.recv(1), b"")
                try:
                    observed = inspect_trace(path.read_text())
                except ValueError as error:
                    self.fail(f"Invalid public CONNECT trace: {error}")
                self.assertEqual(observed, {"sockets": 5, "closed": 5, "submissions": 7, "rings": 1,
                                            "peer": peer, "local": local, "guard": observed["guard"],
                                            "synchronous_connects": 0, "listeners": 0})
                expected = expected_report(peer, local, observed["guard"])
                self.assertEqual(json.loads(result.stdout), expected)
                self.assertEqual(json.loads(result.stdout), literal({"$peer": peer, "$local": local, "$guard": observed["guard"]}))
        original = (FIXTURES / "connect.trace").read_text()
        self.assertEqual(inspect_trace(original), {"sockets": 5, "closed": 5, "submissions": 7, "rings": 1,
                                                   "peer": 43123, "local": 41234, "guard": 42345,
                                                   "synchronous_connects": 0, "listeners": 0})
        for case in json.loads((FIXTURES / "connect-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(original.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])

    @settings(max_examples=CASES, deadline=None, derandomize=True)
    @given(invalid_ports)
    def test_invalid_port_language_is_rejected(self, port):
        """Kills signed/nondecimal/out-of-range parsing that could dial an unintended endpoint."""
        result = run("reference-connect", port, success=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr.splitlines()[0], b"error: InvalidConnectPort")

    def test_arguments_refusal_and_pre_setup_rejection(self):
        """Kills missing/extra operands, late validation and success reported for a non-listening peer."""
        for case in json.loads((FIXTURES / "connect-invalid-arguments.json").read_text()):
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "invalid.trace"
                result = subprocess.run(["strace", "-qq", "-e", "trace=socket,io_uring_setup", "-o", str(path),
                                         str(BIN / "reference-connect"), *case["arguments"]], capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.splitlines()[0], ("error: " + case["error"]).encode())
                self.assertEqual(path.read_bytes(), b"")
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            result = run("reference-connect", reserved.getsockname()[1], success=False)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr.splitlines()[0], b"error: RequestedPeerConnectionFailed")


if __name__ == "__main__":
    unittest.main()
