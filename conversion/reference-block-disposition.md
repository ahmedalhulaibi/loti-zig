# Reference-block conversion notes

Author comparison against `c9ee2424af02e4c1e4765088580107d5e17b826e`.
These 75 IDs complement the 37 tutorial and 16 implicit-literal notes. This
accounts for all 128 inventoried blocks, **not** all prose lines or independent
review. A disposition records the translation and its evidence limits; it is
not a claim that every operation, flag or failure path was executed.

Evidence keys: **S** = installed Zig 0.17.0 declaration/ABI, included by
`tools/reference_docs.py`; **P** = executed constructor plus selected metadata
checks, **not submission**; **E** = actual operation effect at the CLI/TCP
boundary. Current test/source hashes: `test-verification.json`. Raw mapping
evidence: `raw-mapping-verification.json`. Prefixes below are repository paths.

## Setup — `ref-zig/setup_teardown.rst`

| Original block ID | Native replacement and semantic comparison | Evidence / limit |
|---|---|---|
| `ref-liburing/setup_teardown.rst:9` | `linux.IoUring`: owned value, not output pointer; no copying ownership | S; SDK setup in all wrapper examples |
| `ref-liburing/setup_teardown.rst:10` | SDK `IoUring` replaces handwritten wrapper layout; SQ/CQ resources remain explicit | S; no promise of identical foreign wrapper fields |
| `ref-liburing/setup_teardown.rst:24` | `IoUring.SubmissionQueue` | S; native queue type used by `reference-setup` |
| `ref-liburing/setup_teardown.rst:25` | SDK SQ pointers/mask/array/local producer state replace obsolete layout | S; submitted reads exercise it; complete interleaving model open |
| `ref-liburing/setup_teardown.rst:46` | `IoUring.CompletionQueue` | S; native queue type used by `reference-setup` |
| `ref-liburing/setup_teardown.rst:47` | SDK CQ storage/head/tail/mask replace obsolete wrapper layout | S/E; copy and manual acknowledgement use separate batches |
| `ref-liburing/setup_teardown.rst:63` | `IoUring.init(entries, flags)`: error union and nonzero power-of-two u16 depth | S/E; narrower SDK input contract stated, raw syscall remains u32 |
| `ref-liburing/setup_teardown.rst:80` | `init_params`: zero reserved fields; CQ sizing added to original flags/CPU/idle inputs | S/E; SQ 8/CQ 32 actually created |
| `ref-liburing/setup_teardown.rst:90` | `RawRing.map(fd, params)`, not an invented SDK method; ownership transfers only on success | E; shared/separate real mappings; injected construction failures open |
| `ref-liburing/setup_teardown.rst:104` | `RawRing.dontFork` applies advice to every owned region; does not stop FD inheritance | E; actual child checks absent pages and inherited descriptor |
| `ref-liburing/setup_teardown.rst:118` | `deinit` releases mappings and ring FD; application files/operands remain separate | E; per-page mincore and closed-FD fcntl checks after normal teardown |

## Completion — `ref-zig/completion.rst`, `ref-zig/cqe.rst`

