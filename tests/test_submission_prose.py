"""Mode-qualified reference bindings and faithful reader-facing narrative."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "testdata/inputs"
BOOK = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"
X = "{http://www.w3.org/1999/xhtml}"


def damage(original, case):
    files = dict(original)
    name = case["page"]
    page = ET.fromstring(files[name])
    paragraphs = [node for node in page.findall(".//" + X + "p")
                  if not {"rubric", "caption", "admonition-title"} & set(node.get("class", "").split())]
    parents = {child: parent for parent in page.iter() for child in parent}
    first, second = paragraphs[:2]
    parent = parents[first]
    if case["kind"] == "text":
        first.clear()
        first.text = case["text"]
    elif case["kind"] == "missing":
        parent.remove(first)
    elif case["kind"] == "duplicate":
        parent.insert(list(parent).index(first) + 1, copy.deepcopy(first))
    elif case["kind"] == "order":
        other = parents[second]
        a, b = list(parent).index(first), list(other).index(second)
        parent[a], other[b] = second, first
    elif case["kind"] == "rubric":
        first.set("class", "rubric")
    elif case["kind"] == "whitespace":
        # Formatting whitespace has no prose meaning; preserve child/role order.
        for element in first.iter():
            if element.text:
                element.text = element.text.replace(" ", " \n\t ")
            if element.tail:
                element.tail = element.tail.replace(" ", " \n\t ")
    else:
        raise ValueError("UnknownNarrativeDamage")
    files[name] = ET.tostring(page)
    return files


def archive(path, files):
    with ZipFile(path, "w") as book:
        for name, data in files.items():
            book.writestr(name, data, compress_type=ZIP_STORED if name == "mimetype" else ZIP_DEFLATED)


class SubmissionBindingContracts(unittest.TestCase):
    def test_both_wrappers_and_raw_enter_have_mode_qualified_whole_bindings(self):
        """Kills accurate-looking signatures paired with unqualified or completion-count semantics."""
        result = subprocess.run([sys.executable, str(ROOT / "tools/reference_map.py"), "--check"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {row["original"]: row for row in json.loads((ROOT / "conversion/reference-map.json").read_text())["entries"]}
        expected = json.loads((INPUTS / "submission-count-bindings.json").read_text())
        self.assertEqual(len(expected), 3)
        for row in expected:
            with self.subTest(original=row["original"]):
                self.assertEqual(rows[row["original"]], row)


class NarrativePublicationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make", "epub"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, timeout=60)
        with ZipFile(BOOK) as book:
            cls.files = {name: book.read(name) for name in book.namelist()}

    def test_reader_count_paragraphs_have_whole_mode_qualified_contracts(self):
        """Kills correct manifests paired with source prose that overstates SQPOLL return counts."""
        expected = json.loads((INPUTS / "submission-count-paragraphs.json").read_text())
        self.assertEqual(len(expected), 2)
        for case in expected:
            with self.subTest(page=case["page"]):
                page = ET.fromstring(self.files[case["page"]])
                paragraphs = [" ".join("".join(node.itertext()).split()) for node in page.findall(".//" + X + "p")
                              if not {"rubric", "caption", "admonition-title"} & set(node.get("class", "").split())]
                self.assertEqual(paragraphs[case["index"]], case["text"])

    def test_narrative_changes_fail_but_formatting_whitespace_is_accepted(self):
        """Kills literal-only, set-based, missing-paragraph and vacuous prose comparison."""
        cases = json.loads((INPUTS / "submission-prose-damages.json").read_text())
        self.assertEqual(len(cases), 7)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.epub"
            for case in cases:
                with self.subTest(case=case["name"]):
                    archive(path, damage(self.files, case))
                    result = subprocess.run([sys.executable, str(ROOT / "tools/verify_epub.py"), "--book", str(path)],
                                            cwd=ROOT, capture_output=True, text=True, timeout=30)
                    if case["kind"] == "whitespace":
                        self.assertEqual((result.returncode, result.stderr), (0, ""))
                        self.assertEqual(json.loads(result.stdout), {
                            "scope": "Publication structure and source fidelity; not semantic or independent review.",
                            "source_commit": "c9ee2424af02e4c1e4765088580107d5e17b826e",
                            "book_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "original_chapters": 26, "edition_chapters": 27, "literal_blocks": 121,
                            "byte_identical_illustrations": 5, "licence_exact": True,
                            "local_links_valid": True, "drm_absent": True, "javascript_absent": True,
                            "literal_policy": {"language_counts": {"zig": 99, "console": 18, "json": 2, "text": 2},
                                               "rendered_languages_match": True, "bounded_legacy_markers_absent": True},
                            "narrative_paragraphs": 365, "narrative_source_matches": True,
                        })
                    else:
                        self.assertEqual((result.returncode, result.stdout), (1, ""))
                        self.assertEqual(json.loads(result.stderr), {
                            "event": "loti.epub.verification.failed", "error": "Narrative source differs in ref-zig/submission.rst"})


if __name__ == "__main__":
    unittest.main()
