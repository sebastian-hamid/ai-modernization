import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import current_capabilities as c
from contracts import UnsupportedCase,evaluate
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
    def test_reviewed_bg06_scope_receipt_is_source_bound_and_exact(self):
        promotions,provenance=c.reviewed_bg06_scope()
        expected={"CURRENT::BG-06::"+actor+"::active" for actor in c.ACTORS}
        expected.add("CURRENT::BG-06-MACHINE::deployment-migration::active")
        self.assertEqual(promotions,{case:"PASS" for case in expected})
        self.assertEqual(provenance["kind"],"reviewed-fresh-scoped-runtime")
        self.assertRegex(provenance["scope_receipt_sha256"],r"^[0-9a-f]{64}$")
        self.assertTrue(provenance["run_id"].startswith("kan18pg-"))
    def test_live_fingerprint_covers_reviewed_bg06_fixture_inputs(self):
        with patch.object(c.subprocess,"check_output",return_value="") as command:
            c.source_fingerprint()
        paths=command.call_args.args[0]
        for expected in (".dockerignore","infrastructure/database",
                "notes/evidence/kan-15-bg06-scope/validation.json",
                "notes/agent-reviews/2026-11-11-kan15-bg06-scope-review.md"):
            self.assertIn(expected,paths)
    def test_bg06_scope_promotes_only_five_blocked_rows_with_separate_provenance(self):
        adapter=c.CurrentAdapter()
        baseline=[{"case":case["id"],"outcome":"BLOCKED","reason":"unsupported"}
                  for case in adapter.contracts.values()]
        promotions,provenance=c.reviewed_bg06_scope()
        replayed=c.apply_bg06_scoped_results(baseline,promotions,provenance)
        promoted=[row for row in replayed if row["outcome"]=="PASS"]
        self.assertEqual({row["case"] for row in promoted},set(promotions))
        self.assertTrue(all(row["evidence_provenance"]==provenance for row in promoted))
        unchanged_before=[row for row in baseline if row["case"] not in promotions]
        unchanged_after=[row for row in replayed if row["case"] not in promotions]
        self.assertEqual(unchanged_before,unchanged_after)
        self.assertIn("separate fixture",promoted[0]["reason"])
    def test_bg06_scope_promotion_rejects_missing_rows_tampered_provenance_and_pass_rows(self):
        adapter=c.CurrentAdapter()
        baseline=[{"case":case["id"],"outcome":"BLOCKED"} for case in adapter.contracts.values()]
        promotions,provenance=c.reviewed_bg06_scope()
        invalid=[dict(promotions),dict(promotions),dict(promotions)]
        invalid[0].pop(next(iter(promotions)))
        invalid[1][next(iter(promotions))]="BLOCKED"
        bad_provenance={**provenance,"scope_receipt_sha256":"bad"}
        with self.assertRaises(ValueError):c.apply_bg06_scoped_results(baseline,invalid[0],provenance)
        with self.assertRaises(ValueError):c.apply_bg06_scoped_results(baseline,invalid[1],provenance)
        with self.assertRaises(ValueError):c.apply_bg06_scoped_results(baseline,promotions,bad_provenance)
        already_pass=copy.deepcopy(baseline)
        next(row for row in already_pass if row["case"]==next(iter(promotions)))["outcome"]="PASS"
        with self.assertRaises(ValueError):c.apply_bg06_scoped_results(already_pass,promotions,provenance)
        missing_row=[row for row in baseline if row["case"]!=next(iter(promotions))]
        with self.assertRaises(ValueError):c.apply_bg06_scoped_results(missing_row,promotions,provenance)
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
            if mode=="promote-pending":bad["pending_current_actions"].append(bad["mapped_actions"].pop())
            elif mode=="swap-retirement":
                next(row for row in bad["mapped_actions"] if row["legacy_id"]=="ACTION-24")["legacy_id"]="ACTION-08"
                next(row for row in bad["retirement_candidates"] if row["legacy_id"]=="ACTION-08")["legacy_id"]="ACTION-24"
                next(row for row in bad["replacement_capabilities"] if row["id"]=="cancel-editor")["legacy_ids"]=["ACTION-24"]
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
    def test_action08_retirement_requires_fresh_specific_entry_and_replacement_proof(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        case={"id":"RETIREMENT::ACTION-08::Operator","legacy_id":"ACTION-08","actor":"Operator","replacement_case_id":"REPLACEMENT::cancel-editor::Operator"}
        proof={"driver":"browser-retired-action-v1","legacy_id":"ACTION-08","actor":"Operator","method":"POST",
               "source_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH",
               "historical_source_component_id":"j_idt8:j_idt23","historical_source_parameter":"javax.faces.source",
               "current_form_verified":True,"current_csrf_present":True,"current_viewstate_present":True,
               "callback_response_absent":True,"post_target_verified":True,"callback_implementation_absent":True,"response_status":200,
               "independent_effects_unchanged":True,
               "identity":{"server_verified":True,"principal":"operator","roles":["Operator"]}}
        adapter.legacy.retirement_observations={case["id"]:proof}
        replacement=[{"case":case["replacement_case_id"],"outcome":"PASS"}]
        self.assertEqual(adapter.execute_retirement(case,replacement),proof)
        for field,value in [("historical_source_component_id","wrong"),("current_csrf_present",False),
                            ("callback_response_absent",False),("post_target_verified",False),
                            ("callback_implementation_absent",False),("independent_effects_unchanged",False)]:
            adapter.legacy.retirement_observations={case["id"]:{**proof,field:value}}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute_retirement(case,replacement)
        adapter.legacy.retirement_observations={case["id"]:proof}
        with self.assertRaises(UnsupportedCase):adapter.execute_retirement(case,[])
        adapter._run_fingerprint="b"*64
        with self.assertRaises(UnsupportedCase):adapter.execute_retirement(case,replacement)

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

    def test_current_itinerary_alias_cannot_reuse_direct_route_evidence(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-18::Reader::active")
        proof={"supported":True,"status":403,"protected_payload_absent":True,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},"driver":"direct","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/admin/route.xhtml","query_keys":["trackingId"],"tracking_id":"ABCDEFGH","source_page":"admin/selectItinerary.xhtml?trackingId=ABCDEFGH","current_load_driver":"native-current-load-v1","invalid_inputs_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        proof["route_alias_verified"]=True
        self.assertEqual(adapter.execute(case)["status"],403)
        proof["source_page"]="admin/route.xhtml?trackingId=ABCDEFGH"
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_current_route_details_require_own_render_evidence(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-15::Operator::active")
        proof={"supported":True,"status":200,"identity":{"server_verified":True,"principal":"operator","roles":["Operator"]},"driver":"direct","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/admin/route.xhtml","query_keys":["trackingId"],"tracking_id":"ABCDEFGH","source_page":"admin/route.xhtml?trackingId=ABCDEFGH","current_load_driver":"native-current-load-v1","invalid_inputs_verified":True,"selected_cargo_verified":True,"current_values_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        proof["route_details_verified"]=True
        self.assertTrue(adapter.execute(case)["route_details_verified"])

    def test_claimed_cargo_requires_persisted_details_from_click(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-10::Reader::active")
        proof={"supported":True,"status":200,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},"driver":"click","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/admin/show.xhtml","query_keys":["trackingId"],"tracking_id":"ABCDEFGH","source_page":"admin/listClaimed.xhtml","current_navigation_driver":"browser-claimed-cargo-v1","selected_cargo_verified":True,"persisted_details_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertTrue(adapter.execute(case)["persisted_details_verified"])
        for key,value in [("persisted_details_verified",False),("driver","direct"),("source_page","admin/listRouted.xhtml")]:
            adapter.legacy.current_observations={case["id"]:{**proof,key:value}}
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_unrouted_route_entry_requires_verified_chain_and_state(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-11::Operator::active")
        proof={"supported":True,"status":200,"identity":{"server_verified":True,"principal":"operator","roles":["Operator"]},
               "driver":"click","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/admin/route.xhtml",
               "query_keys":["trackingId"],"tracking_id":"ABCDEFGH","source_page":"admin/listNotRouted.xhtml",
               "current_navigation_driver":"browser-cargo-entry-v1","entry_state":"NOT_ROUTED",
               "entry_chain_verified":True,"selected_cargo_verified":True,"route_choices_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertTrue(adapter.execute(case)["entry_chain_verified"])
        for key,value in [("entry_state","ROUTED"),("entry_chain_verified",False),("source_page","admin/show.xhtml?trackingId=ABCDEFGH")]:
            adapter.legacy.current_observations={case["id"]:{**proof,key:value}}
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_canonical_anonymous_return_uses_explicit_editor_stage(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-13::anonymous::active")
        proof={"return_driver":"native-staged-return-v1","tracking_id":"ABCDEFGH","save":None,"denied_entry_effects_unchanged":True}
        for stage,path in [("editor","changeDestination"),("details","show")]:
            proof[stage]={"method":"GET","path":"/cargo-tracker/admin/"+path+".xhtml?trackingId=ABCDEFGH",
                          "status":303,"protected_payload_absent":True,"redirect_is_configured_login":True}
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertEqual(case["current_source"],"admin/changeDestination.xhtml")
        self.assertEqual(adapter.execute(case)["evaluated_stage"],"editor")

    def test_lookup_case_requires_actual_post_and_invalid_input_evidence(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-45::Reader::active")
        proof={"supported":True,"status":200,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},
               "current_navigation_driver":"browser-lookup-v1","tracking_id":"ABCDEFGH","driver":"click",
               "action_method":"POST","action_path":"/cargo-tracker/admin/track.xhtml","entry_page":"public/track.xhtml",
               "source_entry_verified":True,"submission_status":303,"invalid_inputs_verified":True,"csrf_checks_verified":True,
               "legacy_entry_verified":True,"selected_cargo_verified":True,"persisted_details_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertEqual(adapter.execute(case)["action_method"],"POST")
        for key,value in [("legacy_entry_verified",False),("action_method","GET"),("invalid_inputs_verified",False),("csrf_checks_verified",False)]:
            adapter.legacy.current_observations={case["id"]:{**proof,key:value}}
            with self.subTest(key=key),self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_marker_requires_keyboard_activation_of_verified_marker(self):
        adapter,case,_=self.fixture("CURRENT::ACTION-25::Reader::active")
        proof={"supported":True,"status":200,"identity":{"server_verified":True,"principal":"reader","roles":["Reader"]},
               "current_navigation_driver":"browser-marker-v1","tracking_id":"ABCDEFGH","driver":"keyboard",
               "action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/admin/show.xhtml",
               "query_keys":["trackingId"],"source_page":"admin/live.xhtml","live_marker_verified":True,
               "selected_cargo_verified":True,"persisted_details_verified":True}
        adapter.legacy.current_observations={case["id"]:proof}
        self.assertTrue(adapter.execute(case)["live_marker_verified"])
        proof["live_marker_verified"]=False
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_canonical_replacement_preserves_reader_return_access(self):
        adapter,case,base=self.fixture("REPLACEMENT::cancel-editor::Reader")
        sample={"fixture_id":"a"*64,"tables":{"CARGO":{"rows":1}},"queues":{"handling":1},"business_invocations":{"save":1}}
        proof={"replacement_driver":"browser-replacement-v1","group":"cancel-editor","tracking_id":"ABCDEFGH",
               "identity":base["identity"],"source_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH",
               "target_path":"/cargo-tracker/admin/show.xhtml?trackingId=ABCDEFGH","source_status":403,"target_status":200,
               "source_entry_verified":True,"return_access_verified":True,"source_payload_absent":True,
               "persisted_state_unchanged":True,
               "before":{**copy.deepcopy(sample),"stage":"cancel-editor:Reader:before"},
               "after":{**copy.deepcopy(sample),"stage":"cancel-editor:Reader:after"}}
        proof["before"]["business_invocations"]["net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"]=5
        proof["after"]["business_invocations"]["net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"]=6
        adapter.legacy.replacement_observations={case["id"]:proof}
        result=adapter.execute(case)
        self.assertEqual(result["status"],403)
        self.assertEqual(result["target_status"],200)
        self.assertTrue(result["invocation_denied"])
        proof["after"]["fixture_id"]="b"*64
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_action08_anonymous_retirement_requires_login_redirect_and_no_identity(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        case={"id":"RETIREMENT::ACTION-08::anonymous","legacy_id":"ACTION-08","actor":"anonymous","replacement_case_id":"REPLACEMENT::cancel-editor::anonymous"}
        proof={"driver":"browser-retired-action-v1","legacy_id":"ACTION-08","actor":"anonymous","method":"POST",
               "source_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH",
               "historical_source_component_id":"j_idt8:j_idt23","historical_source_parameter":"javax.faces.source",
               "post_target_verified":True,"callback_implementation_absent":True,"response_status":303,
               "authorization_denied":True,"protected_payload_absent":True,"redirect_is_configured_login":True,
               "independent_effects_unchanged":True}
        adapter.legacy=FakeLegacy({})
        adapter.legacy.retirement_observations={case["id"]:proof}
        replacement=[{"case":case["replacement_case_id"],"outcome":"PASS"}]
        self.assertEqual(adapter.execute_retirement(case,replacement),proof)
        for field,value in [("response_status",403),("redirect_is_configured_login",False),
                            ("identity",{"server_verified":True,"principal":"operator","roles":["Operator"]})]:
            adapter.legacy.retirement_observations={case["id"]:{**proof,field:value}}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute_retirement(case,replacement)
    def test_bg03_requires_all_human_denials_and_dedicated_worker_identity(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        sample={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},
                "queues":{"test":{"MessageCount":0}},
                "business_invocations":{"HandlingEventRegistrationAttemptConsumer#onMessage":0}}
        effects={"settled":True,"fixture_id":"owned","before_fixture":"owned","after_fixture":"owned",
                 "before":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]},
                 "after":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]}}
        identities={"Reader":{"server_verified":True,"principal":"reader","roles":["Reader"]},
                    "Operator":{"server_verified":True,"principal":"operator","roles":["Operator"]},
                    "Administrator":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        denials={}
        for actor in ["anonymous","Reader","Operator","Administrator"]:
            proof={"driver":"native-handling-worker-v1","actor":actor,"supported":True,
                   "status":401 if actor=="anonymous" else 403,"invocation_denied":True,
                   "direct_service_denied":True,"protected_payload_absent":True,
                   "independent_effects_unchanged":True,"effects":effects}
            if actor!="anonymous":proof["identity"]=identities[actor]
            denials[actor]=proof
            case=adapter.contracts["CURRENT::BG-03::"+actor+"::active"]
            adapter.legacy.handling_worker_denials={actor:proof}
            self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
            for field,value in [("direct_service_denied",False),("protected_payload_absent",False),
                                ("independent_effects_unchanged",False)]:
                adapter.legacy.handling_worker_denials={actor:{**proof,field:value}}
                with self.subTest(actor=actor,field=field):
                    if field=="protected_payload_absent":
                        self.assertNotEqual(evaluate(case,adapter.execute(case))[0],"PASS")
                    else:
                        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        machine={"driver":"native-handling-worker-v1","supported":True,"status":200,
                 "machine_identity_verified":True,
                 "machine_scope":"Dedicated server worker authority; human identity does not automatically propagate through ObjectMessage",
                 "authorized_adapter_events_verified":True,"producer_boundary_verified":True,
                 "human_direct_denials_effects_unchanged":True,"semantic_success":True,
                 "authorized_effect_verified":True,
                 "native_identity":{"server_verified":True,"principal":"handling-worker","roles":["HandlingWorker"]}}
        adapter.legacy.handling_worker_denials=denials
        adapter.legacy.handling_worker_observation=machine
        producer_raw={"anonymousDenied":True,"humanAuthenticated":[True,True,True],
            "humanSendDenied":[True,True,True],
            "machinePrincipals":["batch-worker","handling-worker","inspection-worker","notification-worker"],
            "machineAuthenticated":[True,True,True,True],"machineSendDenied":[True,True,True,True],
            "trustedAllowed":True,"rejectedQueueDenied":True,"deliveredQueueDenied":True}
        adapter.legacy.remote_producer_raw_observation=producer_raw
        adapter.legacy.remote_producer_unauthorized_effects_unchanged=True
        case=adapter.contracts["CURRENT::BG-03-MACHINE::worker-BG-03::active"]
        self.assertEqual(case["binding_status"],"native-handling-worker")
        self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
        for field,value in [("machine_identity_verified",False),
                            ("machine_scope","human identity forwarded"),
                            ("authorized_adapter_events_verified",False),
                            ("producer_boundary_verified",False),
                            ("human_direct_denials_effects_unchanged",False)]:
            adapter.legacy.handling_worker_observation={**machine,field:value}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        for field,value in [("machineSendDenied",[True,True,False,True]),
                            ("machinePrincipals",["batch-worker","inspection-worker","handling-worker","notification-worker"])]:
            adapter.legacy.remote_producer_raw_observation={**producer_raw,field:value}
            with self.subTest(remote_proof_field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.remote_producer_raw_observation=producer_raw
        adapter.legacy.handling_worker_observation={**machine,
            "native_identity":{"server_verified":True,"principal":"operator","roles":["Operator"]}}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
    def test_service04_requires_both_direct_worker_only_denials_and_contiguous_effects(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        actors={"Reader":{"server_verified":True,"principal":"reader","roles":["Reader"]},
                "Operator":{"server_verified":True,"principal":"operator","roles":["Operator"]},
                "Administrator":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        snapshot={"database":{"CARGO":{"rows":1,"sha256":"a"}},
                  "queue":{"events":{"MessageCount":0}},
                  "business_audit":{"register":0,"inspect":0}}
        denials={}
        for actor in c.ACTORS:
            identity=None if actor=="anonymous" else actors[actor]
            effect={"settled":True,"fixture_id":"owned","before_fixture":"owned","after_fixture":"owned",
                    "before":snapshot,"after":snapshot}
            def proof(driver):
                item={"driver":driver,"actor":actor,"supported":True,
                      "status":401 if actor=="anonymous" else 403,"invocation_denied":True,
                      "direct_service_denied":True,"protected_payload_absent":True,
                      "independent_effects_unchanged":True,"effects":copy.deepcopy(effect)}
                if identity is not None:item["identity"]=identity
                return item
            denials[actor]=(proof("native-handling-worker-v1"),proof("native-inspection-worker-v1"))
            case=adapter.contracts[f"CURRENT::SERVICE-04::{actor}::active"]
            adapter.legacy.handling_worker_denials={actor:denials[actor][0]}
            adapter.legacy.inspection_worker_denials={actor:denials[actor][1]}
            self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
        actor="Operator";case=adapter.contracts[f"CURRENT::SERVICE-04::{actor}::active"]
        handling,inspection=denials[actor]
        for field,value in [("direct_service_denied",False),("protected_payload_absent",False),
                            ("independent_effects_unchanged",False),("status",200)]:
            adapter.legacy.handling_worker_denials={actor:{**handling,field:value}}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.handling_worker_denials={actor:handling}
        for field,value in [("actor","Reader"),("driver","generic-success"),
                            ("identity",{"server_verified":True,"principal":"admin","roles":["Operator"]})]:
            adapter.legacy.inspection_worker_denials={actor:{**inspection,field:value}}
            with self.subTest(inspection_field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.inspection_worker_denials={actor:inspection}
        changed=copy.deepcopy(inspection);changed["effects"]["after"]["queue"]["events"]["MessageCount"]=1
        adapter.legacy.inspection_worker_denials={actor:changed}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.inspection_worker_denials={actor:inspection}
        gap=copy.deepcopy(inspection);gap["effects"]["before"]["database"]["CARGO"]["rows"]=2
        adapter.legacy.inspection_worker_denials={actor:gap}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.inspection_worker_denials={actor:inspection}
        missing=copy.deepcopy(inspection);missing["effects"]["after"].pop("business_audit")
        adapter.legacy.inspection_worker_denials={actor:missing}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_bg04_requires_human_denials_origin_correlation_and_producer_boundary(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="b"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"b"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        sample={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},
                "queues":{"test":{"MessageCount":0}},
                "business_invocations":{"CargoHandledConsumer#onMessage":0}}
        effects={"settled":True,"fixture_id":"owned","before_fixture":"owned","after_fixture":"owned",
                 "before":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]},
                 "after":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]}}
        identities={"Reader":{"server_verified":True,"principal":"reader","roles":["Reader"]},
                    "Operator":{"server_verified":True,"principal":"operator","roles":["Operator"]},
                    "Administrator":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        denials={}
        for actor in ["anonymous","Reader","Operator","Administrator"]:
            proof={"driver":"native-inspection-worker-v1","actor":actor,"supported":True,
                   "status":401 if actor=="anonymous" else 403,"invocation_denied":True,
                   "direct_service_denied":True,"protected_payload_absent":True,
                   "independent_effects_unchanged":True,"effects":effects}
            if actor!="anonymous":proof["identity"]=identities[actor]
            denials[actor]=proof
            case=adapter.contracts["CURRENT::BG-04::"+actor+"::active"]
            adapter.legacy.inspection_worker_denials={actor:proof}
            self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
            adapter.legacy.inspection_worker_denials={actor:{**proof,"independent_effects_unchanged":False}}
            with self.subTest(actor=actor),self.assertRaises(UnsupportedCase):adapter.execute(case)
        machine={"driver":"native-inspection-worker-v1","supported":True,"status":200,
                 "machine_identity_verified":True,
                 "machine_scope":"Server worker; audit origin/correlation to be designed, not trusted role fields in payload",
                 "producer_origin_verified":True,"correlation_verified":True,
                 "correlation_count":2,"unique_correlation_count":2,
                 "authorized_adapter_events_verified":True,"producer_boundary_verified":True,
                 "human_direct_denials_effects_unchanged":True,
                 "semantic_success":True,"authorized_effect_verified":True,
                 "native_identity":{"server_verified":True,"principal":"inspection-worker","roles":["InspectionWorker"]}}
        adapter.legacy.inspection_worker_denials=denials
        adapter.legacy.inspection_worker_observation=machine
        producer_raw={"cargoHandledAnonymousDenied":True,
            "cargoHandledHumanAuthenticated":[True,True,True],"cargoHandledHumanSendDenied":[True,True,True],
            "cargoHandledMachinePrincipals":["batch-worker","inspection-worker","notification-worker"],
            "cargoHandledMachineAuthenticated":[True,True,True],"cargoHandledMachineSendDenied":[True,True,True],
            "cargoHandledTrustedPrincipal":"handling-worker","cargoHandledTrustedAllowed":True}
        adapter.legacy.cargo_handled_producer_raw_observation=producer_raw
        adapter.legacy.cargo_handled_producer_effects_unchanged=True
        case=adapter.contracts["CURRENT::BG-04-MACHINE::worker-BG-04::active"]
        self.assertEqual(case["binding_status"],"native-inspection-worker")
        self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
        for field,value in [("machine_identity_verified",False),("producer_origin_verified",False),
                            ("correlation_verified",False),("authorized_adapter_events_verified",False),
                            ("producer_boundary_verified",False),("human_direct_denials_effects_unchanged",False)]:
            adapter.legacy.inspection_worker_observation={**machine,field:value}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):
                adapter.execute(case)
        adapter.legacy.inspection_worker_observation=machine
        for field,value in [("cargoHandledAnonymousDenied",False),
                ("cargoHandledHumanSendDenied",[True,True,False]),
                ("cargoHandledMachinePrincipals",["batch-worker","notification-worker","inspection-worker"]),
                ("cargoHandledMachineSendDenied",[True,False,True]),
                ("cargoHandledTrustedPrincipal","inspection-worker"),
                ("cargoHandledTrustedAllowed",False)]:
            adapter.legacy.cargo_handled_producer_raw_observation={**producer_raw,field:value}
            with self.subTest(producer_field=field),self.assertRaises(UnsupportedCase):
                adapter.execute(case)
        adapter.legacy.cargo_handled_producer_raw_observation=producer_raw
        adapter.legacy.cargo_handled_producer_effects_unchanged=False
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_bg05_requires_consumer_view_denials_and_rejection_disposition(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="c"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"c"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        sample={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},
                "queues":{"jms.queue.HandlingEventRegistrationAttemptQueue":{"MessageCount":0}},
                "business_invocations":{"HandlingEventRegistrationAttemptConsumer#onMessage":0}}
        effects={"settled":True,"fixture_id":"owned","before_fixture":"owned","after_fixture":"owned",
                 "before":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]},
                 "after":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]}}
        identities={"Reader":{"server_verified":True,"principal":"reader","roles":["Reader"]},
                    "Operator":{"server_verified":True,"principal":"operator","roles":["Operator"]},
                    "Administrator":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        denials={}
        for actor in ["anonymous","Reader","Operator","Administrator"]:
            proof={"driver":"native-notification-worker-v1","actor":actor,"supported":True,
                   "status":401 if actor=="anonymous" else 403,"invocation_denied":True,
                   "direct_service_denied":True,"protected_payload_absent":True,
                   "independent_effects_unchanged":True,"effects":effects}
            if actor!="anonymous":proof["identity"]=identities[actor]
            denials[actor]=proof
            case=adapter.contracts["CURRENT::BG-05::"+actor+"::active"]
            adapter.legacy.notification_worker_denials={actor:proof}
            self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
            adapter.legacy.notification_worker_denials={actor:{**proof,"independent_effects_unchanged":False}}
            with self.subTest(actor=actor),self.assertRaises(UnsupportedCase):adapter.execute(case)
        machine={"driver":"native-notification-worker-v1","supported":True,"status":200,
                 "machine_identity_verified":True,"machine_scope":"Server workers",
                 "consumer_bindings_verified":True,"sanitized_logs_verified":True,
                 "queue_cycles_verified":True,"producer_boundary_verified":False,
                 "rejection_producer_verified":True,"final_disposition_verified":True,
                 "native_identity":{"server_verified":True,"principal":"notification-worker","roles":["NotificationWorker"]}}
        adapter.legacy.notification_worker_denials=denials
        adapter.legacy.notification_worker_observation=machine
        adapter.legacy.rejection_disposition_observation={"trusted_broker_dead_letter_verified":True,
            "sanitized_rejection_audit_verified":True,"business_side_effects_unchanged":True}
        case=adapter.contracts["CURRENT::BG-05-MACHINE::worker-BG-05::active"]
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.notification_worker_observation={**machine,"producer_boundary_verified":True}
        adapter.legacy.rejection_disposition_observation["trusted_broker_dead_letter_verified"]=False
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_bg02_requires_private_processing_and_exact_archive_failed_outputs(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        admin={"driver":"native-batch-import-v1","actor":"Administrator","supported":True,
               "status":200,"semantic_success":True,"authorized_effect_verified":True,
               "authorized_form_status":200,"csrf_present":True,"viewstate_present":True,
               "authorized_start_accepted":True,"empty_business_state_unchanged":True,
               "empty_control_calls_bounded":True,"worker_identity_verified":True,
               "valid_event_persisted":True,"valid_queue_cycles":True,"valid_table_deltas":True,
               "valid_invocation_deltas_bounded":True,"direct_api_denials":{"read":403,"start":403},
               "direct_api_payload_absent":{"read":True,"start":True},"direct_api_effects_unchanged":True,
               "identity":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        processing={"driver":"native-batch-processing-v1","actor":"Administrator","supported":True,"status":200,
                    "authorized_job_completed":True,"batch_worker_identity_verified":True,
                    "directory_policy_verified":True,"valid_input_consumed":True,"valid_event_persisted":True,
                    "valid_archive_verified":True,"invalid_input_consumed":True,
                    "invalid_failed_output_verified":True,"business_side_effects_bounded":True,
                    "administrator_identity":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        adapter.legacy.batch_import_observations={"Administrator":admin}
        adapter.legacy.batch_processing_observation=processing
        case=adapter.contracts["CURRENT::BG-02::Administrator::active"]
        self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
        for field,value in [("directory_policy_verified",False),("valid_archive_verified",False),
                            ("invalid_failed_output_verified",False),("business_side_effects_bounded",False),
                            ("batch_worker_identity_verified",False)]:
            adapter.legacy.batch_processing_observation={**processing,field:value}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.batch_processing_observation=processing
        adapter.legacy.batch_import_observations={"Administrator":{**admin,"identity":{"server_verified":False}}}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        self.assertEqual(case["binding_status"],"native-batch-processing")
    def test_bg01_machine_requires_distinct_batch_worker_and_scoped_processing(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        processing={"driver":"native-batch-processing-v1","actor":"Administrator","supported":True,"status":200,
                    "authorized_job_completed":True,"batch_worker_identity_verified":True,
                    "directory_policy_verified":True,"valid_input_consumed":True,"valid_event_persisted":True,
                    "valid_archive_verified":True,"invalid_input_consumed":True,
                    "invalid_failed_output_verified":True,"business_side_effects_bounded":True,
                    "administrator_identity":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        adapter.legacy.batch_processing_observation=processing
        case=adapter.contracts["CURRENT::BG-01-MACHINE::worker-BG-01::active"]
        self.assertEqual(case["binding_status"],"native-batch-worker")
        observation=adapter.execute(case)
        self.assertEqual(observation["native_identity"],{"server_verified":True,"principal":"batch-worker","roles":["BatchWorker"]})
        self.assertEqual(observation["initiator_identity"]["principal"],"admin")
        self.assertEqual(evaluate(case,observation)[0],"PASS")
        for field,value in [("authorized_job_completed",False),("valid_event_persisted",False),
                            ("directory_policy_verified",False),("business_side_effects_bounded",False),
                            ("administrator_identity",{"server_verified":True,"principal":"batch-worker","roles":["BatchWorker"]})]:
            adapter.legacy.batch_processing_observation={**processing,field:value}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_bg02_machine_requires_approved_filesystem_producer_private_paths_and_batch_worker(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="d"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"d"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        processing={"driver":"native-batch-processing-v1","supported":True,"actor":"Administrator","status":200,
            "authorized_job_completed":True,"batch_worker_identity_verified":True,"directory_policy_verified":True,
            "filesystem_producer_identity":{"verified":True,"uid":0,"scope":"approved fixture administration tooling"},
            "filesystem_worker_identity":{"verified":True,"uid":1000},"filesystem_worker_uid":1000,
            "trusted_filesystem_staging_verified":True,"untrusted_os_identity_denied":True,
            "untrusted_os_uid":65534,"untrusted_os_access":{name:{"list_denied":True,"read_denied":True,
                "write_denied":True,"marker_absent":True} for name in ["incoming","archive","failed"]},
            "valid_input_consumed":True,"valid_event_persisted":True,"valid_archive_verified":True,
            "invalid_input_consumed":True,"invalid_failed_output_verified":True,"business_side_effects_bounded":True,
            "administrator_identity":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        adapter.legacy.batch_processing_observation=processing
        case=adapter.contracts["CURRENT::BG-02-MACHINE::worker-BG-02::active"]
        self.assertEqual(case["binding_status"],"native-batch-worker")
        observation=adapter.execute(case)
        self.assertEqual(observation["native_identity"],{"server_verified":True,"principal":"batch-worker","roles":["BatchWorker"]})
        self.assertEqual(evaluate(case,observation)[0],"PASS")
        for field,value in [("trusted_filesystem_staging_verified",False),("untrusted_os_identity_denied",False),
                ("directory_policy_verified",False),("valid_archive_verified",False),("batch_worker_identity_verified",False),
                ("untrusted_os_uid",True)]:
            adapter.legacy.batch_processing_observation={**processing,field:value}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        for field,value in [("filesystem_producer_identity",{"verified":True,"uid":1000,"scope":"approved fixture administration tooling"}),
                ("filesystem_worker_identity",{"verified":False,"uid":0}),
                ("filesystem_producer_identity",{"verified":True,"uid":False,"scope":"approved fixture administration tooling"})]:
            adapter.legacy.batch_processing_observation={**processing,field:value}
            with self.subTest(identity_field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        adapter.legacy.batch_processing_observation={**processing,"filesystem_worker_identity":{"verified":True,"uid":1},"filesystem_worker_uid":True}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)
        for directory,field in [("incoming","list_denied"),("archive","read_denied"),
                ("failed","write_denied"),("incoming","marker_absent")]:
            access={name:dict(proof) for name,proof in processing["untrusted_os_access"].items()}
            access[directory][field]=False
            adapter.legacy.batch_processing_observation={**processing,"untrusted_os_access":access}
            with self.subTest(directory=directory,proof_field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        access={name:dict(proof) for name,proof in processing["untrusted_os_access"].items()}
        access.pop("failed")
        adapter.legacy.batch_processing_observation={**processing,"untrusted_os_access":access}
        with self.assertRaises(UnsupportedCase):adapter.execute(case)

    def test_bg01_current_gate_requires_actor_specific_denial_or_admin_worker_evidence(self):
        adapter=c.CurrentAdapter()
        adapter._run_fingerprint="a"*64
        adapter.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":"a"*64,"legacy_fixture_cleanup_verified":True}
        adapter.legacy=FakeLegacy({})
        direct={"read":403,"start":403}
        direct_absent={"read":True,"start":True}
        common={"driver":"native-batch-import-v1","direct_api_denials":direct,
                "direct_api_payload_absent":direct_absent,"direct_api_effects_unchanged":True}
        admin={"driver":"native-batch-import-v1","actor":"Administrator",**common,
               "supported":True,"status":200,"semantic_success":True,"authorized_effect_verified":True,
               "authorized_form_status":200,"csrf_present":True,"viewstate_present":True,
               "authorized_start_accepted":True,"empty_business_state_unchanged":True,
               "empty_control_calls_bounded":True,"worker_identity_verified":True,
               "valid_event_persisted":True,"valid_queue_cycles":True,"valid_table_deltas":True,
               "valid_invocation_deltas_bounded":True,
               "identity":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        adapter.legacy.batch_import_observations={"Administrator":admin}
        admin_case=adapter.contracts["CURRENT::BG-01::Administrator::active"]
        self.assertEqual(evaluate(admin_case,adapter.execute(admin_case))[0],"PASS")
        for field,value in [("worker_identity_verified",False),("authorized_start_accepted",False),
                            ("direct_api_effects_unchanged",False)]:
            adapter.legacy.batch_import_observations={"Administrator":{**admin,field:value}}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(admin_case)
        for role,actor,expected_status in [("Reader","reader",403),("Operator","operator",403)]:
            sample={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},
                    "queues":{"test":{"MessageCount":0}},
                    "business_invocations":{"BatchImport#start":0}}
            effects={"settled":True,"fixture_id":"owned","before_fixture":"owned","after_fixture":"owned",
                     "before":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]},
                     "after":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]}}
            denied={"driver":"native-batch-import-v1","actor":role,**common,
                    "supported":True,"status":expected_status,"invocation_denied":True,"effects":effects,
                    "get_status":expected_status,"post_status":expected_status,
                    "protected_payload_absent":True,"independent_effects_unchanged":True,
                    "identity":{"server_verified":True,"principal":actor,"roles":[role]}}
            adapter.legacy.batch_import_observations={role:denied}
            case=adapter.contracts["CURRENT::BG-01::"+role+"::active"]
            self.assertEqual(evaluate(case,adapter.execute(case))[0],"PASS")
            for field,value in [("independent_effects_unchanged",False),("protected_payload_absent",False),("get_status",200)]:
                adapter.legacy.batch_import_observations={role:{**denied,field:value}}
                with self.subTest(role=role,field=field),self.assertRaises(UnsupportedCase):adapter.execute(case)
        sample={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},
                "queues":{"test":{"MessageCount":0}},
                "business_invocations":{"BatchImport#start":0}}
        effects={"settled":True,"fixture_id":"owned","before_fixture":"owned","after_fixture":"owned",
                 "before":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]},
                 "after":{"database":sample["tables"],"queue":sample["queues"],"business_audit":sample["business_invocations"]}}
        anonymous={"driver":"native-batch-import-v1","actor":"anonymous",**common,
                   "supported":True,"status":303,"invocation_denied":True,"effects":effects,
                   "get_status":303,"post_status":303,"redirect_is_configured_login":True,
                   "protected_payload_absent":True,"independent_effects_unchanged":True}
        adapter.legacy.batch_import_observations={"anonymous":anonymous}
        anon_case=adapter.contracts["CURRENT::BG-01::anonymous::active"]
        self.assertEqual(evaluate(anon_case,adapter.execute(anon_case))[0],"PASS")
        for field,value in [("redirect_is_configured_login",False),("independent_effects_unchanged",False),
                            ("identity",{"principal":"admin","roles":["Administrator"]})]:
            adapter.legacy.batch_import_observations={"anonymous":{**anonymous,field:value}}
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):adapter.execute(anon_case)
if __name__=="__main__":unittest.main()
