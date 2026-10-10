import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_examples import ROOT


def inspect_deadlines(text):
    """Independent syscall oracle; an empty_timeout JSON boolean is insufficient."""
    fields = r"io_uring_enter\((\d+), (\d+), (\d+), ([A-Z0-9_|]+), \{sigmask=([^,]+), sigmask_sz=(\d+), min_wait_usec=(\d+), ts=\{tv_sec=(-?\d+), tv_nsec=(\d+)\}\}, (\d+)\) = -1 ETIME \(Timer expired\)"
    rows = []
    rings = set()
    submissions = 0
    for line in text.splitlines():
        header = re.match(r"io_uring_enter\((\d+),", line)
        if header:
            rings.add(int(header[1]))
        submit = re.fullmatch(r"io_uring_enter\(\d+, 1, 0, 0, NULL, 8\)\s+= 1", line)
        submissions += int(submit is not None)
        error = re.search(r"= -1 (\w+) \(", line)
        if error is None:
            continue
        match = re.fullmatch(fields, line)
        if match is None:
            raise ValueError("InvalidPollDeadlineTrace")
        _, submitted, minimum, flags, mask, mask_size, minimum_time, seconds, nanoseconds, size = match.groups()
        rows.append({"submitted": int(submitted), "minimum": int(minimum),
                     "flags": sorted(flags.split("|")), "mask": mask,
                     "mask_size": int(mask_size), "minimum_time": int(minimum_time),
                     "seconds": int(seconds), "nanoseconds": int(nanoseconds), "size": int(size), "errno": "ETIME"})
    if len(rings) != 1 or submissions != 6:
        raise ValueError("InvalidPollSubmissionTrace")
    if len(rows) != 4:
        raise ValueError("WrongPollDeadlineCount")
    expected = {"submitted": 0, "minimum": 1,
                "flags": ["IORING_ENTER_EXT_ARG", "IORING_ENTER_GETEVENTS"],
                "mask": "NULL", "mask_size": 0, "minimum_time": 0,
                "seconds": 0, "nanoseconds": 1000000, "size": 24, "errno": "ETIME"}
    if rows != [expected] * 4:
        raise ValueError("WrongPollDeadlineArguments")
    return {"rings": 1, "submissions": 6, "deadline_waits": rows}


class PollDeadlineContracts(unittest.TestCase):
    def test_native_deadline_waits_and_damaged_traces(self):
        """Kills bypassed/fabricated empty checks and weak timeout/count/mask trace parsing."""
        fixtures = ROOT / "testdata/inputs"
        commands = json.loads((fixtures / "poll-literal-plan.json").read_text())
        literal = json.loads((fixtures / "poll-report.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "poll.trace"
            result = subprocess.run(["strace", "-qq", "-e", "trace=io_uring_enter", "-o", str(trace),
                                     str(ROOT / "zig-out/bin/reference-poll"), *commands], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), literal)
            try:
                observed = inspect_deadlines(trace.read_text())
            except ValueError as error:
                self.fail(f"Invalid public poll deadline trace: {error}")
            self.assertEqual(observed, inspect_deadlines((fixtures / "poll-deadline.trace").read_text()))
        original = (fixtures / "poll-deadline.trace").read_text()
        for case in json.loads((fixtures / "poll-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                damaged = original.replace(case["old"], case["new"], case["count"])
                with self.assertRaises(ValueError) as raised:
                    inspect_deadlines(damaged)
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
