# Remaining whole-chapter prose

Base `ec7e1d9`; README red `7e662c4`. Prior seven purpose reports compare20
original whole chapters/128 blocks. Read the remaining six original/current
chapters completely, plus README, config, licence and template. All26 original
chapter bodies now have author comparison. This is not independent acceptance.

| Original chapter | Purpose / current disposition |
|---|---|
| index.rst | Linux asynchronous-I/O scope, Shuveb/unixism origin and contribution/source navigation. Native exact0.17 title/attribution/build instructions; personal fork replaces separate examples repo. Introduction→tutorial8→reference7→syscalls3→history order retained through section-owned toctrees. Added licence chapter; no lost teaching chapter. |
| async_intro.rst | Blocking/preemption, shared address space/synchronization, worker pools and seven iterative/forking/preforked/threaded/prethreaded/poll/epoll models retained. Historical diagrams/benchmarks attributed, not relabelled as Zig results. Remove universal request-rate cutoff; choose measured workload. std.Thread/std.Io/native IoUring replace foreign-framework recommendations. Readiness is not completion; correct regular-file epoll and POSIX/native-AIO confusion. No all-submission-never-blocks claim. |
| what_is_io_uring.rst | Axboe/Linux5.1, shared SQ/CQ, acquire/prepare/tag/publish/complete/consume model, batching/poller and raw/wrapper teaching paths retained. Feature-selected ring-control/SQE mappings, single-shot vs multishot/suppression, storage/atomic lifetimes and failed linked cleanup qualified. Metadata sharing is not payload zero-copy; original paper remains historical, not Zig throughput proof. Actual support/policy/CQEs replace version-only assumptions. |
| tutorial/index.rst | High-level boilerplate abstraction and low-level understanding retained. IoUring owns mappings/publication; application owns operands/state. Complete compiled sources and all eight tutorial children in original order; no foreign examples repo dependency. |
| ref-liburing/index.rst | ref-zig/index retains seven reference children/order. Exact0.17 SDK-local signatures, error unions, preparation vs execution, copied vs borrowed CQEs and repository helpers explained; declarations are not runnable applications. |
| changelog.rst | Original2020-06-15 SINGLE_MMAP change retains attribution and related links. Three mappings→two, not one; SQEs still separate. Edition history points to native sources and honestly incomplete audit/review. |

## Actual preservation / links

- LICENSE bytes equal immutable original; license.rst includes that exact text.
  All seven original source illustrations/logo are byte-identical, including
  the unused alternate process-model PNG. Current EPUB title/creator/publisher,
  language and licence page inspected; five chapter illustrations/logo already
  have packaged-byte contracts. Original figures are explicitly historical.
- Actual local chapter/navigation targets and external attribution/paper links
  inspected in source/current package. Man references remain Linux concepts,
  not unconverted C APIs. Manuscript scan finds only fio's original io_uring.c
  citation; this is attributed provenance, not an edition C example.
- Original compile_commands.json is empty, not a missed C program. delme.c is
  an accounted-for declaration catalog without main/bodies. Generated Python3.8
  plugin bytecode is retired, source retained. The original unused analytics
  template remains in source; effective templates_path=[] excludes it. EPUB
  script absence is checked, not inferred from a configuration omission.
- Personal fork/parent/master/path refreshed by GitHub API and SSH: remote master
  still immutablec9ee2424; no conversion delivered. Source links into future
  converted fork paths need final post-push verification. External-link liveness
  is not implied by correct attribution/local-link validation.

## README gap / repair

README advertised120 literals/359 paragraphs; actual source/package contracts
are121/368. Full102 and strict source fidelity did not cover README. Red preserves
whole old file Git blob/hash and independent new fixture/test failure. Correct
the two counts; expected values do not change. No native/manuscript change.

Old README commands wrote current reports onto tracked historical canonical
receipts. New instructions create ignored _build/verification and write epub,
reader-layout and block-devices JSON there. Retained conversion receipts remain
history; output paths alone are not verification. New consumer test compares
four actual reader statistics and complete argv, executes the fixture-confirmed
mkdir/publication command, compares actual published properties/file/stdout.
It does not execute arbitrary README shell or replace test expectations.

Three valid source-prose kills: old literal count, old narrative count, historical
output overwrite. Each1 failure/0 errors/skips; restored1. Expectations/source
hashes unchanged; source routed into owned directories, no production edit or
receipt overwrite. Author fixture hashes are not ACL seals or verifier acceptance.

## Bounded replay and final author aggregate

- New1 documentation contract green. Selected6 (documentation/inventory/index)
  green; two existing publication methods with nine archive damages green.
  Direct testcase replay bypasses their make-epub setup but assigns actual owned
  archive bytes exactly as setup would. No expected-value override/new full-suite
  claim. An unused wrong InventoryContract import failed before replay; retained
  reproduction/error, no tests or kills attributed to it.
- All93 native/publication inputs and historical full102's200 source pins remain
  exact; README is excluded from both. New full103 passes169.323s, zero failures/
  errors/skips,16 properties×400 and203 source pins including README/new contract.
  Suite invokes make epub; post-suite current archivee5f9fbb3 is verified with81
  detailed reader cases/EPUBCheck zero messages. Earlier77a receipts and bounded
  pre-suite replay remain history, not current acceptance. No new51-step native
  or strict HTML/EPUB run is claimed; their inputs are byte-identical.
- Three bounded user-scope prose mutations, cumulative292 author kills; no native
  or new property. Current objective still requires independent current-HEAD
  review/findings resolution, final accepted gates/push and remote-content check.
  Reviewer host blocker unchanged; no retry/alternate mechanism or completion.

## Required scope vs broader assurance

Required: all original chapters/examples/declarations and reference meanings,
exact compiler/native code, complete source enumeration, preserved provenance,
consistent reader instructions and accepted fork delivery. Author comparison
finds no other gap in these six chapters; only independent review can challenge
that decision. Whole prompt acceptance remains unverified until review/delivery.

Not introduced as requirements: all kernel/architecture/flag/transport/filesystem
races, physical durability/OOM/ENOSPC, production HTTP, concurrent SQ/CQ/SQPOLL,
multishot/pbuf-ring/full cancellation semantics, forced header/vector/RECV shorts,
multi-slot physical overlap, device pagination/font overrides or every error
unwind. Examples/references state supported teaching scopes; bounded tests do
not attest these wider behaviours. A reviewer may still find a required omission;
uncertainty is incomplete, not waived by this classification.
