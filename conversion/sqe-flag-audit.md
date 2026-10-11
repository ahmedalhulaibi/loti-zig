# SQE flag scopes — author audit

Baseline `44d9b32`; reproduction `539cf32`. Native/tests/fixtures unchanged.
`sqe-flag-reproduction.json` stores old source/package paragraphs, complete
helper/model, observed rows and failed discovery. `sqe-flag-verification.json`
stores current gates and16 live supplemental slices.
Scope diagnosis: tutorial and syscall reference duplicate the same kernel
contract. Both presentation surfaces need correction;native module boundaries
and test/fixture expectations stay unchanged. No ACL-seal claim.

## Findings / repair

- LINK chains end at a submission boundary, not only at a clear LINK bit.
  A flagged pending READ in the first submission does not delay the second
  submission's WRITE. Clarified raw syscall reference and linking tutorial.
- HARDLINK protects operation results, not SQE validation/initialization.
  Unsupported opcode255 yields parent−22/tail−125 even when submit returns2.
  Short READ1/2, expired TIMEOUT−62 and badFD READ−9 retain the hardlinked tail;
  soft links cancel it. Error number alone does not identify failure stage.
  Both chapters now name initialization and distinguish positive API return.
- DRAIN prose was already correct. Two private-pipe plans observe ordering
  before and after the drained READ; no-flag controls expose the early WRITE.

## Evidence / limits

Exact0.17.0/native SDK, ordinary rings/current Linux7.2.3.20 processes×19 finite
plans:840 tagged CQEs,460 submission calls,220 actual1ms completion guards.
Extra traced process:19 setups/23 submissions/11 guards; not added to those totals.
Full CQE/poison/readiness/witness rows match the scoped model. These are finite
author checks, not PBT, independent acceptance, concurrency or cross-kernel proof.

Initial nonblocking linked READ returned−11; switched the owned boundary source
to blocking mode, retaining failed output/helper. Initial badFD-as-initialization
prediction failed; kept mismatch, then added unsupported opcode. Unlinked invalid
opcode initially consumes only one SQE; remaining WRITE needs a second submit.
Compiler/formatter/model failures are retained, not native edition defects/kills.

Four source CLIs;affected6 tests/10.046s/zero failures-errors-skips;fresh strict
HTML/EPUB;four whole corrected packaged paragraphs;27 chapters/121 literals/
368 paragraphs;81 reflows/zero violations;EPUBCheck5.2.1 zero messages. Only
two manuscript hashes differ within prior226 selected pins. Canonical replay
changes only those two target digests;3618/128/567 and note selectors stay exact.
Historical supplement target `ee0b124` is not repinned;four old slices differ;
fresh16 slices are in the current receipt. Selected pins are not dependency seals.
Supported changed paths have no diagnostics. RST has no configured LSP;strict
Sphinx checks it. Canonical index exceeds the5000-line LSP budget;CLI replay
checks its syntax/structure/current hashes. No inline suppression.

Last full103/16×400 and uncached25 build remain `44d9b32` consumer evidence,
not replayed after these prose edits. No test/property/kill inflation;292 kills
unchanged. Independent BLOCK, original completeness/meaning, teardown assurance
and final fork delivery remain open. No reviewer, push, PR, release or completion.
