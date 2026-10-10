# Completion audit

Status: **not complete**. Independent review is **blocked**; see `review-blocker.md`.

| Requirement | Current evidence | Missing |
|---|---|---|
| GitHub fork and local clone | `ahmedalhulaibi/loti-zig`; personal origin and upstream remotes | Final converted commit pushed and verified |
| Enumerate original C/io_uring lines | 3,447 lines; 104 C blocks/declarations; regeneration and `--check` agree | Semantic disposition for every original line/block |
| Rewrite every reference | `reference-map.json`: 76 inventoried API symbols, 98 total bindings; signatures checked against exact SDK source | Remaining 22 documents, navigation, semantic review, build commands and links |
| Recreate examples in Zig 0.17.0 | 15 native executables; 31/31 build steps; 17 boundary tests pass | Broader failure paths, queue-state model checks, bounded mutation gate, independent review |
| Book verification | Original edition built earlier; not Zig evidence | Zig HTML/EPUB, validator, content audit |

A green inventory, constructor test, or compiler gate does not prove the full
conversion. Inspect each requirement against the resulting guide and executed code.

## Verified code milestone

```sh
python3 tools/inventory.py --check
python3 tools/reference_map.py --check
zig fmt --check build.zig examples
zig build --summary all
LOTI_TEST_CASES=400 .venv/bin/python -m unittest tests.test_examples tests.test_http tests.test_reference
git diff --check
```

- Compiler: **0.17.0**. Build: **31/31**. Tests: **17 passed**.
- Ten tutorial executables: `readv`, `raw-cat`, `cat`, `cp`, `probe`, `link`,
  `fixed-buffers`, `sq-poll`, `register-eventfd`, `webserver`.
- Five reference executables: `reference-setup`, `reference-completion`,
  `reference-registration`, `reference-submission`, `reference-raw`.
- Core boundary checks: exact file bytes, hard-link safety, linked cancellation,
  four fixed buffers, post-idle polling, threaded eventfd notification. The reader
  and copy properties use 400 generated cases per configured run; the earlier
  milestone also independently inspected Hypothesis's passing-case statistics.
- HTTP: real loopback TCP, binary/empty files, MIME types, query paths, directory
  indexes, missing files, method rejection, malformed escapes, direct/encoded
  traversal, symlink confinement, oversized headers, fragmented requests,
  concurrent clients, and one stalled client alongside a completing request.
- Raw mapping: `RawRing.map` and **`RawRing.dontFork` are called**, followed by an
  actual read. Native SQE/CQE sizes and requested CQ size are checked.
- Completion: real NOPs copied and automatically consumed; a separate batch is
  borrowed and manually acknowledged exactly once. An EXT_ARG deadline expires,
  and a submitted timer reports `-ETIME`.
- Registration: buffer/file registration and table update; forced async NOP
  eventfd notification; credential registration used by an actual NOP; both probe
  paths query the kernel.
- Missing convenience wrappers: `openat2`, `fadvise`, and `madvise` are **submitted**.
  The opened file yields its actual bytes; `MADV_DONTNEED` zeros an independently
  allocated page. This is stronger evidence than constructor metadata alone.
- `reference-submission` exercises **32 SQE constructors**. Its incompatible mixed
  operands are deliberately **not submitted**. Do not infer filesystem/network
  operation execution from these metadata checks.
- SDK source hashes and actual signatures are retained in `reference-map.json`.
  LSP probes were clean, but failed to detect an obsolete `dupeZ` call. The native
  compiler rejected it; the corrected `dupeSentinel` call builds and runs.

## Verified chapter subset

- Rewritten: `async_intro.rst`, `what_is_io_uring.rst`, `low_level.rst`, and
  `tutorial/webserver_liburing.rst`. The legacy HTTP filename/anchor stays until
  navigation migration; its body now includes the compiled Zig source.
- `.venv/bin/python tools/check_chapters.py`: isolated Sphinx 8.2.3 HTML build
  with `-n -W --keep-going` passed. All included sources are compiled repository
  files; original illustrations remain. This is **not** a full-guide build.
- The included `public/index.html` was served byte-exactly over actual loopback
  TCP using the readiness record's ephemeral port.
- Remaining original documents: **22**. Full HTML, EPUB, line/block disposition,
  independently reviewed semantics, and final navigation are still unverified.

## Next work

1. Rewrite all chapters/navigation from verified source; retire stale artifacts.
2. Record line/block disposition and inspect all reference semantics.
3. Extend failure/model checks and run the bounded mutation assessment.
4. Restore independent-review capability; resolve findings.
5. Build/audit the Zig EPUB, complete the requirement audit, then push the fork.
