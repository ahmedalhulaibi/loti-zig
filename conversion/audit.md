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
| 4. Recreate every example | 25 native executables; exact compiler gate; 51/51 build steps; 58 native CLI/TCP/reference tests plus eleven binding/trace-tool contracts plus isolated block-device VM test; 37 tutorial-block dispositions | Inspect remaining conversion limits; broader failure paths/state checks and source mutation assessment; independent review |
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
in `mutation-reader-layout.json`. Reader checkpoint bounded total: **69** (51 native,
three line-index, two trace-parser, seven binding-producer, three CSS, three layout
oracle). Historical hashes pin tested versions; this is not whole-port assurance.

Reader checkpoint gates: 47 tests/zero skips, eight 400-case properties, 37/37 Zig build
steps, strict HTML/EPUB and clean EPUBCheck. Reader tooling pins Node 26.8.1 and
Playwright 1.64.0; Chromium sandbox stays enabled, documents have JavaScript
and network disabled. The script lives outside the EPUB. Mandatory independent
review and remaining semantic/effect acceptance are still open; no push or
reviewer retry/fallback occurred.

## Submitted SPLICE effects

`splice-reproduction.json` records constructor-only coverage and the absent
executable, not a native defect. `reference-splice INPUT` now executes owned
file/pipe/pipe and pipe/memfd transfers. Exact 4096-byte pipe capacity forces
short results; an 8196-byte explicit fixture yields request/result pairs
8192/4096, 4100/4096, 4/4. Progress uses completed counts.

`tests/test_splice.py` compares whole reports against an independent byte/cursor
model (400 generated inputs) and a separate literal five-byte oracle. It checks
both source/destination offset modes, output overlap/zero gap, positional
observation, EOF, six correlated negative CQEs, flags and FD teardown before
exit. Exact path/argument failures preserve input; no externally visible output
file is opened. The reference map/disposition/book now point to actual effects.

Eight compiled native mutants were killed; source restored byte-exactly and
rebuilt baseline passed. Two initial Hypothesis assertion groups required a
literal-oracle reassessment; one unused-capture close variant did not compile
and is not assessed. Partial-input failures are explicit, not shrunk. See
`splice-verification.json` and `mutation-splice.json`.

SPLICE checkpoint bounded total: **77** (59 native, three line-index, two trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). This is not
whole-port/SDK assurance. SPLICE scope excludes every filesystem/socket/fixed-FD,
concurrency/cancellation, physical-copy/performance and other-architecture paths.
Independent semantic review remains blocked; nothing is pushed.

SPLICE checkpoint gates: 49 tests/zero skips; nine attributed 400-case properties; exact
Zig 0.17.0/39 build steps; strict HTML/EPUB/EPUBCheck; 27 chapters/113 literals;
81 browser cases/339 code blocks/309 headings, no violations. Browser evidence
still does not attest Supernote, pagination or font overrides. Source fingerprints
are refreshed only after the corresponding full-suite replay.

## Submitted poll readiness and removal

`poll-reproduction.json` records two constructor-only references, not a native
bug. `reference-poll` now validates up to 64 commands before setup and exercises
owned-pipe one-shot IN, pending/immediate readiness, rearm without consuming
bytes, later writes without implicit rearm, FIFO draining and empty cancellation.
Target `-ECANCELED` and remover zero CQEs are correlated independently and sorted
for output only. Missing targets return `-ENOENT`; invalid FDs return `-EBADF`.
Closing the writer produces unrequested HUP, then a positive-length READ proves
EOF. Both pipe descriptors are checked closed before process exit.

The independent command model covers 400 generated plans; separate literal and
eight valid/13 invalid plans cover complete reports and typed rejection. Original
spec-first core hashes remain exact; no ACL seal or independent verifier claim.
A deadline-bypass mutant initially survived all three self-report contracts.
A new syscall oracle checks four actual 1 ms EXT_ARG/ETIME guards and six separate
submissions; seven damaged traces reject wrong count/arguments/errno/submission.
That survivor is now killed, along with eight other compiled native and two
syntax-valid trace-parser variants. One initial typed trace rejection was classified
as a unittest error; assertion classification was made explicit before reassessment.
Every stop restored/rebuilt the baseline. No compile failures are counted.

