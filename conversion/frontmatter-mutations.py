"""Bounded reader-source mutations with owned README routing; no production edit."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".mutants/frontmatter/2026-10-11"
OUT.mkdir(parents=True, exist_ok=True)
source = (ROOT / "README.md").read_bytes()
specs = {str(path): hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
         for path in [Path("tests/test_readme_publication.py"),
                      Path("testdata/inputs/readme-publication-contract.json")]}
variants = [
    ("old-literal-cardinality", "121 literal", "120 literal"),
    ("old-narrative-cardinality", "368 resolved", "359 resolved"),
    ("overwrite-historical-receipts", "_build/verification/epub.json", "conversion/epub-verification.json"),
]
runner = '''import json,sys,unittest
from pathlib import Path
import tests.test_readme_publication as subject
subject.ROOT=Path(sys.argv[1])
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_readme_publication'))
Path(sys.argv[2]).write_text(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)},indent=2)+'\\n')
'''
rows = []
for name, old, new in variants:
    directory = OUT / name
    directory.mkdir(parents=True, exist_ok=True)
    assert source.decode().count(old) == 1
    (directory / "README.md").write_text(source.decode().replace(old, new))
    # Failures occur before commands execute; these links retain correct routing if reached.
    for label in ["tools", ".venv"]:
        destination = directory / label
        if not destination.exists():
            destination.symlink_to(ROOT / label, target_is_directory=True)
    tested = subprocess.run([sys.executable, "-c", runner, str(directory), str(directory / "tests.json")],
                            cwd=ROOT, capture_output=True, timeout=40)
    (directory / "tests.log").write_bytes(tested.stdout + tested.stderr)
    for label in ["tools", ".venv"]:
        destination = directory / label
        assert destination.is_symlink() and destination.resolve() == ROOT / label
        destination.unlink()
    try:
        counts = json.loads((directory / "tests.json").read_text())
    except (OSError, ValueError) as error:
        raise AssertionError("InvalidOwnedDocumentationMutationCounts") from error
    assert tested.returncode == 0 and counts == {"tests": 1, "failures": 1, "errors": 0, "skips": 0}, (name, counts)
    rows.append({"name": name, "kind": "source-prose", "counts": counts,
                 "assessment": "substantive-assertion-kill", "syntax": "valid Markdown/unchanged shell command structure"})
assert (ROOT / "README.md").read_bytes() == source
for path, expected in specs.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
restored = subprocess.run([sys.executable, "-m", "unittest", "tests.test_readme_publication", "-v"],
                          cwd=ROOT, capture_output=True, timeout=40)
(OUT / "restored.log").write_bytes(restored.stdout + restored.stderr)
assert restored.returncode == 0
report = {"scope": "Three author reader-source contract kills, not native or independent acceptance. Owned README routing only; fixed expectations/test source unchanged; no tracked historical reports overwritten.",
          "constraints": {"MemoryMax": "4G", "MemorySwapMax": 0, "TasksMax": 128},
          "core_sha256": specs, "assessments": rows, "restored_tests": 1,
          "production_readme_unchanged_during_mutations": True,
          "exclusions": "Syntax/runner/test errors and skips are not substantive kills."}
(OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
(ROOT / "conversion/mutation-frontmatter.json").write_text(json.dumps(report, indent=2) + "\n")
print("Three valid source-prose assertion kills;restored1;native and historical receipts unchanged.")
