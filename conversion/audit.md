# Completion audit

Status: **not complete**. Independent review remains **blocked**; see
`review-blocker.md`. Evidence below is author-run verification, not that review.

## Success criteria and artifact checklist

Deliver a forked, complete Zig **0.17.0** edition: enumerate every original
C/io_uring line, recreate all examples, update every reference, preserve teaching
coverage/attribution/licence/illustrations, validate the book, then push the fork.

| Requirement | Actual artifacts/evidence | Open requirement |
|---|---|---|
| 1. Fork and local clone | `fork-verification.json`: GitHub reports `isFork=true`, parent `shuveb/loti`; local repository and personal/upstream remotes | Push final conversion and verify remote commit |
| 2. Enumerate every original C/io_uring line | `source-inventory.json`/`.md`: 3,618 matched lines, 128 original blocks/declarations (120 C + eight output); fresh `--check`, independent Docutils extraction and exact source-line comparison | 3,618/3,618 lines now have author note references; independent semantic acceptance remains open |
| 3. Update all references | All 26 original documents rewritten; `chapter-map.json` maps actual paths/order; `reference-map.json` maps 76 inventoried symbols/99 bindings; 13 exact declaration includes | Independent semantic review; resolve any missing operation/lifetime coverage found by disposition |
| 4. Recreate every example | 18 native executables; exact compiler gate; 37/37 build steps; 34 native CLI/TCP/reference tests plus three binding/trace-tool contracts plus isolated block-device VM test; 37 tutorial-block dispositions | Inspect remaining conversion limits; broader failure paths/state checks and source mutation assessment; independent review |
| Build commands/metadata/links | `README.md`, `Makefile`, `conf.py`; native navigation and source inclusions; manuscript scan has no old domains, C blocks, includes or old example URLs | Final scan after remaining fixes |
| Reader-facing book | Full HTML/EPUB build, EPUBCheck 5.2.1, `verify_epub.py`, `epub-verification.json`, publication boundary tests; `reader-layout-verification.json`/two layout contracts cover all spine documents at three CSS widths, with before/after previews | Final rebuild/audit after semantic/review fixes; Supernote/device pagination and font overrides remain unverified |
| Licence/illustrations | Original MIT text in `license.rst`; five original illustrations and logo compared byte-for-byte to immutable upstream | Preserve through final rebuild |
| Independent verification | Failed launcher/run recorded in `review-blocker.md`; no reviewer report exists | Working child host or owner-authorised independent mechanism |

A green inventory, API map, constructor test or book manifest is not proof of
semantic completeness. In particular, document-path coverage does not establish
line/block disposition. Nine rejected archive mutations are publication boundary
tests, **not** the outstanding source-code mutation gate.

## Inventory coverage repair

The first scanner counted 3,447 lines/104 blocks but omitted implicit RST C
literals. `ca7b34e` records the omission. The corrected inventory adds 171 lines
and 24 blocks: 16 implicit C literals, seven implicit output literals and one
explicit HTTP build/output block. Existing source IDs/text and all 76 API
symbols remain. Current totals: 3,618 lines; 120 C blocks/declarations + eight
output literals. The immutable upstream commit is unchanged.

Three boundary tests check the 16 pinned omissions, compare all implicit blocks
with an independent Docutils parse, compare every recorded line/block range with
the original source, and regenerate in fresh processes. `--check` alone had
passed despite the omissions; it was not a coverage proof. LSP: both changed
Python files supported and clean. `implicit-literal-disposition.md` records
these 16 conversions and their limits; independent line/prose acceptance remains open. This
parser check is not the blocked independent agent review.

## Current semantic comparison

`tutorial-block-disposition.md` compares 37 low-level/tutorial blocks (29 C/eight
build-output literals); `implicit-literal-disposition.md` covers 16 implicit C
literals; `reference-block-disposition.md` covers the remaining 75 declarations
and literals. The three ID sets are disjoint and equal the inventory's **128/128**
block IDs. `block-disposition-verification.json` records exact document/inventory
hashes and index coverage, **not** semantic acceptance or independent review.

