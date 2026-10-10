"""Whole published bindings for the selected semantic-conversion regressions."""
import json
import unittest

from tests.test_examples import ROOT


class ReferenceSemanticContracts(unittest.TestCase):
    def test_selected_reference_claims_match_whole_binding_contract(self):
        actual = {row["original"]: row for row in json.loads((ROOT / "conversion/reference-map.json").read_text())["entries"]}
        expected = json.loads((ROOT / "testdata/inputs/reference-semantics-bindings.json").read_text())
        for row in expected:
            with self.subTest(original=row["original"]):
                self.assertEqual(actual[row["original"]], row)


if __name__ == "__main__":
    unittest.main()