Poll checkpoint bounded total: **88** (68 native, three line-index, four trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). These do not
attest all kernel operations, every mask/descriptor, readiness/cancel races,
multishot/SQPOLL/concurrency or whole-port assurance. Mandatory independent review
remains blocked; no launcher retry/fallback or push occurred.

Poll checkpoint gates: Zig 0.17.0/41 build steps; 53 tests/zero skips; ten attributed
400-case properties; strict HTML/EPUB/EPUBCheck; 27 chapters/114 literals and 81
browser cases/342 code blocks/312 headings without violations. Source fingerprints
refresh only after corresponding replay. Browser rendering is not device/pagination
or font-override assurance. See `poll-verification.json` and `mutation-poll.json`.

## Submitted epoll interest-list effects

`epoll-reproduction.json` records constructor-only original line 544, not a
kernel defect. `reference-epoll` now submits ADD/MOD/DEL, correlates distinct
control CQEs, and observes actual readiness through native epoll_wait. MOD changes
IN/OUT plus opaque u64 tokens while bytes remain unread; duplicate/missing
operations fail without changing membership. Repeated IN waits show level readiness.
READ drains exact FIFO bytes; closing the last owned read FD removes membership.
Cleanup removes/drains remaining state and queries pipe/epoll/retired FD closure
before exit. Six negative CQEs cover invalid FD/type/op/self/null-ADD storage.

The SDK's target-FD @intCast cannot encode a negative value; a positive owned
retired duplicate provides EBADF without reuse. This is not a production helper
fix. Independent literal transitions/eight fixed plans/nine typed invalid plans
and a 400-case state property check complete reports. A syscall oracle checks 11
separate ring submissions, six actual nonblocking readiness calls/u64 tokens and
no synchronous epoll_ctl substitution; seven damaged traces fail. Ten compiled
native/two syntax-valid parser mutants are killed, without errors/skips or counted
compile failures. Sources restored byte-exactly; rebuilt four-test baseline passed.

The author pre-implementation snapshot is retained, not an ACL seal or independent
agent proof. Two test-only corrections were required: success=False exposes
expected CLI failures; strace 7.0 prints hexadecimal data instead of a decimal
union. Expected behavior and all fixtures stayed exact; amendment pins both
versions. One development anonymous/named request-type mismatch was fixed before
green build; it is not a runtime mutant. Independent acceptance remains open.

Epoll checkpoint bounded total: **100** (78 native, three line-index, six trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). No whole-port,
SDK, every descriptor/flag, ET/ONESHOT/EXCLUSIVE, duplicate-lifetime, race/concurrency
or independent-review assurance. Epoll checkpoint gates: Zig 0.17.0/43 build steps; 57 tests,
zero skips; eleven attributed 400-case properties; strict publication/EPUBCheck;
27 chapters/115 literals, 81 browser cases/345 code blocks/315 headings, no layout
violations. Browser evidence is not device/pagination/font-override assurance.
See `epoll-verification.json`, `epoll-spec-amendment.json`, `mutation-epoll.json`.
At that checkpoint, remaining message/CONNECT effects, other required state/failure semantics,
mandatory blocked review and personal-fork delivery keep the goal incomplete.

## Submitted client connection

`connect-reproduction.json` records constructor-only original line 525, not a
kernel defect. `reference-connect PORT` now connects an owned nonblocking/CLOEXEC
client to a caller-owned IPv4 loopback listener. CONNECT takes peer input/value
length, not a listener/output-length pointer; actual SQE off/len/tag/flags and
CQEs are reported. Getsockname/getpeername return actual endpoints and lengths;
the external listener verifies both identities and EOF after client closure.

Six error CQEs cover invalid FD, non-socket, short address, wrong family, refusal
and already-connected TCP. Three failed socket probes each create/close a fresh
FD; a private bound-but-not-listening guard holds the refusal port. Five socket
lifetimes and the caller-owned ring are checked before exit. No packet is sent
to an arbitrary external address. Addresses conservatively remain live through
CQEs; modern SUBMIT_STABLE requirements are distinguished from early kernels.
The recorded loopback trace takes the CQ-ready fast path; a delayed CONNECT or
actual EXT_ARG fallback entry is not attested by this example.

