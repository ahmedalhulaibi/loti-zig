import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_copy_short import FIXTURES, limits
from tests.test_examples import BIN


def inspect_recovery(text, original):
    value = lambda n: "RLIM64_INFINITY" if n == (1 << 64) - 1 else str(n)
    saved = f"{{rlim_cur={value(original['soft'])}, rlim_max={value(original['hard'])}}}"
    cap = f"{{rlim_cur=2, rlim_max={value(original['hard'])}}}"
    expected = [("NULL", saved), (cap, "NULL"), (saved, "NULL"), ("NULL", saved)]
    actual, order, rings = [], [], set()
    for line in text.splitlines():
        matched = re.fullmatch(r"prlimit64\(0, RLIMIT_FSIZE, (NULL|\{rlim_cur=[^,}]+, rlim_max=[^}]+\}), (NULL|\{rlim_cur=[^,}]+, rlim_max=[^}]+\})\)\s+= 0", line)
        if matched:
            actual.append(matched.groups()); order.append("query" if matched[1] == "NULL" else "set")
        submitted = re.fullmatch(r"io_uring_enter\((\d+), 1, 0, 0, NULL, 8\)\s+= 1", line)
        if submitted:
            rings.add(int(submitted[1])); order.append("submit")
    if actual != expected:
        raise ValueError("CopyFailureLimitsNotRestoredAndQueried")
    if order != ["query", "set", "submit", "set", "query"] or len(rings) != 1:
        raise ValueError("WrongCopyFailureRecoveryOrder")
    return {"submissions": 1, "limit_queries": 2, "limit_sets": 2, "restored_before_error_return": True}


class ShortCopyRecoveryContracts(unittest.TestCase):
    def test_actual_invalid_read_restores_and_queries_before_error_return(self):
        """Kills exit-only cleanup, hidden restoration failure and unobserved/error-first resource rollback."""
        original = limits()
        with tempfile.TemporaryDirectory() as directory:
            output, trace = Path(directory) / "new-output", Path(directory) / "recovery.trace"
            source = FIXTURES / "copy-short-input.bin"; before = source.read_bytes()
            result = subprocess.run(["strace", "-qq", "-e", "trace=prlimit64,io_uring_enter", "-o", str(trace),
                                     str(BIN / "cp"), str(source), str(output), "--short-write", "2", "--fail-read"],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr.splitlines()[0], b"error: IoCompletionFailed")
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(output.read_bytes(), b"")
            try:
                actual = inspect_recovery(trace.read_text(), original)
            except ValueError as error:
                self.fail(f"Invalid public short-copy recovery trace: {error}")
            self.assertEqual(actual, {"submissions": 1, "limit_queries": 2, "limit_sets": 2, "restored_before_error_return": True})
        fixture = (FIXTURES / "copy-short-recovery.trace").read_text()
        unlimited = {"soft": (1 << 64) - 1, "hard": (1 << 64) - 1}
        self.assertEqual(inspect_recovery(fixture, unlimited), actual)
        for case in json.loads((FIXTURES / "copy-short-recovery-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_recovery(fixture.replace(case["old"], case["new"], case["count"]), unlimited)
                self.assertEqual(str(raised.exception), case["error"])
        self.assertEqual(limits(), original)


if __name__ == "__main__":
    unittest.main()
