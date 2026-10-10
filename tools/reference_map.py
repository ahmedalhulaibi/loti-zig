#!/usr/bin/env python3
"""Map the immutable source inventory to compiled native Zig declarations."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SETUP = "examples/reference_setup.zig"
COMPLETE = "examples/reference_completion.zig"
REGISTER = "examples/reference_registration.zig"
PREPARE = "examples/reference_submission.zig"
FILES = "examples/reference_files.zig"
BUFFERS = "examples/reference_buffers.zig"
SPLICE = "examples/reference_splice.zig"
POLL = "examples/reference_poll.zig"
EPOLL = "examples/reference_epoll.zig"
RAW = "examples/reference_raw.zig"

PREPARERS = {
    "nop": "nop", "read": "read", "write": "write", "readv": "read",
    "writev": "writev", "read_fixed": "read_fixed", "write_fixed": "write_fixed",
    "fsync": "fsync", "close": "close", "openat": "openat", "fallocate": "fallocate",
    "statx": "statx", "splice": "splice", "recvmsg": "recvmsg", "sendmsg": "sendmsg",
    "recv": "recv", "send": "send", "accept": "accept", "connect": "connect",
    "epoll_ctl": "epoll_ctl", "poll_add": "poll_add", "poll_remove": "poll_remove",
    "provide_buffers": "provide_buffers", "remove_buffers": "remove_buffers",
    "timeout": "timeout", "timeout_remove": "timeout_remove", "cancel": "cancel",
    "link_timeout": "link_timeout",
}

TYPES = {
    "io_uring": "std.os.linux.IoUring",
    "io_uring_sq": "std.os.linux.IoUring.SubmissionQueue",
    "io_uring_cq": "std.os.linux.IoUring.CompletionQueue",
    "io_uring_sqe": "std.os.linux.io_uring_sqe",
    "io_uring_cqe": "std.os.linux.io_uring_cqe",
    "io_uring_probe": "std.os.linux.io_uring_probe",
    "io_uring_probe_op": "std.os.linux.io_uring_probe_op",
    "io_uring_params": "std.os.linux.io_uring_params",
    "io_sqring_offsets": "std.os.linux.io_sqring_offsets",
    "io_cqring_offsets": "std.os.linux.io_cqring_offsets",
    "iovec": "std.posix.iovec / std.posix.iovec_const",
    "open_how": "raw_ops.OpenHow",
    "__kernel_timespec": "std.os.linux.kernel_timespec",
    "sigset_t": "std.os.linux.sigset_t",
    "sockaddr": "std.os.linux.sockaddr",
    "socklen_t": "std.os.linux.socklen_t",
    "msghdr": "std.os.linux.msghdr / std.os.linux.msghdr_const",
    "statx": "std.os.linux.Statx",
    "size_t": "usize",
    "off_t": "i64; SQE offsets use u64 with the current-offset sentinel",
    "loff_t": "i64; SQE offsets use u64 with the current-offset sentinel",
    "mode_t": "std.posix.mode_t",
}

OTHER = {
    "io_uring_queue_init": ("init", "examples/cat.zig", "Returns an owned value through a Zig error union; power-of-two u16 entries."),
    "io_uring_queue_init_params": ("init_params", SETUP, "Caller supplies zeroed native parameters; returned fields describe actual mappings."),
    "io_uring_queue_exit": ("deinit", SETUP, "Closes the descriptor and unmaps memory; complete or cancel-and-drain outstanding requests before destroying their operands."),
    "io_uring_get_sqe": ("get_sqe", PREPARE, "Queue exhaustion is SubmissionQueueFull, not a null pointer."),
    "io_uring_submit": ("submit", COMPLETE, "Returns submitted SQEs, not completed operations; SQPOLL counts are not completion proof."),
    "io_uring_submit_and_wait": ("submit_and_wait", COMPLETE, "Publishes requests and waits; the return value still counts submissions."),
    "io_uring_wait_cqe": ("copy_cqe", COMPLETE, "Returns a CQE value and advances the CQ; do not acknowledge it again."),
    "io_uring_wait_cqe_nr": ("copy_cqes", COMPLETE, "copy_cqes(destination, wait_nr) copies available entries and advances CQ; its waiting semantics are not a strict batch-size guarantee."),
    "io_uring_peek_cqe": ("copy_cqes", COMPLETE, "A one-element destination with wait_nr=0 gives nonblocking copy-and-consume, not a borrowed pointer."),
    "io_uring_peek_batch_cqe": ("copy_cqes", COMPLETE, "wait_nr=0 returns the actual copied count and consumes those entries."),
    "io_uring_cqe_seen": ("cqe_seen", COMPLETE, "Only for manually borrowed CQEs; not for copy_cqe/copy_cqes results."),
    "io_uring_cq_advance": ("cq_advance", COMPLETE, "Acknowledge exactly the manually processed count."),
    "io_uring_cq_ready": ("cq_ready", COMPLETE, "Acquire-load completion readiness; does not consume entries."),
    "io_uring_sq_ready": ("sq_ready", COMPLETE, "Counts outstanding submission entries, not completion entries."),
    "io_uring_get_probe_ring": ("get_probe", "examples/probe.zig", "Returns an owned fixed-capacity probe value; no heap allocation or free."),
    "io_uring_register_buffers": ("register_buffers", REGISTER, "Borrowed buffers remain valid until outstanding requests finish and registration ends."),
    "io_uring_unregister_buffers": ("unregister_buffers", REGISTER, "Release registration only after dependent operations complete."),
    "io_uring_register_files": ("register_files", REGISTER, "With IOSQE_FIXED_FILE, SQE fd is a table index rather than a process descriptor."),
    "io_uring_register_files_update": ("register_files_update", REGISTER, "Updates a registered table at an offset; unlike prep_files_update it is a synchronous registration operation."),
    "io_uring_unregister_files": ("unregister_files", REGISTER, "Release the registered table after dependent requests finish."),
    "io_uring_register_eventfd": ("register_eventfd", REGISTER, "Completion notifications are a counter, not CQE identities."),
    "io_uring_register_eventfd_async": ("register_eventfd_async", REGISTER, "Inline completions do not notify; the executable forces an asynchronous NOP."),
    "io_uring_unregister_eventfd": ("unregister_eventfd", REGISTER, "Detach notifications before closing the event descriptor."),
}

SPECIAL = {
    "io_uring_setup": ("std.os.linux.io_uring_setup", "os/linux.zig", SETUP, "io_uring_setup", "Raw setup returns errno-encoded usize and fills native parameters; successful result owns a descriptor."),
    "io_uring_enter": ("std.os.linux.io_uring_enter", "os/linux.zig", "examples/raw_cat.zig", "io_uring_enter", "Consumes already-published SQ entries or waits according to flags; the caller publishes SQ tail first. Decode the raw usize result with linux.errno."),
    "io_ring_get_sqe": ("std.os.linux.IoUring.get_sqe", "os/linux/IoUring.zig", PREPARE, "get_sqe", "Corrects an original prose typo; no function named io_ring_get_sqe exists."),
    "io_uring_set_sqe_data": ("sqe.user_data = tag", None, PREPARE, None, "Corrects an original prose typo; use the native tag field."),
    "io_uring_queue_mmap": ("RawRing.map", "examples/raw_cat.zig", SETUP, "map", "Accepts an existing setup descriptor; owns it only on success. Selects shared SQ/CQ or separate SQ/CQ plus SQEs by SINGLE_MMAP; failure unmaps partial regions but leaves the FD to the caller."),
    "io_uring_ring_dontfork": ("RawRing.dontFork", "examples/raw_cat.zig", SETUP, "dontFork", "Applies MADV_DONTFORK to every owned SQ/CQ/SQE region; excludes memory, not descriptor inheritance."),
    "io_uring_sqe_set_data": ("sqe.user_data = tag", None, PREPARE, None, "u64 tags are copied unchanged into CQEs; avoid borrowed application pointers."),
    "io_uring_sqe_set_flags": ("sqe.flags = flags / sqe.flags |= flags", None, PREPARE, None, "Assignment replaces flags; |= adds bits without clearing preparer-set flags. Native flags fit u8."),
    "io_uring_cqe_get_data": ("cqe.user_data", None, COMPLETE, None, "Read the u64 correlation tag directly."),
    "io_uring_sq_space_left": ("ring.sq.sqes.len - ring.sq_ready()", None, COMPLETE, None, "Free slots are distinct from completion readiness."),
    "io_uring_for_each_cqe": ("CQ head/count/mask iteration", None, COMPLETE, None, "Borrow CQ slots after acquiring readiness; acknowledge once after processing."),
    "io_uring_opcode_supported": ("probe.is_supported(opcode)", "os/linux.zig", REGISTER, None, "Takes a native IORING_OP enum and returns bool, using kernel probe flags."),
    "io_uring_register": ("std.os.linux.io_uring_register", "os/linux.zig", REGISTER, "io_uring_register", "Raw register returns errno-encoded usize; decode with linux.errno."),
    "io_uring_sq_test": ("caller-selected output pathname", None, "examples/sq_poll.zig", None, "Original filename, not an API; replaced by the CLI path argument."),
    "io_uring_submit_sqe": ("SQPOLL write/submit sequence", None, "examples/sq_poll.zig", None, "Original application helper, not a public library function."),
}


def signature(text, name):
    match = re.search(r"^\s*pub fn " + re.escape(name) + r"\(", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"Missing installed declaration: {name}")
    return text[match.start():text.index("{", match.end())].strip()


def generate():
    version = subprocess.check_output(["zig", "version"], text=True).strip()
    if version != "0.17.0":
        raise ValueError(f"Required Zig 0.17.0, found {version}")
    env = subprocess.check_output(["zig", "env"], text=True)
    match = re.search(r'\.std_dir = "([^"]+)"', env)
    if match is None:
        raise ValueError("Zig environment did not report std_dir")
    stdlib = Path(match[1])
    sources = {path: (stdlib / path).read_text() for path in ["os/linux/IoUring.zig", "os/linux/io_uring_sqe.zig", "os/linux.zig"]}
    inventory = json.loads((ROOT / "conversion/source-inventory.json").read_text())
    symbols = set(inventory["c_api_symbols"]) | set(TYPES) | {"io_uring_setup", "io_uring_enter", "io_ring_get_sqe", "io_uring_set_sqe_data", "IORING_OP_SYNC_FILE_RANGE"}
    entries = []
    for original in sorted(symbols):
        native_name = None
        native_source = None
        scope = "compiled and executed"
        if original in TYPES:
            target = TYPES[original]
            example = PREPARE if original not in {"io_uring", "io_uring_sq", "io_uring_cq", "io_uring_params", "io_sqring_offsets", "io_cqring_offsets"} else SETUP
            difference = "Native Zig type or explicit Linux ABI representation; not a foreign-language import."
            scope = "compiled type usage; runtime ABI-size checks where applicable"
            if original == "io_uring_cqe":
                example = BUFFERS
                scope = "compiled type usage; actual selected/unselected flags and buffer-ID helper outcomes; no CQE32 or multishot assurance"
        elif original == "IORING_OP_SYNC_FILE_RANGE":
            target, native_source, native_name, example = "raw_ops.sync_file_range", "examples/raw_ops.zig", "sync_file_range", RAW
            scope = "constructed and submitted; valid range and invalid flags/descriptor CQEs checked; not crash-durability evidence"
            difference = "Original opcode reference, not an inventoried C helper declaration. Encodes fd/off/len/rw_flags; no metadata or disk-cache durability guarantee."
        elif original.startswith("io_uring_prep_"):
            method = original.removeprefix("io_uring_prep_")
            example = PREPARE
            scope = "executed SQE construction; mixed requests intentionally not submitted"
            difference = "Acquires an SQE, prepares operands and stores the tag; caller submits separately."
            if method in {"openat2", "fadvise", "madvise"}:
                target = "raw_ops." + method
                native_source = "examples/raw_ops.zig"
                native_name = method
                example = RAW
                scope = {
                    "openat2": "constructed and submitted; returned descriptor and exact regular-file input prefix checked; RDONLY/RESOLVE_NO_SYMLINKS path only",
                    "fadvise": "constructed and submitted; NORMAL-advice success CQE checked; no cache-residency or performance assurance",
                    "madvise": "constructed and submitted; DONTNEED success CQE and exact zeroed anonymous page checked; not other advice or mapping types",
                }[method]
                difference = "No corresponding IoUring wrapper in Zig 0.17.0; helper encodes the actual Linux SQE."
            elif method == "files_update":
                target = "sqe.prep_files_update"
                native_source = "os/linux/io_uring_sqe.zig"
                native_name = "prep_files_update"
                example = REGISTER
                scope = "constructed and submitted separately; correlated updated-entry count and subsequent fixed-file bytes checked"
                difference = "Use get_sqe then the native SQE preparer; keep the descriptor array alive through its CQE. Distinct from synchronous register_files_update."
            else:
                native_name = PREPARERS[method]
                native_source = "os/linux/IoUring.zig"
                target = "std.os.linux.IoUring." + native_name
                if method == "readv":
                    difference = "No ring.readv method: call ring.read with ReadBuffer.iovecs."
                elif method == "splice":
                    difference = "Offsets are u64 values, not pointers; maxInt(u64) means current position. Set splice flags in SQE rw_flags. One descriptor must be a pipe."
                    example = SPLICE
                    scope = "constructed and submitted; file/pipe/pipe transfers, forced partial progress, source/destination value-offset cursor semantics, EOF and six negative CQEs checked; private 4096-byte pipes and memfd destination only"
                if method in {"readv", "writev", "fsync", "close", "openat", "fallocate", "statx"}:
                    example = FILES
                    scope = "constructed and submitted on owned regular files; exact bytes/size, flags, invalid-descriptor CQEs and FD ownership checked; not crash-durability evidence"
                elif method in {"provide_buffers", "remove_buffers"}:
                    example = BUFFERS
                    scope = "constructed and submitted; selected bytes/flags, exhaustion, group isolation, recycling and actual removal counts checked; sequential nonempty regular-file reads only"
                elif method in {"poll_add", "poll_remove"}:
                    example = POLL
                    scope = "constructed and submitted; validated command-state model, one-shot IN/rearm, two cancellation CQEs, missing target/invalid FD, HUP/EOF and before-exit pipe closure; independent syscall oracle checks deadline guards; no readiness/cancel race or multishot assurance"
                    difference = "Native u32 mask encoded little-endian; default one-shot returns an event bitmask, not bytes. HUP can be reported without requesting it." if method == "poll_add" else "Target is the original u64 tag, not a foreign pointer; target and remover have distinct CQEs. Sequential pending cancellation returns -ECANCELED/0; absent targets return -ENOENT."
                elif method == "epoll_ctl":
                    example = EPOLL
                    scope = "constructed and submitted; ADD/MOD/DEL outcomes, IN/OUT mask changes and opaque u64 data independently observed via epoll_wait; duplicate/missing and six negative CQEs, last-owned-FD removal/teardown checked; sequential level-triggered pipe only"
                    difference = "Completion zero means interest-list mutation, not readiness; event storage stays alive through the CQE, then epoll stores its mask/data. DEL accepts null. SDK target-FD cast requires a nonnegative value; retired positive owned FD exercises EBADF."
        elif original in OTHER:
            native_name, example, difference = OTHER[original]
            native_source = "os/linux/IoUring.zig"
            target = "std.os.linux.IoUring." + native_name
        elif original in {"io_uring_get_probe", "io_uring_register_probe", "io_uring_register_personality", "io_uring_unregister_personality", "io_uring_wait_cqes", "io_uring_wait_cqe_timeout"}:
            native_name = {
                "io_uring_get_probe": "probe", "io_uring_register_probe": "register_probe",
                "io_uring_register_personality": "register_personality", "io_uring_unregister_personality": "unregister_personality",
                "io_uring_wait_cqes": "wait_with_timeout", "io_uring_wait_cqe_timeout": "wait_with_timeout",
            }[original]
            target = "raw_ops." + native_name
            native_source = "examples/raw_ops.zig"
            example = COMPLETE if original.startswith("io_uring_wait_") else REGISTER
            difference = "Explicit native helper; does not invent a standard-library method."
            if native_name == "wait_with_timeout":
                difference = "ENTER_EXT_ARG relative deadline (Linux 5.11+), optional signal mask; no hidden SQE, implicit submission or CQ consumption. Submit first, then copy available CQEs."
        else:
            target, native_source, example, native_name, difference = SPECIAL[original]
            if original == "io_uring_queue_mmap":
                scope = "compiled; both mapping strategies execute; five private-descriptor x86_64 seccomp mmap failures verify partial unwind and caller FD ownership"
            elif original == "io_uring_ring_dontfork":
                scope = "compiled; per-page mincore in child verifies all owned regions excluded, while fcntl verifies FD inheritance"
        if not (ROOT / example).is_file():
            raise ValueError(f"Missing executable source: {example}")
        item = {"original": original, "zig": target, "example": example, "verification_scope": scope, "semantic_difference": difference}
        if native_source and native_name:
            text = sources[native_source] if native_source in sources else (ROOT / native_source).read_text()
            item["declaration_source"] = native_source
            item["zig_signature"] = signature(text, native_name)
        entries.append(item)
    return {"source_commit": inventory["source_commit"], "zig_version": version,
        "inventory_api_symbols": len(inventory["c_api_symbols"]),
        "stdlib_sha256": {path: hashlib.sha256(text.encode()).hexdigest() for path, text in sources.items()},
        "entries": entries,
        "limitations": ["This map records code bindings, not completed document conversion.",
            "Constructor tests are not proof of executing all mixed filesystem/network operations.",
            "Independent code review is currently blocked by the subagent host launcher."]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = generate()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    path = ROOT / "conversion/reference-map.json"
    if args.check:
        if not path.is_file() or path.read_text() != rendered:
            raise SystemExit("Reference map is stale; run tools/reference_map.py")
    else:
        path.write_text(rendered)
    print(f"{result['inventory_api_symbols']} original API symbols; {len(result['entries'])} total native bindings; Zig {result['zig_version']}")


if __name__ == "__main__":
    main()
