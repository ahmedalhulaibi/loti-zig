#!/usr/bin/env python3
"""Audit packaged chapter coverage, exact literals, illustrations and EPUB structure."""

import argparse
import hashlib
import json
from pathlib import Path
import pickle
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from zipfile import ZIP_STORED, ZipFile

from docutils import nodes

ROOT = Path(__file__).resolve().parent.parent
NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "x": "http://www.w3.org/1999/xhtml",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def required_element(root: ET.Element, path: str) -> ET.Element:
    value = root.find(path, NS)
    if value is None:
        raise ValueError(f"Missing XML element: {path}")
    return value


def required_attribute(element: ET.Element, name: str) -> str:
    value = element.get(name)
    if value is None or value == "":
        raise ValueError(f"Missing XML attribute: {name}")
    return value


def upstream(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def page_name(source):
    return str(Path(source).with_suffix(".xhtml"))


def verify(book, doctrees):
    mapping = json.loads((ROOT / "conversion/chapter-map.json").read_text())
    commit = mapping["source_commit"]
    originals = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit], cwd=ROOT, text=True,
    ).splitlines()
    originals = {name for name in originals if name.endswith(".rst")}
    chapters = mapping["chapters"]
    require({entry["original"] for entry in chapters} == originals,
            "Chapter mapping does not cover all immutable original documents")
    original_index = upstream(commit, "index.rst").decode()
    order = ["index.rst"] + [
        str(Path(name).with_suffix(".rst"))
        for name in re.findall(r"^    ([a-zA-Z][\w/.-]*)\s*$", original_index, re.MULTILINE)
    ]
    require([entry["original"] for entry in chapters] == order,
            "Chapter mapping changed the original reading order")
    documents = [entry["zig"] for entry in chapters] + mapping["additional_chapters"]
    require(len(documents) == len(set(documents)), "Duplicate mapped document")
    source_documents = {
        str(path.relative_to(ROOT)) for directory in ["", "tutorial", "ref-zig", "ref-iouring"]
        for path in (ROOT / directory).glob("*.rst")
    }
    require(set(documents) == source_documents, "Unmapped or missing edition document")
    expected_pages = [page_name(name) for name in documents]
    literal_count = image_count = 0
    with ZipFile(book) as archive:
        require(archive.testzip() is None, "Archive CRC failure")
        members = archive.namelist()
        require(len(members) == len(set(members)), "Duplicate archive member")
        require(archive.infolist()[0].filename == "mimetype", "Mimetype is not first")
        require(archive.infolist()[0].compress_type == ZIP_STORED, "Mimetype is compressed")
        require(archive.read("mimetype") == b"application/epub+zip", "Wrong mimetype")
        require(not {"META-INF/rights.xml", "META-INF/encryption.xml"} & set(members),
                "Unexpected DRM/encryption metadata")
        require(not any(name.endswith(".js") for name in members), "Unexpected JavaScript")
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        package_name = required_attribute(required_element(container, ".//{*}rootfile"), "full-path")
        require(package_name == "content.opf", "Unexpected package location")
        package = ET.fromstring(archive.read(package_name))
        manifest = {
            required_attribute(item, "id"): unquote(required_attribute(item, "href"))
            for item in package.findall("./opf:manifest/opf:item", NS)
        }
        spine = [manifest[required_attribute(item, "idref")] for item in package.findall("./opf:spine/opf:itemref", NS)]
        require(spine == expected_pages, "Spine is missing/reordered/duplicated/extended")
        require(required_element(package, "./opf:metadata/dc:title").text == "Lord of the io_uring — Zig 0.17.0",
                "Wrong edition title")
        require(required_element(package, "./opf:metadata/dc:language").text == "en", "Wrong language")
        require(required_element(package, "./opf:metadata/dc:creator").text ==
                "Shuveb Hussain; Zig adaptation by Ahmed Alhulaibi", "Missing author attribution")
        require(set(manifest.values()) <= set(members), "Missing manifest resource")
        pages = {name: ET.fromstring(archive.read(name)) for name in members if name.endswith(".xhtml")}
        require(set(pages) == set(expected_pages) | {"nav.xhtml"}, "Unexpected/missing XHTML page")
        nav_targets = {
            unquote(urlsplit(required_attribute(link, "href")).path)
            for link in pages["nav.xhtml"].findall(".//x:a", NS)
        }
        require(set(expected_pages) <= nav_targets, "Missing chapter in EPUB navigation")
        ids = {name: {element.get("id") for element in page.iter() if element.get("id")}
               for name, page in pages.items()}
        for name, page in pages.items():
            require(not page.findall(".//x:script", NS), f"Script in {name}")
            require(not page.findall(".//x:iframe", NS), f"Iframe in {name}")
            for element in page.iter():
                uri = element.get("href") or element.get("src")
                if uri is None:
                    continue
                parsed = urlsplit(uri)
                if element.tag == "{" + NS["x"] + "}img":
                    require(not parsed.scheme and not parsed.netloc, f"Remote image in {name}")
                if parsed.scheme or parsed.netloc:
                    continue
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path))) if parsed.path else name
                require(target in members, f"Missing local target: {name} -> {uri}")
                if parsed.fragment:
                    require(target in ids and unquote(parsed.fragment) in ids[target],
                            f"Missing fragment: {name} -> {uri}")
        for document in documents:
            page = pages[page_name(document)]
            # Only load locally generated Sphinx artifacts, never untrusted pickles.
            with (doctrees / Path(document).with_suffix(".doctree")).open("rb") as stream:
                tree = pickle.load(stream)
            expected = [node.astext().rstrip("\n") for node in tree.findall(nodes.literal_block)]
            actual = ["".join(element.itertext()).rstrip("\n") for element in page.findall(".//x:pre", NS)]
            require(actual == expected, f"Literal source differs in {document}")
            literal_count += len(actual)
            for node in tree.findall(nodes.literal_block):
                require(node.get("language") != "c", f"Foreign-language code in {document}")
            entry = next((entry for entry in chapters if entry["zig"] == document), None)
            if entry is None:
                continue
            original_images = [uri for uri in re.findall(
                r"^\.\. image:: (\S+)", upstream(commit, entry["original"]).decode(), re.MULTILINE,
            ) if not urlsplit(uri).scheme]
            images = page.findall(".//x:img", NS)
            require(len(images) == len(original_images), f"Changed illustration count in {document}")
            for original, image in zip(original_images, images):
                original_name = posixpath.normpath(posixpath.join(posixpath.dirname(entry["original"]), original))
                packaged = posixpath.normpath(posixpath.join(posixpath.dirname(page_name(document)), unquote(required_attribute(image, "src"))))
                require(archive.read(packaged) == upstream(commit, original_name), f"Changed illustration: {original_name}")
                image_count += 1
        license_literals = ["".join(node.itertext()).rstrip("\n") for node in pages["license.xhtml"].findall(".//x:pre", NS)]
        require(license_literals == [upstream(commit, "LICENSE").decode().rstrip("\n")], "Changed original licence")
        require(archive.read("_static/ebook.css") == (ROOT / "_static/ebook.css").read_bytes(), "Wrong ebook stylesheet")
        require(archive.read("_static/io_uring_logo.png") == upstream(commit, "_static/io_uring_logo.png"), "Changed original logo")
    return {
        "scope": "Publication structure and source fidelity; not semantic or independent review.",
        "source_commit": commit, "book_sha256": hashlib.sha256(book.read_bytes()).hexdigest(),
        "original_chapters": len(chapters), "edition_chapters": len(documents),
        "literal_blocks": literal_count, "byte_identical_illustrations": image_count,
        "licence_exact": True, "local_links_valid": True, "drm_absent": True, "javascript_absent": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", type=Path, default=ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub")
    parser.add_argument("--doctrees", type=Path, default=ROOT / "_build/doctrees")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.book, args.doctrees)
    except ValueError as error:
        print(json.dumps({"event": "loti.epub.verification.failed", "error": str(error)}), file=sys.stderr)
        raise SystemExit(1)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
