# Implicit-literal conversion notes

Scope: the 16 unlabelled C literals omitted by the first inventory scanner.
Source: `c9ee2424af02e4c1e4765088580107d5e17b826e`. IDs below now occur in
`source-inventory.json`. These are author-inspected dispositions, **not** an
independent review or a disposition of all 3,618 lines/128 blocks.

| Original block ID | Zig replacement | Contract/evidence scope |
|---|---|---|
| `ref-iouring/io_uring_enter.rst:11` | `examples/raw_cat.zig` imports `std.os.linux`; native declaration in `ref-iouring/_api/io_uring_enter.inc` | Foreign header removed; native syscall used by `RawRing.readv` |
| `ref-iouring/io_uring_enter.rst:58` | Signal-mask explanation in `ref-iouring/io_uring_enter.rst`; `raw_ops.wait_with_timeout` in `examples/raw_ops.zig` | Ordinary mask and EXT_ARG layouts distinguished; a non-null empty mask is exercised by the expiring reference wait |
| `ref-iouring/io_uring_enter.rst:64` | Atomic-mask explanation in `ref-iouring/io_uring_enter.rst` | Separate set/wait/restore calls identified as racy, not recreated as recommended code; delivered-signal/mask-restoration behaviour remains untested |
| `ref-iouring/io_uring_enter.rst:76` | `ref-zig/_api/sqe.inc`, included by `ref-zig/sqe.rst` | Exact installed extern layout; `reference-setup` checks 64-byte ordinary stride; 33 constructors exercised separately |
| `ref-iouring/io_uring_enter.rst:425` | `ref-zig/_api/cqe.inc`, included by `ref-zig/cqe.rst` | Exact installed extern layout; 16-byte stride checked; flags corrected from reserved to meaningful; copied/borrowed acknowledgement tested separately |
| `ref-iouring/io_uring_register.rst:11` | Native declaration in `ref-iouring/_api/io_uring_register.inc`; `examples/raw_ops.zig` | Foreign header removed; probe and personality registrations execute through native syscall |
| `ref-iouring/io_uring_setup.rst:11` | Native declaration in `ref-iouring/_api/io_uring_setup.inc`; `examples/raw_cat.zig` | Foreign header removed; setup succeeds before mapping; errno-encoded result checked |
| `ref-iouring/io_uring_setup.rst:30` | `ref-iouring/_api/params.inc`; zero-initialisation in `RawRing.init` and `reference-setup` | Exact installed parameters; input/output roles documented; CQSIZE SQ 8/CQ 32 exercised |
| `ref-iouring/io_uring_setup.rst:77` | `IoUring.submit` in `examples/sq_poll.zig`; publication/wakeup explanation in `ref-iouring/io_uring_setup.rst` | No architecture-specific C barrier; native wrapper handles wakeup; post-idle operation executes, not a proof of all memory-order interleavings |
| `ref-iouring/io_uring_setup.rst:163` | `ref-iouring/_api/offsets.inc`; `RawRing.map` in `examples/raw_cat.zig` | Native SQ offsets; aligned pointers derived from returned byte offsets; mapped read executes |
| `ref-iouring/io_uring_setup.rst:181` | `RawRing.map` shared-region calculation and `std.posix.mmap` | SINGLE_MMAP uses max(SQ size, CQ size); otherwise SQ and optional CQ use their own sizes/offsets; both real strategies execute in reference-setup; forced mode is not an older-kernel attestation |
| `ref-iouring/io_uring_setup.rst:194` | `RawRing.map` derives `sq_head` with checked pointer/alignment casts | Byte offset plus mapping base, not C pointer arithmetic; actual read exercises mapping |
| `ref-iouring/io_uring_setup.rst:211` | `RawRing.readv`: `tail & self.sq_mask`, wrapping subtraction/addition | Regular-file PBT exercises repeated slot reuse; u32 wraparound/state model remains open |
| `ref-iouring/io_uring_setup.rst:217` | `RawRing.map` separate SQE mapping | Native SQE size times returned SQ capacity, correct SQES offset; mapping/read and cleanup execute |
| `ref-iouring/io_uring_setup.rst:226` | `ref-iouring/_api/offsets.inc`; CQ pointer derivation in `RawRing.map` | Exact native CQ offsets; mask used to address CQEs; head advances once per copied result |
| `ref-iouring/io_uring_setup.rst:241` | `RawRing.map` shared-region calculation and CQ pointer derivation | CQ uses shared region with SINGLE_MMAP, otherwise its own mapping and pointer base; teardown/advice cover each owned region exactly once; actual pointer-origin, fork-exclusion and page-release checks pass |

Inventory regression history: `ca7b34e` records the bug (all 16 missing despite
`--check` passing). The fix adds those blocks, seven implicit output literals
and the HTTP build/output block. Every implicit block is cross-checked by
Docutils; each captured line is compared with the immutable source. An
independent parser is not an independent **agent** review.

All 128 block IDs now have author notes across this file,
`tutorial-block-disposition.md` and `reference-block-disposition.md`. Still open:
complete line/prose disposition; delivered-signal/interruption and mask-restoration
execution; queue-state/wraparound checks; whole-port source mutation assessment;
independent semantic review. The SYNC_FILE_RANGE gap now has a native
helper, constructor and actual success/invalid-flags/invalid-descriptor CQEs.
Neither CQ success nor publication fidelity proves physical write-out/durability.