| Original block ID | Native replacement and semantic comparison | Evidence / limit |
|---|---|---|
| `ref-liburing/completion.rst:11` | `examples/cat.zig` and `reference_completion.zig`: result/tag processing retained; copied CQE consumes automatically | E; explicit difference prevents a second acknowledgement |
| `ref-liburing/completion.rst:45` | `copy_cqe`: wait, return owned value, consume; error union instead of errno/output pointer | S/E; first NOP CQE and timer CQE |
| `ref-liburing/completion.rst:60` | `copy_cqes(destination, wait_nr)`: actual count, not guaranteed exact batch size | S/E; loop gathers tags 1–4; no borrowed pointer return |
| `ref-liburing/completion.rst:76` | `raw_ops.wait_with_timeout`: EXT_ARG relative deadline and optional atomic mask | E for expiry/empty non-null mask; explicit submission required; no hidden SQE/reserved tag; delivered signals/restoration open |
| `ref-liburing/completion.rst:97` | Same helper with minimum 1/null mask replaces timeout-only convenience | S; null and non-null masks expressible; expiry execution uses empty non-null mask |
| `ref-liburing/completion.rst:103` | One-element `copy_cqes(..., 0)` replaces nonblocking peek and consumes returned value | S; empty nonblocking result executed; successful singleton nonblocking case not separately attested |
| `ref-liburing/completion.rst:118` | `copy_cqes(..., 0)` for batch; borrowed alternative documented with `cq_ready`/mask | S/E for copied batches; nonblocking populated batch not separately attested |
| `ref-liburing/completion.rst:134` | Direct `cqe.user_data` u64 tag replaces foreign pointer extraction | E; correlation tags checked; tag does not extend operand lifetime |
| `ref-liburing/completion.rst:148` | `cqe_seen` only for a borrowed entry; never after copy methods | E; separate manual batch uses one seen plus advance-three |
| `ref-liburing/completion.rst:159` | `cq_ready` completes original TODO with acquire/readiness semantics | S/E; four ready, then zero after acknowledgement |
| `ref-liburing/cqe.rst:12` | Exact `linux.io_uring_cqe`; signed result and meaningful flags retained | S/E; ordinary 16-byte stride; original universal one-SQE/one-CQE assertion corrected for multishot/notifications |

## Registration — `ref-zig/advanced_usage.rst`

| Original block ID | Native replacement and semantic comparison | Evidence / limit |
|---|---|---|
| `ref-liburing/advanced_usage.rst:9` | `register_buffers([]const posix.iovec)` retains registration/range lifetimes | S/E; table registration and actual fixed-buffer tutorial I/O |
| `ref-liburing/advanced_usage.rst:31` | `unregister_buffers`; application allocation remains owned | S/E; unregister after tutorial completions |
| `ref-liburing/advanced_usage.rst:51` | `register_files([]const linux.fd_t)`; fixed SQE descriptor is table index | S/E; SQPOLL fixed-file reads/writes |
| `ref-liburing/advanced_usage.rst:73` | `unregister_files` releases table references, not application ownership | S/E; completion-before-unregister discipline |
| `ref-liburing/advanced_usage.rst:93` | `register_files_update(offset, fds)`; synchronous table update distinguished from SQE update | S/E; slot 1 changes to a distinct FD, stays readable after application close, restores via async update, then rejects removal/unregistered reads; exact prefixes/CQEs checked |
| `ref-liburing/advanced_usage.rst:115` | `register_eventfd`: counter notification, not request identity or I/O success | S/E; threaded tutorial notification plus actual read bytes |
| `ref-liburing/advanced_usage.rst:135` | `register_eventfd_async`: omit inline completion notifications | E; IOSQE_ASYNC NOP forces an async notification; inline omission case open |
| `ref-liburing/advanced_usage.rst:155` | `unregister_eventfd`; one attached counter per ring | S/E; detach called; later no-notification behaviour not separately checked |
| `ref-liburing/advanced_usage.rst:174` | `raw_ops.register_personality` returns u16 ID; prepared SQE selects captured credentials | E; actual personality NOP; cross-user credential differences not tested |
| `ref-liburing/advanced_usage.rst:189` | `raw_ops.unregister_personality` passes ID through nr_args after completion | E; successful unregister; stale-ID failure not tested |

## Capability/layout references — `ref-zig/supported_caps.rst`, `ref-zig/sqe.rst`

