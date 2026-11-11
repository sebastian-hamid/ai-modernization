import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
LAB_EFFECTS_SOURCE = (Path(__file__).parents[1] / "candidate-runtime/observer/LabEffects.java").read_text()

spec = importlib.util.spec_from_file_location("fixture_bridge", Path(__file__).with_name("effects_bridge.py"))
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class EffectsBridgeTests(unittest.TestCase):
    def test_bounded_handling_query_matches_candidate_schema(self):
        self.assertIn("FROM HANDLING_EVENT h", LAB_EFFECTS_SOURCE)
        self.assertIn("h.completion_date AS COMPLETION_DATE", LAB_EFFECTS_SOURCE)
        self.assertIn("h.completion_date=?", LAB_EFFECTS_SOURCE)
        self.assertIn('rows.getDate("COMPLETION_DATE")', LAB_EFFECTS_SOURCE)
        self.assertNotIn("FROM HANDLINGEVENT h", LAB_EFFECTS_SOURCE)
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

    def test_bounded_handling_event_observation_uses_sequential_id(self):
        script = """import json,sys; print('@@LAB_HANDLING_EVENT@@{"id":0,"tracking_id":"ABCDEFGH","completion_date":"2032-02-04","location_code":"USCHI"}',flush=True); reply=json.loads(sys.stdin.readline()); assert reply["id"]==0 and reply["snapshot"]["row_count"]==1; print("done",flush=True)"""
        calls=[]
        def inspect(tracking_id,completion_date,location_code,budget):
            calls.append((tracking_id,completion_date,location_code))
            return {"row_count":1,"matches":[]}
        result=bridge.run_browser_with_effects([sys.executable,"-u","-c",script],lambda stage,budget:{},5,inspect_event=inspect)
        self.assertEqual(result.returncode,0)
        self.assertEqual(calls,[("ABCDEFGH","2032-02-04","USCHI")])
        self.assertEqual(result.stdout,"done\n")

    def test_invalid_handling_event_selector_never_invokes_observer(self):
        script = """print('@@LAB_HANDLING_EVENT@@{"id":0,"tracking_id":"ABCDEFGH","completion_date":"2032-02-04","location_code":"FIHEL"}',flush=True); input()"""
        with self.assertRaises(RuntimeError):
            bridge.run_browser_with_effects([sys.executable,"-u","-c",script],lambda stage,budget:{},5,
                inspect_event=lambda *args:self.fail("Unexpected event observation"))

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

    def test_retired_action_stages_are_allowlisted_for_all_actors(self):
        for role in bridge.ROLES:
            for phase in ("before", "after"):
                self.assertIn("retired-action:" + role + ":" + phase, bridge.STAGES)
