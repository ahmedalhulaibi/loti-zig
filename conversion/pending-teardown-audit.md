# Pending-I/O teardown — author exploration

Source `021e98e`;no native/manuscript/test/fixture edit.226 selected edition
inputs remain exact. Evidence: `pending-teardown-reproduction.json`;owned
helpers/logs under `_build/verification/pending-teardown.NdwGSvQN/`.

## Established

- HTTP baseline serves exact146-byte response. Fourth observer stdout `writev`
  injected with EIO propagates `WriteFailed` through `emit`→`complete`→`main`.
  Idle peer remains open/sends no bytes. Before trigger, native enter consumes2
  SQEs:idle RECV/next ACCEPT, as prepared by the inspected source. Fatal wire is
  exact116-byte header/no body;exit1. Reproduced with existing binary and a fresh
  isolated exact0.17 source build. This is a real fatal-unwind path,not a claim
  of observed use-after-free or late buffer writes.
- Fatal trace closes ring5,client6,client7,listener4,root3 before error output.
  SDK `deinit` unmaps CQ/SQ and closes FD;`Client.release` closes FDs,frees owned
  heap storage,resets slot. No explicit cancellation/retirement barrier exists
  in this path. LIFO ring-before-client order does not establish IO retirement.
- Exact SDK has64-byte `io_uring_sync_cancel_reg`,REGISTER_SYNC_CANCEL and
  ALL|ANY. Two finite pipe modes,each repeated once under strace:12 validated
  CQEs total. Closing reader FDs does not retire their outstanding READs.
  Unknown high cancel flag returns−22;another actual1ms guard still times out.
  Valid synchronous cancellation returns2;both targets produce−125/flags0;
  buffers remain all165;empty queues;repeated ALL|ANY returns0,not−ENOENT.

## Authority / unresolved scope

Local manuals: `man-qmd/build/docs/liburing/man/io_uring_cancelation.7.txt`,
**Shutdown cancelation / Synchronous cancelation**;`io_uring_register_sync_cancel.3.txt`,
**Description / Return value**;`io_uring_queue_exit.3.txt`,**Description**.
Closing a ring cancels requests,but explicit retirement is needed before
dependent resource release. Cancellation failure/timeout is not retirement.
Private-pipe success does not establish all HTTP READ/SEND/hardware/race paths.
No forced OOM,stalled heap-backed SEND/READ,allocator reuse or corruption proved.

## Required next step

Independent verifier must specify/test fatal cleanup before implementation:
pending RECV/ACCEPT plus heap-backed READ/SEND;prepared versus published SQEs;
completed-but-unhandled successful ACCEPT owns an FD;noncancelable completion;
unsupported cancellation/timeout cannot resume unsafe release or report success.
Stop producing requests,retain operands,retire relevant CQEs,then release storage.
Synchronous cancellation is a candidate,not an accepted universal fix.

Workflow requires verifier-authored sealed tests and prohibits self-acceptance.
Owner prefers direct review;builtin reviewer is read-only. No profile/tool
bypass or new reviewer. Need owner approval for a runtime-capable independent
verifier or an explicit qualifying alternative before this design-heavy repair.

All6 constitution files read untruncated;Fabric unavailable/cached graph stale;
syntax/source reads used. No test/property/kill inflation:103/16×400 and292 kills
stay historical. No full/publication replay,dependency install,host mutation,
push,PR,release or completion. Fatal retirement/completeness/acceptance remain open.
Diagnostics:preserve exact SDK `ACCES` and original manual spellings;marked
false positives. Capture JSON intentionally fails closed before receipt creation;
its unchecked-throw rule also marked false-positive. No inline suppression.
Initial capture incorrectly hashed its own stdout log before final print.
One stale digest was reproduced;initial receipt/script/mismatch retained in
owned output. Final capture excludes its own receipt/log;all listed artifact
hashes checked after exit. This was an evidence-producer defect,not a native kill.
