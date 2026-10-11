"""Finite owned stdout/trace observations; not a new public test or mutation gate."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path.cwd()
ROWS = [
    ("NOP", 0, 4, 0), ("READ", 4096, 0, 0), ("WRITE", 4096, 0, 0),
    ("READV", 1, 0, 0), ("WRITEV", 1, 0, 0), ("FSYNC", 0, 0, 0),
    ("CLOSE", 0, 0, 0), ("OPENAT", 0, 0, 0), ("OPENAT2", 24, 0, 0),
    ("FALLOCATE", 0, 0, 0), ("STATX", 512, 0, 0), ("FADVISE", 4096, 0, 0),
    ("MADVISE", 4096, 0, 0), ("SPLICE", 4096, 0, 0), ("ACCEPT", 0, 0, 0),
    ("CONNECT", 0, 0, 0), ("RECV", 4096, 0, 0), ("SEND", 4096, 0, 0),
    ("RECVMSG", 1, 0, 0), ("SENDMSG", 1, 0, 0), ("EPOLL_CTL", 1, 0, 0),
    ("POLL_ADD", 0, 0, 0), ("POLL_REMOVE", 0, 0, 0), ("READ_FIXED", 4096, 0, 0),
    ("WRITE_FIXED", 4096, 0, 0), ("FILES_UPDATE", 1, 0, 0),
    ("PROVIDE_BUFFERS", 4096, 0, 1), ("REMOVE_BUFFERS", 0, 0, 1),
    ("TIMEOUT", 1, 0, 0), ("TIMEOUT_REMOVE", 0, 0, 0),
    ("ASYNC_CANCEL", 0, 4, 0), ("LINK_TIMEOUT", 1, 0, 0),
    ("SYNC_FILE_RANGE", 4096, 0, 0),
]
EXPECTED_ROWS = [
    dict(tag=tag, operation=operation, length=length, flags=flags, buffer_index=index)
    for tag, (operation, length, flags, index) in enumerate(ROWS, 1)
]
EXPECTED_RAW = {
    "openat2": True, "fadvise_result": 0, "madvise_result": 0,
    "memory_zeroed": True, "read_result": 64,
    "sync_range": {"offset": 0, "length": 4096, "flags": 7, "result": 0},
    "sync_failures": [-22, -9],
}
payload = bytes(range(96))
cases = []
with tempfile.TemporaryDirectory(prefix="loti-submission-purpose-") as directory:
    owned = Path(directory)
    source = owned / "input"
    source.write_bytes(payload)
    for program in ("reference-submission", "reference-raw"):
        trace = owned / "calls.trace"
        command = [str(ROOT / "zig-out/bin" / program), str(source)]
        result = subprocess.run(
            ["strace", "-qq", "-e", "trace=io_uring_setup,io_uring_enter,io_uring_register,close",
             "-o", str(trace), *command], capture_output=True, timeout=10,
        )
        assert (result.returncode, result.stderr) == (0, b""), result.stderr
        output = owned / "stdout"
        with output.open("wb") as stream:
            file_result = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, timeout=10)
        assert (file_result.returncode, file_result.stderr) == (0, b"")
        assert output.read_bytes() == result.stdout
        assert source.read_bytes() == payload
        text = trace.read_text()
        setup = re.findall(r"^io_uring_setup\((\d+), (.*)\)\s+= (\d+)$", text, re.M)
        assert len(setup) == 1
        depth, _, ring = setup[0]
        assert re.findall(rf"^close\({ring}\)\s+= (.*)$", text, re.M) == ["0"]
        register = [line for line in text.splitlines() if line.startswith("io_uring_register(")]
        assert register == []
        enters = [line for line in text.splitlines() if line.startswith("io_uring_enter(")]
        parsed = []
        for line in enters:
            match = re.fullmatch(r"io_uring_enter\((\d+), (\d+), (\d+), ([^,]+), NULL, 8\)\s+= (\d+)", line)
            assert match is not None, line
            fd, submit, minimum, flags, returned = match.groups()
            assert fd == ring
            parsed.append(dict(submit=int(submit), minimum=int(minimum), flags=flags, returned=int(returned)))
        if program == "reference-submission":
            assert int(depth) == 128 and enters == []
            report = [json.loads(line) for line in result.stdout.splitlines()]
            assert report == EXPECTED_ROWS
            body = b""
        else:
            assert int(depth) == 8
            assert [call["submit"] for call in parsed if call["submit"]] == [1, 3, 1, 2]
            for call in parsed:
                assert call["returned"] == call["submit"]
                if call["submit"]:
                    assert (call["minimum"], call["flags"]) == (0, "0")
                else:
                    assert (call["minimum"], call["flags"]) == (1, "IORING_ENTER_GETEVENTS")
            header, separator, body = result.stdout.partition(b"\n")
            assert separator == b"\n" and body == payload[:64]
            report = json.loads(header)
            assert report == EXPECTED_RAW
        artifact = ROOT / "conversion" / f"submission-purpose-{program}.trace"
        artifact.write_bytes(trace.read_bytes())
        cases.append({
            "program": program, "stdout_bytes": len(result.stdout),
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stdout_hex": result.stdout.hex(), "report": report, "body_hex": body.hex(),
            "pipe_file_equal": True, "input_unchanged": True, "empty_stderr": True,
            "setup_depth": int(depth), "enter_calls": parsed, "registration_calls": 0,
            "ring_close_observed": True, "trace_path": str(artifact.relative_to(ROOT)),
        })
(ROOT / "conversion/submission-purpose-native.json").write_text(json.dumps({
    "scope": "Two finite owned file/pipe comparisons. Constructor observation covers five printed fields, not every operand; zero enters establishes no mixed submission. Raw tagged CQEs plus exact prefix/page checks, not advisory performance or durability. Not PBT/independent-agent acceptance.",
    "input_hex": payload.hex(), "cases": cases,
}, indent=2) + "\n")
print("33 whole constructor records without enter; raw batches1/3/1/2; exact stdout file/pipe and input bytes")
