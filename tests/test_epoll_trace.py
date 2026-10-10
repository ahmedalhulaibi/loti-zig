import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_examples import ROOT


def inspect_trace(text):
    waits, rings, submissions = [], set(), 0
    for line in text.splitlines():
        if re.match(r"epoll_ctl\(", line):
            raise ValueError("SynchronousEpollControlDetected")
        enter = re.fullmatch(r"io_uring_enter\((\d+), 1, 1, IORING_ENTER_GETEVENTS, NULL, 8\)\s+= 1", line)
        if enter:
            rings.add(int(enter[1]))
            submissions += 1
        if re.match(r"epoll_pwait\(", line):
            row = re.fullmatch(r"epoll_pwait\(\d+, (.*), 1, 0, NULL, 8\)\s+= ([01])", line)
            if row is None:
                raise ValueError("InvalidEpollWaitArguments")
            data, count = row.groups()
            if data == "[]" and count == "0":
                waits.append([])
            else:
                event = re.fullmatch(r"\[\{events=EPOLLIN, data=\{u32=(\d+), u64=(\d+)\}\}\]", data)
                hexadecimal = re.fullmatch(r"\[\{events=EPOLLIN, data=(0x[0-9a-f]+)\}\]", data)
                if count != "1":
                    raise ValueError("InvalidEpollWaitEvent")
                if event is not None:
                    token = int(event[2])
                    if int(event[1]) != token & 0xffffffff:
                        raise ValueError("InvalidEpollWaitEvent")
                elif hexadecimal is not None:
                    token = int(hexadecimal[1], 16)
                else:
                    raise ValueError("InvalidEpollWaitEvent")
                waits.append([{"mask": 1, "token": token}])
    if len(rings) != 1 or submissions != 11:
        raise ValueError("WrongEpollSubmissionCount")
    expected = [[{"mask": 1, "token": 72623859790382856}], [],
                [{"mask": 1, "token": 18364758544493064720}], [], [], []]
    if waits != expected:
        raise ValueError("WrongEpollReadinessSequence")
    return {"rings": 1, "submissions": 11, "waits": waits, "synchronous_controls": 0}


class EpollTraceContracts(unittest.TestCase):
    def test_actual_waits_async_controls_and_damaged_traces(self):
        """Kills fabricated readiness, synchronous ctl substitutions, truncated event tags and vacuous traces."""
        fixtures = ROOT / "testdata/inputs"
        commands = json.loads((fixtures / "epoll-literal-plan.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "epoll.trace"
            result = subprocess.run(["strace", "-qq", "-e", "trace=io_uring_enter,epoll_ctl,epoll_pwait", "-o", str(trace),
                                     str(ROOT / "zig-out/bin/reference-epoll"), *commands], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), json.loads((fixtures / "epoll-report.json").read_text()))
            try:
                observed = inspect_trace(trace.read_text())
            except ValueError as error:
                self.fail(f"Invalid public EPOLL_CTL trace: {error}")
            self.assertEqual(observed, inspect_trace((fixtures / "epoll.trace").read_text()))
        original = (fixtures / "epoll.trace").read_text()
        for case in json.loads((fixtures / "epoll-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                damaged = original.replace(case["old"], case["new"], case["count"])
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(damaged)
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