Three author spec-first tests/fixtures remain byte-exact, not ACL-sealed or an
independent verifier's work. Twenty-five fresh processes use an independent
listener, symbolic literal and syscall oracle: five socket lifetimes, actual
endpoint queries, seven separate submissions, no synchronous connect/listen
substitution. Seven damaged traces fail; 400 generated invalid-port strings and
fixed typed/pre-setup/refusal cases reject unsafe operands. Nine compiled native
and two syntax-valid trace-parser mutants die with substantive assertions,
zero errors/skips; exact source restoration and rebuilt baseline pass. Port
byte-order mutation changes only reporting, not a wire destination; zero-port
mutation cannot address an unrelated listening port. No compile failure counted.

CONNECT checkpoint bounded total: **111** (87 native, three line-index, eight trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). CONNECT checkpoint gates:
Zig 0.17.0/45 build steps; 60 tests/zero failures/errors/skips; twelve attributed
400-case properties; strict publication/EPUBCheck; 27 chapters/116 literals and
81 browser cases/348 code blocks/318 headings without violations. Scope excludes
payload, DNS/TLS, IPv6/datagrams, remote policy, cancellation/interleavings and
accept's supplied peer outputs; no device/pagination or whole-port assurance.
See `connect-verification.json`, `connect-spec-sha256.json`, `mutation-connect.json`.
Active diagnostics: four changed paths, no visible findings, one suppressed
finding disclosed. Fabric/cached graph cannot prove complete callers; current
explicit build/test/map/book consumers were inspected. No blocked reviewer retry,
fallback or push. At that checkpoint, message effects and other semantic gaps, independent review and
personal-fork delivery still keep the goal incomplete.

## Submitted datagrams and ancillary ownership

`messages-reproduction.json` records constructor-only original lines 442/461,
not a native/kernel defect. `reference-messages INPUT CAPACITY` now gathers and
scatters two vectors on a private UNIX datagram pair. Zero records are consumed,
not interpreted as TCP EOF. With input MSG_TRUNC, CQE result is the full datagram
length even above capacity; only the exact bounded prefix is initialized. Without
that input flag, a short receive returns copied bytes. Output msg.flags and CQE
flags are checked separately; whole storage includes untouched poisoned tails.

Native aligned SCM_RIGHTS passes the input's open file description. The sender
FD closes after send completion, before receipt; its numeric slot can be reused.
The received FD independently reads original bytes and has CMSG_CLOEXEC, then
closes/queries before exit. A second right is discarded with absent control
capacity: CTRUNC/data TRUNC are real and the next receive is EAGAIN. Six negative
CQEs check invalid/non-socket FDs, malformed header and invalid passed FD.
Input stays unchanged; no external socket path, network address or output file.

Three author pre-implementation contracts and fixtures remain byte-exact, not
ACL-sealed or independent-verifier artifacts. The binary/capacity property runs
400 valid generated cases, plus zero/boundary examples, a separate literal, seven
fixed plans and 14 typed input negatives. One trace oracle checks 14 actual ring
submissions and closure/CLOEXEC, with seven damaged traces. A compiled fake-census
mutant survived these three tests (40-case initial property run): self-reported
counts were insufficient. A supplemental oracle now independently decodes five
actual procfs open/getdents/EOF/close snapshots, complete byte counts/names and
FD deltas 0/4/4/3/1, excluding the enumerating FD. Seven census damages fail and
the survivor is killed. Original spec stayed exact; no native census change.

Ten compiled native/four syntax-valid syscall/census-parser mutants die with
substantive assertions, no accepted errors/skips/compile failures. Exact source
restoration and rebuilt four-test baseline pass, in a sequential 4 GiB/no-swap
systemd scope. Development shadowed-local compilation and zero-length literal
iovec sentinel EFAULT were fixed in new code before green implementation; neither
is a killed mutant or a defect in previously delivered examples. No shrinking
claim for these development failures. See `messages-spec-sha256.json`,
`messages-oracle-gap.json`, `messages-verification.json`, `mutation-messages.json`.

