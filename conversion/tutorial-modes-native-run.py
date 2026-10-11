"""Retain finite owned tutorial bytes, link ownership checkpoints and current traces."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.test_link_ownership import BIN, observe


def decoded(value: bytes):
    try:
        return json.loads(value)
    except ValueError as error:
        raise AssertionError("InvalidOwnedTutorialJsonObservation") from error


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    links, sinks, events = [], [], []
    contracts = json.loads((ROOT / "testdata/inputs/link-ownership-contracts.json").read_text())
    with tempfile.TemporaryDirectory(prefix="loti-tutorial-modes-native-") as directory:
        owned = Path(directory)
        for plan in contracts["plans"]:
            path = owned / "linked-output"
            trace = ROOT / f"conversion/tutorial-modes-link-{plan['name']}.trace"
            actual = observe(BIN, path, plan["arguments"], trace)
            assert actual["publication"] == plan["publication"]
            assert actual["application_close_results"] == plan["application_close_results"]
            assert decoded(actual["stdout"]) == plan["report"]
            assert path.read_bytes() == contracts["payload"].encode()
            links.append({"plan": plan["name"], "publication": actual["publication"],
                          "report": decoded(actual["stdout"]),
                          "application_close_results": actual["application_close_results"],
                          "file_bytes": len(path.read_bytes()), "file_sha256": digest(path.read_bytes()),
                          "trace": str(trace.relative_to(ROOT)), "trace_sha256": digest(trace.read_bytes())})
        poem = b"What is this life if, full of care,\nWe have no time to stand and stare."
        polling = (ROOT / "testdata/inputs/sqpoll-wakeup-output.bin").read_bytes()
        assert (len(poem), len(poem.splitlines(keepends=True)[0]), len(poem.splitlines()[1])) == (71, 36, 35)
        for name, payload in [("fixed-buffers", poem), ("sq-poll", polling)]:
            path, stdout = owned / "output", owned / "stdout"
            command = [str(ROOT / "zig-out/bin" / name), str(path)]
            pipe = subprocess.run(command, capture_output=True, timeout=10)
            assert (pipe.returncode, pipe.stdout, pipe.stderr) == (0, payload, b"")
            assert path.read_bytes() == payload
            with stdout.open("wb") as sink:
                file = subprocess.run(command, stdout=sink, stderr=subprocess.PIPE, timeout=10)
            assert (file.returncode, stdout.read_bytes(), file.stderr) == (0, payload, b"")
            assert path.read_bytes() == payload
            sinks.append({"program": name, "stdout_file_equals_pipe": True,
                          "stdout_bytes": len(payload), "stdout_sha256": digest(payload),
                          "file_equals_stdout": True, "exit_code": 0, "stderr_bytes": 0})
        binary = (ROOT / "testdata/inputs/http-send-input.bin").read_bytes()
        for payload in [b"", binary[:37], binary]:
            source, stdout = owned / "input", owned / "event-stdout"
            source.write_bytes(payload)
            expected = payload[:512]
            command = [str(ROOT / "zig-out/bin/register-eventfd"), str(source)]
            result = subprocess.run(command, capture_output=True, timeout=10)
            report = {"notifications": 1, "user_data": 1, "result": len(expected)}
            assert (result.returncode, result.stdout) == (0, expected)
            assert decoded(result.stderr) == report
            with stdout.open("wb") as sink:
                file = subprocess.run(command, stdout=sink, stderr=subprocess.PIPE, timeout=10)
            assert (file.returncode, stdout.read_bytes()) == (0, expected)
            assert decoded(file.stderr) == report
            assert source.read_bytes() == payload
            events.append({"input_bytes": len(payload), "stdout_bytes": len(expected),
                           "stdout_sha256": digest(expected), "stderr_report": report,
                           "stdout_file_equals_pipe": True, "source_unchanged": True})
    report = {"scope": "Finite owned link pre-publication descriptor census/two before-exit syscall traces; fixed/SQPOLL file-pipe bytes; eventfd empty/37/131072 input prefix/file-pipe bytes. Not all error paths, races, platforms, notifications or transports.",
              "links": links, "sinks": sinks, "events": events,
              "limits": "Link syscall filter openat/close/setup/enter does not observe every SQE operand or all syscalls. Procfs census at owned blocked stdout is separate from CQE report/automatic exit cleanup. Finite runs are not generated PBT."}
    (ROOT / "conversion/tutorial-modes-native.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
