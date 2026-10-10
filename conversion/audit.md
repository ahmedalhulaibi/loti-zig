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
| 4. Recreate every example | 15 native executables; exact compiler gate; 31/31 build steps; 19 native CLI/TCP/reference tests plus isolated block-device VM test; 37 tutorial-block dispositions | Inspect remaining conversion limits; broader failure paths/state checks and source mutation assessment; independent review |
| Build commands/metadata/links | `README.md`, `Makefile`, `conf.py`; native navigation and source inclusions; manuscript scan has no old domains, C blocks, includes or old example URLs | Final scan after remaining fixes |
| Reader-facing book | Full HTML/EPUB build, EPUBCheck 5.2.1, `verify_epub.py`, `epub-verification.json`, publication boundary tests | Final rebuild/audit after semantic/review fixes; reader-device layout not inspected |
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
rows still separate preparation from effects. An idempotent same-FD table update
does not verify changed-descriptor use. Full probe flags, delivered signals/mask
restoration, populated nonblocking CQ and capacity/failure/state checks remain open.

The original copy's `BLKGETSIZE64` input feature is now recreated and executed
against disposable read-only virtual disks. Native `cp` accepts regular or block
input; output is explicitly restricted to regular files. Raw mapping now restores
the separate SQ/CQ strategy; forced-mode evidence is not an older-kernel boot.
Complete probe-flag oracle and forced short-I/O/state checks remain unverified.

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

This evidence does **not** verify historical-kernel boot compatibility, injected
mapping-construction failures, u32 counter wraparound/interleaving, whole-port
mutation coverage or the blocked independent agent review.

## Native execution evidence

- Compiler: **0.17.0**. Build: **31/31**. Current complete suite: **27 passed**
  (19 native + one VM + two publication + three inventory + two line-index tests), zero skips,
  with `LOTI_TEST_CASES=400`.
- Ten tutorial executables: `readv`, `raw-cat`, `cat`, `cp`, `probe`, `link`,
  `fixed-buffers`, `sq-poll`, `register-eventfd`, `webserver`.
- Five reference executables: `reference-setup`, `reference-completion`,
  `reference-registration`, `reference-submission`, `reference-raw`.
- Readers/copy: whole binary bytes, argument order, empty/boundary-size inputs,
  hard-link safety; two Hypothesis properties use 400 generated cases each.
  A third property checks raw-operation prefix/input preservation and range CQEs
  over arbitrary binary files. `test-verification.json` records **400 passing
  generated cases for each of all three properties**, source hashes, 27 passing
  tests and zero skips; this remains author-run evidence, not independent review.
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
- **105 current literal blocks** match Sphinx's source, independently of the
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
   operation/lifetime gaps, starting with changed-FD registered-table I/O.
2. Extend failure/state checks and execute bounded source mutation verification.
3. Obtain independent review and resolve findings; do not substitute parent checks.
4. Rebuild/audit final artifacts, push only the personal fork, verify remote state.
