# Remaining original-line comparison

Author comparison notes for the **567 inventoried lines outside the 128 block ranges**,
against `c9ee2424af02e4c1e4765088580107d5e17b826e`. Ranges below select only those
inventoried outside-block lines; intervening block lines retain their existing
notes. `source-inventory.json` retains every original line number and exact text.
`line-disposition-verification.json` expands the four note documents into an
explicit line-to-note index. Index completeness is **not semantic acceptance**,
complete operation execution or mandatory independent review.

Targets are actual repository files. Section names identify inspected text,
not a promise that every described kernel mode has been executed. Execution,
constructor-only and unverified scopes remain in `reference-block-disposition.md`.

## Navigation, metadata and concepts

| Original range | Current target | Disposition / semantic comparison |
|---|---|---|
| `async_intro.rst:58-81` | `async_intro.rst` | Earlier asynchronous APIs / Readiness and completion: distinguish POSIX/native AIO, readiness/completion and thread pools; use std.Io/std.Thread; remove universal no-blocking and regular-file epoll-readiness claims |
| `changelog.rst:9-10` | `changelog.rst` | Original update retained with attribution; SINGLE_MMAP reduces three mappings to two, not one; native chapter links |
| `conf.py:20-20` | `conf.py` | project/version/release and EPUB title explicitly identify Zig 0.17.0; original author plus adaptation attribution |
| `conf.py:48-48` | `conf.py` | Original logo path retained; publication verifier compares bytes against upstream |
| `index.rst:6-14` | `index.rst` | Zig-edition title, native language scope, Shuveb Hussain/unixism attribution; edition contributions directed to the personal fork |
| `index.rst:32-32` | `index.rst` | Introduction toctree retains what_is_io_uring |
| `index.rst:52-62` | `index.rst` | Native Zig reference toctree replaces obsolete wrapper-library paths; ref-zig/index owns its seven child pages |
| `index.rst:66-72` | `index.rst` | Linux syscall reference retains all three calls through ref-iouring/index; raw Zig errno contract stated there |
| `what_is_io_uring.rst:1-28` | `what_is_io_uring.rst` | The mental model: native setup/submit, SQ indirection/CQ entries, feature-selected mappings, u64 tags, result decoding and exactly-once consumption; qualify modern one-SQE/one-CQE exceptions |
| `what_is_io_uring.rst:33-43` | `what_is_io_uring.rst` | Performance: batching/polling purpose retained; metadata sharing is not payload zero-copy; wakeups/waits can enter kernel; historical paper linked, not claimed as edition measurements |
| `what_is_io_uring.rst:47-53` | `what_is_io_uring.rst` | Use the native Zig wrapper: complete raw-reader tutorial and IoUring reference replace foreign-library recommendation; actual results/policy checks replace version-only assumptions |
| `low_level.rst:3-17` | `low_level.rst` | Native raw teaching implementation still has one outstanding operation; deeper eight-slot ring does not imply concurrency; submit/completion and batching described |
| `low_level.rst:21-33` | `low_level.rst` | Submission and completion types: exact extern layouts, signed results and stable numeric correlation instead of expired heap pointers |
| `low_level.rst:71-80` | `low_level.rst` | READV vector count/address/offset/tag and complete raw reader retained; native prep_readv and publication replace C directives |
| `low_level.rst:462-479` | `low_level.rst` | Setup and mappings: RawRing.init, zeroed native params, kernel outputs and errno decoding; original flags-only input claim corrected |
| `low_level.rst:511-519` | `low_level.rst` | SQ indirection and separate SQEs; choose shared/separate control mappings by feature, not version; syscall reference link retained |
| `low_level.rst:523-525` | `low_level.rst` | Publishing an SQE: metadata/array before release tail, acquire kernel head; portable atomics replace architecture-specific barriers; no universal syscall-free promise |
| `low_level.rst:550-550` | `low_level.rst` | Reading a CQE: acquire tail, masked slot, value copy and release wrapping head; consumption once, pointer invalid after reuse |
| `low_level.rst:572-572` | `low_level.rst` | Publishing an SQE: native prep/tag/index precede tail publication; storage lifetime separate from ordering |

## Syscall prose

