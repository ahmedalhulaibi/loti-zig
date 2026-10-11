# Clean local consumer — author verification

Source `244cc2a`, tree `d574df1b7493e2db476d90515c87c86bdc3c6e84`.
No native/book/test/fixture edit. Independent acceptance and delivery remain open.

## New boundary

Local Git clone, initially clean, with no copied `.venv`, `.zig-cache`, `zig-out`
or `_build`. Empty owned global cache plus fresh local cache; exact Zig0.17.0.
All25 executables compile **uncached**;51/51 steps succeed with two jobs under
bounded user scope. All4 inventory/map/declaration/index CLIs pass from the
relocated checkout. This checks tracked-source/consumer closure, not GitHub
delivery or a second operating system/compiler environment.

Existing pinned interpreter reused explicitly; all26 locked package versions
checked. A temporary `.venv` symlink enables unchanged README test commands;
the directory-only ignore pattern does not ignore that symlink. It is a known
untracked prerequisite fixture, removed after tests. Shared environment untouched;
no package installation or dependency bootstrap claimed. Source tree is clean
before and after; original226 selected hashes remain exact.

## Gates

`clean-consumer-verification.json`; artifacts/logs in
`_build/verification/clean-consumer.Yt50Fiy4/`.

- Full103/zero failures-errors-skips/175.449s;16 properties×400 valid cases.
  Runner only reanchors ROOT/routes output; no expectation or historical receipt
  change. Initial strict HTML/EPUB retained separately from post-suite archive.
- Actual final consumer archive:27 chapters/121 literals/368 paragraphs; exact
  licence/assets/order/local links;81 reflows/zero violations; EPUBCheck5.2.1
  zero messages. All28 XHTML bodies, including navigation, byte-match the original
  checkout's package. Archive SHA differs; no archive-bit determinism claim.
- Legacy build-runner source path was absent; actual `zig env` confirms the cache
  environment override. Initial system-Python version audit failed on alabaster;
  locked-interpreter replay verifies all26 versions. Lost polling handles resolved
  from completed logs/receipts/current hashes; none of these is a test kill.
- JSON spelling diagnostic for exact package name `certifi` marked false-positive;
  dependency identity preserved;no inline suppression. Other changed Markdown clean.

292 historical kills unchanged. Clean consumers do not establish complete
original-purpose/line semantics or waive independent agent verification. Next
required acceptance input is an owner-approved independent verification method
consistent with the direct-review preference. No new reviewer, push, PR or release.
