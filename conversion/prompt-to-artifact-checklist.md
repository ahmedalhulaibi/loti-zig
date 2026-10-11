# Zig edition acceptance checkpoint

Required end state: personal fork/local clone; exhaustive immutable C/io_uring
inventory; native Zig0.17.0 examples, references and language-specific prose;
preserved purpose/order/attribution/licence/images; verified accepted delivery.
**Incomplete.** This checklist maps evidence, not intent or green-status proxies.

| Requirement/surface | Concrete evidence | Current disposition |
|---|---|---|
| 1. Fork/location | `.git/config`, origin personal SSH URL, immutable upstreamc9ee2424, prior API fork/parent evidence in review handoff/blocker history; checkout `/home/ahmed/workspace/va/loti-zig` | Created/cloned; refresh remote/API and verify delivered commit at final gate. Nothing pushed. |
| 2. Every C/io_uring line/block | `conversion/source-inventory.json`, inventory/check_line_dispositions checks:3618 lines/128 blocks/567 outside lines | Enumeration/index freshness checked; not line-purpose acceptance. |
| 3. Update references | `tools/reference_map.py --check`:76 original symbols/99 native bindings; reference_docs13 includes;22 type scopes/reflection and actual native consumers | Covered reference subsets; still audit broader prose/links against original purpose, not just fresh maps. |
| 4. Recreate every example | `build.zig`,25 native executables, exact compiler guard, current51/51 build; compiled literalincludes | Native conversion exists; purpose reports117/128, remaining11 HTTP tutorial blocks. |
| 4. Update relevant text | Original/current whole-chapter purpose reports; latest `tutorial-modes-purpose-audit.md`; link15→16 reproduced in source/archive/runtime | Required link-count defect fixed; remaining HTTP/wider prose/final semantic audit open. Faithful publication alone cannot establish correctness. |
| Publication fidelity | `tutorial-modes-publication.json`:26 original/27 edition chapters,121 literals/368 paragraphs, licence/images/order/links, no DRM/JS; strict HTML/EPUB logs | Current archive3a1aebc6… verified after suite/builds; exact structure/fidelity, not semantics. Older canonical-name receipts remain historical/pinned. |
| Native/public/tool contracts | `tutorial-modes-full-tests.json/log`:101/zero failures-errors-skips,16 properties×400 generated valid cases,198 source pins | Current full boundary replay; finite cases, generators, shrink/development failures and broader unsupported behaviours remain distinct. |
| Verify verifier strength | `mutation-link-ownership.json`, retained initial failure/original15-byte draft; cumulative287 bounded valid mutants | Two native/one source-prose kills added. Not universal conversion/SDK/kernel proof or independent review. |
| Reader suitability | `tutorial-modes-reader.json`:81 Chromium reflows; current EPUBCheck5.2.1 zero messages | Browser/offline checks, not Supernote/device pagination/font-override acceptance. No Calibre. |
| Attribution/licence/images | Current publication verifier plus unchanged original `LICENSE`, licence.rst, five illustrations/logo and Shuveb/Ahmed credits | Byte/structure checks retained; final prompt audit must inspect actual artefacts. |
| Mandatory independent review | `conversion/review-blocker.md`, handoff; both reviewer reports remain absent | Blocked supported Pi child host; no qualifying change, retry or alternate mechanism. Owner-supported host/authorisation required. |
| Final delivery/completion | Final current-HEAD review/findings, affected/full gates, personal-fork push and remote hash verification | Not done. No PR/release requested; do not push/complete before acceptance. |

Next: remaining HTTP11 purposes, wider original prose/explicit requirements,
independent review of final HEAD, findings resolution and final acceptance/delivery.
Historical99/type/build/reader reports are retained as history, not silently
promoted after manuscript change. Uncertainty or missing verification means
not achieved; hashes/indexes/effort cannot substitute for the requirement.