These ranges contain 3,051 inventoried lines. `prose-line-disposition.md` now
compares the other **567 matched lines** in 87 ranges, including the 226-line
retired `delme.c` declaration catalog (not a runnable program). Four note files
now index **3,618/3,618** original matched lines. `line-disposition-verification.json`
records each original line's actual note row, note/inventory hashes and current
target hashes. `python3 tools/check_line_dispositions.py --check` validates this index;
two boundary tests reject missing/duplicate/unknown references, invalid targets,
empty ranges and stale evidence, and independently reverse-check every note link.
This is author comparison/index evidence, **not semantic acceptance** or review.

`mutation-line-dispositions.json` records three syntax-valid source mutants killed
by these boundary tests: duplicate-block acceptance, wrong note assignment and
ignored stale report. Exact source bytes were restored; baseline tests pass.
This is bounded **index-tool** mutation evidence, not a whole-port assessment.
Python LSP checks have no server findings; three auxiliary rules were marked
false positives (digit-guarded parsing and errors handled at the CLI boundary).
RST LSP is unsupported; refreshed Sphinx/EPUB gates validate the documentation.

The comparison found missing per-I/O `linux.RWF` / `sqe.rw_flags` guidance;
`ref-zig/submission.rst` now distinguishes it from u8 dependency flags. Constructor
rows still separate preparation from effects. Changed-descriptor registered-file
reads now have actual sync replacement/async restore and ownership checks.
Probe listing flags/bounds now have an independent oracle. Full-SQ rejection and
populated nonblocking CQ now have bounded exact/model checks. SIGUSR1/EXT_ARG
pending delivery and full mask restoration now run. Broader signal/restart and
ordinary-enter policies, u32 wrap, CQ overflow and failure/interleavings remain open.

The original copy's `BLKGETSIZE64` input feature is now recreated and executed
against disposable read-only virtual disks. Native `cp` accepts regular or block
input; output is explicitly restricted to regular files. Raw mapping now restores
the separate SQ/CQ strategy; forced-mode evidence is not an older-kernel boot.
Forced short-I/O/state checks remain unverified; see the bounded probe oracle below.

## Reader/copy repair and bounded mutation evidence

- `1b82a08` reproduces a missed public contract: fresh positional stdout writers
  overwrite prior chunks on regular-file redirection. Existing pipe-only PBT
  did not catch this. `84e8f41` selects `writerStreaming`; all three readers now
  preserve the complete redirected bytes.
- `ab3311c` reproduces rejected block input. `sourceSize` now uses native
  `linux.IOCTL.IOR(0x12, 114, usize)`/`linux.ioctl`; the encoded size is `size_t`,
  the result is u64, and interrupted queries retry. The metadata query is
  synchronous; actual data uses the existing two-slot io_uring pipeline.
- `block-device-verification.json`: three readers plus copy execute against
  0/512/33,280/131,584-byte virtio devices in an isolated x86_64 KVM guest.
  Independent fixture/`cmp` checks every output byte; host disk hashes remain
  unchanged. QEMU receives only generated read-only files, never host storage
  devices. QEMU 11.1.1/Linux 7.2.3-arch1-3 are recorded. This is one kernel/ABI,
  not universal device compatibility or independent review.
- `mutation-readers-block.json`: two compiled source mutants killed—positional
  stdout reset and returning block file metadata size instead of ioctl capacity.
  Exact source bytes restored; both boundary tests pass afterward. This is a
  bounded contribution, **not** the remaining whole-port mutation gate.

## Raw mapping restoration

`e0891ef` reproduces the omitted separate-mapping branch. `RawRing.map` now
selects a shared SQ/CQ region or independently sized SQ/CQ mappings, then maps
SQEs separately. Error unwinding releases acquired regions; successful ownership
includes optional CQ memory in `dontFork` and `deinit`.

