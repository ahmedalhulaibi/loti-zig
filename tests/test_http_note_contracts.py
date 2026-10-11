"""Author evidence notes must not conflate requests/responses or overstate tests."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


class HttpNoteContracts(unittest.TestCase):
    def test_http_operation_notes_have_whole_evidence_scopes(self):
        # Kills response-as-RECV input claims, stale short-SEND exclusions and
        # unsupported SIGPIPE/per-fragment assurance despite a fresh full index.
        expected = json.loads((ROOT / "testdata/inputs/http-note-contracts.json").read_text())
        selected = {row["original"] for row in expected}
        actual = []
        for line in (ROOT / "conversion/reference-block-disposition.md").read_text().splitlines():
            if not line.startswith("| `"):
                continue
            fields = line.removeprefix("| ").removesuffix(" |").split(" | ")
            identity = fields[0].removeprefix("`").removesuffix("`")
            if identity in selected:
                self.assertEqual(len(fields), 3)
                actual.append({"original": identity, "replacement": fields[1], "evidence": fields[2]})
        self.assertEqual(actual, expected)
