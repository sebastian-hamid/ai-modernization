import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("candidate_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
INPUT="jms.queue.HandlingEventRegistrationAttemptQueue"
INTAKE="jms.queue.HandlingAttemptQuarantineIntakeQueue"
def snapshots():
    queues={name:{attribute:0 for attribute in h.QUEUE_ATTRIBUTES}
        for name in (INPUT,INTAKE,"jms.queue.DLQ")}
    before={"queues":queues,"business_invocations":{},"tables":{
        name:{"rows":1,"sha256":"before"} for name in (
            "location","voyage","cargo","leg","handling_event","carrier_movement",
            "handling_attempt_quarantine","handling_quarantine_state","handling_quarantine_replay_audit",
            "handling_request_idempotency","handling_quarantine_pending")}}
    after=copy.deepcopy(before)
    after["queues"][INPUT].update(MessagesAdded=1,MessagesKilled=1,AcknowledgeAttempts=4)
    after["queues"][INTAKE].update(MessagesAdded=1,MessagesAcknowledged=1,AcknowledgeAttempts=1)
    after["tables"]["handling_attempt_quarantine"]={"rows":2,"sha256":"after"}
    after["tables"]["handling_request_idempotency"]={"rows":2,"sha256":"after"}
    after["business_invocations"]={
        "net.java.cargotracker.application.internal.DefaultHandlingEventService#registerHandlingEvent":3,
        "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage":3,
        "net.java.cargotracker.infrastructure.messaging.jms.HandlingWorkerAudit#recordConsumedAttempt":3,
        "net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService#markQuarantined":1,
        "net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService#reserve":4,
        "net.java.cargotracker.infrastructure.quarantine.HandlingQuarantineCapacityAlert#pendingResolved":1,
        "net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineService#registerLegacyRequest":1,
        "net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineService#store":1,
        "net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineConsumer#onMessage":1,
        "net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService#beginProcessing":3,
        "net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService#eligibleForQuarantine":1}
    return before,after
class QuarantineDispositionTests(unittest.TestCase):
    def test_log_sanitization_checks_only_the_newly_appended_segment(self):
        self.assertEqual(h.appended_log_text("booking ID-123\n","booking ID-123\nworker retry\n"),"worker retry\n")
        self.assertIsNone(h.appended_log_text("before\n","replaced logs\n"))
    def test_remote_producer_boundary_requires_all_machine_principal_denials(self):
        observation={"anonymousDenied":True,"humanAuthenticated":[True,True,True],
            "humanSendDenied":[True,True,True],"machinePrincipals":["batch-worker","handling-worker","inspection-worker","notification-worker"],
            "machineAuthenticated":[True,True,True,True],"machineSendDenied":[True,True,True,True],
            "producerAuthenticated":True,"trustedAllowed":True,
            "rejectedQueueDenied":True,"deliveredQueueDenied":True}
        self.assertTrue(h.remote_producer_boundary_verified(observation,True,True))
        for field,value in [("machinePrincipals",["batch-worker","handling-worker","notification-worker","inspection-worker"]),
                            ("machineAuthenticated",[True,True,False,True]),
                            ("machineSendDenied",[True,False,True,True]),
                            ("humanSendDenied",[True,True,False]),("anonymousDenied",False),
                            ("producerAuthenticated",False)]:
            with self.subTest(field=field):
                self.assertFalse(h.remote_producer_boundary_verified({**observation,field:value},True,True))
        self.assertFalse(h.remote_producer_boundary_verified(observation,False,True))
        self.assertFalse(h.remote_producer_boundary_verified(observation,True,False))
    def test_exact_retry_and_quarantine_deltas_are_accepted(self):
        before,after=snapshots()
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE)
        self.assertTrue(result["all_queue_and_invocation_deltas_bounded"])
        self.assertTrue(result["business_tables_unchanged"])
        self.assertEqual(result["business_invocation_deltas"],result["expected_business_invocation_deltas"])
        self.assertEqual(result["queue_counter_deltas"],result["expected_queue_counter_deltas"])
    def test_request_id_flow_accounts_for_rest_producer_and_skips_legacy_registration(self):
        before,after=snapshots()
        calls=after["business_invocations"]
        calls["net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService#reserve"]=1
        calls.pop("net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineService#registerLegacyRequest")
        calls["net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptProducer#publish"]=1
        calls["net.java.cargotracker.interfaces.handling.rest.HandlingReportService#submitReport"]=1
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE,{
            "net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService#reserve":1,
            "net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineService#registerLegacyRequest":None,
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptProducer#publish":1,
            "net.java.cargotracker.interfaces.handling.rest.HandlingReportService#submitReport":1})
        self.assertTrue(result["all_queue_and_invocation_deltas_bounded"])
    def test_unrelated_queue_mutation_is_rejected(self):
        before,after=snapshots();after["queues"]["jms.queue.DLQ"]["MessagesAdded"]+=1
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE)
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
    def test_unrelated_business_invocation_is_rejected(self):
        before,after=snapshots();after["business_invocations"]["unrelated.Service#mutate"]=1
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE)
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
    def test_business_table_mutation_is_rejected(self):
        before,after=snapshots();after["tables"]["cargo"]={"rows":2,"sha256":"changed"}
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE)
        self.assertFalse(result["business_tables_unchanged"])
    def test_missing_or_unexpected_queue_is_rejected(self):
        before,after=snapshots();after["queues"].pop(INTAKE)
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE)
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
        before,after=snapshots();after["queues"]["jms.queue.InjectedQueue"]={name:0 for name in h.QUEUE_ATTRIBUTES}
        result=h.compare_quarantine_effect_deltas(before,after,INPUT,INTAKE)
        self.assertFalse(result["all_queue_and_invocation_deltas_bounded"])
if __name__=="__main__":unittest.main()