`raw-mapping-verification.json` records both real strategies on the current
kernel. The reference clears SINGLE_MMAP locally for separate mode; the SDK
wrapper still requires the feature. Each case performs 1,025 alternating
64/31-byte READV operations across SQ/CQ slot reuse. Whole metadata, total 48,704
bytes, independently computed SHA-256 and final prefix are checked. CQ pointer
origins are checked separately because current kernels can share physical backing
between distinct virtual mappings.

Every mapped page passes `mincore` before fork, reports `ENOMEM` in the child
after DONTFORK, and reports `ENOMEM` after parent teardown. Raw `fcntl` confirms
descriptor inheritance in the child and `EBADF` after parent closure. Child
processing uses no inherited allocator/I/O locks. Four compiled source mutants
are killed: SQ-base CQ alias, omitted CQ unmap, omitted CQ DONTFORK, and zero CQ
mask. `.mutants/zig/2026-10-10/raw-mapping/` retains their report and actual
failure logs. Source/test hashes are restored exactly and the rebuilt boundary
passes. LSP supports the three changed source/test files with no diagnostics;
RST is unsupported, so the clean Sphinx/EPUB gates provide document checks.

At that checkpoint, evidence did **not** verify historical-kernel boot compatibility,
injected mapping failures, u32 counter wraparound/interleaving, whole-port
mutation coverage or the blocked independent agent review.

## Registered-file effects

`8ec2675` records the earlier same-FD-only exercise and two-input CLI rejection.
`reference-registration ORIGINAL REPLACEMENT` now observes six fixed reads and
one separately submitted `FILES_UPDATE`: slot 1 reads original bytes, then the
replacement after its application FD is closed, then original bytes after an
async restore. Sparse slot 0, removed slot 1 and an unregistered table return
correlated `-EBADF`. `F_GETFD` independently confirms application descriptor
closure; the async update CQE reports **one** replaced entry.

`registered-files-verification.json` records the actual whole report, source/input
hashes, unchanged inputs and **400 generated passing two-file cases**. The reads
are bounded to the first 64 bytes, not whole-file copying. Pinned differing files
provide an independent byte oracle; empty/binary prefixes and exact tags/results/
flags are checked. CLI arity failures have a separate exact typed-error matrix.

Five compiled source mutants are killed: same-FD substitution, async wrong-slot
update, missing FIXED_FILE, suppressed application close and retained removal
entry. Two initially uncompilable variants are **not assessed**. All logs and
observed mutant fixture reports are retained; exact source restoration and a
rebuilt passing baseline are recorded in `mutation-registered-files.json`.
Concurrent updates and partial multi-entry failures remain unverified.

Fabric tooling is unavailable, Zig call hierarchy is unsupported and the cached
graph is stale; direct bodies and explicit consumers were inspected instead.
This single CLI change crosses implementation/test/publication consumer folders,
not separate domain modules. Active LSP probes found no new diagnostics; one
existing disposition was suppressed. No blocked reviewer retry was attempted.

## Complete named probe-flag oracle

`95faeec` pins all 59 SDK names and reproduces ignored raw/snapshot arguments.
All named opcodes advertise support on this kernel: live-only checks could not
kill constant-true listing. Native `--raw` now queries an unmapped ring into ABI
bytes; Python independently decodes literal header/entry offsets and all returned
flags. Default SDK output must agree exactly for every named opcode.

Mixed/native-endian snapshots check absent/unrelated support bits. The new binary
snapshot property covers both u8 bounds and 256 u16 flag entries; three explicit
bounds cases and an actual shrunk high-flag counterexample are retained/replayed.
The negative CLI matrix rejects wrong arity and short/long snapshots.
`probe-verification.json` records exact output, kernel header/flags and hashes.