| Original range | Current target | Disposition / semantic comparison |
|---|---|---|
| `ref-iouring/index.rst:1-11` | `ref-iouring/index.rst` | All three native entry points retained; raw errno-encoded usize contrasted with wrapper error unions, not libc errno |
| `ref-iouring/io_uring_setup.rst:1-23` | `ref-iouring/io_uring_setup.rst` | Native title/descriptor/params output contract; setup does not itself mmap queues |
| `ref-iouring/io_uring_setup.rst:45-58` | `ref-iouring/io_uring_setup.rst` | Setup flags / IOPOLL: storage/direct-I/O support/alignment and GETEVENTS drive; not SQ thread polling or arbitrary socket-operation support |
| `ref-iouring/io_uring_setup.rst:60-75` | `ref-iouring/io_uring_setup.rst` | SQPOLL: publish before checking NEED_WAKEUP; native wrapper handles sleeping-thread wakeup, not thread restart |
| `ref-iouring/io_uring_setup.rst:91-92` | `tutorial/sq_poll.rst` | Registered files retained in tutorial; privilege/fixed-file historical restrictions qualified with modern SQPOLL_NONFIXED and unprivileged support |
| `ref-iouring/io_uring_setup.rst:95-98` | `ref-iouring/io_uring_setup.rst` | SQ_AFF selects sq_thread_cpu and requires SQPOLL; no claim affinity was executed |
| `ref-iouring/io_uring_setup.rst:101-107` | `ref-iouring/io_uring_setup.rst` | CQSIZE/native cq_entries and ordinary interrupt-driven default; actual SQ 8/CQ 32 reference separate from general sizing rules |
| `ref-iouring/io_uring_setup.rst:115-121` | `ref-iouring/io_uring_setup.rst` | SINGLE_MMAP and NODROP: mapping ownership and overflow/backpressure/draining retained, not unlimited capacity |
| `ref-iouring/io_uring_setup.rst:130-137` | `ref-iouring/io_uring_setup.rst` | SUBMIT_STABLE is not data-buffer lifetime release; RW_CUR_POS all-ones value and shared-position race distinguished from explicit offsets |
| `ref-iouring/io_uring_setup.rst:145-157` | `ref-iouring/io_uring_setup.rst` | CUR_PERSONALITY submits with task credentials or explicit ID; no added privilege; params outputs named in Native parameters |
| `ref-iouring/io_uring_setup.rst:188-201` | `ref-iouring/io_uring_setup.rst` | Mapping and queue indices: native per-base offsets, SQ array indirection, flags and dropped/overflow diagnostics; Zig wrapping arithmetic/acquire-release |
| `ref-iouring/io_uring_setup.rst:247-256` | `ref-iouring/io_uring_setup.rst` | Owned setup descriptor used for map/register/enter; native teardown closes and unmaps, application operand ownership remains separate |
| `ref-iouring/io_uring_setup.rst:268-292` | `ref-iouring/io_uring_setup.rst` | Errors: invalid reserved/options/sizing, descriptor/memory limits, privileges or execution policy; named wrapper errors and related-call links replace C return/errno conventions |
| `ref-iouring/io_uring_enter.rst:1-41` | `ref-iouring/io_uring_enter.rst` | Native submit/wait/count contract, ordinary CQ inspection and IOPOLL distinction; caller release-publishes SQ tail before enter; consumed submissions are not operation results or CQ consumption |
| `ref-iouring/io_uring_enter.rst:53-56` | `ref-iouring/io_uring_enter.rst` | Optional atomic signal mask and restoration retained; ordinary and EXT_ARG layouts/size separated; SIGUSR1/EXT_ARG pending delivery, timeout/restoration and null-mask semantics now checked; ordinary-enter delivery and broader policies remain unverified |
| `ref-iouring/io_uring_enter.rst:116-192` | `ref-zig/submission.rst` | NOP, scalar/vectored/fixed I/O, fsync ordering, one-shot readiness/removal, epoll_ctl, range sync and sockets all map to native methods/helpers; operation flags differ from SQE dependency flags; reference-files now executes vector I/O, sync modes, allocation and async metadata on owned files |
| `ref-iouring/io_uring_enter.rst:194-250` | `ref-zig/submission.rst` | Timers/cancellation: stable timespec, time/count/absolute modes and distinct target/remover completions; linked timer is not CQ wait; count-zero semantics corrected |
| `ref-iouring/io_uring_enter.rst:253-317` | `ref-zig/submission.rst` | Connect, allocation/advice, open/close/statx and scalar I/O retain typed operands/lifetimes; SDK preparers avoid obsolete handwritten overlapping-field encodings |
| `ref-iouring/io_uring_enter.rst:321-335` | `ref-zig/submission.rst` | Splice requires a pipe and value offsets, not pointers; asynchronous FILES_UPDATE borrows descriptor array until its CQE, unlike synchronous registration |
| `ref-iouring/io_uring_enter.rst:346-379` | `ref-iouring/io_uring_enter.rst` | SQE flags: fixed index, drain, soft/hard links and forced async retained; independent chains stay independent; short-result cancellation and submission-failure caveat retained |
| `ref-iouring/io_uring_enter.rst:392-414` | `ref-zig/sqe.rst` | Native operand-dependent storage, vector count versus bytes, fixed range/index, flags and personality. Submission chapter also restores linux.RWF/rw_flags guidance and fsync/data-only distinction |
| `ref-iouring/io_uring_enter.rst:420-449` | `ref-iouring/io_uring_enter.rst` | Publication/lifetimes and raw submission return separated from correlated CQE results; modern CQE flags are meaningful, not reserved |
| `ref-iouring/io_uring_enter.rst:476-538` | `ref-iouring/io_uring_enter.rst` | Errors and recovery: distinguish invalid ring syscall failure from request descriptor/range/opcode/flag CQE errors, resource-pressure retry and interrupted waits; obsolete blanket IOPOLL/fixed-buffer prohibitions not repeated |
| `ref-iouring/io_uring_register.rst:1-27` | `ref-iouring/io_uring_register.rst` | Native ring/typed opcode/optional arg/opcode-specific count; long-lived references do not transfer application ownership |
| `ref-iouring/io_uring_register.rst:29-66` | `ref-iouring/io_uring_register.rst` | Buffers: native vectors, stable ranges/partial ranges, null/zero unregister, memory-lock/huge-page accounting, outstanding-work coordination; historical backing/1-GiB restrictions qualified |
| `ref-iouring/io_uring_register.rst:69-103` | `ref-iouring/io_uring_register.rst` | Files: native fd_t array/sparse -1/fixed index, update offset and count; synchronous/asynchronous update and descriptor/table ownership separated |
| `ref-iouring/io_uring_register.rst:106-120` | `ref-iouring/io_uring_register.rst` | Eventfd pointer/count/null rules and single registration retained; async excludes inline notifications; coalesced hints require separate CQE checks |
| `ref-iouring/io_uring_register.rst:126-133` | `ref-iouring/io_uring_register.rst` | Probe native storage, operation-array capacity, ops_len/support flags and zero reserved fields; capability is not operand success |
| `ref-iouring/io_uring_register.rst:136-147` | `ref-iouring/io_uring_register.rst` | Personality null/zero register, returned ID, prepared SQE field and ID-in-nr_args unregister retained; finish dependents first |
| `ref-iouring/io_uring_register.rst:153-204` | `ref-iouring/io_uring_register.rst` | Correct nonzero successful ID/count results and errno decoding; resource/argument/absent-registration/backing failures remain, limits are target-specific rather than universal old rules |

