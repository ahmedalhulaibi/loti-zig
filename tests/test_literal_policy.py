"""Source fidelity alone can faithfully publish stale C code or compiler commands."""

import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from docutils import nodes

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"
X = "http://www.w3.org/1999/xhtml"


def candidate(directory, original, base, case):
    """Mutate only owned locally generated artifacts, never a supplied external pickle."""
    tree = pickle.loads(pickle.dumps(base))
    literal = list(tree.findall(nodes.literal_block))[case["index"]]
    files = dict(original)
    page = ET.fromstring(files["tutorial/cat.xhtml"])
    pre = page.findall(".//{" + X + "}pre")[case["index"]]
    parents = {child: parent for parent in page.iter() for child in parent}
    parent = pre
    while parent is not None:
        classes = parent.get("class", "").split()
        if any(name.startswith("highlight-") for name in classes):
            if case["render"] == "missing":
                parent.set("class", " ".join(name for name in classes if not name.startswith("highlight-")))
            elif case["render"] == "duplicate":
                parent.set("class", parent.get("class", "") + " highlight-console")
            else:
                parent.set("class", " ".join("highlight-" + case["render"] if name.startswith("highlight-") else name for name in classes))
            break
        parent = parents.get(parent)
    assert parent is not None
    if case["kind"] == "source":
        if case["language"] is None:
            literal.attributes.pop("language", None)
        else:
            literal["language"] = case["language"]
        literal[:] = [nodes.Text(case["text"])]
        pre.clear()
        pre.text = case["text"]
    files["tutorial/cat.xhtml"] = ET.tostring(page)
    (directory / "trees/tutorial/cat.doctree").write_bytes(pickle.dumps(tree))
    book = directory / "candidate.epub"
    with ZipFile(book, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content, compress_type=ZIP_STORED if name == "mimetype" else ZIP_DEFLATED)
    return book


class LiteralPolicyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make", "epub"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, timeout=60)
        with ZipFile(BOOK) as archive:
            cls.files = {name: archive.read(name) for name in archive.namelist()}
        cls.tree = pickle.loads((ROOT / "_build/doctrees/tutorial/cat.doctree").read_bytes())

    def check_cases(self, kind):
        cases = json.loads((ROOT / "testdata/inputs/literal-policy-damages.json").read_text())
        selected = [case for case in cases if case["kind"] == kind]
        self.assertEqual(len(selected), {"source": 19, "render": 4}[kind])
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            shutil.copytree(ROOT / "_build/doctrees", work / "trees")
            for case in selected:
                with self.subTest(case=case["name"]):
                    book = candidate(work, self.files, self.tree, case)
                    result = subprocess.run([sys.executable, str(ROOT / "tools/verify_epub.py"),
                                             "--book", str(book), "--doctrees", str(work / "trees")],
                                            cwd=ROOT, capture_output=True, text=True, timeout=15)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(json.loads(result.stderr), {
                        "event": "loti.epub.verification.failed", "error": case["error"]})

    def test_source_language_aliases_and_legacy_markers_fail_even_with_exact_fidelity(self):
        self.check_cases("source")

    def test_packaged_literal_languages_must_match_the_source(self):
        self.check_cases("render")


if __name__ == "__main__":
    unittest.main()
