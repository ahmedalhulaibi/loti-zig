"""Whole native type meaning/consumer scopes and current-target declarations."""

import json
from pathlib import Path
import subprocess
import unittest

from tools.reference_map import generate

ROOT = Path(__file__).resolve().parent.parent


class NativeTypeContracts(unittest.TestCase):
    def test_remaining_type_rows_have_whole_consumer_and_representation_scopes(self):
        # Kills foreign wrapper casts, wrong primitive/field namespaces, unused
        # primaries, mask ABI confusion and false execution despite fresh maps.
        expected = json.loads((ROOT / "testdata/inputs/type-binding-contracts.json").read_text())
        selected = {row["original"] for row in expected}
        for name, surface in {"producer": generate(), "published": json.loads((ROOT / "conversion/reference-map.json").read_text())}.items():
            with self.subTest(surface=name):
                self.assertEqual([row for row in surface["entries"] if row["original"] in selected], expected)

    def test_current_native_declarations_keep_layout_width_and_constness_boundaries(self):
        # Kills compiler/ABI drift concealed by identical-looking type labels;
        # explicit literals, not an encoder or expectations derived from SDK.
        result = subprocess.run(["zig", "run", "--dep", "raw_ops", "-Mroot=conversion/type-binding-reflection.zig",
                                 "-Mraw_ops=examples/raw_ops.zig"], cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stderr, b"")
        self.assertEqual(json.loads(result.stdout), json.loads((ROOT / "testdata/inputs/type-binding-reflection.json").read_text()))
