# Setup and completion purpose comparison

Author comparison, **not independent acceptance**. Original:
`c9ee2424af02e4c1e4765088580107d5e17b826e`. Read the complete original setup,
completion and CQE chapters, all 22 inventory blocks and current chapters;
inspect SDK/native consumer bodies, not only generated signatures. Originals
are declarations/layouts plus a completion-processing excerpt, not three
standalone programs. No required conversion gap found in this subset.

IDs select original `ref-liburing/setup_teardown.rst` (S), `completion.rst` (C)
and `cqe.rst` (Q). Current targets are their `ref-zig/` counterparts.

| ID | Preserved purpose / necessary native difference | Consumer / bounded evidence |
|---|---|---|
| S:9 | Owned ring type | Native IoUring value owns FD/mappings; copying does not duplicate ownership |
| S:10 | Wrapper ring fields | SDK auto-layout owner, not kernel extern record or obsolete foreign layout |
| S:24 | SQ wrapper type | IoUring.SubmissionQueue; reference-setup uses actual SDK queue |
| S:25 | Shared SQ pointers/array/entries and local producer state | SDK source assigns mappings/pointers/local counters; raw publication and capacity checks retain distinction |
| S:46 | CQ wrapper type | IoUring.CompletionQueue; native CQ consumer uses actual mapped entries |
| S:47 | CQ shared indices/storage/overflow | Acquire readiness and separate copy/borrow batches; no concurrent-consumer acceptance |
| S:63 | Initialise ring before requests | `init(u16, flags) !IoUring`, nonzero power-of-two depth, delegates to init_params; cat uses8. Raw syscall remains u32; no kernel-filled foreign wrapper pointer |
| S:80 | Supply setup parameters | Zeroed native params with CQSIZE: SDK SQ8/CQ32. Original flags/CPU/idle-only restriction corrected; kernel supplies outputs |
| S:90 | Map an already-created raw FD | RawRing.map owns FD only on success, caller closes after failure; shared/separate mappings and five ENOMEM unwind cases. No invented SDK queue_mmap |
| S:104 | Prevent mapping inheritance across fork | MADV_DONTFORK on every owned region; real child mincore checks absent pages and retained inherited FD. Does not prevent FD inheritance |
| S:118 | Unmap queues and close ring FD | SDK deinit / RawRing.deinit; normal per-page/FD retirement checked. Complete/cancel-and-drain before releasing dependent application operands; not universal failure-unwind proof |
| C:11 | Wait, identify, inspect result, process, acknowledge | Native cat checks tag/result/actual bytes; copied CQE already consumed. Original borrowed-pointer seen call must not follow a copy |
| C:45 | Wait for one available CQE | copy_cqe returns value/error and advances CQ; loops if copy_cqes returns0 |
| C:60 | Wait threshold when none available | copy_cqes copies available prefix up to destination capacity; may return before threshold if entries already ready. Actual count, not exact batch promise |
| C:76 | Bounded CQ wait with optional atomic signal mask | raw_ops.wait_with_timeout uses EXT_ARG, no hidden timer SQE/reserved tag/implicit submission/consumption. SIGUSR1 interruption, blocked/null deadlines and restoration checked |
| C:97 | Deadline-only convenience | Same helper with minimum1/null mask; null retains caller mask, not empty mask. Enter deadline error differs from submitted timer CQE |
| C:103 | Peek one without waiting for a completion | One-element copy_cqes(...,0) returns0/1 and consumes copied value; not borrowed peek. Overflow flush may enter kernel; not a syscall-free promise |
| C:118 | Fetch up to available destination capacity | Nonblocking drain model, populated zero-capacity/singleton/batch cases and physical CQ wrap; not u32 wrap or overflow/concurrency assurance |
| C:134 | Recover submitted request identity | Direct full-u64 user_data tag replaces application pointer; tag does not extend operand lifetime |
| C:148 | Acknowledge processed borrowed CQE | Separate manual batch calls cqe_seen once and cq_advance3; copied batch never acknowledged twice |
| C:159 | Report CQ readiness (original TODO) | Acquire tail/head difference without consumption; ready4 then drained0 in manual batch |
| Q:12 | CQE tag/signed result/flags layout and correlation | Native extern16-byte ordinary CQE and helpers; selected BUFFER/ID and EOF ownership real. Correct original universal1:1 claim for multishot/notifications/skipped-success; newer modes unclaimed |

## Meaning and limits

- Submission success is not completion success. Positive results are
  operation-specific (bytes, FD, updated count); negative results are Linux
  errno. CQ flags are meaningful. Storage and borrowed-pointer lifetimes remain
  separate from tag identity and exactly-once acknowledgement.
- Original cat/low-level/syscall/advice links now target native chapters. The
  original init_params TODO has a complete executable. Native queue owner types
  retain their teaching purpose without pretending to be stable kernel layouts.
- SDK `copy_cqes` may enter to flush CQ overflow even with wait_nr0; the tested
  drain has no active producer/overflow. The timeout helper has a CQ-ready fast
  path; a mask is installed only when it actually enters a wait.
- Manual file/pipe stdout comparisons passed for reference-setup (both mapping
  modes) and reference-completion (default/explicit capacities). This finite
  check is not generated PBT or arbitrary sink/position assurance.
- `setup-completion-purpose-verification.json` records selected current checks.
  Full99/build/publication gates remain historical because no native, manuscript,
  test or producer input changed. No new mutation or independent-review claim.
  Remaining original-purpose comparisons, mandatory review and delivery stay open.
