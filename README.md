# Lord of the io_uring — Zig 0.17.0

**Draft edition. Required independent review and final conversion audit remain open.**

Native Zig adaptation of [Shuveb Hussain's guide](https://github.com/shuveb/loti).
All 26 original documents have rewritten counterparts; `license.rst` adds the
unchanged MIT licence. Ten tutorial and five reference programs live here, using
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
java -jar "$EPUBCHECK_JAR" _build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub
python3 tools/check_block_devices.py --report conversion/block-device-verification.json
```

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

Publication checks verify all 27 chapters in reading order/navigation, 105 literal
blocks against Sphinx source, five byte-identical illustrations, licence and local
links. Negative tests reject nine damaged-archive classes. These checks **do not**
prove semantic completeness or satisfy independent review.

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

## Run examples

```sh
zig-out/bin/readv input.txt
zig-out/bin/raw-cat input.txt
zig-out/bin/cat input.txt
zig-out/bin/cp source.bin destination.bin
zig-out/bin/link linked.txt
zig-out/bin/link linked.txt --fail-read
zig-out/bin/fixed-buffers fixed.txt
zig-out/bin/sq-poll polling.txt
zig-out/bin/register-eventfd input.txt
zig-out/bin/probe
zig-out/bin/probe --raw > probe.bin
zig-out/bin/probe --snapshot probe.bin
zig-out/bin/webserver public 8080
zig-out/bin/reference-setup input.txt
zig-out/bin/reference-setup input.txt --separate-mappings
zig-out/bin/reference-completion
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

Probe raw output is a 2,064-byte native-endian ABI snapshot, not JSON. Snapshot
listing uses the same SDK lookup as the live listing. Independent raw decoding
checks all named support flags; mixed/generated snapshots check false bits and
both header bounds. A supported opcode still does not guarantee operand success.
