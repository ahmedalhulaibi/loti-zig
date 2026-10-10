# Verification boundaries

Compiler gate: exactly Zig `0.17.0`. Linux execution is required; a sandbox that
blocks io_uring is a blocker, not a reason to report completion.

| Boundary | Contract and kill claim | Strategy |
|---|---|---|
| `raw-cat`, `cat`, `readv` | Output equals concatenated input bytes; no padding, truncation or lost ranges | Hypothesis subprocess PBT; empty, binary, multiple-file, buffer-boundary inputs |
| `cp` | Destination bytes equal input bytes; failed input must not silently produce success; multiple outstanding requests remain correctly correlated | Hypothesis PBT over payloads; boundary lengths; independently compare bytes |
| `link` | Write/read/close chain yields correlated results; deliberate read failure cancels linked close | Table-driven subprocess test; completion IDs and exact results |
| `fixed-buffers` | Four registered buffers implement two writes and two reads; indexes and lengths correct | Exact file/stdout bytes and completion results |
| `sq-poll` | Registered file index used; no false submission-count assumption; sleeping poller wakes and later request completes | Execute both initial and post-idle operations; verify final bytes |
| `register-eventfd` | Completion changes counter and CQE correlates with submitted operation; actual file data read | Execute notification/read path; exact counter and bytes |
| `probe` | Kernel-reported opcode flags drive results, not a hardcoded list | Compare emitted capability records and exercised operations |
| `webserver` | Accept/read/write use io_uring; GET serves correct MIME/body; missing, forbidden, traversal, fragmented, and oversized requests have defined responses | Real TCP/HTTP boundary, table-driven, temporary document root |
| Raw ring | SQ/CQ atomics, wrapping counters, setup/mmap/cleanup, and actual read operations | Native execution; generated queue-state model checks remain pending |
| Reference APIs | Every documented call is analyzed by the compiler; unsupported conveniences have real raw-ABI replacements | Build complete executable reference examples; execute applicable cases |
| Reference raw operations | Real `OPENAT2` yields correct file bytes; `MADV_DONTNEED` clears the owned page; advisory requests return correlated CQEs | Native submissions plus exact bytes and whole JSON report |
| Reference completion | Automatic copy/consume and manual acknowledgement use different batches; no double acknowledgement; deadline expires | Real NOP/timer CQEs; exact IDs, readiness and results |
| Reference registration | Async-only eventfd actually notifies; credential ID is used; probe methods query kernel flags | Registration and real NOPs; exact counters/results |
| Reference constructors | All 32 requests encode the right opcode, tag, flags, selected lengths and buffer groups; mixed operands stay unsubmitted | Executed constructors and exact metadata properties; not operation-effect evidence |
| Docs | All original chapter topics migrated; no stale domains/snippets/build commands; code inclusions refer to compiled sources | Inventory mapping + independent semantic review; Sphinx warnings-as-errors |
| EPUB | Chapter order, navigation, local images, attribution, licence, no DRM | EPUBCheck + archive/content audit |
| Publication verifier CLI | Valid edition returns the whole fidelity report; damaged chapter/spine/title/navigation/literals/images/DRM/script classes fail with exact structured reasons | One table-driven subprocess test over nine damaged archives plus exact successful report; not source-code mutation verification |

Hypothesis uses shrinking and retains discovered cases. Static inventories are
coverage indexes, not proof of semantic conversion. Native compiler checks and
actual CLI execution are separate gates. Mutation verification will be bounded
to our code and recorded; source edits must be restored after each probe.
