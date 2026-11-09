import copy,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("candidate_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"notes/evidence/kan-15-bg05-gate/candidate-runtime.json"
class RejectionDispositionTests(unittest.TestCase):
    def snapshots(self):
        report=json.loads(EVIDENCE.read_text())
        receipt=report["rejection_disposition_observation"]["before"]
        before={"queues":receipt["before"]["queue"],
                "business_invocations":receipt["before"]["business_audit"]}
        after={"queues":receipt["after"]["queue"],
               "business_invocations":receipt["after"]["business_audit"]}
        return before,after
    def test_saved_live_receipt_matches_exact_queue_and_invocation_deltas(self):
        before,after=self.snapshots()
        result=h.compare_rejection_effect_deltas(before,after,
            "jms.queue.HandlingEventRegistrationAttemptQueue",
            "jms.queue.RejectedRegistrationAttemptsQueue")
        self.assertTrue(result["all_queue_and_invocation_deltas_bounded"])
        self.assertEqual(result["business_invocation_deltas"],
                         result["expected_business_invocation_deltas"])
        self.assertEqual(result["queue_counter_deltas"],result["expected_queue_counter_deltas"])
    def test_unrelated_queue_mutation_is_rejected(self):
        before,after=self.snapshots()
        changed=copy.deepcopy(after)
        changed["queues"]["jms.queue.DLQ"]["MessagesAdded"]+=1
        result=h.compare_rejection_effect_deltas(before,changed,
            "jms.queue.HandlingEventRegistrationAttemptQueue",
            "jms.queue.RejectedRegistrationAttemptsQueue")
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
    def test_unrelated_business_invocation_is_rejected(self):
        before,after=self.snapshots()
        changed=copy.deepcopy(after)
        changed["business_invocations"]["unrelated.Service#mutate"]=1
        result=h.compare_rejection_effect_deltas(before,changed,
            "jms.queue.HandlingEventRegistrationAttemptQueue",
            "jms.queue.RejectedRegistrationAttemptsQueue")
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
    def test_new_after_only_queue_is_rejected(self):
        before,after=self.snapshots()
        changed=copy.deepcopy(after)
        changed["queues"]["jms.queue.InjectedQueue"]={name:0 for name in h.QUEUE_ATTRIBUTES}
        result=h.compare_rejection_effect_deltas(before,changed,
            "jms.queue.HandlingEventRegistrationAttemptQueue",
            "jms.queue.RejectedRegistrationAttemptsQueue")
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
if __name__=="__main__":unittest.main()
