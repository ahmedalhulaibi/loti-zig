"""Legacy provided-buffer EOF/zero-request ownership at the public CLI boundary."""

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run

INPUTS = ROOT / "testdata/inputs"
NAMES = ["provide", "eof", "remove_consumed_eof", "eof_exhausted", "provide_for_zero_length",
         "zero_length_read", "remove_consumed_zero_length", "zero_length_exhausted",
         "provide_for_data", "read", "provide_for_cleanup", "remove_final", "eof_after_remove"]


def expected(payload):
    count = min(len(payload), 64)
    poison = [165] * 64
    filled = list(payload[:64]) + [165] * (64 - count)
    commands = [("PROVIDE_BUFFERS", 0, 64, 257), ("READ", 0, 64, len(payload)),
                ("REMOVE_BUFFERS", 0, 0, 0), ("READ", -105, 64, len(payload)),
                ("PROVIDE_BUFFERS", 0, 64, 257), ("READ", count, 0, 0),
                ("REMOVE_BUFFERS", 0, 0, 0), ("READ", -105, 0, 0),
                ("PROVIDE_BUFFERS", 0, 64, 257), ("READ", count, 64, 0),
                ("PROVIDE_BUFFERS", 0, 64, 257), ("REMOVE_BUFFERS", 1, 0, 0),
                ("READ", -105, 64, len(payload))]
    steps = []
    for tag, (name, (operation, result, length, offset)) in enumerate(zip(NAMES, commands, strict=True), 1):
        selected = tag in {2, 6, 10}
        storage = filled if tag in {6, 7, 8, 10} else poison
        steps.append({"name": name,
                      "request": {"operation": operation, "tag": tag,
                                  "descriptor": "input" if operation == "READ" else "count",
                                  "count": None if operation == "READ" else 1,
                                  "offset": offset, "length": length,
                                  "flags": 32 if operation == "READ" else 0, "group": 7},
                      "cqe": {"tag": tag, "result": result, "flags": 16842753 if selected else 0,
                              "buffer_id": 257 if selected else None, "no_buffer_selected": not selected},
                      "storage": storage})
    return {"group": 7, "id": 257, "input_size": len(payload), "cursor_before": 0,
            "cursor_after": 0, "steps": steps, "queued": 0, "cq_ready": 0}


def inspect_trace(text):
    setups, enters, positions = [], [], []
    reads = []
    for index, line in enumerate(text.splitlines()):
        setup = re.fullmatch(r"io_uring_setup\(8, \{flags=0, .*\}\)\s+= (\d+)", line)
        if setup:
            setups.append((index, int(setup[1])))
        enter = re.fullmatch(r"io_uring_enter\((\d+), (\d+), (\d+), ([A-Z_0-9|]+), (NULL|0x[0-9a-f]+), (\d+)\)\s+= (-?\d+)", line)
        if enter:
            enters.append((index, int(enter[1]), int(enter[2]), int(enter[3]), enter[4], enter[5], int(enter[6]), int(enter[7])))
        elif line.startswith("io_uring_enter("):
            raise ValueError("InvalidBufferZeroEnterTrace")
        position = re.fullmatch(r"lseek\((\d+), 0, SEEK_CUR\)\s+= (-?\d+)", line)
        if position:
            positions.append((index, int(position[1]), int(position[2])))
        read = re.match(r"(?:read|readv|pread64|preadv)\((\d+),", line)
        if read:
            reads.append(int(read[1]))
    if len(setups) != 1 or len(enters) != 13 or len(positions) != 2:
        raise ValueError("IncompleteBufferZeroTrace")
    ring = setups[0][1]
    source = positions[0][1]
    if positions[1][1] != source or source == ring or [row[2] for row in positions] != [0, 0]:
        raise ValueError("WrongBufferZeroCursor")
    if any(row[1:] != (ring, 1, 1, "IORING_ENTER_GETEVENTS", "NULL", 8, 1) for row in enters):
        raise ValueError("WrongBufferZeroEnterArguments")
    if not setups[0][0] < positions[0][0] < enters[0][0] < enters[-1][0] < positions[1][0]:
        raise ValueError("WrongBufferZeroObservationOrder")
    if source in reads:
        raise ValueError("SynchronousBufferZeroRead")
    return {"rings": 1, "submissions": 13, "ordinary_waits": 13,
            "cursor_queries": 2, "absolute_cursor_preserved": True, "synchronous_source_reads": 0}


class ProvidedBufferZeroContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None)
    @given(payload=st.binary(min_size=1, max_size=4097))
    @example(payload=(INPUTS / "provided-buffer-zero-input.bin").read_bytes())
    @example(payload=b"\x5a" * 64)
    @example(payload=b"\x6b" * 65)
    @example(payload=b"\xff" * 4097)
    def test_zero_result_flags_and_requested_zero_length_follow_buffer_ownership(self, payload):
        """Kills result-positive ownership, EOF len0 proxy, wrong offset/group/ID, stale poison and early reuse."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(payload)
            self.assertEqual(json.loads(run("reference-buffers", source, "--zero-result").stdout), expected(payload))
            self.assertEqual(source.read_bytes(), payload)

    def test_literal_and_invalid_modes_keep_the_default_contract(self):
        """Kills fabricated zero-result report, broad flags/error acceptance and default CLI drift."""
        source = INPUTS / "provided-buffer-zero-input.bin"
        self.assertEqual(json.loads(run("reference-buffers", source, "--zero-result").stdout),
                         json.loads((INPUTS / "provided-buffer-zero-report.json").read_text()))
        old = INPUTS / "provided-buffer-input.bin"
        self.assertEqual(json.loads(run("reference-buffers", old).stdout),
                         json.loads((INPUTS / "provided-buffer-report.json").read_text()))
        with tempfile.TemporaryDirectory() as directory:
            empty, large, missing = (Path(directory) / name for name in ("empty", "large", "missing"))
            empty.write_bytes(b"")
            large.write_bytes(b"x" * 4098)
            cases = {"missing_argument": ([], "ExpectedInputAndBufferCommands"),
                     "extra_command": ([source, "--zero-result", "read"], "BufferZeroModeNeedsNoCommands"),
                     "empty": ([empty, "--zero-result"], "ExpectedNonemptyRegularInput"),
                     "large": ([large, "--zero-result"], "BufferZeroInputTooLarge"),
                     "missing": ([missing, "--zero-result"], "FileNotFound"),
                     "directory": ([directory, "--zero-result"], "ExpectedNonemptyRegularInput"),
                     "device": (["/dev/null", "--zero-result"], "ExpectedNonemptyRegularInput")}
            for name, (args, error) in cases.items():
                with self.subTest(case=name):
                    result = run("reference-buffers", *args, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertEqual(result.stderr.decode().splitlines()[0], "error: " + error)
            self.assertEqual(source.read_bytes(), bytes([0, 255, 90, 105, 103]))
            self.assertEqual(large.read_bytes(), b"x" * 4098)

    def test_actual_submissions_absolute_cursor_and_damaged_traces(self):
        """Kills fabricated cursor, missing/implicit submissions and synchronous source read proxies."""
        literal = (INPUTS / "provided-buffer-zero.trace").read_text()
        oracle = {"rings": 1, "submissions": 13, "ordinary_waits": 13,
                  "cursor_queries": 2, "absolute_cursor_preserved": True, "synchronous_source_reads": 0}
        self.assertEqual(inspect_trace(literal), oracle)
        cases = json.loads((INPUTS / "provided-buffer-zero-invalid-traces.json").read_text())
        self.assertEqual(len(cases), 8)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(literal.count(case["old"]), 1)
                with self.assertRaises(ValueError) as failure:
                    inspect_trace(literal.replace(case["old"], case["new"]))
                self.assertEqual(failure.exception.args, (case["error"],))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace"
            result = subprocess.run(["strace", "-qq", "-e",
                                     "trace=io_uring_setup,io_uring_enter,lseek,read,readv,pread64,preadv", "-o", str(path),
                                     str(ROOT / "zig-out/bin/reference-buffers"), str(INPUTS / "provided-buffer-zero-input.bin"),
                                     "--zero-result"], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            self.assertEqual(json.loads(result.stdout), json.loads((INPUTS / "provided-buffer-zero-report.json").read_text()))
            try:
                actual = inspect_trace(path.read_text())
            except ValueError as error:
                self.fail(f"Invalid public buffer-zero trace: {error}")
            self.assertEqual(actual, oracle)