Message checkpoint bounded total: **125** (97 native, three line-index, twelve trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). Message checkpoint gates:
Zig 0.17.0/47 build steps; 64 tests/zero failures/errors/skips; thirteen attributed
400-case properties; strict HTML/EPUB/EPUBCheck; 27 chapters/117 literals, 81
browser cases/351 code blocks/321 headings without violations. Scope is current
x86_64/Linux, sequential bounded UNIX datagrams/one right. TCP partial sends and
SIGPIPE, UDP/address outputs, other ancillary types, descriptor limits, races,
multishot/cancellation, architectures/kernels and all failure unwinding remain
unattested. Browser evidence is not device/pagination/font-override acceptance.
Five source/test/build/generator diagnostic paths plus supplemental census probe
have no visible findings; suppressed disposition disclosed. Fabric/cached graph
does not establish all callers; explicit CLI/build/test/map/book consumers were
inspected. Mandatory review stays blocked, with no retry/fallback or push. Other
semantic/state/failure gaps and personal-fork delivery keep the goal incomplete.

## Supplied ACCEPT peer outputs and new-FD flags

`accept-reproduction.json` records original line 505's unchecked peer outputs:
HTTP already accepts real clients with null/null outputs. No existing native or
kernel defect claimed. New `reference-accept CAPACITY FLAGS` owns an ephemeral
IPv4 loopback listener, flushes readiness, then accepts an independent owned
client. All 72 null/0–16 capacities × none/nonblock/cloexec/both flag modes are
table-tested; this small finite value domain is not another generated property.

Actual value-result length remains 16 even for zero/truncated capacity; only the
exact native-family/network-port/address prefix is initialized, with all tails
and guards poisoned. Null/null leaves storage untouched. Input length is a
pointer in SQE off, not CONNECT's value. Returned CQE is a new FD independently
identified by native endpoint syscalls/client endpoints, not a zero-success
token. Actual flags show Linux does not inherit listener NONBLOCK. Accepted FD
survives listener close, then closes/queries while ring remains open; client
observes EOF. Three negative CQEs leave address bytes/length unchanged. A
separate symbolic literal, ten typed pre-setup negatives and seven damaged
submission/endpoint/closure traces pin whole contracts.

Author spec snapshot was amended before any implementation solely to contain
strace/native descendants in an owned process group; original draft retained.
Final core tests/fixtures remain byte-exact, not ACL seals or verifier-agent
acceptance. A compiled input-derived flag report survived all three core tests:
the original trace oracle did not require actual flag queries. A supplemental
four-mode oracle now requires six successful fcntl observations, exact absent
or present flags and ordered listener-close/accepted-retention/ring-survival
queries. Seven damaged flag/order traces fail; survivor now dies. A genuine
optional-regex-match diagnostic was fixed in the supplement; affected three
supplemental variants were reassessed, not counted twice. Import-root diagnostic
was disposed with exact runtime import evidence; suppressed findings disclosed.

Eleven compiled native/four syntax-valid syscall/flag-parser mutants die via
assertions, no accepted errors/skips/compile failures. The first Python-only
mutation runner mistakenly retained the last native mutant binary after source
restoration: its 120-second harness timeout is excluded. Owned scope was stopped,
sources restored/rebuilt three-test baseline passed, first ten native kills
retained, remaining oracles reassessed with baseline rebuilds. Exact final
source/spec restoration and rebuilt four-test baseline pass. Memory4GiB/no-swap,
sequential execution; no arbitrary peer or destructive host-storage operations.
See `accept-spec-{initial-sha256,sha256}.json`, `accept-oracle-gap.json`,
`accept-verification.json`, `mutation-accept.json` and retained runner log.

ACCEPT checkpoint bounded total: **140** (108 native, three line-index, sixteen trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). ACCEPT checkpoint gates:
Zig0.17.0/49 build steps; 68 tests/zero failures/errors/skips; thirteen attributed
400-case properties; strict HTML/EPUB/EPUBCheck; 27 chapters/118 literals, 81
browser cases/354 code blocks/324 headings without violations. Scope: current
Linux/x86_64, IPv4 loopback, one-shot outputs/FD flags/lifetimes. No payload,
IPv6/other protocols, resource limits/aborts, descriptor reuse, multishot,
concurrency/cancellation or all failure-unwind claim. Browser is not device
pagination/font-override acceptance. Explicit SDK/source/CLI/build/test/map/book
consumers inspected; stale graph/Fabric unavailability do not imply complete
callgraph coverage. Independent review remains blocked; no retry/fallback or
push. Remaining semantic/state/failure acceptance and delivery keep goal open.

## Real positive short regular-file copy writes

