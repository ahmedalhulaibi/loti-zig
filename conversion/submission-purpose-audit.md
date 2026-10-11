# Submission and SQE purpose comparison

Author comparison, **not independent acceptance**. Read complete original
`ref-liburing/submission.rst` and `sqe.rst` at
`c9ee2424af02e4c1e4765088580107d5e17b826e`, all 32 inventory blocks and
their current `ref-zig/` chapters/includes. Inspect native constructor/preparer
bodies and actual consumers, not signatures alone. No required conversion gap
found in this subset. Original declarations are not 30 standalone applications.

S selects original `ref-liburing/submission.rst`; Q selects `sqe.rst`.

| ID | Preserved purpose / necessary correction | Consumer / evidence boundary |
|---|---|---|
| S:12 | Acquire, prepare READV, tag, submit | cat combines acquisition/preparation; copied CQE checks tag/result and initialized bytes before next iteration |
| S:32 | Vacant SQE and queue-full result | SDK get_sqe returns slot/error, not NULL; existing eight-slot/ninth-rejection contract preserves tail/count |
| S:51 | Request correlation | Constructor u64 tag or direct user_data after prep; no pointer ownership/lifetime transfer |
| S:62 | SQE bitmap setter | u8 assignment replaces; |= preserves constructor bits; operation flags instead occupy rw_flags |
| S:73 | Submit batches | Ordinary return counts submissions, not CQEs; SQPOLL may return higher/lower/zero relative to current-call submissions |
| S:89 | Submit plus wait threshold | submit_and_wait publishes and requests threshold; tagged CQEs still establish results and require consumption |
| S:114 | NOP queue experiment | Real NOP batches/identity; no bytes or efficiency benchmark claim |
| S:127 | Scalar read into mutable storage | .buffer slice replaces pointer/count; copy/raw bytes and current/absolute offsets remain distinct |
| S:148 | Scalar write from const storage | cp/link execute writes; separate controlled-short mode tests completed-byte progress, not WRITEV shorts |
| S:169 | Scatter read and vector count | .iovecs prepares READV; cat/reference-files use stable vectors and separately initialized byte ranges |
| S:190 | Registered-buffer read | fixed-buffers uses registered range and buffer index, not a fixed-file slot or implicit registration |
| S:213 | Gather write | writev takes const iovec slice; reference-files observes exact bytes/reopen hash; vector count is not byte count |
| S:234 | Registered-buffer write | Correct original mistaken read/FD/buffer prose; four 512-byte registrations, 36/35-byte writes and readbacks, 71 total bytes |
| S:259 | Full/data-only synchronization and ordering | reference-files completes writes/allocation before both FSYNC modes; success is not crash/media durability |
| S:283 | Close process descriptor | Successful CLOSE CQE retires ownership; F_GETFD observes EBADF before exit; no double-close |
| S:300 | Relative directory/path open, flags, mode | Sentinel path/native O; reference-files opens input/reopened output and passes mode0600 to exclusive output OPENAT; result is an owned FD, permission/umask effects unclaimed |
| S:321 | OpenHow-controlled resolution | Native three-u64 OpenHow; raw OPENAT2 returns FD used for independently observed prefix; HTTP confinement is separate |
| S:341 | Allocate/change file space by mode/range | u64 offset/length, i32 mode; reference-files mode0 adds exact4096 zero tail; other modes/filesystems unclaimed |
| S:361 | Path/lookup flags, mask and output metadata | Stable native Statx output; actual TYPE/SIZE bits and sizes checked, not all fields/path policies |
| S:380 | File range/access-pattern advice | Explicit FADVISE SQE, u32 ABI length; NORMAL success CQE is not cache/performance evidence |
| S:399 | Memory range/advice | Explicit MADVISE SQE; owned page DONTNEED zeroing, not FADVISE's effect or all advice modes |
| S:418 | Pipe transfer and independent input/output offsets | Correct original synchronous pointer/NULL prose to value/all-ones offsets; reference-splice observes actual short progress, bytes/cursors and failures |
| S:442 | Socket receive via message/vector/control storage | Native msghdr and nested loans; UNIX datagram truncation/empty records/rights observed, not all TCP/UDP behavior |
| S:461 | Message send | Native const header/vector type; actual socketpair SENDMSG and separately owned received FD; sender's numeric FD is not the right |
| S:473 | Scalar socket receive and flags | RecvBuffer, not original erroneous msghdr description; HTTP initialized bytes/TCP EOF differ from empty datagrams; binary/empty fixtures are response bodies |
| S:493 | Scalar socket send and flags | Const remaining slice/NOSIGNAL; HTTP actual positive-short body SEND, exact wire/reset/recovery; no forced header/vector short or SIGPIPE-delivery proof |
| S:505 | Accept listener, peer output/value-result length and new FD | Native addr/off pointer pair; initialized capacity, poison/prefix/full length, independent endpoints and actual FD flags/retirement |
| S:525 | Connect client to input peer/value length | Correct original listener/output-pointer prose; addr/off value pair, CQE0, fresh negative sockets and independently checked loopback endpoints |
| S:544 | ADD/MOD/DEL interest-list control | Separate control CQE/readiness wait; native positive-retired target avoids @intCast negative trap; full-u64 event token retained |
| S:565 | One-shot readiness and rearm | Native u32 little-endian mask; pipe IN/HUP, real bounded quiet waits/rearm; not a persistent notification stream |
| S:583 | Remove request by identity | Full-u64 target tag replaces pointer; target/remover CQEs separate, sorted by tag not arrival; selected sequential path, not every race |
| Q:13 | Ordinary SQE ABI, overlapping fields, tag and referenced storage | Exact installed extern64 type; opcode enum/u8 flags/u32 operation flags; buf_index/group, personality and splice input meanings retained; SQE128 excluded |

