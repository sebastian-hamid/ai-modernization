import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import run_candidate_contracts as adapter
from contracts import UnsupportedCase,evaluate
class LiveSubsetTests(unittest.TestCase):
    def case(self):return dict(adapter.bound_contracts()["API-02::Reader::active"])
    def prepared(self):
        value=adapter.LiveSubsetCandidate.__new__(adapter.LiveSubsetCandidate)
        value.observations={self.case()["id"]:{"supported":True,"status":403}}
        value.contracts=adapter.bound_contracts()
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
        case=dict(adapter.bound_contracts()["PAGE-01::Reader::active"]);case["path"]="/cargo-tracker/admin/dashboard.xhtml"
        value=self.prepared();value.observations[case["id"]]={"supported":True,"status":404}
        with self.assertRaises(UnsupportedCase):value.execute(case)
    def test_lifecycle_or_actor_mutation_cannot_reuse_an_observation(self):
        for key,value in [("actor","Administrator"),("channel","session"),("session_state","expired")]:
            case=self.case();case[key]=value
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):self.prepared().execute(case)
    def test_machine_scope_mutation_cannot_reuse_an_observation(self):
        case=dict(adapter.bound_contracts()["API-03-SCOPED::routing-service::active"])
        value=self.prepared();value.observations[case["id"]]={"supported":True,"status":200}
        case["required_machine_scope"]="administrator"
        with self.assertRaises(UnsupportedCase):value.execute(case)
    def test_private_metadata_binding_cannot_be_repointed_to_public_file(self):
        case=dict(adapter.bound_contracts()["PRIVATE-03::Reader::active"])
        value=self.prepared();value.observations[case["id"]]={"supported":True,"status":404}
        case["path"]="/cargo-tracker/index.xhtml"
        with self.assertRaises(UnsupportedCase):value.execute(case)
    def test_read_page_classification_or_role_cannot_reuse_observation(self):
        canonical=adapter.bound_contracts()["PAGE-06::Reader::active"]
        value=self.prepared();value.observations[canonical["id"]]={"supported":True,"status":200}
        for key,new in [("classification","internal-template"),("actor","anonymous"),("method","POST")]:
            case=dict(canonical);case[key]=new
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):value.execute(case)
    def test_html_only_dynamic_page_stays_blocked(self):
        case=dict(adapter.bound_contracts()["PAGE-09::Reader::active"])
        value=self.prepared();value.observations[case["id"]]={"supported":False,"status":200,"semantic_success":False}
        self.assertEqual(evaluate(case,value.execute(case))[0],"BLOCKED")
    def test_error_page_classification_cannot_be_changed(self):
        case=dict(adapter.bound_contracts()["PAGE-18::anonymous::active"])
        value=self.prepared();value.observations[case["id"]]={"supported":True,"status":200}
        case["classification"]="read"
        with self.assertRaises(UnsupportedCase):value.execute(case)
    def test_navigation_callback_or_write_mutation_cannot_reuse_observation(self):
        canonical=adapter.bound_contracts()["ACTION-02::Operator::active"]
        value=self.prepared();value.observations[canonical["id"]]={"supported":True,"status":200}
        for field,new in [("callback","other"),("method","POST"),("write",True),("page_id","PAGE-99"),("source","other"),("source_line",999),("path","/other")]:
            case=dict(canonical);case[field]=new
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):value.execute(case)
    def test_unknown_case_remains_blocked(self):
        case=self.case();case["id"]="API-02::Administrator::expired"
        with self.assertRaises(UnsupportedCase):self.prepared().execute(case)
    def test_changed_surface_contract_never_reuses_old_observation(self):
        for key,value in [("path","/other"),("method","GET"),("expected","allow"),("write",False),("surface_id","API-99")]:
            case=self.case();case[key]=value
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):self.prepared().execute(case)
    def test_failed_or_unclean_live_fixture_is_rejected(self):
        for report in [{"status":"PASS","owned_container_removed":True,"private_files_removed":True,"access_observations":{}},{"status":"FAIL"},{"status":"PASS","owned_container_removed":False,"private_files_removed":True},{"status":"PASS","owned_container_removed":True,"private_files_removed":False}]:
            fake=type("Module",(),{"main":staticmethod(lambda:report)})()
            fake_spec=type("Spec",(),{"loader":type("Loader",(),{"exec_module":staticmethod(lambda module:None)})()})()
            with patch.object(adapter.importlib.util,"spec_from_file_location",return_value=fake_spec),patch.object(adapter.importlib.util,"module_from_spec",return_value=fake):
                with self.assertRaises(RuntimeError):adapter.LiveSubsetCandidate()
if __name__=="__main__":unittest.main()