Five valid compiled mutants die: constant support, any-nonzero flag, omitted
last-op bound, omitted count bound and truncated raw capacity. An initial literal
true variant failed compilation and is **not assessed**. Exact source restoration
and passing baseline are in `mutation-probe-oracle.json` and committed logs.
This is not whole-port mutation coverage, operation-effect proof, historical
kernel attestation or independent review. Only native little-endian execution
was performed; big-endian fixtures were independently decoded, not executed.

This single CLI change crosses source/test/book consumers, not domain modules.
Fabric call-graph tooling is unavailable; direct bodies/consumers and current
active LSP diagnostics were used, not the stale cached graph. Review remains
blocked; no unsupported-host retry or alternative reviewer launch occurred.

## Full-SQ rejection and nonblocking CQ model

`4fde86c` reproduces an ignored capacity plan and absent execution paths. The
completion CLI now fills eight SQEs and observes ninth-request rejection without
changing pending count/local tail, then submits/waits for all eight CQEs. Default
zero/singleton/batch capacities `0 1 3 8 1` yield counts `0 1 3 4 0` and CQ head
`9 9 10 13 17 17`; all tags 10–17 are consumed once. A literal full-report oracle
pins these values independently of the pure drain model.

Model-based Hypothesis generates destination-capacity command sequences. Its
separate model uses `min(capacity, remaining)` and advances head by that count;
no native encoder/helper is reused. Five input plans and seven rejected argument
cases are committed. `nonblocking-completion-verification.json` records complete
fixture reports, current hashes and 400 generated passing command sequences.
Head 9→17 across a 16-entry CQ proves physical wrap, not u32 counter overflow.
The CQ is stable after the submit/wait barrier: no concurrency/SQPOLL claim.

Seven compiled native exercise mutants die: ignored capacity, double ack,
zero-capacity consumption, incomplete fill, changed tail after rejection,
repeated batch tag and a blocking peek. The last produces the boundary's actual
10-second `TimeoutExpired`. A runner duplicate-anchor assertion stopped before
mutant six; source restoration/rebuilt baseline were checked, completed five
were not repeated, and unique context resumed the remaining two. This runner
error is not a compile-failing mutant. Reports/logs retain the limitation;
installed SDK sources were not mutated. Baseline source is byte-exact restored.

Current active LSP probes find no changed-source/test diagnostics. Fabric graph
navigation is unavailable/stale; direct bodies and CLI/test/book consumers were
inspected. One CLI crosses consumer folders, not domain modules. Author checks
remain separate from blocked independent review; no reviewer retry occurred.

## Pending signals and complete wait-mask restoration

`eb20efe` records absent runtime evidence. New `reference-signals` owns SIGUSR1
in a fresh process: `tgkill` queues it to the blocked calling thread before entry.
No sleep/concurrent sender is used. EXT_ARG temporarily unblocks it and produces
actual handler delivery plus `WaitInterrupted`; handler/caller masks are observed.
USR2/WINCH sentinels distinguish complete masks from a single-bit check.

A second signal stays pending across blocked-mask and null-mask deadline expiry.
The queued NOP remains unsubmitted in both waits. Explicit unblocking delivers
it; explicit submission then yields tag 1/result 0/flags 0. Original mask/kernel
action are restored and independently queried, including restorer flags.
Native rollback errors propagate instead of being silently discarded.
`signal-wait-verification.json` pins the full report, all source/fixture hashes,
current kernel/compiler and **25 fresh passing processes**. The fixture resolves
symbolic masks with Python's independent signal definitions and queries the
parent's initial mask without changing it.

Seven compiled mutants die: ignored mask, zero mask size, EINTR misreported,
signal left blocked, wrong original-mask restore, SDK restore adding RESTORER,
and hidden SQ submission. Both edited native sources were restored byte-exactly;
rebuilt passing baseline and logs are in `mutation-signal-waits.json`.
This is not ordinary-enter, asynchronous-sender race, all-signal/restart-policy,
cross-architecture or historical-kernel attestation. Broader paths remain open.

