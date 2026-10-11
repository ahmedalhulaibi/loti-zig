"""Finite raw reader syscall/mapping and exact stdout observations."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path.cwd()


def number(value: str, base: int = 10) -> int:
    try:
        return int(value, base)
    except ValueError as error:
        raise AssertionError("InvalidOwnedNumericObservation") from error


fixture = ROOT / "testdata/inputs/http-send-input.bin"
payload = fixture.read_bytes()
assert len(payload) == 131072
with tempfile.TemporaryDirectory(prefix="loti-raw-purpose-native-") as directory:
    owned = Path(directory)
    source, empty, output, trace = [owned / name for name in ("input", "empty", "stdout", "calls.trace")]
    source.write_bytes(payload)
    empty.write_bytes(b"")
    command = [str(ROOT / "zig-out/bin/raw-cat"), str(source), str(empty)]
    piped = subprocess.run(
        ["strace", "-qq", "-e", "trace=io_uring_setup,io_uring_enter,io_uring_register,mmap,munmap,close",
         "-o", str(trace), *command], capture_output=True, timeout=10,
    )
    assert (piped.returncode, piped.stderr) == (0, b""), piped.stderr
    assert piped.stdout == payload
    with output.open("wb") as stream:
        redirected = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, timeout=10)
    assert (redirected.returncode, redirected.stderr) == (0, b"")
    assert output.read_bytes() == payload and source.read_bytes() == payload and empty.read_bytes() == b""
    text = trace.read_text()
    lines = text.splitlines()
    setup = re.findall(r"^io_uring_setup\(8, (.*)\)\s+= (\d+)$", text, re.M)
    assert len(setup) == 1
    params, ring = setup[0]
    assert params.startswith("{flags=0,")
    names = ("sq_entries", "cq_entries", "array", "cqes")
    values = {}
    for name in names:
        matches = re.findall(rf"\b{name}=(\d+)\b", params)
        assert len(matches) == 1
        values[name] = number(matches[0])
    assert (values["sq_entries"], values["cq_entries"]) == (8, 16)
    mappings = re.findall(
        rf"^mmap\(NULL, (\d+), PROT_READ\|PROT_WRITE, MAP_SHARED\|MAP_POPULATE, {ring}, (0x[0-9a-f]+|0)\)\s+= (0x[0-9a-f]+)$",
        text, re.M,
    )
    assert len(mappings) == 2
    expected_shared = max(values["array"] + 8 * 4, values["cqes"] + 16 * 16)
    assert [(number(size), number(offset, 0)) for size, offset, _ in mappings] == [(expected_shared, 0), (8 * 64, 0x10000000)]
    calls = [line for line in lines if line.startswith("io_uring_enter(")]
    assert len(calls) == 34
    for line in calls:
        assert re.fullmatch(rf"io_uring_enter\({ring}, 1, 1, IORING_ENTER_GETEVENTS, NULL, 8\)\s+= 1", line), line
    assert [line for line in lines if line.startswith("io_uring_register(")] == []
    closes = [index for index, line in enumerate(lines) if re.fullmatch(rf"close\({ring}\)\s+= 0", line)]
    assert len(closes) == 1
    retired = []
    for _, _, address in mappings:
        locations = [index for index, line in enumerate(lines) if re.fullmatch(rf"munmap\({address}, \d+\)\s+= 0", line)]
        assert len(locations) == 1 and locations[0] < closes[0]
        retired.append(locations[0])
    assert retired[1] < retired[0]
    artifact = ROOT / "conversion/raw-syscall-purpose-native.trace"
    artifact.write_bytes(trace.read_bytes())
    report = {
        "scope": "One finite owned regular-binary/empty concatenation plan, pipe and file stdout. Current SINGLE_MMAP ordinary one-producer/one-outstanding operation; not u32 wrap, all partial reads/signals, concurrency/overflow, older kernels or independent acceptance.",
        "fixture": str(fixture.relative_to(ROOT)), "input_bytes": [len(payload), 0],
        "stdout_bytes": len(piped.stdout), "stdout_sha256": hashlib.sha256(piped.stdout).hexdigest(),
        "pipe_file_equal": True, "input_unchanged": True, "empty_stderr": True,
        "sq_entries": 8, "cq_entries": 16, "submissions": 34,
        "enter_shape": {"to_submit": 1, "min_complete": 1, "flags": "IORING_ENTER_GETEVENTS", "mask": None, "mask_bytes": 8, "returned_submissions": 1},
        "mapping_bytes": [expected_shared, 512], "mapping_offsets": [0, 0x10000000],
        "mapping_retirement": "SQEs then shared region, each exactly once before observed ring close",
        "trace": str(artifact.relative_to(ROOT)),
        "limits": "Enter counts are submissions, not CQE/result counts. Full output and inspected native tag/result/head publication provide bounded byte evidence; trace does not observe atomics or all operand fields. No synchronous-read substitution assertion from this restricted trace filter.",
    }
(ROOT / "conversion/raw-syscall-purpose-native.json").write_text(json.dumps(report, indent=2) + "\n")
print("131072 exact stdout bytes +empty input;34 raw enters;two real ring maps/ordered retirement;pipe/file equality")
