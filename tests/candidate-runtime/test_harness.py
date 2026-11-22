import contextlib,importlib.util,io,json,os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("kan18",Path(__file__).with_name("run_candidate.py"))
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
class LiveRunNamespaceTests(unittest.TestCase):
    def load_candidate(self,instance):
        env=dict(os.environ)
        if instance is None:env.pop("AI_MODERNIZATION_LIVE_RUN_ID",None)
        else:env["AI_MODERNIZATION_LIVE_RUN_ID"]=instance
        with patch.dict(os.environ,env,clear=True):
            spec=importlib.util.spec_from_file_location("candidate_namespace_test",Path(__file__).with_name("run_candidate.py"))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module
    def test_default_namespace_remains_the_shared_kan18_contract(self):
        module=self.load_candidate(None)
        self.assertEqual(module.WORK,module.ROOT/".work/kan18")
        self.assertEqual(module.NAME,"ai-modernization-kan18")
    def test_kan15_namespace_is_isolated_and_uses_its_candidate_image(self):
        module=self.load_candidate("kan15-callback-capture")
        self.assertEqual(module.WORK,module.ROOT/".work/kan15-callback-capture/candidate-runtime")
        self.assertEqual(module.NAME,"ai-modernization-kan15-callback-capture")
        self.assertEqual(module.IMAGE,"ai-modernization-kan15-callback-capture:candidate")
        module=self.load_candidate("kan18-post-kan31-regression")
        self.assertEqual(module.WORK,module.ROOT/".work/kan18-post-kan31-regression/candidate-runtime")
        self.assertEqual(module.NAME,"ai-modernization-kan18-post-kan31-regression")
        self.assertEqual(module.IMAGE,"ai-modernization-kan18-post-kan31-regression:candidate")
        self.assertEqual(module.PROJECT,"kan18p-kan18-post-kan31-regression")
        kan31=self.load_candidate("kan31-post-kan31-regression")
        self.assertNotEqual(module.PROJECT,kan31.PROJECT)
        module=self.load_candidate("kan24-malformed-inputs")
        self.assertEqual(module.WORK,module.ROOT/".work/kan24-malformed-inputs/candidate-runtime")
        self.assertEqual(module.NAME,"ai-modernization-kan24-malformed-inputs")
        self.assertEqual(module.IMAGE,"ai-modernization-kan24-malformed-inputs:candidate")
        module=self.load_candidate("kan31-ttl-policy")
        self.assertEqual(module.WORK,module.ROOT/".work/kan31-ttl-policy/candidate-runtime")
        self.assertEqual(module.NAME,"ai-modernization-kan31-ttl-policy")
        self.assertEqual(module.IMAGE,"ai-modernization-kan31-ttl-policy:candidate")
    def test_invalid_namespace_fails_closed(self):
        with self.assertRaises(ValueError):self.load_candidate("../../kan18")

class BatchInvocationAccountingTests(unittest.TestCase):
    def test_two_unsafe_attempts_and_one_concurrent_form_have_exact_deltas(self):
        self.assertEqual(harness.expected_batch_control_deltas(),{
            "net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#issueNonce":3,
            "net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#start":4,
            "net.java.cargotracker.interfaces.handling.file.BatchImportLauncher#start":3,
            "net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobStarted":1,
            "net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobFinished":1})

