# Raw syscall purpose comparison

Author comparison, **not independent acceptance**. Read complete original/current
`ref-iouring/{index,io_uring_setup,io_uring_enter,io_uring_register}.rst`;
original commit `c9ee2424af02e4c1e4765088580107d5e17b826e`. This covers
19 inventory blocks (all16 implicit syscall literals plus three declarations),
330 inventoried lines, including197 outside-block lines. Inspect SDK syscall/
errno bodies, native raw setup/map/publication/consumption/cleanup and referenced
consumers. No required conversion gap found in this chapter subset.

S/E/R select the original setup/enter/register chapter, respectively.

| ID | Preserved purpose / necessary native correction |
|---|---|
| S:11 | Foreign include replaced by native std.os.linux declarations; no header import/libc dependency |
| S:15 | Raw setup takes u32/native params and returns errno-encoded usize; decode before FD cast, unlike old -1/errno convention |
| S:30 | Exact native params: wq_fd/resv3 replace old resv4; zero reserved/input fields, kernel output offsets/capacities/features; CQSIZE input is not an output-only field |
| S:77 | Publish tail before testing NEED_WAKEUP; native wrapper handles portable ordering/wakeup, not an architecture-specific smp_mb macro |
| S:163 | Exact SQ offset record; byte offsets relative to correct mapped base, not process addresses |
| S:181 | Control mapping length from returned offsets/capacities; SINGLE_MMAP uses max(SQ,CQ), otherwise separate regions |
| S:194 | Derive aligned SQ head pointer from base plus returned byte offset |
| S:211 | Slot is wrapping counter masked by ring_mask; counter does not reset at physical ring boundary |
| S:217 | Separate SQE mapping at SQES offset, actual returned capacity × ordinary64-byte stride |
| S:226 | Exact native CQ offsets; CQ owns entries directly, unlike SQ's index array |
| S:241 | CQ uses shared or distinct CQ base; mapping ownership/retirement separate from caller-owned operands |
| E:11 | Native syscall interface replaces foreign include |
| E:15 | fd/to_submit/min_complete/flags/optional mask retain roles; hidden sixth ordinary ABI-size argument supplied by SDK; raw result counts submissions, not CQEs |
| E:58 | Kernel atomically installs/restores optional wait mask; native SIGUSR1 basic/EXT_ARG consumers distinguish interrupted wait from operation CQE |
| E:64 | Original set/wait/restore sequence is explanatory equivalence, not safe separate calls to recreate; race explicitly described |
| E:76 | Exact installed SQE replaces historical union/padding copy; operand storage meanings delegated to native preparers, with loans retained |
| E:425 | Native CQE tag/signed result/flags; correct obsolete reserved-flags claim; copy consumes once, borrow acknowledges once |
| R:11 | Native register syscall replaces foreign include |
| R:15 | Typed IORING_REGISTER/optional opaque arg/opcode-specific count; nonzero successful personality IDs/update counts preserved |

## Complete surrounding prose

- Index retains all three entry points and separates raw errno words from Zig
  error unions. Setup creates FD/context, **not mappings**. Wrapper u16/power-of-
  two constraints do not redefine raw u32 kernel sizing. CQSIZE SQ8/CQ32 and
  actual shared/separate mappings have bounded consumers.
- Four original setup flags remain: IOPOLL storage/direct-I/O support, SQPOLL
  publication/sleep/wakeup, SQ_AFF's SQPOLL requirement, CQSIZE sizing. Five
  original feature families remain: SINGLE_MMAP, NODROP, SUBMIT_STABLE,
  RW_CUR_POS, CUR_PERSONALITY. Correct universal syscall-free, unlimited CQ,
  data-buffer-release and old mandatory privilege/fixed-file assumptions.
  Affinity, IOPOLL, physical overflow/resource exhaustion and cross-user
  credentials are documented capabilities, not executed assurance.
- SQ/CQ producer/consumer roles, release/acquire publication, index indirection,
  wrapping counters and diagnostics remain. Enter does not publish SQ tail or
  consume application CQ head. SQE reuse does not release referenced storage.
  SQE128/CQE32/alternate-layout modes are excluded from these ordinary mappers.
- Every original enter opcode family has a native constructor/helper and operand
  explanation in submission; the preceding32-block audit covers the consumers.
  Correct original EPOLL_CTL's swapped pointer/FD operands, FALLOCATE length
  storage, SPLICE pointer-offset prose and timeout count-zero semantics through
  actual preparers/helpers. Operation flags use rw_flags, not u8 SQE flags.
  Construction-only mixed requests are not submitted as an invented example.
- FIXED_FILE, DRAIN, LINK, HARDLINK and ASYNC meanings remain. Short/unexpected
  linked results can cancel unstarted dependents; separate chains remain
  independent. HARDLINK does not prevent submission failure or require a second
  soft-link bit. General drain/hardlink/race combinations are not newly tested.
- All eleven original registration operations remain: buffer/file registration and
  unregistration, file update, normal/async eventfd and detach, probe, personality
  registration/unregistration. Array counts, fixed range/index, sparse -1,
  null/count rules, update offset, nested lifetimes and ID return are retained.
  Table references are not application FD ownership; eventfd is not identity;
  capability support is not operand success. Historic backing/1-GiB/resource
  restrictions are contextual, not universal modern rules.
- All original errno classes retain corresponding failure/recovery meanings;
  distinguish failed syscall from negative request CQE, interrupted enter from
  timer expiration, temporary resource pressure from successful submission.
  Obsolete blanket IOPOLL/registered-buffer restrictions are not repeated.
  Current wrapper/helper and target-kernel behavior remain authoritative.

## Evidence and correction

- Fresh raw-cat observation uses owned131072-byte binary and empty inputs:
  exact pipe/file stdout, unchanged inputs, SQ8/CQ16,34 basic enters, two real
  ring mappings352/512 bytes, ordered unmaps and ring close. This is one finite
  plan, not PBT, u32 wrap or concurrency/overflow/memory-order assurance. Trace
  filter does not establish absence of all synchronous read substitutes.
- Found stale **Ordered365** in excluded `testing.md`; current archive has368
  resolved narrative paragraphs. Red commit records original whole row/Git blob
  and actual archive verifier. Green changes only365→368; all other bytes stay
  exact. It is an author-plan correction, not a native or manuscript defect.
- Replayed15 affected public contracts, one property ×400 generated valid cases;
  directly replayed23 literal and seven narrative archive probes without their
  make-epub setup (six narrative negatives plus whitespace positive). No public
  test/expectation override or new damage/mutation-count claim. The current
  archive is reverified afterward and remains byte-identical.
- Seven receipts that pin testing.md get an explicit scoped replay while
  retaining original bodies/digests. Native/publication/tool inputs93 and
  historical full99 source pins stay exact. No native/strict/full-suite/reader/
  EPUBCheck rerun, make epub or independent-review claim. Runner diagnostics and
  dispositions are recorded, not an unconditional workspace-clean verdict.

Remaining original-purpose comparisons, mandatory independent review/findings,
final prompt-to-artifact acceptance and personal-fork delivery stay open. No
unsupported-host review retry or fallback; latest author mutation count stays284.
