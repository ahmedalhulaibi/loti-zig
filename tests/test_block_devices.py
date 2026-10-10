"""Block-device public contracts in an isolated, disposable KVM guest."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent


class BlockDeviceContracts(unittest.TestCase):
    def test_owned_virtio_disks_preserve_every_byte(self):
        result = subprocess.run([
            sys.executable, "tools/check_block_devices.py", "--expect-copy-rejection",
        ], cwd=ROOT, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        expected = [{"event": "loti.vm.case", "program": name, "size": size,
                     "exit_code": 1 if name == "cp" else 0,
                     "result": "known_bug" if name == "cp" else "pass"}
                    for size in [0, 512, 33280, 131584]
                    for name in ["readv", "raw-cat", "cat", "cp"]]
        # BUG: the original copy's block-device input contract is rejected.
        self.assertEqual(report["cases"], expected)


if __name__ == "__main__":
    unittest.main()
