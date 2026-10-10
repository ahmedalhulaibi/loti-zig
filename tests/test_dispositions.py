"""CLI index boundary; kills omitted/duplicate references and stale evidence."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("implicit-literal-disposition.md", "tutorial-block-disposition.md",
        "reference-block-disposition.md", "prose-line-disposition.md")


def run_index(*args):
    return subprocess.run([sys.executable, "tools/check_line_dispositions.py", *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=30)


class DispositionContracts(unittest.TestCase):
    def test_exact_line_index_and_fresh_process_determinism(self):
        inventory = json.loads((ROOT / "conversion/source-inventory.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            reports = [Path(directory) / name for name in ("first.json", "second.json")]
            for path in reports:
                result = run_index("--report", path)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout), {
                    "event": "loti.disposition.written", "lines": 3618, "blocks": 128,
                    "outside_block_lines": 567,
                })
            self.assertEqual(reports[0].read_bytes(), reports[1].read_bytes())
            report = json.loads(reports[0].read_text())
            self.assertEqual([row["original"] for row in report["line_note_index"]],
                             [f"{row['file']}:{row['line']}" for row in inventory["lines"]])
            # Independent reverse check: every served note row actually selects its original line.
            for entry in report["line_note_index"]:
                document, row_number = entry["note"].rsplit(":", 1)
                row = (ROOT / "conversion" / document).read_text().splitlines()[int(row_number) - 1]
                selector = row.split(" | ", 1)[0].removeprefix("| `").removesuffix("`")
                original_file, original_number = entry["original"].rsplit(":", 1)
                selected_file, selected_range = selector.rsplit(":", 1)
                self.assertEqual(selected_file, original_file)
                if "-" in selected_range:
                    first, last = map(int, selected_range.split("-"))
                else:
                    block = next(b for b in inventory["blocks"] if b["id"] == selector)
                    first, last = block["start_line"], block["end_line"]
                self.assertGreaterEqual(int(original_number), first)
                self.assertLessEqual(int(original_number), last)
            checked = run_index("--report", reports[0], "--check")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(json.loads(checked.stdout), {
                "event": "loti.disposition.checked", "lines": 3618, "blocks": 128,
                "outside_block_lines": 567,
            })

    def test_damaged_notes_and_stale_reports_fail(self):
        cases = {
            "missing_block": (DOCS[0], "remove", "| `ref-iouring/io_uring_enter.rst:11`", "missing_block", "ref-iouring/io_uring_enter.rst:11"),
            "duplicate_block": (DOCS[0], "duplicate", "| `ref-iouring/io_uring_enter.rst:11`", "duplicate_block", "ref-iouring/io_uring_enter.rst:11"),
            "unknown_block": (DOCS[0], "unknown", "| `ref-iouring/io_uring_enter.rst:11`", "unknown_block", "unknown.rst:1"),
            "missing_line": (DOCS[3], "remove", "| `async_intro.rst:58-81`", "missing_line", "async_intro.rst:58"),
            "overlapping_range": (DOCS[3], "duplicate", "| `async_intro.rst:58-81`", "ambiguous_line", "async_intro.rst:58"),
            "missing_target": (DOCS[3], "target", "| `async_intro.rst:58-81`", "missing_target", "missing-target.rst"),
            "empty_range": (DOCS[3], "range", "| `async_intro.rst:58-81`", "empty_range", "async_intro.rst:999-999"),
            "stale_report": (None, "stale", None, "stale_report", "report.json"),
        }
        for name, (doc, mutation, prefix, reason, identity) in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as directory:
                notes = Path(directory)
                for filename in DOCS:
                    shutil.copyfile(ROOT / "conversion" / filename, notes / filename)
                report = notes / "report.json"
                if mutation == "stale":
                    report.write_text("{}\n")
                else:
                    path = notes / doc
                    lines = path.read_text().splitlines()
                    index = next(i for i, line in enumerate(lines) if line.startswith(prefix))
                    if mutation == "remove":
                        del lines[index]
                    elif mutation == "duplicate":
                        lines.insert(index, lines[index])
                    elif mutation == "unknown":
                        lines[index] = lines[index].replace("ref-iouring/io_uring_enter.rst:11", "unknown.rst:1")
                    elif mutation == "target":
                        lines[index] = lines[index].replace("| `async_intro.rst` |", "| `missing-target.rst` |")
                    else:
                        lines[index] = lines[index].replace("58-81", "999-999")
                    path.write_text("\n".join(lines) + "\n")
                args = ("--check",) if mutation == "stale" else ()
                result = run_index("--notes-dir", notes, "--report", report, *args)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout), {
                    "event": "loti.disposition.failed", "reason": reason, "id": identity,
                })
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
