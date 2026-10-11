"""Two isolated default-mode leaks; no production mutation or expectation override."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".mutants/http-close/2026-10-11"
CACHE = ROOT / ".zig-cache/http-close-owned-variants"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
source = (ROOT / "examples/webserver.zig").read_bytes()
helper = (ROOT / "examples/raw_ops.zig").read_bytes()
binary_sha256 = hashlib.sha256((ROOT / "zig-out/bin/webserver").read_bytes()).hexdigest()
marker = "        self.clients[id].release(self.allocator);"
assert source.decode().count(marker) == 1
specs = {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
         for p in [Path("tests/test_http_close.py"), Path("tests/test_http.py"),
                   Path("testdata/inputs/http-close-contracts.json")]}
variants = [
    ("default-close-omitted", "        if (self.mode == .serve) self.clients[id].fd = -1;\n"),
    ("default-shutdown-is-not-close", "        if (self.mode == .serve) {\n            _ = linux.shutdown(self.clients[id].fd, linux.SHUT.WR);\n            self.clients[id].fd = -1;\n        }\n"),
]
rows = []
runner = '''import json,sys,unittest
from pathlib import Path
import tests.test_http_close as subject
subject.BIN=Path(sys.argv[1])
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_http_close'))
Path(sys.argv[2]).write_text(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)},indent=2)+'\\n')
'''
for name, insertion in variants:
    directory = OUT / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "webserver.zig").write_text(source.decode().replace(marker, insertion + marker))
    (directory / "raw_ops.zig").write_bytes(helper)
    binary = CACHE / name
    result = subprocess.run(["zig", "build-exe", str(directory / "webserver.zig"),
                             "-femit-bin=" + str(binary)], cwd=ROOT, capture_output=True, timeout=60)
    (directory / "build.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, "CompilationIsNotAKill"
    tested = subprocess.run([sys.executable, "-c", runner, str(binary), str(directory / "tests.json")],
                            cwd=ROOT, capture_output=True, timeout=30)
    (directory / "tests.log").write_bytes(tested.stdout + tested.stderr)
    try:
        counts = json.loads((directory / "tests.json").read_text())
    except (OSError, ValueError) as error:
        raise AssertionError("InvalidOwnedHttpMutationCounts") from error
    assert tested.returncode == 0 and counts == {"tests": 1, "failures": 1, "errors": 0, "skips": 0}, (name, counts)
    rows.append({"name": name, "kind": "native", "result": "substantive-assertion-kill",
                 "counts": counts, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                 "scope": "Default-mode only; owned native execution path routing, no test/expected-value changes."})
assert (ROOT / "examples/webserver.zig").read_bytes() == source
assert (ROOT / "examples/raw_ops.zig").read_bytes() == helper
for path, expected in specs.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
restored = subprocess.run([sys.executable, "-m", "unittest", "tests.test_http_close",
                           "tests.test_http", "tests.test_http_send", "-v"], cwd=ROOT,
                          capture_output=True, timeout=60)
(OUT / "restored.log").write_bytes(restored.stdout + restored.stderr)
assert restored.returncode == 0
assert hashlib.sha256((ROOT / "zig-out/bin/webserver").read_bytes()).hexdigest() == binary_sha256
report = {"scope": "Two author-run bounded compiled default-mode leaks. Header-only and write-shutdown proxies killed by public EOF/child-only descriptor census; not whole-port or independent acceptance.",
          "constraints": {"MemoryMax": "4G", "MemorySwapMax": 0, "TasksMax": 128},
          "spec_sha256": specs, "assessments": rows, "new_native_kills": 2,
          "restored_tests": 7, "production_source_unchanged": True, "production_binary_sha256": binary_sha256,
          "exclusions": "Compiler/test errors, skips and runner failures cannot count. Targeted owned EOF deadline assertion is the public connection-close contract; native omission keeps connection open, not a compiler/runner timeout."}
(OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
(ROOT / "conversion/mutation-http-close.json").write_text(json.dumps(report, indent=2) + "\n")
print("Two valid native assertion kills; restored seven HTTP contracts; production source/binary and expected fixtures unchanged.")
