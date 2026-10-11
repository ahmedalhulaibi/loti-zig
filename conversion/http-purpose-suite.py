"""Full current102 replay; preserve prior101/99 receipts as historical evidence."""

import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from typing import Any, Callable, ContextManager, cast

from hypothesis.statistics import collector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
active: list[str | None] = [None]
statistics: list[dict[str, Any]] = []


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def startTest(self, test):
        active[0] = test.id()
        super().startTest(test)


def collect(value: dict[str, Any]) -> None:
    phases = {}
    for phase in ["reuse-phase", "generate-phase", "shrink-phase"]:
        if phase in value:
            counts = Counter(case["status"] for case in value[phase]["test-cases"])
            phases[phase] = {status: counts[status] for status in
                             ["valid", "interesting", "invalid", "overrun"]}
    statistics.append({"test": active[0], "phases": phases,
                       "stopped_because": value["stopped-because"]})


scope = cast(Callable[[Callable[[dict[str, Any]], None]], ContextManager[None]], collector.with_value)
with scope(collect):
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(
        unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT)))
assert result.wasSuccessful() and result.testsRun == 102 and not result.skipped
assert len(statistics) == 16
assert all(entry["phases"]["generate-phase"]["valid"] == 400 for entry in statistics)
try:
    old = json.loads((ROOT / "conversion/tutorial-modes-full-tests.json").read_text())
except (OSError, ValueError) as error:
    raise AssertionError("InvalidOwnedPriorSuiteReceipt") from error
sources = set(old["source_sha256"]) | {"tests/test_http_close.py", "testdata/inputs/http-close-contracts.json"}
(ROOT / "conversion/http-purpose-full-tests.json").write_text(json.dumps({
    "scope": "Author full current102, including default HTTP EOF/descriptor ownership; historical101/99 unchanged, not independent acceptance.",
    "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
    "skipped": len(result.skipped), "property_statistics": statistics,
    "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(sources)},
    "publication": "Suite invokes make epub. Check actual current archive after suite; unchanged native/publication inputs do not imply semantic acceptance.",
}, indent=2) + "\n")
print("102 tests;zero failures/errors/skips;16 properties x400 generated valid cases;historical101/99 receipts unchanged.")
