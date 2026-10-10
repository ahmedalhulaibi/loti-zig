# Lord of the io_uring — Zig edition

**Migration in progress. Not yet a complete Zig edition.**

Zig 0.17.0 adaptation of [Shuveb Hussain's guide](https://github.com/shuveb/loti).
The edition uses `std.os.linux.IoUring` and native Linux syscalls. Examples live
in this repository; no separate example repository or external ring library is
required. Original MIT licence and attribution are retained.

See `conversion/plan.md`, `conversion/source-inventory.json`, and
`conversion/audit.md` for scope, original line enumeration, and actual progress.

## Verify the inventory

```sh
zig version                         # must print 0.17.0
python3 tools/inventory.py --check
```

Build and execution instructions will be added with the verified examples.
