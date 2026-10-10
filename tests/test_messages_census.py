import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_examples import BIN, ROOT

FIXTURES = ROOT / "testdata/inputs"


def inspect_census(text):
    active, names, finished, counts = None, {}, False, []
    for line in text.splitlines():
        opened = re.fullmatch(r'openat\(AT_FDCWD, "/proc/self/fd", O_RDONLY\|O_CLOEXEC\|O_DIRECTORY\)\s+= (\d+)', line)
        if opened:
            if active is not None:
                raise ValueError("OverlappingMessageCensus")
            active, names, finished = int(opened[1]), {}, False
            continue
        row = re.fullmatch(r"getdents64\((\d+), \[(.*)\], 2048\)\s+= (\d+)", line)
        if row:
            if active != int(row[1]) or finished:
                raise ValueError("UnownedMessageCensusRead")
            body, size = row[2], int(row[3])
            entries = list(re.finditer(r'\{d_ino=\d+, d_off=\d+, d_reclen=(\d+), d_type=(DT_DIR|DT_LNK), d_name="([^"]+)"\}', body))
            if ", ".join(match[0] for match in entries) != body or sum(int(match[1]) for match in entries) != size:
                raise ValueError("InvalidMessageCensusRecords")
            if size == 0:
                finished = True
            for entry in entries:
                name = entry[3]
                if name in names or (entry[2] == "DT_DIR" and name not in (".", "..")) or (entry[2] == "DT_LNK" and re.fullmatch(r"[0-9]+", name) is None):
                    raise ValueError("InvalidMessageCensusName")
                names[name] = entry[2]
            continue
        closed = re.fullmatch(r"close\((\d+)\)\s+= 0", line)
        if closed and active == int(closed[1]):
            if not finished or names.get(".") != "DT_DIR" or names.get("..") != "DT_DIR" or names.get(str(active)) != "DT_LNK":
                raise ValueError("IncompleteMessageCensusRead")
            counts.append(sum(kind == "DT_LNK" for kind in names.values()) - 1)
            active = None
    if active is not None or len(counts) != 5:
        raise ValueError("WrongMessageCensusCount")
    deltas = [count - counts[0] for count in counts]
    if deltas != [0, 4, 4, 3, 1]:
        raise ValueError("WrongMessageDescriptorDeltas")
    return {"snapshots": 5, "descriptor_deltas": deltas, "own_directory_excluded": True,
            "all_reads_reach_eof_and_close": True}


class MessageCensusContracts(unittest.TestCase):
    def test_actual_procfs_census_rejects_fake_counts_and_damaged_traces(self):
        """Kills fabricated descriptor census that survives JSON/model and socket-CQE checks."""
        expected = {"snapshots": 5, "descriptor_deltas": [0, 4, 4, 3, 1], "own_directory_excluded": True,
                    "all_reads_reach_eof_and_close": True}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "census.trace"
            result = subprocess.run(["strace", "-qq", "-v", "-e", "trace=openat,getdents64,close", "-o", str(path),
                                     str(BIN / "reference-messages"), str(FIXTURES / "messages-input.bin"), "3"],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), json.loads((FIXTURES / "messages-report.json").read_text()))
            try:
                report = inspect_census(path.read_text())
            except ValueError as error:
                self.fail(f"Invalid public procfs census: {error}")
            self.assertEqual(report, expected)
        original = (FIXTURES / "messages-census.trace").read_text()
        self.assertEqual(inspect_census(original), expected)
        for case in json.loads((FIXTURES / "messages-census-invalid-traces.json").read_text()):
            with self.subTest(case=case["name"]):
                with self.assertRaises(ValueError) as raised:
                    inspect_census(original.replace(case["old"], case["new"], case["count"]))
                self.assertEqual(str(raised.exception), case["error"])


if __name__ == "__main__":
    unittest.main()
