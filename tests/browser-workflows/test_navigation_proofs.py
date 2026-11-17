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

class RetiredTrackingDiscoveryProofTests(unittest.TestCase):
    def fixture(self):
        proofs={};hashes=h.action23_source_evidence()
        identities={"Reader":{"server_verified":True,"principal":"reader","roles":["Reader"]},
                    "Operator":{"server_verified":True,"principal":"operator","roles":["Operator"]},
                    "Administrator":{"server_verified":True,"principal":"admin","roles":["Administrator"]}}
        for role in ("anonymous","Reader","Operator","Administrator"):
            if role=="anonymous":
                proofs["RETIREMENT::ACTION-08::"+role]={"driver":"browser-retired-action-v1","legacy_id":"ACTION-08","actor":role,"method":"POST",
                    "source_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH","historical_source_component_id":"j_idt8:j_idt23",
                    "post_target_verified":True,"callback_implementation_absent":True,"independent_effects_unchanged":True,"response_status":303,
                    "authorization_denied":True,"protected_payload_absent":True,"redirect_is_configured_login":True,"identity":None}
            elif role=="Reader":
                proofs["RETIREMENT::ACTION-08::"+role]={"driver":"browser-retired-action-v1","legacy_id":"ACTION-08","actor":role,"method":"POST",
                    "source_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH","historical_source_component_id":"j_idt8:j_idt23",
                    "post_target_verified":True,"callback_implementation_absent":True,"independent_effects_unchanged":True,"response_status":403,
                    "authorization_denied":True,"protected_payload_absent":True,"identity":identities[role]}
            else:
                proofs["RETIREMENT::ACTION-08::"+role]={"driver":"browser-retired-action-v1","legacy_id":"ACTION-08","actor":role,"method":"POST",
                    "source_path":"/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH","historical_source_component_id":"j_idt8:j_idt23",
                    "post_target_verified":True,"callback_implementation_absent":True,"independent_effects_unchanged":True,"response_status":200,
                    "current_form_verified":True,"current_csrf_present":True,"current_viewstate_present":True,"callback_response_absent":True,"identity":identities[role]}
            proof={"driver":"browser-retired-tracking-v1","legacy_id":"ACTION-23","actor":role,"method":"POST",
                "source_path":"/cargo-tracker/admin/track.xhtml","historical_source_component_id":"trackingForm:trackIdInput",
                "historical_source_parameter":"javax.faces.source","callback_implementation_absent":True,
                "legacy_binding_discrepancy_verified":True,"source_hashes":hashes,"post_target_verified":True,
                "callback_response_absent":True,"protected_payload_absent":True,"autocomplete_payload_absent":True,
                "cargo_snapshot_sha256":"a"*64,"cargo_snapshot_count":4,"independent_effects_unchanged":True}
            if role=="anonymous":proof.update(response_status=303,authorization_denied=True,redirect_is_configured_login=True,identity=None)
            else:proof.update(response_status=200,authorization_denied=False,current_source_parameter="jakarta.faces.source",
                current_form_verified=True,current_legacy_component_absent=True,current_csrf_present=True,current_viewstate_present=True,identity=identities[role])
            proofs["RETIREMENT::ACTION-23::"+role]=proof
            public={"driver":"browser-retired-public-tracking-v1","legacy_id":"ACTION-44","actor":role,"method":"POST",
                "source_path":"/cargo-tracker/public/track.xhtml","historical_source_component_id":"trackingForm:trackingId",
                "historical_source_parameter":"javax.faces.source","current_source_parameter":"jakarta.faces.source",
                "current_callback_implementation_absent":True,"legacy_callback_implementation_verified":True,
                "source_hashes":h.action44_source_evidence(),"response_status":200,
                "post_target_verified":True,"current_form_verified":True,"current_csrf_present":False,
                "current_viewstate_present":True,"current_legacy_component_absent":True,
                "callback_response_absent":True,"autocomplete_payload_absent":True,"authorization_denied":False,
                "protected_payload_absent":True,"independent_effects_unchanged":True,"redirect_is_configured_login":False,
                "cargo_snapshot_sha256":"b"*64,"cargo_snapshot_count":4}
            if role=="anonymous":public["identity"]=None
            else:public["identity"]=identities[role]
            proofs["RETIREMENT::ACTION-44::"+role]=public
            deadline={"driver":"browser-retired-deadline-v1","legacy_id":"ACTION-26","actor":role,"method":"POST",
                "source_path":"/cargo-tracker/booking/booking-date.xhtml","historical_source_component_id":"dateForm:deadline",
                "historical_source_parameter":"javax.faces.source","source_hashes":h.action26_source_evidence(),"current_post_handler_absent":True,
                "post_target_verified":True,"callback_response_absent":True,"protected_payload_absent":True,
                "independent_effects_unchanged":True,"cargo_snapshot_sha256":"c"*64,"cargo_snapshot_count":13}
            if role=="anonymous":deadline.update(response_status=303,authorization_denied=True,redirect_is_configured_login=True,identity=None)
            elif role=="Reader":deadline.update(response_status=403,authorization_denied=True,identity=identities[role])
            else:deadline.update(response_status=405,authorization_denied=False,current_form_verified=True,
                current_csrf_present=True,current_viewstate_present=True,identity=identities[role])
            proofs["RETIREMENT::ACTION-26::"+role]=deadline
            rendered=h.action32_render_evidence()
            destination={"driver":"browser-retired-destination-next-v1","legacy_id":"ACTION-32","actor":role,"method":"POST",
                "source_path":"/cargo-tracker/booking/booking-destination.xhtml","historical_source_component_id":rendered["component_id"],
                "historical_submitted_parameter":rendered["component_id"],"historical_source_parameter":"javax.faces.source",
                "historical_render_evidence_verified":True,"historical_button_markup_sha256":rendered["button_markup_sha256"],
                "source_hashes":rendered["source_hashes"],"current_post_handler_absent":True,"post_target_verified":True,
                "callback_response_absent":True,"protected_payload_absent":True,"independent_effects_unchanged":True,
                "cargo_snapshot_sha256":"d"*64,"cargo_snapshot_count":13}
            if role=="anonymous":destination.update(response_status=303,authorization_denied=True,redirect_is_configured_login=True,identity=None)
            elif role=="Reader":destination.update(response_status=403,authorization_denied=True,identity=identities[role])
            else:destination.update(response_status=405,authorization_denied=False,current_form_verified=True,
                current_csrf_present=True,current_viewstate_present=True,identity=identities[role])
            proofs["RETIREMENT::ACTION-32::"+role]=destination
        return proofs

    def test_current_candidate_can_be_rechecked_while_prior_retirements_use_pinned_receipts(self):
        all_proofs=self.fixture()
        action32={key:value for key,value in all_proofs.items() if "::ACTION-32::" in key}
        h.validate_retirement_keys(action32)
        subset={key:value for key,value in all_proofs.items() if "::ACTION-32::" in key or "::ACTION-08::" in key}
        h.validate_retirement_keys(subset)
        subset.pop("RETIREMENT::ACTION-32::Administrator")
        with self.assertRaises(AssertionError):h.validate_retirement_keys(subset)
        action32.pop("RETIREMENT::ACTION-32::Administrator")
        with self.assertRaises(AssertionError):h.validate_retirement_keys(action32)

    def test_current_roles_and_anonymous_proof_validate_for_both_retirements(self):
        h.validate_retirement_keys(self.fixture())

    def test_action32_uses_exact_rendered_destination_next_and_denies_all_actors(self):
        h.validate_retirement_keys(self.fixture())
        for role,field,value in [("Operator","historical_source_component_id","j_idt29:j_idt36"),
                                 ("Administrator","historical_submitted_parameter","j_idt29:j_idt36"),
                                 ("Reader","response_status",405),("anonymous","redirect_is_configured_login",False),
                                 ("Operator","current_csrf_present",False),("Administrator","current_viewstate_present",False)]:
            proofs=self.fixture();proofs["RETIREMENT::ACTION-32::"+role][field]=value
            with self.subTest(role=role,field=field),self.assertRaises(AssertionError):h.validate_retirement_keys(proofs)

    def test_handling_page_retirement_binds_both_controls_to_role_denial_and_replacement(self):
        evidence=h.handling_page_retirement_evidence();proofs={}
        for action,source in evidence["actions"].items():
            for role in ("anonymous","Reader","Operator","Administrator"):
                status={"anonymous":303,"Reader":403,"Operator":303,"Administrator":303}[role]
                target="/login" if role=="anonymous" else "/mobile.xhtml" if role in {"Operator","Administrator"} else None
                identity=None if role=="anonymous" else {"server_verified":True,"principal":{"Reader":"reader","Operator":"operator","Administrator":"admin"}[role],"roles":[role]}
                proofs["RETIREMENT::"+action+"::"+role]={"driver":"browser-retired-handling-page-v1","legacy_id":action,"actor":role,"method":"GET",
                    "source_path":"/cargo-tracker/eventLogger/eventLogger.xhtml","legacy_outcome":source["outcome"],
                    "legacy_control_sha256":source["legacy_control_sha256"],"source_hashes":evidence["source_hashes"],
                    "source_control_identity_verified":True,"candidate_legacy_page_redirect_verified":True,
                    "response_status":status,"redirect_target":target,"application_origin":"http://candidate:8080",
                    "application_context_path":"/cargo-tracker","redirect_location":None if role=="Reader" else "/cargo-tracker"+target,
                    "authorization_denied":role in {"anonymous","Reader"},
                    "redirect_is_configured_login":role=="anonymous","protected_payload_absent":True,"independent_effects_unchanged":True,
                    "replacement_served":role in {"Operator","Administrator"},"legacy_controls_absent":role in {"Operator","Administrator"},
                    **({"identity":identity} if identity else {})}
        h.validate_retirement_keys(proofs)
        for action in evidence["actions"]:
            for role,field,value in [("anonymous","redirect_is_configured_login",False),("Reader","response_status",303),
                                     ("Operator","legacy_controls_absent",False),("Administrator","source_hashes",{}),
                                     ("anonymous","redirect_location","https://attacker.example/cargo-tracker/login"),
                                     ("Operator","redirect_location","https://attacker.example/cargo-tracker/mobile.xhtml"),
                                     ("Administrator","redirect_location","/wrong-context/mobile.xhtml")]:
                changed=copy.deepcopy(proofs);changed["RETIREMENT::"+action+"::"+role][field]=value
                with self.subTest(action=action,role=role,field=field),self.assertRaises(AssertionError):h.validate_retirement_keys(changed)

    def test_action26_stale_deadline_requires_exact_denial_or_csrf_backed_method_rejection(self):
        h.validate_retirement_keys(self.fixture())
        for role,field,value in [("Operator","current_csrf_present",False),("Administrator","current_viewstate_present",False),
                                 ("Reader","response_status",405),("anonymous","redirect_is_configured_login",False)]:
            proofs=self.fixture();proofs["RETIREMENT::ACTION-26::"+role][field]=value
            with self.subTest(role=role,field=field),self.assertRaises(AssertionError):h.validate_retirement_keys(proofs)

    def test_action44_proof_requires_real_legacy_callback_and_removed_current_entry(self):
        for field,value in [("legacy_callback_implementation_verified",False),("current_callback_implementation_absent",False),
                            ("source_hashes",{}),("current_form_verified",False),("current_viewstate_present",False),("autocomplete_payload_absent",False),("cargo_snapshot_count",0)]:
            proofs=self.fixture();proofs["RETIREMENT::ACTION-44::Operator"][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):h.validate_retirement_keys(proofs)
    def test_action23_proof_rejects_missing_source_or_runtime_guards(self):
        for field,value in [("legacy_binding_discrepancy_verified",False),("source_hashes",{}),
                            ("post_target_verified",False),("callback_response_absent",False),("autocomplete_payload_absent",False),
                            ("cargo_snapshot_sha256","invalid"),("cargo_snapshot_count",0),
                            ("protected_payload_absent",False),("independent_effects_unchanged",False),
                            ("current_legacy_component_absent",False),("current_csrf_present",False),
                            ("current_viewstate_present",False),("response_status",500)]:
            proofs=self.fixture();proofs["RETIREMENT::ACTION-23::Operator"][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):h.validate_retirement_keys(proofs)
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

