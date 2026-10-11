"""Owned blocked-stdout checkpoint distinguishes CLOSE effects from NOP metadata."""

import fcntl
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "zig-out/bin/link"
FIXTURE = ROOT / "testdata/inputs/link-ownership-contracts.json"


def number(value: str, base: int = 10) -> int:
    try:
        return int(value, base)
    except ValueError as error:
        raise AssertionError("InvalidOwnedLinkNumericObservation") from error


def publication(tracer: subprocess.Popen, binary: Path, path: Path) -> dict[str, int]:
    """Inspect only this launch's child after its report blocks on our full pipe."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if tracer.poll() is not None:
            raise RuntimeError("OwnedLinkExitedBeforePublicationCheckpoint")
        try:
            children = (Path(f"/proc/{tracer.pid}/task/{tracer.pid}/children")
                        .read_text().split())
            if len(children) != 1:
                time.sleep(0.005)
                continue
            child = number(children[0])
            process = Path(f"/proc/{child}")
            if Path(os.readlink(process / "exe")) != binary.resolve():
                time.sleep(0.005)
                continue
            blocked = False
            for task in (process / "task").iterdir():
                fields = (task / "syscall").read_text().split()
                # Linux x86_64 write/writev/pwrite64/pwritev/pwritev2, stdout FD1.
                if len(fields) >= 2 and fields[0] in {"1", "20", "18", "296", "328"}:
                    if number(fields[1], 0) == 1:
                        blocked = True
            if not blocked:
                time.sleep(0.005)
                continue
            identity = path.stat()
            files = rings = 0
            for fd in (process / "fd").iterdir():
                target = os.readlink(fd)
                if target == "anon_inode:[io_uring]":
                    rings += 1
                metadata = fd.stat()
                if (metadata.st_dev, metadata.st_ino) == (identity.st_dev, identity.st_ino):
                    files += 1
            return {"file_descriptors": files, "ring_descriptors": rings}
        except FileNotFoundError:
            time.sleep(0.005)
    raise TimeoutError("OwnedLinkPublicationCheckpointNotObserved")


def application_closes(text: str, path: Path) -> list[int]:
    lines = [re.sub(r"^\d+\s+", "", line) for line in text.splitlines()]
    pattern = re.compile(r'openat\([^,]+, "' + re.escape(str(path)) +
                         r'", [^)]*\)\s+= (\d+)$')
    opened = [(index, number(match.group(1))) for index, line in enumerate(lines)
              if (match := pattern.fullmatch(line)) is not None]
    assert len(opened) == 1, "OwnedLinkOutputOpenNotObserved"
    order, descriptor = opened[0]
    results = []
    for line in lines[order + 1:]:
        match = re.fullmatch(r"close\((\d+)\)\s+= (-?\d+)(?: [^\n]*)?", line)
        if match is not None and number(match.group(1)) == descriptor:
            results.append(number(match.group(2)))
        # This finite program has no later explicit opens of a reused target FD.
        match = re.fullmatch(r"openat\([^\n]+\)\s+= (\d+)", line)
        assert match is None or number(match.group(1)) != descriptor, "OwnedLinkDescriptorReused"
    return results


def observe(binary: Path, path: Path, arguments: list[str], trace: Path) -> dict:
    assert platform.machine() == "x86_64", "Link ownership checkpoint requires Linux x86_64/procfs/strace"
    read_fd, write_fd = os.pipe2(os.O_CLOEXEC)
    process = None
    try:
        capacity = fcntl.fcntl(write_fd, fcntl.F_SETPIPE_SZ, 4096)
        filler = bytes([165]) * capacity
        assert os.write(write_fd, filler) == capacity
        process = subprocess.Popen([
            "strace", "-f", "-qq", "-o", str(trace), "-e",
            "trace=openat,close,io_uring_setup,io_uring_enter",
            str(binary), str(path), *arguments,
        ], stdout=write_fd, stderr=subprocess.PIPE, start_new_session=True)
        os.close(write_fd)
        write_fd = -1
        census = publication(process, binary, path)
        consumed = bytearray()
        while len(consumed) < capacity:
            data = os.read(read_fd, capacity - len(consumed))
            assert data, "OwnedLinkFillerMissing"
            consumed.extend(data)
        assert bytes(consumed) == filler
        _, stderr = process.communicate(timeout=5)
        output = bytearray()
        while data := os.read(read_fd, 4096):
            output.extend(data)
        assert (process.returncode, stderr) == (0, b""), "OwnedLinkExecutionFailed"
        return {"publication": census, "stdout": bytes(output),
                "application_close_results": application_closes(trace.read_text(), path)}
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)
        os.close(read_fd)
        if write_fd != -1:
            os.close(write_fd)


class LinkedOwnershipContracts(unittest.TestCase):
    def test_close_effect_and_cancelled_close_fallback_before_process_exit(self):
        """Kills NOP-as-CLOSE and process-exit-only cleanup despite identical CQE reports."""
        expected = json.loads(FIXTURE.read_text())
        with tempfile.TemporaryDirectory(prefix="loti-link-ownership-") as directory:
            path, trace = Path(directory) / "output", Path(directory) / "trace"
            for plan in expected["plans"]:
                path.write_bytes(b"previous longer output must be truncated")
                actual = observe(BIN, path, plan["arguments"], trace)
                self.assertEqual(actual["publication"], plan["publication"], plan["name"])
                self.assertEqual(json.loads(actual["stdout"]), plan["report"])
                self.assertEqual(actual["application_close_results"], plan["application_close_results"])
                self.assertEqual(path.read_bytes(), expected["payload"].encode())


if __name__ == "__main__":
    unittest.main()
