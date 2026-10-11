# Native type-purpose comparison

Author body/SDK audit of all22 type rows;19 generic scopes replaced, three prior
CQE/probe contracts retained. Not independent or all128-block semantic acceptance.
Original selectors/text are checked against immutable Git objects in
`type-binding-original-selectors.json`; names are token matches, not type parsing.

| Original | Actual consumer/purpose | Boundary |
|---|---|---|
| `io_uring` | `reference_setup.main`:owned SDK value/init/deinit | Auto layout; not kernel/liburing ABI to cast |
| `io_uring_sq` | Explicit `*SubmissionQueue`/SQ8 view | Local counters versus published mapped tail; auto layout |
| `io_uring_cq` | Explicit `*CompletionQueue`/CQ32 view | Readiness/copy/ack differ; auto layout |
| `io_uring_params` | Zeroed CQSIZE inputs/returned entries/features | Kernel extern120; input/output, not owner |
| `io_sqring_offsets` | `RawRing.map` adds returned SQ byte offsets | Kernel extern40; offsets, not pointer fields |
| `io_cqring_offsets` | Correct shared/separate CQ region checked | Kernel extern40; offsets, not queue objects |
| `io_uring_sqe` | `reference_submission.emit`:33 prepared records | Ordinary extern64; mixed INPUT batch stays unsubmitted |
| `io_uring_cqe` | `reference_buffers`:tag/res/flags/selected ID | Existing EOF0+BUFFER/ID consumption contract; not CQE32 |
| `io_uring_probe` | `probe`:owned256-entry value/header bounds | Existing2064-byte/native-endian scope, not flexible allocation |
| `io_uring_probe_op` | Native8-byte entry/enum/u16 flags | Existing bit0/both bounds/59 names scope, not opcode success |
| `iovec` | `reference_files`:two mutable read/const write vectors | Extern16 each; descriptor+bytes retained; SQE len counts vectors |
| `__kernel_timespec` | `reference_signals`:timers/basic/EXT_ARG waits | Extern16/i64 sec+nsec; timer CQE versus blocking-call loan |
| `sigset_t` | Actual temporary/blocked/null/handler masks | Current raw kernel8, not glibc/musl1024-bit signal-set ABI |
| `off_t` | `reference_rwf.position`:explicit `linux.off_t` | Signed i64 seek input; raw u64 return requires errno decode |
| `loff_t` | `reference_splice.transfer`:u64 offset values | -1 bit pattern/current sentinel; no borrowed offset pointers |
| `mode_t` | `reference_files`:u32 open argument/0o600 | Not u16 `Statx.mode` or u64 `OpenHow.mode`; no permissions oracle |
| `size_t` | `webserver`:usize slice lengths/remaining progress | Current word64; bounded narrowing to opcode-specific u32 SQE len |
| `msghdr` | `reference_messages`:mutable receive/const send headers | Raw Linux extern56; nested loans; usize fields differ from some libc ABIs |
| `sockaddr` | `reference_connect`:stable IPv4 peer input | Generic header/concrete family layout/network order; length value |
| `socklen_t` | `reference_accept`:u32 initialized capacity pointer | Returned full length/truncated bytes; not CONNECT input semantics |
| `statx` | `reference_files.statFile`:zeroed output/mask checks | Extern256; read TYPE/SIZE only when present; result0 is not file size |
| `open_how` | `reference_raw`:local extern/helper/owned returned FD | Flags/mode/resolve:u64;24 bytes; how/path retained through CQE |

## Evidence boundaries

- `type-binding-reflection.zig`:stateless exact0.17 compiler diagnostic, not an
  installed26th example or kernel exercise. Literal expectation pins current
  Linux/x86_64/no-libc widths/layouts/constness; no other-architecture assurance.
- Existing native byte/cursor/mask/address/control/cleanup contracts corroborate
  the relevant consumers. They do not test every type field/flag/error/race.
- File tests assert bytes/size, not actual permissions/umask effects. No inference
  of a permissions oracle from a compiled0o600 argument or mode-bearing fields.
- Initial diagnostic used obsolete `Pointer.is_const`; compiler rejected it.
  Actual0.17 `Pointer.attrs.const` was read and used; failure preserved/excluded,
  not a native example defect or valid mutant.
- Reflection amendment adds exact `OpenHow.mode`/raw-message length types;
  size alone cannot prove their widths. Original helper/expectation/core/mutants
  and full99 checkpoint retained; no changed19-row fixture/test or weaker oracle.
  Final13 producer kills replace initial13, not26.
- Whole19-entry fixture preceded producer change. Thirteen producer damages pass
  generation/freshness but fail scopes; exact restoration. Hashes are author
  provenance, not ACL seals/verifier-agent or all-original-purpose acceptance.

Mandatory independent review host remains blocked; no retry/fallback/report,
push or goal completion. Other original-purpose comparisons/final acceptance
remain open; these type comparisons alone do not close the full port.
