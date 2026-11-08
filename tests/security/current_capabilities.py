"""Versioned current-capability contracts; historical definitions remain untouched."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import hashlib,json,subprocess,re
from urllib.parse import urlsplit,parse_qs,parse_qsl
from generate_cases import ROOT,build
from contracts import UnsupportedCase,run_cases,exit_code
import run_candidate_contracts as legacy
from staged_returns import return_observation
from replacements import SUPPORTED_REPLACEMENTS, replacement_observation
MANIFEST=ROOT/"specifications/current-capability-mapping-v2.json"
INVENTORY=ROOT/"specifications/access-policy-inventory.json"
NATIVE_CURRENT_LOADS=frozenset({"ACTION-07","ACTION-15","ACTION-16","ACTION-18","ACTION-20"})
ACTORS=["anonymous","Reader","Operator","Administrator"]
USERS={"Reader":"reader","Operator":"operator","Administrator":"admin"}

# Version-2 approval boundary: changes require explicit policy/code review.
APPROVED_INVENTORY_SHA256="fdde15304f5629fa356d4ac9f0462ac7d89b21c65b87c1e841680d23746303ea"
APPROVED_MAPPED=frozenset("ACTION-"+i for i in ["01","02","03","04","05","06","07","09","10","11","12","13","14","15","16","17","18","19","20","21","22","24","25","29","41","45"])
APPROVED_PENDING=frozenset()
APPROVED_GROUPS={'cancel-editor': {'legacy_ids': ['ACTION-08'], 'modern_method': 'GET', 'requirement': 'Leave destination editing without applying a change.'}, 'tracking-discovery': {'legacy_ids': ['ACTION-23', 'ACTION-44'], 'modern_method': 'POST', 'requirement': 'Authorized cargo discovery and valid/invalid typed tracking lookup.'}, 'booking-deadline': {'legacy_ids': ['ACTION-26', 'ACTION-32'], 'modern_method': 'POST', 'requirement': 'Strict deadline validation on the current booking form.'}, 'booking-single-page': {'legacy_ids': ['ACTION-27', 'ACTION-30', 'ACTION-34'], 'modern_method': 'POST', 'requirement': 'Origin/destination/deadline entry on one current booking page.'}, 'booking-cancel': {'legacy_ids': ['ACTION-28', 'ACTION-31', 'ACTION-33'], 'modern_method': 'GET', 'requirement': 'Leave booking without creating a cargo.'}, 'handling-single-page': {'legacy_ids': ['ACTION-35', 'ACTION-40', 'ACTION-43'], 'modern_method': 'GET', 'requirement': 'Authorized single-page handling entry and editing.'}, 'handling-cargo-voyage': {'legacy_ids': ['ACTION-36'], 'modern_method': 'POST', 'requirement': 'Valid selected cargo and available known-voyage choices; LOAD/UNLOAD requirements.'}, 'handling-location': {'legacy_ids': ['ACTION-37'], 'modern_method': 'POST', 'requirement': 'Valid required location selection.'}, 'handling-event': {'legacy_ids': ['ACTION-38'], 'modern_method': 'POST', 'requirement': 'Event validation, LOAD/UNLOAD voyage requirement and non-load voyage clearing.'}, 'handling-voyage': {'legacy_ids': ['ACTION-39'], 'modern_method': 'POST', 'requirement': 'Known-voyage validation, LOAD/UNLOAD requirements and non-load voyage clearing.'}, 'handling-completion': {'legacy_ids': ['ACTION-42'], 'modern_method': 'POST', 'requirement': 'Strict completion-time validation.'}}
APPROVED_RETIREMENT_POLICY='Never PASS; remain BLOCKED until replacement, specific negative-entry and independent-review evidence have a supported fresh runtime verifier.'
APPROVED_RETIREMENT_GROUP={ident:group for group,row in APPROVED_GROUPS.items() for ident in row["legacy_ids"]}
SCOPED_SOURCES={"/cargo-tracker/admin/show.xhtml","/cargo-tracker/admin/changeDestination.xhtml","/cargo-tracker/admin/route.xhtml","/cargo-tracker/admin/selectItinerary.xhtml"}

def local_uri(value):
    """Normalize context-relative proof metadata without discarding semantic query."""
    if not isinstance(value,str) or not value:raise UnsupportedCase()
    parsed=urlsplit(value)
    path=parsed.path if parsed.path.startswith("/") else "/cargo-tracker/"+parsed.path
    if parsed.scheme or parsed.netloc or parsed.fragment or not path.startswith("/cargo-tracker/") or chr(92) in path or any(x in path for x in ["..","%",";","//"]):raise UnsupportedCase()
    try:pairs=parse_qsl(parsed.query,keep_blank_values=True,strict_parsing=True)
    except ValueError:raise UnsupportedCase()
    keys=[key for key,value in pairs]
    if len(keys)!=len(set(keys)) or set(keys)-{"trackingId","jfwid"} or any(not value for key,value in pairs):raise UnsupportedCase()
    return path,dict(pairs)

def verify_action_proof(case,observation):
    tracking=observation.get("tracking_id")
    if "{cargo}" in case["path"] and re.fullmatch("[A-Z0-9]{8}",str(tracking)) is None:raise UnsupportedCase()
    target=case["path"].replace("{cargo}",str(tracking))
    target_path,target_query=local_uri(target)
    if case["method"]=="POST":
        if observation.get("action_method")!="POST" or observation.get("action_path")!=target or observation.get("source_entry_verified") is not True:raise UnsupportedCase()
        source=observation.get("entry_page") or observation.get("source_page")
    else:
        keys=observation.get("query_keys")
        drivers={"click","direct","keyboard"} if case.get("surface_id")=="ACTION-25" else {"click","direct"}
        if observation.get("driver") not in drivers or observation.get("action_executed") is not True or observation.get("target_origin_verified") is not True or observation.get("actual_target_path")!=target_path:raise UnsupportedCase()
        if not isinstance(keys,list) or any(not isinstance(k,str) for k in keys) or len(keys)!=len(set(keys)) or set(keys)-set(target_query)-{"jfwid"} or set(keys)-{"jfwid"}!=set(target_query):raise UnsupportedCase()
        if tracking!=target_query.get("trackingId"):raise UnsupportedCase()
        source=observation.get("source_page")
    expected_path,expected_query=local_uri(case["current_source"])
    if expected_path in SCOPED_SOURCES and "trackingId" not in expected_query and "trackingId" in target_query:
        expected_query["trackingId"]=target_query["trackingId"]
    source_path,source_query=local_uri(source)
    source_query.pop("jfwid",None)
    if source_path!=expected_path or source_query!=expected_query:raise UnsupportedCase()


def load_model():
    raw=INVENTORY.read_bytes();inventory=json.loads(raw);model=json.loads(MANIFEST.read_text())
    validate_model(model,inventory,hashlib.sha256(raw).hexdigest())
    return model,inventory

def validate_model(model,inventory,inventory_hash):
    if set(model)!={"schema_version","approval_record","approved_proposal_sha256","legacy_inventory_sha256","mapped_actions","pending_current_actions","replacement_capabilities","retirement_candidates","retirement_policy"}:raise ValueError("Unknown or missing model field")
    if model.get("schema_version")!=2 or model.get("legacy_inventory_sha256")!=inventory_hash:raise ValueError("Unknown version or inventory drift")
    if model.get("approval_record")!="notes/decisions/2026-11-02-current-ui-acceptance.md" or model.get("approved_proposal_sha256")!="710b00d37001276e8bd60d806f9fe21ea66a39b7b47ae465122ca78da931da5a":raise ValueError("Unbound approval")
    if inventory_hash!=APPROVED_INVENTORY_SHA256:raise ValueError("Approved inventory changed")
    if {r["legacy_id"] for r in model["mapped_actions"]}!=APPROVED_MAPPED or {r["legacy_id"] for r in model["pending_current_actions"]}!=APPROVED_PENDING or {r["legacy_id"] for r in model["retirement_candidates"]}!=set(APPROVED_RETIREMENT_GROUP):raise ValueError("Approved mapping partition changed")
    if model["retirement_policy"]!=APPROVED_RETIREMENT_POLICY:raise ValueError("Approved retirement policy changed")
    if {r["id"] for r in model["replacement_capabilities"]}!=set(APPROVED_GROUPS):raise ValueError("Approved replacement groups changed")
    for row in model["replacement_capabilities"]:
        approved=APPROVED_GROUPS[row["id"]]
        if row.get("legacy_ids")!=approved["legacy_ids"] or row.get("modern_method")!=approved["modern_method"] or row.get("requirement")!=approved["requirement"]:raise ValueError("Approved replacement requirements changed")
    for row in model["retirement_candidates"]:
        if row.get("replacement_id")!=APPROVED_RETIREMENT_GROUP[row["legacy_id"]]:raise ValueError("Approved retirement membership changed")
    callbacks={r["id"]:r for r in inventory["view_callbacks"]}
    actions=model.get("mapped_actions",[])+model.get("pending_current_actions",[])
    retire=model.get("retirement_candidates",[])
    identifiers=[r["legacy_id"] for r in actions+retire]
    if len(identifiers)!=len(set(identifiers)) or set(identifiers)!=set(callbacks):raise ValueError("Missing duplicate or unknown callback mapping")
    capids=[r["capability_id"] for r in actions]
    groups=model.get("replacement_capabilities",[]);group_ids=[r["id"] for r in groups]
    if len(capids)!=len(set(capids)) or len(group_ids)!=len(set(group_ids)) or set(capids)&set(group_ids):raise ValueError("Duplicate capability")
    group_map={r["id"]:r for r in groups};used=[]
    for row in actions:
        if set(row)!={"legacy_id","capability_id","modern_source","modern_target","modern_method"}:raise ValueError("Unknown or missing mapping field")
        target=urlsplit(row["modern_target"]);query=parse_qs(target.query,keep_blank_values=True)
        if row.get("modern_method") not in {"GET","POST"} or target.scheme or target.netloc or target.fragment or not target.path.startswith("/cargo-tracker/") or any(x in target.path for x in ["..","%","\\\\",";","//"]) or set(query)-{"trackingId"} or any(len(v)!=1 or not v[0] for v in query.values()):raise ValueError("Unsafe current target")
        try:
            source_path,source_query=local_uri(row["modern_source"])
            if set(source_query)-{"trackingId"}:raise UnsupportedCase()
        except UnsupportedCase:raise ValueError("Unsafe current source")
        if callbacks[row["legacy_id"]]["domain_mutation"] and row["modern_method"]!="POST":raise ValueError("Mutation transport weakened")
    for row in retire:
        if set(row)!={"legacy_id","replacement_id","status","required_evidence","negative_driver"}:raise ValueError("Unknown or missing retirement field")
        old=callbacks[row["legacy_id"]];group=group_map.get(row.get("replacement_id"))
        if old["domain_mutation"] or row.get("status")!="candidate" or row.get("negative_driver")!="pending" or group is None or row["legacy_id"] not in group.get("legacy_ids",[]):raise ValueError("Premature or unbound retirement")
        if set(row.get("required_evidence",[]))!={"replacement-per-actor","specific-negative-entry","native-role-session","no-protected-payload","required-independent-effects","independent-review"}:raise ValueError("Retirement evidence weakened")
        used.append(row["legacy_id"])
    declared=[]
    for group in groups:
        if set(group)!={"id","legacy_ids","allowed_roles","anonymous","modern_method","requirement","driver"}:raise ValueError("Unknown or missing replacement field")
        expected_driver="browser-replacement-v1" if group["id"] in SUPPORTED_REPLACEMENTS else "pending"
        if group.get("driver")!=expected_driver or group.get("modern_method") not in {"GET","POST"} or not group.get("requirement") or not group.get("legacy_ids"):raise ValueError("Unsupported replacement driver")
        for ident in group["legacy_ids"]:
            old=callbacks.get(ident)
            if old is None or old["domain_mutation"] or old["allowed_roles"]!=group.get("allowed_roles") or old["anonymous"]!=group.get("anonymous"):raise ValueError("Replacement policy drift")
            declared.append(ident)
    if len(declared)!=len(set(declared)) or set(declared)!=set(used):raise ValueError("Incomplete replacement traceability")

def build_current(model,inventory):
    mapped={r["legacy_id"]:r for r in model["mapped_actions"]}
    pending={r["legacy_id"]:r for r in model["pending_current_actions"]}
    retired={r["legacy_id"] for r in model["retirement_candidates"]}
    cases=[]
    for old in build(inventory):
        if old["surface_id"] in retired:continue
        row=mapped.get(old["surface_id"]) or pending.get(old["surface_id"])
        case=deepcopy(old)
        case.update(id="CURRENT::"+old["id"],contract_version=2,kind="current",legacy_case_id=old["id"],legacy_contract=deepcopy(old),capability_id=row["capability_id"] if row else old["surface_id"].lower(),binding_status="pending" if old["surface_id"] in pending else "native-batch-import" if old["surface_id"]=="BG-01" else "native-batch-processing" if old["surface_id"]=="BG-02" else "native-staged-return" if old["surface_id"]=="ACTION-13" else "native-current-load" if old["surface_id"] in NATIVE_CURRENT_LOADS else "browser-current-navigation" if old["surface_id"] in {"ACTION-10","ACTION-11","ACTION-12","ACTION-21","ACTION-22","ACTION-24","ACTION-25","ACTION-45"} else "existing-runtime-driver")
        if row:
            source="index.xhtml" if old["surface_id"]!="ACTION-13" and old["actor"]=="anonymous" and old["expected"]=="deny" and row["modern_method"]=="GET" else row["modern_source"]
            case.update(path=row["modern_target"],method=row["modern_method"],current_source=source)
        cases.append(case)
    for group in model["replacement_capabilities"]:
        for actor in ACTORS:
            allowed=group["anonymous"] if actor=="anonymous" else actor in group["allowed_roles"]
            cases.append({"id":"REPLACEMENT::"+group["id"]+"::"+actor,"contract_version":2,"kind":"replacement","capability_id":group["id"],"channel":"capability","actor":actor,"expected":"allow" if allowed else "deny","write":False,"method":group["modern_method"],"semantic_requirement":group["requirement"],"requires_specific_driver":True,"binding_status":group["driver"],"legacy_ids":deepcopy(group["legacy_ids"])})
    if len({c["id"] for c in cases})!=len(cases):raise ValueError("Duplicate current case")
    return cases

def source_fingerprint():
    paths=subprocess.check_output(["git","ls-files","-co","--exclude-standard","--","candidate","tests/candidate-runtime","tests/browser-workflows","tests/security","specifications/access-policy-inventory.json","specifications/current-capability-mapping-v2.json","notes/decisions/2026-11-02-current-ui-acceptance.md"],cwd=ROOT,text=True).splitlines()
    digest=hashlib.sha256()
    for name in sorted(set(paths)):
        path=ROOT/name
        if path.is_file():digest.update(name.encode()+b"\0"+hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()

class CurrentAdapter:
    def __init__(self,live=False):
        # Snapshot before loading definitions so the cache and receipt share one baseline.
        before=source_fingerprint() if live else None
        self.model,self.inventory=load_model()
        self.contracts={c["id"]:deepcopy(c) for c in build_current(self.model,self.inventory)}
        self.legacy_contracts=deepcopy(build(self.inventory))
        self._retirement_model=deepcopy(self.model)
        definitions={"current":list(self.contracts.values()),"legacy":self.legacy_contracts,"retirements":self._retirement_model["retirement_candidates"]}
        self._contracts_fingerprint=hashlib.sha256(json.dumps(definitions,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        self.provenance=None;self.legacy=None;self._run_fingerprint=None
        if live:
            if source_fingerprint()!=before:raise RuntimeError("Inputs changed while loading canonical contracts")
            self.legacy=legacy.LiveSubsetCandidate()
            if source_fingerprint()!=before:raise RuntimeError("Runtime or contract inputs changed during fixture")
            self._run_fingerprint=before
            self.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":before,"canonical_contracts_sha256":self._contracts_fingerprint,"legacy_fixture_cleanup_verified":True,"imported_code_attested":False,"fingerprint_scope":"On-disk inputs and constructed canonical contracts; already imported Python code identity is not attested."}
    def execute(self,case):
        canonical=self.contracts.get(case.get("id"))
        if canonical is None or canonical!=case:raise UnsupportedCase()
        if case["kind"] not in {"current","replacement"} or self.legacy is None or self.provenance is None:
            raise UnsupportedCase()
        if case["kind"]=="current" and case.get("binding_status") not in {"existing-runtime-driver","native-current-load","browser-current-navigation","native-staged-return","native-batch-import","native-batch-processing"}:
            raise UnsupportedCase()
        if not isinstance(self.provenance,dict) or self.provenance.get("kind")!="fresh-owned-runtime" or self.provenance.get("legacy_fixture_cleanup_verified") is not True or self.provenance.get("inputs_fingerprint")!=self._run_fingerprint or re.fullmatch("[0-9a-f]{64}",str(self._run_fingerprint)) is None:raise UnsupportedCase()
        if case["kind"]=="replacement":
            observation=replacement_observation(case,getattr(self.legacy,"replacement_observations",{}).get(case["id"],{}))
        elif case["binding_status"] in {"native-batch-import","native-batch-processing"}:
            observation=deepcopy(getattr(self.legacy,"batch_import_observations",{}).get(case["actor"],{}))
            if (observation.get("driver")!="native-batch-import-v1" or observation.get("actor")!=case["actor"]
                    or observation.get("supported") is not True):
                raise UnsupportedCase()
            if case["actor"]!="anonymous":
                if observation.get("direct_api_effects_unchanged") is not True or any(
                        observation.get("direct_api_denials",{}).get(operation)!=403
                        or observation.get("direct_api_payload_absent",{}).get(operation) is not True
                        for operation in ("read","start")):
                    raise UnsupportedCase()
            if case["binding_status"]=="native-batch-processing" and case["actor"]=="Administrator":
                processing=deepcopy(getattr(self.legacy,"batch_processing_observation",{}))
                required_processing=("native-batch-processing-v1","Administrator",200)
                if (processing.get("driver")!=required_processing[0]
                        or processing.get("actor")!=required_processing[1]
                        or processing.get("status")!=required_processing[2]
                        or processing.get("supported") is not True
                        or processing.get("authorized_job_completed") is not True
                        or processing.get("batch_worker_identity_verified") is not True
                        or processing.get("directory_policy_verified") is not True
                        or processing.get("valid_input_consumed") is not True
                        or processing.get("valid_event_persisted") is not True
                        or processing.get("valid_archive_verified") is not True
                        or processing.get("invalid_input_consumed") is not True
                        or processing.get("invalid_failed_output_verified") is not True
                        or processing.get("business_side_effects_bounded") is not True
                        or processing.get("administrator_identity",{}).get("server_verified") is not True
                        or processing.get("administrator_identity",{}).get("principal")!="admin"
                        or processing.get("administrator_identity",{}).get("roles")!=["Administrator"]):
                    raise UnsupportedCase()
                observation["processing_evidence"]=processing
            if case["expected"]=="allow":
                if (case["actor"]!="Administrator" or observation.get("authorized_form_status")!=200
                        or observation.get("csrf_present") is not True or observation.get("viewstate_present") is not True
                        or observation.get("authorized_start_accepted") is not True
                        or observation.get("empty_business_state_unchanged") is not True
                        or observation.get("empty_control_calls_bounded") is not True
                        or observation.get("worker_identity_verified") is not True
                        or observation.get("valid_event_persisted") is not True
                        or observation.get("valid_queue_cycles") is not True
                        or observation.get("valid_table_deltas") is not True
                        or observation.get("valid_invocation_deltas_bounded") is not True):
                    raise UnsupportedCase()
            elif (observation.get("independent_effects_unchanged") is not True
                    or observation.get("protected_payload_absent") is not True):
                raise UnsupportedCase()
            elif case["actor"]=="anonymous":
                if (observation.get("get_status")!=303 or observation.get("post_status")!=303
                        or observation.get("redirect_is_configured_login") is not True):
                    raise UnsupportedCase()
            elif observation.get("get_status")!=403 or observation.get("post_status")!=403:
                raise UnsupportedCase()
        elif case["binding_status"]=="native-staged-return":
            observation=return_observation(case,getattr(self.legacy,"current_observations",{}).get(case["id"],{}))
        elif case["binding_status"]=="native-current-load":
            observation=deepcopy(getattr(self.legacy,"current_observations",{}).get(case["id"],{}))
            if observation.get("current_load_driver")!="native-current-load-v1" or observation.get("invalid_inputs_verified") is not True:raise UnsupportedCase()
            if case["surface_id"]=="ACTION-15" and case["expected"]=="allow" and observation.get("route_details_verified") is not True:
                raise UnsupportedCase()
            if case["surface_id"]=="ACTION-18" and observation.get("route_alias_verified") is not True:raise UnsupportedCase()
            if case["expected"]=="allow" and (observation.get("selected_cargo_verified") is not True or observation.get("current_values_verified") is not True):raise UnsupportedCase()
        elif case["binding_status"]=="browser-current-navigation":
            observation=deepcopy(getattr(self.legacy,"current_observations",{}).get(case["id"],{}))
            if case["surface_id"]=="ACTION-10":
                if observation.get("current_navigation_driver")!="browser-claimed-cargo-v1":raise UnsupportedCase()
                allowed_flags=("selected_cargo_verified","persisted_details_verified")
                denied_flags=("claimed_list_denied",)
            elif case["surface_id"] in {"ACTION-24","ACTION-45"}:
                if observation.get("current_navigation_driver")!="browser-lookup-v1":raise UnsupportedCase()
                if case["expected"]=="allow":
                    if observation.get("submission_status") not in {302,303} or observation.get("invalid_inputs_verified") is not True or observation.get("csrf_checks_verified") is not True:raise UnsupportedCase()
                    if case["surface_id"]=="ACTION-45" and observation.get("legacy_entry_verified") is not True:raise UnsupportedCase()
                allowed_flags=("selected_cargo_verified","persisted_details_verified")
                denied_flags=("lookup_source_denied",)
            elif case["surface_id"]=="ACTION-25":
                if observation.get("current_navigation_driver")!="browser-marker-v1":raise UnsupportedCase()
                allowed_flags=("selected_cargo_verified","persisted_details_verified","live_marker_verified")
                denied_flags=("live_source_denied",)
            else:
                state="ROUTED" if case["surface_id"]=="ACTION-22" else "NOT_ROUTED"
                if observation.get("current_navigation_driver")!="browser-cargo-entry-v1" or observation.get("entry_state")!=state:raise UnsupportedCase()
                allowed_flags=("entry_chain_verified","selected_cargo_verified","editor_verified" if case["surface_id"]=="ACTION-12" else "route_choices_verified")
                denied_flags=("source_access_verified","source_controls_hidden")
            if case["expected"]=="allow":
                if observation.get("driver")!=("keyboard" if case["surface_id"]=="ACTION-25" else "click") or not all(observation.get(key) is True for key in allowed_flags):raise UnsupportedCase()
            elif observation.get("driver")!="direct" or not all(observation.get(key) is True for key in denied_flags):raise UnsupportedCase()
        else:
            observation=deepcopy(self.legacy.execute(deepcopy(canonical["legacy_contract"])))
        actor=case["actor"]
        if actor in USERS:
            identity=observation.get("identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:raise UnsupportedCase()
        elif actor=="anonymous":
            if observation.get("identity") is not None:raise UnsupportedCase()
        elif actor=="routing-service":
            identity=observation.get("native_identity",{})
            if identity.get("principal")!="routing" or identity.get("roles")!=["RoutingService"] or observation.get("machine_identity_verified") is not True or observation.get("machine_scope")!=case.get("required_machine_scope"):raise UnsupportedCase()
        else:raise UnsupportedCase()
        if case["kind"]=="current" and case["binding_status"]!="native-staged-return" and (canonical["legacy_contract"]["channel"]=="action" or canonical["legacy_contract"].get("original_channel")=="action"):
            verify_action_proof(case,observation)
        observation["current_provenance"]=deepcopy(self.provenance)
        return observation
    def execute_retirement(self,case,replacement_results):
        if (not isinstance(case,dict) or case.get("legacy_id")!="ACTION-08"
                or case.get("actor") not in ACTORS
                or case.get("replacement_case_id")!="REPLACEMENT::cancel-editor::"+str(case.get("actor"))
                or self.legacy is None or not isinstance(self.provenance,dict)
                or self.provenance.get("kind")!="fresh-owned-runtime"
                or self.provenance.get("legacy_fixture_cleanup_verified") is not True
                or self.provenance.get("inputs_fingerprint")!=self._run_fingerprint
                or re.fullmatch("[0-9a-f]{64}",str(self._run_fingerprint)) is None):
            raise UnsupportedCase()
        replacement=next((row for row in replacement_results if row.get("case")==case["replacement_case_id"]),None)
        if not isinstance(replacement,dict) or replacement.get("outcome")!="PASS":
            raise UnsupportedCase()
        proof=deepcopy(getattr(self.legacy,"retirement_observations",{}).get(case["id"],{}))
        actor=case["actor"]
        if (proof.get("driver")!="browser-retired-action-v1" or proof.get("legacy_id")!="ACTION-08"
                or proof.get("actor")!=actor or proof.get("method")!="POST"
                or re.fullmatch(r"/cargo-tracker/admin/changeDestination\.xhtml\?trackingId=[A-Z0-9]{8}",str(proof.get("source_path"))) is None
                or proof.get("historical_source_component_id")!="j_idt8:j_idt23"
                or proof.get("historical_source_parameter")!="javax.faces.source"
                or proof.get("callback_implementation_absent") is not True
                or proof.get("post_target_verified") is not True
                or proof.get("independent_effects_unchanged") is not True):
            raise UnsupportedCase()
        if actor in {"Operator","Administrator"}:
            identity=proof.get("identity",{})
            if (proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                    or proof.get("current_viewstate_present") is not True or proof.get("callback_response_absent") is not True
                    or proof.get("response_status") != 200
                    or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor]
                    or identity.get("roles")!=[actor]):
                raise UnsupportedCase()
        elif actor=="Reader":
            identity=proof.get("identity",{})
            if (proof.get("response_status")!=403 or proof.get("authorization_denied") is not True
                    or proof.get("protected_payload_absent") is not True
                    or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor]
                    or identity.get("roles")!=[actor]):
                raise UnsupportedCase()
        elif (proof.get("response_status")!=303 or proof.get("authorization_denied") is not True
                or proof.get("protected_payload_absent") is not True
                or proof.get("redirect_is_configured_login") is not True
                or proof.get("identity") is not None):
            raise UnsupportedCase()
        return proof

def retirement_results(model,adapter,current_results):
    results=[]
    for row in model["retirement_candidates"]:
        for actor in ACTORS:
            case={"id":"RETIREMENT::"+row["legacy_id"]+"::"+actor,"legacy_id":row["legacy_id"],"actor":actor,"replacement_case_id":"REPLACEMENT::"+row["replacement_id"]+"::"+actor}
            try:
                adapter.execute_retirement(case,current_results)
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"BLOCKED","specific_negative_entry_verified":True,"outcome_note":"Fresh replacement and retired-entry evidence validated; independent review pending, so not RETIRED or PASS"})
            except UnsupportedCase:
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"BLOCKED","reason":"Replacement and specific fresh negative-entry/review verifier pending; not RETIRED or PASS"})
    return results

def report(live=False):
    adapter=CurrentAdapter(live=live)
    cases=deepcopy(list(adapter.contracts.values()))
    current=run_cases(cases,adapter);retirements=retirement_results(adapter._retirement_model,adapter,current)
    audit=run_cases(deepcopy(adapter.legacy_contracts),adapter.legacy if live else legacy.PendingCandidate())
    status=exit_code(current)
    if status==0 and any(r["outcome"]!="RETIRED" for r in retirements):status=2
    retirement_observations=deepcopy(getattr(adapter.legacy,"retirement_observations",{})) if live else {}
    return {"schema_version":2,"execution":"fresh-owned-runtime" if live else "not executed","current_counts":dict(Counter(r["outcome"] for r in current)),"current_results":current,"retirement_counts":dict(Counter(r["outcome"] for r in retirements)),"retirement_results":retirements,"retirement_observations":retirement_observations,"legacy_audit":{"total":len(audit),"counts":dict(Counter(r["outcome"] for r in audit)),"results":audit},"gate_exit":status,"provenance":adapter.provenance}
