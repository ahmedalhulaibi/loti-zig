"""Public rendered-EPUB contract; browser checks are not device attestation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"


def run(book, report):
    return subprocess.run([sys.executable, str(ROOT / "tools/check_reader_layout.py"),
                           "--book", str(book), "--report", str(report)],
                          capture_output=True, text=True, timeout=75)


class ReaderLayoutContracts(unittest.TestCase):
    def test_published_spine_reflows_without_horizontal_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            result = run(BOOK, report)
            self.assertEqual((result.returncode, result.stderr), (0, ""))
            self.assertEqual(json.loads(result.stdout), {
                "chapters": 27, "viewports": [320, 600, 800], "cases": 81,
                "element_counts": {"pre": 357, "table": 6, "image": 15, "heading": 327, "figure": 0},
                "violations": [], "event": "loti.reader-layout.checked"})
            data = json.loads(report.read_text())
            self.assertEqual(set(data), {"scope", "book_sha256", "renderer", "chapters", "viewports",
                                         "cases", "element_counts", "violations", "measurements"})
            self.assertEqual(len(data["measurements"]), 81)

    def test_damaged_styles_and_metadata_are_rejected(self):
        cases = {
            "heading": "h1,h2,h3,h4,h5,h6{overflow-wrap:normal!important;white-space:nowrap!important}",
            "pre": "pre{white-space:pre!important}",
            "table": "table{min-width:1200px!important}",
            "image": "img{min-width:1600px!important}",
        }
        with tempfile.TemporaryDirectory() as directory:
            for kind, css in cases.items():
                with self.subTest(kind=kind):
                    book = Path(directory) / (kind + ".epub")
                    report = Path(directory) / (kind + ".json")
                    with zipfile.ZipFile(BOOK) as original, zipfile.ZipFile(book, "w") as damaged:
                        for entry in original.infolist():
                            content = original.read(entry.filename)
                            if entry.filename == "_static/ebook.css":
                                content += ("\n" + css + "\n").encode()
                            damaged.writestr(entry, content)
                    result = run(book, report)
                    self.assertEqual((result.returncode, result.stderr), (1, ""))
                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["event"], "loti.reader-layout.failed")
                    self.assertEqual((summary["chapters"], summary["viewports"], summary["cases"]), (27, [320, 600, 800], 81))
                    self.assertTrue(any(issue["kind"] == kind for row in summary["violations"] for issue in row["issues"]))
            for case, path, reason in (("rootfile", "META-INF/container.xml", "MissingRootfile"),
                                       ("href", "content.opf", "InvalidPackageAttribute"),
                                       ("spine", "content.opf", "EmptySpine")):
                with self.subTest(metadata=case):
                    book = Path(directory) / (case + ".epub")
                    with zipfile.ZipFile(BOOK) as original, zipfile.ZipFile(book, "w") as damaged:
                        document = ET.fromstring(original.read(path))
                        selector = {"rootfile": "{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles",
                                    "href": "{http://www.idpf.org/2007/opf}manifest/{http://www.idpf.org/2007/opf}item",
                                    "spine": "{http://www.idpf.org/2007/opf}spine"}[case]
                        target = document.find(selector)
                        assert target is not None, "OriginalFixtureElementMissing"
                        if case == "rootfile":
                            target.clear()
                        elif case == "href":
                            del target.attrib["href"]
                        else:
                            target.clear()
                        for entry in original.infolist():
                            content = ET.tostring(document) if entry.filename == path else original.read(entry.filename)
                            damaged.writestr(entry, content)
                    result = run(book, Path(directory) / (case + ".json"))
                    self.assertEqual((result.returncode, result.stderr), (1, ""))
                    self.assertEqual(json.loads(result.stdout), {"event": "loti.reader-layout.failed", "error": reason})


if __name__ == "__main__":
    unittest.main()
