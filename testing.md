# Verification boundaries

Compiler gate: exactly Zig `0.17.0`. Linux execution is required; a sandbox that
blocks io_uring is a blocker, not a reason to report completion.
The block-device test requires x86_64/KVM, QEMU, an installed guest kernel with
built-in virtio block support, initcpio BusyBox and GNU `cmp`. It uses generated
read-only disk files; no host block device, mount or privileged host syscall.

| Boundary | Contract and kill claim | Strategy |
|---|---|---|
| `raw-cat`, `cat`, `readv` | Output equals concatenated input bytes; no padding, truncation, lost ranges or overwrite after stdout redirection | Hypothesis subprocess PBT; empty, binary, multiple-file, buffer-boundary inputs; exact regular-file stdout regression |
| `cp` | Destination bytes equal input bytes; reject aliases/unsupported kinds before discarding data; outstanding requests remain correlated | Hypothesis PBT; boundary lengths; exact bytes and typed error headers |
| Reader/copy block input | Real block-device reads/size ioctl preserve all bytes, including empty capacity; destinations stay regular files | Isolated KVM guest: four read-only virtio images, independent fixture/`cmp` oracle; host image hashes unchanged |
| `link` | Write/read/close chain yields correlated results; deliberate read failure cancels linked close | Table-driven subprocess test; completion IDs and exact results |
| `fixed-buffers` | Four registered buffers implement two writes and two reads; indexes and lengths correct | Exact file/stdout bytes and completion results |
| `sq-poll` | Registered file index used; no false submission-count assumption; sleeping poller wakes and later request completes | Execute both initial and post-idle operations; verify final bytes |
| `register-eventfd` | Completion changes counter and CQE correlates with submitted operation; actual file data read | Execute notification/read path; exact counter and bytes |
| `probe` | Every named support result agrees with independently decoded kernel flags; both metadata bounds and bit-0-only semantics hold; raw response complete; inputs unchanged | Exact 59-name fixture and raw ABI offsets/flags; mixed bit fixtures; Hypothesis over native snapshots; argument/size matrix. No operation-effect or cross-kernel guarantee |
| `webserver` | Accept/read/write use io_uring; GET serves correct MIME/body; missing, forbidden, traversal, fragmented, and oversized requests have defined responses | Real TCP/HTTP boundary, table-driven, temporary document root |
| Raw ring | Shared/separate SQ/CQ mapping; queue pointer origins; actual bytes/CQE counts; all owned pages excluded at fork and unmapped at teardown, descriptor closed | Both real mapping strategies; 1,025 variable-length reads and independent hash/prefix oracle; mincore/fcntl/fork checks. Five x86_64 private-FD seccomp mmap failures additionally check procfs identity, exact strace address/length unwind pairs and caller ownership; seven damaged traces challenge the parser. Requires strace/procfs/seccomp. Historical kernel boot, other errno paths and u32 queue-state model remain pending |
| Reference APIs | Every documented call is analyzed by the compiler; unsupported conveniences have real raw-ABI replacements | Build complete executable reference examples; execute applicable cases |
| Reference raw operations | Real `OPENAT2` yields exact prefix/unchanged input; `MADV_DONTNEED` clears owned memory; range flags/length/offset and success/invalid-flags/invalid-descriptor CQEs match | Hypothesis over binary files plus literal expected metadata/errno values; no physical write-out/durability claim |
| Reference file operations | Async OPENAT/READV/WRITEV/FALLOCATE/STATX/FSYNC/CLOSE: exact source copy plus 4096 zero bytes, returned stat fields, flag modes, FD ownership and reopened hash; seven -EBADF CQEs | Binary Hypothesis property plus separate literal 4097-byte/GNU-digest oracle; exact preserved-path and argument matrices; no forced short-write, other allocation modes or physical/crash durability claim |
| Provided buffers | Selected regular-file reads consume one buffer; raw flags/IDs and exact prefix/tail match; exhaustion/group isolation/remove-count/recycling/cleanup are real | Model-based generated commands and binary prefixes plus separate literal report; exact plan/input matrix; positive-result/single-buffer selected groups only; EOF, concurrent/multishot/cancellation ownership unverified |
| Reference completion | Automatic/manual batches separate; deadline expires; full-SQ rejection preserves state; nonblocking zero/single/batch copies consume once across physical CQ wrap | Literal full report; model-based capacity commands check min-count/head/readiness transitions and all tags; typed invalid-plan matrix. u32 wrap, overflow and concurrent/SQPOLL interleavings remain open |
| Reference signals | Pre-queued SIGUSR1 delivers once during an interrupted EXT_ARG wait; blocked/null masks keep it pending until explicit unblock; masks/actions restore exactly; queued NOP is not implicitly submitted | Whole symbolic fixture resolved from Python signal definitions; actual pending bits/handler masks/counts/CQE; exact argument matrix. No sender races, other-signal/restart or ordinary-enter claim |
| Reference registration | Slot-index fixed reads follow distinct-FD sync replacement and async restore; survive application close; sparse/removal/unregistered reads fail; inputs unchanged; eventfd/personality NOPs remain real | Hypothesis over two binary files; whole JSON with exact prefixes/tags/flags/CQE count; pinned differing fixtures kill no-op/wrong-offset updates; typed argument matrix; concurrency/multi-entry partial failure remain open |
| Reference constructors | All 33 requests encode the right opcode, tag, flags, selected lengths and buffer groups; mixed operands stay unsubmitted | Executed constructors and exact metadata properties; not operation-effect evidence |
| Inventory CLI / persisted JSON | Implicit C/output literals cannot be silently omitted; all captured ranges/text match immutable source; fresh runs agree | Original Git snapshot as fixture; 16 pinned C cases; independent Docutils extraction; exact line/range and determinism checks |
| Author line-index CLI | Every inventoried line has exactly one actual note-row reference; missing/overlapping/unknown entries and stale hashes fail; no semantic acceptance claim | Fresh-process determinism; all-line reverse check; eight damaged-input/report cases. Note and target hashes pin inspected versions, not correctness |
| Docs | All original chapter topics migrated; no stale domains/snippets/build commands; code inclusions refer to compiled sources | Inventory mapping + independent semantic review; Sphinx warnings-as-errors |
| EPUB | Chapter order, navigation, local images, attribution, licence, no DRM | EPUBCheck + archive/content audit |
| Publication verifier CLI | Valid edition returns the whole fidelity report; damaged chapter/spine/title/navigation/literals/images/DRM/script classes fail with exact structured reasons | One table-driven subprocess test over nine damaged archives plus exact successful report; not source-code mutation verification |

Hypothesis uses shrinking and retains discovered cases. Static inventories are
coverage indexes, not proof of semantic conversion. Native compiler checks and
actual CLI execution are separate gates. Mutation verification will be bounded
to our code and recorded; source edits must be restored after each probe.
