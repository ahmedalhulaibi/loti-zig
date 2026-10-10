"""Private SQPOLL sleep/wakeup, registered I/O and pre-exit ownership contracts."""

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "zig-out/bin/sq-poll"
FIXTURES = ROOT / "testdata/inputs"


def inspect_trace(text):
    setup, registered, unregistered, entries, closes, queries = [], [], [], [], [], []
    for order, line in enumerate(text.splitlines()):
        match = re.fullmatch(r"io_uring_setup\(8, \{flags=IORING_SETUP_SQPOLL, sq_thread_cpu=0, sq_thread_idle=10, .*\}\)\s+= (\d+)", line)
        if match:
            setup.append((order, int(match[1])))
        match = re.fullmatch(r"io_uring_register\((\d+), IORING_REGISTER_FILES, \[(\d+)\], 1\)\s+= 0", line)
        if match:
            registered.append((order, int(match[1]), int(match[2])))
        match = re.fullmatch(r"io_uring_register\((\d+), IORING_UNREGISTER_FILES, NULL, 0\)\s+= 0", line)
        if match:
            unregistered.append((order, int(match[1])))
        if line.startswith("io_uring_enter("):
            match = re.fullmatch(r"io_uring_enter\((\d+), (\d+), (\d+), ([A-Z_|0-9]+), (.*), (\d+)\)\s+= (\d+)", line)
            if match is None:
                raise ValueError("InvalidPollingEnterTrace")
            entries.append((order, int(match[1]), int(match[2]), int(match[3]), match[4], match[5], int(match[6]), int(match[7])))
        match = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if match:
            closes.append((order, int(match[1])))
        match = re.fullmatch(r"fcntl\((\d+), F_GETFD\)\s+= (-1 EBADF \(Bad file descriptor\)|0x1 \(flags FD_CLOEXEC\))", line)
        if match:
            queries.append((order, int(match[1]), match[2]))
    if len(setup) != 1 or len(registered) != 1 or len(unregistered) != 1:
        raise ValueError("IncompletePollingSetupAndRegistration")
    ring, file = setup[0][1], registered[0][2]
    if registered[0][1] != ring or unregistered[0][1] != ring or not setup[0][0] < registered[0][0] < unregistered[0][0]:
        raise ValueError("WrongPollingRegisteredDescriptor")
    phase, previous_wait = 0, False
    for order, descriptor, submitted, minimum, flags, argument, size, result in entries:
        if descriptor != ring or not registered[0][0] < order < unregistered[0][0]:
            raise ValueError("WrongPollingEnterOwnership")
        if flags == "IORING_ENTER_SQ_WAKEUP":
            if (submitted, minimum, argument, size) != (1, 0, "NULL", 8):
                raise ValueError("WrongPollingWakeArguments")
            phase += 1
            previous_wait = False
        elif flags == "IORING_ENTER_GETEVENTS|IORING_ENTER_EXT_ARG":
            argument_valid = re.fullmatch(r"\{sigmask=NULL, sigmask_sz=0, (?:min_time|min_wait_usec)=0, ts=\{tv_sec=1, tv_nsec=0\}\}", argument)
            if (submitted, minimum, size, result) != (0, 1, 24, 0) or argument_valid is None or phase == 0 or previous_wait:
                raise ValueError("WrongPollingCompletionGuard")
            previous_wait = True
        else:
            raise ValueError("UnexpectedPollingEnterFlags")
    if phase != 3:
        raise ValueError("WrongPollingWakeCount")
    # The close before the EBADF query cannot be process-exit cleanup.
    if len(queries) != 2 or queries[0][1:] != (file, "-1 EBADF (Bad file descriptor)") or queries[1][1:] != (ring, "0x1 (flags FD_CLOEXEC)"):
        raise ValueError("IncompletePollingQueriedOwnership")
    file_closes = [order for order, descriptor in closes if descriptor == file and registered[0][0] < order]
    ring_closes = [order for order, descriptor in closes if descriptor == ring and setup[0][0] < order]
    if len(file_closes) != 1 or len(ring_closes) != 1 or not unregistered[0][0] < file_closes[0] < queries[0][0] < queries[1][0] < ring_closes[0]:
        raise ValueError("WrongPollingOwnershipOrder")
    return {"rings": 1, "registered_files": 1, "wake_calls": 3,
            "completion_guards": sum(entry[4] == "IORING_ENTER_GETEVENTS|IORING_ENTER_EXT_ARG" for entry in entries),
            "queried_closures": 1, "ring_retained_after_unregister": True}


class PollingWakeContracts(unittest.TestCase):
    def test_observed_sleep_and_cqes_preserve_default_file_bytes(self):
        """Kills elapsed-time/fabricated-flag proxies, wrong fixed indexes/offsets and premature CQ consumption."""
        expected = json.loads((FIXTURES / "sqpoll-wakeup-report.json").read_text())
        payload = (FIXTURES / "sqpoll-wakeup-output.bin").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output"
            for _ in range(5):
                result = subprocess.run([str(BIN), str(path), "--observe"], capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, b"")
                self.assertEqual(json.loads(result.stdout), expected)
                self.assertEqual(path.read_bytes(), payload)
            result = subprocess.run([str(BIN), str(path)], capture_output=True, timeout=10)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, payload, b""))
            self.assertEqual(path.read_bytes(), payload)
            for case in json.loads((FIXTURES / "sqpoll-wakeup-invalid-arguments.json").read_text()):
                with self.subTest(case=case["name"]):
                    path.write_bytes(payload)
                    args = [str(path) if argument == "$output" else argument for argument in case["arguments"]]
                    result = subprocess.run([str(BIN), *args], capture_output=True, timeout=10)
                    self.assertEqual((result.returncode, result.stdout), (1, b""))
                    self.assertEqual(result.stderr.splitlines()[0].decode(), "error: " + case["error"])
                    self.assertEqual(path.read_bytes(), payload)

    def test_actual_private_ring_wakeup_calls_and_damaged_traces(self):
        """Kills metadata-only wakeup/ownership and omitted, wrong-flag or implicit-submission syscall claims."""
        expected = json.loads((FIXTURES / "sqpoll-wakeup-report.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            path, trace = Path(directory) / "output", Path(directory) / "trace"
            result = subprocess.run(["strace", "-qq", "-e", "trace=io_uring_setup,io_uring_register,io_uring_enter,close,fcntl", "-o", str(trace), str(BIN), str(path), "--observe"], capture_output=True, timeout=10)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertEqual(json.loads(result.stdout), expected)
            self.assertEqual(path.read_bytes(), (FIXTURES / "sqpoll-wakeup-output.bin").read_bytes())
            try:
                live = inspect_trace(trace.read_text())
            except ValueError as error:
                self.fail(f"Invalid public polling trace: {error}")
            self.assertEqual({key: value for key, value in live.items() if key != "completion_guards"},
                             {"rings": 1, "registered_files": 1, "wake_calls": 3,
                              "queried_closures": 1, "ring_retained_after_unregister": True})
            self.assertIn(live["completion_guards"], [0, 1, 2, 3])
        fixture = (FIXTURES / "sqpoll-wakeup.trace").read_text()
        self.assertEqual(inspect_trace(fixture), {"rings": 1, "registered_files": 1, "wake_calls": 3,
                                               "completion_guards": 1, "queried_closures": 1,
                                               "ring_retained_after_unregister": True})
        for case in json.loads((FIXTURES / "sqpoll-wakeup-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(fixture.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
