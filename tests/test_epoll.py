import json
import unittest

from hypothesis import given, settings, strategies as st
from tests.test_examples import CASES, ROOT, run

FIXTURES = ROOT / "testdata/inputs"
DEFAULT = json.loads((FIXTURES / "epoll-default-plan.json").read_text())
PRIMARY, SECONDARY, CURRENT = 72623859790382856, 18364758544493064720, 18446744073709551615


def control(tag, operation, event, result, epoll="epoll", target="pipe"):
    return {"request": {"operation": "EPOLL_CTL", "tag": tag, "epoll_descriptor": epoll,
                        "target_descriptor": target, "control_operation": operation, "flags": 0, "event": event},
            "cqe": {"tag": tag, "result": result, "flags": 0}}


def read(tag, data):
    return {"request": {"operation": "READ", "tag": tag, "length": len(data), "offset": CURRENT, "flags": 0},
            "cqe": {"tag": tag, "result": len(data), "flags": 0}, "data": list(data)}


def expected_report(commands):
    """Independent interest-list/FIFO model; no native code or generated map is imported."""
    event = {"mask": 1, "token": PRIMARY}
    failures = [control(1000000, 1, event, -9, epoll="invalid"),
                control(1000001, 1, event, -9, target="retired"),
                control(1000002, 1, event, -22, epoll="pipe"),
                control(1000003, 99, event, -22),
                control(1000004, 1, event, -22, target="epoll"),
                control(1000005, 1, None, -14)]
    registered, mask, token, closed, data = False, 0, None, False, []
    def state():
        return {"registered": registered, "mask": mask, "token": token, "queued": len(data), "closed": closed}
    steps = []
    for index, command in enumerate(commands):
        tag = index + 1
        step = {"command": command, "tag": tag, "before": state(), "after": None,
                "control": None, "read": None, "write": [], "events": None}
        if command == "add":
            step["control"] = control(tag, 1, event, -17 if registered else 0)
            if not registered:
                registered, mask, token = True, 1, PRIMARY
        elif command == "modify":
            new_mask = 4 if mask == 1 else 1
            step["control"] = control(tag, 3, {"mask": new_mask, "token": SECONDARY}, 0 if registered else -2)
            if registered:
                mask, token = new_mask, SECONDARY
        elif command == "delete":
            step["control"] = control(tag, 2, None, 0 if registered else -2)
            registered, mask, token = False, 0, None
        elif command == "write":
            data.append(index)
            step["write"] = [index]
        elif command == "wait":
            step["events"] = [{"mask": 1, "token": token}] if registered and mask == 1 and data else []
        elif command == "drain":
            step["read"] = read(tag, data)
            data = []
        elif command == "close":
            registered, mask, token, closed, data = False, 0, None, True, []
        else:
            raise AssertionError("Unknown model command")
        step["after"] = state()
        steps.append(step)
    cleanup = {"control": control(1000010, 2, None, 0) if registered else None,
               "read": read(1000011, data) if data else None, "events": [],
               "pipe_closed": [True, True], "epoll_closed": True}
    return {"failures": failures, "steps": steps, "cleanup": cleanup, "retired_descriptor_closed": True}


def valid_commands(choices):
    vocabulary = ("add", "modify", "delete", "write", "wait", "drain", "close")
    closed, queued, commands = False, 0, []
    for choice in choices:
        command = vocabulary[choice]
        if (closed and command != "wait") or (command == "drain" and queued == 0):
            command = "wait"
        if command == "write":
            queued += 1
        elif command == "drain":
            queued = 0
        elif command == "close":
            closed, queued = True, 0
        commands.append(command)
    return commands


class EpollContracts(unittest.TestCase):
    @settings(max_examples=CASES, deadline=None, derandomize=True)
    @given(st.lists(st.integers(0, 6), min_size=1, max_size=64))
    def test_commands_follow_interest_list_and_fifo_model(self, choices):
        """Kills wrong ADD/MOD/DEL state, mask/tag truncation, stale readiness, discarded/lost FIFO bytes."""
        commands = valid_commands(choices)
        result = run("reference-epoll", *commands)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(json.loads(result.stdout), expected_report(commands))

    def test_literal_and_fixed_plans(self):
        """Kills shared-model blindness, fake ctl success, optional-event misuse and exit-only cleanup."""
        commands = json.loads((FIXTURES / "epoll-literal-plan.json").read_text())
        literal = json.loads((FIXTURES / "epoll-report.json").read_text())
        for _ in range(2):
            result = run("reference-epoll", *commands)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout), literal)
        for case in json.loads((FIXTURES / "epoll-plans.json").read_text()):
            with self.subTest(case=case["name"]):
                result = run("reference-epoll", *case["commands"])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, b"")
                self.assertEqual(json.loads(result.stdout), expected_report(case["commands"] or DEFAULT))

    def test_invalid_plans_are_typed(self):
        """Kills late validation, FD-use-after-close, empty drains and unbounded command plans."""
        for case in json.loads((FIXTURES / "epoll-invalid-plans.json").read_text()):
            with self.subTest(case=case["name"]):
                result = run("reference-epoll", *case["commands"], success=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr.splitlines()[0], ("error: " + case["error"]).encode())


if __name__ == "__main__":
    unittest.main()
