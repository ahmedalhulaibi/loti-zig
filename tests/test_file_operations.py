"""Public native file-operation contract; author oracle, not independent review."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run


def expected_report(payload):
    length = len(payload)
    chunks = [min(4096, length - offset) for offset in range(0, length, 4096)]
    return {
        "opens": [True, True, True], "closed": [True, True, True],
        "input_size": length,
        "readv": {"vectors": 2, "results": chunks + [0]},
        "writev": {"vectors": 2, "results": chunks or [0]},
        "allocation": {"offset": length, "length": 4096, "mode": 0, "result": 0},
        "statx": {"requested_mask": 513, "size_present": True, "type_present": True,
                  "regular": True, "size": length + 4096},
        "fsync": [{"operation": "FSYNC", "tag": 20, "flags": 0, "result": 0},
                  {"operation": "FSYNC", "tag": 21, "flags": 1, "result": 0}],
        "reopened": {"bytes": length + 4096,
                     "sha256": hashlib.sha256(payload + bytes(4096)).hexdigest()},
        "invalid_descriptors": [
            {"operation": operation, "tag": tag, "result": -9, "flags": 0}
            for tag, operation in enumerate(
                ["OPENAT", "READV", "WRITEV", "FALLOCATE", "STATX", "FSYNC", "CLOSE"], 50
            )
        ],
    }


class FileOperationContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None)
    @given(payload=st.binary(max_size=8193))
    @example(payload=b"")
    @example(payload=(ROOT / "testdata/inputs/file-operations-write-offset-regression.bin").read_bytes())
    def test_file_operation_effects_and_correlated_failures(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.write_bytes(payload)
            self.assertEqual(json.loads(run("reference-files", source, output).stdout), expected_report(payload))
            self.assertEqual(source.read_bytes(), payload)
            self.assertEqual(output.read_bytes(), payload + bytes(4096))
            self.assertEqual(output.stat().st_size, len(payload) + 4096)

    def test_literal_oracle_and_rejected_paths_preserve_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.write_bytes((ROOT / "testdata/inputs/file-operations.bin").read_bytes())
            literal = json.loads((ROOT / "testdata/inputs/file-operations-report.json").read_text())
            self.assertEqual(json.loads(run("reference-files", source, output).stdout), literal)
            self.assertEqual(output.read_bytes(), source.read_bytes() + bytes(4096))
            before_source, before_output = source.read_bytes(), output.read_bytes()
            link = Path(directory) / "link"
            link.symlink_to(output)
            cases = {
                "existing": (source, output, "ExclusiveOutputOpenFailed"),
                "same_file": (source, source, "ExclusiveOutputOpenFailed"),
                "symlink_output": (source, link, "ExclusiveOutputOpenFailed"),
                "missing_source": (Path(directory) / "missing", Path(directory) / "absent", "InputOpenFailed"),
                "device_source": (Path("/dev/null"), Path(directory) / "absent", "ExpectedRegularInputFile"),
                "symlink_source": (link, Path(directory) / "absent", "InputOpenFailed"),
            }
            for name, (src, dst, error) in cases.items():
                with self.subTest(case=name):
                    result = run("reference-files", src, dst, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertEqual(result.stderr.decode().splitlines()[0], "error: " + error)
                    self.assertEqual(source.read_bytes(), before_source)
                    self.assertEqual(output.read_bytes(), before_output)
                    self.assertEqual(link.readlink(), output)
                    self.assertFalse((Path(directory) / "absent").exists())

    def test_file_operation_reference_rejects_argument_counts(self):
        cases = json.loads((ROOT / "testdata/inputs/file-operations-invalid-arguments.json").read_text())
        for name, arguments in cases.items():
            with self.subTest(case=name):
                result = run("reference-files", *arguments, success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.decode().splitlines()[0], "error: ExpectedInputAndNewOutput")


if __name__ == "__main__":
    unittest.main()
