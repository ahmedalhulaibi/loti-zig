# HTTP tutorial purposes

Base `2af592a`; red oracle-gap reproduction `ded4581`. Full original649-line
`tutorial/webserver_liburing.rst`, current150-line `tutorial/webserver.rst`,
385-line native server and HTTP boundary bodies read. Eleven blocks plus complete
surrounding prose. Author comparison, not independent acceptance.

| Original selector | Preservation / correction |
|---|---|
| `tutorial/webserver_liburing.rst:18` | Complete runnable static server: loopback listener, asynchronous ACCEPT/RECV/file READ/SEND and one tagged completion loop. GET/index/MIME/length/error responses and retained request state. Modern scalar operations replace the legacy5.5 READV/WRITEV choice; metadata/open remain synchronous, file data becomes asynchronous. No external library. |
| `tutorial/webserver_liburing.rst:472` | Native build/run/root/port and second-terminal curl instructions; included public/index.html. Real readiness reports actual port, including kernel-selected0. No obsolete CMake/kernel-version success proxy. |
| `tutorial/webserver_liburing.rst:490` | Submit/copy-consume/dispatch loop; tag0 accept, slot+1 clients, exactly one outstanding request per occupied slot. Current phase selects handling; no heap pointer cast or additional CQ acknowledgement. Socket error is isolated, not server-wide fatal. |
| `tutorial/webserver_liburing.rst:537` | Native ACCEPT with CLOEXEC and null unused peer-address outputs. Successful CQE supplies a new socket; actual server re-arms acceptance. Separate ACCEPT reference covers address value-result semantics. |
| `tutorial/webserver_liburing.rst:553` | Stable Client slots hold socket/file descriptors, request/header/body storage, lengths and progress. Five phases refine accepted→request→response by adding asynchronous file loading and separate header/body sends. |
| `tutorial/webserver_liburing.rst:568` | Accepted socket starts reception and next accept is queued.32 occupied slots reject/close newcomers; no overload guarantee. Arrival order does not identify the client. |
| `tutorial/webserver_liburing.rst:578` | RECV uses only the remaining8192-byte request range. Accumulate initialized bytes, not zero-filled C strings; wait for full terminator. Legacy single-iovec READV choice is not needed by the target SDK/kernel. |
| `tutorial/webserver_liburing.rst:597` | Parse complete received request or close on EOF; incomplete EOF also retires ownership. Body/empty response fixtures are not binary/zero-length RECV evidence. New empty and unfinished TCP half-close plans exercise genuine request EOF. |
| `tutorial/webserver_liburing.rst:611` | Confined open/stat, stable bounded owned body, asynchronous complete loading and exact status/server/MIME/length/terminator bytes. Original5 header vectors+body become one header buffer and retained body with two SEND phases, not an HTTP scatter/gather implementation. Actual vectored file/message consumers remain elsewhere in edition. Original excerpt's set_headers typo and sendfile/POST comments do not describe its actual code. |
| `tutorial/webserver_liburing.rst:623` | Native SEND retains storage and resubmits address-relative remainder after actual positive short completion. NOSIGNAL is operation rw_flags, not SQE flags. Actual bounded body short before drain/reset and exact wire/recovery are separately tested; not forced header/vector shorts or SIGPIPE delivery. |
| `tutorial/webserver_liburing.rst:636` | Release retained body and close socket only after completion/error; slot becomes reusable. New default-mode contract observes whole wire through TCP EOF and process-private socket/file census before server exit. A write-half shutdown is not descriptor close. |

## Prose and changed design

- Preserve ZeroHTTPd/Shuveb origin, process-model link and original screenshot;
  screenshot explicitly is not a Zig execution capture. Native source is included
  from the compiled repository file. Adaptation credit/licence remain elsewhere.
- Original copy_file_contents actually used synchronous open/read/close despite
  its sendfile comment. Native loading uses READ; no zero-copy/performance claim.
  Native openat2/metadata are explicitly synchronous. No all-I/O-exclusive claim.
- Original implementation handled GET only despite its POST comment. Native
  method matching is case-sensitive; HTTP/1.0/1.1 request lines, one decode,
  query exclusion/trailing index and confined relative lookup are explicit.
  No request-body/header validation, TLS, keep-alive, streaming or snapshot claim.
- Contiguous headers/separate body are a disclosed adaptation, not preservation
  of six-vector socket output. READV/WRITEV and SENDMSG/RECVMSG vector purposes
  have actual native consumers in reader/file/message chapters. Partial body
  progress is established here; no header-vector progress experiment is claimed.
- Nine original extension spellings/case folding plus unknown fallback are measured
  over real default-mode peers. Finite size cases4MiB−1/4MiB/4MiB+1 establish
  the documented inclusive limit/413; expected whole bodies/headers/EOF, unchanged
  source files and no retained target FD. Not valid image-format decoding.
- Ctrl-C uses normal OS termination, not the original signal handler's unsafe
  library teardown. Owned test groups terminate after assertions. No graceful
  cancellation/drain, heap-allocation census or complete failure-unwind proof.

## Verifier gap, not a native defect

Current native release code already closes descriptors. Two isolated compiled
default-only variants passed all four unchanged original HTTP boundary tests:
omit close; shutdown write then omit close. Content-Length/Connection header
checks and observer-mode closure checks did not establish default-mode retirement.
Red records preserve successful old tests, native/spec hashes and compiler logs.

New table-driven boundary contract owns its server and peers. Five plans compare
complete wire through EOF; then child-only procfs socket identities must equal
the original listener and owned regular-file inode count must be0. A later GET
proves survival after request EOF. Sources remain byte-identical.5-second owned
EOF deadline is a bounded missing-close assertion, not a compiler/runner timeout.
Hashes are author provenance, not ACL seals or independent verifier acceptance.

Two native assertion kills: missing close fails EOF; shutdown-only passes EOF but
fails descriptor census. Each1 failure/0 errors/skips; seven restored HTTP
contracts pass. Diagnostic-only runner amendments retain the initial report/log;
amended two replace, not add to initial two. No native implementation/prose change.

A final live index check found another artifact defect: the prior link16-byte
repair left the canonical line index's link target SHA stale. Full102 did not
prove that CLI freshness. Red `a9539f5` preserves the original report/Git blob and
CLI failure. Regenerate only that target digest; all128 blocks/3618 selectors,
567 outside lines, notes and other targets are identical. Two existing index
contracts and the current CLI pass after repair; no new mutant/native claim.

## Acceptance boundary

Full102/zero failures-errors-skips/170.813s;16 properties×400 generated valid
cases. New EOF contract is finite, not a17th property. Suite invokes make epub;
post-suite current archive is separately verified.13 new native MIME/limit
plans are bounded additional observations, not extra suite tests. Source/native
inputs are unchanged from prior accepted51-step/strict builds; those receipts
remain historical rather than relabelled as new runs. Current81 reader reflows
and EPUBCheck separately cover the post-suite archive; not device acceptance.

All seven purpose reports now select128/128 original blocks without duplicates.
This is author comparison coverage, not whole-port semantic/independent acceptance.
Wider original prose/explicit requirements, final fork state, independent review
and accepted delivery remain open. No unsupported reviewer retry/fallback, push
or goal completion. No all-status/permission/umask/durability, short RECV CQE
counts, header/vector shorts, concurrency races or all kernel/error/unwind proof.
