"""Replay existing reader/copy boundary contracts; do not replace full-suite evidence."""

import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from typing import Any, Callable, ContextManager, cast

from hypothesis.statistics import collector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
NAMES = [
    "tests.test_examples.ExampleContracts.test_readers_preserve_concatenated_bytes",
    "tests.test_examples.ExampleContracts.test_copy_preserves_bytes_across_buffer_boundaries",
    "tests.test_examples.ExampleContracts.test_copy_rejects_alias_without_destroying_input",
    "tests.test_examples.ExampleContracts.test_readers_preserve_bytes_when_stdout_is_a_regular_file",
    "tests.test_examples.ExampleContracts.test_copy_rejects_unsupported_kinds_before_discarding_data",
    "tests.test_block_devices.BlockDeviceContracts.test_owned_virtio_disks_preserve_every_byte",
]
statistics: list[dict[str, Any]] = []
totals = Counter()

for name in NAMES:
    def collect(value: dict[str, Any]) -> None:
        phases = {}
        for phase in ["reuse-phase", "generate-phase", "shrink-phase"]:
            if phase in value:
                counts = Counter(case["status"] for case in value[phase]["test-cases"])
                phases[phase] = {status: counts[status] for status in
                                 ["valid", "interesting", "invalid", "overrun"]}
        statistics.append({"test": name, "phases": phases,
                           "stopped_because": value["stopped-because"]})

    collect_scope = cast(Callable[[Callable[[dict[str, Any]], None]], ContextManager[None]],
                         collector.with_value)
    with collect_scope(collect):
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromName(name))
    assert result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    totals.update(tests=result.testsRun, failures=len(result.failures),
                  errors=len(result.errors), skips=len(result.skipped))

assert totals == {"tests": 6, "failures": 0, "errors": 0, "skips": 0}
assert [entry["test"] for entry in statistics] == NAMES[:2]
assert all(entry["phases"]["generate-phase"]["valid"] == 400 for entry in statistics)
(ROOT / "conversion/reader-copy-purpose-tests.json").write_text(
    json.dumps({**totals, "selected_tests": NAMES, "property_statistics": statistics,
                "vm": "Existing contract runs zig build plus vm-mount build-exe and16 owned read-only guest cases; not full99/strict publication."},
               indent=2) + "\n")
