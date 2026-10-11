"""Affected contract replay and owned archive damages, without make epub."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, ContextManager, cast
import unittest
from zipfile import ZipFile

from hypothesis.statistics import collector

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from tests.test_literal_policy import candidate
from tests.test_submission_prose import archive, damage

PROPERTY = "tests.test_provided_buffer_zero.ProvidedBufferZeroContracts.test_zero_result_flags_and_requested_zero_length_follow_buffer_ownership"
NAMES = [
    "tests.test_sqpoll_wakeup", "tests.test_provided_buffer_zero",
    "tests.test_provided_buffer_zero_failure", "tests.test_linked_timeout",
    "tests.test_async_cancel", "tests.test_http_send",
    "tests.test_submission_prose.SubmissionBindingContracts", "tests.test_dispositions",
]
statistics: list[dict[str, Any]] = []


def record(value: dict[str, Any]) -> None:
    phases = {}
    for name in ("reuse-phase", "generate-phase", "shrink-phase"):
        if name in value:
            counts = Counter(case["status"] for case in value[name]["test-cases"])
            phases[name] = {status: counts[status] for status in ("valid", "interesting", "invalid", "overrun")}
    statistics.append({"test": PROPERTY, "phases": phases, "stopped_because": value["stopped-because"]})


def decoded(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise AssertionError("InvalidOwnedJsonObservation") from error


def check_book(book: Path, trees: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(ROOT / "tools/verify_epub.py"), "--book", str(book)]
    if trees is not None:
        command += ["--doctrees", str(trees)]
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)


start = time.monotonic()
scoped = cast(Callable[[Callable[[dict[str, Any]], None]], ContextManager[None]], collector.with_value)
with scoped(record):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(NAMES))
assert result.wasSuccessful() and result.testsRun == 15 and not result.skipped
assert len(statistics) == 1 and statistics[0]["phases"]["generate-phase"]["valid"] == 400
book = ROOT / "_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub"
before_book = hashlib.sha256(book.read_bytes()).hexdigest()
publication = check_book(book)
assert (publication.returncode, publication.stderr) == (0, "")
positive = decoded(publication.stdout)
assert positive == decoded((ROOT / "conversion/epub-verification.json").read_text())
assert positive["book_sha256"] == before_book and positive["narrative_paragraphs"] == 368
assert positive["narrative_source_matches"]
with ZipFile(book) as owned_archive:
    files = {name: owned_archive.read(name) for name in owned_archive.namelist()}
# This is the repository's locally generated doctree, never a supplied pickle.
tree = pickle.loads((ROOT / "_build/doctrees/tutorial/cat.doctree").read_bytes())
literal_cases = decoded((ROOT / "testdata/inputs/literal-policy-damages.json").read_text())
narrative_cases = decoded((ROOT / "testdata/inputs/submission-prose-damages.json").read_text())
assert Counter(case["kind"] for case in literal_cases) == {"source": 19, "render": 4}
assert len(narrative_cases) == 7
probes = []
with tempfile.TemporaryDirectory(prefix="loti-raw-purpose-publication-") as directory:
    work = Path(directory)
    shutil.copytree(ROOT / "_build/doctrees", work / "trees")
    for case in literal_cases:
        path = candidate(work, files, tree, case)
        checked = check_book(path, work / "trees")
        assert (checked.returncode, checked.stdout) == (1, "")
        expected = {"event": "loti.epub.verification.failed", "error": case["error"]}
        assert decoded(checked.stderr) == expected
        probes.append({"family": "literal", "name": case["name"], "returncode": 1, "result": expected})
    for case in narrative_cases:
        path = work / "narrative.epub"
        archive(path, damage(files, case))
        checked = check_book(path)
        if case["kind"] == "whitespace":
            assert (checked.returncode, checked.stderr) == (0, "")
            expected = dict(positive, book_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            assert decoded(checked.stdout) == expected
        else:
            assert (checked.returncode, checked.stdout) == (1, "")
            expected = {"event": "loti.epub.verification.failed", "error": "Narrative source differs in ref-zig/submission.rst"}
            assert decoded(checked.stderr) == expected
        probes.append({"family": "narrative", "name": case["name"], "returncode": checked.returncode, "result": expected})
assert hashlib.sha256(book.read_bytes()).hexdigest() == before_book
reproduction = decoded((ROOT / "conversion/raw-syscall-purpose-reproduction.json").read_text())
original = subprocess.check_output(["git", "show", reproduction["base_commit"] + ":testing.md"])
current = (ROOT / "testing.md").read_bytes()
assert current == original.replace(b"Ordered365", b"Ordered368", 1)
rows = [line for line in current.decode().splitlines() if line.startswith("| Narrative / submission counts |")]
assert rows == [reproduction["expected_whole_row"]]
report = {
    "scope": "15 selected public tests, plus30 existing publication boundary probes run directly without their make-epub setUpClass. No test/expectation overrides, no new full99/mutant/review claim.",
    "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
    "skips": len(result.skipped), "seconds": round(time.monotonic() - start, 3),
    "selected_tests": NAMES, "property_statistics": statistics,
    "publication": positive, "publication_probes": probes,
    "testing_plan": {"whole_row_matches": True, "other_bytes_unchanged": True,
                     "old_sha256": hashlib.sha256(original).hexdigest(),
                     "new_sha256": hashlib.sha256(current).hexdigest()},
    "make_epub_invoked": False,
}
(ROOT / "conversion/raw-syscall-purpose-tests.json").write_text(json.dumps(report, indent=2) + "\n")
print("15 tests/one400-case property;23 literal +7 narrative probes; testing row corrected, other bytes/book unchanged")
