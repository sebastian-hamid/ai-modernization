import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("socket_browser",Path(__file__).with_name("run_browser.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class SocketProofTests(unittest.TestCase):
    def fixture(self):
        proofs={"WS-01::anonymous::active":{"supported":True,"status":401,"upgraded":False,"protected_payload_absent":True}}
        for role,user in [("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
            identity={"server_verified":True,"principal":user,"roles":[role]}
            proofs["WS-01::"+role+"::active"]={"supported":True,"status":101,"identity":identity,"socket_open_observed":True,"semantic_success":True,"authorized_frame_received":True}
            proofs["WS-ORIGIN::"+role+"::active"]={"supported":True,"status":403,"upgraded":False,"protected_payload_absent":True,"identity":identity}
            for state in ["logged_out","expired"]:
                proofs["WS-01::"+role+"::"+state]={"supported":True,"status":401,"upgraded":False,"protected_payload_absent":True,"identity":identity,"authenticated_before_revocation":True,"revocation_verified":True,"existing_socket_closed":True,"post_revocation_frame_received":False,"stale_cookie_replay_verified":True}
        return {"access_observations":{}},{"socket_observations":proofs}
    def test_complete_native_socket_proofs_promote_exactly13(self):
        report,result=self.fixture();h.promote_socket_cases(report,result);self.assertEqual(len(report["access_observations"]),13)
    def test_missing_or_extra_observation_fails_without_partial_mutation(self):
        for mode in ["missing","extra"]:
            report,result=self.fixture()
            if mode=="missing":result["socket_observations"].pop("WS-01::Reader::active")
            else:result["socket_observations"]["unexpected"]={}
            with self.assertRaises(AssertionError):h.promote_socket_cases(report,result)
            self.assertEqual(report["access_observations"],{})
    def test_handshake_without_data_or_native_identity_fails(self):
        for key,value in [("authorized_frame_received",False),("socket_open_observed",False),("status",200),("identity",{"server_verified":True,"principal":"admin","roles":["Reader"]})]:
            report,result=self.fixture();result["socket_observations"]["WS-01::Reader::active"][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):h.promote_socket_cases(report,result)
            self.assertEqual(report["access_observations"],{})
    def test_revocation_without_old_cookie_close_and_no_frame_evidence_fails(self):
        for key,value in [("stale_cookie_replay_verified",False),("existing_socket_closed",False),("post_revocation_frame_received",True),("authenticated_before_revocation",False),("protected_payload_absent",False)]:
            report,result=self.fixture();result["socket_observations"]["WS-01::Reader::expired"][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):h.promote_socket_cases(report,result)
            self.assertEqual(report["access_observations"],{})
if __name__=="__main__":unittest.main()
