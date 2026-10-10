# Completion audit

Status: **not complete**.

| Requirement | Current evidence | Missing |
|---|---|---|
| GitHub fork and local clone | Created `ahmedalhulaibi/loti-zig`; origin points to personal fork, upstream to `shuveb/loti` | Final converted commit pushed and verified |
| Enumerate original C/io_uring lines | 3,447 lines and 104 C blocks/declarations; regeneration and `--check` agree | Semantic disposition for each original reference |
| Rewrite every reference | Inventory identifies 61 function declarations, five type declarations, and 38 explicit C blocks | All 26 documents, complete API mapping, build commands, links |
| Recreate every example in Zig 0.17.0 | Nine native executables compile; eight CLI tests pass; two PBTs each completed 400 generated passing cases | HTTP server, all reference examples, lazy unused declarations, broader failure paths, mutation gate |
| Book verification | Original C edition built earlier; not Zig evidence | Zig HTML/EPUB builds, validator, content audit |

Do not infer completion from this table or from any single green gate. The final
audit must inspect each requirement against the resulting guide and executed code.

## Verified milestone: native tutorial core

Commands run from the repository:

```sh
python3 tools/inventory.py --check
zig fmt --check build.zig examples
zig build --summary all
LOTI_TEST_CASES=400 .venv/bin/python -m unittest tests.test_examples
```

- Compiler: `0.17.0`; build: **19/19** steps succeeded.
- Executables: `readv`, `raw-cat`, `cat`, `cp`, `probe`, `link`, `fixed-buffers`,
  `sq-poll`, `register-eventfd`.
- Native execution confirmed file bytes, hard-link rejection without truncation,
  linked failure cancellation, four fixed buffers, post-idle polling, and threaded
  eventfd notification. No io_uring sandbox restriction was encountered.
- Hypothesis statistics independently confirmed **400 passing generated cases**
  for each of the reader and copy properties. Explicit large/binary examples also
  ran. These properties do not replace the remaining reference/HTTP tests.
- Zig 0.17.0 reflection uses `field_names` and `@backingInt`; older reflection
  APIs were rejected by the compiler and corrected.
- LSP probes reported no errors on individual changed paths. Compiler results,
  not the LSP's empty output, establish actual example type checking.
- `RawRing.dontFork` is not yet called by a compiled reference example. It is
  explicitly **not** counted as verified merely because `raw-cat` builds.

## Next work

1. Recreate and test the asynchronous HTTP example.
2. Map all original API references, including scratch-only helpers, to real Zig
   0.17.0 declarations or executable raw ABI paths. Compile every included snippet.
3. Rewrite every chapter and navigation entry; remove stale source/build artifacts.
4. Run the complete execution and mutation gates, build the Zig EPUB, audit all
   requirements against actual artifacts, and push the finished fork.
