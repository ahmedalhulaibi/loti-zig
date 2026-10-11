# Reader/copy purpose comparison

Base: `dfce7d28`; immutable upstream: `c9ee2424`. Author comparison, not
independent acceptance. Full original/current low-level, cat and copy chapters,
their12 original blocks and surrounding prose were read. Current reader/copy
bodies and helpers were inspected; the earlier raw-syscall and setup audits
already inspect the unchanged raw mapper, publication and cleanup bodies.

## Original purposes

| Original selector | Native preservation/correction |
|---|---|
| `low_level.rst:23` | Native CQE tag, signed result and flags; bytes/errors are operation-specific. Independent tags correlate requests, not arrival order. |
| `low_level.rst:45` | Native SQE/prep_readv: descriptor, vector-array address/count, explicit offset and full tag; retain vectors and byte ranges through completion. Not a copied obsolete C layout. |
| `low_level.rst:82` | Complete raw reader: setup, returned-offset mappings, SQ index indirection, publication, enter, copied completion and exact stdout. Synchronous readv remains a complete native precursor. |
| `low_level.rst:464` | Zero native params; decode raw errno before descriptor cast. Returned capacities/offsets drive mappings. Historical resv[5]/only-flags-input declaration is not the current ABI. |
| `low_level.rst:481` | SINGLE_MMAP selects max(SQ,CQ) shared region; otherwise distinct CQ mapping, plus SQEs. Feature test, not kernel-version guessing. Acquired regions/descriptor have explicit owners. |
| `low_level.rst:531` | Acquire kernel CQ tail; head==tail means empty; mask selects physical slot; copy then release head acknowledges once. Shared pointers are not retained after reuse. |
| `low_level.rst:556` | Acquire SQ head before reuse; prepare SQE and index before release-publishing tail. Wrapping counters versus physical masks; native atomics replace x86 compiler-only macros. |
| `tutorial/cat_liburing.rst:7` | Complete high-level vectored cat, one outstanding request, argument order, exact binary output and ring teardown. Wrapper hides mapping boilerplate, not application ownership. |
| `tutorial/cat_liburing.rst:182` | Checked native init/deinit; exact compiler and Linux requirements. Old source-line-count comparison is not an API contract. |
| `tutorial/cat_liburing.rst:188` | read(user_data, fd, .iovecs, offset) constructs and tags; submit publishes. Error union replaces nullable SQE. No invented ring.readv method. |
| `tutorial/cat_liburing.rst:201` | copy_cqe waits/copies/consumes; tag checked, negative result decoded, initialized byte count used. No cqe_seen after copying. |
| `tutorial/cp_liburing.rst:10` | Two stable16-KiB slots preserve batching/pipelining; tag id+1 selects state, not completion order. Reading precedes writing; only complete writes retire a range/slot. Partial counts advance both buffer and offset. |

## Complete prose and program comparison

- Raw/high-level readers still distinguish visible shared-ring machinery from
  wrapper boilerplate. SQ8 capacity does not change their deliberately
  single-outstanding teaching purpose. Completion order and linked dependencies
  remain separate concepts. The ordinary one-shot examples do not imply one CQE
  for every possible modern multishot/skipped-success/notification mode.
- Two2048-byte vectors replace whole-file allocation. Reads proceed to EOF;
  print only completed bytes, including empty/binary/multiple-file input. The
  old whole-capacity output on a short/error result is corrected, not preserved.
  Regular and owned read-only virtual block devices retain byte semantics;
  explicit-offset readers are not stdin/pipe programs. No forced short READ or
  every device/architecture claim.
- Raw setup uses actual native syscall wrappers and layouts. Acquire/release
  publication and acknowledgment preserve the old barrier/index explanations
  without retaining pointer/padding/compiler-barrier defects. Prior mapper
  checks cover separate mappings, DONTFORK and partial-construction unwind;
  those are not an older-kernel boot or concurrent-ring proof.
- Copy's ring has8 entries, but only two slots are active. It fills available
  slots, submits pending work, processes a correlated CQE, then queues the
  remaining read/write or retires a fully written slot. Single-range scalar
  READ/WRITE replace the old one-element readv/writev, not the multi-request
  purpose. Vectored I/O remains in the reader and file-reference examples.
- `written` advances on full WRITE completion, not when a WRITE is queued.
  The old counter/outer-loop form is not copied as a completion guarantee.
  EINTR/EAGAIN do not advance progress; premature zero/count-overrun fail.
  Correlation is a stable slot ID, not an integer masquerading as a heap pointer.
- Copy retains regular/block size querying. BLKGETSIZE64 encodes size_t but
  returns u64; interrupted queries retry. Input is read-only; output must be
  regular, checked for device/inode alias before truncation. Empty input
  truncates a distinct destination. No host storage experiment is needed.
- Fio origin and Shuveb attribution remain; runnable native source is included
  from this repository. Build/run/API references use Zig0.17.0. The controlled
  scalar-short mode is additional bounded evidence, not a replacement for the
  normal two-slot copy. Its unchanged prior evidence remains historical.
- No metadata preservation, atomic source snapshot/replacement, crash/media
  durability, throughput benchmark, forced completion reordering, multi-slot
  short/error interleaving or exhaustive failure-unwind assurance is claimed.

## Replay and limits

- Six existing contracts: readers/copy properties, alias preservation,
  redirected stdout, unsupported-kind rejection and the owned VM boundary.
  Two attributed properties each generate400 valid cases; explicit examples
  and generated/shrink phases remain distinguishable in the receipt.
- VM contract invokes `zig build` and builds the owned vm-mount fixture, then
  checks16 cases: four programs × four disposable read-only virtio inputs.
  This is a new bounded native build/guest replay, not a new full51-step build
  report, full99 suite or strict HTML/EPUB/reader/EPUBCheck gate.
- Fresh three-reader plans use empty/131072-byte binary/37-byte/empty inputs.
  Owned pipe/file stdout matches whole131109 bytes; every source is unchanged.
- Ordinary copy plans use0/37/131072 bytes and pre-existing longer output.
  Whole destination bytes and source preservation are checked. Large input's
  first enter submits2 requests; total accepted submissions are16. Empty copy
  submits none. Native tags/state and byte effects, not enter return counts,
  establish the completion interpretation. Ring closes before file descriptors.
- Retained copy traces cover the listed syscall filter only. Absence of listed
  synchronous data-transfer substitutes/registrations is not absence of every
  possible syscall/substitute or proof of every SQE operand. Batching does not
  prove simultaneous physical I/O, reduced latency or a performance advantage.
- Exact93-input snapshot, historical full99 source/log pins and current archive
  fidelity are checked separately. No reader/native/manuscript/public-test/
  binding-producer change, new mutation count or historical gate promotion.

Author decision: no required conversion/example-purpose gap found **in this
subset**. Twelve new unique block comparisons bring these purpose reports to
103/128;25 tutorial blocks remain outside them. Enumeration is not semantic
acceptance. Wider prose/final requirement audit, independent review and fork
delivery remain open. Supported reviewer host remains blocked; no retry,
fallback, push or goal-completion claim.
