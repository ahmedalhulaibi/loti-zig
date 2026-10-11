# Selected reference-claim audit

Scope: author comparison, not independent review or acceptance of all 99 bindings.
The full description list was inspected; these bodies/claims were checked directly.

| Claim | Inspected evidence | Correction |
|---|---|---|
| Enter publishes SQEs | `RawRing.readv` release-stores SQ tail before enter; SDK `linux.io_uring_enter` only invokes syscall6 | Caller publishes; kernel consumes already-published entries |
| Setup reference demonstrates `IoUring.init` | `reference_setup.main` calls `init_params`; SDK `init` calls `init_params`, not reverse; `cat.main` calls `init(8,0)` | Default-init binding targets `examples/cat.zig` |
| FADVISE has read/memory effects | `reference_raw.main`: tag 2, NORMAL advice, success CQE; later read and page-zero checks have different requests | Hint acceptance only; no cache/performance claim |
| MADVISE effect | Tag 3, DONTNEED on owned anonymous memory; every byte becomes zero | Exact page-zero boundary, not other advice/mappings |
| OPENAT2 effect | Tag 1 returns FD; tag 5 reads its exact prefix; RDONLY/NO_SYMLINKS | Descriptor/prefix boundary, not memory advice |
| Normal eventfd binding was suspected unused | `reference_registration.main` registers/unregisters normal mode before async mode; tutorial also uses normal mode | No change; suspicion disproved by body inspection |
| Both submit wrappers always return exact submitted counts | Zig0.17.0 SDK `submit` delegates to `submit_and_wait(0)`; method comment qualifies SQPOLL count higher/lower/zero; actual bodies flush SQ/wake/enter | Ordinary submission count versus non-exact SQPOLL result, never operation-completion count; both bindings/manuscript qualified |
| Raw enter always observes poller consumption | `io_uring_enter.2` RETURN VALUE separates ordinary consumed requests and SQPOLL generally returning `to_submit` | SQPOLL raw count is not observed poller consumption; caller release-publication/CQE ownership remain unchanged |

External ordering reference: `man-qmd/build/docs/liburing/man/io_uring.7.txt`,
**EXAMPLES**: release store at line 623 precedes enter at line 631. This is ABI
documentation, not an independent code review.

`reference-semantics-reproduction.json` records the bad generated descriptions and
a passing freshness check. The red commit tests the bad state as-is; the fix flips
five whole-binding fixtures. Five valid producer mutants are rejected even though
generation and `--check` still pass. No native operation or kernel policy changed.

Installed declarations, author notes, indexes and this selected audit do not accept
the remaining semantic conversion. Independent review and final delivery stay open.
