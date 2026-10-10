import json
import re
import tempfile
import unittest
from pathlib import Path

from tests.test_accept import FIXTURES, MODES, inspect_trace, observe


def inspect_flags(text, mode):
    trace = inspect_trace(text)
    listener, accepted = trace["listener_fd"], trace["accepted_fd"]
    entered = re.search(r"io_uring_enter\((\d+),", text)
    if entered is None:
        raise ValueError("IncompleteAcceptKernelTrace")
    ring = int(entered[1])
    values = {"0x2 (flags O_RDWR)": 2, "0x802 (flags O_RDWR|O_NONBLOCK)": 2050,
              "0x1 (flags FD_CLOEXEC)": 1, "0": 0}
    records, closed = {}, {}
    for index, line in enumerate(text.splitlines()):
        matched = re.fullmatch(r"fcntl\((\d+), (F_GETFL|F_GETFD)\)\s+= (.*)", line)
        if matched and not matched[3].startswith("-1"):
            if matched[3] not in values:
                raise ValueError("InvalidAcceptFlagsTrace")
            records.setdefault((int(matched[1]), matched[2]), []).append((index, values[matched[3]]))
        close = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if close:
            closed[int(close[1])] = index
    expected = {(listener, "F_GETFL"): [2050], (listener, "F_GETFD"): [1],
                (accepted, "F_GETFL"): [2 | (MODES[mode] & 2048)],
                (accepted, "F_GETFD"): [int(bool(MODES[mode] & 524288))] * 2, (ring, "F_GETFD"): [1]}
    actual = {key: [value for _, value in rows] for key, rows in records.items()}
    if actual != expected:
        raise ValueError("WrongAcceptFlagQueries")
    if not records[(accepted, "F_GETFD")][0][0] < closed[listener] < records[(accepted, "F_GETFD")][1][0] < closed[accepted] < records[(ring, "F_GETFD")][0][0] < closed[ring]:
        raise ValueError("WrongAcceptOwnershipQueryOrder")
    return {"listener_flags": {"nonblocking": True, "cloexec": True},
            "accepted_flags": {"nonblocking": bool(MODES[mode] & 2048), "cloexec": bool(MODES[mode] & 524288)},
            "successful_flag_queries": 6, "accepted_retained_after_listener_close": True,
            "ring_open_after_accepted_close": True}


class AcceptFlagContracts(unittest.TestCase):
    def test_actual_flags_and_ordered_ownership_queries(self):
        """Reject input-derived flags without actual kernel observations; retain after listener close before teardown."""
        for mode in MODES:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "flags.trace"
                actual, _, _, _ = observe(16, mode, path)
                try:
                    measured = inspect_flags(path.read_text(), mode)
                except ValueError as error:
                    self.fail(f"Invalid public accepted-FD flags trace: {error}")
                self.assertEqual(measured, {"listener_flags": actual["listener_flags"], "accepted_flags": actual["accepted"]["flags"],
                                            "successful_flag_queries": 6, "accepted_retained_after_listener_close": True,
                                            "ring_open_after_accepted_close": True})
        original = (FIXTURES / "accept-flags.trace").read_text()
        self.assertEqual(inspect_flags(original, "both"), {"listener_flags": {"nonblocking": True, "cloexec": True},
                                                          "accepted_flags": {"nonblocking": True, "cloexec": True},
                                                          "successful_flag_queries": 6, "accepted_retained_after_listener_close": True,
                                                          "ring_open_after_accepted_close": True})
        for case in json.loads((FIXTURES / "accept-flags-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_flags(original.replace(case["old"], case["new"], case["count"]), "both")
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
