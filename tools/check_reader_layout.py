"""Measure rendered EPUB spine reflow, not a particular reader device."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"
WIDTHS = [320, 600, 800]


class LayoutError(Exception):
    pass


def attribute(element: ET.Element, name: str) -> str:
    value = element.get(name)
    if not value:
        raise LayoutError("InvalidPackageAttribute")
    return value


def playwright_module():
    binary = shutil.which("playwright")
    if binary is None:
        raise LayoutError("PlaywrightUnavailable")
    package = Path(binary).resolve().parent
    if not (package / "package.json").is_file():
        binary = subprocess.check_output(["mise", "which", "playwright"], text=True).strip()
        package = Path(binary).resolve().parent
    if not (package / "package.json").is_file():
        package = package.parent / "playwright"
    if json.loads((package / "package.json").read_text())["version"] != "1.64.0":
        raise LayoutError("ExpectedPlaywright1_64_0")
    return package


def measure(book, module=None, browser=None):
    module = module or playwright_module()
    browser = browser or shutil.which("chromium")
    if browser is None:
        raise LayoutError("ChromiumUnavailable")
    if shutil.which("node") is None:
        raise LayoutError("NodeUnavailable")
    with tempfile.TemporaryDirectory(prefix="loti-reader-layout.") as directory:
        root = Path(directory)
        with zipfile.ZipFile(book) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise LayoutError("DuplicateArchiveEntry")
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or "\\" in name:
                    raise LayoutError("UnsafeArchivePath")
            if sum(info.file_size for info in archive.infolist()) > 64 * 1024 * 1024:
                raise LayoutError("ArchiveTooLarge")
            container = ET.fromstring(archive.read("META-INF/container.xml"))
            rootfile = container.find("{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles/{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
            if rootfile is None:
                raise LayoutError("MissingRootfile")
            package = attribute(rootfile, "full-path")
            if package not in names:
                raise LayoutError("MissingPackageDocument")
            package_xml = ET.fromstring(archive.read(package))
            ns = {"o": "http://www.idpf.org/2007/opf"}
            items = {attribute(item, "id"): attribute(item, "href") for item in package_xml.findall("./o:manifest/o:item", ns)}
            chapters = []
            for item in package_xml.findall("./o:spine/o:itemref", ns):
                reference = attribute(item, "idref")
                if reference not in items:
                    raise LayoutError("UnknownSpineReference")
                chapters.append(str(PurePosixPath(package).parent / items[reference]))
            if not chapters:
                raise LayoutError("EmptySpine")
            for chapter in chapters:
                if chapter not in names:
                    raise LayoutError("MissingSpineDocument")
                document = ET.fromstring(archive.read(chapter))
                if document.findall(".//{http://www.w3.org/1999/xhtml}script"):
                    raise LayoutError("ScriptedChapterRejected")
            archive.extractall(root)
        (root / "plan.json").write_text(json.dumps({"chapters": chapters, "widths": WIDTHS}))
        result = subprocess.run(["node", str(ROOT / "tools/reader_layout.cjs"), str(root), str(module), str(browser)], capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise LayoutError("BrowserProbeFailed: " + result.stderr.strip())
        raw = json.loads(result.stdout)
    expected = [(chapter, width) for width in WIDTHS for chapter in chapters]
    if [(row["chapter"], row["width"]) for row in raw["rows"]] != expected:
        raise LayoutError("IncompleteLayoutSweep")
    violations = []
    counts = {kind: 0 for kind in ("pre", "table", "image", "heading", "figure")}
    for row in raw["rows"]:
        issues = []
        if row["viewport"] != row["width"]:
            raise LayoutError("ViewportWidthMismatch")
        if row["scroll"] > row["width"]:
            issues.append({"kind": "document", "index": 0, "reason": "horizontal_overflow"})
        if set(row["elements"]) != set(counts):
            raise LayoutError("IncompleteElementMeasurement")
        for kind, elements in row["elements"].items():
            counts[kind] += len(elements)
            for element in elements:
                if element["left"] < -1 or element["right"] > row["width"] + 1 or element["scroll"] > element["client"] + 1:
                    issues.append({"kind": kind, "index": element["index"], "reason": "horizontal_overflow"})
                if kind == "pre" and element["white_space"] != "pre-wrap":
                    issues.append({"kind": kind, "index": element["index"], "reason": "code_not_reflowed"})
        if issues:
            violations.append({"chapter": row["chapter"], "width": row["width"], "issues": issues})
    return {"scope": "Chromium browser reflow at three CSS viewports; not Supernote-device, paginated-reader, semantic or independent review.",
            "book_sha256": hashlib.sha256(Path(book).read_bytes()).hexdigest(),
            "renderer": {key: raw[key] for key in ("node", "playwright", "browser")},
            "chapters": len(chapters), "viewports": WIDTHS, "cases": len(expected),
            "element_counts": counts, "violations": violations, "measurements": raw["rows"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=BOOK)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--playwright-module", type=Path)
    parser.add_argument("--browser", type=Path)
    args = parser.parse_args()
    try:
        report = measure(args.book, args.playwright_module, args.browser)
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + "\n")
        summary = {key: report[key] for key in ("chapters", "viewports", "cases", "element_counts", "violations")}
        summary["event"] = "loti.reader-layout.failed" if report["violations"] else "loti.reader-layout.checked"
        print(json.dumps(summary))
        return 1 if report["violations"] else 0
    except (LayoutError, OSError, ValueError, ET.ParseError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        print(json.dumps({"event": "loti.reader-layout.failed", "error": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
