# Independent review handoff

Status: **incomplete, not accepted**. `review-blocker.md` retains earlier host
failures. Native async reviewer `c27be9dc` now ran against `fd9025d`; its report
is `independent-review-fd9025d.md`. It found no verified defect in its inspected
subset but returned BLOCK: original-purpose coverage and independent runtime/
publication acceptance were incomplete. Do not substitute author tests, hashes,
parsers, mutation results or this document for that review.

Owner now prefers direct review; no new reviewer agents are launched. Fresh
direct gates are recorded in `direct-review-checkpoint.md`; these are author
verification, not a waiver of independent acceptance. `direct-source-review-a194680.md`
adds18 complete native bodies, nine chapter pairs and16 supplemental lexical
rows persisted in `source-inventory-supplement.json`. Current-body reach is30/30; original-purpose
classification and independent acceptance remain distinct, unresolved gates.

Latest author checkpoint: `frontmatter-verification.json`,
`completion-audit-current.md` and `prompt-to-artifact-checklist.md`. Original
26 whole chapters/128 blocks have author comparison; full103/16×400,292 bounded
mutants. These are not review acceptance. Current frontmatter-* package/reader/
EPUBCheck receipts follow suite make-epub; older102/101/99/canonical receipts stay
historical. Inspect default TCP EOF/private descriptor retirement, not Connection
headers or observer mode alone. Prior link target index SHA and README121/368/
non-overwriting current-report instructions were separately reproduced/repaired.
No other required gap found by author; independently challenge that decision,
classify broader unclaimed assurance and review final exact HEAD before delivery.

## Contract

Review the current checked-out commit; record its full hash and clean/dirty state.
Verify a complete Zig **0.17.0** edition against immutable upstream
`c9ee2424af02e4c1e4765088580107d5e17b826e`. Preserve the original teaching
purposes, attribution, MIT text, illustrations and chapter order. No upstream PR
or release is requested. Push only the personal fork after acceptance/final audit.

| User requirement | Read surfaces | Decision required |
|---|---|---|
| Fork + local clone | Git remotes; `fork-verification.json`; current remote receipt in `reference-execution-verification.json` | Personal fork/parent/path exact; final conversion still not delivered |
| Enumerate every C/io_uring line/block | `source-inventory.json`, `tools/inventory.py`, `tests/test_inventory.py`; original Git trees | Independent completeness of 3,618 lines/128 blocks, including implicit literals; selectors/text exact |
| Update all references | `chapter-map.json`, `reference-map.json`, manuscript, `tools/reference_docs.py` | All 26 original chapters/76 original symbols/99 bindings; native operand/return/flag/lifetime meanings, not signature matching alone |
| Recreate every example | `build.zig`; all 25 executable sources/shared helpers; public CLI/TCP tests; original blocks | Each original runnable/static teaching purpose preserved or explicitly corrected; native implementations/no foreign imports |
| Publication/preservation | `verify_epub.py`, current EPUB, reader checker, licence/images, metadata/links | 27 chapters/121 literals/368 resolved paragraphs; exact images/licence; structural/fidelity gates do not establish semantics or device acceptance |

Start at `audit.md`, then use the 16 implicit/37 tutorial/75 reference block notes
and 567 outside-block line notes to compare **all** original purposes. These are
author indexes, not accepted dispositions. Read source bodies, not cached outlines.

## Focus

- Raw SQ/CQ publication, mapping/unwind/FD ownership; automatic vs manual CQ
  acknowledgement; queue capacities and counter arithmetic.
- Mutable buffers, registered files/buffers, selection/EOF, partial I/O, tagged
  target/canceler/timer lifetimes, signal masks and before-exit cleanup.
- HTTP root confinement/request state/short SEND/reset isolation; socket/address/
  vector/control ownership in CONNECT/ACCEPT/messages/poll/epoll/SPLICE.
- Submission counts vs completion counts; RWF/dependency/message/buffer-index
  namespaces; SDK-only helpers and exact native ABI fields.
- Four repaired map rows: NOP, READ_FIXED, WRITE_FIXED and RECV were falsely
  construction-only. Inspect `reference-execution-verification.json`; confirm
  executing primaries and iovec-metadata vs byte-storage lifetime independently.
  Check the arithmetic amendment:the poem is71 bytes (36/35), not68. Initial
  author fixture/core and excluded bytecode-cache replay remain in evidence.
- Probe header/op bindings now target the actual probe consumer, not an unused
  constructor catalog. Inspect `probe-type-verification.json`; independently
  check fixed-capacity value ownership, native enum fields, both lookup bounds
  and bit0-only support. Generic type-primary rows receive author comparison below, not independent acceptance.
- RECV/SEND author-note rows now separate request inputs from response bodies
  and state the actual positive-short body SEND evidence. Inspect
  `http-note-verification.json`; index freshness alone does not accept meanings
  or forced signal/header/vector/fragment-CQE claims. No native/book-source change.
- All22 type rows now have body-level author comparison;19 generic scopes are
  specific. Read `type-binding-audit.md`/`type-binding-verification.json`; inspect
  auto-layout owners versus extern records, kernel8-byte versus libc masks,
  signed/bit-pattern offsets, mode-field widths, nested loans and address-length
  direction. Reflection amendment preserves initial evidence;13 final producer
  kills replace initial13. Neither reflection nor this handoff is independent
  all-original-purpose acceptance; permissions/umask effects stay unclaimed.

## Verification and evidence

Use exact installed Zig 0.17.0 and the locked `.venv`; Hypothesis requires its
Python. Run commands in the repository root. Prerequisites fail, not skip.

```console
zig version
zig fmt --check build.zig examples tests/fixtures/vm-mount.zig
zig build --summary all
python3 tools/inventory.py --check
python3 tools/reference_map.py --check
python3 tools/reference_docs.py --check
python3 tools/check_line_dispositions.py --check
LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
make html SPHINXOPTS='-E -n -W --keep-going'
make epub SPHINXOPTS='-E -n -W --keep-going'
.venv/bin/python tools/verify_epub.py
.venv/bin/python tools/check_reader_layout.py
```

Inspect current command logs/receipts and source pins, then rerun selected adverse
cases independently. `test-verification.json` attributes 16 generated properties;
repeated/finite command flows are not PBT. Historical mutant counts/screenshots
remain historical. Check EPUBCheck 5.2.1 separately; browser reflow is not Supernote,
pagination or font-override acceptance. Use only owned generated inputs/devices,
loopback peers and bounded process groups; no destructive host storage tests.

Return findings with original selector, current path/symbol, severity, exact
reproduction/evidence and required correction. Separate acceptance-critical gaps
from unclaimed broader kernel/protocol/race assurances. Record inspected coverage
and remaining uncertainty. No completion attestation while any required purpose,
review finding, final gate or personal-fork delivery remains unresolved.