| Original block ID | Native replacement and semantic comparison | Evidence / limit |
|---|---|---|
| `ref-liburing/supported_caps.rst:7` | `linux.io_uring_probe` | S; owned return value replaces allocated pointer |
| `ref-liburing/supported_caps.rst:8` | SDK header/reserved fields plus fixed-capacity 256-op array; ops_len bounds valid results | S/E; kernel query, not a redeclared flexible-array allocation |
| `ref-liburing/supported_caps.rst:20` | `linux.io_uring_probe_op` | S; opcode and support flags remain native ABI |
| `ref-liburing/supported_caps.rst:21` | SDK probe-op layout; no foreign allocation/free | S; independent full-flag oracle remains open |
| `ref-liburing/supported_caps.rst:35` | `ring.get_probe()` on existing ring returns value/error | S/E; kernel query; NOP checked, not every support flag independently |
| `ref-liburing/supported_caps.rst:51` | `raw_ops.probe()` owns and tears down a temporary ring | E; standalone kernel query; no caller ring/foreign free needed |
| `ref-liburing/supported_caps.rst:69` | `probe.is_supported(native_opcode)` returns bool bounded by reported metadata and flag | S/E for listing shape/NOP; complete independent flag truth check open |
| `ref-liburing/supported_caps.rst:85` | `raw_ops.register_probe` zeroes caller storage; nr_args is operation-array capacity | E; raw query on existing ring; helper, not an SDK ring method |
| `ref-liburing/sqe.rst:13` | Exact `linux.io_uring_sqe` replaces old union/padding copy; operation-specific overlapping fields explained | S/E; 64-byte ordinary stride and P for constructors; SQE128 excluded explicitly |

## Submission — `ref-zig/submission.rst`

All rows below retain referenced-storage lifetime rules. **P** does not verify
every operand field or execute the opcode. Original spelling errors
`io_ring_get_sqe`/`io_uring_set_sqe_data` are corrected, not recreated as APIs.

| Original block ID | Native replacement and semantic comparison | Evidence / limit |
|---|---|---|
| `ref-liburing/submission.rst:12` | `ring.read(tag, fd, .iovecs, offset)` plus `submit`; acquisition/preparation combined, correlation remains explicit | E in cat/copy; construction alone does not issue I/O |
| `ref-liburing/submission.rst:32` | `get_sqe` returns slot/error.SubmissionQueueFull, not nullable pointer | S/P; multiple slots prepared; full-capacity failure oracle open |
| `ref-liburing/submission.rst:51` | Assign `sqe.user_data` after low-level prep; constructors accept u64 tag | P/E; tag correlation; foreign pointer ownership not reproduced |
| `ref-liburing/submission.rst:62` | Assign u8 `sqe.flags` to replace, or |= to preserve constructor bits | P/E for soft-link/async/fixed flags; all flag combinations not verified |
| `ref-liburing/submission.rst:73` | `submit` returns submitted count/error, not completion count | S/E; batches, SQPOLL consumption caveat stated |
| `ref-liburing/submission.rst:89` | `submit_and_wait(wait_nr)` returns submission count and requests CQ threshold | S/E; NOP batches; completion consumption separate |
| `ref-liburing/submission.rst:114` | `ring.nop` | P/E; NOP batches/personality/async notification, no data-I/O claim |
| `ref-liburing/submission.rst:127` | `ring.read(.buffer)`: mutable slice carries length; u64 value offset | P/E in copy/raw references; actual count may be short |
| `ref-liburing/submission.rst:148` | `ring.write`: const slice carries length and offset | P/E in copy/link/fixed examples |
| `ref-liburing/submission.rst:169` | `ring.read(.iovecs)`: vectored read with stable iovecs and buffers | P/E in both io_uring readers; whole binary bytes checked |
| `ref-liburing/submission.rst:190` | `read_fixed`: registered range/index, not implicit registration | P/E; four registered-buffer operations |
| `ref-liburing/submission.rst:213` | `writev`: const iovec slice and offset; vector count is not byte count | P; constructor only; copy now uses scalar WRITE, so vectored-write effect unverified |
| `ref-liburing/submission.rst:234` | `write_fixed`: write from registered range/index; original mistaken read prose corrected | P/E; successful fixed write/readback |
| `ref-liburing/submission.rst:259` | `fsync`: flags 0/data-only; earlier submissions need link/drain/completion ordering | P only; no submitted FSYNC example; physical durability/crash outcome not attested |
| `ref-liburing/submission.rst:283` | `close`: successful CQE consumes process descriptor ownership | P/E in link; prevent subsequent double-close |
| `ref-liburing/submission.rst:300` | `openat`: sentinel path, native O flags/mode; CQE returns owned descriptor | P only; HTTP uses synchronous confined openat2, not evidence for this SQE |
| `ref-liburing/submission.rst:321` | `raw_ops.openat2`: native three-u64 OpenHow and SQE encoding | P/E; actual async open and exact file prefix |
| `ref-liburing/submission.rst:341` | `fallocate`: mode/offset/u64 length preserved; filesystem-specific support | P only; allocation/deallocation effect unverified |
| `ref-liburing/submission.rst:361` | `statx`: sentinel path, native mask and stable output storage; directory/path flags explained | P only; synchronous file stat is not asynchronous STATX evidence |
| `ref-liburing/submission.rst:380` | `raw_ops.fadvise`: file descriptor/range/advice SQE, not synchronous substitute | P/E for successful CQE; advisory performance outcome not claimed |
| `ref-liburing/submission.rst:399` | `raw_ops.madvise`: memory range/advice SQE and Linux alignment | P/E; owned-page MADV_DONTNEED zeroing checked |
| `ref-liburing/submission.rst:418` | `splice`: value offsets with all-ones sentinel; at least one pipe; rw_flags set after prep | P only; original pointer-offset prose corrected; actual transfer unverified |
| `ref-liburing/submission.rst:442` | `recvmsg`: mutable linux.msghdr and nested storage retained | P only; datagram/control-message effects unverified |
| `ref-liburing/submission.rst:461` | `sendmsg`: linux.msghdr_const and stable nested vectors | P only; actual message send unverified |
| `ref-liburing/submission.rst:473` | `recv`: RecvBuffer; scalar bytes, not msghdr; zero datagrams differ from TCP EOF | P/E; real fragmented/binary/empty HTTP requests exercise RECV; datagram effects unverified |
| `ref-liburing/submission.rst:493` | `send`: const bytes/message flags; partial counts and NOSIGNAL explained | P/E; exact HTTP headers/bodies over real TCP; forced partial-send/SIGPIPE cases unverified |
| `ref-liburing/submission.rst:505` | `accept`: optional address/length outputs and accept flags; CQE owns new FD | P/E; real loopback HTTP accept; supplied peer-address output not independently checked |
| `ref-liburing/submission.rst:525` | `connect`: peer pointer plus value length; original listener/value-result mistakes corrected | P only; actual async connect unverified |
| `ref-liburing/submission.rst:544` | `epoll_ctl`: interest-list operation, not readiness wait; optional event storage | P only; actual ADD/MOD/DEL effects unverified |
| `ref-liburing/submission.rst:565` | `poll_add`: one-shot readiness mask, not modifying a global poll list | P only; rearm/readiness effect unverified |
| `ref-liburing/submission.rst:583` | `poll_remove`: target u64 tag; remover/target CQEs distinct, races possible | P only; actual cancellation/race effects unverified |