## Boundary decisions

- Intro cat/copy, low-level and enter links resolve to native chapters. Fixed
  buffers and SQPOLL replace the original TODO links/examples. Mistaken read,
  CONNECT, RECV and SPLICE prose is corrected, not reproduced as false Zig APIs.
- Native constructors acquire/prepare/tag but do not submit. Preparer bodies
  clear fields: apply extra flags/personality afterward. Encoded addresses do
  not retain application storage; SQE-slot reuse does not release its operands.
- The executable 33-constructor reference emits preparation metadata only.
  Its mixed regular-FD/socket/epoll/registered-buffer operands must not be
  submitted. A fresh trace has one setup, **zero enters/registrations** and
  observed ring closure. Whole33 records cover five printed fields, not all
  operands or kernel effects. SQE chapter's “executed 33-constructor reference”
  means executed constructors, not completed operations.
- The raw reference submits batches1/3/1/2, with an additional zero-submit wait
  in this trace. Whole result/prefix bytes agree across owned pipe/file stdout;
  input is unchanged. FD/prefix, advice-page zeroing and range CQEs remain
  operation-specific. No advisory-performance, physical-writeout or durability
  inference. Two finite sink cases are not arbitrary-position/PBT assurance.
- Current chapters additionally cover timers, cancellation, selected buffers,
  RWF and registration updates; optional deadline/cancel modes submit only their
  compatible owned operations. Current CQEs override the SDK's stale linked
  timeout result comment. Broader clocks/flags/races/transports/multishot,
  concurrency/overflow, historical kernels/architectures and all unwind paths
  are not original-purpose gaps merely because this bounded suite omits them.
- Current replay: **31 selected tests**, zero failures/errors/skips, **one
  property ×400 generated valid cases**. Other cases are finite contracts, not
  additional generated properties. No make epub, native/strict build, full99,
  reader, EPUBCheck, new mutant or independent-review claim.
- All93 native/publication/tool inputs and historical full-suite pins remain
  byte-identical. Active runner diagnostics/dispositions are recorded in
  `submission-purpose-verification.json`; no whole-workspace verdict.

Other original-purpose comparisons, mandatory review/findings/final acceptance
and personal-fork delivery remain open. No unsupported review retry or fallback.
