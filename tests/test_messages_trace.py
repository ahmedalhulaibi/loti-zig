import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_examples import BIN, ROOT

FIXTURES = ROOT / "testdata/inputs"


def inspect_trace(text):
    pairs, rings, submissions, closed, badf, cloexec = [], set(), 0, set(), [], set()
    for line in text.splitlines():
        if re.match(r"(?:sendmsg|recvmsg)\(", line):
            raise ValueError("SynchronousMessageOperationDetected")
        pair = re.fullmatch(r"socketpair\(AF_UNIX, SOCK_DGRAM\|SOCK_CLOEXEC\|SOCK_NONBLOCK, 0, \[(\d+), (\d+)\]\)\s+= 0", line)
        if pair:
            pairs.append([int(pair[1]), int(pair[2])])
        enter = re.fullmatch(r"io_uring_enter\((\d+), 1, 1, IORING_ENTER_GETEVENTS, NULL, 8\)\s+= 1", line)
        if enter:
            rings.add(int(enter[1])); submissions += 1
        close = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if close:
            closed.add(int(close[1]))
        invalid = re.fullmatch(r"fcntl\((\d+), F_GETFD\)\s+= -1 EBADF \(Bad file descriptor\)", line)
        if invalid:
            fd = int(invalid[1])
            if fd not in closed:
                raise ValueError("MessageCloseNotObservedBeforeQuery")
            badf.append(fd)
        flags = re.fullmatch(r"fcntl\((\d+), F_GETFD\)\s+= 0x1 \(flags FD_CLOEXEC\)", line)
        if flags:
            cloexec.add(int(flags[1]))
    if len(pairs) != 1 or len(rings) != 1 or submissions != 14:
        raise ValueError("IncompleteMessageSubmissionTrace")
    if len(badf) != 4 or any(fd not in badf for fd in pairs[0]) or len(cloexec) != 2 or not rings.issubset(cloexec):
        raise ValueError("IncompleteMessageOwnershipTrace")
    return {"socket_pairs": 1, "submissions": 14, "rings": 1, "queried_closures": 4, "queried_cloexec": 2,
            "synchronous_sendmsg": 0, "synchronous_recvmsg": 0}


class MessageTraceContracts(unittest.TestCase):
    def test_actual_async_messages_ownership_and_damaged_traces(self):
        """Kills synchronous stand-ins, omitted submissions/closures/CLOEXEC checks and permissive trace parsing."""
        expected = {"socket_pairs": 1, "submissions": 14, "rings": 1, "queried_closures": 4, "queried_cloexec": 2,
                    "synchronous_sendmsg": 0, "synchronous_recvmsg": 0}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.trace"
            result = subprocess.run(["strace", "-qq", "-e", "trace=socketpair,sendmsg,recvmsg,fcntl,close,io_uring_enter",
                                     "-o", str(path), str(BIN / "reference-messages"), str(FIXTURES / "messages-input.bin"), "3"],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), json.loads((FIXTURES / "messages-report.json").read_text()))
            try:
                report = inspect_trace(path.read_text())
            except ValueError as error:
                self.fail(f"Invalid public message trace: {error}")
            self.assertEqual(report, expected)
        original = (FIXTURES / "messages.trace").read_text()
        self.assertEqual(inspect_trace(original), expected)
        for case in json.loads((FIXTURES / "messages-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(original.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
