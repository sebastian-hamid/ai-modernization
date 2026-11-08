import contextlib,importlib.util,io,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("browser_harness",Path(__file__).with_name("run_browser.py"))
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
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
