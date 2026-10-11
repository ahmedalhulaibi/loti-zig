"""Three sequential bounded variants; compiled native routing never changes expectations."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".mutants/link-ownership/2026-10-11"
SOURCE = ROOT / "examples/link.zig"
DOCUMENT = ROOT / "tutorial/link.rst"
original = SOURCE.read_bytes()
document = DOCUMENT.read_bytes()
specs = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
         for path in [ROOT / "tests/test_link_ownership.py", ROOT / "tests/test_link_prose.py",
                      ROOT / "tests/test_examples.py", ROOT / "testdata/inputs/link-ownership-contracts.json"]}
OUT.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / ".zig-cache/link-ownership-owned-variants"
CACHE.mkdir(parents=True, exist_ok=True)
variants = [
    ("close-is-nop", "native", "_ = try ring.close(3, file.handle);", "_ = try ring.nop(3);"),
    ("cancelled-close-fallback-omitted", "native", "defer if (!closed) file.close(init.io);", "defer if (!closed) {};"),
    ("source-link-count-is-fifteen", "source-prose", "", ""),
]
assessments = []
runner = '''import json,sys,unittest
from pathlib import Path
import tests.test_link_ownership as ownership
name=sys.argv[1]
if sys.argv[2]!='-':ownership.BIN=Path(sys.argv[2])
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(name))
Path(sys.argv[3]).write_text(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)},indent=2)+'\\n')
'''

try:
    for name, kind, old, new in variants:
        directory = OUT / name
        directory.mkdir(parents=True, exist_ok=True)
        binary = "-"
        if kind == "native":
            assert original.decode().count(old) == 1
            source = directory / "link.zig"
            source.write_text(original.decode().replace(old, new))
            binary = str(CACHE / name)
            built = subprocess.run(["zig", "build-exe", str(source), "-femit-bin=" + binary],
                                   cwd=ROOT, capture_output=True, timeout=60)
            (directory / "build.log").write_bytes(built.stdout + built.stderr)
            assert built.returncode == 0, (name, "CompilationIsNotAKill")
            selected = "tests.test_link_ownership"
        else:
            assert document.decode().count("[16,16,0]") == 1
            assert document.decode().count("[16,-9,-125]") == 1
            DOCUMENT.write_text(document.decode().replace("[16,16,0]", "[15,15,0]")
                                .replace("[16,-9,-125]", "[15,-9,-125]"))
            build = subprocess.run(["make", "epub"], cwd=ROOT, capture_output=True, timeout=60)
            (directory / "build.log").write_bytes(build.stdout + build.stderr)
            assert build.returncode == 0, "PublicationBuildIsNotAKill"
            fidelity = subprocess.run([sys.executable, "tools/verify_epub.py"], cwd=ROOT,
                                      capture_output=True, timeout=30)
            (directory / "fidelity.json").write_bytes(fidelity.stdout)
            (directory / "fidelity.stderr").write_bytes(fidelity.stderr)
            assert (fidelity.returncode, fidelity.stderr) == (0, b"")
            selected = "tests.test_link_prose"
        tested = subprocess.run([sys.executable, "-c", runner, selected, binary,
                                 str(directory / "tests.json")], cwd=ROOT,
                                capture_output=True, timeout=60)
        (directory / "tests.log").write_bytes(tested.stdout + tested.stderr)
        counts = json.loads((directory / "tests.json").read_text())
        assert tested.returncode == 0 and counts == {"tests": 1, "failures": 1, "errors": 0, "skips": 0}, (name, counts)
        assessments.append({"name": name, "kind": kind, "result": "substantive-assertion-kill",
                            "counts": counts, "binary_sha256": hashlib.sha256(Path(binary).read_bytes()).hexdigest() if kind == "native" else None,
                            "selected_test": selected,
                            "scope": "Owned binary path routing only; sources/expectations unchanged." if kind == "native" else "Fresh source/package fidelity passed; whole original/native JSON contract failed."})
        DOCUMENT.write_bytes(document)
finally:
    DOCUMENT.write_bytes(document)
    assert SOURCE.read_bytes() == original
    for path, expected in specs.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected

restored = subprocess.run([sys.executable, "-m", "unittest", "tests.test_link_ownership",
                           "tests.test_link_prose", "tests.test_examples.ExampleContracts.test_linked_execution_and_failure_cancellation", "-v"],
                          cwd=ROOT, capture_output=True, timeout=60)
(OUT / "restored.log").write_bytes(restored.stdout + restored.stderr)
assert restored.returncode == 0
report = {"scope": "Author three bounded variants; isolated native copies, unchanged native repository source/binary and immutable expectation hashes. Not whole-port proof or independent review.",
          "constraints": {"MemoryMax": "4G", "MemorySwapMax": 0, "TasksMax": 128},
          "spec_sha256": specs, "assessments": assessments, "restored_tests": 3,
          "new_kills": {"native": 2, "source_prose": 1},
          "excluded": "Initial incorrect15-byte draft fixture/baseline preserved separately; not a kill. Initial incomplete batch/driver and uncompiled fallback variant missing semicolon retained under initial-before-syntax-correction; final three replace partial initial assessment, not add to it. Compilation, test errors, skips and runner failures cannot count."}
(OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
(ROOT / "conversion/mutation-link-ownership.json").write_text(json.dumps(report, indent=2) + "\n")
print("Two native +one source-prose substantive kills; restored three contracts; original native binary/source untouched.")
