"""SPLICE byte, cursor, pipe-ownership and partial-progress contract."""
import json
from pathlib import Path
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run

CURRENT = 2**64 - 1


def splice(tag, phase, off_in, off_out, requested, result):
    return {"tag": tag, "phase": phase, "input_offset": off_in, "output_offset": off_out,
            "requested": requested, "operation_flags": 2, "result": result, "flags": 0}


def read(tag, requested, offset=CURRENT):
    return {"tag": tag, "offset": offset, "requested": requested, "result": requested, "flags": 0}


def expected_report(payload):
    splices, reads, offset, tag = [], [], 0, 10
    while offset < len(payload):
        request = min(8192, len(payload) - offset)
        count = min(4096, request)
        splices += [splice(tag, "fill", offset, CURRENT, request, count),
                    splice(tag + 1, "relay", CURRENT, CURRENT, count, count)]
        reads.append(read(tag + 2, count))
        offset += count
        tag += 3
    prefix = payload[:64]
    destination = bytearray(11 + len(prefix) if prefix else 0)
    destination[11:] = prefix
    destination[:len(prefix)] = prefix
    return {"source_size": len(payload), "capacities": [4096, 4096],
            "explicit": {"position_before": 7, "position_after": 7, "splices": splices,
                         "reads": reads, "data": list(payload)},
            "eof": splice(1000000, "eof", len(payload), CURRENT, 1, 0),
            "current": {"position_before": 0, "position_after": len(prefix),
                        "splice": splice(1000001, "current", CURRENT, CURRENT, 64, len(prefix)),
                        "read": read(1000002, len(prefix)), "data": list(prefix)},
            "destination": {"explicit_before": 7, "explicit_after": 7,
                            "current_before": 0, "current_after": len(prefix), "after_observation": len(prefix),
                            "splices": [splice(1000030, "fill_output_explicit", 0, CURRENT, 64, len(prefix)),
                                        splice(1000031, "output_explicit", CURRENT, 11, len(prefix), len(prefix)),
                                        splice(1000032, "fill_output_current", 0, CURRENT, 64, len(prefix)),
                                        splice(1000033, "output_current", CURRENT, CURRENT, len(prefix), len(prefix))],
                            "read": read(1000034, len(destination), 0), "data": list(destination)},
            "failures": [splice(1000010, "invalid_source", 0, CURRENT, 1, -9),
                         splice(1000011, "empty_pipe", CURRENT, CURRENT, 1, -11),
                         splice(1000012, "input_offset", 0, CURRENT, 1, -29),
                         splice(1000013, "output_offset", 0, 0, 1, -29),
                         splice(1000014, "same_pipe", CURRENT, CURRENT, 1, -22),
                         splice(1000015, "no_pipe", 0, 0, 1, -22)],
            "pipes_closed": [True, True, True, True], "source_still_open": True}


class SpliceContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None)
    @given(payload=st.binary(max_size=12289))
    @example(payload=b"")
    @example(payload=(ROOT / "testdata/inputs/splice-partial.bin").read_bytes())
    def test_splice_bytes_cursors_and_partial_progress(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(payload)
            result = run("reference-splice", source)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertEqual(json.loads(result.stdout), expected_report(payload))
            self.assertEqual(source.read_bytes(), payload)

    def test_literal_oracle_and_typed_invalid_inputs(self):
        fixture = ROOT / "testdata/inputs/splice-input.bin"
        literal = json.loads((ROOT / "testdata/inputs/splice-report.json").read_text())
        self.assertEqual(json.loads(run("reference-splice", fixture).stdout), literal)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            link = root / "symlink"
            link.symlink_to(fixture)
            large = root / "large"
            large.write_bytes(bytes(1024 * 1024 + 1))
            cases = {"missing": (root / "missing", "SpliceInputOpenFailed"),
                     "symlink": (link, "SpliceInputOpenFailed"),
                     "directory": (root, "ExpectedRegularSpliceInput"),
                     "device": (Path("/dev/null"), "ExpectedRegularSpliceInput"),
                     "large": (large, "SpliceInputTooLarge")}
            for name, (source, error) in cases.items():
                with self.subTest(case=name):
                    result = run("reference-splice", source, success=False)
                    self.assertEqual((result.returncode, result.stdout), (1, b""))
                    self.assertEqual(result.stderr.decode().splitlines()[0], "error: " + error)
            self.assertEqual(large.stat().st_size, 1024 * 1024 + 1)
            self.assertEqual(link.readlink(), fixture)
        for arguments in ([], [str(fixture), "extra"]):
            with self.subTest(arguments=arguments):
                result = run("reference-splice", *arguments, success=False)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertEqual(result.stderr.decode().splitlines()[0], "error: ExpectedSpliceInput")


if __name__ == "__main__":
    unittest.main()
