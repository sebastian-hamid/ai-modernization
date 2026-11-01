import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("page_browser",Path(__file__).with_name("run_browser.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class PageProofTests(unittest.TestCase):
    def fixture(self):
        observations={};proofs={}
        for surface,path in [("PAGE-09","/admin/map.xhtml"),("PAGE-10","/admin/mapFrame.html")]:
            for role,user in [("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
                key=surface+"::"+role+"::active"
                observations[key]={"supported":False,"shell_rendered":True,"browser_required":True,"identity":{"server_verified":True,"principal":user,"roles":[role]}}
                proofs[key]={"principal":user,"roles":[role],"source_path":path,"final_path":"/cargo-tracker/admin/live.xhtml","status":200,"cargo_observed":"ABC123","socket_live":True}
        return {"access_observations":observations},{"page_semantics":proofs}
    def test_only_complete_native_data_socket_proofs_promote(self):
        report,result=self.fixture();h.promote_live_pages(report,result)
        self.assertTrue(all(o["supported"] and o["semantic_success"] for o in report["access_observations"].values()))
    def test_missing_or_extra_case_never_promotes_partial_results(self):
        for mode in ["missing","extra"]:
            report,result=self.fixture()
            if mode=="missing":result["page_semantics"].pop("PAGE-09::Reader::active")
            else:result["page_semantics"]["unrecognized"]={}
            with self.assertRaises(AssertionError):h.promote_live_pages(report,result)
            self.assertFalse(any(o["supported"] for o in report["access_observations"].values()))
    def test_wrong_role_redirect_cargo_or_socket_fails_atomically(self):
        for key,value in [("principal","admin"),("roles",[]),("source_path","/admin/dashboard.xhtml"),("final_path","https://untrusted.example/"),("status",303),("cargo_observed","UNKNOWN"),("socket_live",False)]:
            report,result=self.fixture();result["page_semantics"]["PAGE-09::Reader::active"][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):h.promote_live_pages(report,result)
            self.assertFalse(any(o["supported"] for o in report["access_observations"].values()))
    def test_unverified_server_identity_or_missing_shell_cannot_pass(self):
        for mode in ["identity","shell"]:
            report,result=self.fixture()
            if mode=="identity":report["access_observations"]["PAGE-09::Reader::active"]["identity"]["server_verified"]=False
            else:report["access_observations"]["PAGE-09::Reader::active"]["shell_rendered"]=False
            with self.assertRaises(AssertionError):h.promote_live_pages(report,result)
if __name__=="__main__":unittest.main()
