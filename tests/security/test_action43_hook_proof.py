import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import action43_hook_proof as action43

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

if __name__ == "__main__":
    unittest.main()