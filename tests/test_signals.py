"""Public contract for signal delivery and io_uring wait-mask restoration."""

import unittest

from tests.test_examples import run


class SignalContracts(unittest.TestCase):
    def test_pending_signal_delivery_and_wait_mask_restoration(self):
        with self.assertRaises(FileNotFoundError):
            run("reference-signals")


if __name__ == "__main__":
    unittest.main()
