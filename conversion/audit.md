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
| 2. Enumerate every original C/io_uring line | `source-inventory.json`/`.md`: 3,618 matched lines, 128 original blocks/declarations (120 C + eight output); fresh `--check`, independent Docutils extraction and exact source-line comparison | Semantic disposition for each inventoried line/block |
| 3. Update all references | All 26 original documents rewritten; `chapter-map.json` maps actual paths/order; `reference-map.json` maps 76 inventoried symbols/98 bindings; 13 exact declaration includes | Independent semantic review; resolve any missing operation/lifetime coverage found by disposition |
| 4. Recreate every example | 15 native executables; exact compiler gate; 31/31 build steps; 17 native CLI/TCP/reference tests | Broader failure paths, generated queue-state checks, bounded source mutation assessment, independent review |
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
explicit directory-output block. Existing source IDs/text and all 76 API
symbols remain. Current totals: 3,618 lines; 120 C blocks/declarations + eight
output literals. The immutable upstream commit is unchanged.

Three boundary tests check the 16 pinned omissions, compare all implicit blocks
with an independent Docutils parse, compare every recorded line/block range with
the original source, and regenerate in fresh processes. `--check` alone had
passed despite the omissions; it was not a coverage proof. LSP: both changed
Python files supported and clean. `implicit-literal-disposition.md` records
these 16 conversions and their limits; other dispositions remain open. This
parser check is not the blocked independent agent review.

## Native execution evidence

- Compiler: **0.17.0**. Build: **31/31**. Current complete suite: **22 passed**
  (17 native + two publication + three inventory tests), with `LOTI_TEST_CASES=400`.
- Ten tutorial executables: `readv`, `raw-cat`, `cat`, `cp`, `probe`, `link`,
  `fixed-buffers`, `sq-poll`, `register-eventfd`, `webserver`.
- Five reference executables: `reference-setup`, `reference-completion`,
  `reference-registration`, `reference-submission`, `reference-raw`.
- Readers/copy: whole binary bytes, argument order, empty/boundary-size inputs,
  hard-link safety; two Hypothesis properties use 400 generated cases each.
- Linked success/cancellation, four fixed buffers, post-idle polling and threaded
  eventfd notification execute on Linux; actual file/stdout bytes are checked.
- HTTP: real loopback TCP; binary/empty bodies, MIME/length, queries/indexes,
  malformed/method/missing cases, traversal/symlink confinement, oversized headers,
  fragments, concurrent clients and a completing request beside a stalled client.
- Raw setup/map/`dontFork` are invoked, followed by a real read. NOP batches verify
  copy/consume versus separate manual acknowledgement; EXT_ARG wait expires and a
  submitted timer returns `-ETIME`. Async-only eventfd and credential NOP execute;
  both probe paths query the kernel.
- `OPENAT2`, `FADVISE` and `MADVISE` are submitted; opened bytes and owned-page
  zeroing are checked. The separate **32-constructor** mixed reference is never
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
- **104 current literal blocks** match Sphinx's source, independently of the
  **128 original** inventory blocks/declarations; this is not a 1:1 map.
- Local links/fragments resolve; five illustrations, logo and licence are exact.
  No DRM/encryption metadata, JavaScript, script/iframe elements or remote images.
- EPUBCheck **5.2.1**: **0 errors, 0 warnings**. Output is the Zig edition at
  `_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub`; its SHA-256 is in the report.
- Publication tests reject missing chapters, reordered spine, wrong edition title,
  missing navigation, changed code/licence/image, DRM and JavaScript.
- Native chapter names replace old wrapper-library paths. Tracked `delme.c`,
  `compile_commands.json` and Python bytecode are retired. Historical upstream
  text remains only as immutable conversion evidence, not reader-facing code.

## Next work

1. Record each line/block's semantic disposition; inspect operation/lifetime gaps.
2. Extend failure/state checks and execute bounded source mutation verification.
3. Obtain independent review and resolve findings; do not substitute parent checks.
4. Rebuild/audit final artifacts, push only the personal fork, verify remote state.
