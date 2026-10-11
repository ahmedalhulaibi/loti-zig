# Independent review — fd9025d

## Review

No issues found.

This means no verified code defect in the inspected subset. It is **not** exhaustive conversion, runtime or publication acceptance.

- **Correct:** `build.zig:4–12` requires exactly Zig 0.17.0 and Linux; its executable table contains 25 entries (`:13–39`). No build was executed.
- **Correct:** raw SQ publication and CQ consumption use acquire/release ordering, wrapping counters and copy-before-acknowledgement (`examples/raw_cat.zig:105–129`). Mapping unwind distinguishes shared and separate CQ mappings (`:34–85`). `ref-zig/completion.rst:14–38` distinguishes consuming copies from borrowed entries and prohibits double acknowledgement.
- **Correct:** copy progress uses completed byte counts, bounds-checks them and retains slot storage across short operations (`examples/cp.zig:68–115`). Same-file rejection precedes destination truncation (`:56–59`).
- **Correct:** default HTTP completion closes clients after complete headers/body or receive EOF; positive short SENDs advance only by completed bytes (`examples/webserver.zig:243–305`). Resource release closes file/socket descriptors and frees owned bytes (`:76–81`); confinement uses root-relative OPENAT2 with BENEATH/NO_SYMLINKS (`:176–241`). The default-mode test reads actual TCP EOF and checks actual procfs descriptor retirement, not header text or observer reports (`tests/test_http_close.py:48–83`). These are static observations, not executed results.
- **Correct:** probe ownership is a returned native value, not an allocated foreign flexible-array pointer (`examples/probe.zig:44–55`). Installed SDK `std/os/linux.zig:8032–8059` defines the fixed-capacity native probe, checks both lookup bounds and tests support bit zero; `std/os/linux/IoUring.zig:1315–1323` returns it by value.
- **Correct:** sampled original semantic errors are explicitly corrected: original `ref-liburing/submission.rst:418–435` mixed pointer/NULL prose with SPLICE value offsets; current `ref-zig/submission.rst:130–136` explains value/sentinel semantics. Original CONNECT prose (`:525–534`) described a listener and value-result pointer; current prose (`:298–304`) distinguishes the client and numeric input length.
- **Correct:** displayed original/current MIT text matches (`LICENSE:1–21`). Attribution remains explicit (`index.rst:12–17`, `conf.py:9–12,33–40`). This does not verify packaged licence/image bytes.
- **Fixed:** none; review-only. Only this report was written outside the repository.
- **Merge verdict: BLOCK** — the required independent acceptance is incomplete. This is an evidence/setup block, not a demonstrated implementation defect. Do not treat this report as permission to push or release.

## Identity and supplied artifacts

Independent live HEAD/branch/status verification was unavailable. Reviewer rules prohibit shell/Git access, and `watchdog_diff` was not exposed. The supervisor explicitly retained that restriction and permitted source review from parent-generated snapshots.

Parent-supplied identity: clean `master`, HEAD `fd9025d5685209c9c0c6c4cc8e3398835be875a4`; upstream `c9ee2424af02e4c1e4765088580107d5e17b826e`. No supplied mismatch was observed. **These are parent observations, not independently measured live state.**

Artifact root:
`/tmp/pi-subagents-uid-1000/async-subagent-runs/c27be9dc-be43-4ca0-85d3-d98be72fdf5f/review-inputs/`

Read snapshot entry points, selected original bodies and selected range-patch headers. `README.md:7–26` and `capture-summary.json:3–20` report:

- 42 original tracked files; 280 selected current files, with all 1,578 current tracked paths indexed.
- 285 supplied committed-range patches; zero-byte staged/unstaged patches and no non-ignored untracked paths. Ignored outputs/venv/runtime paths are not inventoried.
- Initial capture failure: `conversion/source-inventory.json` patch exceeded the 512 KiB bound (762,329 bytes). Its current body is supplied; the patch is omitted. This is not a complete diff inspection.
- Manifest SHA-256: `2497ebd8afcc8820a55664b4053f97304416528ee83cbe0d8b84392785ac9c40`. Hash/tree matching is the parent's assertion; not independently recomputed.

## Coverage and gaps

Read workspace instructions and the six constitution files through bounded text tools; some long rows were truncated. Read conversion handoff, completion audit/checklist, audit and selected purpose/verification indexes. Author documents expressly keep acceptance open (`conversion/review-handoff.md:3–17`; `conversion/completion-audit-current.md:26–39`).

Static inspection reached all 29 indexed example paths, build configuration, inventory tooling, selected public tests and portions of the current manuscript. Source-body reads covered queue/publication/ownership, short I/O, signals, registration/selection and network/control examples. **Reaching a path is not full-line review.** Large text responses were truncated. All current chapters and every original body were not exhaustively compared.

Installed SDK bodies were inspected under `/home/ahmed/.local/share/mise/installs/zig/0.17.0/lib/`: selected IoUring submission/CQ/queue/publication/deinit methods, SQE preparation, basic ENTER and probe records/consumer. Directory identity is not executable-version verification.

Remaining acceptance-critical work:

1. Independently verify live expected HEAD, branch, clean status and bounded working-tree delta.
2. Independently enumerate and compare every original purpose. The **26 chapters / 128 blocks / 3,618 lines / 76 symbols / 99 bindings** remain author-indexed claims, not independently established totals or accepted meanings. Selected original C/reference bodies and scanner/tests do not prove completeness.
3. Finish whole-body original/current comparison, including nested operand lifetimes, fixed versus provided namespaces, flags/results, cancellation target ownership and error cleanup. The mixed constructor catalogue is not evidence of executing every operation.
4. Execute boundary/adverse tests independently; inspect actual command/trace artifacts. No build, test, kernel, mutation, package, reader or device command ran in this review.
5. Independently verify final EPUB content/order, all illustrations, attribution/licence bytes and links. Author package counts, browser/EPUBCheck receipts and hashes were not reproduced. Device/font/pagination acceptance is separate and unverified.

Broader architecture/kernel, concurrency/cancellation races, transport/production and device assurances remain outside the bounded examples' stated claims; they are not invented code findings. Personal-fork delivery remains the parent's responsibility after acceptance.

## Supervisor-run verification

Use the exact installed SDK and locked `.venv`; record command, exit status, environment prerequisites and log paths against the final HEAD. Suggested first gates (not results):

```console
zig version
zig fmt --check build.zig examples tests/fixtures/vm-mount.zig
zig build --summary all
python3 tools/inventory.py --check
python3 tools/reference_map.py --check
python3 tools/reference_docs.py --check
python3 tools/check_line_dispositions.py --check
.venv/bin/python -m unittest tests.test_http_close tests.test_http_send tests.test_signals tests.test_ordinary_signals
LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
make html SPHINXOPTS='-E -n -W --keep-going'
make epub SPHINXOPTS='-E -n -W --keep-going'
.venv/bin/python tools/verify_epub.py
.venv/bin/python tools/check_reader_layout.py
```

Run the pinned EPUBCheck 5.2.1 gate separately. Runtime passes do not replace the missing exhaustive original-purpose review. Do not install prerequisites, mutate sources or run destructive host-storage tests as part of this review.
