"""Immutable-source inventory boundary; omitted implicit C literals are a bug."""

import json
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest

from docutils.core import publish_doctree
from docutils import nodes

ROOT = Path(__file__).resolve().parent.parent
IMPLICIT_C = {
    "ref-iouring/io_uring_enter.rst": [(11, 13), (58, 60), (64, 68), (76, 112), (425, 434)],
    "ref-iouring/io_uring_register.rst": [(11, 13)],
    "ref-iouring/io_uring_setup.rst": [
        (11, 13), (30, 42), (77, 85), (163, 174), (181, 185),
        (194, 196), (211, 213), (217, 221), (226, 236), (241, 245),
    ],
}


def checked_inventory():
    subprocess.run([sys.executable, "tools/inventory.py", "--check"], cwd=ROOT,
                   check=True, capture_output=True, timeout=30)
    return json.loads((ROOT / "conversion/source-inventory.json").read_text())


class InventoryContracts(unittest.TestCase):
    def test_implicit_syscall_literals_are_not_silently_omitted(self):
        data = checked_inventory()
        found = {block["id"] for block in data["blocks"]}
        missing = [f"{file}:{start}" for file, ranges in IMPLICIT_C.items()
                   for start, _ in ranges if f"{file}:{start}" not in found]
        self.assertEqual(missing, [])
        blocks = {block["id"]: block for block in data["blocks"]}
        for file, ranges in IMPLICIT_C.items():
            for start, end in ranges:
                with self.subTest(file=file, start=start):
                    self.assertEqual(blocks[f"{file}:{start}"], {
                        "id": f"{file}:{start}", "file": file,
                        "start_line": start, "end_line": end,
                        "kind": "literal-block", "declaration": "c",
                    })

    def test_independent_rst_parser_agrees_and_every_literal_line_is_present(self):
        data = checked_inventory()
        files = subprocess.check_output([
            "git", "ls-tree", "-r", "--name-only", data["source_commit"],
        ], cwd=ROOT, text=True).splitlines()
        inventoried_files = {row["file"] for row in data["lines"]}
        self.assertEqual(len(data["lines"]), len({(row["file"], row["line"]) for row in data["lines"]}))
        self.assertEqual(len(data["blocks"]), len({block["id"] for block in data["blocks"]}))
        for file in files:
            if file not in inventoried_files and not file.endswith(".rst"):
                continue
            source = subprocess.check_output([
                "git", "show", f"{data['source_commit']}:{file}",
            ], cwd=ROOT, text=True)
            lines = source.splitlines()
            found = {row["line"]: row["text"] for row in data["lines"]
                     if row["file"] == file}
            with self.subTest(file=file):
                self.assertEqual(list(found.items()), [(number, lines[number - 1]) for number in found])
                for block in data["blocks"]:
                    if block["file"] == file:
                        self.assertEqual(
                            [found.get(number) for number in range(block["start_line"], block["end_line"] + 1)],
                            lines[block["start_line"] - 1:block["end_line"]],
                        )
            if not file.endswith(".rst"):
                continue
            tree = publish_doctree(source, settings_overrides={
                "warning_stream": StringIO(), "halt_level": 6, "report_level": 5,
                "file_insertion_enabled": False, "raw_enabled": False,
            })
            # Unknown Sphinx C directives become system messages, not source literals.
            expected = [(node.line, node.line + len(node.rawsource.splitlines()) - 1)
                        for node in tree.findall(nodes.literal_block)
                        if node.line is not None and not node.get("classes")]
            blocks = [block for block in data["blocks"]
                      if block["file"] == file and block["kind"] == "literal-block"]
            with self.subTest(file=file):
                self.assertEqual([(b["start_line"] + 2, b["end_line"]) for b in blocks],
                                 expected)

    def test_fresh_inventory_processes_are_deterministic(self):
        self.assertEqual(checked_inventory(), checked_inventory())


if __name__ == "__main__":
    unittest.main()
