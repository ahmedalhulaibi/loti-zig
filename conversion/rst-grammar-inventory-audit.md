# Original RST grammar cross-check

Source354f629;originalc9ee2424. Scope:requirement2 block enumeration,not independent
teaching-purpose acceptance. Sphinx8.2.3/Docutils0.21.2/locked Python3.13.15.

## Actual result

- All26 original RSTs parsed from immutable Git bytes;7 original images copied
  into the owned fixture. No original config/plugin execution or external fetch.
- Exactly128 unique inventory spans matched:62 literal blocks,61 C function
  declarations,5 C struct declarations. Literals:39 explicit/23 implicit. Earlier
  inventory repair added16 implicit literals;that was not the total count.
- All62 complete literal bodies match their original span suffix under actual
  Docutils input normalization:tabs8/trailing-whitespace removal/vertical-space
  conversion,then common-indent removal. Not raw-byte or C-semantic equivalence.
- No unmatched/missing block;Sphinx status0/warnings0 with a generated minimal
  config and inline man-role stub. Stub does not validate manual links.
- Four owned negative inputs each omit one explicit literal,implicit literal,
  function declaration or struct declaration. Each exits1 with the corresponding
  parser mismatch/127 matched spans. Controls,not formal tests/native mutation kills.

## Preserved failures

Initial plain Docutils lacks Sphinx C-domain;wrong guessed io_uring_cqe filename
failed before correction to actual cqe.rst;overlarge declaration tally truncated.
First Sphinx comparison paired128 spans but found10 body whitespace mismatches and
172 role errors. Inspecting actual string2lines established normalization;man-role
adapter corrected. Initial source/helper/receipt/log and diagnoses retained;no
canonical inventory or manuscript change to force a pass.

## Evidence / limits

`rst-grammar-inventory-verification.json` pins source/config/helper/versions,all33
original fixture inputs,full128-row receipt and4 control receipts. Owned roots:
`_build/verification/rst-grammar-crosscheck.nym5coj2/` final,
`rst-grammar-crosscheck.4qv4924n/` initial,`rst-grammar-controls.f18ch925/` controls.

This challenges block-boundary enumeration with a grammar different from the
production text scanner. It does not prove all lexical spellings,non-RST reference
coverage,converted semantics,lifetimes or original purposes. C declarations are
not separate applications. All226 prior selected edition inputs/archive5739833e
unchanged;no formal/full/cold/native/publication replay,new kills or delivery.
HTTP defect/retirement,sealing,provider-blocked author qualification and independent
acceptance remain open. Goal incomplete.
Six-path LSP:4 clean;fail-closed JSON loading and exact original Fulll filename
marked false-positive. Stale review graph used only for an outline;live source read.
