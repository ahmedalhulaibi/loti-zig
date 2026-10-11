"""Original16-byte link example, publisher-resolved and packaged whole JSON records."""

import json
from pathlib import Path
import subprocess
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from docutils import nodes
from sphinx.application import Sphinx

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"


class LinkedProseContracts(unittest.TestCase):
    def test_complete_link_json_examples_match_original_and_native_byte_counts(self):
        """Kills source/runtime arithmetic drift even when publication faithfully preserves it."""
        result = subprocess.run(["make", "epub"], cwd=ROOT, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        expected = [plan["report"] for plan in json.loads(
            (ROOT / "testdata/inputs/link-ownership-contracts.json").read_text())["plans"]]
        publisher = Sphinx(str(ROOT), str(ROOT), str(ROOT / "_build/epub"),
                           str(ROOT / "_build/doctrees"), "epub", status=None, warning=None)
        source = publisher.env.get_doctree("tutorial/link")
        records = [json.loads(node.astext()) for node in source.findall(nodes.literal_block)
                   if node.get("language") == "json"]
        self.assertEqual(records, expected)
        with ZipFile(BOOK) as archive:
            document = ET.fromstring(archive.read("tutorial/link.xhtml"))
        namespace = {"x": "http://www.w3.org/1999/xhtml"}
        rendered = [json.loads("".join(pre.itertext()))
                    for div in document.findall(".//x:div", namespace)
                    if "highlight-json" in div.get("class", "").split()
                    for pre in div.findall(".//x:pre", namespace)]
        self.assertEqual(rendered, expected)


if __name__ == "__main__":
    unittest.main()
