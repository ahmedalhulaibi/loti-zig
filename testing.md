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
| `probe` | Kernel-reported opcode flags drive results, not a hardcoded list | Compare emitted capability records and exercised operations |
| `webserver` | Accept/read/write use io_uring; GET serves correct MIME/body; missing, forbidden, traversal, fragmented, and oversized requests have defined responses | Real TCP/HTTP boundary, table-driven, temporary document root |
| Raw ring | SQ/CQ atomics, wrapping counters, setup/mmap/cleanup, and actual read operations | Native execution; generated queue-state model checks remain pending |
| Reference APIs | Every documented call is analyzed by the compiler; unsupported conveniences have real raw-ABI replacements | Build complete executable reference examples; execute applicable cases |
| Reference raw operations | Real `OPENAT2` yields exact prefix/unchanged input; `MADV_DONTNEED` clears owned memory; range flags/length/offset and success/invalid-flags/invalid-descriptor CQEs match | Hypothesis over binary files plus literal expected metadata/errno values; no physical write-out/durability claim |
| Reference completion | Automatic copy/consume and manual acknowledgement use different batches; no double acknowledgement; deadline expires | Real NOP/timer CQEs; exact IDs, readiness and results |
| Reference registration | Async-only eventfd actually notifies; credential ID is used; probe methods query kernel flags | Registration and real NOPs; exact counters/results |
| Reference constructors | All 33 requests encode the right opcode, tag, flags, selected lengths and buffer groups; mixed operands stay unsubmitted | Executed constructors and exact metadata properties; not operation-effect evidence |
| Inventory CLI / persisted JSON | Implicit C/output literals cannot be silently omitted; all captured ranges/text match immutable source; fresh runs agree | Original Git snapshot as fixture; 16 pinned C cases; independent Docutils extraction; exact line/range and determinism checks |
| Docs | All original chapter topics migrated; no stale domains/snippets/build commands; code inclusions refer to compiled sources | Inventory mapping + independent semantic review; Sphinx warnings-as-errors |
| EPUB | Chapter order, navigation, local images, attribution, licence, no DRM | EPUBCheck + archive/content audit |
| Publication verifier CLI | Valid edition returns the whole fidelity report; damaged chapter/spine/title/navigation/literals/images/DRM/script classes fail with exact structured reasons | One table-driven subprocess test over nine damaged archives plus exact successful report; not source-code mutation verification |

Hypothesis uses shrinking and retains discovered cases. Static inventories are
coverage indexes, not proof of semantic conversion. Native compiler checks and
actual CLI execution are separate gates. Mutation verification will be bounded
to our code and recorded; source edits must be restored after each probe.
