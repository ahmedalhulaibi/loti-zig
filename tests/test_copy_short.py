import json
import re
import resource
import subprocess
import tempfile
import unittest
from pathlib import Path

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import BIN, CASES, ROOT, run

FIXTURES = ROOT / "testdata/inputs"


def limits():
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    return {"soft": (1 << 64) - 1 if soft == resource.RLIM_INFINITY else soft,
            "hard": (1 << 64) - 1 if hard == resource.RLIM_INFINITY else hard}


def expected(size, split, original):
    steps = []
    for operation, length, offset, result, before, after, phase, written in [
            ("READ", size, 0, size, 0, 0, "writing", 0),
            ("WRITE", size, 0, split, 0, split, "writing", 0),
            ("WRITE", size - split, split, size - split, split, size, "idle", size)]:
        steps.append({"request": {"operation": operation, "tag": 1, "length": length, "offset": offset, "flags": 0},
                      "cqe": {"tag": 1, "result": result, "flags": 0}, "done_before": before, "done_after": after,
                      "phase_after": phase, "written": written})
    return {"event": "loti.copy.short-write.checked", "input_size": size, "limit": split, "steps": steps,
            "limits": {"original": original, "armed": {"soft": split, "hard": original["hard"]}, "restored": original},
            "written": size}


@st.composite
def plans(draw):
    payload = draw(st.binary(min_size=2, max_size=16384))
    return payload, draw(st.integers(min_value=1, max_value=len(payload) - 1))


def inspect_limits(text, split, original):
    infinity = "RLIM64_INFINITY"
    soft = infinity if original["soft"] == (1 << 64) - 1 else str(original["soft"])
    hard = infinity if original["hard"] == (1 << 64) - 1 else str(original["hard"])
    previous = f"{{rlim_cur={soft}, rlim_max={hard}}}"
    armed = f"{{rlim_cur={split}, rlim_max={hard}}}"
    observed, submits, rings, order = [], 0, set(), []
    for line in text.splitlines():
        matched = re.fullmatch(r"prlimit64\((\d+), RLIMIT_FSIZE, (NULL|\{rlim_cur=[^,}]+, rlim_max=[^}]+\}), (NULL|\{rlim_cur=[^,}]+, rlim_max=[^}]+\})\)\s+= 0", line)
        if matched:
            pid, new, old = matched.groups()
            if pid != "0":
                raise ValueError("CopyChangedAnotherProcessLimit")
            observed.append((new, old)); order.append("query" if new == "NULL" else "set")
        enter = re.fullmatch(r"io_uring_enter\((\d+), 1, 0, 0, NULL, 8\)\s+= 1", line)
        if enter:
            rings.add(int(enter[1])); submits += 1; order.append("submit")
        write = re.match(r"(?:write|pwrite64|writev|pwritev|pwritev2)\((\d+),", line)
        if write and int(write[1]) not in {1, 2}:
            raise ValueError("SynchronousCopyWriteDetected")
        if line.startswith("--- SIGXFSZ"):
            raise ValueError("CopyHitLimitInsteadOfMakingPartialProgress")
    if observed != [("NULL", previous), (armed, "NULL"), (previous, "NULL"), ("NULL", previous)]:
        raise ValueError("WrongCopyLimitTransitions")
    if submits != 3 or len(rings) != 1:
        raise ValueError("WrongShortCopySubmissionCount")
    if order != ["query", "set", "submit", "submit", "set", "submit", "query"]:
        raise ValueError("CopyLimitRestoreNotBeforeRemainderSubmission")
    return {"submissions": 3, "rings": 1, "limit_queries": 2, "limit_sets": 2,
            "same_hard_limit": True, "restored_before_remainder_submission": True, "synchronous_file_writes": 0}


class ShortCopyContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None, derandomize=True)
    @given(plan=plans())
    @example(plan=(bytes(range(256)) * 64, 8192))
    @example(plan=(b"\x00\xffZig", 2))
    def test_completed_bytes_advance_both_buffer_and_file_offset(self, plan):
        """Kills requested-count progress, reset buffer/offset, premature slot retirement and fake short-write metadata."""
        payload, split = plan
        original = limits()
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.write_bytes(payload); output.write_bytes(b"owned prior output")
            result = run("cp", source, output, "--short-write", split)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), expected(len(payload), split, original))
            self.assertEqual(output.read_bytes(), payload)
            self.assertEqual(source.read_bytes(), payload)
        self.assertEqual(limits(), original)

    def test_literal_and_typed_invalid_modes_preserve_owned_inputs(self):
        """A whole pinned literal and input-error matrix catch mirror/late-validation/truncation regressions."""
        original = limits()
        literal = json.loads((FIXTURES / "copy-short-report.json").read_text())
        literal["limits"]["original"] = original; literal["limits"]["restored"] = original
        literal["limits"]["armed"]["hard"] = original["hard"]
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.write_bytes((FIXTURES / "copy-short-input.bin").read_bytes())
            for _ in range(2):
                self.assertEqual(json.loads(run("cp", source, output, "--short-write", 2).stdout), literal)
                self.assertEqual(output.read_bytes(), source.read_bytes())
            for case in json.loads((FIXTURES / "copy-short-invalid-plans.json").read_text()):
                with self.subTest(case=case["name"]):
                    source.write_bytes(bytes(case["size"]))
                    output.write_bytes(b"owned prior output")
                    arguments = [source, output, *case["suffix"]]
                    result = run("cp", *arguments, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertEqual(result.stderr.splitlines()[0], ("error: " + case["error"]).encode())
                    self.assertEqual(output.read_bytes(), b"owned prior output")
                    self.assertEqual(source.read_bytes(), bytes(case["size"]))
        self.assertEqual(limits(), original)

    def test_actual_process_limit_transitions_and_damaged_syscall_traces(self):
        """Kills cap bypass/early restore, changed hard/foreign process limits and synchronous file-write substitution."""
        original = limits()
        with tempfile.TemporaryDirectory() as directory:
            source, output, trace = Path(directory) / "source", Path(directory) / "output", Path(directory) / "trace"
            source.write_bytes((FIXTURES / "copy-short-input.bin").read_bytes())
            result = subprocess.run(["strace", "-qq", "-e", "trace=prlimit64,io_uring_enter,write,pwrite64,writev,pwritev,pwritev2",
                                     "-o", str(trace), str(BIN / "cp"), str(source), str(output), "--short-write", "2"],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), expected(5, 2, original))
            self.assertEqual(output.read_bytes(), source.read_bytes())
            try:
                measured = inspect_limits(trace.read_text(), 2, original)
            except ValueError as error:
                self.fail(f"Invalid public short-copy trace: {error}")
            self.assertEqual(measured, {"submissions": 3, "rings": 1, "limit_queries": 2, "limit_sets": 2,
                                        "same_hard_limit": True, "restored_before_remainder_submission": True,
                                        "synchronous_file_writes": 0})
        fixture = (FIXTURES / "copy-short.trace").read_text()
        unlimited = {"soft": (1 << 64) - 1, "hard": (1 << 64) - 1}
        self.assertEqual(inspect_limits(fixture, 2, unlimited), measured)
        for case in json.loads((FIXTURES / "copy-short-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_limits(fixture.replace(case["old"], case["new"], case["count"]), 2, unlimited)
                self.assertEqual(str(raised.exception), case["error"])
        self.assertEqual(limits(), original)


if __name__ == "__main__":
    unittest.main()
