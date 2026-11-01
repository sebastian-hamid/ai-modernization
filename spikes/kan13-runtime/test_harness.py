import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location("kan13_harness",Path(__file__).with_name("run_spike.py"))
harness=importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

class HarnessFailureTests(unittest.TestCase):
    def test_partial_realm_initialization_is_cleaned_and_reported(self):
        # Reproduce the real boundary: first realm file exists, second write fails.
        # Docker must never be invoked beyond the mocked existence check.
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);work=root/"work";evidence=root/"evidence"
            original=Path.write_text
            def fail_second_file(path,*args,**kwargs):
                if path.name=="application-roles.properties":
                    raise OSError("simulated realm-file write failure")
                return original(path,*args,**kwargs)
            with patch.object(harness,"WORK",work), patch.object(harness,"EVIDENCE",evidence), \
                 patch.object(harness.subprocess,"run",return_value=subprocess.CompletedProcess([],1)), \
                 patch.object(harness,"command",side_effect=AssertionError("Unexpected Docker command")), \
                 patch.object(Path,"write_text",fail_second_file), patch("sys.argv",["run_spike.py"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                result=harness.main()
            self.assertEqual(result,1)
            self.assertFalse((work/"secrets/application-users.properties").exists())
            self.assertFalse((work/"secrets/application-roles.properties").exists())
            report=json.loads((evidence/"results.json").read_text())
            self.assertIn("simulated realm-file write failure",report["failure"])
            self.assertEqual(report["outcome"],"FAIL")
            self.assertEqual(report["cleanup"]["status"],"PASS")
            suite=ET.parse(evidence/"TEST-kan13-runtime.xml").getroot()
            self.assertEqual(suite.get("tests"),"1")
            self.assertEqual(suite.get("failures"),"1")
            self.assertIsNotNone(suite.find("testcase/failure"))

if __name__=="__main__":unittest.main()
