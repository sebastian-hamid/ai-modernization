import contextlib,importlib.util,io,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("kan18",Path(__file__).with_name("run_candidate.py"))
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
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
