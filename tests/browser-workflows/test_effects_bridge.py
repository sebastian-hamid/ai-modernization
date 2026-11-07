import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location("fixture_bridge", Path(__file__).with_name("effects_bridge.py"))
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class EffectsBridgeTests(unittest.TestCase):
    def test_known_stage_receives_fresh_snapshot_over_stdin(self):
        script = (
            'import json,sys; '
            'print(\'@@LAB_EFFECTS@@{"id":0,"stage":"cancel-editor:Operator:before"}\',flush=True); '
            'reply=json.loads(sys.stdin.readline()); '
            'assert reply["id"]==0 and reply["snapshot"]["fixture_id"]=="owned"; '
            'print("done",flush=True)'
        )
        calls = []
        def capture(stage,budget):
            self.assertGreater(budget,0)
            self.assertLessEqual(budget,5)
            calls.append(stage)
            return {"fixture_id": "owned"}
        result = bridge.run_browser_with_effects([sys.executable, "-u", "-c", script], capture, 5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls, ["cancel-editor:Operator:before"])
        self.assertEqual(result.stdout, "done\n")

    def test_unknown_stage_never_invokes_observer(self):
        script = 'print(\'@@LAB_EFFECTS@@{"id":0,"stage":"arbitrary"}\',flush=True); input()'
        def capture(stage,budget):
            self.fail("Unexpected observation")
        with self.assertRaises(RuntimeError):
            bridge.run_browser_with_effects([sys.executable, "-u", "-c", script], capture, 5)

    def test_after_stage_cannot_precede_before(self):
        script = 'print(\'@@LAB_EFFECTS@@{"id":0,"stage":"cancel-editor:Operator:after"}\',flush=True); input()'
        with self.assertRaises(RuntimeError):
            bridge.run_browser_with_effects([sys.executable, "-u", "-c", script], lambda stage,budget: self.fail("Observer called"), 5)

    def test_quiet_child_has_a_bounded_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            bridge.run_browser_with_effects([sys.executable, "-c", "import time;time.sleep(60)"], lambda stage,budget: {}, 0.1)
