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
        module=self.load_candidate("kan24-malformed-inputs")
        self.assertEqual(module.WORK,module.ROOT/".work/kan24-malformed-inputs/candidate-runtime")
        self.assertEqual(module.NAME,"ai-modernization-kan24-malformed-inputs")
        self.assertEqual(module.IMAGE,"ai-modernization-kan24-malformed-inputs:candidate")
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

class CleanupTests(unittest.TestCase):
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
