#!/usr/bin/env python3
"""Enumerate original C/io_uring source lines from an immutable Git snapshot."""

import argparse
import json
from pathlib import Path
import re
import subprocess

SOURCE_COMMIT = "c9ee2424af02e4c1e4765088580107d5e17b826e"
ROOT = Path(__file__).resolve().parent.parent
C_MENTION = re.compile(r"\bC(?:\+\+|99|11)?\b|\b(?:gcc|clang|liburing)\b|\.c\b|#include|\bc:(?:function|func|struct|type|data|macro):")
URING_MENTION = re.compile(r"io_uring|IORING_|\bliburing\b", re.IGNORECASE)
C_API = re.compile(r"\bio_uring_(?:get|opcode|register|unregister|queue|ring|wait|peek|cqe|cq|sq|submit|prep|for_each)[A-Za-z_0-9]*\b")
DIRECTIVE = re.compile(r"^(\s*)\.\. (code-block|c:function|c:struct)::\s*(.*)$")
C_LITERAL = re.compile(
    r"(?m)^\s*(?:#\s*include\b|(?:struct|typedef|union|enum)\s+[A-Za-z_]"
    r"|[A-Za-z_]\w*\s*(?:=|\([^;\n]*\)\s*;))"
)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def inventory():
    files = git("ls-tree", "-r", "--name-only", SOURCE_COMMIT).decode().splitlines()
    hits = []
    blocks = []
    symbols = set()
    for name in files:
        if Path(name).suffix not in {".rst", ".c", ".json", ".py", ".html"} and name not in {"Makefile", "make.bat"}:
            continue
        lines = git("show", f"{SOURCE_COMMIT}:{name}").decode().splitlines()
        symbols.update(C_API.findall("\n".join(lines)))
        block_lines = set()
        literal_lines = set()
        for offset, line in enumerate(lines):
            match = DIRECTIVE.match(line)
            implicit = (name.endswith(".rst") and line.rstrip().endswith("::")
                        and not line.lstrip().startswith(".."))
            if match is None and not implicit:
                continue
            if match is not None:
                indent, kind, value = match.groups()
                indent_size = len(indent)
            else:
                indent_size = len(line) - len(line.lstrip())
                kind, value = "literal-block", "unlabelled"
            stop = offset + 1
            while stop < len(lines) and (
                not lines[stop].strip()
                or len(lines[stop]) - len(lines[stop].lstrip()) > indent_size
            ):
                stop += 1
            last = stop
            while last > offset + 1 and not lines[last - 1].strip():
                last -= 1
            if implicit and last == offset + 1:
                continue
            if implicit and C_LITERAL.search("\n".join(lines[offset + 1:last])):
                value = "c"
            is_c = kind.startswith("c:") or value.strip() == "c"
            if is_c:
                block_lines.update(range(offset, last))
            else:
                literal_lines.update(range(offset, last))
            blocks.append({
                "id": f"{name}:{offset + 1}", "file": name,
                "start_line": offset + 1, "end_line": last,
                "kind": kind, "declaration": value,
            })
        for offset, line in enumerate(lines):
            categories = []
            if name.endswith(".c") or offset in block_lines:
                categories.append("c-code")
            if offset in literal_lines:
                categories.append("example-literal")
            if C_MENTION.search(line):
                categories.append("c-reference")
            if URING_MENTION.search(line):
                categories.append("io-uring-reference")
            if categories:
                hits.append({"file": name, "line": offset + 1, "categories": categories, "text": line})
    return {"source_commit": SOURCE_COMMIT, "lines": hits, "blocks": blocks, "c_api_symbols": sorted(symbols)}


def markdown(data):
    result = [
        "# Original C and io_uring inventory", "",
        f"Snapshot: `{SOURCE_COMMIT}`. Regenerate: `python3 tools/inventory.py`.", "",
        "`source-inventory.json` enumerates every matched original line, its exact",
        "text, and categories. Explicit/implicit C literals and example output include",
        "lines without API names. Block coverage is not semantic disposition.", "",
        f"Matched lines: **{len(data['lines'])}**. Source blocks/declarations: **{len(data['blocks'])}**. API symbols: **{len(data['c_api_symbols'])}**.", "",
        "## Per-file line coverage", "", "| File | Original lines |", "|---|---|",
    ]
    for name in sorted({row["file"] for row in data["lines"]}):
        numbers = [str(row["line"]) for row in data["lines"] if row["file"] == name]
        result.append(f"| `{name}` | {', '.join(numbers)} |")
    result.extend(["", "## Source blocks and declarations", "", "| Original location | Kind | Declaration |", "|---|---|---|"])
    for row in data["blocks"]:
        value = row["declaration"].replace("|", "\\|")
        result.append(f"| `{row['file']}:{row['start_line']}-{row['end_line']}` | `{row['kind']}` | `{value}` |")
    return "\n".join(result) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = inventory()
    outputs = {
        ROOT / "conversion/source-inventory.json": json.dumps(data, indent=2) + "\n",
        ROOT / "conversion/source-inventory.md": markdown(data),
    }
    for path, text in outputs.items():
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f"Inventory mismatch: {path}")
        else:
            path.write_text(text)
    print(f"{len(data['lines'])} lines; {len(data['blocks'])} source blocks/declarations; source {SOURCE_COMMIT}")


if __name__ == "__main__":
    main()
