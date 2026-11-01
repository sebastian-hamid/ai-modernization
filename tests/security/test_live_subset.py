import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import run_candidate_contracts as adapter
from contracts import UnsupportedCase,evaluate
class LiveSubsetTests(unittest.TestCase):
    def case(self):return {"id":"API-02::Reader::active","surface_id":"API-02","path":"/cargo-tracker/rest/handling/reports","method":"POST","expected":"deny","write":True}
    def prepared(self):
        value=adapter.LiveSubsetCandidate.__new__(adapter.LiveSubsetCandidate)
        value.observations={self.case()["id"]:{"supported":True,"status":403}}
        return value
    def test_internal_template_404_is_denial_but_never_success_or_login(self):
        case={"channel":"page","classification":"internal-template","actor":"anonymous","expected":"deny","write":False}
        for status in [403,404]:
            self.assertEqual(evaluate(case,{"supported":True,"status":status,"protected_payload_absent":True})[0],"PASS")
        for status in [200,303]:
            self.assertEqual(evaluate(case,{"supported":True,"status":status,"protected_payload_absent":True,"redirect_is_configured_login":True})[0],"FAIL")
    def test_operational_page_404_does_not_become_authorization_pass(self):
        case={"channel":"page","classification":"read","actor":"anonymous","expected":"deny","write":False}
        self.assertEqual(evaluate(case,{"supported":True,"status":404,"protected_payload_absent":True})[0],"FAIL")
    def test_private_binding_never_accepts_operational_page(self):
        case={"id":"PAGE-01::Reader::active","surface_id":"PAGE-01","path":"/cargo-tracker/admin/dashboard.xhtml","method":"GET","classification":"internal-template","expected":"deny","write":False}
        value=self.prepared();value.observations[case["id"]]={"supported":True,"status":404}
        with self.assertRaises(UnsupportedCase):value.execute(case)
    def test_unknown_case_remains_blocked(self):
        case=self.case();case["id"]="API-02::Administrator::expired"
        with self.assertRaises(UnsupportedCase):self.prepared().execute(case)
    def test_changed_surface_contract_never_reuses_old_observation(self):
        for key,value in [("path","/other"),("method","GET"),("expected","allow"),("write",False),("surface_id","API-99")]:
            case=self.case();case[key]=value
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):self.prepared().execute(case)
    def test_failed_or_unclean_live_fixture_is_rejected(self):
        for report in [{"status":"FAIL"},{"status":"PASS","owned_container_removed":False,"private_files_removed":True},{"status":"PASS","owned_container_removed":True,"private_files_removed":False}]:
            fake=type("Module",(),{"main":staticmethod(lambda:report)})()
            fake_spec=type("Spec",(),{"loader":type("Loader",(),{"exec_module":staticmethod(lambda module:None)})()})()
            with patch.object(adapter.importlib.util,"spec_from_file_location",return_value=fake_spec),patch.object(adapter.importlib.util,"module_from_spec",return_value=fake):
                with self.assertRaises(RuntimeError):adapter.LiveSubsetCandidate()
if __name__=="__main__":unittest.main()
