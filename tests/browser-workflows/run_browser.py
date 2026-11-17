#!/usr/bin/env python3
"""Owned app + Chromium fixture; no shared services, no browser credential persistence."""
from pathlib import Path
import importlib.util,json,re,subprocess,time,uuid,hashlib,os
ROOT=Path(__file__).resolve().parents[2]
LIVE_RUN_ID=os.environ.get("AI_MODERNIZATION_LIVE_RUN_ID","")
if LIVE_RUN_ID and not re.fullmatch(r"kan15-[a-z0-9-]{1,40}",LIVE_RUN_ID):
    raise ValueError("Invalid AI modernization live-run identifier")
WORK=(ROOT/".work"/LIVE_RUN_ID/"browser") if LIVE_RUN_ID else ROOT/".work/kan19"
BROWSER_IMAGE=("ai-modernization-"+LIVE_RUN_ID+":browser") if LIVE_RUN_ID else "ai-modernization-kan19:browser"
handling_capture_spec=importlib.util.spec_from_file_location("handling_retirement_evidence",ROOT/"tests/security/handling_retirement_evidence.py")
handling_capture=importlib.util.module_from_spec(handling_capture_spec);handling_capture_spec.loader.exec_module(handling_capture)
redirect_spec=importlib.util.spec_from_file_location("handling_page_redirects",ROOT/"tests/security/handling_page_redirects.py")
redirects=importlib.util.module_from_spec(redirect_spec);redirect_spec.loader.exec_module(redirects)
spec=importlib.util.spec_from_file_location("candidate_runtime",ROOT/"tests/candidate-runtime/run_candidate.py")
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
bridge_spec=importlib.util.spec_from_file_location("effects_bridge",Path(__file__).with_name("effects_bridge.py"))
bridge=importlib.util.module_from_spec(bridge_spec)
bridge_spec.loader.exec_module(bridge)

def promote_live_pages(report,results):
    proofs=results.get("page_semantics",{})
    role_users={"Reader":"reader","Operator":"operator","Administrator":"admin"}
    expected={surface+"::"+role+"::active":(role,user,path) for surface,path in [("PAGE-09","/admin/map.xhtml"),("PAGE-10","/admin/mapFrame.html")] for role,user in role_users.items()}
    if set(proofs)!=set(expected):raise AssertionError("Missing or unexpected live-page browser proof")
    observations=report.get("access_observations",{});validated=[]
    for key,(role,user,path) in expected.items():
        proof=proofs[key];observation=observations.get(key,{})
        identity=observation.get("identity",{})
        if not (observation.get("browser_required") is True and observation.get("shell_rendered") is True and identity.get("server_verified") is True and identity.get("principal")==user and role in identity.get("roles",[]) and proof.get("principal")==user and role in proof.get("roles",[]) and proof.get("source_path")==path and proof.get("final_path")=="/cargo-tracker/admin/live.xhtml" and proof.get("status")==200 and proof.get("cargo_observed")=="ABC123" and proof.get("socket_live") is True):raise AssertionError("Invalid live-page browser proof")
        validated.append(observation)
    for observation in validated:observation.update({"supported":True,"semantic_success":True,"browser_semantics_verified":True})
    report["browser_page_proofs"]=proofs

