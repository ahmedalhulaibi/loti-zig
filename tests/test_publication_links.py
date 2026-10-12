"""Whole packaged citation destinations; network availability is a separate audit."""

import json
import os
from pathlib import Path
import subprocess
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"


class PublicationLinkContracts(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        subprocess.run(
            ["make", "epub", "SPHINXBUILD=" + os.environ.get(
                "SPHINXBUILD", str(ROOT / ".venv/bin/sphinx-build"))],
            cwd=ROOT, check=True, capture_output=True, timeout=90,
        )

    def test_complete_external_citation_destinations_and_chapters(self):
        """Reject dead publisher destinations and wrong/missing/extra citation bindings."""
        expected = json.loads((ROOT / "testdata/inputs/publication-links.json").read_text())
        actual: dict[str, set[str]] = {}
        with zipfile.ZipFile(ARCHIVE) as archive:
            for name in archive.namelist():
                if not name.endswith(".xhtml"):
                    continue
                for node in ET.fromstring(archive.read(name)).iter():
                    href = node.get("href", "")
                    if urlsplit(href).scheme in {"http", "https"}:
                        actual.setdefault(href, set()).add(name)
        self.assertEqual({href: sorted(names) for href, names in actual.items()}, expected)


if __name__ == "__main__":
    unittest.main()
