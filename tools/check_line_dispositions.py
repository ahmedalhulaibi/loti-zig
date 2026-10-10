"""Check author note indexing, not conversion semantics or independent review."""

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
BLOCK_DOCS = (
    "implicit-literal-disposition.md",
    "tutorial-block-disposition.md",
    "reference-block-disposition.md",
)
PROSE_DOC = "prose-line-disposition.md"


class DispositionError(ValueError):
    def __init__(self, reason, identity):
        self.record = {"event": "loti.disposition.failed", "reason": reason, "id": identity}
        super().__init__(reason)


def indexed_report(notes_dir):
    inventory_path = ROOT / "conversion/source-inventory.json"
    inventory = json.loads(inventory_path.read_text())
    blocks = {block["id"]: block for block in inventory["blocks"]}
    block_notes = {}
    documents = []
    for name in (*BLOCK_DOCS, PROSE_DOC):
        path = notes_dir / name
        documents.append({"name": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        if name == PROSE_DOC:
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            match = re.match(r"^\| `([^`]+:\d+)` \|", line)
            if not match:
                continue
            identity = match[1]
            if identity not in blocks:
                raise DispositionError("unknown_block", identity)
            if identity in block_notes:
                raise DispositionError("duplicate_block", identity)
            block_notes[identity] = f"{name}:{number}"
    for identity in blocks:
        if identity not in block_notes:
            raise DispositionError("missing_block", identity)

    candidates = {}
    for block in blocks.values():
        for number in range(block["start_line"], block["end_line"] + 1):
            candidates.setdefault((block["file"], number), []).append(block_notes[block["id"]])
    outside = {(row["file"], row["line"]) for row in inventory["lines"]} - candidates.keys()
    target_hashes = {}
    for number, line in enumerate((notes_dir / PROSE_DOC).read_text().splitlines(), 1):
        match = re.fullmatch(r"\| `([^`]+):(\d+)-(\d+)` \| `([^`]+)` \| (.+) \|", line)
        if not match:
            continue
        file, start, end, target, _ = match.groups()
        target_path = (ROOT / target).resolve()
        if not target_path.is_relative_to(ROOT) or not target_path.is_file():
            raise DispositionError("missing_target", target)
        target_hashes[target] = hashlib.sha256(target_path.read_bytes()).hexdigest()
        selected = sorted(key for key in outside if key[0] == file and int(start) <= key[1] <= int(end))
        if not selected:
            raise DispositionError("empty_range", f"{file}:{start}-{end}")
        for key in selected:
            candidates.setdefault(key, []).append(f"{PROSE_DOC}:{number}")

    index = []
    for row in inventory["lines"]:
        key = (row["file"], row["line"])
        notes = candidates.get(key, [])
        if len(notes) != 1:
            raise DispositionError("missing_line" if not notes else "ambiguous_line", f"{key[0]}:{key[1]}")
        index.append({"original": f"{key[0]}:{key[1]}", "note": notes[0]})
    return {
        "scope": "Author line-to-note index only; not semantic acceptance, operation execution or independent review.",
        "source_commit": inventory["source_commit"],
        "inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        "note_documents": documents,
        "target_sha256": dict(sorted(target_hashes.items())),
        "inventoried_lines": len(index),
        "inventoried_blocks": len(blocks),
        "outside_block_lines": len(outside),
        "line_note_index": index,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes-dir", type=Path, default=ROOT / "conversion")
    parser.add_argument("--report", type=Path, default=ROOT / "conversion/line-disposition-verification.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        report = indexed_report(args.notes_dir)
        encoded = (json.dumps(report, indent=2) + "\n").encode()
        if args.check:
            if args.report.read_bytes() != encoded:
                raise DispositionError("stale_report", args.report.name)
        else:
            args.report.write_bytes(encoded)
    except DispositionError as error:
        print(json.dumps(error.record))
        return 1
    except (OSError, ValueError) as error:
        print(json.dumps({"event": "loti.disposition.failed", "reason": type(error).__name__, "id": "input_or_report"}))
        return 1
    print(json.dumps({"event": "loti.disposition.checked" if args.check else "loti.disposition.written",
                      "lines": report["inventoried_lines"], "blocks": report["inventoried_blocks"],
                      "outside_block_lines": report["outside_block_lines"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
