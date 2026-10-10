# Zig edition work contract

## Outcome

Fork `shuveb/loti` to `ahmedalhulaibi/loti-zig`, cloned at
`$HOME/workspace/va/loti-zig`. Convert the complete guide and every example to
Zig **0.17.0**. Preserve attribution, MIT licence, Linux ABI semantics, chapter
coverage, illustrations, and the teaching purpose of each example.

## Deliverables and evidence

| Requirement | Artifact | Completion evidence |
|---|---|---|
| 1. GitHub fork and local clone | Git remotes and GitHub parent | `gh repo view`, `git remote -v`; final commit pushed to own fork |
| 2. Every original C/io_uring line | `source-inventory.json`, `source-inventory.md` | Regenerate from pinned upstream commit; enumerate line numbers and text, including complete C blocks |
| 3. All references updated | All 26 source documents, build commands, project metadata | Review every document against inventory; no stale C domains, C snippets, C build instructions, liburing calls, or old example URLs |
| 4. Every example recreated | `examples/*.zig`, reference examples, build graph | Exact Zig version gate; compile every displayed example; execute each tutorial's demonstrated behaviour |
| Complete reference coverage | `reference-map.json`, reference chapters | Map every original C function/type to a real Zig API or an explicit raw Linux operation; compile calls, verify signatures against installed 0.17.0 stdlib |
| Reader-facing book | Sphinx HTML and DRM-free EPUB | Warnings-as-errors build; EPUBCheck; audit chapter order, images, licence, and code inclusions |
| Verification | Boundary tests and `audit.md` | File byte preservation, linked completions, buffers, eventfd, polling, feature probe, HTTP behaviours; genuine execution, not compile-only proxies |

## Boundaries

- Work only in this fork and its generated book output. Do not change other repos.
- Use native `std.os.linux.IoUring` and Linux syscalls. No C imports, libc, or
  liburing dependency. Explain Linux ABI constants as Zig declarations, not C code.
- Keep conceptual discussions that apply to io_uring. Rewrite language-specific
  explanations, examples, references, installation, and troubleshooting.
- Do not claim a Zig API exists if 0.17.0 lacks it; show the raw ABI path instead.
- Keep examples small, but preserve their behaviour. No placeholder programs,
  silently omitted operations, blanket skip gates, or passing exit-code proxies.
- Pin tool dependencies. Include the original licence. Publish only to the named
  personal fork; do not submit upstream contributions or create a release.

## Iteration

Inventory first; then define public boundary tests, implement examples, and
convert each chapter from verified code. Record actual evidence and uncovered
requirements. Re-run compilation, behaviour checks, and docs checks after changes.
Perform a prompt-to-artifact audit before marking the active goal complete.

If blocked, preserve diagnostics, attempted paths, missing evidence, and the next
input needed in `audit.md`. Do not mark the goal complete while blocked.

## Baseline

- Upstream: `c9ee2424af02e4c1e4765088580107d5e17b826e`.
- Compiler present: `zig version` = `0.17.0`.
- Host: Linux `7.2.3-arch1-3`, x86_64.
- Fork created and cloned. Migration and execution audit remain incomplete.
