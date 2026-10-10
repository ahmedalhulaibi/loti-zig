import json
import subprocess
import unittest

from hypothesis import example, given, settings, strategies as st

from tests.test_examples import CASES, ROOT, run

CURRENT = (1 << 64) - 1
DEFAULT = ["arm", "write", "wait", "write", "quiet", "arm", "wait", "drain", "arm", "cancel", "missing", "quiet"]


def request(operation, tag, *, mask=None, target=None, length=0, offset=0):
    return {"operation": operation, "tag": tag, "mask": mask, "target": target,
            "length": length, "offset": offset, "flags": 0}


def cqe(tag, result):
    return {"tag": tag, "result": result, "flags": 0}


def expected_report(commands):
    """Independent one-shot ownership/FIFO model; does not import a producer."""
    pending, data, steps = None, [], []
    for index, command in enumerate(commands):
        tag = index + 1
        step = {"command": command, "tag": tag, "poll_before": pending,
                "queued_before": len(data), "request": None, "cqes": [],
                "data": [], "empty_timeout": False}
        if command == "arm":
            pending = tag
            step.update(request=request("POLL_ADD", tag, mask=1), empty_timeout=not data)
        elif command == "write":
            data.append(index)
            step["data"] = [index]
        elif command == "wait":
            step["cqes"] = [cqe(pending, 1)]
            pending = None
        elif command == "cancel":
            step.update(request=request("POLL_REMOVE", tag, target=pending),
                        cqes=[cqe(pending, -125), cqe(tag, 0)])
            pending = None
        elif command == "drain":
            step.update(request=request("READ", tag, length=len(data), offset=CURRENT),
                        cqes=[cqe(tag, len(data))], data=list(data))
            data = []
        elif command == "missing":
            step.update(request=request("POLL_REMOVE", tag, target=CURRENT), cqes=[cqe(tag, -2)])
        elif command == "quiet":
            step["empty_timeout"] = True
        else:
            raise AssertionError(command)
        step.update(poll_after=pending, queued_after=len(data))
        steps.append(step)
    assert pending is None
    cleanup = {"request": request("READ", 1000002, length=len(data), offset=CURRENT) if data else None,
               "cqes": [cqe(1000002, len(data))] if data else [], "data": list(data)}
    return {"steps": steps, "cleanup": cleanup,
            "invalid_descriptor": {"request": request("POLL_ADD", 1000000, mask=1), "cqe": cqe(1000000, -9)},
            "absent_target": {"request": request("POLL_REMOVE", 1000001, target=CURRENT), "cqe": cqe(1000001, -2)},
            "hup": {"request": request("POLL_ADD", 1000003, mask=1), "empty_timeout": True,
                    "cqe": cqe(1000003, 16),
                    "eof": {"request": request("READ", 1000004, length=1, offset=CURRENT),
                            "cqe": cqe(1000004, 0), "data": []}},
            "pipe_closed": [True, True], "final_queue_empty": True}


def commands_from_choices(choices):
    armed, queued, commands = False, 0, []
    for choice in choices:
        available = (["wait"] if queued else ["write", "cancel"]) if armed else ["arm", "write", "missing", "quiet"] + (["drain"] if queued else [])
        command = available[choice % len(available)]
        commands.append(command)
        if command == "arm": armed = True
        elif command == "write": queued += 1
        elif command in ("wait", "cancel"): armed = False
        elif command == "drain": queued = 0
    if armed: commands.append("wait" if queued else "cancel")
    return commands


class PollContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None, database=None)
    @given(choices=st.lists(st.integers(min_value=0, max_value=255), min_size=1, max_size=30))
    @example(choices=[0, 1, 0, 3, 0, 0, 4, 0, 1])
    def test_poll_commands_follow_ownership_and_one_shot_model(self, choices):
        """Kills wrong masks/tags, stale one-shot CQEs, lost FIFO bytes and double acknowledgement."""
        commands = commands_from_choices(choices)
        self.assertEqual(json.loads(run("reference-poll", *commands).stdout), expected_report(commands))

    def test_literal_oracle_and_valid_plans(self):
        """Kills false cancellation success, omitted rearm, HUP/EOF substitution and exit-only cleanup."""
        fixtures = ROOT / "testdata/inputs"
        literal = json.loads((fixtures / "poll-report.json").read_text())
        commands = json.loads((fixtures / "poll-literal-plan.json").read_text())
        for _ in range(2):
            self.assertEqual(json.loads(run("reference-poll", *commands).stdout), literal)
        for case in json.loads((fixtures / "poll-plans.json").read_text()):
            with self.subTest(case=case["name"]):
                args = case["commands"]
                self.assertEqual(json.loads(run("reference-poll", *args).stdout), expected_report(args or DEFAULT))

    def test_invalid_command_states_are_rejected_before_execution(self):
        """Kills weakened state/length/name validation and pending-poll leaks on invalid plans."""
        for case in json.loads((ROOT / "testdata/inputs/poll-invalid-plans.json").read_text()):
            with self.subTest(case=case["name"]):
                result = subprocess.run([str(ROOT / "zig-out/bin/reference-poll"), *case["commands"]],
                                        capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.decode().splitlines()[0], "error: " + case["error"])


if __name__ == "__main__":
    unittest.main()
