# Tutorial block disposition

Author comparison, not independent review. Source:
`c9ee2424af02e4c1e4765088580107d5e17b826e`. These 37 IDs are exactly the
inventoried low-level/tutorial blocks: 29 C blocks and eight build/output
literals. Together with `implicit-literal-disposition.md` and
`reference-block-disposition.md`, all 128 block IDs have author conversion notes.
**This is not a complete line-level disposition.**

Replacement paths below are repository-relative. The migrated chapter for each
original path is recorded in `chapter-map.json`; chapters include these compiled
sources, not separate handwritten copies. Tests/limits follow the table.

| Original block ID | Native replacement | Disposition / semantic delta |
|---|---|---|
| `low_level.rst:23` | `ref-zig/_api/cqe.inc`, `examples/reference_setup.zig` | Native extern CQE; u64 tag, signed result, meaningful flags; ordinary 16-byte stride checked |
| `low_level.rst:45` | `ref-zig/_api/sqe.inc`, `examples/reference_submission.zig` | Native extern SQE/overlapping fields, not copied obsolete layout; 64-byte stride and 33 constructor metadata records checked |
| `low_level.rst:82` | `examples/raw_cat.zig` | Raw setup/map/publication/read/consume preserved; fixed streaming vectors replace whole-file allocation and size ioctl; multiple files, actual counts, cleanup; block-device bytes verified in isolated KVM guest |
| `low_level.rst:464` | `ref-iouring/_api/params.inc`, `RawRing.init` | Exact SDK parameters and zero-initialised inputs replace obsolete handwritten fields/reserved sizes |
| `low_level.rst:481` | `RawRing.map` | Feature-selected shared or separate SQ/CQ mapping plus SQEs; per-base pointer offsets, optional CQ ownership/advice/teardown. Both real strategies execute; forced separate mode is not a historical-kernel boot attestation |
| `low_level.rst:531` | `RawRing.readv` | Acquire CQ tail, copy masked CQE, release wrapping head; copied value survives slot reuse; consume once |
| `low_level.rst:556` | `RawRing.readv` | Capacity check, masked SQ slot, native prep, u64 tag, SQ index before release tail; architecture-specific barrier macros removed |
| `tutorial/cat_liburing.rst:7` | `examples/cat.zig` | Native ring convenience reader; stable two-vector streaming buffers and scalar tag replace heap state pointers; whole returned byte prefix only; block-device bytes verified in isolated KVM guest |
| `tutorial/cat_liburing.rst:182` | `cat.main` | `IoUring.init(8, 0)` returns owned value/error union; deferred teardown |
| `tutorial/cat_liburing.rst:188` | `cat.main` read/submit loop | `ReadBuffer.iovecs` selects READV, constructor assigns tag, submit separate; vectors stay valid through completion |
| `tutorial/cat_liburing.rst:201` | `cat.main` completion loop | `copy_cqe` consumes automatically; no second seen acknowledgement; tag/error/actual byte count checked |
| `tutorial/cp_liburing.rst:10` | `examples/cp.zig`, `examples/support.zig` | Two stable 16-KiB slots pipeline read/write with partial-progress state and tags; same-inode rejection before truncation. Native BLKGETSIZE64 now restores read-only block input; generated ioctl request encodes usize and returns u64; isolated VM verifies exact bytes. Destination restricted to regular files |
| `tutorial/fixed_buffers.rst:8` | `examples/fixed_buffers.zig` | Four registered ranges, two writes then two reads, distinct indexes/tags; stable storage and unregister/teardown lifetimes |
| `tutorial/fixed_buffers.rst:138` | `tutorial/fixed_buffers.rst`, fixed-buffer CLI test | Poem retained; actual byte lengths replace old numeric/C-string transcript; whole stdout/file checked |
| `tutorial/link_liburing.rst:8` | `examples/link.zig` | Write/read/close dependency chain preserved; tags allow unordered CQ arrival; cancelled close retains application ownership; successful close prevents double-close |
| `tutorial/link_liburing.rst:96` | `tutorial/link.rst`, linked CLI test | Native JSON replaces CMake/printf transcript; payload is 15 bytes without a trailing newline, not old transcript's 16; results checked as `[15,15,0]` |
| `tutorial/link_liburing.rst:106` | `link.main` normal create flags | Read/write descriptor for successful chain; caller supplies path instead of global temporary filename |
| `tutorial/link_liburing.rst:112` | `link.main --fail-read` | Write-only descriptor produces failed read; option does not invent an error result |
| `tutorial/link_liburing.rst:118` | Linked CLI failure case | Real read `-EBADF` and dependent close `-ECANCELED`; expected JSON `[15,-9,-125]`, file bytes preserved |
| `tutorial/probe_liburing.rst:7` | `examples/probe.zig` | Native fixed-capacity probe value; enum reflection replaces manually maintained name array; no heap probe/free |
| `tutorial/probe_liburing.rst:74` | `tutorial/probe.rst`, probe CLI test | Target-kernel JSON replaces stale kernel 5.6 sample; tests check stream shape/numeric identity/NOP, **not an independent oracle for every support flag** |
| `tutorial/register_eventfd.rst:9` | `examples/register_eventfd.zig` | Native 64-bit counter and joined listener; one bounded 512-byte read; notifications are hints, CQE is separate; retained counter removes sleep-based ordering |
| `tutorial/sq_poll.rst:20` | `examples/sq_poll.zig` | Native setup parameters, registered index 0/FIXED_FILE, writes and read; 10-ms idle/50-ms pause; actual CQ counts replace submission-count assumptions |
| `tutorial/sq_poll.rst:180` | `tutorial/sq_poll.rst`, polling CLI test | Native invocation/bytes replace root/password/ps/poem transcript; no thread-name detection; timing does not prove poller slept on every run |
| `tutorial/sq_poll.rst:201` | `tutorial/sq_poll.rst` observation command | Same kernel tracepoint observes native `fixed-buffers`; host-specific PID/name output not asserted; optional command not run by suite |
| `tutorial/sq_poll.rst:212` | `tutorial/sq_poll.rst` observation command | Observe native `sq-poll`; do not claim all enter calls eliminated; optional trace command not run by suite |
| `tutorial/webserver_liburing.rst:18` | `examples/webserver.zig`, `public/index.html` | Complete native accept/receive/file-read/send server; confined root, stable state and partial progress replace flexible arrays/heap pointer tags; loopback and bounded teaching scope |
| `tutorial/webserver_liburing.rst:472` | `tutorial/webserver.rst`, README build/run commands | Zig build/native CLI and readiness JSON replace CMake and obsolete kernel/listener transcript; actual TCP sample served |
| `tutorial/webserver_liburing.rst:490` | `webserver.main`, `Server.complete` | Value-copy CQEs consume once; per-client stages and tags dispatch; recover/cleanup per-client failures instead of exit on every request error |
| `tutorial/webserver_liburing.rst:537` | `Server.accept` | Native ACCEPT with tag 0/CLOEXEC; optional address outputs omitted, avoiding stack-address lifetime hazards |
| `tutorial/webserver_liburing.rst:553` | `webserver.Client` | Stable fixed client array replaces flexible request/iovec allocation; slot-derived u64 identity and owned buffer/cursors |
| `tutorial/webserver_liburing.rst:568` | `Server.complete` accept branch | Activate free client, receive, rearm listener; close newly accepted descriptor on saturation; multiple clients tested |
| `tutorial/webserver_liburing.rst:578` | `Server.queue` receiving stage | Native RECV replaces old kernel-5.5 READV workaround; appends into remaining header capacity, retains storage |
| `tutorial/webserver_liburing.rst:597` | `Server.complete` receiving stage, `Server.prepare` | Fragmented headers accumulate; EOF releases client; limits/method/path checks produce defined responses |
| `tutorial/webserver_liburing.rst:611` | `Server.prepare`, `Server.response` | Confined open and metadata lookup synchronous; content read async; exact MIME/length and bounded storage replace six heap vectors |
| `tutorial/webserver_liburing.rst:623` | `Server.queue` sending stages | Native SEND with NOSIGNAL; separate stable header/body, advance cursor on short sends rather than assume one full WRITEV |
| `tutorial/webserver_liburing.rst:636` | `Server.complete`, `Client.release` | Release storage/descriptors only after final send/error; no freeing pending operands; connection closes after one response |

