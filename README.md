# Lord of the io_uring — Zig edition

**Migration in progress. Not yet a complete Zig edition.**

Zig 0.17.0 adaptation of [Shuveb Hussain's guide](https://github.com/shuveb/loti).
The edition uses `std.os.linux.IoUring` and native Linux syscalls. Examples live
in this repository; no separate example repository or external ring library is
required. Original MIT licence and attribution are retained.

See `conversion/plan.md`, `conversion/source-inventory.json`, and
`conversion/audit.md` for scope, original line enumeration, and actual progress.

## Build the migrated tutorial core

```sh
zig version                         # must print 0.17.0
zig build
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.lock
LOTI_TEST_CASES=400 .venv/bin/python -m unittest discover
python3 tools/inventory.py --check
python3 tools/reference_map.py --check
.venv/bin/python tools/check_chapters.py  # four converted chapters only
```

The ten tutorial programs and five reference programs compile and run. Four source
chapters are rewritten and pass a scoped Sphinx warnings-as-errors check; 22
chapters and full navigation/API prose still need conversion. The Zig EPUB is
pending. `conversion/reference-map.json` records 98 native bindings and their
verification scope. Independent review is blocked by the subagent host; see the
audit. Passing the current tests does **not** mean the complete guide is converted.

```sh
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
