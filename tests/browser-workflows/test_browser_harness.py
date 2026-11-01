import contextlib,importlib.util,io,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("browser_harness",Path(__file__).with_name("run_browser.py"))
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
class BrowserCleanupTests(unittest.TestCase):
    def exercise(self,mode):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary);report={};calls=[]
            def run(args,**kwargs):
                calls.append(args)
                if args[:2]==["docker","inspect"]:return subprocess.CompletedProcess(args,1)
                if args[:2]==["docker","exec"]:
                    self.assertIn("input",kwargs)
                    self.assertNotIn("secret-test-value",str(args))
                    if mode=="timeout":raise subprocess.TimeoutExpired("docker exec",240)
                    return subprocess.CompletedProcess(args,1,"")
                if args[:3]==["docker","rm","-f"] and mode=="remove-fails":
                    return subprocess.CompletedProcess(args,1)
                return subprocess.CompletedProcess(args,0,"")
            def output(args,**kwargs):
                calls.append(args)
                if args[:3]==["docker","network","create"]:return "owned-network"
                if args[:2]==["docker","create"]:return "owned-browser"
                if args[:2]==["docker","exec"]:return json.dumps({"checks":[{"passed":False}]})
                raise AssertionError("Unexpected command")
            def app(after_checks):
                after_checks("owned-app","unused",{"operator":"secret-test-value"},report)
            with patch.object(harness,"WORK",work),patch.object(harness.subprocess,"run",run),patch.object(harness.subprocess,"check_output",output),patch.object(harness.app,"main",app),contextlib.redirect_stdout(io.StringIO()):
                expected=subprocess.TimeoutExpired if mode=="timeout" else RuntimeError if mode=="remove-fails" else AssertionError
                with self.assertRaises(expected):harness.main()
            self.assertIn(["docker","rm","-f","owned-browser"],calls)
            self.assertIn(["docker","network","disconnect","-f","owned-network","owned-app"],calls)
            self.assertIn(["docker","network","rm","owned-network"],calls)
            self.assertEqual(report["browser_cleanup"]["container_removed"],mode!="remove-fails")
            self.assertTrue(report["browser_cleanup"]["network_removed"])
    def test_browser_assertion_failure_cleans_owned_resources(self):self.exercise("failure")
    def test_browser_timeout_cleans_owned_resources(self):self.exercise("timeout")
    def test_removal_failure_is_not_a_cleanup_pass(self):self.exercise("remove-fails")
if __name__=="__main__":unittest.main()
