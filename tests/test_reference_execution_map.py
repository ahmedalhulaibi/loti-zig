"""Executing primary examples and native operand/lifetime meanings, not freshness."""

import json
from pathlib import Path
import unittest

from tools.reference_map import generate

ROOT = Path(__file__).resolve().parent.parent


class ReferenceExecutionMapContracts(unittest.TestCase):
    def test_executed_nop_fixed_buffer_and_stream_receive_bindings_have_whole_contracts(self):
        # Kills construction-only misclassification and buffer-index/iovec/RECV
        # capacity meanings that still pass syntax, generation and freshness.
        expected = json.loads((ROOT / "testdata/inputs/reference-execution-bindings.json").read_text())
        selected = {entry["original"] for entry in expected}
        actual = [entry for entry in generate()["entries"] if entry["original"] in selected]
        self.assertEqual(actual, expected)
