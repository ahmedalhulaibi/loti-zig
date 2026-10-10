"""Public contract for signal delivery and io_uring wait-mask restoration."""

import json
from pathlib import Path
import signal
import unittest

from tests.test_examples import run


ROOT = Path(__file__).resolve().parent.parent


def expected_report():
    def masks(value):
        if isinstance(value, dict):
            return {key: masks(item) for key, item in value.items()}
        if isinstance(value, list):
            if value and isinstance(value[0], str):
                return sum(1 << (int(getattr(signal, name)) - 1) for name in value)
            return [masks(item) for item in value]
        return value
    report = masks(json.loads((ROOT / "testdata/inputs/signal-contract.json").read_text()))
    assert isinstance(report, dict)
    report["mask_bytes"] = (max(map(int, signal.valid_signals())) + 7) // 8
    report["initial_mask"] = sum(1 << (int(item) - 1) for item in signal.pthread_sigmask(signal.SIG_BLOCK, []))
    return report


class SignalContracts(unittest.TestCase):
    def test_pending_signal_delivery_and_wait_mask_restoration(self):
        self.assertEqual(json.loads(run("reference-signals").stdout), expected_report())

    def test_signal_reference_rejects_arguments(self):
        cases = json.loads((ROOT / "testdata/inputs/signal-invalid-arguments.json").read_text())
        for name, arguments in cases.items():
            with self.subTest(case=name):
                result = run("reference-signals", *arguments, success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.decode().splitlines()[0], "error: ExpectedNoSignalArguments")


if __name__ == "__main__":
    unittest.main()
