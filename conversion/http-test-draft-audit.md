# HTTP regression draft audit — BLOCK: not seal-ready

Parent read-only audit of source1606bf6. Workflow077cdd6b/child8b04aa6b failed after
1200000ms;requested author report missing. Two additions remain in its isolated
worktree,not adopted. Full identifiers/receipts in http-test-draft-audit.json.

## Verified scope

- Original test write:transcript75,2026-10-11T23:48:41.879Z. Exact body hash equals
  frozen pre-exposure e976e0d1. Captured native body first appears at record86,
  23:49:14.162Z. Spec-first authorship confirmed;not fully unexposed independence.
- Five default-control assertEqual calls and one fatal assertEqual call have
  identical complete ASTs before/after exposure. Fixture45974538 unchanged.
  Type/trace-PID,owned-census stability and injection-suffix changes are preserved
  separately. Unchanged literal assertions do not prove unchanged harness semantics.
- Suite03:two methods/9.571s/default control passes;three fatal subtests fail at
  UNRELEASED_SUCCESSFUL_ACCEPT_PRE_EXIT,not harness errors. Private checkpoints
  show stdio plus owned late socket8;tuple/inode identities differ per process.
  Idle peer EOF;late peer stays open. After stderr release:exit1/WriteFailed,
  no forced termination. Earlier wchan/fixture/type/trace errors retained separately.
- Native source30 hashes match main;compiled privately with exact0.17.0. Source
  provenance also hashes historical mutants/build/reflection;not all dependencies
  or a test seal. No captured child Bash git-add call;final index attribution open.

## Required qualification before sealing

**Green-path observability gap:** test lines461/accepted245–256 require a *currently
live* late descriptor before the cleanup checkpoint. Valid schedule:ACCEPT installs
FD → correct cleanup closes it → first10ms census poll sees no FD/peer EOF. The
desired contract holds,but accepted() never returns and times out before the oracle.
This is a static observer counterexample,not an executed corrected implementation.
Three reds do not establish a usable green acceptance path. Independent author must
handle already-closed accepted results or distinguish never-accepted backlog
cancellation,and demonstrate the conforming observation path without SUT-oracle reuse.

**Failure-path cleanup risk:** close319–369 collects/decodes stdout before later
termination/reap/FD-release steps,without an unconditional cleanup-finally over
those steps. Collection errors can bypass them. No malformed-output/orphan probe
demonstrated;validate this path before claiming cleanup on every harness failure.

Protected tests remain absent;same-owner ACL chmod bypass remains proven. FD draft
does not cover pending-memory retirement,unpublished/copy-undispatched/cancel-failure
states or all12 scenarios. No native repair/accepted design. Also settle the local
red-commit policy conflict:testing.md requests passing BUG-as-is then flipped green;
workflow.md requests a failing red commit. No sealed-test expectation flip authorized.

## Evidence / boundaries

Frozen capture:`_build/verification/http-test-draft-timeout.oAPsCWVx/`;audit helper,
receipt/log:`_build/verification/http-test-draft-audit.UmIs6z6t/`. All3239 captured
file digests checked;exact transcript/body/fixture and fatal checkpoint fields read.
Both classes/all helpers read directly;stale graph989c85c0/enclosing2f4b15a7 used
only for syntax outlines. One grouped exposure read truncated;small ordering/hash
and patch/source reads completed separately. Six constitution files read completely.
Six-path LSP:five clean;helper's seven fail-closed JSON throws and intentional
boolean-identity check marked false-positive. No suppressions/behavior changes.

All226 prior selected edition inputs and archive5739833e unchanged. No draft edit,
native execution,formal-suite/property/mutation addition,full/cold/publication replay,
new reviewer,fallback protocol,push or goal completion. Next:same-role author
qualification from this contract finding;then owner-enforced protection and the
remaining lifecycle tests before implementation. Overall acceptance still incomplete.
