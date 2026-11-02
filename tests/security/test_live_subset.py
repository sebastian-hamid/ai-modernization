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
    def test_booking_action_requires_post_driver_and_concrete_positive_evidence(self):
        case=adapter.bound_contracts()["ACTION-29::Operator::active"]
        value=self.prepared();proof={"supported":True,"status":200,"action_method":"POST","action_path":"/cargo-tracker/admin/book.xhtml","real_form_verified":True,"post_status":303,"tracking_id":"ABCDEFGH","processing_evidence":{"database_changed":True,"book_new_cargo_invocation_delta":1,"queue_unchanged":True,"independent_reader_persistence":True,"independent_reader_deadline":True}}
        value.observations[case["id"]]=proof
        self.assertEqual(value.execute(case),proof)
        for field,new in [("action_method","GET"),("action_path","/other"),("real_form_verified",False),("post_status",500),("tracking_id","short"),("processing_evidence",{})]:
            altered=dict(proof);altered[field]=new;value.observations[case["id"]]=altered
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):value.execute(case)
    def test_revoked_booking_needs_original_owned_form_and_canonical_session(self):
        case=adapter.bound_contracts()["ACTION-29::Operator::expired"];value=self.prepared()
        value.observations[case["id"]]={"supported":True,"action_method":"POST","action_path":"/cargo-tracker/admin/book.xhtml","real_form_verified":True}
        with self.assertRaises(UnsupportedCase):value.execute(case)
        value.observations[case["id"]]["form_owned_before_revocation"]=True
        self.assertEqual(value.execute(case)["form_owned_before_revocation"],True)
        changed=dict(case);changed["method"]="GET"
        with self.assertRaises(UnsupportedCase):value.execute(changed)
    def test_only_mutation_transport_metadata_changes_in_502_case_inventory(self):
        import copy,json
        from generate_cases import build,ROOT
        inventory=json.loads((ROOT/"specifications/access-policy-inventory.json").read_text());old=copy.deepcopy(inventory)
        writes={"ACTION-09","ACTION-17","ACTION-19","ACTION-29","ACTION-41"}
        for row in old["view_callbacks"]:
            if row["id"] in writes:row.pop("method",None)
        current=build(inventory);previous=build(old)
        self.assertEqual(len(current),502);self.assertEqual([c["id"] for c in current],[c["id"] for c in previous])
        changed=0
        for now,before in zip(current,previous):
            if now!=before:
                self.assertEqual(now["method"],"POST");self.assertEqual(before["method"],"GET")
                self.assertIn(now["surface_id"],writes)
                self.assertEqual({k:v for k,v in now.items() if k!="method"},{k:v for k,v in before.items() if k!="method"});changed+=1
        self.assertEqual(changed,40)
    def test_inventory_regeneration_preserves_reviewed_post_descriptors(self):
        import contextlib,io,json,tempfile
        path=adapter.ROOT/"scripts/build-access-inventory.py"
        spec=importlib.util.spec_from_file_location("inventory_generator",path)
        generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/"inventory.json"
            with patch.object(generator,"OUT",output),contextlib.redirect_stdout(io.StringIO()):generator.main()
            self.assertEqual(json.loads(output.read_text()),json.loads((adapter.ROOT/"specifications/access-policy-inventory.json").read_text()))
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
