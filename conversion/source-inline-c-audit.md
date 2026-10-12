# Original inline C reference supplement

Originalc9ee2424;targetb10f816. Requirement2 still had a concrete enumeration gap:
7 C typedef/NULL reference lines outside the canonical3618 and historical16 rows.
They were already converted in the edition;no manuscript/native change needed.

## New original lines → native target

| Original | Current representation |
| --- | --- |
| io_uring_enter.rst:225 | ACCEPT output length pointer;submission.rst:250–258 |
| io_uring_enter.rst:256 | CONNECT input length value;submission.rst:298–304 |
| io_uring_register.rst:65 | UNREGISTER_BUFFERS null/zero;register:21–25 |
| io_uring_register.rst:123 | UNREGISTER_EVENTFD null/zero;register:56–60 |
| io_uring_register.rst:142 | REGISTER_PERSONALITY null/zero;register:71–72 |
| io_uring_register.rst:148 | UNREGISTER_PERSONALITY null/ID;register:73–76 |
| io_uring_register.rst:180 | Unregister null/zero preconditions and generic INVAL;register:21–25,38–42,85–89 |

Original paths are ref-iouring/;target submission is ref-zig/submission.rst and
register is ref-iouring/io_uring_register.rst. SDK0.17.0 prep_accept uses optional
socklen_t pointer in SQE off;prep_connect uses its value. Native socklen_t is u32.
SDK unregister methods pass null/0;raw_ops personality helpers pass null/0 or ID.
Bodies inspected,not new runtime tests. Last row does not attest an isolated
invalid-unregister failure;current error bucket is deliberately general.

## Query / preservation

All42 original blobs hashed;34 UTF8 text files searched/8 binary files excluded.
Additional C build aliases0 hits,inline syntax/type names295 hits,language aliases
118 hits. Of9 outside canonical inventory,7 are the references above. Other2 are
HTML comment terminator and state-transition arrows,not C member access. Retained
layout template is inactive:conf has no template override;Sphinx8.2.3 default[].
Neither zero build hits nor these finite patterns prove every spelling covered.

`source-inline-c-supplement.json` stores exact original lines,current target slices,
all original/target/SDK/helper hashes,query and limits. Canonical3618/128 unchanged;
historical16-row supplement targetee0b124/hash730dc0d7 unchanged. Separate7-row
addition yields3641 unique enumerated lines across the three artifacts;not a claim
that all3641 are C language lines or independently accepted meanings.

Owned evidence:`_build/verification/inline-c-enumeration.ffnmzwrg/`. Selected226
edition inputs/archive5739833e unchanged;no new formal tests/properties/kills,
full/cold/publication replay,HTTP author retry,sealing,repair,push or completion.
Provider restriction/test protection/retirement/independent acceptance remain open.
Six-path LSP:4 clean;2 deliberate fail-closed JSON loads/2 original asset-name
findings marked false-positive. No suppressions;SDK bodies override stale graph.
