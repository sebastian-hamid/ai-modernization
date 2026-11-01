import unittest
from contracts import evaluate,exit_code,run_cases,UnsupportedCase
from generate_cases import build
import json
from pathlib import Path

class ContractEngineTests(unittest.TestCase):
    def denial(self,channel="api",write=False):
        return dict(id="fixture",channel=channel,actor="Reader",expected="deny",write=write)
    def test_403_without_observers_is_blocked(self):
        state,_=evaluate(self.denial(write=True),dict(supported=True,status=403,protected_payload_absent=True))
        self.assertEqual(state,"BLOCKED")
    def effects(self):
        sample={"database":{"records":4,"events":8},"queue":{"enqueues":2},"business_audit":{"invocations":2}}
        return dict(settled=True,fixture_id="isolated",before_fixture="isolated",after_fixture="isolated",before=sample,after=json.loads(json.dumps(sample)))
    def test_denied_write_requires_every_channel_unchanged(self):
        effects=self.effects();effects["after"]["queue"]["enqueues"]+=1
        self.assertEqual(evaluate(self.denial(write=True),dict(supported=True,status=403,protected_payload_absent=True,effects=effects))[0],"FAIL")
    def test_complete_denial_evidence_can_pass_oracle(self):
        self.assertEqual(evaluate(self.denial(write=True),dict(supported=True,status=403,protected_payload_absent=True,effects=self.effects(),identity=dict(server_verified=True,principal="reader-fixture",roles=["Reader"])))[0],"PASS")
    def test_allowed_open_endpoint_without_identity_is_blocked(self):
        case=dict(id="allowed",actor="Reader",channel="api",expected="allow",write=False)
        self.assertEqual(evaluate(case,dict(supported=True,status=200,semantic_success=True))[0],"BLOCKED")
    def test_expired_session_needs_real_lifecycle(self):
        case=dict(id="expired",actor="Reader",channel="session",expected="deny",session_state="expired")
        self.assertEqual(evaluate(case,dict(supported=True,status=401,protected_payload_absent=True))[0],"BLOCKED")
    def test_arbitrary_redirect_is_not_login_denial(self):
        case=dict(id="anon",actor="anonymous",channel="page",expected="deny")
        self.assertEqual(evaluate(case,dict(supported=True,status=302,redirect_is_configured_login=False))[0],"FAIL")
    def test_socket_101_is_not_denial(self):
        case=dict(id="ws",actor="anonymous",channel="socket",expected="deny")
        self.assertEqual(evaluate(case,dict(supported=True,status=101,upgraded=True))[0],"FAIL")
    def test_blocked_suite_cannot_exit_success(self):
        self.assertEqual(exit_code([dict(outcome="BLOCKED")]),2)
        self.assertEqual(exit_code([]),2)
    def test_adapter_error_does_not_echo_secret(self):
        class Broken:
            def execute(self,case):raise RuntimeError("private-password-value")
        result=run_cases([self.denial()],Broken())
        self.assertNotIn("private-password",str(result));self.assertEqual(exit_code(result),1)
    def test_allowed_server_error_cannot_pass(self):
        case=dict(id="allowed",actor="anonymous",channel="page",expected="allow",write=False)
        self.assertEqual(evaluate(case,dict(supported=True,status=500,semantic_success=True,protected_payload_absent=True))[0],"FAIL")
    def test_machine_identity_cannot_use_human_admin(self):
        case=dict(id="worker",actor="worker-BG-03",channel="internal",expected="allow",required_machine_scope="queue",write=True)
        self.assertEqual(evaluate(case,dict(supported=True,identity={"server_verified":True,"principal":"admin","roles":["Administrator"]},semantic_success=True,authorized_effect_verified=True))[0],"BLOCKED")
    def test_missing_database_observer_is_blocked(self):
        effects=self.effects();del effects["after"]["database"]
        self.assertEqual(evaluate(self.denial(write=True),dict(supported=True,status=403,protected_payload_absent=True,effects=effects))[0],"BLOCKED")
    def test_revoked_socket_cannot_upgrade_or_receive_frames(self):
        case=dict(id="ws-expired",actor="Reader",channel="session",original_channel="socket",expected="deny",write=False)
        obs=dict(supported=True,status=401,protected_payload_absent=True,authenticated_before_revocation=True,revocation_verified=True,identity=dict(server_verified=True,principal="reader",roles=["Reader"]),upgraded=True,post_revocation_frame_received=True)
        self.assertEqual(evaluate(case,obs)[0],"FAIL")
        obs.update(upgraded=False,existing_socket_closed=True)
        self.assertEqual(evaluate(case,obs)[0],"FAIL")
        obs["post_revocation_frame_received"]=False
        self.assertEqual(evaluate(case,obs)[0],"PASS")
        del obs["existing_socket_closed"]
        self.assertEqual(evaluate(case,obs)[0],"BLOCKED")
    def test_public_page_cannot_leak_data(self):
        case=dict(id="public",actor="anonymous",channel="page",expected="allow",write=False)
        obs=dict(supported=True,status=200,semantic_success=True,protected_payload_absent=False)
        self.assertEqual(evaluate(case,obs)[0],"FAIL")
        del obs["protected_payload_absent"]
        self.assertEqual(evaluate(case,obs)[0],"BLOCKED")
        obs["protected_payload_absent"]=True
        self.assertEqual(evaluate(case,obs)[0],"PASS")
    def test_denied_role_without_verified_identity_is_blocked(self):
        self.assertEqual(evaluate(self.denial(),dict(supported=True,status=403,protected_payload_absent=True))[0],"BLOCKED")
    def test_catalogue_covers_surfaces_and_sessions(self):
        root=Path(__file__).resolve().parents[2]
        inventory=json.loads((root/"specifications/access-policy-inventory.json").read_text())
        cases=build(inventory)
        self.assertEqual(len(cases),len({c["id"] for c in cases}))
        self.assertTrue(all(any(c["surface_id"]==row["id"] for c in cases) for row in inventory["pages"]+inventory["view_callbacks"]+inventory["interfaces"]+inventory["background"]+inventory["service_boundaries"]))
        self.assertTrue(any(c.get("session_state")=="expired" for c in cases))
        self.assertTrue(any(c.get("session_state")=="logged_out" for c in cases))

if __name__=="__main__":unittest.main()