`copy-short-reproduction.json` records unforced partial-write coverage, not a
native/kernel defect: the existing copy loop already advances completed bytes.
Original C copy's partial-I/O branch is at tutorial/cp_liburing.rst:191–197.
Optional `cp INPUT OUTPUT --short-write LIMIT` now lowers only this process's
soft RLIMIT_FSIZE; stable regular source2–16384 bytes, 0<LIMIT<size, original
limit must permit completion. Validation precedes destination creation/truncate;
ordinary two-slot/block copying remains unchanged. Owned files only, no host
device/other-process/resource-hard-limit mutation or privilege requirement.

One full READ precedes a real WRITE(size,offset0) CQE=LIMIT. The helper restores
the exact saved limit before the same copy loop submits the remaining slice at
offsetLIMIT. Only the completed tail retires the slot. Whole output/source bytes,
prepared requests/CQEs and exact progress are compared with an independent
binary/split model (400 valid cases) and whole pinned literal. Fourteen typed
invalid plans preserve prior output/input. Actual prlimit/enter traces require
four limit operations in order around three submissions and reject synchronous
file-write substitutes; seven damaged traces fail. Optional `--fail-read` submits
an invalid-FD READ after arming; actual restore and query precede the typed copy
error. Four damaged recovery traces fail; parent limits/input stay unchanged.
This supplemental recovery contract is author-written after the first core
green implementation, not a preimplementation/ACL-sealed verifier artifact.

Original author spec snapshot retained; one explicit unsealed parser amendment
fixes greedy capture splitting inside an rlimit structure. Live and synthetic
traces both exposed it; behavioral expectations/fixtures stayed exact. System
Python's missing Hypothesis was a runner prerequisite error, not a mutant. Nine
compiled native/four syntax-valid success/recovery parser mutants die through
assertions, zero accepted errors/skips/compile failures. Buffer-reset mutation
leaves metadata correct but corrupts real bytes; exact byte oracle kills it.
All regressions used explicit literal inputs, no shrinking claim. Exact source
restoration and rebuilt four-test baseline pass; baseline rebuilt after every
mutant, including before Python cases. Sequential 4GiB/no-swap process scope.

See `copy-short-spec-sha256.json`, `copy-short-spec-amendment.json`,
`copy-short-verification.json`, `mutation-copy-short.json` and live success/error
traces. Map/dispositions now separate scalar READ/WRITE effects; forced short WRITEV
and forced short READ remain unattested. Scope: current regular filesystem,
one active slot/split, no SIGXFSZ delivery, physical ENOSPC/full-device/crash
durability, multi-slot partial ordering/races, every restoration failure or
other kernels/architectures. Explicit source/SDK/build/CLI/test/map/book consumers
inspected; stale graph/unavailable Fabric is not complete-callgraph proof.

Short-copy checkpoint bounded total: **153** (117 native, three line-index, twenty trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). Short-copy checkpoint gates:
Zig0.17.0/49 build steps; 72 tests/zero failures/errors/skips; fourteen attributed
400-case properties; strict HTML/EPUB/EPUBCheck; 27 chapters/119 literals,
81 browser cases/357 code blocks/327 headings without violations. Diagnostics
and disposed import-root finding disclosed, not an unconditional clean verdict.
Browser is not device/pagination/font overrides. Mandatory review still blocked;
no retry/fallback/push. Semantic/state/failure acceptance and delivery remain open.

## Ordinary enter signal masks, timer ownership and return values

`ordinary-signal-reproduction.json` records missing basic mask evidence, not a
kernel/native defect. Existing EXT_ARG/default contract remains byte-exact.
`reference-signals --ordinary` uses the SDK's basic sigset pointer/NSIG/8 ABI,
not getevents_arg or its deadline. A submitted one-second guard bounds the first
wait; a prequeued self-thread blocked SIGUSR1 is unmasked atomically, handler
runs and raw EINTR returns. Explicit TIMEOUT_REMOVE produces separate target
-ECANCELED/remover0 CQEs, correlated/tag-sorted rather than assuming arrival.
Two submitted timers then expire at20ms/1s; prepared NOP stays local. Blocked
mask/min1 and null-mask/min2 waits return0 submissions without consuming CQEs;
timer CQEs are both -ETIME, not enter errors. Explicit unblock delivers the
second signal; only explicit submit produces the NOP CQE. Full original kernel
action/caller mask checks remain common. No sleeps/external sender/host devices.

