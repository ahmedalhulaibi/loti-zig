"""Provided-buffer CLI state model; no shared native encoder or helper."""

import json
from pathlib import Path
import tempfile
import unittest

from hypothesis import example, given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run


PLANS = json.loads((ROOT / "testdata/inputs/provided-buffer-plans.json").read_text())
REGRESSION = json.loads((ROOT / "testdata/inputs/provided-buffer-cleanup-regression.json").read_text())


def cqe(tag, result, buffer_id=None):
    return {"tag": tag, "result": result,
            "flags": 0 if buffer_id is None else (buffer_id << 16) | 1,
            "buffer_id": buffer_id, "no_buffer_selected": buffer_id is None}


def model(payload, commands):
    count = min(len(payload), 64)
    filled = list(payload[:64]) + [165] * (64 - count)
    storage, available, steps = [165] * 64, True, []
    for tag, command in enumerate(commands, 100):
        if command == "provide":
            assert not available
            storage, available, result = [165] * 64, True, cqe(tag, 0)
        elif command == "remove":
            assert available
            available, result = False, cqe(tag, 1)
        elif available:
            storage, available, result = filled, False, cqe(tag, count, 257)
        else:
            result = cqe(tag, -105)
        steps.append({"command": command, "cqe": result, "available": available, "storage": storage})
    return {
        "multiple": {"provide": cqe(1, 0), "remove": cqe(2, 2), "after_remove": cqe(3, -105),
                     "count": 2, "size": 64, "group": 12, "first_id": 1000,
                     "storage": [165] * 128},
        "isolation": {"provide": cqe(4, 0), "wrong_group": cqe(5, -105),
                      "selected": cqe(6, count, 513), "exhausted": cqe(7, -105), "storage": filled},
        "initial": cqe(8, 0), "selection_group": 7, "selection_id": 257,
        "steps": steps, "cleanup": cqe(200, 1) if available else None, "final_available": False,
    }


def plan_from_choices(choices):
    available, commands = True, []
    for choice in choices:
        command = ("read" if choice == 0 else
                   ("read" if available else "provide") if choice == 1 else
                   ("remove" if available else "read"))
        commands.append(command)
        available = command == "provide"
    return commands


class ProvidedBufferContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None)
    @given(payload=st.binary(min_size=1, max_size=1025),
           choices=st.lists(st.integers(min_value=0, max_value=2), min_size=1, max_size=32))
    @example(payload=(ROOT / "testdata/inputs/provided-buffer-input.bin").read_bytes(), choices=[0, 0, 1, 0, 1, 2, 0])
    @example(payload=bytes(REGRESSION["payload"]), choices=REGRESSION["choices"])
    def test_selected_buffers_follow_ownership_model(self, payload, choices):
        commands = plan_from_choices(choices)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(payload)
            self.assertEqual(json.loads(run("reference-buffers", source, *commands).stdout), model(payload, commands))
            self.assertEqual(source.read_bytes(), payload)

    def test_literal_default_and_all_plan_fixtures(self):
        source = ROOT / "testdata/inputs/provided-buffer-input.bin"
        literal = json.loads((ROOT / "testdata/inputs/provided-buffer-report.json").read_text())
        self.assertEqual(json.loads(run("reference-buffers", source).stdout), literal)
        for name, commands in PLANS.items():
            with self.subTest(plan=name):
                self.assertEqual(json.loads(run("reference-buffers", source, *commands).stdout), model(source.read_bytes(), commands))

    def test_invalid_plans_and_inputs_are_rejected(self):
        source = ROOT / "testdata/inputs/provided-buffer-input.bin"
        invalid = json.loads((ROOT / "testdata/inputs/provided-buffer-invalid-plans.json").read_text())
        cases = {name: ([source, *case["commands"]], case["error"]) for name, case in invalid.items()}
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "empty"
            empty.write_bytes(b"")
            cases.update({"missing": ([], "ExpectedInputAndBufferCommands"),
                          "too_many": ([source, *(["read"] * 33)], "ExpectedInputAndBufferCommands"),
                          "empty": ([empty], "ExpectedNonemptyRegularInput"),
                          "device": (["/dev/null"], "ExpectedNonemptyRegularInput")})
            for name, (arguments, error) in cases.items():
                with self.subTest(case=name):
                    result = run("reference-buffers", *arguments, success=False)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertEqual(result.stderr.decode().splitlines()[0], "error: " + error)


if __name__ == "__main__":
    unittest.main()
