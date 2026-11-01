import importlib.util
import io
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("handling_reports",ROOT/"tests/runtime/handling_workflow.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RuntimeReportTests(unittest.TestCase):
    def run_case(self,case):
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(case)
        return unittest.TextTestRunner(stream=io.StringIO(),resultclass=module.XmlResult).run(suite)

    def test_failed_journey_substeps_make_one_failed_junit_case(self):
        class Journey(unittest.TestCase):
            def test_journey(self):
                for step in range(2):
                    with self.subTest(step=step):
                        self.fail("observable step failure")
        result=self.run_case(Journey)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.testsRun,1)
        self.assertEqual(len(result.cases),1)
        self.assertIsNotNone(result.cases[0].find("failure"))

    def test_fixture_error_is_reported_without_a_passing_case(self):
        class BrokenFixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("runtime unavailable")
            def test_workflow(self):
                pass
        result=self.run_case(BrokenFixture)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.cases),1)
        self.assertIsNotNone(result.cases[0].find("error"))
        self.assertGreaterEqual(float(result.cases[0].get("time")),0)
