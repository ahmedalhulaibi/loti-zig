# HTTP heap retirement — direct review

Native repair80631c8 unchanged. New public CLI/syscall/mapping regression extends
tests/test_http_lifecycle.py;all prior methods AST-identical. No subagents,
mutation execution,new property,independent-review or protection claim.

## Four owned scenarios

4MiB patterned regular file;exact0.17 SDK emits SQE/CQE field offsets/operation
values. Strace setup exposes actual shared-ring offsets. Read only owned descendant
/proc/PID/mem,not another user's memory. Decoder scope:x86_64/little-endian/no SQ
or CQ counter/physical wrap;prerequisite failure is not a skip.

| Scenario | Pre-error observation | Before mapping release |
|---|---|---|
| READ enter EAGAIN | Shared SQ has published READ tag1/4MiB;kernel has not consumed it | Retried submit,target READ terminal CQE consumed;whole heap bytes equal input;SQ/CQ empty;cancel receipt and ACCEPT -125 separately observed. |
| Body SEND enter EAGAIN | Shared SQ has published SEND tag1/4MiB | Actual positive-short terminal SEND;whole original heap bytes retained;target consumed before release,not submission count alone. |
| Repeated READ enter EAGAIN | Published READ remains unconsumed after >=2 failures | Same buffer bytes/mapping/SQ entry and8 owned FDs remain live. Owned harness terminates/reaps after observation;this is retained ownership,not successful shutdown. |
| Consumed blocked body SEND | SQ head/tail8,CQ head/tail6;ACCEPT and SEND outstanding. Peer SO_RCVBUF4096;two positive-short sends precede blocked slice | Distinct cancel receipts and target ACCEPT/SEND -125;all10 CQEs consumed,whole4MiB remains byte-identical before unmap. |

Final values are observed checkpoint-specific,not portable performance constants.
Target lookup starts at the operand's observed CQ cursor,not an earlier CQE with
the same reused tag. Stable final snapshot checked twice. Cancellation receipt
alone cannot satisfy target retirement. Oracle uses independent fixture bytes,
kernel queues/FDs and literal terminal outcomes;does not call native ledger helpers.

Fixture:http-retirement-contracts.json. Helpers:http_retirement_abi.zig and
http_retirement_observer.py under tests/fixtures. One table-driven method/four
cases,not PBT or a complete12-scenario lifecycle model. Source/API exposure is
disclosed;directly authored qualification,not independent test authorship.

## Qualification limits / retained failures

Owned evidence:_build/verification/http-heap-retirement/ and http-retirement-*.
Initial EIO probe timed out:SDK unexpectedErrno wrote to the filled stderr before
unwind. Changed fault to SDK-mapped EAGAIN/SystemResources,not a native bug fix.
Initial /proc/syscall filter missed injected calls;explicit queue snapshots replaced
it. Python optional-type findings fixed. First READ pilot's captured helper followed
two minor scanner/type edits;formal runs pin their actual helpers,not that capture.
Consumed-SEND pilots retain SO.RCVBUF typo,wrong submit ordinal8 and never-reached
ordinal10/deadline. Correct wait ordinal9 is verified by whole injected-enter shape.
Harness failures/deadlines are not native reds or mutation kills. Unconditional
process-group termination/reaping and pipe/peer/memory-FD release precede reporting.
Lost polling handles recovered from complete logs/exit files,not silently promoted.
Initial capture included its unfinished log hash;receipt/helper retained,log and
receipt excluded from self-hashing. No native/runtime replay needed for this fix.

## Final gates

Receipt:http-heap-retirement-verification.json. Targeted1/3 cases21.750s;affected
6 methods/4 heap cases31.366s;full109/201.611s before moving identical wire/name
inputs into fixture;final109/200.682s/0 failures-errors-skips,16 properties
configured400. Every prior class method AST-identical;232 source pins extend229
with3 fixtures,only oldtest_http_lifecycle.py changes. All30 native bodies,
README/manuscripts/dependencies and canonical128 targets unchanged.
Exact0.17/formatter/build51/51(25 cached),fresh private HTTP/ABI compile;four
CLIs3618/128/567,76/99,13 pass. Strict HTML/final EPUB63f6aee8;27 chapters/121
literals/368 paragraphs;81 reflows/0 violations;EPUBCheck0. All changed tracked
paths probed;initial unconfirmed helper recheck later confirmed clean.
Previous a735fe85 ZIP was not saved before suite rebuild;no prior28-XHTML-byte
comparison claimed. Current whole fidelity/preservation/reader gates replayed.

These finite probes establish actual target acknowledgment plus accessible heap
bytes before release,including a kernel-pending cancelled SEND. They do not prove
all kernels/architectures/concurrency,unbounded cleanup progress,physical OOM,
arbitrary control failure or a general no-UAF theorem. Remaining final source/
original-purpose review and personal-fork delivery are separate gates.
