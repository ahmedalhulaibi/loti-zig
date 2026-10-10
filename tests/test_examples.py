"""Public CLI contracts. Expected file bytes are independent of the examples."""

import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "zig-out/bin"
CASES = int(os.environ.get("LOTI_TEST_CASES", "40"))
PROBE_NAMES = json.loads((ROOT / "testdata/inputs/probe-opcodes.json").read_text())
SUPPORT_ONLY_FLAGS = (1).to_bytes(2, sys.byteorder) * 256


def run(name, *args, success=True):
    result = subprocess.run(
        [str(BIN / name), *map(str, args)], capture_output=True, timeout=10
    )
    if success and result.returncode != 0:
        raise AssertionError(f"{name} exited {result.returncode}: {result.stderr.decode(errors='replace')}")
    return result


class ExampleContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None)
    @given(
        name=st.sampled_from(["readv", "raw-cat", "cat"]),
        payloads=st.lists(st.binary(max_size=131073), min_size=1, max_size=3),
    )
    @example(name="cat", payloads=[b"", bytes(range(256)) * 257, b"last"])
    @example(name="raw-cat", payloads=[bytes(range(256)) * 257])
    @example(name="readv", payloads=[bytes(range(256)) * 257])
    def test_readers_preserve_concatenated_bytes(self, name, payloads):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, data in enumerate(payloads):
                path = Path(directory) / f"input-{index}"
                path.write_bytes(data)
                paths.append(path)
            self.assertEqual(run(name, *paths).stdout, b"".join(payloads))

    @settings(max_examples=CASES, deadline=None)
    @given(payload=st.binary(max_size=524289))
    @example(payload=b"")
    @example(payload=bytes(range(256)) * 2049)
    def test_copy_preserves_bytes_across_buffer_boundaries(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.write_bytes(payload)
            output.write_bytes(b"old bytes that must not remain")
            run("cp", source, output)
            self.assertEqual(output.read_bytes(), payload)
            self.assertEqual(source.read_bytes(), payload)

    def test_copy_rejects_alias_without_destroying_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source, alias = Path(directory) / "source", Path(directory) / "alias"
            payload = b"same inode must not be truncated"
            source.write_bytes(payload)
            alias.hardlink_to(source)
            for target in [source, alias]:
                with self.subTest(target=target.name):
                    result = run("cp", source, target, success=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(source.read_bytes(), payload)

    def test_readers_preserve_bytes_when_stdout_is_a_regular_file(self):
        payload = bytes(range(256)) * 257
        with tempfile.TemporaryDirectory() as directory:
            source, destination = Path(directory) / "source", Path(directory) / "stdout"
            source.write_bytes(payload)
            for name in ["readv", "raw-cat", "cat"]:
                with self.subTest(program=name), destination.open("wb") as stdout:
                    result = subprocess.run([str(BIN / name), str(source)], stdout=stdout,
                                            capture_output=False, stderr=subprocess.PIPE, timeout=10)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(destination.read_bytes(), payload)

    def test_copy_rejects_unsupported_kinds_before_discarding_data(self):
        payload = b"input and prior output must remain intact"
        with tempfile.TemporaryDirectory() as directory:
            source, destination = Path(directory) / "source", Path(directory) / "destination"
            source.write_bytes(payload)
            destination.write_bytes(payload)
            for input_path, output_path, error in [
                (Path("/dev/null"), destination, b"error: ExpectedRegularFileOrBlockDevice"),
                (source, Path("/dev/null"), b"error: ExpectedRegularOutputFile"),
            ]:
                with self.subTest(input=input_path.name, output=output_path.name):
                    result = run("cp", input_path, output_path, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stderr.partition(b"\n")[0], error)
                    self.assertEqual(source.read_bytes(), payload)
                    self.assertEqual(destination.read_bytes(), payload)

    def test_linked_execution_and_failure_cancellation(self):
        message = b"Hello, io_uring!"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "linked"
            for fail, expected in [(False, [len(message), len(message), 0]), (True, [len(message), -9, -125])]:
                with self.subTest(fail_read=fail):
                    args = [path, "--fail-read"] if fail else [path]
                    report = json.loads(run("link", *args).stdout)
                    self.assertEqual(report, {"results": expected, "data": "" if fail else message.decode()})
                    self.assertEqual(path.read_bytes(), message)

    def test_fixed_buffers_write_and_read_registered_ranges(self):
        poem = b"What is this life if, full of care,\nWe have no time to stand and stare."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixed"
            self.assertEqual(run("fixed-buffers", path).stdout, poem)
            self.assertEqual(path.read_bytes(), poem)

    def test_polling_survives_an_idle_poller(self):
        expected = b"Submission queue polling.\nAfter the idle period.\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "polling"
            self.assertEqual(run("sq-poll", path).stdout, expected)
            self.assertEqual(path.read_bytes(), expected)

    def test_eventfd_counter_and_completion_are_real(self):
        payload = b"completion notification\x00binary\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "event-input"
            path.write_bytes(payload)
            result = run("register-eventfd", path)
            self.assertEqual(result.stdout, payload)
            self.assertEqual(json.loads(result.stderr), {"notifications": 1, "user_data": 1, "result": len(payload)})

    def test_probe_emits_kernel_report_for_every_known_opcode(self):
        records = [json.loads(line) for line in run("probe").stdout.splitlines()]
        raw = run("probe", "--raw").stdout
        self.assertEqual(len(raw), 2064)
        order = "<" if sys.byteorder == "little" else ">"
        last, length, reserved, *reserved_words = struct.unpack_from(order + "BBHIII", raw)
        self.assertEqual((reserved, reserved_words), (0, [0, 0, 0]))
        self.assertEqual(length, last + 1)
        kernel_flags = []
        for opcode in range(length):
            op, padding, flags, padding_word = struct.unpack_from(order + "BBHI", raw, 16 + 8 * opcode)
            self.assertEqual((op, padding, padding_word), (opcode, 0, 0))
            kernel_flags.append(flags)
        self.assertEqual(raw[16 + 8 * length:], bytes(8 * (256 - length)))
        self.assertEqual(records, [
            {"opcode": opcode, "name": name,
             "supported": opcode <= last and opcode < length and bool(kernel_flags[opcode] & 1)}
            for opcode, name in enumerate(PROBE_NAMES)
        ])
        self.assertEqual(records[0], {"opcode": 0, "name": "NOP", "supported": True})
        cycles = {"mixed": [False, True, False, True, False, True],
                  "regression-high-flag": [False]}
        for case, cycle in cycles.items():
            with self.subTest(snapshot=case):
                fixture = ROOT / f"testdata/inputs/probe-{case}-{sys.byteorder}.bin"
                decoded = [json.loads(line) for line in run("probe", "--snapshot", fixture).stdout.splitlines()]
                self.assertEqual(decoded, [
                    {"opcode": opcode, "name": name, "supported": cycle[opcode % len(cycle)]}
                    for opcode, name in enumerate(PROBE_NAMES)
                ])

    @settings(max_examples=CASES, deadline=None)
    @given(last=st.integers(min_value=0, max_value=255),
           length=st.integers(min_value=0, max_value=255),
           flags=st.binary(min_size=512, max_size=512))
    @example(last=0, length=59, flags=SUPPORT_ONLY_FLAGS)
    @example(last=58, length=1, flags=SUPPORT_ONLY_FLAGS)
    @example(last=58, length=0, flags=SUPPORT_ONLY_FLAGS)
    def test_probe_snapshot_support_respects_both_bounds_and_flag_bit(self, last, length, flags):
        payload = bytearray(2064)
        payload[0], payload[1] = last, length
        for opcode in range(256):
            payload[16 + 8 * opcode] = opcode
            payload[18 + 8 * opcode:20 + 8 * opcode] = flags[2 * opcode:2 * opcode + 2]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.bin"
            path.write_bytes(payload)
            records = [json.loads(line) for line in run("probe", "--snapshot", path).stdout.splitlines()]
            self.assertEqual(records, [
                {"opcode": opcode, "name": name,
                 "supported": opcode <= last and opcode < length and
                 bool(int.from_bytes(flags[2 * opcode:2 * opcode + 2], sys.byteorder) & 1)}
                for opcode, name in enumerate(PROBE_NAMES)
            ])
            self.assertEqual(path.read_bytes(), bytes(payload))

    def test_probe_rejects_invalid_arguments_and_snapshot_sizes(self):
        fixture = ROOT / f"testdata/inputs/probe-mixed-{sys.byteorder}.bin"
        with tempfile.TemporaryDirectory() as directory:
            short, long = Path(directory) / "short", Path(directory) / "long"
            short.write_bytes(fixture.read_bytes()[:-1])
            long.write_bytes(fixture.read_bytes() + bytes(1))
            cases = {
                "unknown": (("--unknown",), "ExpectedProbeArguments"),
                "missing_snapshot": (("--snapshot",), "ExpectedProbeArguments"),
                "extra_raw": (("--raw", fixture), "ExpectedProbeArguments"),
                "extra_snapshot": (("--snapshot", fixture, "extra"), "ExpectedProbeArguments"),
                "short": (("--snapshot", short), "InvalidProbeSnapshotSize"),
                "long": (("--snapshot", long), "InvalidProbeSnapshotSize"),
            }
            for name, (args, error) in cases.items():
                with self.subTest(case=name):
                    result = run("probe", *args, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertEqual(result.stderr.decode().splitlines()[0], f"error: {error}")


if __name__ == "__main__":
    unittest.main()
