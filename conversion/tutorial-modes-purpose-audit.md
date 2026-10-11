# Remaining non-HTTP tutorial purposes

Base: `c13f63d`; red reproduction: `0c4e5b9`. Full original/current fixed-buffer,
link, probe, eventfd and SQPOLL chapters,14 blocks and native/helper bodies read.
Author comparison, not independent acceptance.

| Original selector | Native preservation/correction |
|---|---|
| `tutorial/fixed_buffers.rst:8` | Four stable512-byte registered ranges; WRITE_FIXED indices0/1, READ_FIXED2/3; offsets0/36, lengths36/35, four independent tags. Wait for both writes before reads; exact counts/duplicates checked; unregister before reuse. |
| `tutorial/fixed_buffers.rst:138` | Same W. H. Davies poem,71 bytes, stdout/file bytes. Remove noisy result prefixes, not text/effects. Registration does not generally make buffered I/O zero-copy. |
| `tutorial/link_liburing.rst:8` | Write/read/close chain with LINK on first two only. Tags1/2/3, complete16-byte message, exact results; close ownership differs on success/cancellation. |
| `tutorial/link_liburing.rst:96` | Successful JSON must be16/16/0, not this edition's erroneous15/15/0. Original C/native16 verified; reader/runtime mismatch reproduced before repair. |
| `tutorial/link_liburing.rst:106` | Read-enabled owned output yields a successful read after write. No shared hardcoded /tmp path. |
| `tutorial/link_liburing.rst:112` | --fail-read opens write-only; WRITE succeeds, READ-EBADF, linked CLOSE-ECANCELED; explicit application fallback. Earlier write is not rolled back. |
| `tutorial/link_liburing.rst:118` | Failure JSON must16/-9/-125. Queue/arrival order is not the dependency; soft/hard links and drain are distinct. Linux5.6 note and actual capability/result checks retained. |
| `tutorial/probe_liburing.rst:7` | Native value probe and all59 installed enum names; actual support bit0 and both last_op/ops_len bounds. Fixed-capacity owner, no heap-free shim/manual stale string array. |
| `tutorial/probe_liburing.rst:74` | Runtime complete records replace stale kernel5.6.4 sample. Kernel/version/policy can change support; positive advertisement is not successful operands/effects. |
| `tutorial/register_eventfd.rst:9` | One≤512-byte read plus native thread/counter notification; persistent eventfd permits producer-first sequencing without artificial2-second sleep. Join before consuming listener state; real CQE bytes, not a string terminator. |
| `tutorial/sq_poll.rst:20` | Native SQPOLL params, registered file/table index0/FIXED_FILE, two writes and readback across idle. Sleep, not poller exit; current privilege/nonfixed support qualified. |
| `tutorial/sq_poll.rst:180` | Real tags/counts/stdout/file bytes replace global thread-name/root/password output. Acquired NEED_WAKEUP plus three real wake calls protect the explicit observed mode. |
| `tutorial/sq_poll.rst:201` | Optional local bpftrace observation still contrasts submitting versus polling task. Field availability and task identities are kernel-specific, not a fixed test fixture. |
| `tutorial/sq_poll.rst:212` | Poller submission can occur without awake-path enter, but waits/wakeups can enter. Tracepoint task names alone do not prove syscall absence; old absolute claim corrected. |

## Gaps found and repaired

- Native link source was correct. The source and existing EPUB advertised15-byte
  results for the16-byte original message. Publication fidelity passed because
  it faithfully reproduced the error. Red records preserve whole source,
  source/archive/native JSON, hashes and the first incorrect author draft.
- Existing link result/file-byte test also passed a compiled CLOSE→NOP variant.
  This survivor is verification weakness, not evidence of a native source bug.
- New boundary contract fills an owned4096-byte stdout pipe. At the report's
  write syscall, only the launched tracer's verified child/tasks are inspected:
  successful close has no target-file FD; cancelled close retains one; both
  still own the ring. After draining filler, whole JSON/file bytes are checked.
  The cancelled case must issue one successful application close before exit.
  Automatic process cleanup, CQE0 or self-reported closed flags cannot replace
  these observations. Linux x86_64/procfs/strace are explicit prerequisites.
- New reader contract compares complete publisher-resolved and packaged JSON
  records with the original/native16-byte fixture. Fixtures/test expectations
  stay unchanged during mutations; isolated native execution routing is not an
  expectation override. Author hashes are not ACL seals or verifier acceptance.
- Initial new draft copied the erroneous15 counts and failed after the valid
  ownership checkpoint. Its bytes/log remain. An uncompiled mutation lacked a
  semicolon; the partial batch/driver/logs remain excluded. Final three valid
  assertion kills replace the partial batch: two native, one source-prose.

## Other complete prose/ownership distinctions

- Fixed ranges retain storage through dependent CQEs/registration; buffer index
  is not fixed-file index. Two-range batches can complete in either order. No
  arbitrary registration failures, direct-I/O alignment or zero-copy guarantee.
- Eventfd is a persistent aggregate counter/wakeup, not request identity or read
  success. Producer stops accessing the ring before the joined listener consumes
  one copied CQE. Async-only registration is a separate forced-async reference;
  no many-producer/listener, coalescing-race or exhaustive failure-unwind claim.
- Probe raw2064-byte ABI and snapshot paths retain native endianness, exact size,
  reserved/unused records, all59 names and bounded-bit tests. Separate raw/live
  reports and400 generated snapshots are not execution of every opcode.
- SQPOLL replaces the original poem with49-byte polling/idle text and combines
  readback into one read; two writes, fixed descriptor addressing and poller
  purpose remain. It is not a fixed-buffer example. Observed sleep has2000
  acquire attempts/1-ms sleeps and a bounded guarded CQ wait; elapsed timing alone
  is not sleep proof. Submit returns are not completion counts.
- Source/API/build references use actual Zig0.17.0; no foreign header/library,
  string-pointer cast, inherited global /etc/passwd input or hardcoded shared
  output is needed. Shuveb origin, poem attribution and chapter reading order
  remain. Optional privileged bpftrace commands were read, not executed or claimed
  as mandatory automated acceptance.

## Acceptance boundary

Current full suite is101 (new ownership and reader tests),16 properties×400;
native build/strict HTML+EPUB/81 browser cases/current EPUBCheck are separately
recorded after manuscript repair. Suite invokes make epub. Full99/type receipts
and original gates remain historical; the old93-input snapshot is preserved,
with exactly its link manuscript input changed. No silent freshness repinning.

These14 comparisons bring purpose reports to117/128; remaining11 are HTTP
tutorial blocks. No broader races, failed thread spawn, permission/umask effects,
all flags/architectures/kernels, syscall-free polling, durability or physical
overlap assurance. Whole prompt/prose acceptance, independent review and delivery
remain open. Reviewer host blocker is unchanged; no retry, fallback, push or goal
completion.
