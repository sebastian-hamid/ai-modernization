import copy,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("navigation_browser",Path(__file__).with_name("run_browser.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class NavigationProofTests(unittest.TestCase):
    def fixture(self):
        proofs={}
        rows=json.loads(Path(__file__).with_name("navigation-actions.json").read_text())
        for row in rows:
            for role,user in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
                allowed=row["anonymous"] if role=="anonymous" else role in row["allowed_roles"]
                direct=not allowed and row["id"] in {"ACTION-02","ACTION-05","ACTION-14"}
                proof={"supported":True,"action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/"+row["target"].split("?")[0],"query_keys":["trackingId","jfwid"] if row["kind"]=="routed-detail" else ["jfwid"],"tracking_id":"ABC123" if row["kind"]=="routed-detail" else None,"routing_status":"ROUTED","transport_status":"IN_PORT","target":row["target"],"source_page":"index.xhtml" if role=="anonymous" and not row["anonymous"] else row["source_page"],"driver":"direct" if direct else "click","control_hidden":direct,"status":200 if allowed else 303 if role=="anonymous" else 403,"semantic_success":allowed,"protected_payload_absent":True,"redirect_is_configured_login":not allowed and role=="anonymous","cargo_observed":"ABC123","socket_live":True,"form_observed":True}
                if user:proof["identity"]={"server_verified":True,"principal":user,"roles":[role]}
                proofs[row["id"]+"::"+role+"::active"]=proof
        return {"access_observations":{"existing":{"supported":True}}},{"navigation_actions":proofs}
    def test_complete_native_actions_promote_all_twenty_eight(self):
        report,result=self.fixture();h.promote_navigation_actions(report,result)
        self.assertEqual(len(report["access_observations"]),29)
    def test_missing_extra_or_wrong_driver_never_partially_promotes(self):
        for mode in ["missing","extra","driver","target","source","hidden"]:
            report,result=self.fixture();before=copy.deepcopy(report)
            key="ACTION-02::Reader::active"
            if mode=="missing":result["navigation_actions"].pop(key)
            elif mode=="extra":result["navigation_actions"]["UNKNOWN"]={}
            else:result["navigation_actions"][key][{"driver":"driver","target":"target","source":"source_page","hidden":"control_hidden"}[mode]]={"driver":"click","target":"other.xhtml","source":"index.xhtml","hidden":False}[mode]
            with self.subTest(mode=mode),self.assertRaises(AssertionError):h.promote_navigation_actions(report,result)
            self.assertEqual(report,before)
    def test_role_or_destination_semantics_must_be_real(self):
        for key,field,value in [("ACTION-01::Reader::active","cargo_observed","UNKNOWN"),("ACTION-04::Reader::active","socket_live",False),("ACTION-02::Operator::active","form_observed",False),("ACTION-03::Reader::active","semantic_success",False),("ACTION-06::anonymous::active","protected_payload_absent",False)]:
            report,result=self.fixture();before=copy.deepcopy(report)
            result["navigation_actions"][key][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):h.promote_navigation_actions(report,result)
            self.assertEqual(report,before)
        report,result=self.fixture();result["navigation_actions"]["ACTION-02::Reader::active"]["identity"]["principal"]="operator"
        with self.assertRaises(AssertionError):h.promote_navigation_actions(report,result)
        self.assertEqual(len(report["access_observations"]),1)
    def test_only_local_target_and_single_faces_window_parameter_pass(self):
        for field,value in [("target_origin_verified",False),("actual_target_path","/other"),("query_keys",["redirect"]),("query_keys",["jfwid","jfwid"]),("query_keys",None)]:
            report,result=self.fixture();result["navigation_actions"]["ACTION-01::Reader::active"][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(AssertionError):h.promote_navigation_actions(report,result)
            self.assertEqual(len(report["access_observations"]),1)
    def test_routed_detail_requires_exact_cargo_status_and_query(self):
        for field,value in [("tracking_id","DEF789"),("query_keys",["trackingId","trackingId"]),("query_keys",["trackingId","redirect"]),("routing_status","NOT_ROUTED"),("transport_status","CLAIMED"),("cargo_observed","DEF789")]:
            report,result=self.fixture();result["navigation_actions"]["ACTION-14::Reader::active"][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(AssertionError):h.promote_navigation_actions(report,result)
            self.assertEqual(len(report["access_observations"]),1)
    def test_arbitrary_redirect_success_or_leak_is_not_denial(self):
        for key,field,value in [("ACTION-01::anonymous::active","redirect_is_configured_login",False),("ACTION-02::Reader::active","status",200),("ACTION-05::anonymous::active","protected_payload_absent",False)]:
            report,result=self.fixture();result["navigation_actions"][key][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):h.promote_navigation_actions(report,result)
            self.assertEqual(len(report["access_observations"]),1)

class ClaimedNavigationProofTests(unittest.TestCase):
    def test_claimed_receipts_promote_only_to_current_observations(self):
        roles={"Reader":"reader","Operator":"operator","Administrator":"admin"}
        common={"supported":True,"action_executed":True,"target_origin_verified":True,
                "actual_target_path":"/cargo-tracker/admin/show.xhtml","query_keys":["trackingId"],
                "tracking_id":"ABCDEFGH","current_navigation_driver":"browser-claimed-cargo-v1"}
        proofs={"CURRENT::ACTION-10::"+role+"::active":{
            **common,"status":200,"source_page":"admin/listClaimed.xhtml","driver":"click",
            "identity":{"server_verified":True,"principal":user,"roles":[role]},
            "semantic_success":True,"selected_cargo_verified":True,"persisted_details_verified":True,
        } for role,user in roles.items()}
        proofs["CURRENT::ACTION-10::anonymous::active"]={
            **common,"status":303,"source_page":"index.xhtml","driver":"direct",
            "protected_payload_absent":True,"redirect_is_configured_login":True,"claimed_list_denied":True,
        }
        report={"current_access_observations":{},"access_observations":{}}
        h.promote_claimed_cargo_actions(report,{"claimed_cargo_actions":proofs})
        self.assertEqual(report["current_access_observations"],proofs)
        self.assertEqual(report["access_observations"],{})
        proofs["CURRENT::ACTION-10::Reader::active"]["tracking_id"]="OTHERID1"
        with self.assertRaises(AssertionError):
            h.promote_claimed_cargo_actions(report,{"claimed_cargo_actions":proofs})

if __name__=="__main__":unittest.main()
