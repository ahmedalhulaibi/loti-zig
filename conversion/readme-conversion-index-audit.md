# Reader-guide conversion index / cleanup disclosure

Source611379c;only README changed among prior226 selected edition inputs.
README now links canonical inventory,historical/inline supplements,grammar check,
native binding/chapter maps and current completion audit. It distinguishes
canonical3618/128 from expanded union3641 and added16 vs total23 implicit literals.
Entry-page warning names the reproduced fatal late-ACCEPT omission and unverified
pending-I/O retirement;not a repair or production recommendation.

## Scoped verification

- Existing tests.test_readme_publication:1 test/0.647s/no errors,failures or skips.
  Covers statistics/commands and invokes verify_epub on the unchanged archive;
  does not cover new navigation or lifecycle cleanup.
- Owned checker compares all9 relative link label/target pairs exactly,checks
  every target is tracked/in-repo,and matches the whole warning paragraph.
  Old guide,wrong inline-catalog link and false retirement-guarantee controls
  reject specifically. Reader-fidelity controls,not formal tests/native kills.
- Four canonical CLIs pass:3618/128/567,76 source APIs/99 native bindings,
  13 native includes. Canonical and historical catalog targets unchanged.
- README is Markdown;Sphinx source suffix is .rst. No book/manuscript/native/test
  change. Archive5739833e identical;no rebuild/reflow/EPUBCheck/full/cold replay.

`readme-conversion-index-verification.json` records fresh226 source pins without
repinning historical receipts,README7a2a5117→0458782c,artifact/helper hashes and
limits. Owned evidence:`_build/verification/readme-conversion-index.3lsexzer/`.
Only README changed;225 prior inputs unchanged. Two-path LSP:README clean;helper
fail-closed JSON load marked false-positive. Stale graph used for outline only;
actual existing test body read. No new test author/reviewer/provider retry or bypass.

HTTP resource/retirement repair,protected tests,independent completeness/meaning
acceptance,final audit and personal-fork delivery remain open. Goal incomplete.