An independent whole symbolic fixture checks five fresh processes/selected typed
argument negatives and parent isolation. Actual seven-call basic syscall oracle
checks sizes, masks, thresholds, five submitted SQEs, two same-thread tgkills,
handler query masks and rt_sigreturn masks; ten damaged traces fail. It accepts
equivalent EINTR/ERESTARTNOHAND tracer presentation, not a fabricated event.
Core preimplementation snapshot retained. One transparent unsealed correction
asserts the symbolic fixture root is a dictionary before subscripting: real
Pyright finding, not verifier acceptance/spec relaxation. Valid expectations and
fixtures unchanged; all thirteen ids reassessed on corrected core, no double
count. Nine compiled native/four syntax-valid trace variants fail through
assertions, no errors/skips/compile failures accepted. Exact restoration and
rebuilt four-test baseline (ordinary2/default2). Sequential4GiB/no-swap scope.
Private SDK copy_cqes_ready compile mistake corrected to public copy_cqes(...,0)
during development; not an old-program defect or killed mutant. Missing guessed
Linux-man-pages path and truncated broad manual output are not reading evidence;
specific liburing io_uring_enter mask/EINTR passages were subsequently inspected.

See `ordinary-signal-{spec-sha256,spec-amendment,verification}.json`,
`mutation-ordinary-signal.json`, live trace and scoped fixtures. Two timer bindings
now point at their actual effect consumer; ordinary-enter remains an additional
consumer of the unchanged raw-reader mapping. Native source/build/CLI/test/map/
book consumers inspected; stale graph/Fabric gaps are not complete-callgraph
proof. Scope excludes arbitrary handlers/signals, concurrent sender/SA_RESTART/
IOPOLL/general expiration-removal races, all failure unwinding, other kernels/
architectures. If scheduling misses the intermediate timer-CQ plan, test fails;
no passing skip, no global timing guarantee. Author runs are not independent
verifier/ACL seal or semantic acceptance of every indexed original purpose.

Ordinary-signal checkpoint bounded total: **166** (126 native, three line-index, twenty-four trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). Ordinary-signal checkpoint gates:
Zig0.17.0/49 build steps; 74 tests/zero failures/errors/skips; fourteen attributed
400-case properties; strict HTML/EPUB/EPUBCheck; 27 chapters/119 literals,
81 browser cases/357 code blocks/330 headings without violations. Diagnostics
disclosed, not unconditional clean; browser not device/pagination/font overrides.
Mandatory review host unchanged (installed nested package predates blocker), no
retry/fallback/push. Semantic/state/failure acceptance and delivery remain open.

## Nonzero per-I/O APPEND flags

`rwf-reproduction.json` records unexecuted nonzero-RWF guidance, not a native/
kernel defect. New `reference-rwf INPUT` accepts stable regular1–4097 bytes,
creates only an owned CLOEXEC memfd, never an external output. Source validation
precedes memfd/ring creation; final-component symlinks/nonregular/empty/oversize
inputs rejected. A marker seeds memory. Explicit offset0 +RWF_APPEND appends
payload while cursor1 stays unchanged. Next zero-flag positional write actually
overwrites the prefix, proving per-request APPEND did not become O_APPEND.
All-ones current-position APPEND appends again and advances to completed EOF.
Positional reads/stat/CUR queries capture independent whole bytes/size/cursor
snapshots without advancing position. Unsupported high-bit READ/WRITE return
-EOPNOTSUPP; invalid-FD APPEND -EBADF. Failed-read poison and final bytes/cursor
unchanged. Memory/source close then F_GETFD/-EBADF; caller ring remains open.

Three core contracts: 400 generated binary cases plus explicit1/4097 examples,
separate manually pinned five-byte whole literal/two fresh runs, eight typed
input negatives preserving input/files/symlink. Actual trace requires seven
submissions, private CLOEXEC creation, five non-O_APPEND GETFL observations,
queried ownership, no synchronous memfd-write substitute; eight damages fail.
Core author preimplementation snapshot/fixtures stayed exact, no ACL seal or
independent verifier claim. Nine compiled native/four syntax-valid trace variants
fail through assertions, zero accepted errors/skips. Fake close observations
would preserve JSON; live trace rejects the missing real closes/queries before
exit. Exact restoration and rebuilt three-test baseline. Sequential4GiB/no-swap
scope; baseline rebuilt after every native variant and before Python variants.
Initial array-multiplication mutant did not compile on0.17: excluded, retained
log/partial report, replaced with typed @splat and all ids reassessed once.
No shrinking claim; literal/damaged traces produce deterministic regressions.

