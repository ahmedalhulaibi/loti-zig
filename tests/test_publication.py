"""Publication CLI contract: correct books pass; damaged structure/content fails."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"
X = "http://www.w3.org/1999/xhtml"
O = "http://www.idpf.org/2007/opf"
D = "http://purl.org/dc/elements/1.1/"


def run_verifier(book):
    return subprocess.run([
        sys.executable, str(ROOT / "tools/verify_epub.py"), "--book", str(book),
    ], cwd=ROOT, capture_output=True, text=True, timeout=30)


def damaged_files(original, mutation):
    files = copy.copy(original)
    if mutation == "missing-chapter":
        del files["tutorial/cat.xhtml"]
    elif mutation == "drm":
        files["META-INF/encryption.xml"] = b"<encryption/>"
    elif mutation == "javascript":
        files["unexpected.js"] = b"alert(1)"
    elif mutation == "image":
        files["_images/ZeroHTTPd_static.png"] = b"changed illustration"
    elif mutation in {"spine", "title"}:
        package = ET.fromstring(files["content.opf"])
        if mutation == "spine":
            spine = package.find("{" + O + "}spine")
            assert spine is not None
            first, second = spine[0].get("idref"), spine[1].get("idref")
            assert first is not None and second is not None
            spine[0].set("idref", second)
            spine[1].set("idref", first)
        else:
            title = package.find(".//{" + D + "}title")
            assert title is not None
            title.text = "Wrong edition"
        files["content.opf"] = ET.tostring(package)
    elif mutation == "navigation":
        page = ET.fromstring(files["nav.xhtml"])
        for parent in page.iter():
            for child in list(parent):
                if child.tag == "{" + X + "}a" and child.get("href", "").split("#")[0] == "tutorial/cat.xhtml":
                    parent.remove(child)
        files["nav.xhtml"] = ET.tostring(page)
    elif mutation in {"literal", "licence"}:
        name = "tutorial/cat.xhtml" if mutation == "literal" else "license.xhtml"
        page = ET.fromstring(files[name])
        literal = page.find(".//{" + X + "}pre")
        assert literal is not None
        literal.text = "Changed literal"
        files[name] = ET.tostring(page)
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return files


class PublicationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make", "epub"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, timeout=60)
        with ZipFile(BOOK) as archive:
            cls.files = {name: archive.read(name) for name in archive.namelist()}

    def test_complete_source_fidelity_report(self):
        result = run_verifier(BOOK)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "scope": "Publication structure and source fidelity; not semantic or independent review.",
            "source_commit": "c9ee2424af02e4c1e4765088580107d5e17b826e",
            "book_sha256": hashlib.sha256(BOOK.read_bytes()).hexdigest(),
            "original_chapters": 26, "edition_chapters": 27, "literal_blocks": 119,
            "byte_identical_illustrations": 5, "licence_exact": True,
            "local_links_valid": True, "drm_absent": True, "javascript_absent": True,
        })

    def test_damaged_artifacts_are_rejected(self):
        cases = {
            "missing-chapter": "Missing manifest resource",
            "drm": "Unexpected DRM/encryption metadata",
            "javascript": "Unexpected JavaScript",
            "image": "Changed illustration: _static/ZeroHTTPd_static.png",
            "spine": "Spine is missing/reordered/duplicated/extended",
            "title": "Wrong edition title",
            "navigation": "Missing chapter in EPUB navigation",
            "literal": "Literal source differs in tutorial/cat.rst",
            "licence": "Literal source differs in license.rst",
        }
        with tempfile.TemporaryDirectory(prefix="loti-publication-tests-") as directory:
            book = Path(directory) / "damaged.epub"
            for mutation, error in cases.items():
                with self.subTest(mutation=mutation):
                    with ZipFile(book, "w") as archive:
                        for name, content in damaged_files(self.files, mutation).items():
                            archive.writestr(name, content, compress_type=ZIP_STORED if name == "mimetype" else ZIP_DEFLATED)
                    result = run_verifier(book)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(json.loads(result.stderr), {
                        "event": "loti.epub.verification.failed", "error": error,
                    })


if __name__ == "__main__":
    unittest.main()
