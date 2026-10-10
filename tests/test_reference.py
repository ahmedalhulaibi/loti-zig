"""Reference programs verify real mappings, completions, registrations and SQEs."""

import json
from pathlib import Path
import tempfile
import unittest

from tests.test_examples import run


class ReferenceContracts(unittest.TestCase):
    def test_raw_sqe_bindings_execute_and_memory_advice_changes_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            payload = bytes(range(128))
            path.write_bytes(payload)
            header, separator, body = run("reference-raw", path).stdout.partition(b"\n")
            self.assertEqual(separator, b"\n")
            self.assertEqual(json.loads(header), {
                "openat2": True, "fadvise_result": 0, "madvise_result": 0,
                "memory_zeroed": True, "read_result": 64,
            })
            self.assertEqual(body, payload[:64])

    def test_mapping_sizes_dontfork_and_actual_raw_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(bytes(range(128)))
            self.assertEqual(json.loads(run("reference-setup", path).stdout), {
                "sq_entries": 8, "cq_entries": 32, "sqe_size": 64, "cqe_size": 16,
                "raw_read": 64, "dontfork": True,
            })

    def test_copy_and_manual_ack_are_distinct_and_deadline_really_expires(self):
        self.assertEqual(json.loads(run("reference-completion").stdout), {
            "empty": 0, "pending": 4, "space": 4,
            "copied": [1, 2, 3, 4], "manual": [5, 6, 7, 8],
            "drained": 0, "timed_out": True, "timer_result": -62,
        })

    def test_registration_helpers_and_async_notification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(b"registration input\n")
            self.assertEqual(json.loads(run("reference-registration", path).stdout), {
                "buffers": True, "files_updated": True, "async_notifications": 1,
                "personality_result": 0, "probe_nop": True, "standalone_probe_nop": True,
            })

    def test_every_preparation_has_the_expected_opcode_and_correlation_tag(self):
        expected = [
            "NOP", "READ", "WRITE", "READV", "WRITEV", "FSYNC", "CLOSE", "OPENAT",
            "OPENAT2", "FALLOCATE", "STATX", "FADVISE", "MADVISE", "SPLICE", "ACCEPT",
            "CONNECT", "RECV", "SEND", "RECVMSG", "SENDMSG", "EPOLL_CTL", "POLL_ADD",
            "POLL_REMOVE", "READ_FIXED", "WRITE_FIXED", "FILES_UPDATE", "PROVIDE_BUFFERS",
            "REMOVE_BUFFERS", "TIMEOUT", "TIMEOUT_REMOVE", "ASYNC_CANCEL", "LINK_TIMEOUT",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(b"constructor reference\n")
            records = [json.loads(line) for line in run("reference-submission", path).stdout.splitlines()]
            self.assertEqual([row["operation"] for row in records], expected)
            self.assertEqual([row["tag"] for row in records], list(range(1, 33)))
            self.assertEqual([row["flags"] for row in records], [4] + [0] * 29 + [4, 0])
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


if __name__ == "__main__":
    unittest.main()
