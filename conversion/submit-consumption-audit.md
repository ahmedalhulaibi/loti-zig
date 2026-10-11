# CONNECT metadata lifetime — author correction

Base `6c5016c`; reproduction `b80710e`. Objective/independent acceptance remain
**incomplete**. Native examples/tests/fixtures are unchanged.

## Finding and correction

The CONNECT paragraph said SUBMIT_STABLE input storage was needed through
successful submission only and cited a liburing helper. API-return/consumption
are not interchangeable with SQPOLL. The example itself retains its address
through the tagged CQE; no native premature-free defect was reproduced.

`submit-consumption-reproduction.json` retains the whole old source/package
paragraph and exact0.17.0 owned probe. Both rings advertise SUBMIT_STABLE:
ordinary mode has zero pending observations; SQPOLL has256, each with positive
submit return and unconsumed SQEs. First return64/pending64. Each mode validates
16384 full-tag/result0/flags0 CQEs, no duplicates, empty SQ/CQ between batches.
This is finite NOP consumption evidence, not CONNECT released-memory effects,
PBT or exhaustive kernel/race assurance.

`ref-zig/submission.rst` now specifies kernel consumption, rejects SQPOLL return
as an acknowledgment, retains the peer address until its CQE, and links the
native kernel feature chapter instead of the liburing helper. Authority:
local `man-qmd/build/docs/liburing/man/io_uring_setup.2.txt`, heading
`IORING_FEAT_SUBMIT_STABLE`; exact SDK `submit`, `submit_and_wait`, `sq_ready`.

## Affected gates

`submit-consumption-verification.json`: three selected publication/README tests
pass6.814s; fresh strict HTML/EPUB, exact whole lifetime paragraph, native internal
link,121 literals/368 paragraphs,81 reflows/zero violations, EPUBCheck5.2.1 zero
messages. Only submission changes in the selected226 pins; canonical index
refresh changes its target SHA only. All notes/selectors/3618/128/567 remain exact.
Last full103/16×400 is the earlier6c5016c checkpoint; not replayed/promoted here.
RST LSP and oversized canonical-index limits remain; strict/structural checks
are separate.292 historical kills unchanged; no new campaign/property.

HTTP source defers ring teardown before client release; no verified ordering
defect found. That inspection is not all-pending-I/O memory-safety proof.
Owned helper's rejected array-repeat draft/log remain; not a kill. External HTTP/
HTTPS manual-page probes timed out; no availability or HTTPS repair claimed.
Logs/source/native output stay in `_build/verification/submit-consumption.RYEh7Fh8/`.

No new reviewer or push. Complete original-purpose/line coverage acceptance,
approved independent verification, final prompt audit and accepted delivery
remain open. Author counterexamples and green gates cannot waive these.
