# ACCEPT / fatal teardown — author findings

Source `3934e60`;native/test/fixture/manuscript unchanged. Receipt:
`accept-teardown-reproduction.json`;owned logs/helpers:
`_build/verification/accept-teardown.T5rwCjyB/`.226 selected inputs unchanged.

## Actual HTTP defect

Two runs of the previously source-built exact0.17 HTTP binary. Fourth observer
stdout writev gets EIO after an owned1s delay;late loopback peer connects while
output is delayed. Full stderr pipe holds fatal error reporting before exit.
Trace closes ring5,client6-7,listener4,root3. Actual live descriptor census then
contains0,1,2 **and socket8**,mapped to the late peer by owned TCP tuple/inode.
Late peer has no EOF during50ms guard. Release stderr:exact `error: WriteFailed`,
exit1,then peer EOF. This is a pre-exit cleanup omission;process exit eventually
closes the descriptor. No post-exit leak,use-after-free or corruption demonstrated.

Earlier close8 is the loaded file;accepted socket reuses8 later. Descriptor
number alone is not identity. HTTP main copies one CQE at a time;no batch-tail
defect asserted. Exact CQE-publication/FD-installation moment was not observed.

## Candidate barrier is insufficient by itself

Private native20 processes/40 ACCEPT CQEs;one additional traced process excluded
from totals. Unread CQ and copied/acknowledged CQ modes both retain accepted FD
after synchronous ALL|ANY returns0,ring deinit and listener close. Byte90 still
crosses the connection;explicit accepted close gives peer EOF. Complete reports
match;trace independently shows syscalls/effects. Cancellation is not ownership
handling for successful resource-producing CQEs.

Initial helper defer syntax failure retained. Initial HTTP checkpoint wrongly
required FD installation while syscall-entry delay stopped the task;corrected
checkpoint observes post-cleanup/pre-exit descriptors. Neither is a mutation kill.

## Repair contract — verifier must author/seal tests

| State | Required boundary effect / killed defect |
|---|---|
| Prepared,not published | Stop producing requests;do not submit during unwind. Kills cleanup that publishes stale operands. |
| Pending RECV/ACCEPT/heap READ/SEND | Keep operands live through relevant retirement;close/free only afterward. Kills close-only/early-free cleanup. |
| Completed ACCEPT,unread or copied/undispatched | Claim/close returned FD independently of cancel result;whole pre-exit census/peer EOF. Kills cancel-only/ready-CQE discard/process-exit cleanup. |
| Cancel failure/timeout/noncancelable target | Do not treat failure/zero count as universal retirement or resume unsafe release;retain ownership until defensible completion. Kills optimistic fallback. |

Scenarios must include original fatal stdout path and default mode where applicable;
normal request/error behavior unchanged. Tests must observe effects before exit,
not self-reported closure. These are author requirements,not independently authored
tests/ACL seals or an accepted implementation design.

Existing read-only reviewer cannot write/run these tests. Need owner approval for
runtime-capable independent verifier/qualifying alternative before design-heavy
repair. No new reviewer/profile bypass/native fix/self-acceptance.
Scope diagnosis: HTTP producer/cleanup/CQE ownership are one lifecycle boundary;
change plan must account for memory retirement and successful descriptor results.

Last full103/16×400/cold25 remains44d9b32;affected3/publication3934e60/04c4e128
unchanged;292 kills unchanged. No new formal test/property/mutation/full-suite/
publication replay,dependency install,host change,push,PR,release or completion.
All6 constitution files read untruncated;Fabric unavailable/stale graph disclosed;
exact source/SDK/runtime used. Completeness/independent acceptance/delivery open.

Diagnostics:fixed possibly-unbound census in current helper;observed runtime
helper/initial capture/receipt preserved. Diagnostic-only change not transport
replayed. Final capture explicitly allows only owned evidence files;all226 pins
checked. Exact captured `ACCES`,kernel procfs descriptor parsing and `is True`
boolean type checks marked false-positive;no inline suppression. Final capture
excludes its log/receipt;artifact hashes verified after exit.