The first full suite rejected stale publication literal count 105; the verifier
reported 107 for the two new signal console/source literals. The exact consumer
contract was updated and the final **34-test** suite passed. An auxiliary check
initially used system Python without Hypothesis; `.venv` corrected the command,
not native code. Current source/test/build LSP probes are clean. Fabric call
navigation is unavailable/stale; direct bodies and explicit build/test/book
consumers were inspected. This is one signal-wait concern across consumer
folders, not separate domain modules. Independent review remains blocked; no
unsupported-host retry or replacement reviewer was launched.

## Submitted file-operation effects

`d07ede7` records seven passing constructors, not operation effects. Public tests
for new `reference-files INPUT NEW_OUTPUT` first fail with the CLI absent.
The implementation now submits real OPENAT, READV/WRITEV, mode-zero FALLOCATE,
EMPTY_PATH STATX, full/data-only FSYNC and CLOSE requests. Existing output,
same-path output, final symlinks, missing input and non-regular input are rejected.
Tests retain exact original files and reject all invalid argument counts.

Two stable 1024/3072-byte vectors copy every initialized byte, including observed
EOF/empty-input requests. Allocation appends 4096 actual zero bytes; returned
STATX TYPE/SIZE bits and size are checked. Write/allocation CQEs are consumed
before FSYNC; observed opcode/flags distinguish FSYNC from a successful NOP.
Async CLOSE plus F_GETFD/-EBADF checks descriptor ownership before reuse. Reopen
reads/hash the whole output again. Seven separate invalid-descriptor operations
produce exact correlated -EBADF CQEs, not constructor errors.

`file-operations-verification.json` pins whole report/source/fixture/SDK hashes,
400 generated binary cases, independent GNU size/digest and unchanged source.
The 4097-byte literal fixture uses explicit chunk/CQE/flag fields and a GNU
sha256sum digest, separate from the property oracle. The map now points those
seven preparers at actual execution, keeping constructor/effect scope explicit.
The actual failing 4100-byte explicit WRITEV-offset example is retained as a
binary fixture and consumed by its existing example decorator, with identical
bytes. It is not labelled as a generated or shrunk counterexample. The complete
suite was rerun after moving that input from inline bytes to the committed file.

Eight compiled mutants die: existing output accepted, WRITEV offset reset,
FALLOCATE KEEP_SIZE, missing DATASYNC flag, FSYNC replaced by NOP, wrong STATX
FD, CLOSE replaced by NOP and READV reduced to one vector. Exact restored source
and rebuilt passing baseline are recorded in `mutation-file-operations.json`.
There are now 41 bounded valid kills (38 native exercises, three index-tool);
this is not whole-port/SDK assurance. Earlier compile failures remain unassessed.

At the file-reference checkpoint, gates passed: exact Zig 0.17.0, 35 build steps, 37 tests/zero skips,
seven properties each generating 400 valid cases, full strict HTML/EPUB,
109 source-faithful literals and clean EPUBCheck. The VM block receipt was
regenerated because the build target list changed; signal report was replayed
in 25 fresh processes before refreshing consumer fingerprints.

Scope: current kernel/filesystem, sequential owned regular files, allocation
mode zero and TYPE/SIZE fields only. No physical/crash durability, forced short
writes, other allocation modes, concurrent snapshot or atomic replacement claim.
A later failure can leave the new partial output; existing files are not replaced.
Fabric navigation is unavailable/stale; direct bodies and explicit build/test/
map/book consumers were inspected and active LSP probes used. This is one
reference concern across consumer folders, not separate domain modules.
Independent review remains blocked; no new reviewer launch/fallback occurred.

## Provided-buffer ownership and CQE flags

`a9d3f4c` records provide/remove preparation without selected-buffer execution.
Those original declarations came from retired `delme.c`, not a missed runnable
upstream tutorial. Three spec-first CLI contracts failed before implementation.
`reference-buffers INPUT [COMMAND ...]` now executes actual provide/remove and
positive selected reads against owned, nonempty regular input.