SDK File wrapper initially lacked its required flags field; corrected to actual
source NONBLOCK/memfd blocking flags during development, not old defect/kill.
Installed RWF namespace has only HIPRI/DSYNC/SYNC/NOWAIT/APPEND: newer NOAPPEND/
ATOMIC/DONTCACHE SDK names are not invented. Those flags, other filesystems,
append atomicity/concurrent writers, physical durability, forced partial I/O,
cancellation/all unwinding/architectures/historical kernels remain unattested.
One stale README eight-reference-program count was found and replaced with
count-free prose; build target list is inspected/current, not semantic proof.
See `rwf-{spec-sha256,verification}.json`, `mutation-rwf.json`, live trace/fixtures.
Native source/SDK/build/CLI/test/map/book consumers inspected; stale graph/Fabric
gaps are not complete-callgraph or independent semantic acceptance evidence.

RWF checkpoint bounded total: **179** (135 native, three line-index, twenty-eight trace-parser,
seven historical binding-producer, three CSS, three layout-oracle). Checkpoint gates:
Zig0.17.0/51 build steps; 77 tests/zero failures/errors/skips; fifteen attributed
400-case properties; strict HTML/EPUB/EPUBCheck; 27 chapters/120 literals,
81 browser cases/360 code blocks/333 headings without violations. Zero visible
primary diagnostics, three suppressed/two existing OPF spelling infos disclosed,
not unconditional clean. Browser not device/pagination/font overrides. Mandatory
review remains blocked, no retry/fallback/push. Semantic acceptance/delivery open.

## Published literal policy: faithful stale artifacts

`literal-policy-reproduction.json` records four real accepted damaged local
archive/doctree pairs: C text under `cpp`, a GCC/liburing build command, a Zig
C-import declaration, and a mismatched packaged language label. Source-text
fidelity, chapter counts and green EPUB structure were insufficient. No original
native/kernel defect or externally supplied pickle is asserted.

The publication CLI now requires explicit Zig/console/JSON/text labels and exact
packaged/source language correspondence. Bounded markers reject representative
C imports/includes/prototypes, wrapper helpers and compiler/library commands.
Two new CLI contracts challenge 19 source-policy and four rendered-language
cases, including source/archive text changed together. Current 120 literals:
98 Zig, 18 console, two JSON, two text (poem/licence preserved). These counts
are not 98 runnable examples or proof that every declaration is complete.

Original author specs/fixtures retained. A transparent pre-mutation amendment
uses marker-free Zig text under foreign labels, so marker rejection cannot mask
missing language checks; case counts/errors and the separate C-main case stay
exact. This is unsealed author work, not independent verifier acceptance.
Six syntax-valid policy-tool mutants fail substantive CLI assertions; the initial
alias variant produced eight unittest decode errors after a count-dictionary
KeyError and is excluded. Its revised variant makes aggregation dynamic, exposing
actual accepted aliases. Source/spec restoration and four-test baseline verified.

`literal-policy-verification.json` and `mutation-literal-policy.json` bind scope,
inputs and current evidence. Literal-policy checkpoint bounded total **185**: 135 native, three
line-index, 28 trace-parser, seven historical binding-producer, three CSS, three
layout-oracle, six publication-policy. Exact Zig0.17.0/51 build steps, **79 tests**,
zero failures/errors/skips, fifteen attributed 400-case properties. Primary LSP
on three changed Python paths: zero findings. Independent review remains blocked;
no retry/fallback, remote push or goal completion. Pattern checks are not arbitrary
language parsing, prose/link semantics, all original-purpose acceptance or review.

## Observed SQPOLL sleep and genuine wakeups