class RemoteJmsProbeSeparationTests(unittest.TestCase):
    def test_denial_effects_are_separate_from_trusted_invalid_event(self):
        observation={
            "anonymousDenied":True,"humanAuthenticated":[True,True,True],
            "humanSendDenied":[True,True,True],
            "machinePrincipals":["batch-worker","handling-worker","inspection-worker","notification-worker"],
            "machineAuthenticated":[True,True,True,True],"machineSendDenied":[True,True,True,True],
            "producerAuthenticated":True,"rejectedQueueDenied":True,"deliveredQueueDenied":True}
        self.assertTrue(harness.remote_producer_boundary_verified(observation,True,True))
        self.assertFalse(harness.remote_producer_boundary_verified(observation,False,True))
        self.assertFalse(harness.remote_producer_boundary_verified(observation,True,False))
        root=Path(__file__).resolve().parents[2]
        source=(root/"tests/candidate-runtime/RemoteJmsProducerProbe.java").read_text()
        runner=(root/"tests/candidate-runtime/run_candidate.py").read_text()
        self.assertIn('"authorization".equals(args[1])',source)
        self.assertIn('"trusted-attempt".equals(args[1])',source)
        self.assertIn("producerAuthenticated",source)
        self.assertIn("trustedAllowed",source)
        self.assertIn('"authorization"]',runner)
        self.assertIn('"trusted-attempt"]',runner)
        self.assertIn('rejection_before=producer_after',runner)

    def test_unauthorized_probe_compares_database_queues_and_business_calls(self):
        before={"tables":{"cargo":{"rows":1}},"queues":{"attempt":{"MessagesAdded":0}},
            "business_invocations":{"consumer#onMessage":0}}
        observation={"anonymousDenied":True,"producerAuthenticated":True,
            "humanAuthenticated":[True,True,True],"humanSendDenied":[True,True,True],
            "machineAuthenticated":[True,True,True,True],"machineSendDenied":[True,True,True,True],
            "rejectedQueueDenied":True,"deliveredQueueDenied":True}
        self.assertTrue(harness.remote_producer_unauthorized_effects_unchanged(before,before,observation))
        for section,key in [("tables","cargo"),("queues","attempt"),("business_invocations","consumer#onMessage")]:
            after={name:dict(value) for name,value in before.items()}
            after[section][key]={**after[section][key],"changed":True} if isinstance(after[section][key],dict) else 1
            self.assertFalse(harness.remote_producer_unauthorized_effects_unchanged(before,after,observation),section)

class BatchAuditCorrelationTests(unittest.TestCase):
    def test_other_run_completion_and_target_start_do_not_match(self):
        log=("IMPORT_AUDIT event=finished:COMPLETED runId=empty-run initiator=admin worker=batch-worker\n"
             "IMPORT_JOB_SUBMIT runId=valid-run initiator=admin trigger=batch-trigger worker=batch-worker\n"
             "IMPORT_AUDIT event=started runId=valid-run initiator=admin worker=batch-worker\n")
        self.assertIsNone(harness.batch_finished_line(log,"valid-run"))

    def test_same_run_completion_matches_exact_line(self):
        log=("IMPORT_AUDIT event=finished:COMPLETED runId=empty-run initiator=admin worker=batch-worker\n"
             "IMPORT_AUDIT event=finished:COMPLETED runId=valid-run initiator=admin worker=batch-worker\n")
        self.assertIn("runId=valid-run",harness.batch_finished_line(log,"valid-run"))

    def test_same_run_failure_is_observed_as_finished(self):
        log="IMPORT_AUDIT event=finished:FAILED runId=valid-run initiator=admin worker=batch-worker\n"
        line=harness.batch_finished_line(log,"valid-run")
        self.assertIsNotNone(line)
        self.assertIn("event=finished:FAILED",line)

class DeploymentCliOwnershipTests(unittest.TestCase):
    def test_handling_queue_address_setting_has_one_candidate_owner(self):
        root=Path(__file__).resolve().parents[2]
        files=[root/"tests/candidate-runtime/configure-batch-security.cli",
               root/"candidate/cargotracker/deployment/wildfly/notification-disposition.cli"]
        settings=[]
        for path in files:
            for line in path.read_text().splitlines():
                match=__import__("re").match(r"/subsystem=messaging-activemq/server=default/address-setting=([^:]+):add\(",line)
                if match:settings.append((match.group(1),path.name))
        names=[name for name,_ in settings]
        self.assertEqual(len(names),len(set(names)),settings)
        self.assertIn(("jms.queue.HandlingEventRegistrationAttemptQueue","notification-disposition.cli"),settings)
        datasource=(root/"tests/candidate-runtime/postgresql/configure-datasource.cli").read_text()
        descriptor=(root/"tests/candidate-runtime/persistence-lab.xml").read_text()
        self.assertIn("CargoTrackerDS",datasource)
        self.assertIn("CargoTrackerDS",descriptor)
        self.assertIn('name="jakarta.persistence.schema-generation.database.action" value="none"',descriptor)
        observer=(root/"tests/candidate-runtime/observer/LabEffects.java").read_text()
        self.assertIn('DATABASE_SCHEMA="cargo"',observer)
        self.assertNotIn('getTables(null,"PUBLIC"',observer)
        expected_observer_tables={"location","voyage","cargo","leg","handling_event","carrier_movement",
            "handling_attempt_quarantine","handling_quarantine_state","handling_quarantine_replay_audit",
            "handling_request_idempotency","handling_quarantine_pending"}
        self.assertTrue(all('"'+table+'"' in observer for table in expected_observer_tables))
        self.assertNotIn('"flyway_schema_history"',observer)
        self.assertNotIn('"legacy_sequence_state"',observer)
        audit=(root/"tests/candidate-runtime/observer/InvocationAudit.java").read_text()
        self.assertIn("HandlingQuarantineRetentionJob#purgeExpired",audit)
        self.assertIn("HandlingAttemptQuarantineService#purgeExpired",audit)
        self.assertIn("if(!PERIODIC_MAINTENANCE.contains(key))",audit)
        harness_source=(root/"tests/candidate-runtime/run_candidate.py").read_text()
        self.assertIn("/opt/jboss/wildfly/modules/org/postgresql/main/postgresql-42.7.14.jar",harness_source)

