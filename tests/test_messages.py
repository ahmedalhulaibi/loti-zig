import json
from pathlib import Path
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run

FIXTURES = ROOT / "testdata/inputs"
CLOEXEC = 1073741824


def request(operation, tag, vectors, control_capacity, operation_flags, descriptor="socket"):
    return {"operation": operation, "tag": tag, "descriptor": descriptor, "length": 1, "offset": 0,
            "flags": 0, "operation_flags": operation_flags, "vector_lengths": vectors,
            "control_capacity": control_capacity, "name_supplied": False, "name_length": 0}


def completed(tag, result):
    return {"tag": tag, "result": result, "flags": 0}


def send(tag, payload, control_length=20, descriptor="socket", result=None):
    split = len(payload) // 2
    return {"request": request("SENDMSG", tag, [split, len(payload) - split], 24, 16448, descriptor),
            "cqe": completed(tag, len(payload) if result is None else result),
            "control": {"length": control_length, "level": 1, "type": 1}, "input_unchanged": True}


def receive(tag, payload, capacity, control=False, whole=False, result=None, descriptor="socket"):
    split = capacity // 2
    flags = 64 | (CLOEXEC if control else 0) | (32 if whole else 0)
    copied = min(capacity, len(payload)) if result is None else 0
    message_flags = (CLOEXEC if control else 0) | (32 if len(payload) > capacity and result is None else 0)
    return {"request": request("RECVMSG", tag, [split, capacity - split], 24 if control and whole else 0, flags, descriptor),
            "cqe": completed(tag, (len(payload) if whole else copied) if result is None else result),
            "message": {"flags": message_flags, "control_length": 24 if control and whole else 0, "name_length": 0},
            "storage": list(payload[:copied]) + [165] * (capacity + 16 - copied),
            "control": {"length": 20, "level": 1, "type": 1} if control and whole else None}


def expected_report(payload, capacity):
    main_receive = receive(3, payload, capacity, control=True, whole=True)
    truncated = receive(7, bytes([0, 255, 90]), 2, control=True)
    truncated["message"]["flags"] |= 8
    return {"abi": {"header_size": 16, "control_length": 20, "control_space": 24, "alignment": 8},
            "empty_before": receive(1, b"", 1, result=-11), "sent": send(2, payload),
            "source_closed_after_send": True, "received": main_receive,
            "empty_after": receive(4, b"", 1, result=-11),
            "passed_file": {"request": {"operation": "READ", "tag": 5, "length": len(payload) + 1, "offset": 0, "flags": 0},
                            "cqe": completed(5, len(payload)), "storage": list(payload) + [165] * 17, "cloexec": True},
            "truncation": {"sent": send(6, bytes([0, 255, 90])), "received": truncated,
                           "empty_after": receive(8, b"", 1, result=-11), "descriptor_delta": 0},
            "failures": [send(10, b"", descriptor="invalid", result=-9),
                         receive(11, b"", 1, result=-9, descriptor="invalid"),
                         send(12, b"", descriptor="ring", result=-88),
                         receive(13, b"", 1, result=-88, descriptor="ring"),
                         send(14, b"", control_length=8, result=-22), send(15, b"", result=-9)],
            "cleanup": {"received_closed": True, "received_close_delta": -1,
                        "sockets_closed": [True, True], "descriptor_delta_from_initial": 1, "ring_still_open": True}}


class MessageContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None, derandomize=True)
    @given(payload=st.binary(max_size=4097), capacity=st.integers(min_value=0, max_value=4097))
    @example(payload=(FIXTURES / "messages-empty.bin").read_bytes(), capacity=0)
    @example(payload=(FIXTURES / "messages-boundary.bin").read_bytes(), capacity=1)
    def test_datagram_vectors_flags_and_rights_follow_byte_ownership_model(self, payload, capacity):
        """Kills vector offsets, truncation=result/initialized-byte confusion, zero=EOF, missing rights/CLOEXEC and FD leaks."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(payload)
            self.assertEqual(json.loads(run("reference-messages", path, capacity).stdout), expected_report(payload, capacity))
            self.assertEqual(path.read_bytes(), payload)

    def test_literal_fixed_plans_and_typed_invalid_inputs(self):
        """Separate hand-pinned shape catches a drifting model; rejection preserves source and bounds allocations."""
        source = FIXTURES / "messages-input.bin"
        literal = json.loads((FIXTURES / "messages-report.json").read_text())
        for _ in range(2):
            self.assertEqual(json.loads(run("reference-messages", source, 3).stdout), literal)
        for case in json.loads((FIXTURES / "messages-plans.json").read_text()):
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "input"
                payload = (FIXTURES / case["input"]).read_bytes()
                path.write_bytes(payload)
                self.assertEqual(json.loads(run("reference-messages", path, case["capacity"]).stdout), expected_report(payload, case["capacity"]))
                self.assertEqual(path.read_bytes(), payload)
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            missing, symlink, oversized = parent / "missing", parent / "symlink", parent / "oversized"
            symlink.symlink_to(source)
            oversized.write_bytes(b"a" * 4098)
            inputs = {"source": str(source), "missing": str(missing), "symlink": str(symlink),
                      "directory": str(parent), "character": "/dev/null", "oversized": str(oversized)}
            before = {"source": source.read_bytes(), "oversized": oversized.read_bytes()}
            for case in json.loads((FIXTURES / "messages-invalid-inputs.json").read_text()):
                with self.subTest(case=case["name"]):
                    args = [inputs.get(value, value) for value in case["arguments"]]
                    result = run("reference-messages", *args, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertEqual(result.stderr.splitlines()[0], ("error: " + case["error"]).encode())
                    self.assertEqual(source.read_bytes(), before["source"])
                    self.assertEqual(oversized.read_bytes(), before["oversized"])
            self.assertEqual(symlink.is_symlink(), True)


if __name__ == "__main__":
    unittest.main()
