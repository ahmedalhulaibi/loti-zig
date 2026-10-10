"""Basic enter's mask ABI is not EXT_ARG's deadline ABI."""

import json
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import unittest

from tests.test_examples import ROOT, run

FIXTURES = ROOT / "testdata/inputs"


def expected_report():
    def resolve(value):
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            if value and isinstance(value[0], str):
                return sum(1 << (int(getattr(signal, name)) - 1) for name in value)
            return [resolve(item) for item in value]
        return value
    report = resolve(json.loads((FIXTURES / "ordinary-signal-report.json").read_text()))
    assert isinstance(report, dict)
    report["mask_bytes"] = (max(map(int, signal.valid_signals())) + 7) // 8
    report["initial_mask"] = sum(1 << (int(item) - 1) for item in signal.pthread_sigmask(signal.SIG_BLOCK, []))
    return report


def inspect_trace(text):
    entries = []
    rings = set()
    sends = []
    handlers = []
    returns = []
    awaiting_handler = False
    for line in text.splitlines():
        if line.startswith("io_uring_enter("):
            row = re.fullmatch(r"io_uring_enter\((\d+), (\d+), (\d+), ([A-Z0-9_|]+), (NULL|\[[A-Z0-9 ]*\]), (\d+)\)\s+= (.+)", line)
            if row is None:
                raise ValueError("InvalidOrdinaryEnterTrace")
            fd, submitted, minimum, flags, mask, size, result = row.groups()
            rings.add(int(fd))
            if result.startswith("? ERESTARTNOHAND "):
                result = "interrupted"
            elif result.startswith("-1 EINTR "):
                result = "interrupted"
            entries.append((int(submitted), int(minimum), flags, mask, int(size), result))
        elif line.startswith("tgkill("):
            row = re.fullmatch(r"tgkill\((\d+), (\d+), SIGUSR1\)\s+= 0", line)
            if row is None or row[1] != row[2]:
                raise ValueError("WrongOrdinarySignalTarget")
            sends.append(int(row[1]))
        elif line.startswith("--- SIGUSR1 "):
            if awaiting_handler:
                raise ValueError("IncompleteOrdinaryHandlerTrace")
            awaiting_handler = True
        elif awaiting_handler and line.startswith("rt_sigprocmask("):
            row = re.fullmatch(r"rt_sigprocmask\(SIG_BLOCK, NULL, (\[[A-Z0-9 ]*\]), 8\)\s+= 0", line)
            if row is None:
                raise ValueError("IncompleteOrdinaryHandlerTrace")
            handlers.append(row[1])
            awaiting_handler = False
        elif line.startswith("rt_sigreturn("):
            row = re.fullmatch(r"rt_sigreturn\(\{mask=(\[[A-Z0-9 ]*\])\}\)\s+= (.+)", line)
            if row is None:
                raise ValueError("InvalidOrdinaryReturnTrace")
            result = "interrupted" if row[2].startswith("-1 EINTR ") else row[2]
            returns.append((row[1], result))
    wanted = [(1, 0, "0", "NULL", 8, "1"),
              (0, 1, "IORING_ENTER_GETEVENTS", "[USR2 WINCH]", 8, "interrupted"),
              (1, 2, "IORING_ENTER_GETEVENTS", "NULL", 8, "1"),
              (2, 0, "0", "NULL", 8, "2"),
              (0, 1, "IORING_ENTER_GETEVENTS", "[USR1 WINCH]", 8, "0"),
              (0, 2, "IORING_ENTER_GETEVENTS", "NULL", 8, "0"),
              (1, 1, "IORING_ENTER_GETEVENTS", "NULL", 8, "1")]
    if len(rings) != 1 or entries != wanted:
        raise ValueError("WrongOrdinaryEnterSequence")
    if len(sends) != 2 or len(set(sends)) != 1:
        raise ValueError("WrongOrdinarySignalTarget")
    if awaiting_handler or handlers != ["[USR1 USR2 WINCH]", "[USR1 USR2]"]:
        raise ValueError("WrongOrdinaryHandlerMasks")
    if returns != [("[USR1 USR2]", "interrupted"), ("[USR2]", "0")]:
        raise ValueError("WrongOrdinaryReturnMasks")
    return {"enter_calls": 7, "submissions": 5, "rings": 1,
            "basic_mask_waits": 3, "ext_arg_calls": 0,
            "self_thread_signals": 2, "handler_masks": handlers,
            "restored_return_masks": [row[0] for row in returns]}


class OrdinarySignalContracts(unittest.TestCase):
    def test_pending_masks_timer_cqes_and_queued_nop_ownership(self):
        expected = expected_report()
        parent_mask = signal.pthread_sigmask(signal.SIG_BLOCK, [])
        parent_action = signal.getsignal(signal.SIGUSR1)
        for index in range(5):
            with self.subTest(process=index):
                self.assertEqual(json.loads(run("reference-signals", "--ordinary").stdout), expected)
        for arguments in [["--ordinary", "extra"], ["--ordinary", "--ordinary"]]:
            with self.subTest(arguments=arguments):
                result = run("reference-signals", *arguments, success=False)
                self.assertEqual((result.returncode, result.stdout, result.stderr.splitlines()[0]),
                                 (1, b"", b"error: ExpectedNoSignalArguments"))
        self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK, []), parent_mask)
        self.assertIs(signal.getsignal(signal.SIGUSR1), parent_action)

    def test_actual_basic_abi_delivery_and_damaged_traces(self):
        original = (FIXTURES / "ordinary-signal.trace").read_text()
        expected = inspect_trace(original)
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace"
            result = subprocess.run(["strace", "-qq", "-e", "trace=io_uring_enter,tgkill,rt_sigprocmask,rt_sigreturn",
                                     "-o", str(trace), str(ROOT / "zig-out/bin/reference-signals"), "--ordinary"],
                                    capture_output=True, timeout=5)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertEqual(json.loads(result.stdout), expected_report())
            try:
                observed = inspect_trace(trace.read_text())
            except ValueError as error:
                self.fail(f"Invalid public ordinary signal trace: {error}")
            self.assertEqual(observed, expected)
        for case in json.loads((FIXTURES / "ordinary-signal-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                self.assertIn(case["old"], original)
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(original.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
