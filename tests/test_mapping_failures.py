"""Real kernel-denied mmap calls and independent syscall unwind oracle."""

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tests.test_examples import ROOT, run


STAGES = json.loads((ROOT / "testdata/inputs/mapping-failure-stages.json").read_text())


def expected_report(stage, case):
    return {"stage": stage, "single_mapping": case["single_mapping"],
            "failed_offset": case["failed_offset"], "mapping_error": "OutOfMemory",
            "before": 0, "after": 0, "fd_retained": True, "fd_closed": True,
            "no_new_privs": True}


def inspect_trace(text, case):
    lines = text.splitlines()
    setup = [match for line in lines if (match := re.fullmatch(r"io_uring_setup\(8, .*\)\s+=\s+(\d+)", line))]
    if len(setup) != 1:
        raise ValueError("ExpectedOneRingSetup")
    fd = int(setup[0].group(1))
    mappings, unmappings = [], []
    for line in lines:
        match = re.fullmatch(r"mmap\(NULL, (?P<length>\d+), (?P<protection>[A-Z_|]+), (?P<flags>[A-Z_|]+), (?P<fd>-?\d+), (?P<offset>0x[0-9a-f]+|0)\)\s+=\s+(?P<outcome>.+)", line)
        if match and int(match["fd"]) == fd:
            if match["protection"] != "PROT_READ|PROT_WRITE" or match["flags"] != "MAP_SHARED|MAP_POPULATE":
                raise ValueError("UnexpectedRingMappingFlags")
            outcome = match["outcome"]
            failed = re.fullmatch(r"-1 (\w+) \([^\n]*\)", outcome)
            if failed:
                if failed[1] != "ENOMEM":
                    raise ValueError("UnexpectedMappingErrno")
                address = None
            elif re.fullmatch(r"0x[0-9a-f]+", outcome):
                address = int(outcome, 16)
            else:
                raise ValueError("UnexpectedMappingOutcome")
            mappings.append({"length": int(match["length"]), "offset": int(match["offset"], 0), "address": address})
        match = re.fullmatch(r"munmap\((0x[0-9a-f]+), (\d+)\)\s+=\s+(-?\d+)", line)
        if match:
            unmappings.append((int(match[1], 16), int(match[2]), int(match[3])))
    if [row["offset"] for row in mappings] != case["successful_offsets"] + [case["failed_offset"]]:
        raise ValueError("WrongMappingCallSequence")
    if not mappings or mappings[-1]["address"] is not None or any(row["address"] is None for row in mappings[:-1]):
        raise ValueError("WrongFailurePosition")
    live = [(row["address"], row["length"]) for row in mappings[:-1]]
    observed = [(address, length) for address, length, result in unmappings if any(address == base for base, _ in live) and result == 0]
    if observed != list(reversed(live)):
        raise ValueError("PartialMappingsNotUnwound")
    return {"successful_offsets": case["successful_offsets"], "failed_offset": case["failed_offset"],
            "unmapped_count": len(observed), "reverse_unwind": True}


class MappingFailureContracts(unittest.TestCase):
    def test_trace_oracle_rejects_incomplete_or_false_unwind(self):
        rows = [
            "io_uring_setup(8, {}) = 3",
            "mmap(NULL, 8288, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_POPULATE, 3, 0) = 0x1000",
            "mmap(NULL, 8256, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_POPULATE, 3, 0x8000000) = 0x5000",
            "mmap(NULL, 512, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_POPULATE, 3, 0x10000000) = -1 ENOMEM (Cannot allocate memory)",
            "munmap(0x5000, 8256) = 0", "munmap(0x1000, 8288) = 0",
        ]
        case = STAGES["separate-sqes"]
        self.assertEqual(inspect_trace("\n".join(rows), case), {
            "successful_offsets": [0, 134217728], "failed_offset": 268435456,
            "unmapped_count": 2, "reverse_unwind": True,
        })
        damaged = {
            "missing_setup": rows[1:], "missing_map": rows[:2] + rows[3:],
            "wrong_errno": [row.replace("ENOMEM", "EINVAL") for row in rows],
            "missing_unmap": rows[:-1], "reversed_unwind": rows[:-2] + rows[-2:][::-1],
            "short_unmap": [row.replace("munmap(0x5000, 8256)", "munmap(0x5000, 4096)") for row in rows],
            "failed_unmap": rows[:-1] + ["munmap(0x1000, 8288) = -1"],
        }
        for damage, trace in damaged.items():
            with self.subTest(damage=damage), self.assertRaises(ValueError):
                inspect_trace("\n".join(trace), case)

    def test_denied_mapping_calls_unwind_and_retain_caller_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            for stage, case in STAGES.items():
                with self.subTest(stage=stage):
                    trace = Path(directory) / (stage + ".trace")
                    result = subprocess.run([
                        "strace", "-qq", "-o", str(trace), "-e", "trace=io_uring_setup,mmap,munmap,prctl,seccomp",
                        str(ROOT / "zig-out/bin/reference-setup"), "--mapping-failure", stage,
                    ], capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr.decode())
                    self.assertEqual(result.stderr, b"")
                    self.assertEqual(json.loads(result.stdout), expected_report(stage, case))
                    self.assertEqual(inspect_trace(trace.read_text(), case), {
                        "successful_offsets": case["successful_offsets"], "failed_offset": case["failed_offset"],
                        "unmapped_count": len(case["successful_offsets"]), "reverse_unwind": True,
                    })

    def test_mapping_failure_mode_rejects_missing_or_unknown_stage(self):
        for arguments, error in [(["--mapping-failure"], "ExpectedMappingFailureStage"),
                                 (["--mapping-failure", "unknown"], "UnknownMappingFailureStage")]:
            with self.subTest(arguments=arguments):
                result = run("reference-setup", *arguments, success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.decode().splitlines()[0], "error: " + error)


if __name__ == "__main__":
    unittest.main()