## Native-reference surrounding text

| Original range | Current target | Disposition / semantic comparison |
|---|---|---|
| `ref-liburing/index.rst:1-7` | `ref-zig/index.rst` | Exact-version native reference/toctree; generated declarations versus runnable sources, constructor versus operation and helpers versus SDK explicitly separated |
| `ref-liburing/setup_teardown.rst:7-7` | `ref-zig/setup_teardown.rst` | Native setup/mapping/teardown responsibilities retained; value/error/ownership differences described with complete reference program; five private-FD x86_64 ENOMEM injection cases check partial mappings and retained caller ownership |
| `ref-liburing/sqe.rst:5-11` | `ref-zig/sqe.rst` | Native extern request type and supported operations replace foreign header/struct references; actual installed ABI used |
| `ref-liburing/cqe.rst:8-10` | `ref-zig/cqe.rst` | Native extern result type replaces foreign header/struct reference; tag/result/flag rules and stride qualify newer modes |
| `ref-liburing/supported_caps.rst:62-62` | `ref-zig/supported_caps.rst` | Link to complete native probe tutorial and existing/temporary/raw probe variants; independent raw flags now cover all 59 named results; synthetic flags/header bounds use an independent ABI encoder; no operand-success claim |
| `ref-liburing/submission.rst:24-28` | `ref-zig/submission.rst` | Cat/copy references; combined native constructors and explicit tags/flags/submit replace misspelled C helper names; SQPOLL link supplied |
| `ref-liburing/submission.rst:107-107` | `ref-zig/submission.rst` | READV illustration points to compiled cat source; native .iovecs variant replaces old snippet anchor |
| `ref-liburing/completion.rst:9-40` | `ref-zig/completion.rst` | Wait/tag/result/short-read/ownership responsibilities retained; copied values already consumed, borrowed entries acknowledged exactly once; u64 replaces pointer extraction |
| `ref-liburing/advanced_usage.rst:24-167` | `ref-zig/advanced_usage.rst` | All eight related registration links become shared native syscall/registered-resource links; buffer/file/eventfd semantics retained in their corresponding sections |

