"""Per-I/O APPEND is not the file's persistent O_APPEND or an SQE flag."""

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run

FIXTURES = ROOT / "testdata/inputs"
APPEND = 16
UNKNOWN = 1 << 31
CURRENT = (1 << 64) - 1


def operation(tag, payload_size, offset=0, flags=0, descriptor="memory", read=False, result=None):
    return {"request": {"operation": "READ" if read else "WRITE", "tag": tag,
                        "descriptor": descriptor, "length": payload_size, "offset": offset,
                        "flags": 0, "operation_flags": flags},
            "cqe": {"user_data": tag, "result": payload_size if result is None else result, "flags": 0}}


def snapshot(data, position):
    return {"position": position, "size": len(data), "bytes_hex": data.hex(), "append": False}


def expected_report(payload):
    marker = b"\xa5\x5a"
    appended = marker + payload
    overwritten = payload + appended[len(payload):]
    final = overwritten + payload
    return {"seed": {**operation(1, 2), "after": snapshot(marker, 0)},
            "explicit_append": {**operation(2, len(payload), flags=APPEND), "after": snapshot(appended, 1)},
            "ordinary": {**operation(3, len(payload)), "after": snapshot(overwritten, 1)},
            "current_append": {**operation(4, len(payload), CURRENT, APPEND), "after": snapshot(final, len(final))},
            "failures": [operation(10, len(payload), flags=UNKNOWN, result=-95),
                         operation(11, 9, flags=UNKNOWN, read=True, result=-95),
                         operation(12, len(payload), flags=APPEND, descriptor="invalid", result=-9)],
            "failed_read_storage": [165] * 9,
            "after_failures": snapshot(final, len(final)),
            "cleanup": {"memory_cloexec": True, "source_closed": True,
                        "memory_closed": True, "ring_still_open": True}}


def inspect_trace(text):
    rows = text.splitlines()
    memory = []
    rings = set()
    submissions = 0
    status_queries = []
    closed = set()
    queried = set()
    cloexec = set()
    for line in rows:
        if line.startswith("memfd_create("):
            row = re.fullmatch(r'memfd_create\("loti-rwf", MFD_CLOEXEC\)\s+= (\d+)', line)
            if row is None:
                raise ValueError("InvalidRwfMemoryFileTrace")
            memory.append(int(row[1]))
        elif line.startswith("io_uring_enter("):
            row = re.fullmatch(r"io_uring_enter\((\d+), 1, 1, IORING_ENTER_GETEVENTS, NULL, 8\)\s+= 1", line)
            if row is None:
                raise ValueError("InvalidRwfSubmissionTrace")
            rings.add(int(row[1]))
            submissions += 1
        elif memory and re.match(r"(?:write|pwrite64|writev|pwritev|pwritev2)\(" + str(memory[0]) + r",", line):
            raise ValueError("SynchronousRwfWriteDetected")
        elif line.startswith("fcntl("):
            status = re.fullmatch(r"fcntl\((\d+), F_GETFL\)\s+= (0x[0-9a-f]+) \(flags ([A-Z0-9_|]+)\)", line)
            if status:
                if not memory or int(status[1]) != memory[0]:
                    raise ValueError("WrongRwfStatusDescriptor")
                value = int(status[2], 16)
                if value & 1024 or "O_APPEND" in status[3] or value & 3 != 2:
                    raise ValueError("StickyRwfAppendDetected")
                status_queries.append(int(status[1]))
            badf = re.fullmatch(r"fcntl\((\d+), F_GETFD\)\s+= -1 EBADF \(Bad file descriptor\)", line)
            if badf:
                if int(badf[1]) not in closed:
                    raise ValueError("RwfCloseNotObservedBeforeQuery")
                queried.add(int(badf[1]))
            good = re.fullmatch(r"fcntl\((\d+), F_GETFD\)\s+= 0x1 \(flags FD_CLOEXEC\)", line)
            if good:
                cloexec.add(int(good[1]))
        elif line.startswith("close("):
            row = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
            if row:
                closed.add(int(row[1]))
    if len(memory) != 1 or len(rings) != 1 or submissions != 7:
        raise ValueError("IncompleteRwfSubmissionTrace")
    if len(status_queries) != 5:
        raise ValueError("IncompleteRwfStatusTrace")
    if memory[0] not in queried or len(queried) != 2 or cloexec != {memory[0], *rings}:
        raise ValueError("IncompleteRwfOwnershipTrace")
    return {"memory_files": 1, "rings": 1, "submissions": 7, "nonappend_status_queries": 5,
            "queried_closures": 2, "queried_cloexec": 2, "synchronous_memory_writes": 0}


class RwfContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None, derandomize=True)
    @given(payload=st.binary(min_size=1, max_size=4097))
    @example(payload=b"\x00")
    @example(payload=bytes(range(256)) * 16 + b"\xff")
    def test_append_and_ordinary_writes_follow_per_request_byte_and_cursor_model(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(payload)
            self.assertEqual(json.loads(run("reference-rwf", source).stdout), expected_report(payload))
            self.assertEqual(source.read_bytes(), payload)
            self.assertEqual(sorted(item.name for item in Path(directory).iterdir()), ["source"])

    def test_literal_and_invalid_inputs_preserve_source_and_create_no_output(self):
        source = FIXTURES / "rwf-input.bin"
        before = source.read_bytes()
        literal = json.loads((FIXTURES / "rwf-report.json").read_text())
        for _ in range(2):
            self.assertEqual(json.loads(run("reference-rwf", source).stdout), literal)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owned = {"empty": b"", "large": bytes(4098), "valid": before}
            for name, data in owned.items():
                (root / name).write_bytes(data)
            (root / "alias").symlink_to(root / "valid")
            replacements = {"$empty": str(root / "empty"), "$large": str(root / "large"),
                            "$valid": str(root / "valid"), "$symlink": str(root / "alias"),
                            "$missing": str(root / "missing"), "$directory": str(root)}
            initial = sorted(path.name for path in root.iterdir())
            for case in json.loads((FIXTURES / "rwf-invalid-inputs.json").read_text()):
                with self.subTest(case=case["name"]):
                    arguments = [replacements.get(value, value) for value in case["arguments"]]
                    result = run("reference-rwf", *arguments, success=False)
                    self.assertEqual((result.returncode, result.stdout, result.stderr.splitlines()[0]),
                                     (1, b"", ("error: " + case["error"]).encode()))
            self.assertEqual(sorted(path.name for path in root.iterdir()), initial)
            self.assertTrue((root / "alias").is_symlink())
            for name, data in owned.items():
                self.assertEqual((root / name).read_bytes(), data)
        self.assertEqual(source.read_bytes(), before)

    def test_actual_async_memory_file_flags_and_ownership_and_damaged_traces(self):
        fixture = (FIXTURES / "rwf.trace").read_text()
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace"
            result = subprocess.run(["strace", "-qq", "-e", "trace=memfd_create,fcntl,close,io_uring_enter,write,pwrite64,writev,pwritev,pwritev2",
                                     "-o", str(trace), str(ROOT / "zig-out/bin/reference-rwf"), str(FIXTURES / "rwf-input.bin")],
                                    capture_output=True, timeout=10)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertEqual(json.loads(result.stdout), json.loads((FIXTURES / "rwf-report.json").read_text()))
            try:
                observed = inspect_trace(trace.read_text())
            except ValueError as error:
                self.fail(f"Invalid public per-I/O flag trace: {error}")
            self.assertEqual(observed, inspect_trace(fixture))
        for case in json.loads((FIXTURES / "rwf-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                self.assertIn(case["old"], fixture)
                with self.assertRaises(ValueError) as raised:
                    inspect_trace(fixture.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
