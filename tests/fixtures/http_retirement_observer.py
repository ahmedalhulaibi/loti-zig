"""Owned public CLI/syscall/mapping probe;not an application modification."""
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import struct
import subprocess
import sys
import time
from typing import BinaryIO, Callable, cast

def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def layout(trace):
    setup = re.search(r"^(\d+) .+io_uring_setup\(64, .*sq_off=\{([^}]+)\}, cq_off=\{([^}]+)\}\}\) = (\d+)", trace, re.M)
    if setup is None:
        return None
    pid, sq, cq, ringfd = setup.groups()
    offsets = [{k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", fields)} for fields in (sq, cq)]
    mappings = re.findall(r"mmap\(NULL, (\d+), .*MAP_SHARED\|MAP_POPULATE, " + ringfd + r"<anon_inode:\[io_uring\]>, (0x[0-9a-f]+|0)\) = (0x[0-9a-f]+)", trace)
    if len(mappings) != 2:
        return None
    return {"pid": int(pid), "ringfd": int(ringfd), "sq": offsets[0], "cq": offsets[1],
            "ring": int(mappings[0][2], 16), "ring_size": int(mappings[0][0]),
            "sqes": int(mappings[1][2], 16), "sqes_size": int(mappings[1][0])}


def snapshot(mem, info, abi):
    ring = os.pread(mem, info["ring_size"], info["ring"])
    need(len(ring) == info["ring_size"], "ShortRingSnapshot")
    word = lambda offset: struct.unpack_from("<I", ring, offset)[0]
    sh, st = (word(info["sq"][k]) for k in ("head", "tail"))
    ch, ct = (word(info["cq"][k]) for k in ("head", "tail"))
    need(st >= sh and ct >= ch and ct < 128, "SnapshotCounterScopeExceeded")
    pending = []
    sqes = os.pread(mem, info["sqes_size"], info["sqes"]) if st != sh else b""
    for cursor in range(sh, st):
        index = word(info["sq"]["array"] + 4 * (cursor & word(info["sq"]["ring_mask"])))
        entry = sqes[index * abi["sqe_size"]:(index + 1) * abi["sqe_size"]]
        pending.append({"opcode": entry[abi["sqe"]["opcode"]],
                        "fd": struct.unpack_from("<i", entry, abi["sqe"]["fd"])[0],
                        "addr": struct.unpack_from("<Q", entry, abi["sqe"]["addr"])[0],
                        "len": struct.unpack_from("<I", entry, abi["sqe"]["len"])[0],
                        "tag": struct.unpack_from("<Q", entry, abi["sqe"]["tag"])[0]})
    completed = []
    for cursor in range(ct):
        entry = ring[info["cq"]["cqes"] + cursor * abi["cqe_size"]:]
        completed.append({"tag": struct.unpack_from("<Q", entry, abi["cqe"]["tag"])[0],
                          "res": struct.unpack_from("<i", entry, abi["cqe"]["res"])[0],
                          "flags": struct.unpack_from("<I", entry, abi["cqe"]["flags"])[0]})
    return {"sq_head": sh, "sq_tail": st, "cq_head": ch, "cq_tail": ct,
            "pending_sqes": pending, "all_cqes_before_wrap": completed}


def run_probe(directory, *, binary, abi, fixture, case):
    need(os.uname().machine == "x86_64" and sys.byteorder == "little", "UnsupportedSnapshotArchitecture")
    when, permanent = case["when"], case["permanent"]
    directory.mkdir()
    document = directory / "root"
    document.mkdir()
    body = bytes.fromhex(fixture["payload_seed_hex"]) * fixture["payload_repetitions"]
    (document / fixture["document_name"]).write_bytes(body)
    stderr_r, stderr_w = os.pipe()
    fill = 0
    argv = ["/usr/bin/strace", "-f", "-yy", "-ttt", "-n", "-s", "128",
            "-e", "trace=io_uring_setup,io_uring_enter,mmap,munmap,close,openat2,writev",
            "-e", f"inject=io_uring_enter:error=EAGAIN:delay_enter=2s:when={when}" + ("+" if permanent else ""),
            "-e", "inject=munmap:delay_enter=100ms:when=1+",
            "-o", str(directory / "trace.log"), str(binary),
            str(document), "0", "--observe-send"]
    process = None
    peer = None
    mem = None
    output = bytearray()
    error_output = bytearray()
    observations = []
    info = None
    operand = None
    operand_cq_cursor = None
    first_payload = None
    final = None
    stream = None
    try:
        os.set_blocking(stderr_w, False)
        try:
            while True:
                fill += os.write(stderr_w, b"X" * 4096)
        except BlockingIOError:
            pass
        os.set_blocking(stderr_w, True)
        save(directory / "argv.json", argv)
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=stderr_w, start_new_session=True,
                                   env={**os.environ, "LC_ALL": "C"})
        stream = cast(BinaryIO, process.stdout)
        os.close(stderr_w)
        stderr_w = -1
        os.set_blocking(stream.fileno(), False)
        deadline = time.monotonic() + fixture["timeout_seconds"]
        connected = False
        while time.monotonic() < deadline:
            if select.select([stream], [], [], 0)[0]:
                output.extend(os.read(stream.fileno(), 65536))
            if not connected and b"\n" in output:
                ready = json.loads(output.split(b"\n", 1)[0])
                need(ready["event"] == "loti.http.ready", "WrongReadiness")
                peer = socket.socket()
                peer.settimeout(3)
                if case.get("receive_buffer"):
                    peer.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, case["receive_buffer"])
                peer.connect(("127.0.0.1", ready["port"]))
                peer.sendall(fixture["request"].encode("ascii"))
                connected = True
            trace = (directory / "trace.log").read_text() if (directory / "trace.log").exists() else ""
            if info is None:
                info = layout(trace)
                if info is not None:
                    mem = os.open(f"/proc/{info['pid']}/mem", os.O_RDONLY)
                    save(directory / "layout.json", info)
            if info is not None:
                assert mem is not None
                captured = snapshot(mem, info, abi)
                if case.get("consumed") and operand is None and captured["sq_head"] == captured["sq_tail"]:
                    count = captured["sq_head"]
                    if count - captured["cq_tail"] == 2 and 6 <= count < 64:
                        raw_sqes = os.pread(mem, info["sqes_size"], info["sqes"])
                        history = []
                        for cursor in range(count):
                            raw = raw_sqes[cursor * abi["sqe_size"]:(cursor + 1) * abi["sqe_size"]]
                            history.append({"opcode": raw[abi["sqe"]["opcode"]],
                                            "fd": struct.unpack_from("<i", raw, abi["sqe"]["fd"])[0],
                                            "addr": struct.unpack_from("<Q", raw, abi["sqe"]["addr"])[0],
                                            "len": struct.unpack_from("<I", raw, abi["sqe"]["len"])[0],
                                            "tag": struct.unpack_from("<Q", raw, abi["sqe"]["tag"])[0]})
                        reads = [s for s in history if s["opcode"] == abi["ops"]["READ"]]
                        if history[-1]["opcode"] == abi["ops"]["SEND"] and len(reads) == 1:
                            operand = history[-1]
                            operand["heap_addr"] = reads[0]["addr"]
                            operand["heap_len"] = reads[0]["len"]
                            operand_cq_cursor = captured["cq_tail"]
                            first_payload = os.pread(mem, operand["heap_len"], operand["heap_addr"])
                            save(directory / "consumed-target.json", {"queue": captured, "operand": operand,
                                                                      "operand_cq_cursor": operand_cq_cursor})
                candidate_targets = [c for c in captured["all_cqes_before_wrap"][operand_cq_cursor or 0:]
                                     if operand is not None and c["tag"] == operand["tag"]]
                if captured["pending_sqes"] and (not observations or captured != observations[-1]):
                    observations.append(captured)
                    save(directory / "submission-snapshots.json", observations)
                    reads = [s for s in captured["pending_sqes"]
                             if s["opcode"] in (abi["ops"]["READ"], abi["ops"]["SEND"])
                             and s["len"] == len(body)]
                    if reads:
                        need(len(reads) == 1 and reads[0]["len"] == len(body), "WrongHeapRead")
                        if reads[0] != operand:
                            operand = reads[0]
                            operand_cq_cursor = captured["cq_tail"]
                            first_payload = os.pread(mem, operand["len"], operand["addr"])
                controls = [c for c in captured["all_cqes_before_wrap"] if c["tag"] == 2**64 - 1]
                if not permanent and controls and candidate_targets and captured["cq_head"] == captured["cq_tail"]:
                    need(captured == snapshot(mem, info, abi), "UnstableFinalQueueSnapshot")
                    final = captured
                    if operand is not None:
                        length, address = operand.get("heap_len", operand["len"]), operand.get("heap_addr", operand["addr"])
                        payload = os.pread(mem, length, address)
                        need(len(payload) == length, "ShortOperandSnapshot")
                        final["payload_sha256"] = hashlib.sha256(payload).hexdigest()
                        final["payload_matches_file"] = payload == body
                    save(directory / "pre-unmap.json", final)
                    break
                if permanent and operand is not None and trace.count("(INJECTED)") >= 2:
                    final = snapshot(mem, info, abi)
                    final["payload_unchanged"] = os.pread(mem, operand["len"], operand["addr"]) == first_payload
                    final["owned_fds"] = sorted(int(p.name) for p in Path(f"/proc/{info['pid']}/fd").iterdir())
                    save(directory / "stalled.json", final)
                    break
            need(process.poll() is None, "TraceeExitedBeforeObservation")
            time.sleep(0.003)
        need(final is not None, "OwnedProbeDeadline")
    finally:
        primary = sys.exception()
        failures: list[BaseException] = []
        try:
            if process is not None:
                os.set_blocking(stderr_r, False)
                if permanent or final is None:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline and process.poll() is None:
                    if select.select([stderr_r], [], [], 0.02)[0]:
                        error_output.extend(os.read(stderr_r, 65536))
                    if stream is not None and select.select([stream], [], [], 0)[0]:
                        output.extend(os.read(stream.fileno(), 65536))
                while select.select([stderr_r], [], [], 0)[0]:
                    data = os.read(stderr_r, 65536)
                    if not data:
                        break
                    error_output.extend(data)
        except BaseException as error:
            failures.append(error)
        finally:
            try:
                if process is not None:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
            except BaseException as error:
                failures.append(error)
            finally:
                releases: list[Callable[[], None]] = [partial(os.close, stderr_r)]
                if mem is not None:
                    releases.append(partial(os.close, mem))
                if peer is not None:
                    releases.append(peer.close)
                if stream is not None:
                    releases.append(stream.close)
                if stderr_w >= 0:
                    releases.append(partial(os.close, stderr_w))
                for release in releases:
                    try:
                        release()
                    except BaseException as error:
                        failures.append(error)
        (directory / "stdout.log").write_bytes(output)
        (directory / "stderr.log").write_bytes(error_output)
        save(directory / "result.json", {"returncode": process.returncode if process is not None else None,
                                         "operand": operand, "operand_cq_cursor": operand_cq_cursor, "final": final,
                                         "stderr_first": bytes(error_output[fill:]).split(b"\n", 1)[0].decode("ascii", "replace")})
        if failures:
            raise BaseExceptionGroup("Owned probe cleanup failed", ([primary] if primary is not None else []) + failures)


    result = json.loads((directory / "result.json").read_text())
    fault_pattern = (r"^(\d+) \d+\.\d+ \[\s*\d+\] io_uring_enter\((\d+)<anon_inode:\[io_uring\]>, "
                     r"(\d+), (\d+), (0|IORING_ENTER_GETEVENTS), NULL, 8\) = -1 EAGAIN "
                     r"\(Resource temporarily unavailable\) \(INJECTED\) \(DELAYED\)$")
    faults = [{"pid": int(m[0]), "ring_fd": int(m[1]), "submitted": int(m[2]),
               "waited": int(m[3]), "flags": m[4]}
              for m in re.findall(fault_pattern, (directory / "trace.log").read_text(), re.M)]
    need(info is not None and all(f["pid"] == info["pid"] and f["ring_fd"] == info["ringfd"] for f in faults),
         "ForeignInjectedEnter")
    result["faults"] = faults
    save(directory / "result.json", result)
    return result
