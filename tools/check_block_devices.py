#!/usr/bin/env python3
"""Execute native readers/copy against owned, read-only QEMU virtio disks."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SIZES = (0, 512, 33280, 131584)
PROGRAMS = ("readv", "raw-cat", "cat", "cp")


def archive(entries):
    output = bytearray()
    for index, (name, mode, data, major, minor) in enumerate(entries, 1):
        encoded = name.encode() + b"\0"
        fields = [index, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(encoded), 0]
        output.extend(("070701" + "".join(f"{field:08x}" for field in fields)).encode())
        output.extend(encoded)
        output.extend(b"\0" * (-len(output) % 4))
        output.extend(data)
        output.extend(b"\0" * (-len(output) % 4))
    return gzip.compress(bytes(output), mtime=0)


def verify(kernel, busybox, expect_copy_rejection=False):
    if platform.machine() != "x86_64":
        raise RuntimeError("This VM verifier requires x86_64; other architectures remain unverified")
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        raise RuntimeError("KVM is unavailable; no block-device verification was performed")
    kernel, busybox = kernel.resolve(strict=True), busybox.resolve(strict=True)
    if subprocess.check_output(["zig", "version"], text=True).strip() != "0.17.0":
        raise RuntimeError("Exactly Zig 0.17.0 is required")
    subprocess.run(["zig", "build"], cwd=ROOT, check=True)
    entries = [(name, stat.S_IFDIR | 0o755, b"", 0, 0)
               for name in ["bin", "dev", "proc", "sys", "tmp", "fixtures", "examples"]]
    entries.append(("dev/console", stat.S_IFCHR | 0o600, b"", 5, 1))
    entries.append(("bin/busybox", stat.S_IFREG | 0o755, busybox.read_bytes(), 0, 0))
    compare = Path("/usr/bin/cmp").resolve(strict=True)
    entries.append(("bin/cmp", stat.S_IFREG | 0o755, compare.read_bytes(), 0, 0))
    dependencies = "\n".join(subprocess.check_output(["ldd", str(path)], text=True)
                             for path in [busybox, compare])
    for path in sorted(set(re.findall(r"/[^\s()]+", dependencies))):
        library = Path(path)
        directories = list(library.parent.parents)[:-1] + [library.parent]
        for directory in directories:
            relative = str(directory).lstrip("/")
            if relative and not any(entry[0] == relative for entry in entries):
                entries.append((relative, stat.S_IFDIR | 0o755, b"", 0, 0))
        entries.append((path.lstrip("/"), stat.S_IFREG | 0o755, library.read_bytes(), 0, 0))
    applets = subprocess.check_output([str(busybox), "--list"], text=True).splitlines()
    entries.extend((f"bin/{name}", stat.S_IFLNK | 0o777, b"busybox", 0, 0)
                   for name in applets if name not in {"busybox", "cmp"})
    source_paths = [ROOT / "build.zig", ROOT / "examples/cp.zig", ROOT / "examples/support.zig",
                    ROOT / "examples/cat.zig", ROOT / "examples/raw_cat.zig", ROOT / "examples/readv.zig",
                    ROOT / "tests/fixtures/block-init.sh", ROOT / "tests/fixtures/vm-mount.zig", Path(__file__)]
    for name in PROGRAMS:
        entries.append((f"examples/{name}", stat.S_IFREG | 0o755,
                        (ROOT / "zig-out/bin" / name).read_bytes(), 0, 0))
    entries.append(("init", stat.S_IFREG | 0o755,
                    (ROOT / "tests/fixtures/block-init.sh").read_bytes(), 0, 0))
    if expect_copy_rejection:
        entries.append(("expect-copy-rejection", stat.S_IFREG | 0o644, b"", 0, 0))
    with tempfile.TemporaryDirectory(prefix="loti-block-vm-") as directory:
        temporary = Path(directory)
        subprocess.run(["zig", "build-exe", str(ROOT / "tests/fixtures/vm-mount.zig"),
                        f"-femit-bin={temporary / 'vm-mount'}"], check=True, cwd=ROOT)
        entries.append(("bin/vm-mount", stat.S_IFREG | 0o755,
                        (temporary / "vm-mount").read_bytes(), 0, 0))
        command = ["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-m", "512",
                   "-smp", "2", "-no-reboot", "-nographic", "-monitor", "none", "-nic", "none",
                   "-kernel", str(kernel), "-initrd", str(temporary / "initramfs.gz"),
                   "-append", "console=ttyS0 quiet panic=-1 rdinit=/init"]
        hashes = {}
        for size in SIZES:
            payload = bytes(range(256)) * (size // 256)
            disk = temporary / f"{size}.raw"
            disk.write_bytes(payload)
            hashes[str(size)] = hashlib.sha256(payload).hexdigest()
            entries.append((f"fixtures/{size}.raw", stat.S_IFREG | 0o644, payload, 0, 0))
            command.extend(["-drive", f"file={disk},format=raw,if=virtio,readonly=on"])
        entries.append(("TRAILER!!!", 0, b"", 0, 0))
        (temporary / "initramfs.gz").write_bytes(archive(entries))
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        events = []
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
        expected = [{"event": "loti.vm.case", "program": name, "size": size,
                     "exit_code": 1 if expect_copy_rejection and name == "cp" else 0,
                     "result": "known_bug" if expect_copy_rejection and name == "cp" else "pass"}
                    for size in SIZES for name in PROGRAMS]
        if (result.returncode != 0 or len(events) != 18
                or events[0].get("event") != "loti.vm.kernel"
                or events[1:-1] != expected
                or events[-1] != {"event": "loti.vm.complete", "cases": 16}):
            raise RuntimeError(f"VM verification failed:\n{result.stdout}\n{result.stderr}")
        if any(hashlib.sha256((temporary / f"{size}.raw").read_bytes()).hexdigest() != hashes[str(size)]
               for size in SIZES):
            raise RuntimeError("Owned input disk changed despite read-only attachment")
    return {
        "scope": "Author-run x86_64 KVM guest, disposable read-only disks; not independent review or host-storage access.",
        "kernel_release": events[0]["release"], "kernel_sha256": hashlib.sha256(kernel.read_bytes()).hexdigest(),
        "busybox_sha256": hashlib.sha256(busybox.read_bytes()).hexdigest(),
        "compare_sha256": hashlib.sha256(compare.read_bytes()).hexdigest(),
        "qemu_version": subprocess.check_output(["qemu-system-x86_64", "--version"], text=True).splitlines()[0],
        "fixture_sha256": hashes, "cases": events[1:-1],
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in source_paths},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", type=Path, default=Path("/usr/lib/modules") / platform.release() / "vmlinuz")
    parser.add_argument("--busybox", type=Path, default=Path("/usr/lib/initcpio/busybox"))
    parser.add_argument("--expect-copy-rejection", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = verify(args.kernel, args.busybox, args.expect_copy_rejection)
        text = json.dumps(report, indent=2) + "\n"
        if args.report:
            args.report.write_text(text)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"event": "loti.vm.failed", "error_type": type(error).__name__,
                          "detail": str(error)}), file=sys.stderr)
        raise SystemExit(1) from error
    print(text, end="")


if __name__ == "__main__":
    main()
