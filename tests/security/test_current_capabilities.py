import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import current_capabilities as c
from contracts import UnsupportedCase
class FakeLegacy:
    """Privileged counterfactual unit double; never runtime evidence."""
    def __init__(self,observation):self.observation=observation
    def execute(self,case):return self.observation
class CurrentCapabilityTests(unittest.TestCase):
    def fixture(self,ident="CURRENT::API-01::Reader::active"):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        observation={"supported":True,"status":200,"semantic_success":True,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]}}
        adapter.legacy=FakeLegacy(observation)
        return adapter,copy.deepcopy(adapter.contracts[ident]),observation
    def test_partition_preserves_every_historical_case_and_pending_replacements(self):
        model,inventory=c.load_model();cases=c.build_current(model,inventory)
        self.assertEqual(len(cases),470)
        current=[x for x in cases if x["kind"]=="current"];self.assertEqual(len(current),426)
        self.assertEqual(len([x for x in cases if x["kind"]=="replacement"]),44)
        retire=c.retirement_results(model,c.CurrentAdapter(),[])
        self.assertEqual(len(retire),76)
        old={x["id"] for x in c.build(inventory)}
        self.assertEqual({x["legacy_case_id"] for x in current}|{x["legacy_case_id"] for x in retire},old)
        self.assertEqual(len(old),502)
        self.assertTrue(all(x["outcome"]=="BLOCKED" for x in retire))
    def test_model_rejects_drift_missing_duplicate_unknown_and_weakened_policy(self):
        model,inventory=c.load_model();fingerprint=model["legacy_inventory_sha256"]
        for mode in ["version","drift","missing","duplicate","unknown","field","target","role","retire","driver","evidence"]:
            bad=copy.deepcopy(model)
            if mode=="version":bad["schema_version"]=1
            elif mode=="drift":bad["legacy_inventory_sha256"]="0"*64
            elif mode=="missing":bad["mapped_actions"].pop()
            elif mode=="duplicate":bad["mapped_actions"].append(copy.deepcopy(bad["mapped_actions"][0]))
            elif mode=="unknown":bad["mapped_actions"][0]["legacy_id"]="ACTION-99"
            elif mode=="field":bad["auto_retire"]=True
            elif mode=="target":bad["mapped_actions"][0]["modern_target"]="https://untrusted.example/cargo-tracker/admin/dashboard.xhtml"
            elif mode=="role":bad["replacement_capabilities"][0]["allowed_roles"]=["Reader"]
            elif mode=="retire":bad["retirement_candidates"][0]["status"]="retired"
            elif mode=="driver":bad["retirement_candidates"][0]["negative_driver"]="generic-success"
            else:bad["retirement_candidates"][0]["required_evidence"].pop()
            with self.subTest(mode=mode),self.assertRaises(ValueError):c.validate_model(bad,inventory,fingerprint)
    def test_exact_role_principal_canonical_contract_and_returned_copy(self):
        adapter,case,proof=self.fixture()
        returned=adapter.execute(case);returned["identity"]["roles"].append("Administrator")
        self.assertEqual(proof["identity"]["roles"],["Reader"])
        for field,value in [("actor","Administrator"),("method","POST"),("path","/other"),("expected","deny")]:
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute({**case,field:value})
        altered=copy.deepcopy(case);altered["legacy_contract"]["source"]="other"
        with self.assertRaises(UnsupportedCase):adapter.execute(altered)
        for identity in [{"server_verified":True,"principal":"admin","roles":["Reader"]},{"server_verified":True,"principal":"reader","roles":["Reader","Administrator"]},{"server_verified":False,"principal":"reader","roles":["Reader"]}]:
            adapter.legacy.observation={**proof,"identity":identity}
            with self.subTest(identity=identity),self.assertRaises(UnsupportedCase):adapter.execute(case)
    def test_action_session_uses_actual_post_target_and_bound_fresh_receipt(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-09::Operator::expired")
        proof={"supported":True,"identity":{"server_verified":True,"principal":"operator","roles":["Operator"]},"action_method":"POST","action_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH","tracking_id":"ABCDEFGH","entry_page":"admin/show.xhtml?trackingId=ABCDEFGH","source_entry_verified":True}
        adapter.legacy.observation=proof;self.assertEqual(adapter.execute(case)["action_method"],"POST")
        for key,value in [("action_method","GET"),("action_path","/other"),("tracking_id","short")]:
            adapter.legacy.observation={**proof,key:value}
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.observation=proof
        for key,value in [("kind","archived-report"),("legacy_fixture_cleanup_verified",False),("inputs_fingerprint","b"*64)]:
            original=copy.deepcopy(adapter.provenance);adapter.provenance[key]=value
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)
            adapter.provenance=original
    def test_generic_success_cannot_satisfy_pending_replacement_or_retirement(self):
        adapter,_,_=self.fixture()
        for case in adapter.contracts.values():
            if case["kind"]=="replacement" or case.get("binding_status")=="pending":
                with self.subTest(case=case["id"]),self.assertRaises(UnsupportedCase):adapter.execute(copy.deepcopy(case))
        fabricated=[{"case":x,"outcome":"PASS"} for x in adapter.contracts]
        result=c.retirement_results(adapter.model,adapter,fabricated)
        self.assertEqual(len(result),76);self.assertTrue(all(x["outcome"]=="BLOCKED" for x in result))
    def test_get_proof_binds_complete_query_and_source(self):
        proof={"supported":True,"status":200,"semantic_success":True,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},"driver":"click","actual_target_path":"/cargo-tracker/admin/show.xhtml","query_keys":["trackingId","jfwid"],"tracking_id":"ABC123","source_page":"admin/listRouted.xhtml","action_executed":True,"target_origin_verified":True}
        for mode in ["declared-cargo","duplicate-query","wrong-source","unknown-query"]:
            model,inventory=c.load_model()
            if mode=="declared-cargo":
                next(row for row in model["mapped_actions"] if row["legacy_id"]=="ACTION-14")["modern_target"]="/cargo-tracker/admin/show.xhtml?trackingId=DEF789"
            with patch.object(c,"load_model",return_value=(model,inventory)):
                adapter,case,_=self.fixture("CURRENT::ACTION-14::Reader::active")
            observation=copy.deepcopy(proof)
            if mode=="duplicate-query":observation["query_keys"]=["trackingId","trackingId"]
            elif mode=="wrong-source":observation["source_page"]="admin/dashboard.xhtml"
            elif mode=="unknown-query":observation["query_keys"]=["trackingId","redirect"]
            adapter.legacy.observation=observation
            with self.subTest(mode=mode),self.assertRaises(UnsupportedCase):adapter.execute(case)
    def test_approved_v2_partition_group_and_policy_cannot_change(self):
        model,inventory=c.load_model();fingerprint=model["legacy_inventory_sha256"]
        for mode in ["promote-pending","swap-retirement","change-requirement","change-policy","swap-groups"]:
            bad=copy.deepcopy(model)
            if mode=="promote-pending":bad["mapped_actions"].append(bad["pending_current_actions"].pop(0))
            elif mode=="swap-retirement":
                next(row for row in bad["pending_current_actions"] if row["legacy_id"]=="ACTION-10")["legacy_id"]="ACTION-08"
                next(row for row in bad["retirement_candidates"] if row["legacy_id"]=="ACTION-08")["legacy_id"]="ACTION-10"
                next(row for row in bad["replacement_capabilities"] if row["id"]=="cancel-editor")["legacy_ids"]=["ACTION-10"]
            elif mode=="change-requirement":bad["replacement_capabilities"][0]["requirement"]="Any page renders."
            elif mode=="change-policy":bad["retirement_policy"]="Retire on generic success."
            else:
                a=next(row for row in bad["retirement_candidates"] if row["legacy_id"]=="ACTION-08")
                b=next(row for row in bad["retirement_candidates"] if row["legacy_id"]=="ACTION-28")
                a["replacement_id"],b["replacement_id"]=b["replacement_id"],a["replacement_id"]
                for group in bad["replacement_capabilities"]:
                    group["legacy_ids"]=["ACTION-28" if ident=="ACTION-08" else "ACTION-08" if ident=="ACTION-28" else ident for ident in group["legacy_ids"]]
            with self.subTest(mode=mode),self.assertRaises(ValueError):c.validate_model(bad,inventory,fingerprint)
    def test_exact_get_target_and_actor_specific_source_still_work(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-14::Reader::active")
        proof={"supported":True,"status":200,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},"driver":"click","actual_target_path":"/cargo-tracker/admin/show.xhtml","query_keys":["trackingId","jfwid"],"tracking_id":"ABC123","source_page":"admin/listRouted.xhtml","action_executed":True,"target_origin_verified":True}
        adapter.legacy.observation=proof
        self.assertEqual(adapter.execute(case)["tracking_id"],"ABC123")
        adapter,case,_=self.fixture("CURRENT::ACTION-01::anonymous::active")
        self.assertEqual(case["current_source"],"index.xhtml")
        adapter.legacy.observation={"supported":True,"status":303,"driver":"click","actual_target_path":"/cargo-tracker/admin/dashboard.xhtml","query_keys":["jfwid"],"tracking_id":None,"source_page":"index.xhtml","action_executed":True,"target_origin_verified":True}
        self.assertEqual(adapter.execute(case)["status"],303)
    def test_missing_post_source_proof_blocks_instead_of_being_inferred(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-09::Operator::expired")
        adapter.legacy.observation={"supported":True,"identity":{"server_verified":True,"principal":"operator","roles":["Operator"]},"action_method":"POST","action_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH","tracking_id":"ABCDEFGH"}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
    def test_fingerprint_drift_aborts_one_fixture_without_retry(self):
        with patch.object(c,"source_fingerprint",side_effect=["a"*64,"a"*64,"b"*64]),patch.object(c.legacy,"LiveSubsetCandidate",return_value=FakeLegacy({})) as factory:
            with self.assertRaises(RuntimeError):c.CurrentAdapter(live=True)
            factory.assert_called_once()
    def test_definition_change_after_load_aborts_before_fixture_launch(self):
        events=[];fingerprints=iter(["a"*64,"b"*64]);original=c.load_model
        def fingerprint():events.append("fingerprint");return next(fingerprints)
        def load():events.append("load-model");return original()
        with patch.object(c,"source_fingerprint",side_effect=fingerprint),patch.object(c,"load_model",side_effect=load),patch.object(c.legacy,"LiveSubsetCandidate",return_value=FakeLegacy({})) as factory:
            with self.assertRaises(RuntimeError):c.CurrentAdapter(live=True)
            factory.assert_not_called()
        self.assertEqual(events,["fingerprint","load-model","fingerprint"])
    def test_report_uses_constructed_contracts_not_mutable_definition_objects(self):
        adapter=c.CurrentAdapter()
        adapter.model["replacement_capabilities"]=[]
        adapter.model["retirement_candidates"]=[]
        adapter.inventory["view_callbacks"]=[]
        with patch.object(c,"CurrentAdapter",return_value=adapter):result=c.report(live=False)
        self.assertEqual(result["current_counts"],{"BLOCKED":470})
        self.assertEqual(result["retirement_counts"],{"BLOCKED":76})
        self.assertEqual(result["legacy_audit"]["total"],502)
    def test_receipt_names_canonical_cache_and_discloses_code_identity_limit(self):
        with patch.object(c,"source_fingerprint",return_value="a"*64),patch.object(c.legacy,"LiveSubsetCandidate",return_value=FakeLegacy({})) as factory:
            adapter=c.CurrentAdapter(live=True)
        factory.assert_called_once()
        self.assertEqual(adapter.provenance["canonical_contracts_sha256"],adapter._contracts_fingerprint)
        self.assertFalse(adapter.provenance["imported_code_attested"])
        self.assertIn("not attested",adapter.provenance["fingerprint_scope"])
    def test_default_cli_is_unexecuted_native_exit_two_and_preserves_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/"result.json"
            run=subprocess.run([sys.executable,str(Path(c.__file__).with_name("run_current_capabilities.py")),"--output",str(output)],capture_output=True,text=True)
            self.assertEqual(run.returncode,2)
            result=json.loads(output.read_text())
            self.assertEqual(result["current_counts"],{"BLOCKED":470})
            self.assertEqual(result["retirement_counts"],{"BLOCKED":76})
            self.assertEqual(result["legacy_audit"]["total"],502)
            self.assertEqual(result["legacy_audit"]["counts"],{"BLOCKED":502})
            self.assertIsNone(result["provenance"])
    def test_anonymous_and_scoped_machine_cannot_reuse_human_identity(self):
        adapter,case,proof=self.fixture("CURRENT::API-01::anonymous::active")
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter,case,_=self.fixture("CURRENT::API-03-SCOPED::routing-service::active")
        good={"supported":True,"machine_identity_verified":True,"machine_scope":case["required_machine_scope"],"native_identity":{"principal":"routing","roles":["RoutingService"]}}
        adapter.legacy.observation=good;self.assertEqual(adapter.execute(case)["native_identity"]["principal"],"routing")
        for field,value in [("machine_scope","other"),("machine_identity_verified",False),("native_identity",{"principal":"admin","roles":["RoutingService"]})]:
            adapter.legacy.observation={**good,field:value}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
    def test_current_native_loads_cannot_reuse_legacy_observations(self):
        adapter,case,proof=self.fixture("CURRENT::ACTION-20::Reader::active")
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        proof.update(driver="direct",action_executed=True,target_origin_verified=True,actual_target_path="/cargo-tracker/admin/show.xhtml",query_keys=["trackingId"],tracking_id="ABCDEFGH",source_page="admin/show.xhtml?trackingId=ABCDEFGH",current_load_driver="native-current-load-v1",selected_cargo_verified=True,current_values_verified=True,invalid_inputs_verified=True)
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertEqual(adapter.execute(case)["tracking_id"],"ABCDEFGH")
        for key,value in [("current_load_driver","generic"),("selected_cargo_verified",False),("current_values_verified",False),("invalid_inputs_verified",False),("source_page","admin/show.xhtml?trackingId=OTHERID1"),("tracking_id","short")]:
            adapter.legacy.current_observations={case["id"]:{**proof,key:value}}
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)
    def test_current_native_denial_still_requires_exact_identity_and_action_proof(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-07::Reader::active")
        proof={"supported":True,"status":403,"protected_payload_absent":True,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},"driver":"direct","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/admin/changeDestination.xhtml","query_keys":["trackingId"],"tracking_id":"ABCDEFGH","source_page":"admin/changeDestination.xhtml?trackingId=ABCDEFGH","current_load_driver":"native-current-load-v1","invalid_inputs_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertEqual(adapter.execute(case)["status"],403)
        for key,value in [("identity",{"server_verified":True,"principal":"operator","roles":["Reader"]}),("actual_target_path","/other"),("query_keys",["trackingId","trackingId"])]:
            adapter.legacy.current_observations={case["id"]:{**proof,key:value}}
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)

if __name__=="__main__":unittest.main()
