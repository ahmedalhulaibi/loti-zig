# Lord of the io_uring — Zig 0.17.0

**Draft edition. Required independent review and final conversion audit remain open.**

Native Zig adaptation of [Shuveb Hussain's guide](https://github.com/shuveb/loti).
All 26 original documents have rewritten counterparts; `license.rst` adds the
unchanged MIT licence. Tutorial and reference programs live here, using
`std.os.linux.IoUring` and native syscalls without libc or an external ring library.
Original attribution and illustrations remain.

## Build and check

```sh
zig version                         # exactly 0.17.0
zig build
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
python3 tools/inventory.py --check
python3 tools/reference_map.py --check
python3 tools/reference_docs.py --check
python3 tools/check_line_dispositions.py --check
LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
make html
make epub
.venv/bin/python tools/verify_epub.py --report conversion/epub-verification.json
.venv/bin/python tools/check_reader_layout.py --report conversion/reader-layout-verification.json
java -jar "$EPUBCHECK_JAR" _build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub
python3 tools/check_block_devices.py --report conversion/block-device-verification.json
```

Reader-layout tests also need Node **26.8.1**, npm Playwright **1.64.0** and system
Chromium. Install exact tooling with `mise install node@26.8.1 npm:playwright@1.64.0`;
`--playwright-module PACKAGE_DIR` and `--browser EXECUTABLE` select explicit paths.
The driver keeps Chromium's sandbox enabled, disables document JavaScript and
network access, and measures all spine documents at 320/600/800 CSS pixels. This
is browser reflow evidence, **not Supernote-device or paginated-reader assurance**.

Use [EPUBCheck 5.2.1](https://github.com/w3c/epubcheck/releases/tag/v5.2.1);
set `EPUBCHECK_JAR` to its installed jar. The full Sphinx builds use warnings as
errors. Output: `_build/html/index.html` and
`_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub`. The EPUB needs no Calibre,
external fonts, JavaScript or DRM. Code reflows on small displays.

The complete suite also requires x86_64 Linux, writable `/dev/kvm`, QEMU,
`/usr/lib/initcpio/busybox`, `/usr/bin/cmp` and a guest kernel with built-in
virtio block support. The VM verifier accepts `--kernel` and `--busybox` paths;
recorded lab: QEMU 11.1.1/Linux 7.2.3-arch1-3. All disks are generated files,
attached read-only. No host storage device or root host operation is used.

Publication checks verify all 27 chapters in reading order/navigation, 120 literal
blocks against Sphinx source, five byte-identical illustrations, licence and local
links. Negative tests reject nine damaged-archive classes plus 19 source-literal
policy and four rendered-language damages, including matched stale artifact pairs.
All literals have explicit Zig/console/JSON/text labels matching packaged classes;
checks reject bounded C-import/helper/compiler markers. Ordered source fidelity
also checks 359 resolved narrative paragraphs (references/typography resolved;
formatting whitespace folded), rejecting six stale/missing/duplicated/reordered
prose damages while accepting whitespace-only formatting. It excludes structural
TOC compact paragraphs/rubrics/captions, not code literals. Three whole bindings
and two independent reader paragraphs qualify ordinary versus SQPOLL return
counts. These checks are not language parsing, all-reference semantic acceptance
or **independent review**.

`conversion/source-inventory.json` preserves 3,618 original matched lines and
128 source blocks/declarations: 120 C blocks/declarations and eight output literals.
This includes 16 unlabelled syscall C literals missed by the first scanner;
`tests/test_inventory.py` cross-checks all implicit literals with Docutils and
checks every captured line against the immutable source. `reference-map.json`
maps 99 native bindings;
`chapter-map.json` maps original/new paths. Line/block semantic disposition,
broader failure/state checks, bounded source mutation verification and independent
review remain open. See `conversion/audit.md` and `conversion/review-blocker.md`.
The goal is not complete; final converted commits have not been pushed.

Author notes index all 128 blocks and 3,618 matched lines; this is not semantic
acceptance. Native `cp` now sizes
read-only block-device input with `BLKGETSIZE64`; output must remain a regular
file. An isolated VM checks all three readers and copy against four disposable
disks. Streaming stdout also preserves chunks when redirected to a regular file.
The raw mapper now selects shared or separate SQ/CQ mappings. The reference
exercises both strategies with actual I/O, fork exclusion and page/descriptor
teardown checks. Forced separate mode is not a historical-kernel attestation.
Five private-descriptor seccomp mmap failures also check partial unwind and
caller FD ownership against procfs and independent syscall traces. This optional
mode requires native x86_64/procfs/seccomp; its tests require strace.

## Run examples

```sh
zig-out/bin/readv input.txt
zig-out/bin/raw-cat input.txt
zig-out/bin/cat input.txt
zig-out/bin/cp source.bin destination.bin
# Optional owned-file split; requires 2–16384 source bytes and 0<LIMIT<size.
zig-out/bin/cp source.bin destination.bin --short-write 1
# Controlled error: restore/query process limits before returning the read error.
zig-out/bin/cp source.bin destination.bin --short-write 1 --fail-read
zig-out/bin/link linked.txt
zig-out/bin/link linked.txt --fail-read
zig-out/bin/fixed-buffers fixed.txt
zig-out/bin/sq-poll polling.txt
zig-out/bin/sq-poll polling.txt --observe # owned output; observed idle flags/wakeups
zig-out/bin/register-eventfd input.txt
zig-out/bin/probe
zig-out/bin/probe --raw > probe.bin
zig-out/bin/probe --snapshot probe.bin
zig-out/bin/webserver public 8080
zig-out/bin/reference-setup input.txt
zig-out/bin/reference-setup input.txt --separate-mappings
zig-out/bin/reference-setup --mapping-failure separate-sqes
zig-out/bin/reference-completion
zig-out/bin/reference-completion 0 1 3 8 1
zig-out/bin/reference-signals
zig-out/bin/reference-signals --ordinary
zig-out/bin/reference-files input.txt new-output.bin
zig-out/bin/reference-rwf input.bin
zig-out/bin/reference-splice input.txt
zig-out/bin/reference-poll
zig-out/bin/reference-poll arm write wait drain arm cancel missing quiet
zig-out/bin/reference-epoll
zig-out/bin/reference-epoll add write wait modify wait modify wait delete drain close wait
# PORT must belong to a disposable 127.0.0.1 listener owned by the caller.
zig-out/bin/reference-connect PORT
# Prints JSON ready; caller then connects one owned client to its loopback port.
zig-out/bin/reference-accept 16 both
zig-out/bin/reference-messages input.txt 3
zig-out/bin/reference-buffers input.txt
zig-out/bin/reference-buffers input.txt read read provide read
zig-out/bin/reference-buffers input.txt --zero-result
zig-out/bin/reference-buffers input.txt --zero-result --fail-eof
zig-out/bin/reference-registration input.txt replacement.txt
zig-out/bin/reference-submission input.txt
zig-out/bin/reference-raw input.txt
```

`reference-registration` takes two regular input files. It checks sparse/fixed
slot reads, replacement after closing the application descriptor, asynchronous
restoration and removal/unregistration failures. It reports the first 64 bytes;
this is not a full-file reader or concurrent table-update model.

`reference-submission` executes constructors but deliberately does not submit its
incompatible mixed operands. Other reference/tutorial programs provide separate
operation-effect evidence. The HTTP server is loopback-only and is not production
software. Consult each chapter for capabilities, lifetimes and limits.

Completion operands are at most 32 destination capacities (0–8), with enough
total capacity to drain eight NOP CQEs. The default is `0 1 3 8 1`. The reference
checks full-SQ rejection/state preservation, populated zero/singleton/batch
nonblocking consumption, and CQ physical wrap. Model-based tests check exact
head/readiness transitions; u32 wrap, overflow and concurrent consumers remain open.

`reference-buffers INPUT [COMMAND ...]` executes provided-buffer selection and
ownership. Nonempty regular input is read at offset zero into 64-byte slots.
Model-based command tests verify flags/IDs, exhaustion, group isolation,
recycling, actual removal counts and final cleanup. Selected groups contain one
buffer each. Optional `--zero-result` (stable regular1–4097 bytes/no extra commands)
observes positive-length EOF0 with BUFFER/ID257, actual remove0 and exhaustion.
Requested length0 at offset0 reads the legacy64-byte buffer capacity, not ordinary
zero-byte I/O; whole bytes/poison/SQEs/CQEs/cursor/final remove1 are checked.
Optional `--fail-eof` produces a real invalid-FD READ CQE; early validation stops
after two submits, then closes the ring before the owned input (no pool reuse).
Concurrency, pbuf-rings, multishot and cancellation races remain open.

`reference-rwf INPUT` uses a private memfd: actual RWF_APPEND bytes and explicit/
current cursor behavior, ordinary overwrite proving flags are not sticky,
unsupported READ/WRITE flags, unchanged read poison and queried FD ownership.
Regular input is 1–4097 bytes; no external output, physical durability or other
RWF/filesystem/concurrency assurance. Only installed SDK constants are named.

`reference-files INPUT NEW_OUTPUT` submits actual OPENAT, READV/WRITEV,
FALLOCATE, STATX, full/data-only FSYNC and CLOSE requests. It rejects existing
output, copies exact input bytes, adds 4,096 zero bytes, checks async metadata,
closes/checks FD ownership, reopens/hashes actual output, and receives seven
invalid-descriptor CQEs. Source must be regular; final symlinks are rejected.
No physical/crash durability or atomic replacement is claimed. A later failure
can leave its newly created partial output; forced short writes remain open.

`reference-signals` owns SIGUSR1 in a fresh process. It pre-queues a blocked
thread-directed signal, checks real interrupted/blocked/null-mask waits, exact
mask restoration, handler masks/counts, retained queued NOP and actual recovery
CQE. It restores/checks the original kernel action and mask. `--ordinary` uses
basic enter's signal-set ABI, submitted guard/expiration timers and distinct
TIMEOUT_REMOVE target/remover CQEs; blocked/null waits do not submit the NOP.
Actual syscall/handler/return-mask observations reject ten damaged traces. Neither
mode models concurrent senders, general restart policy, IOPOLL or timer races.

Probe raw output is a 2,064-byte native-endian ABI snapshot, not JSON. Snapshot
listing uses the same SDK lookup as the live listing. Independent raw decoding
checks all named support flags; mixed/generated snapshots check false bits and
both header bounds. A supported opcode still does not guarantee operand success.
