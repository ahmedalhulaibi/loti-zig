"""Selected author replay; does not overwrite the historical full-suite receipt."""

from collections import Counter
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable, ContextManager, cast
import unittest

from hypothesis.statistics import collector

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
PROPERTY = "tests.test_reference.ReferenceContracts.test_raw_sqe_bindings_execute_and_memory_advice_changes_memory"
NAMES = [
    PROPERTY,
    "tests.test_reference.ReferenceContracts.test_every_preparation_has_the_expected_opcode_and_correlation_tag",
    "tests.test_reference_semantics",
    "tests.test_reference_execution_map",
    "tests.test_submission_prose.SubmissionBindingContracts",
    "tests.test_file_operations.FileOperationContracts.test_literal_oracle_and_rejected_paths_preserve_files",
    "tests.test_examples.ExampleContracts.test_fixed_buffers_write_and_read_registered_ranges",
    "tests.test_examples.ExampleContracts.test_linked_execution_and_failure_cancellation",
    "tests.test_splice.SpliceContracts.test_literal_oracle_and_typed_invalid_inputs",
    "tests.test_poll.PollContracts.test_literal_oracle_and_valid_plans",
    "tests.test_poll_waits",
    "tests.test_epoll.EpollContracts.test_literal_and_fixed_plans",
    "tests.test_epoll_trace",
    "tests.test_connect.ConnectContracts.test_native_connection_matches_external_peer_and_syscalls",
    "tests.test_accept.AcceptContracts.test_independent_full_address_literal",
    "tests.test_accept_flags",
    "tests.test_messages.MessageContracts.test_literal_fixed_plans_and_typed_invalid_inputs",
    "tests.test_messages_trace",
    "tests.test_messages_census",
    "tests.test_http",
    "tests.test_http_send.HttpSendContracts.test_forced_positive_short_send_and_reset_keep_bytes_progress_and_server_alive",
    "tests.test_rwf.RwfContracts.test_literal_and_invalid_inputs_preserve_source_and_create_no_output",
    "tests.test_linked_timeout",
    "tests.test_async_cancel",
    "tests.test_provided_buffers.ProvidedBufferContracts.test_literal_default_and_all_plan_fixtures",
    "tests.test_ordinary_signals.OrdinarySignalContracts.test_pending_masks_timer_cqes_and_queued_nop_ownership",
]
statistics: list[dict[str, Any]] = []


def record(value: dict[str, Any]) -> None:
    phases = {}
    for name in ("reuse-phase", "generate-phase", "shrink-phase"):
        if name in value:
            counts = Counter(case["status"] for case in value[name]["test-cases"])
            phases[name] = {status: counts[status] for status in ("valid", "interesting", "invalid", "overrun")}
    statistics.append({"test": PROPERTY, "phases": phases, "stopped_because": value["stopped-because"]})


suite = unittest.defaultTestLoader.loadTestsFromNames(NAMES)
scoped = cast(Callable[[Callable[[dict[str, Any]], None]], ContextManager[None]], collector.with_value)
start = time.monotonic()
with scoped(record):
    result = unittest.TextTestRunner(verbosity=2).run(suite)
assert result.wasSuccessful() and result.testsRun == 31 and not result.skipped
assert len(statistics) == 1 and statistics[0]["phases"]["generate-phase"]["valid"] == 400
report = {
    "scope": "Selected author submission/SQE replay, not full99 or independent acceptance. No make epub invoked.",
    "tests": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skips": len(result.skipped),
    "seconds": round(time.monotonic() - start, 3),
    "selected_tests": NAMES,
    "property_statistics": statistics,
}
(ROOT / "conversion/submission-purpose-tests.json").write_text(json.dumps(report, indent=2) + "\n")
print("31 selected contracts passed; one property x400 generated valid cases; full99 receipt unchanged")