`sqpoll-wakeup-reproduction.json` records the missing diagnostic; default fixed
file I/O already worked. Its 50-ms pause did not prove NEED_WAKEUP. New
`sq-poll OUTPUT --observe` acquire-loads private shared flags and empty SQ/CQ
state before each request (heads/tails0/1/2); SDK release-publishes and wakes.
Three real SQ_WAKEUP calls precede tagged WRITE26/WRITE23/READ49 completions.
Submit return counts are deliberately not treated as completion results.
Default stdout/file bytes stay exact. Diagnostic output is JSON and the file is
closed/queried after unregister, with ring queried open before final teardown.
Use only owned output paths: both modes create/truncate. Sleep observation has
2000 attempts/1-ms sleeps; scheduling can extend elapsed duration. Completion
waits use 1-s EXT_ARG guards; external test runners bound each process10s.

Two core CLI contracts: five fresh full reports, independent49-byte fixture,
default-byte replay, three argument failures before creation, real kernel trace
and twelve damaged traces. Original author draft/test and fixtures retained.
A transparent harness amendment accepts current strace min_wait_usec or historic
min_time for the same zero reserved field; size/masks/deadline and behavioral
fixtures unchanged. This is not ACL-sealed or independent verifier acceptance.
Nine compiled native/three syntax-valid parser mutants killed by assertions,
zero accepted errors/skips; exact spec/source restoration and rebuilt three-test
baseline, sequential4GiB/no-swap scope. See `mutation-sqpoll-wakeup.json`.
Current bounded total **197**: 144 native, three index,31 trace-parser, seven
historical binding-producer, three CSS, three layout-oracle, six publication-policy.
This is current-host sequential sleep/wakeup evidence, not awake syscall
elimination, all ordering/races, concurrent producers, affinity/shared pollers,
IOPOLL/durability, historical kernels or whole-port assurance.

SDK helpers inspected; unavailable Fabric/stale graphs do not establish complete
callers. Active primary LSP on native/new Python paths: zero findings. One stale
ordinary-enter-unverified author-prose claim was found and corrected against
already executed basic-mask/timer evidence; other restart/IOPOLL/concurrent-sender
limits retained. Churny committed-history probe is not code acceptance. Mandatory
review host unchanged; no retry/fallback/push or goal completion. See
`sqpoll-wakeup-verification.json` for final replay/current fingerprints.
Final gates: Zig0.17.0/51 build steps,81 tests/zero failures/errors/skips,
fifteen attributed400-case properties; strict HTML/EPUB and EPUBCheck5.2.1 with
zero messages. Final27 chapters/120 literals;81 browser cases/360 code blocks/
333 headings, no violations; rebuilt after suite. Browser is not device acceptance.

## Native execution evidence

- Compiler: **0.17.0**. Build: **51/51**. Current complete suite: **81 passed**
  (58 native + one VM + six publication + three inventory + two line-index + eleven binding/trace-tool tests), zero skips,
  with `LOTI_TEST_CASES=400`.
- Ten tutorial executables: `readv`, `raw-cat`, `cat`, `cp`, `probe`, `link`,
  `fixed-buffers`, `sq-poll`, `register-eventfd`, `webserver`.
- Fifteen reference executables: `reference-setup`, `reference-completion`,
  `reference-signals`, `reference-files`, `reference-buffers`, `reference-splice`,
  `reference-poll`, `reference-epoll`, `reference-connect`, `reference-registration`,
  `reference-messages`, `reference-accept`, `reference-rwf`, `reference-submission`, `reference-raw`.
- Readers/copy: whole binary bytes, argument order, empty/boundary-size inputs,
  hard-link safety; two Hypothesis properties use 400 generated cases each.
  A third property checks raw-operation prefix/input preservation and range CQEs;
  a fourth checks registered-file replacement/restore and unchanged binary inputs.
  A fifth checks probe lookup across generated header bounds/flags; a sixth
  models nonblocking CQ capacity commands/head/readiness and whole tag coverage.
  `test-verification.json` records **400 generated passing cases for each of all
  fifteen properties**, source hashes, 77 passing tests and zero skips. These remain
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
- **120 current literal blocks** match Sphinx's source, independently of the
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
   operation/lifetime gaps, including other RWF/restart/IOPOLL, queue state and forced socket/vector/short-read I/O.
2. Extend failure/state checks and execute bounded source mutation verification.
3. Obtain independent review and resolve findings; do not substitute parent checks.
4. Rebuild/audit final artifacts, push only the personal fork, verify remote state.
