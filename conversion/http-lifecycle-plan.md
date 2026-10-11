# HTTP lifecycle repair — proposed contract, not accepted design

Baseline932caf4;`projects/http-lifecycle/{glossary.json,scenarios.js}`: domain
scaffolding,not native examples/tests/seals. Twelve scenarios;five entities,
four value objects,eight events. Verifier must author independent executable
tests from the spec before any implementation. No new reviewer/profile override.

## Source facts

- webserver.main333–385:flags0,64-entry request,32 stable slots;copy one CQE before
  fallible complete. Fatal submit errors return;CQ-wait SignalInterrupt retries.
- complete243–305 queues new work. It cannot be reused unchanged as a shutdown
  drain. ACCEPT saves fd before sendBuffer;an idle slot can already own a descriptor.
- queue128–153 can fail after reserving/preparing SEND. Phase is not publication
  evidence. release76–81 closes/frees/resets without request-retirement tracking.
- Exact0.17 SDK IoUring.get_sqe139–148 reserves local tail. flush_sq221–236 publishes
  shared SQ tail before submit_and_wait164–174 calls enter. Enter error does not
  imply unpublished. copy_cqe310–316 consumes once;deinit123–130 unmaps/closes.
- cancel985–995 queues a separately tagged control request;it is not target CQE
  acknowledgment. Prior40-CQE ACCEPT/private pending-read effects remain scoped
  evidence;no new lifetime/cancellation runtime probe here.

## State / command boundary

RequestLease publication,completion disposition and retirement are separate.
ResourceLease ownership is independent of HTTP phase and CQ advancement. ControlLease
tracks admission/retirement separately;async tags must not collide with app0–32.

| Command | Required event/effect |
|---|---|
| BeginCleanup | CleanupStarted;stop producer/rearm;keep pending operands live |
| AbandonUnpublished | Prove no shared publication;TargetRetired without submitting stale application SQE |
| ObserveTerminal | Correlate target/generation;consume once;TargetRetired before fallible callbacks |
| ClaimAccept | Every nonnegative result,including FD0,gets explicit ResourceLease;copied result retained until claimed |
| ReleaseResource | All retaining requests retired;close/free exactly once;phase never erases ownership |
| SettleCleanup | No pending/unknown target,unclaimed accepted FD or required unretired control;then ordinary defers may release |
| StallCleanup | Preserve ownership/operands/result access;do not return through invalidating defers;escalate |

## Candidate retirement mechanisms — no selection yet

| Option | Advantage | Unresolved/rejected condition |
|---|---|---|
| Async per-tag cancel plus target/result drain | Native SDK preparer;individual target correlation | SQ admission,unpublished SQE abandonment,control namespace,noncancelable/failed/timeout paths must be independently tested |
| Synchronous register cancellation plus target/result drain | Out-of-band admission need not flush prepared application SQEs | Actual availability/result/timeout handling;ALL/ANY compatibility;cancel count does not claim ready ACCEPT FD or acknowledge CQ |
| Ring/FD close then application release | Existing simple defer shape | Rejected as retirement/ownership mechanism:actual late accepted FD survives;closing source FDs alone does not retire pending reads |

SDK exposes no dedicated abandon-unpublished helper in inspected API. Do not
guess rollback by assigning counters;any chosen approach must prove shared/local
publication boundaries. A successful control outcome never authorizes skipping
ready or copied-undispatched resource results.

Conservative one-shot bound:at most32 client targets+1 ACCEPT;up to33 async controls.
33+33=66 exceeds requested SQ64. This is admission math,not observed occupancy or
a performance guarantee;controllers must account for actual remaining capacity.
No distributed/storage topology or throughput target introduced;simrs load
simulation is not applicable to this finite lifecycle decision. No NFR acceptance.

## Unresolved acceptance input

Independently authored protected tests must cover all12 scenarios and the actual
observer failure before process exit. FD census/peer EOF are ownership observations,
not heap-retirement proof. Specify how real pending RECV/heap READ/SEND operand use
is observed;do not accept self-reports or duplicated implementation as the oracle.
Retirement failure/timeout policy cannot silently become optimistic free/return.
Human-controlled sealing/runtime capability and independent completeness/meaning
acceptance remain missing. Existing warning5739833e archive/code untouched.

Local manual directory:`/home/ahmed/workspace/va/man-qmd/build/docs/liburing/man/`.
`io_uring_register_sync_cancel.3.txt` (DESCRIPTION/RETURN VALUE) and
`io_uring_prep_cancel.3.txt` (ERRORS/NOTES). Native SDK and
actual effects override stale/scope-limited manuals. ALL/ANY version restrictions
in the latter are compatibility inputs,not actual older-kernel execution evidence.

## Tooling limits

Initial scengen shim lacked active Go version;use already installed absolute binary,
no global config/install. Version reports unknown,built from source;binary/template
digests captured. CLI list --format json emitted tables;preserve them as table text,
not JSON success. Explicit inspected Markdown templates render twice from fresh
parses;whole output compared to model data. This is syntax/render fidelity,not
independent spec acceptance or executable regression tests. No test-skeleton generated.

Initial author render checker omitted one template-final newline;failed helper/log
preserved,checker corrected without changing model data. Active4-path diagnostics:
actual commit substring caf and two intentional fail-closed JSON throws marked
false-positive;no suppression. Syntax/render success is not lifecycle acceptance.
