import contextlib,importlib.util,io,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("browser_harness",Path(__file__).with_name("run_browser.py"))
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
class HandlingCsrfProofTests(unittest.TestCase):
    def fixture(self):
        proofs={}
        for role,user in (("Operator","operator"),("Administrator","admin")):
            before={"fixture_id":"owned-fixture","stage":"handling-wrong-csrf:"+role+":before",
                    "tables":{"CARGO":{"rows":13,"sha256":"a"*64}},
                    "queues":{"jms.queue.CargoHandledQueue":{"MessagesAdded":5}},
                    "business_invocations":{"submitReport":2}}
            after={"fixture_id":"owned-fixture","stage":"handling-wrong-csrf:"+role+":after",
                   "tables":{"CARGO":{"rows":13,"sha256":"a"*64}},
                   "queues":{"jms.queue.CargoHandledQueue":{"MessagesAdded":5}},
                   "business_invocations":{"submitReport":2}}
            proofs[role]={"source_path":"/cargo-tracker/mobile.xhtml","actor":role,
                          "valid_submission_form":True,"current_csrf_present":True,"current_csrf_nonempty":True,
                          "submit_marker_present":True,"wrong_token_distinct":True,"response_status":403,
                          "protected_payload_absent":True,"independent_effects_unchanged":True,
                          "identity":{"server_verified":True,"principal":user,"roles":[role]},
                          "before":before,"after":after}
        return proofs
    def test_valid_wrong_csrf_proofs_for_both_permitted_roles(self):
        harness.validate_handling_csrf_proofs(self.fixture())
    def test_missing_role_or_incomplete_form_fails_closed(self):
        for change in ("missing_role","invalid_form","missing_csrf","empty_csrf","same_token","wrong_status","wrong_principal","wrong_role"):
            proofs=self.fixture()
            if change=="missing_role":proofs.pop("Administrator")
            elif change=="invalid_form":proofs["Operator"]["valid_submission_form"]=False
            elif change=="missing_csrf":proofs["Administrator"]["current_csrf_present"]=False
            elif change=="empty_csrf":proofs["Operator"]["current_csrf_nonempty"]=False
            elif change=="same_token":proofs["Operator"]["wrong_token_distinct"]=False
            elif change=="wrong_principal":proofs["Operator"]["identity"]["principal"]="admin"
            elif change=="wrong_role":proofs["Administrator"]["identity"]["roles"]=["Reader"]
            else:proofs["Administrator"]["response_status"]=200
            with self.subTest(change=change),self.assertRaises(AssertionError):
                harness.validate_handling_csrf_proofs(proofs)
    def test_effects_or_identity_changes_fail_closed(self):
        for change in ("database","queue","invocation","principal"):
            proofs=self.fixture()
            if change=="database":proofs["Operator"]["after"]["tables"]["CARGO"]["sha256"]="b"*64
            elif change=="queue":proofs["Administrator"]["after"]["queues"]["jms.queue.CargoHandledQueue"]["MessagesAdded"]=6
            elif change=="invocation":proofs["Operator"]["after"]["business_invocations"]["submitReport"]=3
            else:proofs["Administrator"]["identity"]["server_verified"]=False
            with self.subTest(change=change),self.assertRaises(AssertionError):
                harness.validate_handling_csrf_proofs(proofs)


class BrowserCleanupTests(unittest.TestCase):
    def test_replacement_output_requires_exact_canonical_actor_keys(self):
        keys=harness.expected_replacement_keys()
        self.assertEqual(len(keys),44)
        harness.validate_replacement_keys({key:{} for key in keys})
        with self.assertRaises(AssertionError):
            harness.validate_replacement_keys({key:{} for key in keys if key!="REPLACEMENT::handling-completion::Operator"})
        extra={key:{} for key in keys}
        extra["HANDLING_COMPLETION_INPUT::Operator"]={}
        with self.assertRaises(AssertionError):
            harness.validate_replacement_keys(extra)
    def exercise(self,mode):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary);report={"page_fixture_tracking_id":"FIXTURE123"};calls=[]
            def run(args,**kwargs):
                calls.append(args)
                if args[:2]==["docker","inspect"]:return subprocess.CompletedProcess(args,1)
                if args[:2]==["docker","exec"]:
                    if "input" not in kwargs:
                        self.assertEqual(args[3:],["rm","-f","/out/results.json"])
                    else:
                        self.assertEqual(json.loads(kwargs["input"])["fixture_tracking_id"],"FIXTURE123")
                        self.assertNotIn("secret-test-value",str(args))
                    return subprocess.CompletedProcess(args,0,"")
                if args[:3]==["docker","rm","-f"] and mode=="remove-fails":
                    return subprocess.CompletedProcess(args,1)
                return subprocess.CompletedProcess(args,0,"")
            def run_browser(args,capture,timeout,inspect_event=None):
                calls.append(args)
                if mode=="timeout":
                    error=subprocess.TimeoutExpired("docker exec",420)
                    error.elapsed_seconds=421
                    error.last_completed_effect_stage="handling-single-page:Reader:after"
                    error.pending_effect_stage="handling-single-page:Operator:before"
                    error.completed_effect_stages=["handling-single-page:Reader:before","handling-single-page:Reader:after"]
                    raise error
                return subprocess.CompletedProcess(args,1,"")
            def output(args,**kwargs):
                calls.append(args)
                if args[:3]==["docker","network","create"]:return "owned-network"
                if args[:2]==["docker","create"]:return "owned-browser"
                if args[:2]==["docker","exec"]:return json.dumps({"checks":[{"passed":False}]})
                raise AssertionError("Unexpected command")
            def app(after_checks):
                after_checks("owned-app","unused",{"operator":"secret-test-value"},report)
            with patch.object(harness,"WORK",work),patch.object(harness.subprocess,"run",run),patch.object(harness.subprocess,"check_output",output),patch.object(harness.app,"main",app),patch.object(harness.bridge,"run_browser_with_effects",run_browser),contextlib.redirect_stdout(io.StringIO()):
                expected=subprocess.TimeoutExpired if mode=="timeout" else RuntimeError if mode=="remove-fails" else AssertionError
                with self.assertRaises(expected):harness.main()
            if mode=="timeout":
                diagnostic=json.loads((work/"browser-timeout.json").read_text())
                self.assertEqual(diagnostic["timeout_seconds"],600)
                self.assertEqual(diagnostic["elapsed_seconds"],421)
                self.assertEqual(diagnostic["last_completed_effect_stage"],"handling-single-page:Reader:after")
                self.assertEqual(diagnostic["pending_effect_stage"],"handling-single-page:Operator:before")
                self.assertEqual(diagnostic["completed_effect_stage_count"],2)
            self.assertIn(["docker","rm","-f","owned-browser"],calls)
            self.assertIn(["docker","network","disconnect","-f","owned-network","owned-app"],calls)
            self.assertIn(["docker","network","rm","owned-network"],calls)
            self.assertEqual(report["browser_cleanup"]["container_removed"],mode!="remove-fails")
            self.assertTrue(report["browser_cleanup"]["network_removed"])
    def test_browser_assertion_failure_cleans_owned_resources(self):self.exercise("failure")
    def test_browser_timeout_cleans_owned_resources(self):self.exercise("timeout")
    def test_removal_failure_is_not_a_cleanup_pass(self):self.exercise("remove-fails")
if __name__=="__main__":unittest.main()
