# Registration and capability purpose comparison

Author comparison, **not independent acceptance**. Baseline:
`c9ee2424af02e4c1e4765088580107d5e17b826e`. Read both original chapters in full,
their 18 inventory blocks and surrounding text, both current chapters, native
consumer/helper bodies, generated declarations and installed Zig 0.17.0 bodies.
These originals contain declarations/layouts, not separate runnable programs.
No required conversion gap found in this subset; broader assurance is unclaimed.

## Original purpose → current contract

IDs below are original line numbers in `ref-liburing/advanced_usage.rst` (A)
or `ref-liburing/supported_caps.rst` (C). Current targets:
`ref-zig/advanced_usage.rst`, `ref-zig/supported_caps.rst`.

| ID | Preserved purpose / native difference | Actual consumer / limit |
|---|---|---|
| A:9 | Register vector-described ranges for fixed I/O; slice supplies count; `!void`, not C errno return | `fixed_buffers.zig`: four 512-byte ranges, WRITE tags1/2 then READ3/4; byte lengths36/35, indexes0–3. `reference-registration` alone only registers/unregisters this buffer table |
| A:31 | Unregister ranges without freeing application storage | Fixed tutorial waits for all four operation CQEs before unregister; broader failure/unwind paths unclaimed |
| A:51 | Register descriptor table for subsequent fixed-file operations | SQPOLL tutorial plus `reference_registration.readFixed`: ordinary READ + FIXED_FILE/table index, not READ_FIXED/buffer index |
| A:73 | Release table references, not caller descriptor ownership | Subsequent fixed-file READ fails with `-EBADF`; application source descriptor remains owned separately |
| A:93 | Replace descriptors starting at a table offset | Synchronous slot1 replacement; replacement process FD is closed/queried yet retained table reads its bytes. Async restoration is a distinct FILES_UPDATE CQE with res1. SDK synchronous wrapper discards nonnegative raw count; no partial multi-entry/racing-update assurance |
| A:115 | Attach eventfd for completion notification | Threaded tutorial consumes native u64 counter and separately tagged READ CQE/bytes; notification is not request identity or success |
| A:135 | Async-only notification excludes inline completions | Forced ASYNC NOP produces counter1 plus CQE0; deliberate inline-completion omission not forced/tested |
| A:155 | Detach eventfd; one attached counter per ring | Actual unregister and subsequent async registration; no post-detachment silence/duplicate-registration-error oracle |
| A:174 | Capture credentials and return an ID selected by SQE personality | `raw_ops.register_personality`: null/zero native registration, u16 ID; NOP with that actual ID completes0. No cross-user privilege claim |
| A:189 | Unregister captured credential ID | Native helper passes null and ID in nr_args after NOP CQE; stale-ID failure not tested |
| C:7 | Probe header type | Owned native fixed-capacity value replaces allocated pointer; no foreign free |
| C:8 | Last opcode, valid operation count, reserved fields and records | Native extern header +256 entries; zeroed SDK/helper storage, actual kernel query. C flexible allocation is not copied |
| C:20 | Per-operation probe type | Native opcode enum, u16 flags and reserved ABI fields |
| C:21 | Record layout/support flag | Raw2064-byte response independently decoded at literal offsets; support uses bit0, not any nonzero flag |
| C:35 | Query capabilities through an existing ring | `ring.get_probe()` returns value/error; tutorial compares all59 named results with independent raw registration |
| C:51 | Query without a caller-owned ring; destroy temporary ring | `raw_ops.probe()` creates ring, defers deinit and returns probe value; existing caller ring remains separate |
| C:69 | Test operation support | Native `is_supported(IORING_OP)` returns bool; both last_op/ops_len bounds and bit0 matter. Generated/snapshot negatives prevent constant-true inference; support is not operand success |
| C:85 | Low-level caller-storage probe registration | `raw_ops.register_probe` zeroes owned output, calls native REGISTER_PROBE with operation capacity256, not byte count; synchronous output loan, no invented SDK method |

## Surrounding purposes and evidence

- Original buffer/SQPOLL/syscall related links point to native tutorials and the
  shared registration chapter. Kernel introduction dates remain context, not
  version-based capability tests. Negative C errno/NULL results become native
  error unions or explicitly decoded raw results; current credential ownership
  and reserved/probe/count rules are retained.
- `tests/test_reference.py` asserts whole registered-file transition reports,
  independent before/after byte prefixes and unchanged inputs. Buffer registration
  itself is not an I/O oracle; `tests/test_examples.py` checks actual fixed-buffer
  file/stdout and threaded eventfd bytes, raw named probe flags and generated
  snapshot bounds. Current targeted replay is in
  `registration-purpose-verification.json`; full99/build/publication results stay
  historical. No native/manuscript/test/producer modification or new mutant claim.
- Author comparison does not settle all-original-purpose acceptance, concurrent
  ownership, every failure/kernel/architecture or mandatory independent review.
  Supported-host review blocker and personal-fork delivery remain open.