## Tutorial surrounding text

| Original range | Current target | Disposition / semantic comparison |
|---|---|---|
| `tutorial/index.rst:1-3` | `tutorial/index.rst` | Native IoUring boilerplate management; application retains operands/state; compiled source and raw-chapter navigation |
| `tutorial/cat_liburing.rst:3-5` | `tutorial/cat.rst` | Native ring reader contrasted with raw reader; stable vectors/value completions/owned descriptor; no foreign runtime |
| `tutorial/cat_liburing.rst:177-180` | `tutorial/cat.rst` | Wrapper hides setup/publication boilerplate; old C line-count comparison removed rather than claimed for Zig files; complete source is included |
| `tutorial/cat_liburing.rst:211-218` | `tutorial/cat.rst` | Related API references use native init/read(.iovecs)/tag/submit/copy_cqe/deinit and native reference links; no second acknowledgement |
| `tutorial/cp_liburing.rst:3-8` | `tutorial/cp.rst` | Pipelined native copying retains two-file CLI and fio/Shuveb provenance; read/write batches versus single-request reader |
| `tutorial/cp_liburing.rst:260-260` | `tutorial/cp.rst` | State machine replaces nested loops/heap requests; two stable slots, masked identity via tags, partial-progress handling and CQE-driven recycling; scalar read/write replace vectors |
| `tutorial/fixed_buffers.rst:6-6` | `tutorial/fixed_buffers.rst` | Native registration/index/range semantics; incorrect general no-data-copy claim explicitly corrected |
| `tutorial/fixed_buffers.rst:130-132` | `tutorial/fixed_buffers.rst` | Four stable stack ranges replace malloc; writes 0/1 then reads 2/3 and original poem retained; actual lengths, tags and lifetime/teardown stated |
| `tutorial/link_liburing.rst:5-90` | `tutorial/link.rst` | Write/read/close dependency chain retained; unordered CQ arrival handled by tags, native IOSQE_IO_LINK after preparation, last entry unlinked |
| `tutorial/link_liburing.rst:126-126` | `tutorial/link.rst` | Actual -EBADF read/-ECANCELED close failure, successful prior write and application fallback close; not transactional rollback |
| `tutorial/probe_liburing.rst:5-5` | `tutorial/probe.rst` | Native get_probe/is_supported, owned value and reflected numeric/name records; no foreign allocator/free or stale support transcript |
| `tutorial/register_eventfd.rst:7-7` | `tutorial/register_eventfd.rst` | Counter can integrate with poll/epoll; notification is hint, not request identity or proof of operation success |
| `tutorial/register_eventfd.rst:118-120` | `tutorial/register_eventfd.rst` | std.Thread listener replaces foreign threading; retained counter permits producer-before-listener, no sequencing sleep; producer stops ring access and joins before inspecting result |
| `tutorial/sq_poll.rst:6-18` | `tutorial/sq_poll.rst` | Native SQPOLL/wakeup/fixed index mechanics; sleeping does not exit thread; modern privilege/nonfixed support qualified |
| `tutorial/sq_poll.rst:170-178` | `tutorial/sq_poll.rst` | Native init_params, 10-ms idle/50-ms pause and actual fixed-file readback; two writes/one combined read replace four-buffer poem/thread-name detection; no timing-only wakeup proof |
| `tutorial/sq_poll.rst:197-210` | `tutorial/sq_poll.rst` | Observe it: bpftrace command retained for native executables; local names/PIDs not fixed or claimed as edition evidence; tracing submissions alone cannot prove no enter calls |
| `tutorial/webserver_liburing.rst:3-8` | `tutorial/webserver.rst` | Native ACCEPT/RECV/READ/SEND and original ZeroHTTPd provenance; payload I/O uses completion loop; readiness is not completion |
| `tutorial/webserver_liburing.rst:486-551` | `tutorial/webserver.rst` | Native listener/accept plus stable Client phases/tag dispatch replace heap request pointers; continued accepts and concurrent-client handling retained |
| `tutorial/webserver_liburing.rst:576-595` | `tutorial/webserver.rst` | Native RECV replaces old kernel READV workaround; remaining-capacity slices and fragmented-header accumulation; no foreign-library calls or old version-only rationale |

