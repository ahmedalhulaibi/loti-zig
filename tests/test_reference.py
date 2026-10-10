"""Reference programs verify real mappings, completions, registrations and SQEs."""

import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st

from tests.test_examples import CASES, run

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_FIXTURE = (ROOT / "testdata/inputs/registration-original.txt").read_bytes()
REPLACEMENT_FIXTURE = (ROOT / "testdata/inputs/registration-replacement.txt").read_bytes()
COMPLETION_PLANS = json.loads((ROOT / "testdata/inputs/completion-plans.json").read_text())


class ReferenceContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None)
    @given(payload=st.binary(max_size=8193))
    @example(payload=b"")
    @example(payload=bytes(range(128)))
    def test_raw_sqe_bindings_execute_and_memory_advice_changes_memory(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(payload)
            header, separator, body = run("reference-raw", path).stdout.partition(b"\n")
            self.assertEqual(separator, b"\n")
            self.assertEqual(json.loads(header), {
                "openat2": True, "fadvise_result": 0, "madvise_result": 0,
                "memory_zeroed": True, "read_result": min(64, len(payload)),
                "sync_range": {"offset": 0, "length": 4096, "flags": 7, "result": 0},
                "sync_failures": [-22, -9],
            })
            self.assertEqual(body, payload[:64])
            self.assertEqual(path.read_bytes(), payload)

    def test_mapping_sizes_dontfork_and_actual_raw_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(bytes(range(128)))
            for options in [[], ["--separate-mappings"]]:
                with self.subTest(options=options):
                    header, separator, body = run("reference-setup", path, *options).stdout.partition(b"\n")
                    self.assertEqual(separator, b"\n")
                    self.assertEqual(json.loads(header), {
                        "sq_entries": 8, "cq_entries": 32, "sqe_size": 64, "cqe_size": 16,
                        "raw_read": 64, "raw_cq_entries": 512, "mapping_count": 3 if options else 2,
                        "reads": 1025, "raw_bytes": 48704,
                        "raw_sha256": hashlib.sha256(bytes(range(95)) * 512 + bytes(range(64))).hexdigest(),
                        "cq_region_matches": True,
                        "dontfork": True, "fork_excluded": True, "fd_inherited": True, "released": True,
                    })
                    self.assertEqual(body, bytes(range(64)))

    def test_copy_and_manual_ack_are_distinct_and_deadline_really_expires(self):
        self.assertEqual(json.loads(run("reference-completion").stdout), {
            "empty": 0, "pending": 4, "space": 4,
            "copied": [1, 2, 3, 4], "manual": [5, 6, 7, 8],
            "drained": 0, "timed_out": True, "timer_result": -62,
        })

    @settings(max_examples=CASES, deadline=None)
    @given(capacities=st.lists(st.integers(min_value=0, max_value=8), max_size=30)
           .map(lambda prefix: prefix + [8, 0]))
    @example(capacities=COMPLETION_PLANS["default"])
    @example(capacities=COMPLETION_PLANS["all_at_once"])
    @example(capacities=COMPLETION_PLANS["singletons"])
    @example(capacities=COMPLETION_PLANS["zeros"])
    @example(capacities=COMPLETION_PLANS["wrap_boundary"])
    def test_nonblocking_completion_capacities_follow_queue_model(self, capacities):
        observed = json.loads(run("reference-completion", *map(str, capacities)).stdout)
        self.assertEqual(observed, {
            "empty": 0, "pending": 4, "space": 4,
            "copied": [1, 2, 3, 4], "manual": [5, 6, 7, 8],
            "drained": 0, "timed_out": True, "timer_result": -62,
        })

    @settings(max_examples=CASES, deadline=None)
    @given(original=st.binary(max_size=8193), replacement=st.binary(max_size=8193))
    @example(original=ORIGINAL_FIXTURE, replacement=REPLACEMENT_FIXTURE)
    @example(original=b"", replacement=REPLACEMENT_FIXTURE)
    @example(original=ORIGINAL_FIXTURE, replacement=b"")
    def test_registration_helpers_and_async_notification(self, original, replacement):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "original"
            second = Path(directory) / "replacement"
            first.write_bytes(original)
            second.write_bytes(replacement)
            before, after = original[:64], replacement[:64]
            self.assertEqual(json.loads(run("reference-registration", first, second).stdout), {
                "buffers": True, "files_updated": True, "async_notifications": 1,
                "personality_result": 0, "probe_nop": True, "standalone_probe_nop": True,
                "fixed_files": {
                    "before": {"tag": 10, "slot": 1, "res": len(before), "flags": 0, "bytes": list(before)},
                    "sparse": {"tag": 11, "slot": 0, "res": -9, "flags": 0, "bytes": []},
                    "after_sync_update": {"tag": 12, "slot": 1, "res": len(after), "flags": 0, "bytes": list(after)},
                    "replacement_fd_closed": True,
                    "async_update": {"tag": 13, "res": 1, "flags": 0},
                    "after_async_update": {"tag": 14, "slot": 1, "res": len(before), "flags": 0, "bytes": list(before)},
                    "removed": {"tag": 15, "slot": 1, "res": -9, "flags": 0, "bytes": []},
                    "unregistered": {"tag": 16, "slot": 1, "res": -9, "flags": 0, "bytes": []},
                },
            })
            self.assertEqual(first.read_bytes(), original)
            self.assertEqual(second.read_bytes(), replacement)

    def test_registration_rejects_missing_or_extra_inputs(self):
        first = ROOT / "testdata/inputs/registration-original.txt"
        second = ROOT / "testdata/inputs/registration-replacement.txt"
        cases = {"none": (), "single": (first,), "extra": (first, second, "extra")}
        for name, args in cases.items():
            with self.subTest(case=name):
                result = run("reference-registration", *args, success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.decode().splitlines()[0], "error: ExpectedTwoInputFiles")

    def test_every_preparation_has_the_expected_opcode_and_correlation_tag(self):
        expected = [
            "NOP", "READ", "WRITE", "READV", "WRITEV", "FSYNC", "CLOSE", "OPENAT",
            "OPENAT2", "FALLOCATE", "STATX", "FADVISE", "MADVISE", "SPLICE", "ACCEPT",
            "CONNECT", "RECV", "SEND", "RECVMSG", "SENDMSG", "EPOLL_CTL", "POLL_ADD",
            "POLL_REMOVE", "READ_FIXED", "WRITE_FIXED", "FILES_UPDATE", "PROVIDE_BUFFERS",
            "REMOVE_BUFFERS", "TIMEOUT", "TIMEOUT_REMOVE", "ASYNC_CANCEL", "LINK_TIMEOUT",
            "SYNC_FILE_RANGE",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(b"constructor reference\n")
            records = [json.loads(line) for line in run("reference-submission", path).stdout.splitlines()]
            self.assertEqual([row["operation"] for row in records], expected)
            self.assertEqual([row["tag"] for row in records], list(range(1, 34)))
            self.assertEqual([row["flags"] for row in records], [4] + [0] * 29 + [4, 0, 0])
            for row in records:
                self.assertEqual(set(row), {"tag", "operation", "length", "flags", "buffer_index"})
            for index in [1, 2, 11, 12, 13, 16, 17, 23, 24]:
                self.assertEqual(records[index]["length"], 4096)
            self.assertEqual(records[3]["length"], 1)
            self.assertEqual(records[4]["length"], 1)
            self.assertEqual(records[8]["length"], 24)
            self.assertEqual(records[25]["length"], 1)
            self.assertEqual(records[26]["buffer_index"], 1)
            self.assertEqual(records[27]["buffer_index"], 1)
            self.assertEqual(records[32], {
                "tag": 33, "operation": "SYNC_FILE_RANGE", "length": 4096,
                "flags": 0, "buffer_index": 0,
            })


if __name__ == "__main__":
    unittest.main()
