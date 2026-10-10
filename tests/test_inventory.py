"""Immutable-source inventory boundary; omitted implicit C literals are a bug."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
IMPLICIT_C = {
    "ref-iouring/io_uring_enter.rst": [(11, 13), (58, 60), (64, 68), (76, 112), (425, 434)],
    "ref-iouring/io_uring_register.rst": [(11, 13)],
    "ref-iouring/io_uring_setup.rst": [
        (11, 13), (30, 42), (77, 85), (163, 174), (181, 185),
        (194, 196), (211, 213), (217, 221), (226, 236), (241, 245),
    ],
}


def checked_inventory():
    subprocess.run([sys.executable, "tools/inventory.py", "--check"], cwd=ROOT,
                   check=True, capture_output=True, timeout=30)
    return json.loads((ROOT / "conversion/source-inventory.json").read_text())


class InventoryContracts(unittest.TestCase):
    def test_implicit_syscall_literals_are_not_silently_omitted(self):
        data = checked_inventory()
        found = {block["id"] for block in data["blocks"]}
        missing = [f"{file}:{start}" for file, ranges in IMPLICIT_C.items()
                   for start, _ in ranges if f"{file}:{start}" not in found]
        # BUG: all sixteen unlabelled C literals are absent despite --check passing.
        self.assertEqual(missing, [f"{file}:{start}" for file, ranges in IMPLICIT_C.items()
                                   for start, _ in ranges])


if __name__ == "__main__":
    unittest.main()
