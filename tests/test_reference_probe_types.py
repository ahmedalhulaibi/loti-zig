"""Probe-type consumers, allocation and support meanings, not manifest freshness."""

import json
from pathlib import Path
import unittest

from tools.reference_map import generate

ROOT = Path(__file__).resolve().parent.parent


class ProbeTypeBindingContracts(unittest.TestCase):
    def test_probe_header_and_entry_have_whole_native_consumer_contracts(self):
        # Kills unused-catalog primaries, foreign flexible-array ownership and
        # support inferred from unrelated flag bits despite fresh generated data.
        expected = json.loads((ROOT / "testdata/inputs/probe-type-bindings.json").read_text())
        selected = {entry["original"] for entry in expected}
        surfaces = {
            "producer": generate(),
            "published": json.loads((ROOT / "conversion/reference-map.json").read_text()),
        }
        for name, surface in surfaces.items():
            with self.subTest(surface=name):
                actual = [entry for entry in surface["entries"] if entry["original"] in selected]
                self.assertEqual(actual, expected)
