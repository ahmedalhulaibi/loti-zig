#!/usr/bin/env python3
"""Warnings-as-errors check of the explicitly migrated chapter subset only."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = [
    "async_intro.rst", "what_is_io_uring.rst", "low_level.rst",
    "tutorial/webserver_liburing.rst",
]


def main():
    with tempfile.TemporaryDirectory(prefix="loti-zig-chapters-") as directory:
        work = Path(directory)
        source = work / "source"
        source.mkdir()
        (source / "tutorial").mkdir()
        for chapter in CHAPTERS:
            (source / chapter).symlink_to(ROOT / chapter)
        for folder in ["examples", "_static"]:
            (source / folder).symlink_to(ROOT / folder, target_is_directory=True)
        (source / "conf.py").write_text(
            "project='Lord of the io_uring — Zig 0.17.0 converted chapters'\n"
            "exclude_patterns=['examples/**']\nhtml_static_path=['_static']\n"
        )
        (source / "index.rst").write_text(
            "Converted chapter verification\n==============================\n\n"
            ".. toctree::\n\n" + "".join(f"   {Path(chapter).with_suffix('')}\n" for chapter in CHAPTERS)
        )
        subprocess.run([
            str(ROOT / ".venv/bin/sphinx-build"), "-b", "html", "-n", "-W",
            "--keep-going", str(source), str(work / "html"),
        ], check=True)
        for chapter in CHAPTERS:
            if not (work / "html" / Path(chapter).with_suffix(".html")).is_file():
                raise RuntimeError(f"Missing rendered chapter: {chapter}")
    print(f"Verified {len(CHAPTERS)} rewritten chapters only; not the complete guide or EPUB.")


if __name__ == "__main__":
    main()