## Raw syscall declarations

Implicit includes/layout snippets are already in `implicit-literal-disposition.md`.

| Original block ID | Native replacement and semantic comparison | Evidence / limit |
|---|---|---|
| `ref-iouring/io_uring_setup.rst:15` | `linux.io_uring_setup(entries, params)`; errno-encoded usize and owned FD | S/E; real raw setup and mappings; parameter input/output roles updated |
| `ref-iouring/io_uring_enter.rst:15` | `linux.io_uring_enter`: counts submissions, does not consume CQEs; mask size supplied by SDK | S/E; raw reader; EXT_ARG uses explicit syscall6/different structure; signals/IOPOLL limits open |
| `ref-iouring/io_uring_register.rst:15` | `linux.io_uring_register`: typed opcode, optional argument, opcode-specific count/result | S/E; buffers/files/eventfd/probe/personality; returned ID/count distinguished from zero success |

## Audit observations

- Some reference declarations have only constructor evidence. Their native text
  is translated, but stronger operand/effect/failure verification remains open.
- File-table replacement now has changed-FD fixed-read effects and asynchronous
  restore/removal/unregistration checks. Concurrent updates, partial multi-entry
  failure and complete probe-flag truth still need independent checks.
- Delivered signals, mask restoration/interruption, populated nonblocking CQ
  paths and full-capacity errors need boundary checks. Ordinary successful ring
  teardown does not prove cleanup after every partial-construction failure.
- This document does not close the all-line/prose semantic audit, state model,
  whole-port mutation assessment, mandatory independent review or delivery push.