class CargoEntryProofTests(unittest.TestCase):
    def fixture(self):
        proofs={}
        actions={
            "ACTION-11":("admin/listNotRouted.xhtml","/cargo-tracker/admin/route.xhtml","NOT_ROUTED","route_choices_verified"),
            "ACTION-12":("admin/listNotRouted.xhtml","/cargo-tracker/admin/changeDestination.xhtml","NOT_ROUTED","editor_verified"),
            "ACTION-21":("admin/show.xhtml?trackingId=ABCDEFGH","/cargo-tracker/admin/route.xhtml","NOT_ROUTED","route_choices_verified"),
            "ACTION-22":("admin/show.xhtml?trackingId=ABCDEFGH","/cargo-tracker/admin/route.xhtml","ROUTED","route_choices_verified"),
        }
        for action,(source,target,state,detail) in actions.items():
            for role,user in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
                allowed=role in {"Operator","Administrator"}
                proof={"supported":True,"action_executed":True,"target_origin_verified":True,"tracking_id":"ABCDEFGH",
                       "query_keys":["trackingId"],"current_navigation_driver":"browser-cargo-entry-v1","actual_target_path":target,
                       "source_page":"index.xhtml" if user is None else source,"entry_state":state,
                       "status":200 if allowed else 303 if user is None else 403,"driver":"click" if allowed else "direct",
                       "semantic_success":allowed,"entry_chain_verified":True,"selected_cargo_verified":True,detail:True,
                       "source_access_verified":True,"source_controls_hidden":True,"protected_payload_absent":True,"redirect_is_configured_login":True}
                if user:proof["identity"]={"server_verified":True,"principal":user,"roles":[role]}
                proofs["CURRENT::"+action+"::"+role+"::active"]=proof
        return proofs
    def test_complete_cargo_entry_paths_promote_atomically(self):
        report={"current_access_observations":{}}
        proofs=self.fixture()
        h.promote_cargo_entry_actions(report,{"cargo_entry_actions":proofs})
        self.assertEqual(report["current_access_observations"],proofs)
    def test_wrong_cargo_state_source_and_incomplete_denials_are_rejected(self):
        cases=[
            ("ACTION-11","Operator","source_page","admin/dashboard.xhtml"),
            ("ACTION-12","Operator","editor_verified",False),
            ("ACTION-21","Operator","driver","direct"),
            ("ACTION-22","Administrator","entry_state","NOT_ROUTED"),
            ("ACTION-11","Reader","source_controls_hidden",False),
            ("ACTION-12","anonymous","redirect_is_configured_login",False),
        ]
        for action,role,key,value in cases:
            proofs=self.fixture();proofs["CURRENT::"+action+"::"+role+"::active"][key]=value
            report={"current_access_observations":{}}
            with self.subTest(action=action,key=key),self.assertRaises(AssertionError):
                h.promote_cargo_entry_actions(report,{"cargo_entry_actions":proofs})
            self.assertEqual(report,{"current_access_observations":{}})

