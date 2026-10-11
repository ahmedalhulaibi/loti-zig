# Submission reader precision — author scope

Base `b4047f6`; baseline evidence commit `29f01e8`. Independent acceptance remains
**BLOCK**. No native/test/fixture edit, new property, mutation campaign or push.

## Decisions

- `ref-zig/submission.rst:197`: say **payload RECVMSG**, not first RECVMSG.
  Full native report equals the hand-pinned literal. The first receive is tag1,
  DONTWAIT64, result−11; payload receive tag3 uses1073741920
  (DONTWAIT|TRUNC|CMSG_CLOEXEC). Message/control/vector lifetimes are unchanged.
- `ref-zig/sqe.rst:37`: say **unsubmitted33-constructor reference**, not executed
  reference. Program execution invokes constructors; it does not execute that
  incompatible operation batch. Owned strace records one setup, zero enter;
  all33 opcode/tag records and both prior selected public tests pass.
- These are reader-scope clarifications, not reproduced native defects. Exact
  SDK `prep_rw`, `prep_recvmsg`, `prep_connect`, `sq_ready`, `submit_and_wait`
  bodies were read. Earlier combined chapter reads had truncation; this pass
  does not attest exhaustive original/current chapter inspection.

## Verification

`submission-reader-before.json` retains complete old source/package paragraphs
and native observations. `submission-reader-verification.json` records fresh
post-edit gates; ignored logs/artifacts stay under
`_build/verification/submission-reader.XI3aSIDZ/`.

- Zig0.17.0; formatter;51/51 cached build steps; inventory/map/declaration/index
  CLIs pass. Canonical index regenerated after the edits: only two target SHA
  fields changed;3618/128/567 and all notes/selectors remain exact.
- Full103/zero failures-errors-skips/172.323s;16 properties×400 valid cases.
  Strict HTML/EPUB;121 literals/368 paragraphs; exact licence/assets/order/links;
  whole two corrected packaged paragraphs;81 reflows/zero violations;
  EPUBCheck5.2.1 zero messages. Current archive SHA is in the new receipt.
- Historical203 suite pins include only4/27 manuscript files. Only submission
  changes inside that set; SQE is outside it. The initial helper's two-pin-change
  assumption failed before receipt creation. Fresh post-gate27-chapter snapshots
  extend the selected union to226 files; not pre/post seals, whole dependency
  coverage or independent acceptance. Historical receipts are not repinned.
- RST LSP unsupported; canonical index exceeds its5000-line budget. Strict
  Sphinx/structural checks cover those supported surfaces, not code semantics.
  Lost suite polling handle resolved from completed log/receipt/current hashes.

292 historical bounded kills remain unchanged. Complete meaning/completeness
acceptance, final prompt audit and accepted personal-fork delivery remain open.
