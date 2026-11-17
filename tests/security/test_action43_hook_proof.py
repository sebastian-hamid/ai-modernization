import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import action43_hook_proof as action43
import replay_action43_hook_retirement as replay_action43

class Action43HookProofTests(unittest.TestCase):
    def test_fresh_candidate_proves_hook_unbound_and_replacement_access(self):
        proof = action43.build_validation()
        self.assertEqual(proof["result"], "HOOK_SPECIFIC_PROOF_VERIFIED_PENDING_USER_RETIREMENT_DECISION")
        self.assertEqual(proof["source_evidence"]["candidate_init_flow_facelet_bindings"], [])
        self.assertTrue(proof["source_evidence"]["candidate_holderbean_initflow_method_retained"])
        actors = proof["fresh_run_evidence"]["actor_observations"]
        self.assertEqual([actors[x]["status"] for x in ("anonymous", "Reader", "Operator", "Administrator")], [303, 403, 200, 200])
        self.assertTrue(actors["Operator"]["replacement_form_and_workflow_verified"])
        self.assertTrue(actors["Administrator"]["replacement_form_and_workflow_verified"])

    def test_candidate_hook_reintroduction_is_detected_without_mutating_files(self):
        legacy = (action43.ROOT / action43.LEGACY_PAGE).read_text()
        current = (action43.ROOT / action43.CANDIDATE_PAGE).read_text()
        bean = (action43.ROOT / action43.HOLDER_BEAN).read_text()
        facelets = [("mobile.xhtml", current + '\n<f:viewAction action="#{holderBean.initFlow}" />\n')]
        with self.assertRaisesRegex(ValueError, "old initFlow hook remains bound"):
            action43.validate_hook_markup(legacy, current, facelets, bean)

    def test_approved_replay_retires_only_action43_and_clears_current_retirement_gate(self):
        import json
        import tempfile
        from pathlib import Path
        prior = json.loads(replay_action43.INPUT.read_text())
        with tempfile.TemporaryDirectory() as temp:
            result = replay_action43.replay(Path(temp) / "replay.json")
        self.assertEqual(result["current_counts"], {"PASS": 470})
        current_gate = json.loads(replay_action43.CURRENT_GATE.read_text())
        self.assertEqual(result["current_results"], current_gate["current_results"])
        self.assertEqual(len(result["current_results"]), 470)
        self.assertEqual(result["current_capability_source_sha256"], replay_action43.CURRENT_GATE_SHA256)
        self.assertEqual(result["retirement_counts_after_action43"], {"RETIRED": 76})
        self.assertEqual(result["effective_current_retirement_gate_exit"], 0)
        self.assertEqual(result["historical_audit_counts"], {"PASS": 317, "FAIL": 7, "BLOCKED": 178})
        self.assertEqual(result["historical_audit_exit"], 1)
        selected = set(result["changed_cases"])
        self.assertEqual(len(selected), 4)
        for before in prior["retirement_results"]:
            after = next(row for row in result["retirement_results"] if row["case"] == before["case"])
            if before["case"] in selected:
                self.assertEqual(after["outcome"], "RETIRED")
                self.assertTrue(after["specific_negative_entry_verified"])
            else:
                self.assertEqual(after, before)

if __name__ == "__main__":
    unittest.main()