def promote_socket_cases(report,results):
    proofs=results.get("socket_observations",{})
    expected={"WS-01::anonymous::active":("anonymous","active")}
    for role in ["Reader","Operator","Administrator"]:
        for state in ["active","logged_out","expired"]:expected["WS-01::"+role+"::"+state]=(role,state)
        expected["WS-ORIGIN::"+role+"::active"]=(role,"origin")
    if set(proofs)!=set(expected):raise AssertionError("Missing or unexpected socket observation")
    users={"Reader":"reader","Operator":"operator","Administrator":"admin"}
    for case,(role,state) in expected.items():
        proof=proofs[case]
        if proof.get("supported") is not True:raise AssertionError("Unsupported socket observation")
        if role!="anonymous":
            identity=proof.get("identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!=users[role] or role not in identity.get("roles",[]):raise AssertionError("Invalid native socket identity")
        if state=="active" and role!="anonymous":
            if proof.get("status")!=101 or proof.get("socket_open_observed") is not True or proof.get("semantic_success") is not True or proof.get("authorized_frame_received") is not True:raise AssertionError("Missing actual socket delivery")
        else:
            if proof.get("status")!=(403 if state=="origin" else 401) or proof.get("upgraded") is not False or proof.get("protected_payload_absent") is not True:raise AssertionError("Invalid socket denial")
            if state in {"logged_out","expired"} and not (proof.get("authenticated_before_revocation") is True and proof.get("revocation_verified") is True and proof.get("existing_socket_closed") is True and proof.get("post_revocation_frame_received") is False and proof.get("stale_cookie_replay_verified") is True):raise AssertionError("Incomplete socket revocation evidence")
    report["access_observations"].update(proofs)
    report["socket_contract_observations"]=proofs

def promote_navigation_actions(report,results):
    mapping=json.loads((ROOT/"tests/browser-workflows/navigation-actions.json").read_text())
    expected={row["id"]+"::"+role+"::active":(row,role) for row in mapping for role in ["anonymous","Reader","Operator","Administrator"]}
    proofs=results.get("navigation_actions",{})
    if len(mapping)!=7 or len(expected)!=28 or set(proofs)!=set(expected):raise AssertionError("Missing or unexpected navigation action proof")
    users={"Reader":"reader","Operator":"operator","Administrator":"admin"}
    for key,(row,role) in expected.items():
        proof=proofs[key];allowed=row["anonymous"] if role=="anonymous" else role in row["allowed_roles"]
        source="index.xhtml" if role=="anonymous" and not row["anonymous"] else row["source_page"]
        direct=not allowed and (row["id"] in {"ACTION-02","ACTION-05","ACTION-14"})
        if not (proof.get("supported") is True and proof.get("action_executed") is True and proof.get("target")==row["target"] and proof.get("source_page")==source and proof.get("driver")==("direct" if direct else "click")):raise AssertionError("Invalid navigation action driver")
        keys=proof.get("query_keys")
        detail=row["kind"]=="routed-detail"
        allowed_keys=[["trackingId"],["jfwid","trackingId"]] if detail else [[],["jfwid"]]
        if proof.get("target_origin_verified") is not True or proof.get("actual_target_path")!="/cargo-tracker/"+row["target"].split("?")[0] or not isinstance(keys,list) or sorted(keys) not in allowed_keys or proof.get("tracking_id")!=("ABC123" if detail else None):raise AssertionError("Unexpected navigation response URL")
        if direct and proof.get("control_hidden") is not True:raise AssertionError("Forbidden navigation control was exposed")
        if role!="anonymous":
            identity=proof.get("identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!=users[role] or role not in identity.get("roles",[]):raise AssertionError("Invalid native navigation identity")
        if allowed:
            if proof.get("status")!=200 or proof.get("semantic_success") is not True:raise AssertionError("Missing navigation destination semantics")
            if row["kind"] in {"list","live"} and proof.get("cargo_observed")!="ABC123":raise AssertionError("Missing actual cargo after navigation")
            if row["kind"]=="live" and proof.get("socket_live") is not True:raise AssertionError("Missing live navigation transport")
            if detail and not (proof.get("cargo_observed")=="ABC123" and proof.get("routing_status")=="ROUTED" and proof.get("transport_status") in {"NOT_RECEIVED","IN_PORT","ONBOARD_CARRIER"}):raise AssertionError("Missing routed-list details")
            if row["kind"] in {"booking","lookup"} and proof.get("form_observed") is not True:raise AssertionError("Missing navigation form")
            if role=="anonymous" and proof.get("protected_payload_absent") is not True:raise AssertionError("Public navigation leakage unchecked")
        elif proof.get("status")!=(303 if role=="anonymous" else 403) or proof.get("protected_payload_absent") is not True or role=="anonymous" and proof.get("redirect_is_configured_login") is not True:raise AssertionError("Invalid navigation denial")
    report["access_observations"].update(proofs)
    report["navigation_action_observations"]=proofs

def promote_claimed_cargo_actions(report,results):
    proofs=results.get("claimed_cargo_actions",{})
    roles={"anonymous":None,"Reader":"reader","Operator":"operator","Administrator":"admin"}
    expected={"CURRENT::ACTION-10::"+role+"::active":role for role in roles}
    if set(proofs)!=set(expected):raise AssertionError("Missing or unexpected claimed cargo proof")
    ids=set()
    for key,role in expected.items():
        proof=proofs[key]
        tracking=proof.get("tracking_id")
        if not isinstance(tracking,str) or re.fullmatch("[A-Z0-9]{8}",tracking) is None:
            raise AssertionError("Invalid claimed cargo ID")
        ids.add(tracking)
        if proof.get("current_navigation_driver")!="browser-claimed-cargo-v1" or proof.get("supported") is not True or proof.get("action_executed") is not True or proof.get("target_origin_verified") is not True or proof.get("actual_target_path")!="/cargo-tracker/admin/show.xhtml" or sorted(proof.get("query_keys",[])) not in (["trackingId"],["jfwid","trackingId"]):
            raise AssertionError("Invalid claimed cargo navigation")
        if role=="anonymous":
            if proof.get("identity") is not None or (proof.get("source_page"),proof.get("driver"),proof.get("status"))!=("index.xhtml","direct",303) or not all(proof.get(name) is True for name in ("protected_payload_absent","redirect_is_configured_login","claimed_list_denied")):
                raise AssertionError("Invalid claimed cargo denial")
        else:
            identity=proof.get("identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!=roles[role] or identity.get("roles")!=[role] or (proof.get("source_page"),proof.get("driver"),proof.get("status"))!=("admin/listClaimed.xhtml","click",200) or not all(proof.get(name) is True for name in ("semantic_success","selected_cargo_verified","persisted_details_verified")):
                raise AssertionError("Invalid claimed cargo details")
    if len(ids)!=1:raise AssertionError("Claimed cargo proofs use different fixtures")
    report["current_access_observations"].update(proofs)


CARGO_ENTRY_ACTIONS={
    "ACTION-11":("admin/listNotRouted.xhtml","/cargo-tracker/admin/route.xhtml","NOT_ROUTED","route_choices_verified"),
    "ACTION-12":("admin/listNotRouted.xhtml","/cargo-tracker/admin/changeDestination.xhtml","NOT_ROUTED","editor_verified"),
    "ACTION-21":("admin/show.xhtml","/cargo-tracker/admin/route.xhtml","NOT_ROUTED","route_choices_verified"),
    "ACTION-22":("admin/show.xhtml","/cargo-tracker/admin/route.xhtml","ROUTED","route_choices_verified"),
}
def promote_cargo_entry_actions(report,results):
    proofs=results.get("cargo_entry_actions",{})
    expected={"CURRENT::"+action+"::"+role+"::active":(action,role) for action in CARGO_ENTRY_ACTIONS for role in ("anonymous","Reader","Operator","Administrator")}
    if set(proofs)!=set(expected):raise AssertionError("Missing or unexpected cargo entry proof")
    for key,(action,role) in expected.items():
        proof=proofs[key]
        source,target,state,detail=CARGO_ENTRY_ACTIONS[action]
        tracking=proof.get("tracking_id")
        if not isinstance(tracking,str) or re.fullmatch("[A-Z0-9]{8}",tracking) is None:raise AssertionError("Invalid cargo entry ID")
        if source=="admin/show.xhtml":source+="?trackingId="+tracking
        if role=="anonymous":source="index.xhtml"
        allowed=role in {"Operator","Administrator"}
        if proof.get("current_navigation_driver")!="browser-cargo-entry-v1" or not all(proof.get(k) is True for k in ("supported","action_executed","target_origin_verified")) or proof.get("actual_target_path")!=target or proof.get("source_page")!=source or proof.get("entry_state")!=state or sorted(proof.get("query_keys",[])) not in (["trackingId"],["jfwid","trackingId"]):
            raise AssertionError("Cargo entry path/state mismatch")
        if role!="anonymous":
            identity=proof.get("identity",{})
            user={"Reader":"reader","Operator":"operator","Administrator":"admin"}[role]
            if identity.get("server_verified") is not True or identity.get("principal")!=user or identity.get("roles")!=[role]:raise AssertionError("Cargo entry identity mismatch")
        elif proof.get("identity") is not None:raise AssertionError("Anonymous cargo entry has identity")
        if allowed:
            if proof.get("status")!=200 or proof.get("driver")!="click" or not all(proof.get(k) is True for k in ("semantic_success","entry_chain_verified","selected_cargo_verified",detail)):raise AssertionError("Cargo entry click lacks evidence")
        else:
            if proof.get("status")!=(303 if role=="anonymous" else 403) or proof.get("driver")!="direct" or not all(proof.get(k) is True for k in ("source_access_verified","source_controls_hidden","protected_payload_absent")) or role=="anonymous" and proof.get("redirect_is_configured_login") is not True:raise AssertionError("Cargo entry denial lacks evidence")
    report["current_access_observations"].update(proofs)


def promote_tracking_actions(report,results):
    proofs=results.get("tracking_actions",{})
    actions={"ACTION-24":"admin/track.xhtml","ACTION-45":"public/track.xhtml","ACTION-25":"admin/live.xhtml"}
    expected={"CURRENT::"+action+"::"+role+"::active":(action,role) for action in actions for role in ("anonymous","Reader","Operator","Administrator")}
    if set(proofs)!=set(expected):raise AssertionError("Missing tracking proof")
    ids=set()
    for key,(action,role) in expected.items():
        proof=proofs[key]
        tracking=proof.get("tracking_id")
        if not isinstance(tracking,str) or re.fullmatch("[A-Z0-9]{8}",tracking) is None:raise AssertionError("Invalid tracked cargo")
        ids.add(tracking)
        lookup=action!="ACTION-25"
        public_lookup=action=="ACTION-45"
        allowed=role!="anonymous" or public_lookup
        if proof.get("supported") is not True or proof.get("current_navigation_driver")!=("browser-lookup-v1" if lookup else "browser-marker-v1"):raise AssertionError("Unknown tracking driver")
        if allowed:
            if role!="anonymous":
                identity=proof.get("identity",{})
                if identity.get("server_verified") is not True or identity.get("principal")!={"Reader":"reader","Operator":"operator","Administrator":"admin"}[role] or identity.get("roles")!=[role]:raise AssertionError("Tracking identity mismatch")
            elif proof.get("identity") is not None:raise AssertionError("Public anonymous lookup has an identity")
            if proof.get("status")!=200 or proof.get("driver")!=("click" if lookup else "keyboard") or not all(proof.get(k) is True for k in ("semantic_success","selected_cargo_verified","persisted_details_verified")):raise AssertionError("Tracking result lacks details")
            if public_lookup and proof.get("protected_payload_absent") is not True:raise AssertionError("Public tracking exposed unrelated cargo data")
        elif proof.get("identity") is not None or proof.get("status")!=303 or proof.get("driver")!="direct" or not all(proof.get(k) is True for k in ("protected_payload_absent","redirect_is_configured_login")):raise AssertionError("Tracking denial incomplete")
        if lookup:
            expected_path="/cargo-tracker/public/track.xhtml" if public_lookup else "/cargo-tracker/admin/track.xhtml"
            if (proof.get("action_method"),proof.get("action_path"),proof.get("entry_page"))!=("POST",expected_path,actions[action]) or proof.get("source_entry_verified") is not True:raise AssertionError("Lookup POST/source mismatch")
            if allowed and public_lookup:
                if proof.get("submission_status")!=200 or proof.get("invalid_inputs_verified") is not True or proof.get("legacy_entry_verified") is not True or proof.get("autocomplete_source_payload_absent") is not True or proof.get("persisted_details_verified") is not True:raise AssertionError("Public typed lookup or retired autocomplete evidence incomplete")
            elif allowed:
                if proof.get("submission_status") not in {302,303} or proof.get("invalid_inputs_verified") is not True or proof.get("csrf_checks_verified") is not True:raise AssertionError("Lookup form evidence incomplete")
            elif proof.get("lookup_source_denied") is not True:raise AssertionError("Lookup source denial missing")
        else:
            if not all(proof.get(k) is True for k in ("action_executed","target_origin_verified")) or proof.get("actual_target_path")!="/cargo-tracker/admin/show.xhtml" or sorted(proof.get("query_keys",[])) not in (["trackingId"],["jfwid","trackingId"]) or proof.get("source_page")!=("admin/live.xhtml" if allowed else "index.xhtml"):raise AssertionError("Marker target mismatch")
            if proof.get("live_marker_verified" if allowed else "live_source_denied") is not True:raise AssertionError("Marker entry incomplete")
    if len(ids)!=1:raise AssertionError("Tracking proofs use different fixtures")
    report["current_access_observations"].update(proofs)


REPLACEMENT_GROUPS=(
    "cancel-editor","booking-cancel","tracking-discovery","booking-deadline","booking-single-page",
    "handling-single-page","handling-cargo-voyage","handling-location","handling-event","handling-voyage",
    "handling-completion",
)
REPLACEMENT_ROLES=("anonymous","Reader","Operator","Administrator")

def expected_replacement_keys():
    return {"REPLACEMENT::"+group+"::"+role for group in REPLACEMENT_GROUPS for role in REPLACEMENT_ROLES}

def validate_replacement_keys(proofs):
    if set(proofs)!=expected_replacement_keys():
        raise AssertionError("Missing or unexpected replacement observations")

def validate_handling_csrf_proofs(proofs):
    roles=("Operator","Administrator")
    if set(proofs)!=set(roles):
        raise AssertionError("Missing or unexpected handling CSRF observations")
    for role in roles:
        proof=proofs[role]
        if (proof.get("source_path")!="/cargo-tracker/mobile.xhtml" or proof.get("actor")!=role
                or not all(proof.get(name) is True for name in
                    ("valid_submission_form","current_csrf_present","current_csrf_nonempty","submit_marker_present",
                     "wrong_token_distinct","protected_payload_absent","independent_effects_unchanged"))
                or proof.get("response_status")!=403
                or proof.get("identity",{}).get("server_verified") is not True
                or proof.get("identity",{}).get("principal")!={"Operator":"operator","Administrator":"admin"}[role]
                or proof.get("identity",{}).get("roles")!=[role]):
            raise AssertionError("Invalid wrong-CSRF handling proof for "+role)
        before,after=proof.get("before",{}),proof.get("after",{})
        if (before.get("fixture_id")!=after.get("fixture_id")
                or before.get("stage")!="handling-wrong-csrf:"+role+":before"
                or after.get("stage")!="handling-wrong-csrf:"+role+":after"
                or not before.get("tables") or before.get("tables")!=after.get("tables")
                or not before.get("queues") or before.get("queues")!=after.get("queues")
                or not before.get("business_invocations") or before.get("business_invocations")!=after.get("business_invocations")):
            raise AssertionError("Wrong-CSRF handling effects changed or are incomplete for "+role)


def validate_handling_callback_retirements(observations,source_evidence):
    roles=("anonymous","Reader","Operator","Administrator")
    actions=("ACTION-36","ACTION-37","ACTION-38","ACTION-39","ACTION-42")
    if set(observations)!=set(roles):
        raise AssertionError("Missing or unexpected handling callback actor proofs")
    expected_page_status={"anonymous":303,"Reader":403,"Operator":200,"Administrator":200}
    expected_get_status={"anonymous":303,"Reader":403,"Operator":303,"Administrator":303}
    expected_post_status={"anonymous":303,"Reader":403,"Operator":405,"Administrator":405}
    expanded={}
    for role in roles:
        proof=observations[role]
        identity=proof.get("identity")
        if (proof.get("actor")!=role or proof.get("source_path")!="/cargo-tracker/eventLogger/eventLogger.xhtml"
                or proof.get("current_page_status")!=expected_page_status[role]
                or proof.get("legacy_get_status")!=expected_get_status[role]
                or proof.get("legacy_get_redirect_valid") is not True
                or proof.get("independent_effects_unchanged") is not True
                or len(proof.get("callbacks",[]))!=len(actions)):
            raise AssertionError("Invalid handling callback actor proof for "+role)
        if role=="anonymous":
            if identity is not None or proof.get("current_csrf_present") is not False:
                raise AssertionError("Anonymous handling callback proof contains an identity or CSRF session")
        else:
            expected_identity={"Reader":("reader",["Reader"]),"Operator":("operator",["Operator"]),"Administrator":("admin",["Administrator"])}[role]
            if identity!={"server_verified":True,"principal":expected_identity[0],"roles":expected_identity[1]}:
                raise AssertionError("Handling callback proof lacks server-verified actor identity for "+role)
            if proof.get("current_csrf_present") is not True:
                raise AssertionError("Authenticated callback proof lacks current candidate CSRF state for "+role)
        allowed=role in {"Operator","Administrator"}
        if proof.get("current_mobile_form_verified") is not allowed:
            raise AssertionError("Handling callback proof has incomplete current form evidence for "+role)
        viewstate_parameter=proof.get("current_viewstate_parameter")
        if allowed:
            if (not isinstance(viewstate_parameter,str) or not viewstate_parameter.startswith("jakarta.faces.ViewState")
                    or proof.get("current_viewstate_present") is not True):
                raise AssertionError("Permitted callback proof lacks current candidate ViewState for "+role)
        elif viewstate_parameter!="" or proof.get("current_viewstate_present") is not False:
            raise AssertionError("Denied callback proof unexpectedly contains current candidate ViewState for "+role)
        before,after=proof.get("before",{}),proof.get("after",{})
        if (before.get("fixture_id")!=after.get("fixture_id")
                or before.get("stage")!="handling-retired-callback:"+role+":before"
                or after.get("stage")!="handling-retired-callback:"+role+":after"
                or not before.get("tables") or before.get("tables")!=after.get("tables")
                or not before.get("queues") or before.get("queues")!=after.get("queues")
                or not before.get("business_invocations") or before.get("business_invocations")!=after.get("business_invocations")):
            raise AssertionError("Handling callback denial changed or incompletely observed effects for "+role)
        rows=proof.get("callbacks",[])
        by_id={row.get("legacy_id"):row for row in rows if isinstance(row,dict)}
        if set(by_id)!=set(actions) or len(rows)!=len(actions):
            raise AssertionError("Handling callback proof does not bind all exact legacy actions for "+role)
        for action in actions:
            observed=by_id[action]
            rendered=source_evidence["actions"][action]
            if (observed.get("source_component_id")!=rendered["source_component_id"]
                    or observed.get("behavior_event")!=rendered["behavior_event"]
                    or observed.get("partial_event")!=rendered["partial_event"]
                    or observed.get("execute")!=rendered["execute"]
                    or observed.get("render")!=rendered["render"]
                    or observed.get("callback_input_name")!=rendered["callback_input_name"]
                    or observed.get("submitted_callback_value")!=rendered["selected_value"]
                    or observed.get("source_parameter_names")!=rendered["parameter_names"]
                    or not set(rendered["parameter_names"]).issubset(set(observed.get("submitted_parameter_names",[])))
                    or observed.get("submitted_shape_matches") is not True
                    or observed.get("legacy_dynamic_fields_substituted") is not True
                    or observed.get("candidate_csrf_submitted") is not allowed
                    or observed.get("candidate_viewstate_submitted") is not allowed
                    or observed.get("submitted_content_type")!=rendered["content_type"]
                    or observed.get("submitted_faces_request")!=rendered["faces_request"]
                    or observed.get("exact_raw_legacy_replay") is not False
                    or observed.get("replay_kind")!="sanitized-rendered-callback-shape"
                    or observed.get("response_status")!=expected_post_status[role]
                    or observed.get("post_target_verified") is not True
                    or observed.get("protected_payload_absent") is not True):
                raise AssertionError("Invalid rendered callback shape denial proof for "+action+" "+role)
            submitted=set(observed["submitted_parameter_names"])
            expected_names=set(rendered["parameter_names"])
            if allowed:
                expected_names.update(("csrf",viewstate_parameter))
            if submitted!=expected_names:
                raise AssertionError("Submitted callback parameter names differ from rendered shape for "+action+" "+role)
            denied=role in {"anonymous","Reader"}
            if observed.get("authorization_denied") is not denied:
                raise AssertionError("Handling callback authorization outcome changed for "+action+" "+role)
            if allowed and observed.get("callback_response_absent") is not True:
                raise AssertionError("Authorized legacy callback did not reach method refusal for "+action+" "+role)
            if role=="anonymous" and observed.get("redirect_is_configured_login") is not True:
                raise AssertionError("Anonymous legacy callback was not redirected to login")
            expanded["RETIREMENT::"+action+"::"+role]={
                "driver":"browser-rendered-handling-callback-shape-v1","legacy_id":action,"actor":role,"method":"POST",
                "source_path":proof["source_path"],"historical_source_component_id":rendered["source_component_id"],
                "historical_source_parameter":"javax.faces.source","behavior_event":rendered["behavior_event"],
                "historical_execute":rendered["execute"],"historical_render":rendered["render"],
                "historical_render_evidence_verified":True,"source_capture_sha256":source_evidence["capture_sha256"],
                "source_hashes":source_evidence["source_hashes"],"legacy_parameter_names":rendered["parameter_names"],
                "submitted_parameter_names":observed["submitted_parameter_names"],
                "historical_callback_input_name":rendered["callback_input_name"],
                "submitted_callback_value":observed["submitted_callback_value"],
                "rendered_callback_shape_verified":True,"exact_raw_legacy_replay":False,
                "dynamic_legacy_state_redacted":observed["legacy_dynamic_fields_substituted"],
                "candidate_viewstate_parameter":viewstate_parameter or None,
                "candidate_viewstate_present":proof["current_viewstate_present"],
                "candidate_viewstate_submitted":observed["candidate_viewstate_submitted"],
                "candidate_csrf_present":proof["current_csrf_present"],
                "candidate_csrf_submitted":observed["candidate_csrf_submitted"],
                "response_status":observed["response_status"],"post_target_verified":observed["post_target_verified"],
                "authorization_denied":observed["authorization_denied"],
                "callback_response_absent":observed["callback_response_absent"],
                "protected_payload_absent":observed["protected_payload_absent"],
                "redirect_is_configured_login":observed["redirect_is_configured_login"],
                "independent_effects_unchanged":proof["independent_effects_unchanged"],
                "current_form_verified":proof["current_mobile_form_verified"],"identity":identity,
                "before":before,"after":after
            }
    return expanded

def action23_source_evidence():
    legacy_page=ROOT/"experiments/legacy-cargotracker/src/main/webapp/admin/track.xhtml"
    legacy_bean=ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java"
    candidate_page=ROOT/"candidate/cargotracker/src/main/webapp/admin/track.xhtml"
    candidate_bean=ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/CargoPages.java"
    public_page=ROOT/"experiments/legacy-cargotracker/src/main/webapp/public/track.xhtml"
    files={"legacy_admin_page_sha256":legacy_page,"legacy_track_bean_sha256":legacy_bean,
           "candidate_admin_page_sha256":candidate_page,"candidate_cargo_pages_sha256":candidate_bean,
           "legacy_public_page_sha256":public_page}
    raw={key:path.read_bytes() for key,path in files.items()}
    legacy_markup=raw["legacy_admin_page_sha256"].decode("utf-8")
    legacy_class=raw["legacy_track_bean_sha256"].decode("utf-8")
    current_markup=raw["candidate_admin_page_sha256"].decode("utf-8")
    current_class=raw["candidate_cargo_pages_sha256"].decode("utf-8")
    public_markup=raw["legacy_public_page_sha256"].decode("utf-8")
    if ("id=\"trackIdInput\"" not in legacy_markup or "completeMethod=\"#{track.completeTracking}\"" not in legacy_markup
            or re.search(r"\bpublic\s+[^;{]+\bcompleteTracking\s*\(",legacy_class)
            or not re.search(r"\bpublic\s+[^;{]+\bgetTrackingIds\s*\(",legacy_class)
            or 'completeMethod="#{track.getTrackingIds}"' not in public_markup or 'id="trackingId"' not in public_markup
            or "completeTracking" in current_markup or "trackIdInput" in current_markup or "p:autoComplete" in current_markup
            or "completeTracking" in current_class or 'id="id"' not in current_markup):
        raise AssertionError("ACTION-23 source/candidate callback discrepancy changed")
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}

def action44_source_evidence():
    legacy_page=ROOT/"experiments/legacy-cargotracker/src/main/webapp/public/track.xhtml"
    legacy_bean=ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java"
    candidate_page=ROOT/"candidate/cargotracker/src/main/webapp/public/track.xhtml"
    candidate_bean=ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java"
    files={"legacy_public_page_sha256":legacy_page,"legacy_track_bean_sha256":legacy_bean,
           "candidate_public_page_sha256":candidate_page,"candidate_track_bean_sha256":candidate_bean}
    raw={key:path.read_bytes() for key,path in files.items()}
    legacy_markup=raw["legacy_public_page_sha256"].decode("utf-8")
    legacy_class=raw["legacy_track_bean_sha256"].decode("utf-8")
    current_markup=raw["candidate_public_page_sha256"].decode("utf-8")
    current_class=raw["candidate_track_bean_sha256"].decode("utf-8")
    if ('id="trackingId"' not in legacy_markup or 'completeMethod="#{track.getTrackingIds}"' not in legacy_markup
            or not re.search(r"\bpublic\s+List<TrackingId>\s+getTrackingIds\s*\(\s*String\s+query\s*\)",legacy_class)
            or 'id="trackingId"' not in current_markup or "completeMethod" in current_markup
            or "p:autoComplete" in current_markup or "getTrackingIds" in current_markup
            or re.search(r"\bgetTrackingIds\s*\(",current_class)):
        raise AssertionError("ACTION-44 public autocomplete source/candidate callback discrepancy changed")
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}

def action26_source_evidence():
    legacy_page=ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml"
    legacy_bean=ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/domain/model/cargo/BookingBackingBean.java"
    candidate_page=ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml"
    navigation=ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java"
    routes=ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"
    paths={"legacy_booking_date_page_sha256":legacy_page,"legacy_booking_bean_sha256":legacy_bean,
           "candidate_booking_page_sha256":candidate_page,"legacy_navigation_servlet_sha256":navigation,
           "candidate_access_routes_sha256":routes}
    raw={key:path.read_bytes() for key,path in paths.items()}
    old_page=raw["legacy_booking_date_page_sha256"].decode("utf-8")
    old_bean=raw["legacy_booking_bean_sha256"].decode("utf-8")
    current=raw["candidate_booking_page_sha256"].decode("utf-8")
    servlet=raw["legacy_navigation_servlet_sha256"].decode("utf-8")
    access=raw["candidate_access_routes_sha256"].decode("utf-8")
    if ('id="deadline"' not in old_page or 'listener="#{bookingBackingBean.deadlineUpdated}"' not in old_page
            or not re.search(r"\bpublic\s+void\s+deadlineUpdated\s*\(\s*\)",old_bean)
            or 'id="deadline"' not in current or "deadlineUpdated" in current
            or '"/booking/booking-date.xhtml","/admin/book.xhtml"' not in servlet
            or "protected void doPost" in servlet or "/booking/booking-date.xhtml\tOperator,Administrator" not in access):
        raise AssertionError("ACTION-26 source/candidate boundary changed")
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}