Two unused buffers are provided to group 12. Removing three returns **two**;
subsequent selection fails with -ENOBUFS and unchanged storage. Group 9/ID 513
survives a wrong-group read, then is consumed exactly once. Group 7/ID 257 follows
valid read/provide/remove commands; every CQE, flags/ID, availability and owned
storage snapshot matches an independent model. Re-provision resets app-owned
storage before reuse; prefixes and untouched 0xa5 tails are exact. A final
available buffer is removed before pool lifetime ends. Plain/failed CQEs really
exercise NoBufferSelected; selected flags encode IDs in the upper 16 bits.

`provided-buffers-verification.json` pins six actual plan reports, the separate
literal report and current source/fixture/SDK hashes. The new model property
executes 400 valid generated binary/command cases; nine plan/input negatives
have exact typed errors. Selected groups contain one buffer, avoiding any claim
about multi-buffer selection order. Input bytes are unchanged; only first 64
bytes are read. EOF/zero-result, multishot, concurrent arrival and cancellation
ownership remain unverified, as do broader state/failure paths.

Eight compiled mutants die: missing BUFFER_SELECT, wrong group, ID decoded from
low bits, invented unselected ID, changed recycled ID, requested removal count
reported instead of actual count, skipped poison reset and omitted final cleanup.
The actual shrunk cleanup counterexample (one zero byte, choices [0,1]) is
retained as `provided-buffer-cleanup-regression.json` and replayed explicitly;
the whole current suite was rerun after adding that input.
`mutation-provided-buffers.json` records exact restored source and rebuilt passing
baseline; native SDK was not modified. That checkpoint had 49 bounded valid kills
(46 native exercises, three index-tool), not whole-port/SDK assurance.

At the provided-buffer checkpoint, gates passed: exact Zig 0.17.0, 37 build steps, 40 tests/zero skips,
eight 400-case properties, strict full HTML/EPUB, 111 literal blocks and clean
EPUBCheck. Explicit consumers span build/test/map/book folders, not separate
domain modules. Fabric navigation remains unavailable and cached graph stale;
current bodies/consumers and installed declarations were inspected with active
LSP probes. Independent review remains blocked; no retry/fallback was launched.

## Partial-construction failure evidence

`reference-setup --mapping-failure STAGE` now executes five private-descriptor
cases: shared SQ/SQEs and separate SQ/CQ/SQEs. Native x86_64 seccomp denies one
selected mmap with ENOMEM; no privileged operation or host device is used.
Earlier successful mappings are real. Device/inode-matched procfs counts return
to zero; fcntl proves the caller still owns the FD, then proves its explicit
close. Independent strace parsing checks exact syscall order and reverse
address/length unwind pairs. Seven damaged traces are rejected. The filter is
thread-local and permanent for that disposable process, not a security sandbox.
This does not attest physical OOM, all errno paths, SDK construction failures or
other architectures/kernels. `mapping-failure-verification.json` pins the five
reports, actual traces and versions. The absent CLI and spec-red results are
recorded separately; no historical mapping leak is claimed.

Source comparison also found two actual stale generated-reference claims:
SINGLE_MMAP-only mapping and DONTFORK on only two ranges. Both contradicted the
current helper despite a green `reference_map.py --check`. The generator and
whole-binding regression checks now describe all regions and correct ownership.
Two syntactically valid producer regressions are killed. Five compiled native
mutants (omitted SQ/CQ unwind, short unmap, caller FD closure, wrong fault offset)
and two syntax-valid trace-parser mutants are killed; exact restored source and
passing baseline are recorded. That checkpoint had **58** bounded kills (51 native exercise,
three line-index, two trace-parser, two binding-generator), not whole-port/SDK
assurance or independent review. No reviewer retry/fallback was attempted.

At the partial-construction checkpoint, gates passed: Zig 0.17.0, 37/37 build steps, 44 tests/zero skips, eight properties
with 400 generated valid cases each, strict HTML/EPUB, 112 source-faithful
literals and clean EPUBCheck. Current-source hashes are refreshed only after
replaying affected success reports; they pin versions, not correctness.

