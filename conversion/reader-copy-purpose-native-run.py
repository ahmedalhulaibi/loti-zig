"""Owned CLI bytes and finite ordinary-copy submission batching, not performance proof."""

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRECT_IO = ["read", "readv", "pread64", "preadv", "preadv2", "write", "writev",
             "pwrite64", "pwritev", "pwritev2", "copy_file_range", "sendfile", "splice"]


def number(value: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise AssertionError("InvalidOwnedCopyNumericObservation") from error


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def inspect_trace(trace: str, size: int) -> dict:
    setup = re.findall(r"^io_uring_setup\((\d+), \{flags=(\d+), ([^\n]+)\}\)\s+= (\d+)$",
                       trace, re.MULTILINE)
    assert len(setup) == 1
    depth, flags, fields, descriptor = setup[0]
    ring = number(descriptor)
    assert (number(depth), number(flags)) == (8, 0)
    sq_cq = re.search(r"sq_entries=(\d+), cq_entries=(\d+),", fields)
    assert sq_cq is not None and tuple(map(number, sq_cq.groups())) == (8, 16)
    enters = []
    closes = []
    for line in trace.splitlines():
        call = re.match(r"^(\w+)\(", line)
        assert call is not None
        kind = call.group(1)
        assert kind in {"io_uring_setup", "io_uring_enter", "close"}, line
        if kind == "io_uring_enter":
            match = re.fullmatch(r"io_uring_enter\((\d+), (\d+), (\d+), ([^,]+), NULL, (\d+)\)\s+= (\d+)", line)
            assert match is not None
            owner, requested, minimum, mode, mask_size, returned = match.groups()
            request, wait, result = map(number, [requested, minimum, returned])
            assert (number(owner), number(mask_size)) == (ring, 8)
            assert result == request
            if request:
                assert 1 <= request <= 2 and (wait, mode) == (0, "0")
            else:
                assert (wait, mode) in {(0, "0"), (1, "IORING_ENTER_GETEVENTS")}
            enters.append({"requested": request, "minimum": wait, "flags": mode,
                           "mask": None, "mask_size": 8, "returned": result})
        if kind == "close":
            match = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
            assert match is not None
            closes.append(number(match.group(1)))
    expected_operations = 2 * ((size + 16383) // 16384)
    assert sum(entry["requested"] for entry in enters) == expected_operations
    if size:
        assert enters[0]["requested"] == min(2, (size + 16383) // 16384)
    else:
        assert enters == []
    assert len(closes) == 3 and len(set(closes)) == 3 and closes[0] == ring
    return {"ring_descriptor": ring, "sq_entries": 8, "cq_entries": 16,
            "enters": enters, "submitted": expected_operations, "close_order": closes}


def main() -> None:
    body = (ROOT / "testdata/inputs/http-send-input.bin").read_bytes()
    probe = (ROOT / "testdata/inputs/http-send-probe.bin").read_bytes()
    assert (len(body), len(probe)) == (131072, 37)
    sinks = []
    copies = []
    with tempfile.TemporaryDirectory(prefix="loti-reader-copy-purpose-") as directory:
        owned = Path(directory)
        payloads = [b"", body, probe, b""]
        inputs = [owned / f"input-{index}" for index in range(len(payloads))]
        for path, payload in zip(inputs, payloads, strict=True):
            path.write_bytes(payload)
        expected = b"".join(payloads)
        for program in ["readv", "raw-cat", "cat"]:
            command = [str(ROOT / "zig-out/bin" / program), *map(str, inputs)]
            pipe = subprocess.run(command, capture_output=True, timeout=15)
            assert (pipe.returncode, pipe.stdout, pipe.stderr) == (0, expected, b"")
            output = owned / "stdout"
            with output.open("wb") as stdout:
                file = subprocess.run(command, stdout=stdout, stderr=subprocess.PIPE, timeout=15)
            assert (file.returncode, output.read_bytes(), file.stderr) == (0, expected, b"")
            sinks.append({"program": program, "argument_sizes": list(map(len, payloads)),
                          "stdout_bytes": len(expected), "stdout_sha256": digest(expected),
                          "file_equals_pipe": True, "exit_code": 0, "stderr_bytes": 0})
        for index in [0, 2, 1]:
            source = inputs[index]
            payload = payloads[index]
            output = owned / "destination"
            output.write_bytes(b"old" * (len(payload) + 1))
            trace_path = ROOT / f"conversion/reader-copy-purpose-cp-{len(payload)}.trace"
            command = ["strace", "-qq", "-o", str(trace_path), "-e",
                       "trace=" + ",".join(["io_uring_setup", "io_uring_enter",
                                            "io_uring_register", "close", *DIRECT_IO]),
                       str(ROOT / "zig-out/bin/cp"), str(source), str(output)]
            result = subprocess.run(command, capture_output=True, timeout=15)
            assert (result.returncode, result.stdout, result.stderr) == (0, b"", b"")
            assert output.read_bytes() == source.read_bytes() == payload
            copies.append({"input_bytes": len(payload), "output_sha256": digest(payload),
                           "source_unchanged": True, "old_output_tail_removed": True,
                           "trace": str(trace_path.relative_to(ROOT)),
                           "trace_sha256": digest(trace_path.read_bytes()),
                           **inspect_trace(trace_path.read_text(), len(payload))})
        assert [path.read_bytes() for path in inputs] == payloads
    (ROOT / "conversion/reader-copy-purpose-native.json").write_text(json.dumps({
        "scope": "Finite owned binary/empty/multiple-file pipe-file stdout and ordinary copy0/37/131072. Batching, not physical overlap/throughput/all operands/all syscalls/all failure unwind.",
        "sinks": sinks, "copies": copies,
        "trace_filter": ["io_uring_setup", "io_uring_enter", "io_uring_register", "close", *DIRECT_IO],
        "limits": "No listed synchronous data-transfer substitutes or registrations in these copy traces. Filtered absence is not absence of every possible syscall/substitute; return counts are submissions, not CQE counts. Tagged native completion processing and exact destination bytes are separate evidence. Single current Linux/x86_64, no forced short multi-slot operations or completion reorder."
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