class DiagnosticRedactionTests(unittest.TestCase):
    def test_private_file_values_are_redacted_from_failure_output(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"secret.properties"
            path.write_text("password=top-secret\nbare-secret\n")
            redacted=harness.redact_private_diagnostic("password=top-secret bare-secret",[path])
            self.assertNotIn("top-secret",redacted)
            self.assertNotIn("bare-secret",redacted)
            self.assertIn("[REDACTED]",redacted)

class CleanupTests(unittest.TestCase):
    def test_finalizer_removes_owned_host_access_network(self):
        with tempfile.TemporaryDirectory() as temp:
            calls=[]
            def run(args,**kwargs):
                calls.append(args)
                if args[:3]==["docker","network","inspect"]:
                    return subprocess.CompletedProcess(args,0,stdout="[]",stderr="")
                return subprocess.CompletedProcess(args,0,stdout="removed",stderr="")
            report={"checks":[],"status":"PASS","compose_started":True,"host_access_network_created":True}
            with patch.object(harness,"WORK",Path(temp)),patch.object(harness.subprocess,"run",side_effect=run),contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(harness.finalize(None,[],report))
            self.assertTrue(report["postgres_compose_down"])
            self.assertTrue(report["host_access_network_removed"])
            self.assertIn(["docker","network","rm",harness.HOST_ACCESS_NETWORK],calls)

    def test_partial_private_initialization_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp)/"work";original=Path.write_text
            def fail(path,*args,**kwargs):
                if path.name=="application-roles.properties":raise OSError("injected")
                return original(path,*args,**kwargs)
            with patch.object(harness,"WORK",work),patch.object(harness.subprocess,"run",return_value=subprocess.CompletedProcess([],1)),patch.object(Path,"write_text",fail),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError):harness.main()
            self.assertFalse((work/"secrets/application-users.properties").exists())
            self.assertFalse((work/"secrets/application-roles.properties").exists())
            report=json.loads((work/"results.json").read_text())
            self.assertEqual(report["status"],"FAIL")
            self.assertTrue(report["private_files_removed"])
    def test_partial_routing_credential_write_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp)/"work";original=Path.write_text
            def fail(path,*args,**kwargs):
                value=original(path,*args,**kwargs)
                if path.name=="routing-client.properties":raise OSError("injected partial routing secret write")
                return value
            with patch.object(harness,"WORK",work),patch.object(harness.subprocess,"run",return_value=subprocess.CompletedProcess([],1)),patch.object(Path,"write_text",fail),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError):harness.main()
            self.assertFalse(any((work/"secrets").glob("*.properties")))
            report=json.loads((work/"results.json").read_text())
            self.assertEqual(report["status"],"FAIL")
            self.assertTrue(report["private_files_removed"])
    def cleanup_failure(self,operation):
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);users=work/"users";roles=work/"roles"
            users.write_text("private");roles.write_text("private")
            report={"checks":[],"status":"PASS"}
            def command(*args):
                if args[1]==operation:raise OSError("private exception details")
                return "sanitized"
            with patch.object(harness,"WORK",work),patch.object(harness,"command",command),contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(harness.finalize("owned",[users,roles],report))
            self.assertFalse(users.exists());self.assertFalse(roles.exists())
            stored=json.loads((work/"results.json").read_text())
            self.assertEqual(stored["status"],"FAIL")
            self.assertTrue(stored["private_files_removed"])
            self.assertEqual(stored["owned_container_removed"],operation!="rm")
            self.assertNotIn("private exception details",str(stored))
    def test_log_failure_still_removes_container_and_private_files(self):
        self.cleanup_failure("logs")
    def test_container_removal_failure_still_removes_private_files(self):
        self.cleanup_failure("rm")
if __name__=="__main__":unittest.main()