## Selected API-claim corrections

`reference-claim-audit.md` records a selected body-to-description audit after
reading all 99 generated descriptions. Enter consumes already-published SQEs;
it does not publish the userspace tail. Default `IoUring.init` now points to the
cat tutorial that calls it, not the init_params-only setup reference. Three raw
operation scopes now separate OPENAT2 descriptor/prefix, FADVISE hint-acceptance
CQE and MADVISE anonymous-page zeroing; cache/performance and untested modes are
not claimed. The suspected unused normal-eventfd call was inspected and found
present; no false finding was created. Native code did not change.

`reference-semantics-reproduction.json` records the defective descriptions and
green freshness gate; the red commit tests that state as-is. The correction flips
five full-shape binding fixtures. Five syntax-valid producer regressions die in
the exact contract test while generation and `--check` still pass. Restoration
and results are in `mutation-reference-semantics.json`. That checkpoint had
**63** (51 native exercise, three line-index, two trace-parser, seven binding
producer), not whole-port/SDK assurance or independent semantic acceptance.

At the API-claim checkpoint: 45 author tests/zero skips, eight 400-case properties, Zig 0.17.0,
37/37 build steps, strict full HTML/EPUB, 112 literals and clean EPUBCheck. The
selected report and affected source receipts are refreshed after relevant replay.
The mandatory review host is still blocked; no retry/fallback or push occurred.

## Reader-facing reflow correction

`reader-layout-reproduction.json` and `reader-layout-before.png` record three
syscall heading overflows at 320 CSS pixels; `linux.io_uring_register` was visibly
cut off. Heading `overflow-wrap:anywhere` fixes this without changing chapter
text, literal code or illustrations. `reader-layout-verification.json` measures
all 27 spine documents at 320/600/800: 81 cases, 336 code blocks, six tables,
15 images and 306 headings, with no horizontal loss. Counts include three views
of each element. It is Chromium evidence, not Supernote/pagination acceptance.

The two public contracts assert the whole successful summary and reject four
CSS and three malformed-metadata classes. Active diagnostics found optional
package-node handling; explicit validation fixes it and rejects an empty spine
rather than accepting a zero-case sweep. Both existing tool mutants were
re-assessed after this change; unchanged CSS mutants were not repeated.
Three valid CSS regressions and three syntax-valid coverage/false-clean/empty-
spine oracle regressions are killed; exact restoration and rebuilt baseline are
in `mutation-reader-layout.json`. Current bounded total: **69** (51 native,
three line-index, two trace-parser, seven binding-producer, three CSS, three layout
oracle). Historical hashes pin tested versions; this is not whole-port assurance.

Current gates: 47 tests/zero skips, eight 400-case properties, 37/37 Zig build
steps, strict HTML/EPUB and clean EPUBCheck. Reader tooling pins Node 26.8.1 and
Playwright 1.64.0; Chromium sandbox stays enabled, documents have JavaScript
and network disabled. The script lives outside the EPUB. Mandatory independent
review and remaining semantic/effect acceptance are still open; no push or
reviewer retry/fallback occurred.

## Native execution evidence

- Compiler: **0.17.0**. Build: **37/37**. Current complete suite: **47 passed**
  (34 native + one VM + four publication + three inventory + two line-index + three binding/trace-tool tests), zero skips,
  with `LOTI_TEST_CASES=400`.
- Ten tutorial executables: `readv`, `raw-cat`, `cat`, `cp`, `probe`, `link`,
  `fixed-buffers`, `sq-poll`, `register-eventfd`, `webserver`.
- Eight reference executables: `reference-setup`, `reference-completion`,
  `reference-signals`, `reference-files`, `reference-buffers`, `reference-registration`, `reference-submission`, `reference-raw`.