def action32_render_evidence():
    evidence_path=ROOT/"notes/evidence/kan-15-action32-retirement/legacy-rendered-entry.json"
    record=json.loads(evidence_path.read_text())
    files={"legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    hashes={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in files.items()}
    obs=record.get("observation",{});markup=obs.get("button_markup","")
    if (record.get("task")!="KAN-15 ACTION-32 legacy rendered command identity"
            or record.get("source_hashes")!=hashes or obs.get("component_id")!="j_idt29:j_idt37"
            or obs.get("submitted_parameter")!="j_idt29:j_idt37" or obs.get("form_id")!="j_idt29"
            or obs.get("destination_view")!="/cargo-tracker/booking/booking-destination.xhtml"
            or obs.get("render_status")!=200 or obs.get("viewstate_flow_context_error") is not False
            or "<button id=\"j_idt29:j_idt37\"" not in markup or ">Next</span>" not in markup
            or hashlib.sha256(markup.encode()).hexdigest()!=obs.get("button_markup_sha256")):
        raise AssertionError("ACTION-32 rendered JSF component identity is not bound to current source bytes")
    old=files["legacy_booking_destination_page_sha256"].read_text()
    servlet=files["legacy_navigation_servlet_sha256"].read_text();routes=files["candidate_access_routes_sha256"].read_text()
    if ('<p:commandButton value="Next" action="booking-date" />' not in old
            or '"/booking/booking-destination.xhtml","/admin/book.xhtml"' not in servlet
            or "protected void doPost" in servlet or "/booking/booking-destination.xhtml\tOperator,Administrator" not in routes):
        raise AssertionError("ACTION-32 source/candidate POST boundary changed")
    return {"component_id":obs["component_id"],"button_markup_sha256":obs["button_markup_sha256"],"source_hashes":hashes}

def action273034_render_evidence():
    record_path=ROOT/"notes/evidence/kan-15-action273034-retirement/legacy-rendered-actions.json"
    record=json.loads(record_path.read_text())
    files={"legacy_booking_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking.xhtml",
           "legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
           "legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    hashes={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in files.items()}
    servlet=files["legacy_navigation_servlet_sha256"].read_text()
    routes=files["candidate_access_routes_sha256"].read_text()
    expected={"ACTION-27":("/cargo-tracker/booking/booking-date.xhtml","booking-destination","dateForm:j_idt37","dateForm"),
              "ACTION-30":("/cargo-tracker/booking/booking-destination.xhtml","booking","j_idt29:j_idt35","j_idt29"),
              "ACTION-34":("/cargo-tracker/booking/booking.xhtml","booking-destination","j_idt29:j_idt36","j_idt29")}
    if (record.get("task")!="KAN-15 ACTION-27/30/34 legacy rendered booking wizard action identities"
            or record.get("source_hashes")!=hashes or "protected void doPost" in servlet):
        raise AssertionError("ACTION-27/30/34 source evidence is stale or unsupported")
    actions={}
    for action,(source,expression,component,form) in expected.items():
        obs=record.get("observations",{}).get(action,{})
        page=files[{"ACTION-27":"legacy_booking_date_page_sha256","ACTION-30":"legacy_booking_destination_page_sha256","ACTION-34":"legacy_booking_page_sha256"}[action]].read_text()
        if (obs.get("source_path")!=source or obs.get("action_expression")!=expression
                or obs.get("component_id")!=component or obs.get("submitted_parameter")!=component
                or obs.get("form_id")!=form or obs.get("render_status")!=200 or obs.get("flow_post_status")!=200
                or not re.search(r'<p:commandButton[^>]*action="'+re.escape(expression)+r'"',page)
                or source.replace("/cargo-tracker","")+"\tOperator,Administrator" not in routes
                or '"'+source.replace("/cargo-tracker","")+'","/admin/book.xhtml"' not in servlet):
            raise AssertionError("ACTION-27/30/34 rendered component or protected route mismatch: "+action)
        actions[action]={"legacy_id":action,"source_path":source,"component_id":component,"form_id":form,
                         "button_markup_sha256":obs["button_markup_sha256"],"source_hashes":hashes}
    return {"actions":actions,"source_hashes":hashes}

def action283133_render_evidence():
    path=ROOT/"notes/evidence/kan-15-action283133-retirement/legacy-rendered-actions.json"
    record=json.loads(path.read_text())
    files={"legacy_booking_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking.xhtml",
           "legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
           "legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    hashes={key:hashlib.sha256(file.read_bytes()).hexdigest() for key,file in files.items()}
    servlet=files["legacy_navigation_servlet_sha256"].read_text()
    routes=files["candidate_access_routes_sha256"].read_text()
    expected={"ACTION-28":("/cargo-tracker/booking/booking-date.xhtml","dateForm:j_idt38","dateForm"),
              "ACTION-31":("/cargo-tracker/booking/booking-destination.xhtml","j_idt29:j_idt36","j_idt29"),
              "ACTION-33":("/cargo-tracker/booking/booking.xhtml","j_idt29:j_idt35","j_idt29")}
    if (record.get("task")!="KAN-15 ACTION-28/31/33 legacy rendered and executed booking cancel actions"
            or record.get("source_hashes")!=hashes or record.get("capture",{}).get("fixture_cleanup_verified") is not True
            or record.get("capture",{}).get("method") is None or "protected void doPost" in servlet):
        raise AssertionError("ACTION-28/31/33 rendered evidence is stale or unsupported")
    actions={}
    for action,(source,component,form) in expected.items():
        obs=record.get("observations",{}).get(action,{})
        page=files[{"ACTION-28":"legacy_booking_date_page_sha256","ACTION-31":"legacy_booking_destination_page_sha256","ACTION-33":"legacy_booking_page_sha256"}[action]].read_text()
        markup=obs.get("button_markup","")
        if (obs.get("source_path")!=source or obs.get("action_expression")!="/admin/dashboard"
                or obs.get("command_label")!="Cancel" or obs.get("component_id")!=component
                or obs.get("submitted_parameter")!=component or obs.get("form_id")!=form
                or obs.get("render_status")!=200 or obs.get("legacy_cancel_post_status")!=200
                or obs.get("cancel_result_path")!="/cargo-tracker/admin/dashboard.xhtml"
                or obs.get("cancel_returns_to_dashboard") is not True
                or hashlib.sha256(markup.encode()).hexdigest()!=obs.get("button_markup_sha256")
                or not re.search(r'<p:commandButton[^>]*value="Cancel"\s+action="/admin/dashboard"',page)
                or source.replace("/cargo-tracker","")+"\tOperator,Administrator" not in routes
                or '"'+source.replace("/cargo-tracker","")+'","/admin/book.xhtml"' not in servlet):
            raise AssertionError("ACTION-28/31/33 rendered Cancel source mismatch: "+action)
        actions[action]={"legacy_id":action,"source_path":source,"component_id":component,"form_id":form,
                         "button_markup_sha256":obs["button_markup_sha256"],"source_hashes":hashes}
    return {"actions":actions,"source_hashes":hashes}

def handling_page_retirement_evidence():
    paths={
      "legacy_event_logger_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/eventLogger/eventLogger.xhtml",
      "candidate_mobile_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/mobile.xhtml",
      "candidate_legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
      "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    raw={key:path.read_bytes() for key,path in paths.items()}
    legacy=raw["legacy_event_logger_page_sha256"].decode();current=raw["candidate_mobile_page_sha256"].decode()
    servlet=raw["candidate_legacy_navigation_servlet_sha256"].decode();routes=raw["candidate_access_routes_sha256"].decode()
    patterns={"ACTION-35":r'<p:button value="Next" id="nextBtn" outcome="pm:secondScreen\?transition=flip"[^>]*/>',
              "ACTION-40":r'<p:button value="Back" outcome="pm:firstScreen\?transition=flip"\s*/>'}
    actions={}
    for action,pattern in patterns.items():
        match=re.search(pattern,legacy)
        if not match:raise AssertionError("Missing source-bound legacy handling navigation control: "+action)
        actions[action]={"legacy_id":action,"source_component_id":"firstScreen:nextBtn" if action=="ACTION-35" else "secondScreen:back",
          "outcome":"pm:secondScreen?transition=flip" if action=="ACTION-35" else "pm:firstScreen?transition=flip",
          "legacy_control_sha256":hashlib.sha256(match.group(0).encode()).hexdigest()}
    if ('"/eventLogger/eventLogger.xhtml","/mobile.xhtml"' not in servlet
            or "/eventLogger/eventLogger.xhtml\tOperator,Administrator" not in routes
            or 'id="handling"' not in current or "Report handling" not in current or "Event Logger" in current
            or 'outcome="pm:secondScreen?transition=flip"' in current or 'outcome="pm:firstScreen?transition=flip"' in current):
        raise AssertionError("Candidate handling page is not a replacement for the protected legacy mobile flow")
    return {"actions":actions,"source_hashes":{key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}}

def expected_retirement_keys(legacy_ids=("ACTION-08","ACTION-23","ACTION-44","ACTION-26","ACTION-32")):
    return {"RETIREMENT::"+legacy_id+"::"+role for legacy_id in legacy_ids
            for role in ("anonymous","Reader","Operator","Administrator")}


def validate_retirement_keys(proofs):
    # A fresh run may focus on the candidate being reviewed. Previously approved
    # retirements stay governed by their separate hash-pinned review receipts.
    allowed={
        frozenset(expected_retirement_keys()),
        frozenset(expected_retirement_keys(("ACTION-32",))),
        frozenset(expected_retirement_keys(("ACTION-35","ACTION-40"))),
        frozenset(expected_retirement_keys(("ACTION-32","ACTION-08"))),
        frozenset(expected_retirement_keys(("ACTION-27","ACTION-30","ACTION-34"))),
        frozenset(expected_retirement_keys(("ACTION-27","ACTION-30","ACTION-34","ACTION-08"))),
        frozenset(expected_retirement_keys(("ACTION-27","ACTION-30","ACTION-34","ACTION-32"))),
        frozenset(expected_retirement_keys(("ACTION-28","ACTION-31","ACTION-33"))),
        frozenset(expected_retirement_keys(("ACTION-28","ACTION-31","ACTION-33","ACTION-08"))),
        frozenset(expected_retirement_keys(("ACTION-28","ACTION-31","ACTION-33","ACTION-27","ACTION-30","ACTION-34","ACTION-08"))),
        frozenset(expected_retirement_keys(("ACTION-28","ACTION-31","ACTION-33","ACTION-27","ACTION-30","ACTION-34"))),
    }
    handling_ids={"ACTION-35","ACTION-40"}
    handling_keys={"RETIREMENT::"+action+"::"+role for action in handling_ids for role in ("anonymous","Reader","Operator","Administrator")}
    non_handling={key for key in proofs if key.split("::")[1] not in handling_ids}
    if (frozenset(non_handling) not in allowed and not (not non_handling and set(proofs)==handling_keys)) or set(proofs)-non_handling not in (set(),handling_keys):
        raise AssertionError("Missing or unexpected retired-entry observations")
    handling_evidence=handling_page_retirement_evidence()
    for key in set(proofs)-non_handling:
        action,role=key.split("::")[1:];proof=proofs[key]
        observed=handling_evidence["actions"][action]
        expected_status={"anonymous":303,"Reader":403,"Operator":303,"Administrator":303}[role]
        expected_location="/login" if role=="anonymous" else "/mobile.xhtml" if role in {"Operator","Administrator"} else None
        identity=proof.get("identity") or {}
        if (proof.get("driver")!="browser-retired-handling-page-v1" or proof.get("method")!="GET"
                or proof.get("source_path")!="/cargo-tracker/eventLogger/eventLogger.xhtml"
                or proof.get("legacy_outcome")!=observed["outcome"]
                or proof.get("legacy_control_sha256")!=observed["legacy_control_sha256"]
                or proof.get("source_hashes")!=handling_evidence["source_hashes"]
                or proof.get("source_control_identity_verified") is not True
                or proof.get("candidate_legacy_page_redirect_verified") is not True
                or not redirects.is_safe_handling_redirect(proof,expected_location)
                or proof.get("response_status")!=expected_status
                or proof.get("redirect_target")!=expected_location
                or proof.get("protected_payload_absent") is not True
                or proof.get("independent_effects_unchanged") is not True):
            raise AssertionError("Handling legacy page denial/replacement proof is incomplete: "+key)
        if role=="anonymous":
            if identity or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True:raise AssertionError("Anonymous legacy handling access was not denied")
        elif role=="Reader":
            if proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("principal")!="reader" or identity.get("roles")!=["Reader"]:raise AssertionError("Reader legacy handling access was not denied")
        else:
            if (proof.get("authorization_denied") is not False or proof.get("replacement_served") is not True
                    or proof.get("legacy_controls_absent") is not True or identity.get("server_verified") is not True
                    or identity.get("principal")!={"Operator":"operator","Administrator":"admin"}[role] or identity.get("roles")!=[role]):raise AssertionError("Authorized legacy route did not reach the current handling replacement")
    source_hashes=action23_source_evidence()
    for key,proof in proofs.items():
        legacy_id,role=key.split("::")[1:]
        if proof.get("legacy_id")!=legacy_id or proof.get("actor")!=role or (proof.get("method")!="GET" if legacy_id in {"ACTION-35","ACTION-40"} else proof.get("method")!="POST") or proof.get("independent_effects_unchanged") is not True:
            raise AssertionError("Invalid retired-entry observation identity or effects proof")
        if legacy_id in {"ACTION-35","ACTION-40"}:
            continue
        if legacy_id=="ACTION-08":
            if proof.get("driver")!="browser-retired-action-v1" or proof.get("historical_source_component_id")!="j_idt8:j_idt23":
                raise AssertionError("Invalid ACTION-08 retired-entry driver")
            if proof.get("post_target_verified") is not True or proof.get("callback_implementation_absent") is not True:
                raise AssertionError("ACTION-08 replay lacks exact POST target or removed callback proof")
            if role in {"Operator","Administrator"}:
                if proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True or proof.get("current_viewstate_present") is not True or proof.get("callback_response_absent") is not True or proof.get("response_status") != 200 or proof.get("identity",{}).get("server_verified") is not True:
                    raise AssertionError("Authorized ACTION-08 replay lacks current-session denial proof")
            elif proof.get("authorization_denied") is not True or proof.get("protected_payload_absent") is not True or proof.get("response_status") != (403 if role=="Reader" else 303) or (role=="anonymous" and proof.get("redirect_is_configured_login") is not True):
                raise AssertionError("Unauthorized ACTION-08 replay lacks denial proof")
        elif legacy_id in {"ACTION-28","ACTION-31","ACTION-33"}:
            rendered=action283133_render_evidence()["actions"][legacy_id]
            if (proof.get("driver")!="browser-retired-booking-wizard-v1"
                    or proof.get("historical_source_component_id")!=rendered["component_id"]
                    or proof.get("historical_submitted_parameter")!=rendered["component_id"]
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=rendered["button_markup_sha256"]
                    or proof.get("source_path")!=rendered["source_path"]
                    or proof.get("source_hashes")!=rendered["source_hashes"]
                    or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):
                raise AssertionError(legacy_id+" rendered booking cancel proof is incomplete")
            if role=="anonymous":
                if proof.get("response_status")!=303 or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:
                    raise AssertionError(legacy_id+" anonymous stale cancel was not redirected to login")
            elif role=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("roles")!=["Reader"]:
                    raise AssertionError(legacy_id+" Reader stale cancel was not denied")
            else:
                identity=proof.get("identity",{})
                if proof.get("response_status")!=405 or proof.get("authorization_denied") is not False or not all(proof.get(name) is True for name in ("current_form_verified","current_csrf_present","current_viewstate_present")) or identity.get("server_verified") is not True:
                    raise AssertionError(legacy_id+" authorized stale cancel lacked inert-method proof")
        elif legacy_id in {"ACTION-27","ACTION-30","ACTION-34"}:
            rendered=action273034_render_evidence()["actions"][legacy_id]
            if (proof.get("driver")!="browser-retired-booking-wizard-v1"
                    or proof.get("historical_source_component_id")!=rendered["component_id"]
                    or proof.get("historical_submitted_parameter")!=rendered["component_id"]
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=rendered["button_markup_sha256"]
                    or proof.get("source_path")!=rendered["source_path"]
                    or proof.get("source_hashes")!=rendered["source_hashes"]
                    or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):
                raise AssertionError(legacy_id+" rendered booking wizard proof is incomplete")
            if role=="anonymous":
                if proof.get("response_status")!=303 or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:
                    raise AssertionError(legacy_id+" anonymous stale action was not redirected to login")
            elif role=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("roles")!=["Reader"]:
                    raise AssertionError(legacy_id+" Reader stale action was not denied")
            else:
                identity=proof.get("identity",{})
                if proof.get("response_status")!=405 or proof.get("authorization_denied") is not False or not all(proof.get(name) is True for name in ("current_form_verified","current_csrf_present","current_viewstate_present")) or identity.get("server_verified") is not True:
                    raise AssertionError(legacy_id+" authorized stale action lacked inert-method proof")
        elif legacy_id=="ACTION-32":
            rendered=action32_render_evidence()
            if (proof.get("driver")!="browser-retired-destination-next-v1" or proof.get("historical_source_component_id")!=rendered["component_id"]
                    or proof.get("historical_submitted_parameter")!=rendered["component_id"]
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=rendered["button_markup_sha256"]
                    or proof.get("source_path")!="/cargo-tracker/booking/booking-destination.xhtml"
                    or proof.get("source_hashes")!=rendered["source_hashes"] or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True or proof.get("callback_response_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("cargo_snapshot_count")!=13 or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):
                raise AssertionError("ACTION-32 rendered destination Next proof is incomplete")
            if role=="anonymous":
                if proof.get("response_status")!=303 or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:
                    raise AssertionError("ACTION-32 anonymous stale Next request was not redirected to login")
            elif role=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("roles")!=["Reader"]:
                    raise AssertionError("ACTION-32 Reader stale Next request was not denied")
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("current_form_verified") is not True
                        or proof.get("current_csrf_present") is not True or proof.get("current_viewstate_present") is not True
                        or proof.get("authorization_denied") is not False or identity.get("server_verified") is not True
                        or identity.get("roles")!=[role]):
                    raise AssertionError("ACTION-32 authorized stale Next request did not reach method rejection with current session CSRF")
        elif legacy_id=="ACTION-26":
            if (proof.get("driver")!="browser-retired-deadline-v1" or proof.get("historical_source_component_id")!="dateForm:deadline"
                    or proof.get("source_path")!="/cargo-tracker/booking/booking-date.xhtml"
                    or proof.get("source_hashes")!=action26_source_evidence() or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True or proof.get("callback_response_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("cargo_snapshot_count")!=13 or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):
                raise AssertionError("ACTION-26 stale deadline callback proof is incomplete")
            if role=="anonymous":
                if proof.get("response_status")!=303 or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:
                    raise AssertionError("ACTION-26 anonymous stale request was not redirected to login")
            elif role=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("roles")!=["Reader"]:
                    raise AssertionError("ACTION-26 Reader stale request was not denied")
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("current_form_verified") is not True
                        or proof.get("current_csrf_present") is not True or proof.get("current_viewstate_present") is not True
                        or proof.get("authorization_denied") is not False or identity.get("server_verified") is not True
                        or identity.get("roles")!=[role]):
                    raise AssertionError("ACTION-26 authorized stale request did not reach method rejection with valid session CSRF")
        else:
            if legacy_id=="ACTION-23":
                if (proof.get("driver")!="browser-retired-tracking-v1" or proof.get("historical_source_component_id")!="trackingForm:trackIdInput"
                        or proof.get("source_path")!="/cargo-tracker/admin/track.xhtml"
                        or proof.get("callback_implementation_absent") is not True
                        or proof.get("legacy_binding_discrepancy_verified") is not True
                        or proof.get("source_hashes")!=action23_source_evidence()):
                    raise AssertionError("ACTION-23 source binding is incomplete")
            else:
                if (proof.get("driver")!="browser-retired-public-tracking-v1" or proof.get("historical_source_component_id")!="trackingForm:trackingId"
                        or proof.get("source_path")!="/cargo-tracker/public/track.xhtml"
                        or proof.get("current_callback_implementation_absent") is not True
                        or proof.get("legacy_callback_implementation_verified") is not True
                        or proof.get("source_hashes")!=action44_source_evidence()):
                    raise AssertionError("ACTION-44 source binding is incomplete")
            if (proof.get("historical_source_parameter")!="javax.faces.source" or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True or proof.get("autocomplete_payload_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count",0)<1):
                raise AssertionError("Retired tracking callback response/snapshot proof is incomplete")
            if role=="anonymous" and legacy_id=="ACTION-23":
                if proof.get("response_status")!=303 or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:
                    raise AssertionError("ACTION-23 anonymous admin callback request was not denied")
            elif role=="anonymous":
                if (proof.get("response_status")!=200 or proof.get("authorization_denied") is not False
                        or proof.get("current_source_parameter") not in {"jakarta.faces.source","javax.faces.source"}
                        or proof.get("current_form_verified") is not True or proof.get("current_legacy_component_absent") is not True
                        or proof.get("current_callback_implementation_absent") is not True
                        or proof.get("current_viewstate_present") is not True
                        or proof.get("redirect_is_configured_login") is not False or proof.get("identity") is not None):
                    raise AssertionError("ACTION-44 anonymous public typed page lost access or stale callback remained active")
            else:
                identity=proof.get("identity",{});principal={"Reader":"reader","Operator":"operator","Administrator":"admin"}[role]
                if (proof.get("response_status")!=200 or proof.get("authorization_denied") is not False
                        or proof.get("current_source_parameter") not in {"jakarta.faces.source","javax.faces.source"}
                        or proof.get("current_form_verified") is not True or proof.get("current_legacy_component_absent") is not True
                        or (legacy_id=="ACTION-44" and proof.get("current_callback_implementation_absent") is not True)
                        or (legacy_id=="ACTION-23" and proof.get("current_csrf_present") is not True)
                        or proof.get("current_viewstate_present") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=principal or identity.get("roles")!=[role]):
                    raise AssertionError("Current role/session boundary proof is incomplete")
def main():
    WORK.mkdir(parents=True,exist_ok=True)
    handling_source_evidence=handling_capture.load_source_evidence()
    name=("ai-modernization-"+LIVE_RUN_ID+"-browser") if LIVE_RUN_ID else "ai-modernization-kan19-browser"
    if subprocess.run(["docker","inspect",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise RuntimeError("Browser container already exists")
    with (WORK/"browser-build.log").open("w") as log:
        build=subprocess.run(["docker","build","-t",BROWSER_IMAGE,str(ROOT/"tests/browser-workflows")],stdout=log,stderr=subprocess.STDOUT)
    if build.returncode:raise RuntimeError("Browser build failed")
    # Browser credentials travel over stdin to tmpfs, not env/argv/image or bind-mounted results.
    def browser(container,base,credentials,report):
        network=None;bid=None
        try:
            network=subprocess.check_output(["docker","network","create","--internal","ai-modernization-kan19-"+uuid.uuid4().hex[:12]],text=True).strip()
            subprocess.run(["docker","network","connect",network,container],check=True,capture_output=True)
            bid=subprocess.check_output(["docker","create","--name",name,"--init","--network",network,"--shm-size=512m","--tmpfs","/run:rw,noexec,nosuid,size=1m","--tmpfs","/out:rw,noexec,nosuid,size=8m","-i",BROWSER_IMAGE,"sleep","infinity"],text=True).strip()
            subprocess.run(["docker","start",bid],check=True,capture_output=True)
            subprocess.run(
                ["docker","exec","-i",bid,"bash","-c","umask 077; cat > /run/credentials.json"],
                input=json.dumps({"base":"http://"+app.NAME+":8080/cargo-tracker/","credentials":credentials,
                                  "fixture_tracking_id":report["page_fixture_tracking_id"],
                                  "retirement_render_evidence":{"actions":action273034_render_evidence()["actions"],"cancel_actions":action283133_render_evidence()["actions"],"action32":action32_render_evidence(),"handling_page":handling_page_retirement_evidence()},
                                  "handling_callback_render_evidence":handling_source_evidence}),
                text=True,check=True,capture_output=True,
            )
            def capture(stage,remaining):
                deadline=time.monotonic()+remaining
                def observe():
                    budget=deadline-time.monotonic()
                    if budget<=0:raise subprocess.TimeoutExpired("owned effects observer",remaining)
                    return app.capture_effects(container,timeout=budget)
                def pause(seconds):
                    time.sleep(min(seconds,max(0,deadline-time.monotonic())))
                sample=app.settle_effects(observe,timeout=min(15,remaining),pause=pause)
                return {"fixture_id":container,"stage":stage,
                        **{key:sample[key] for key in ("tables","queues","business_invocations")}}
            # Never consume an image-baked or prior-run result after a failed workflow.
            subprocess.run(["docker","exec",bid,"rm","-f","/out/results.json"],
                           check=True,text=True,capture_output=True)
            for artifact in ("results.json","browser.log","browser-timeout.json"):
                (WORK/artifact).unlink(missing_ok=True)
            def inspect_event(tracking_id,completion_date,location_code,remaining):
                if not re.fullmatch(r"[A-Z0-9]{8}",tracking_id) or completion_date!="2032-02-04" or location_code not in {"USCHI","DEHAM"}:
                    raise RuntimeError("Handling-event observer selector is outside the active fixture")
                deadline=time.monotonic()+min(remaining,30)
                processes=app.command("docker","exec",container,"jcmd","-l",timeout=max(.1,deadline-time.monotonic())).splitlines()
                candidates=[line.split()[0] for line in processes if "org.jboss.as.standalone" in line or "jboss-modules.jar" in line]
                if len(candidates)!=1:raise RuntimeError("Cannot identify unique app JVM for event observer")
                raw=app.command("docker","exec",container,"java","-cp","/opt/jboss/observer-client","ReadEffects",candidates[0],"handling-event",tracking_id,completion_date,location_code,timeout=max(.1,deadline-time.monotonic()))
                return json.loads(raw)
            # The lifecycle workflow has two independent five-by-15-second idle
            # windows plus all page, event-worker, and denial matrices. A fresh
            # prior run reached its final booking-cancel effects stage at 600s,
            # so allow one bounded 900-second window for the full suite.
            bound_seconds=900
            try:
                proc=bridge.run_browser_with_effects(
                    ["docker","exec","-i",bid,"node","workflows.cjs"],capture,timeout=bound_seconds,inspect_event=inspect_event,
                )
            except subprocess.TimeoutExpired as error:
                diagnostic={"timeout_seconds":bound_seconds,
                    "elapsed_seconds":getattr(error,"elapsed_seconds",None),
                    "last_completed_effect_stage":getattr(error,"last_completed_effect_stage",None),
                    "pending_effect_stage":getattr(error,"pending_effect_stage",None),
                    "completed_effect_stage_count":len(getattr(error,"completed_effect_stages",[])),
                    "completed_effect_stages":getattr(error,"completed_effect_stages",[])}
                (WORK/"browser-timeout.json").write_text(json.dumps(diagnostic,indent=2)+"\n")
                raise
            # Store raw diagnostics privately; never publish browser HTML/traces/session dumps.
            (WORK/"browser.log").write_text(proc.stdout)
            (WORK/"results.json").write_text(subprocess.check_output(["docker","exec",bid,"cat","/out/results.json"],text=True))
            results=json.loads((WORK/"results.json").read_text())
            report["browser_checks"]={"count":len(results["checks"]),"passed":all(c["passed"] for c in results["checks"])}
            if proc.returncode or not report["browser_checks"]["passed"]:raise AssertionError("Real browser workflow failed; inspect sanitized .work/kan19/results.json")
            promote_live_pages(report,results)
            promote_socket_cases(report,results)
            promote_navigation_actions(report,results)
            promote_claimed_cargo_actions(report,results)
            promote_cargo_entry_actions(report,results)
            promote_tracking_actions(report,results)
            replacement_proofs=results.get("replacement_actions",{})
            validate_replacement_keys(replacement_proofs)
            report["replacement_observations"]=replacement_proofs
            handling_csrf_proofs=results.get("handling_csrf_proofs",{})
            validate_handling_csrf_proofs(handling_csrf_proofs)
            report["handling_csrf_observations"]=handling_csrf_proofs
            handling_callback_proofs=results.get("handling_callback_retirements",{})
            report["handling_callback_retirement_observations"]=validate_handling_callback_retirements(handling_callback_proofs,handling_source_evidence)
            retirement_proofs=results.get("retirement_actions",{})
            callback_source=ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/ChangeDestinationDialog.java"
            if callback_source.exists():
                raise AssertionError("Obsolete destination dialog callback implementation remains in the candidate")
            source_hashes=action23_source_evidence()
            public_source_hashes=action44_source_evidence()
            deadline_source_hashes=action26_source_evidence()
            render_evidence=action32_render_evidence()
            for proof in retirement_proofs.values():
                if proof.get("legacy_id")=="ACTION-08":
                    proof["callback_implementation_absent"]=True
                elif proof.get("legacy_id")=="ACTION-23":
                    proof["callback_implementation_absent"]=True
                    proof["legacy_binding_discrepancy_verified"]=True
                    proof["source_hashes"]=source_hashes
                elif proof.get("legacy_id")=="ACTION-44":
                    proof["source_hashes"]=public_source_hashes
                elif proof.get("legacy_id")=="ACTION-26":
                    proof["source_hashes"]=deadline_source_hashes
                elif proof.get("legacy_id")=="ACTION-32":
                    proof["source_hashes"]=render_evidence["source_hashes"]
            validate_retirement_keys(retirement_proofs)
            report["retirement_observations"]=retirement_proofs
        finally:
            cleanup=[]
            if bid:
                result=subprocess.run(["docker","rm","-f",bid],capture_output=True)
                if result.returncode:cleanup.append("browser removal")
            if network:
                subprocess.run(["docker","network","disconnect","-f",network,container],capture_output=True)
                result=subprocess.run(["docker","network","rm",network],capture_output=True)
                if result.returncode:cleanup.append("private network removal")
            report["browser_cleanup"]={"container_removed":bool(bid) and "browser removal" not in cleanup,"network_removed":bool(network) and "private network removal" not in cleanup,"errors":cleanup}
            if cleanup:raise RuntimeError("Browser fixture cleanup incomplete: "+",".join(cleanup))
    return app.main(after_checks=browser)
if __name__=="__main__":main()