class TrackingProofTests(unittest.TestCase):
    def fixture(self):
        proofs={}
        for action,source in [("ACTION-24","admin/track.xhtml"),("ACTION-45","public/track.xhtml"),("ACTION-25","admin/live.xhtml")]:
            lookup=action!="ACTION-25"
            public_lookup=action=="ACTION-45"
            for role,user in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
                allowed=bool(user) or public_lookup
                proof={"supported":True,"status":200 if allowed else 303,"tracking_id":"ABCDEFGH",
                       "current_navigation_driver":"browser-lookup-v1" if lookup else "browser-marker-v1",
                       "driver":("click" if lookup else "keyboard") if allowed else "direct",
                       "semantic_success":True,"selected_cargo_verified":True,"persisted_details_verified":True,
                       "protected_payload_absent":True,"redirect_is_configured_login":True}
                if user:proof["identity"]={"server_verified":True,"principal":user,"roles":[role]}
                if lookup:
                    proof.update(action_method="POST",action_path="/cargo-tracker/public/track.xhtml" if public_lookup else "/cargo-tracker/admin/track.xhtml",entry_page=source,
                                 source_entry_verified=True,submission_status=200 if public_lookup else 303,invalid_inputs_verified=True,csrf_checks_verified=not public_lookup,
                                 legacy_entry_verified=True,autocomplete_source_payload_absent=True,lookup_source_denied=True)
                else:
                    proof.update(action_executed=True,target_origin_verified=True,actual_target_path="/cargo-tracker/admin/show.xhtml",
                                 query_keys=["trackingId"],source_page=source if user else "index.xhtml",
                                 live_marker_verified=True,live_source_denied=True)
                proofs["CURRENT::"+action+"::"+role+"::active"]=proof
        return proofs
    def test_lookup_and_marker_promote_complete_current_only_group(self):
        report={"current_access_observations":{}}
        proofs=self.fixture()
        h.promote_tracking_actions(report,{"tracking_actions":proofs})
        self.assertEqual(report["current_access_observations"],proofs)
    def test_tracking_transport_source_and_results_remain_required(self):
        for action,role,key,value in [
            ("ACTION-24","Reader","action_method","GET"),
            ("ACTION-45","Reader","entry_page","admin/track.xhtml"),
            ("ACTION-45","Reader","legacy_entry_verified",False),
            ("ACTION-45","anonymous","autocomplete_source_payload_absent",False),
            ("ACTION-45","Reader","action_path","/cargo-tracker/admin/track.xhtml"),
            ("ACTION-24","Reader","invalid_inputs_verified",False),
            ("ACTION-24","Reader","csrf_checks_verified",False),
            ("ACTION-25","Reader","actual_target_path","/other"),
            ("ACTION-25","Reader","query_keys",["trackingId","trackingId"]),
            ("ACTION-25","anonymous","live_source_denied",False),
        ]:
            proofs=self.fixture();proofs["CURRENT::"+action+"::"+role+"::active"][key]=value
            report={"current_access_observations":{}}
            with self.subTest(action=action,key=key),self.assertRaises(AssertionError):
                h.promote_tracking_actions(report,{"tracking_actions":proofs})
            self.assertEqual(report,{"current_access_observations":{}})

if __name__=="__main__":unittest.main()