## Evidence and limits

- Compiler/build: exact Zig 0.17.0; 15 executables/31 steps. Native CLI/TCP
  contracts: `tests/test_examples.py`, `tests/test_http.py`, `tests/test_reference.py`.
  `test-verification.json` binds source hashes and actual passing property counts.
- Readers/copy: binary/empty/multiple-file/buffer-boundary cases and two 400-case
  properties; aliases/unsupported kinds rejected without destruction; exact
  redirected-stdout regression. `block-device-verification.json`: all four
  programs preserve bytes from four owned read-only virtio devices in an isolated
  x86_64 guest. Original copy's sizing feature is restored. Other device/ABI
  combinations and forced short-I/O fault injection remain unverified.
- HTTP: binary/empty files, MIME/length, indexes/queries, malformed/method/missing
  responses, traversal/encoded traversal/symlinks, fragments, limits, concurrency
  and a completing request beside a stalled client. No production security audit,
  TLS, keep-alive, request bodies, deadlines, streaming or exhaustion model.
- Named complete-source blocks above were compared by responsibility/API use;
  repeated excerpts were compared directly. This does not replace a source-line
  semantic audit or independent review. Queue u32 wraparound/interleaving model,
  source mutation assessment and broader failure paths remain open.
- `raw-mapping-verification.json`: shared/separate virtual mapping strategies,
  1,025 variable-length reads per case, independent prefix/hash/count oracle,
  real child DONTFORK exclusion and per-page/descriptor teardown. Four compiled
  mapping mutants killed; exact source restoration checked. Older-kernel boot
  compatibility and injected partial-construction failures remain unverified.
- Original historical performance/thread/sample output is not treated as a
  measured property of this edition. Optional trace commands retain teaching
  purpose but have no execution attestation.
