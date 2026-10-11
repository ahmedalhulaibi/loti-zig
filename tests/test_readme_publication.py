"""Reader-facing statistics and commands, not green-status or report-path proxies."""

import json
from pathlib import Path
import re
import shlex
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "testdata/inputs/readme-publication-contract.json"


class ReaderDocumentationContracts(unittest.TestCase):
    def test_publication_statistics_and_commands_match_current_contract(self):
        """Kills stale literal/narrative claims and historical-receipt overwrite instructions."""
        expected = json.loads(FIXTURE.read_text())
        readme = (ROOT / "README.md").read_text()
        normalized = " ".join(readme.split())
        statistics = re.findall(
            r"Publication checks verify all ([0-9]+) chapters in reading order/navigation, "
            r"([0-9]+) literal blocks against Sphinx source, ([a-z]+) byte-identical illustrations, "
            r"licence and local links\.", normalized,
        )
        narrative = re.findall(r"also checks ([0-9]+) resolved narrative paragraphs", normalized)
        self.assertEqual((len(statistics), len(narrative)), (1, 1))
        chapters, literals, illustration = statistics[0]
        self.assertEqual({"edition_chapters": chapters, "literal_blocks": literals,
                          "illustration_word": illustration, "narrative_paragraphs": narrative[0]},
                         expected["statistics"])
        commands = [shlex.split(line, comments=True)
                    for block in re.findall(r"```sh\n(.*?)\n```", readme, re.DOTALL)
                    for line in block.splitlines() if line.strip()]
        for wanted in expected["commands"]:
            selected = [command for command in commands if command[:2] == wanted[:2]]
            self.assertEqual(selected, [wanted])
        # Run only the fixture-confirmed owned build-output commands, not arbitrary README shell.
        result = subprocess.run(expected["commands"][0], cwd=ROOT, capture_output=True,
                                text=True, timeout=5)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        result = subprocess.run(expected["commands"][1], cwd=ROOT, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        report = json.loads(result.stdout)
        self.assertEqual({key: report[key] for key in expected["report_properties"]},
                         expected["report_properties"])
        self.assertEqual(json.loads((ROOT / "_build/verification/epub.json").read_text()), report)


if __name__ == "__main__":
    unittest.main()