## Retired standalone catalog — not an omitted runnable example

The original `delme.c` consists of declarations, helper names, comments and DONE
markers. It has no main, function bodies or complete runnable program. Removing
it removes a stale C checklist, not an executable. Its native replacements are
in the inspected reference chapters, generated declarations and compiled
reference sources. DONE markers are not reused as verification evidence.

| Original range | Current target | Disposition / semantic comparison |
|---|---|---|
| `delme.c:1-10` | `ref-zig/supported_caps.rst` | Probe/get-probe/opcode-supported catalog maps to native existing/temporary ring and bool support methods; no caller heap free |
| `delme.c:11-27` | `ref-zig/setup_teardown.rst` | init/init_params/deinit plus explicit RawRing.map/dontFork; no invented SDK mmap/dontfork methods |
| `delme.c:28-59` | `ref-zig/completion.rst` | Tag field, copied nonblocking/waiting batches and raw deadline helper; pointer-output/error conventions replaced, acknowledgement explicit; populated single/batch/zero-capacity paths now have exact head/readiness/tag models |
| `delme.c:60-73` | `ref-zig/completion.rst` | for-each macro replaced by acquired readiness/head/mask iteration; native cq_advance/cqe_seen/cq_ready; manual reference actually executes this batch |
| `delme.c:74-87` | `ref-zig/submission.rst` | Native submit/submit_and_wait/get_sqe and tag/flag assignment; counts/ownership/error unions stated |
| `delme.c:88-175` | `ref-zig/submission.rst` | Every listed preparer has a native constructor or explicit raw helper, with actual declarations and 33-constructor source; construction is not operation execution; seven file-operation classes now also submit separately with byte/size/ownership and error checks |
| `delme.c:176-204` | `ref-zig/advanced_usage.rst` | Buffer/file/update/eventfd/personality methods/helpers; probe raw helper also in supported_caps; distinguish captured credentials and application resource ownership |
| `delme.c:205-212` | `ref-zig/submission.rst` | Async table update now submitted separately with count-one CQE and restored fixed-read bytes; provided-buffer reads now expose selected IDs/bytes, exhaustion, group isolation, re-provision/removal counts and model-based ownership transitions; stable arrays/groups, not fixed-buffer registration |
| `delme.c:213-216` | `ref-zig/submission.rst` | sq_ready plus native array-capacity-minus-ready free-space expression; not completed-I/O count, single-producer discipline |
| `delme.c:217-226` | `ref-zig/submission.rst` | Native timeout/timeout_remove/cancel/link_timeout and timespec/tag/flags contracts; cancellation races and separate target CQEs retained |

## Findings and remaining acceptance gates

- Restored missing per-I/O `linux.RWF` / `sqe.rw_flags` prose in submission.
  This is distinct from SQE u8 dependency flags. SDK constants were inspected;
  nonzero-RWF operation effects are not attested by this document.
- The catalog is fully accounted for, including helpers absent from original
  reference declarations. Constructor-only coverage is still constructor-only.
- Sequential sparse/removal/replacement, closed application FD, async restore and
  unregistered-table effects now have exact fixed-read/CQE checks. Concurrent or
  partial multi-entry updates, broader signal/ordinary-enter policies
  and forced partial-I/O/state paths still need checks.
- All-line author note coverage closes the bookkeeping omission, not semantic
  acceptance. Independent review remains blocked; no review report exists.
  Whole-port mutation assessment, final review/fix/rebuild and fork push remain.