- Readers/copy: whole binary bytes, argument order, empty/boundary-size inputs,
  hard-link safety; two Hypothesis properties use 400 generated cases each.
  A third property checks raw-operation prefix/input preservation and range CQEs;
  a fourth checks registered-file replacement/restore and unchanged binary inputs.
  A fifth checks probe lookup across generated header bounds/flags; a sixth
  models nonblocking CQ capacity commands/head/readiness and whole tag coverage.
  `test-verification.json` records **400 generated passing cases for each of all
  eight properties**, source hashes, 47 passing tests and zero skips. These remain
  author-run checks, not independent review.
- Linked success/cancellation, four fixed buffers, post-idle polling and threaded
  eventfd notification execute on Linux; actual file/stdout bytes are checked.
- HTTP: real loopback TCP; binary/empty bodies, MIME/length, queries/indexes,
  malformed/method/missing cases, traversal/symlink confinement, oversized headers,
  fragments, concurrent clients and a completing request beside a stalled client.
- Both raw mapping strategies and actual child exclusion/teardown execute;
  variable-length READV batches verify bytes and slot reuse. NOP batches verify
  copy/consume versus separate manual acknowledgement; EXT_ARG wait expires and a
  submitted timer returns `-ETIME`. Async-only eventfd and credential NOP execute;
  both probe paths query the kernel.
- `OPENAT2`, `FADVISE`, `MADVISE` and `SYNC_FILE_RANGE` are submitted; opened bytes
  and owned-page zeroing are checked. Range flags 7 yield a successful CQE;
  invalid flags 8 and descriptor -1 yield separate correlated `-EINVAL`/`-EBADF`
  CQEs. SQE offset/length/range flags are checked against literal expected values.
  This does not establish physical write-out or crash durability.
  The separate **33-constructor** mixed reference is never
  submitted: its metadata checks are not filesystem/network operation evidence.
- SDK signatures/hashes are retained. Compiler/runtime gates are authoritative;
  earlier clean LSP output missed an obsolete allocator method.

## Whole-book publication evidence

```sh
python3 tools/inventory.py --check
python3 tools/reference_map.py --check
python3 tools/reference_docs.py --check
zig fmt --check build.zig examples
zig build --summary all
LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
make html SPHINXOPTS='-E -n -W --keep-going'
make epub SPHINXOPTS='-E -n -W --keep-going'
.venv/bin/python tools/verify_epub.py --report conversion/epub-verification.json
java -jar "$EPUBCHECK_JAR" _build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub
git diff --check
```

- Full guide, not the earlier four-chapter subset: **27 chapters** (all 26 original
  documents plus licence), exact mapped reading order and navigation.
- **111 current literal blocks** match Sphinx's source, independently of the
  **128 original** inventory blocks/declarations; this is not a 1:1 map.
- Local links/fragments resolve; five illustrations, logo and licence are exact.
  No DRM/encryption metadata, JavaScript, script/iframe elements or remote images.
- EPUBCheck **5.2.1**: **0 errors, 0 warnings**. Output is the Zig edition at
  `_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub`; its SHA-256 is in the report.
- Publication tests reject missing chapters, reordered spine, wrong edition title,
  missing navigation, changed code/licence/image, DRM and JavaScript.
  Tests rebuild the archive; the verifier and EPUBCheck were run **after** the
  suite so the report fingerprints the last EPUB, not an earlier ZIP timestamp.
- Native chapter names replace old wrapper-library paths. Tracked `delme.c`,
  `compile_commands.json` and Python bytecode are retired. Historical upstream
  text remains only as immutable conversion evidence, not reader-facing code.

## Next work

1. Obtain semantic acceptance of the author line/block comparisons; inspect
   operation/lifetime gaps, including broader signal/ordinary-enter policies, queue state and forced short-I/O.
2. Extend failure/state checks and execute bounded source mutation verification.
3. Obtain independent review and resolve findings; do not substitute parent checks.
4. Rebuild/audit final artifacts, push only the personal fork, verify remote state.
