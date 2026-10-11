"""Selected EOF error must stop before pool reset/re-provision, not after the report."""

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tests.test_examples import ROOT

INPUTS = ROOT / "testdata/inputs"


def inspect_failure(text):
    setup, enters, cursor, closed = [], [], [], []
    for index, line in enumerate(text.splitlines()):
        match = re.fullmatch(r"io_uring_setup\(8, \{flags=0, .*\}\)\s+= (\d+)", line)
        if match:
            setup.append((index, int(match[1])))
        match = re.fullmatch(r"io_uring_enter\((\d+), (\d+), (\d+), ([A-Z_0-9|]+), (NULL|0x[0-9a-f]+), (\d+)\)\s+= (-?\d+)", line)
        if match:
            enters.append((index, int(match[1]), int(match[2]), int(match[3]), match[4], match[5], int(match[6]), int(match[7])))
        match = re.fullmatch(r"lseek\((\d+), 0, SEEK_CUR\)\s+= (-?\d+)", line)
        if match:
            cursor.append((index, int(match[1]), int(match[2])))
        match = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if match:
            closed.append((index, int(match[1])))
    if len(setup) != 1 or len(enters) != 2 or len(cursor) != 1:
        raise ValueError("IncompleteBufferZeroFailureTrace")
    ring = setup[0][1]
    source = cursor[0][1]
    if source == ring or cursor[0][2] != 0:
        raise ValueError("WrongBufferZeroFailureCursor")
    if any(row[1:] != (ring, 1, 1, "IORING_ENTER_GETEVENTS", "NULL", 8, 1) for row in enters):
        raise ValueError("WrongBufferZeroFailureEnterArguments")
    ring_close = [row[0] for row in closed if row[1] == ring]
    source_close = [row[0] for row in closed if row[1] == source]
    if len(ring_close) != 1 or not source_close:
        raise ValueError("IncompleteBufferZeroFailureCleanup")
    if not setup[0][0] < cursor[0][0] < enters[0][0] < enters[1][0] < ring_close[0] < source_close[0]:
        raise ValueError("WrongBufferZeroFailureOwnershipOrder")
    return {"rings": 1, "submissions_before_error": 2, "cursor_queries": 1,
            "further_pool_requests": 0, "ring_closed_before_source": True, "source_closed": True}


class ProvidedBufferZeroFailureContracts(unittest.TestCase):
    def test_invalid_eof_cqe_stops_before_further_pool_operations(self):
        """Kills end-of-plan-only validation, speculative re-provision, invented error and unclosed ring/source."""
        fixture = (INPUTS / "provided-buffer-zero-failure.trace").read_text()
        oracle = {"rings": 1, "submissions_before_error": 2, "cursor_queries": 1,
                  "further_pool_requests": 0, "ring_closed_before_source": True, "source_closed": True}
        self.assertEqual(inspect_failure(fixture), oracle)
        self.assertEqual(inspect_failure((INPUTS / "provided-buffer-zero-failure-reused.trace").read_text()), oracle)
        cases = json.loads((INPUTS / "provided-buffer-zero-failure-invalid-traces.json").read_text())
        self.assertEqual(len(cases), 7)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(fixture.count(case["old"]), 1)
                with self.assertRaises(ValueError) as failure:
                    inspect_failure(fixture.replace(case["old"], case["new"]))
                self.assertEqual(failure.exception.args, (case["error"],))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace"
            source = INPUTS / "provided-buffer-zero-input.bin"
            before = source.read_bytes()
            result = subprocess.run(["strace", "-qq", "-e", "trace=io_uring_setup,io_uring_enter,lseek,close", "-o", str(path),
                                     str(ROOT / "zig-out/bin/reference-buffers"), str(source), "--zero-result", "--fail-eof"],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr.decode().splitlines()[0], "error: UnexpectedBufferZeroSelection")
            try:
                actual = inspect_failure(path.read_text())
            except ValueError as error:
                self.fail(f"Invalid public buffer-zero failure trace: {error}")
            self.assertEqual(actual, oracle)
            self.assertEqual(source.read_bytes(), before)
