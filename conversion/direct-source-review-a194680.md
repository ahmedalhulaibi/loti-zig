# Direct source review — author only

2026-10-11; clean target `a194680d1f187d221515363aa9173f24e3273f9d`.
Original: `c9ee2424af02e4c1e4765088580107d5e17b826e`.
Capture: `_build/verification/direct-source-review.1W60SSUd/capture.json`;
owned `capture.py` records hashes, scope and the broader lexical query.
No new agents, implementation edits, gate replay or mutation campaign.
Changed-path probes: five Markdown files clean; owned capture has two
`unchecked-throwing-call-python` findings, marked false-positive. Its native
JSONDecodeError/OSError intentionally terminate invalid/missing-input capture;
no fallback, successful report or inline suppression is written.

## Actual body reach

Complete, untruncated current bodies read in this pass:

| Native files under `examples/` | Inspected contract |
|---|---|
| reference_setup, mapping_fault | SQ/CQ pointer origins; DONTFORK excludes mappings, not FD; reverse partial-map unwind; private seccomp denial, not physical OOM |
| reference_completion | Copied CQEs consume once; separate borrowed batch; ninth-SQE rejection; capacity-zero drain; physical CQ wrap, not counter overflow |
| reference_signals | Pending self-thread signals; ordinary vs EXT_ARG masks; timer/target CQEs; queued NOP retention; exact action/mask restoration |
| reference_registration | Buffer/file namespaces; sparse/replaced/removed slots; retained registered reference; async update count1; eventfd/personality/probe distinctions |
| reference_raw | NO_SYMLINKS OPENAT2 (not BENEATH-confined); correlated advice/range results; actual MADV_DONTNEED zeroing; completed prefix; negative range results |
| link, probe | Tag-correlated dependency/close ownership; native value probe, raw byte response, lookup bounds/support bit |
| register_eventfd, sq_poll | Joined listener/counter/CQE lifetimes; producer-first notification retained; fixed-file index; acquired sleep state and separate actual CQEs |
| reference_files, reference_rwf | Exclusive output; vectored completed-byte progress; allocation/sync/reopen/close; operation flags vs dependency bits; APPEND/cursor/nonsticky effects |
| reference_splice | Private pipes/memfd; value offsets; positive-short progress; explicit/current cursors; FIFO/drain/EOF and owned closure |
| reference_poll, reference_epoll | Validated command plans; one-shot/rearm/cancel; independent readiness observations; full-u64 tokens; retired positive-FD failure operand |
| reference_connect, reference_accept | Address byte order/lifetimes; CONNECT0 vs ACCEPT new FD; fresh failure sockets; addrlen value-result; explicit close/retention |
| reference_messages | Nested vectors/control; zero datagrams vs EOF; TRUNC/CTRUNC; passed open-file description/CLOEXEC; poison and descriptor census |

These18 plus the12 bodies named in `direct-review-checkpoint.md` reach all30
current example/helper files. All203 earlier tested input hashes remain exact.
File-body reach is not exhaustive semantic acceptance or independent review.
No new verified native defect found in this inspected scope; every error unwind,
kernel, race and architecture remains outside the claimed evidence.

Read nine complete original/current chapter pairs: link, probe, eventfd, SQPOLL,
setup/teardown, completion, CQE, supported capabilities and registered resources.
Rechecked native ownership/result differences against the original prose and
selected exact installed SDK bodies: `get_probe`, `register_files_update`,
`poll_add`, `epoll_ctl`. Existing26-chapter/128-block author reports stay historical;
this nine-pair pass is not a new independent26-chapter acceptance claim.

## Inventory challenge and supplemental enumeration

Canonical3618/128 counts follow the scanner's keyword/block policy. A separate
case-insensitive query scanned all34 UTF-8 original files; seven images and one
generated `.pyc` were explicitly excluded, not decoded or executed. It found1056
lexical candidates, including16 lines outside the canonical inventory:

| Original selector | Classification / current disposition |
|---|---|
| LICENSE:3; sphinx-plugins/manpage.py:4 | Two lowercase copyright markers, not C-language mentions; original licence/source credit retained |
| index.rst:67,69; ref-iouring/index.rst:7 | Three navigation/anchor spellings; current index and syscall toctree retain the section/order; obsolete named toctree options removed |
| low_level.rst:9 | Historical external C-oriented introduction link retired; native low-level chapter teaches the readv prerequisite before ring publication |
| tutorial/cp_liburing.rst:264 | Historical article link retired; current copy chapter credits Shuveb/fio and teaches the same pipelined range ownership |
| ref-iouring/io_uring_enter.rst:344,350,355,371,372,376,378,475 | Eight standalone SQE-flag references; current enter chapter's SQE-flags/error sections and native consumers retain their meanings; original hard-link implication corrected |
| ref-iouring/io_uring_register.rst:73 | Fixed-file flag reference; current registration Files section retains table-index addressing |

All16 original texts/hashes are captured; current target chapters were read.
This supplements enumeration, not the historical canonical index: neither its
counts nor old receipts were rewritten. No missing literal block or unconverted
example was found by this query. Do not call the canonical keyword census alone
an exhaustive census of every io_uring spelling/flag; this broader classification
and the original-purpose scope still require independent challenge.

## Follow-up at ee0b124

`source-inventory-supplement.json` now persists the16 complete original lines,
immutable file hashes, nine current target-file hashes and exact target slices.
A separate structural recomputation agrees with the all34-text-file query and
all16 original rows. Classes: nine SQE-flag references, three navigation lines,
two article pointers, two copyright markers. Canonical3618/128 counts and all203
tested input hashes remain unchanged. This is durable author enumeration, not
independent semantic acceptance.

Corrected this audit's misleading **Confined OPENAT2** label. The raw reference
uses AT.FDCWD/NO_SYMLINKS only; it does not set BENEATH. Three owned finite native
CLI plans confirm absolute and parent-relative paths succeed with the whole
expected report/exact64-byte prefix, while a symlink fails with OpenAt2Failed.
HTTP's root-relative BENEATH|NO_SYMLINKS path is separate and unchanged. This is
an audit-wording correction, not a native/manuscript defect or new test/property.
Receipts: `_build/verification/inventory-supplement.7lIA50vJ/`; no full suite,
build, publication or mutation campaign replay. No new agents or push.

Source supplement probe retains the exact original asset pathname (typos false
positive). Two materializer JSON-call findings are fail-closed CLI false positives;
invalid/missing owned input cannot produce an artifact. No inline suppressions.

## Boundary

Actual EPUB hash remains `fc435ceac8ebd730d614c4f43009a19179ed4488b912415d0cc279a5286165a4`.
Earlier103 tests/16 properties, strict publication/81 reflows/EPUBCheck and292
mutant kills remain earlier author evidence, not newly executed results.
The independent report remains partial/BLOCK. Owner prefers direct review;
author body reach and this supplemental scan do not satisfy the constitution's
independent-verification rule. Final acceptance, exact audit and fork delivery
remain open. No push or goal completion.
