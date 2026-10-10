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
LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
make html
make epub
.venv/bin/python tools/verify_epub.py --report conversion/epub-verification.json
java -jar "$EPUBCHECK_JAR" _build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub
```

Use [EPUBCheck 5.2.1](https://github.com/w3c/epubcheck/releases/tag/v5.2.1);
set `EPUBCHECK_JAR` to its installed jar. The full Sphinx builds use warnings as
errors. Output: `_build/html/index.html` and
`_build/epub/Lord-of-the-io_uring-Zig-0.17.0.epub`. The EPUB needs no Calibre,
external fonts, JavaScript or DRM. Code reflows on small displays.

Publication checks verify all 27 chapters in reading order/navigation, 104 literal
blocks against Sphinx source, five byte-identical illustrations, licence and local
links. Negative tests reject nine damaged-archive classes. These checks **do not**
prove semantic completeness or satisfy independent review.

`conversion/source-inventory.json` preserves 3,447 original matched lines and
104 original blocks/declarations. `reference-map.json` maps 98 native bindings;
`chapter-map.json` maps original/new paths. Line/block semantic disposition,
broader failure/state checks, bounded source mutation verification and independent
review remain open. See `conversion/audit.md` and `conversion/review-blocker.md`.
The goal is not complete; final converted commits have not been pushed.

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
zig-out/bin/webserver public 8080
zig-out/bin/reference-setup input.txt
zig-out/bin/reference-completion
zig-out/bin/reference-registration input.txt
zig-out/bin/reference-submission input.txt
zig-out/bin/reference-raw input.txt
```

`reference-submission` executes constructors but deliberately does not submit its
incompatible mixed operands. Other reference/tutorial programs provide separate
operation-effect evidence. The HTTP server is loopback-only and is not production
software. Consult each chapter for capabilities, lifetimes and limits.
