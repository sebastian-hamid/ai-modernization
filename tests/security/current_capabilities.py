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
from replay_bg06_scoped_gate import validate_scope as validate_bg06_scope
from handling_retirement_evidence import load_source_evidence as load_handling_callback_source_evidence
from handling_page_redirects import is_safe_handling_redirect
MANIFEST=ROOT/"specifications/current-capability-mapping-v2.json"
INVENTORY=ROOT/"specifications/access-policy-inventory.json"
NATIVE_CURRENT_LOADS=frozenset({"ACTION-07","ACTION-15","ACTION-16","ACTION-18","ACTION-20"})
BG01_MACHINE_SCOPE="Trusted scheduler/batch worker; no implied logged-in human principal"
BG02_MACHINE_SCOPE="Trusted filesystem producer and batch worker, not untrusted HTTP caller"
ACTORS=["anonymous","Reader","Operator","Administrator"]
USERS={"Reader":"reader","Operator":"operator","Administrator":"admin"}

# Version-2 approval boundary: changes require explicit policy/code review.
APPROVED_INVENTORY_SHA256="1cc4f3cf1320fe9b6f1cbe14b261fab4c09fd3a025c02057f2e2df047f0fafef"
APPROVED_MAPPED=frozenset("ACTION-"+i for i in ["01","02","03","04","05","06","07","09","10","11","12","13","14","15","16","17","18","19","20","21","22","24","25","29","41","45"])
APPROVED_PENDING=frozenset()
ACTION08_RETIREMENT_VALIDATION=ROOT/"notes/evidence/kan-15-action08-retirement/validation.json"
ACTION08_RETIREMENT_REVIEW=ROOT/"notes/agent-reviews/2026-11-14-kan15-action08-retirement-review.md"
ACTION08_RETIREMENT_REVIEW_SHA256="673381cf2fc8c4c36a20105be2ddc76decac3d1567ce7e4f5f1596ebc4ed44d6"
ACTION08_RETIREMENT_VALIDATION_SHA256="773e9538885bd03460afc3dd43b103569ea09271a5cd6192137aab8c6652262e"
ACTION08_RAW_RESULTS_SHA256="d089a8b4f1ffbb63bea9870e05e8ba4e20f68b34cdc430a43ea6abe8c9bc7280"
ACTION23_RETIREMENT_VALIDATION=ROOT/"notes/evidence/kan-15-action23-retirement/validation.json"
ACTION23_RETIREMENT_REVIEW=ROOT/"notes/agent-reviews/2026-11-15-kan15-action23-retirement-review.md"
ACTION23_FRESH_EVIDENCE=ROOT/"notes/evidence/kan-15-action23-retirement/candidate-evidence.json"
ACTION23_RETIREMENT_REVIEW_SHA256="e3cb115b436696aba1bb41e64cc755acc33dfbf3b2ed264d9c550629c70b1259"
ACTION23_RETIREMENT_VALIDATION_SHA256="7168ec3bd1b537d0ca8f85d55bc59a7f79d6358123a18662ca725f362d3f3c9a"
ACTION44_RETIREMENT_VALIDATION=ROOT/"notes/evidence/kan-15-action44-retirement/validation.json"
ACTION44_RETIREMENT_REVIEW=ROOT/"notes/agent-reviews/2026-11-15-kan15-action44-retirement-review.md"
ACTION44_FRESH_EVIDENCE=ROOT/"notes/evidence/kan-15-action44-retirement/candidate-evidence.json"
ACTION44_RETIREMENT_REVIEW_SHA256="f90ba5168f0eae090eec1ecc52906834641bcf79dcccd9907869cdc3683cba32"
ACTION44_RETIREMENT_VALIDATION_SHA256="ba069afbcc7cf2766ecf5a7bba4816fc086d5262ccf105e04123e55d606ed432"
ACTION44_FRESH_EVIDENCE_SHA256="e97f77f83048e1fc53c3de99bdeed9f6df8e64e4e65e18a57b01a6e9c7097ecf"
ACTION26_RETIREMENT_VALIDATION=ROOT/"notes/evidence/kan-15-action26-retirement/validation.json"
ACTION26_RETIREMENT_REVIEW=ROOT/"notes/agent-reviews/2026-11-15-kan15-action26-retirement-review.md"
ACTION26_FRESH_EVIDENCE=ROOT/"notes/evidence/kan-15-action26-retirement/candidate-evidence.json"
ACTION26_RETIREMENT_REVIEW_SHA256="db2cf0b2da9621d943da25c594ce88ac2c0599a89a38b01fa1e454b48396bddc"
ACTION26_RETIREMENT_VALIDATION_SHA256="7e2e0d407e6b3a6558e07b6bd6771f71a5038e857e4080c51d8d65484d8188bb"
ACTION26_FRESH_EVIDENCE_SHA256="11262b6c1f64730ef3483d84e56b5ce92521ed3efa087ac20b5f5b85ef0e260e"
ACTION273034_RENDER_EVIDENCE=ROOT/"notes/evidence/kan-15-action273034-retirement/legacy-rendered-actions.json"
ACTION273034_RENDER_EVIDENCE_SHA256="254efb3c850698d6f707f279d8eb14362af9c5e28a34a141c04294e5bbe931d8"
ACTION283133_RENDER_EVIDENCE=ROOT/"notes/evidence/kan-15-action283133-retirement/legacy-rendered-actions.json"
ACTION283133_RENDER_EVIDENCE_SHA256="f1bf3f6d3b4df711b75d575d49c472488d7bb17177c5b8c4525fb19d15b3efd7"
ACTION283133_PROMOTION_VALIDATION=ROOT/"notes/evidence/kan-15-action283133-retirement/promotion-validation.json"
ACTION283133_PROMOTION_VALIDATION_SHA256="8600680c87d5562872b10e9854655044d849e3a05ae158d82a0cd29ecdea016e"
ACTION283133_PROMOTION_REVIEW=ROOT/"notes/agent-reviews/2026-11-16-kan15-actions283133-mapping-promotion-review.md"
ACTION283133_PROMOTION_REVIEW_SHA256="9447d7b2ac7bb7c670aee400dac33bbc250302cb3d9c55472e78d381e08da8f8"
ACTION283133_CANDIDATE_EVIDENCE=ROOT/"notes/evidence/kan-15-action283133-retirement/candidate-evidence.json"
ACTION283133_CANDIDATE_EVIDENCE_SHA256="53b1b644c5b0eb964848ca3e64d67bac624f2349dc16166b03d7afcf95b99c81"
ACTION283133_BROWSER_RESULTS=ROOT/"notes/evidence/kan-15-action283133-retirement/browser-results.json"
ACTION283133_BROWSER_RESULTS_SHA256="8fcacda9072a7b527721c67bb7387af4ef4a5258652e3cdc81cc9fc6db0301ba"
ACTION273034_PROMOTION_VALIDATION=ROOT/"notes/evidence/kan-15-action273034-retirement/promotion-validation.json"
ACTION273034_PROMOTION_VALIDATION_SHA256="3908d47819d4b7461cc92879e51bb1cb57fad1489ebf8b096f75652dbe1f565d"
ACTION273034_PROMOTION_REVIEW=ROOT/"notes/agent-reviews/2026-11-16-kan15-actions273034-mapping-promotion-review.md"
ACTION273034_PROMOTION_REVIEW_SHA256="811a12922bab66ce3c5b42d01823a358e0b474d6acca70835aab19e2937e43f6"
ACTION273034_CANDIDATE_EVIDENCE=ROOT/"notes/evidence/kan-15-action273034-retirement/candidate-evidence.json"
ACTION273034_CANDIDATE_EVIDENCE_SHA256="9847d60eea220aabe5ede648a487bddd1933a3e774c848e96be1caded37d0e10"
ACTION273034_BROWSER_RESULTS=ROOT/"notes/evidence/kan-15-action273034-retirement/browser-results.json"
ACTION273034_BROWSER_RESULTS_SHA256="fb307132d13270b5d195c610b4b611504b162029dcd4e0d0252af1b110a05f5f"
ACTION32_RETIREMENT_VALIDATION=ROOT/"notes/evidence/kan-15-action32-retirement/validation.json"
ACTION32_RETIREMENT_REVIEW=ROOT/"notes/agent-reviews/2026-11-15-kan15-action32-retirement-review.md"
ACTION32_FRESH_EVIDENCE=ROOT/"notes/evidence/kan-15-action32-retirement/candidate-evidence.json"
ACTION32_RENDER_EVIDENCE=ROOT/"notes/evidence/kan-15-action32-retirement/legacy-rendered-entry.json"
ACTION32_NATIVE_RESULTS=ROOT/"notes/evidence/kan-15-action32-retirement/native-results.json"
ACTION32_BROWSER_RESULTS=ROOT/"notes/evidence/kan-15-action32-retirement/browser-results.json"
ACTION32_RETIREMENT_REVIEW_SHA256="e6b6d16e8f6d74b9ee1f5cd2fece44503fd44c323ee28b2b5d033c34e08bb0b5"
ACTION32_RETIREMENT_VALIDATION_SHA256="bc457834289b0f9b1b6b4a73a16246bc75464fae759d7e2c370d4d3ea9f2861b"
ACTION32_FRESH_EVIDENCE_SHA256="971140884fa2afe35468272e9edb3cfc0f03cb6224b97fc53c5db0669ab99ee2"
ACTION32_RENDER_EVIDENCE_SHA256="f3e959112d5072c28928bb270c85fd1b6cc78e5eca5b9d6f20e7207a01e38e5f"
ACTION32_NATIVE_RESULTS_SHA256="0fc617aa0f868298e46caf3f63c5e3998cf76e513439cbfb40a43c77eaef7274"
ACTION32_BROWSER_RESULTS_SHA256="73c8e6f74a0b441a8c7362d8ae75638b6c9a851bc023a84fcfaadae763740e37"
ACTION23_FRESH_EVIDENCE_SHA256="f466c5c6c00e17b1983247a7f5108e768e8917647b5c46b685368a58eebc9fdd"
ACTION08_PROOF_SHA256={"anonymous":"fa403104559e7db7e9235d03e08dcf9763e245c348f97fc4bef0b36cdc6c485c","Reader":"7fbf2fd784971a123977825a64b822e4714f04b08fa27cb5af8fbc864ab760df","Operator":"edfa114363b1c46a7b2f403d129485e8cdb27c4a676dcbd4e96fbbc0035e39ff","Administrator":"749362921409b4db70c47a263c5a916616a8b933d228b5a6f5433379727e5a09"}
APPROVED_GROUPS={'cancel-editor': {'legacy_ids': ['ACTION-08'], 'modern_method': 'GET', 'requirement': 'Leave destination editing without applying a change.'}, 'tracking-discovery': {'legacy_ids': ['ACTION-23', 'ACTION-44'], 'modern_method': 'POST', 'requirement': 'Authorized cargo discovery and valid/invalid typed tracking lookup.'}, 'booking-deadline': {'legacy_ids': ['ACTION-26', 'ACTION-32'], 'modern_method': 'POST', 'requirement': 'Strict deadline validation on the current booking form.'}, 'booking-single-page': {'legacy_ids': ['ACTION-27', 'ACTION-30', 'ACTION-34'], 'modern_method': 'POST', 'requirement': 'Origin/destination/deadline entry on one current booking page.'}, 'booking-cancel': {'legacy_ids': ['ACTION-28', 'ACTION-31', 'ACTION-33'], 'modern_method': 'GET', 'requirement': 'Leave booking without creating a cargo.'}, 'handling-single-page': {'legacy_ids': ['ACTION-35', 'ACTION-40', 'ACTION-43'], 'modern_method': 'GET', 'requirement': 'Authorized single-page handling entry and editing.'}, 'handling-cargo-voyage': {'legacy_ids': ['ACTION-36'], 'modern_method': 'POST', 'requirement': 'Valid selected cargo and available known-voyage choices; LOAD/UNLOAD requirements.'}, 'handling-location': {'legacy_ids': ['ACTION-37'], 'modern_method': 'POST', 'requirement': 'Valid required location selection.'}, 'handling-event': {'legacy_ids': ['ACTION-38'], 'modern_method': 'POST', 'requirement': 'Event validation, LOAD/UNLOAD voyage requirement and non-load voyage clearing.'}, 'handling-voyage': {'legacy_ids': ['ACTION-39'], 'modern_method': 'POST', 'requirement': 'Known-voyage validation, LOAD/UNLOAD requirements and non-load voyage clearing.'}, 'handling-completion': {'legacy_ids': ['ACTION-42'], 'modern_method': 'POST', 'requirement': 'Strict completion-time validation.'}}
APPROVED_RETIREMENT_POLICY='Never PASS; remain BLOCKED until replacement, specific negative-entry and independent-review evidence have a supported fresh runtime verifier.'
APPROVED_RETIREMENT_GROUP={ident:group for group,row in APPROVED_GROUPS.items() for ident in row["legacy_ids"]}
HANDLING_CALLBACK_RETIREMENT_ACTIONS={"ACTION-36":"handling-cargo-voyage","ACTION-37":"handling-location",
    "ACTION-38":"handling-event","ACTION-39":"handling-voyage","ACTION-42":"handling-completion"}
HANDLING_PAGE_RETIREMENT_ACTIONS={"ACTION-35":"handling-single-page","ACTION-40":"handling-single-page"}
HANDLING_CALLBACK_PROMOTION_VALIDATION=ROOT/"notes/evidence/kan-15-handling-callback-retirement/promotion-validation.json"
HANDLING_CALLBACK_PROMOTION_REVIEW=ROOT/"notes/agent-reviews/2026-11-17-kan15-handling-callback-promotion-review.md"
HANDLING_CALLBACK_GATE_EVIDENCE=ROOT/"notes/evidence/kan-15-handling-callback-retirement/current-capability-gate.json"
HANDLING_CALLBACK_CANDIDATE_EVIDENCE=ROOT/"notes/evidence/kan-15-handling-callback-retirement/candidate-runtime-results.json"
HANDLING_CALLBACK_BROWSER_EVIDENCE=ROOT/"notes/evidence/kan-15-handling-callback-retirement/browser-results.json"
HANDLING_CALLBACK_PROMOTION_VALIDATION_SHA256="8e321f7d7548865d3fb083168fb03af4dfa90e8101b755d1599b037a1a996319"
HANDLING_CALLBACK_PROMOTION_REVIEW_SHA256="40a513fa8b2dedcc4bfe3f10fe77a66e345fd939cfc6d30a0ef64e7c32828dcb"
HANDLING_CALLBACK_GATE_SHA256="2aac7f064b53f7a49a44dc4860d46c5422f370e2c89f8584cd769923d019cba2"
HANDLING_CALLBACK_CANDIDATE_SHA256="c3b9da47d899659447b25f3e84b2e015a975ec0266eca523d36bf6de557e9fbf"
HANDLING_CALLBACK_BROWSER_SHA256="519e7f2e96b63ea1aee21114112500b99f6dcc58f0e1d3f4b23fbd5fe5ea8b16"
HANDLING_CALLBACK_CAPTURE_SHA256="a0f2eb78c8f3c0698f35fd5b2c2cec109a9c2eecc608ae78742c6961a4d113cb"
HANDLING_PAGE_PROMOTION_VALIDATION=ROOT/"notes/evidence/kan-15-handling-page-retirement/promotion-validation.json"
HANDLING_PAGE_PROMOTION_REVIEW=ROOT/"notes/agent-reviews/2026-11-17-kan15-handling-page-retirement-review.md"
HANDLING_PAGE_GATE_EVIDENCE=ROOT/"notes/evidence/kan-15-handling-page-retirement/current-capability-gate.json"
HANDLING_PAGE_CANDIDATE_EVIDENCE=ROOT/"notes/evidence/kan-15-handling-page-retirement/candidate-runtime-results.json"
HANDLING_PAGE_BROWSER_EVIDENCE=ROOT/"notes/evidence/kan-15-handling-page-retirement/browser-results.json"
HANDLING_PAGE_PROMOTION_VALIDATION_SHA256="7a0446e36b4b2375b811cef1517ec0f4860f8c499d8d466019cf7925e3ac01e8"
HANDLING_PAGE_PROMOTION_REVIEW_SHA256="f51613251278825ca4859f442f65e56c1b614603a2bc1a307f5b19aa6b8a0704"
HANDLING_PAGE_GATE_SHA256="96c59c67f207af4cd5d6fb8364e4a7a3471c1fac339abe0534737ca36f72a74e"
HANDLING_PAGE_CANDIDATE_SHA256="637f8b53c5a52c5e799b99516ffa8136492cbbb39110ab63845f6e69bc3f8ff1"
HANDLING_PAGE_BROWSER_SHA256="eac9cf910aa529352709d74952d6e068a7aa8c5044f96c5ddf0f2825543609f6"
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


def batch_worker_observation(case,processing):
    """Bind fresh filesystem and batch evidence to the server batch-worker identity."""
    case_id=case.get("id")
    bg01=case_id=="CURRENT::BG-01-MACHINE::worker-BG-01::active"
    bg02=case_id=="CURRENT::BG-02-MACHINE::worker-BG-02::active"
    required=("authorized_job_completed","batch_worker_identity_verified","directory_policy_verified",
              "valid_input_consumed","valid_event_persisted","valid_archive_verified",
              "invalid_input_consumed","invalid_failed_output_verified","business_side_effects_bounded")
    if bg02:
        required+=("trusted_filesystem_staging_verified","untrusted_os_identity_denied")
    initiator=processing.get("administrator_identity",{})
    scope=BG01_MACHINE_SCOPE if bg01 else BG02_MACHINE_SCOPE if bg02 else None
    producer=processing.get("filesystem_producer_identity",{})
    worker_os=processing.get("filesystem_worker_identity",{})
    untrusted_access=processing.get("untrusted_os_access",{})
    exact_untrusted_denials=(type(processing.get("untrusted_os_uid")) is int
        and processing.get("untrusted_os_uid")==65534
        and set(untrusted_access)=={"incoming","archive","failed"}
        and all(isinstance(proof,dict) and proof.get("list_denied") is True
            and proof.get("read_denied") is True and proof.get("write_denied") is True
            and proof.get("marker_absent") is True
            for proof in untrusted_access.values()))
    if (not (bg01 or bg02)
            or case.get("actor")!=("worker-BG-01" if bg01 else "worker-BG-02")
            or case.get("expected")!="allow"
            or case.get("required_machine_scope")!=scope
            or processing.get("driver")!="native-batch-processing-v1"
            or processing.get("actor")!="Administrator" or processing.get("status")!=200
            or processing.get("supported") is not True
            or not all(processing.get(key) is True for key in required)
            or initiator.get("server_verified") is not True or initiator.get("principal")!="admin"
            or initiator.get("roles")!=["Administrator"]
            or (bg02 and (producer.get("verified") is not True or type(producer.get("uid")) is not int
                or producer.get("uid")!=0 or producer.get("scope")!="approved fixture administration tooling"
                or worker_os.get("verified") is not True or worker_os.get("uid")!=processing.get("filesystem_worker_uid")
                or type(worker_os.get("uid")) is not int or type(processing.get("filesystem_worker_uid")) is not int
                or worker_os.get("uid")==0
                or not exact_untrusted_denials))):
        raise UnsupportedCase()
    observation=deepcopy(processing)
    observation.update(driver="native-batch-worker-v1",actor=case["actor"],
        machine_identity_verified=processing["authorized_job_completed"],machine_scope=scope,
        native_identity={"server_verified":True,"principal":"batch-worker","roles":["BatchWorker"]},
        initiator_identity=deepcopy(initiator),semantic_success=True,authorized_effect_verified=True)
    return observation

def handling_producer_boundary_verified(raw,unauthorized_effects_unchanged):
    """Require an authenticated exact principal set, denied direct sends, and one trusted producer."""
    return (isinstance(raw,dict)
        and raw.get("anonymousDenied") is True
        and raw.get("humanAuthenticated")==[True,True,True]
        and raw.get("humanSendDenied")==[True,True,True]
        and raw.get("machinePrincipals")==["batch-worker","handling-worker","inspection-worker","notification-worker"]
        and raw.get("machineAuthenticated")==[True,True,True,True]
        and raw.get("machineSendDenied")==[True,True,True,True]
        and raw.get("trustedAllowed") is True
        and raw.get("rejectedQueueDenied") is True
        and raw.get("deliveredQueueDenied") is True
        and unauthorized_effects_unchanged is True)

def cargo_handled_producer_boundary_verified(raw, effects_unchanged):
    """Require authenticated denials and the designated HandlingWorker send grant."""
    return (isinstance(raw,dict)
        and raw.get("cargoHandledAnonymousDenied") is True
        and raw.get("cargoHandledHumanAuthenticated")==[True,True,True]
        and raw.get("cargoHandledHumanSendDenied")==[True,True,True]
        and raw.get("cargoHandledMachinePrincipals")==["batch-worker","inspection-worker","notification-worker"]
        and raw.get("cargoHandledMachineAuthenticated")==[True,True,True]
        and raw.get("cargoHandledMachineSendDenied")==[True,True,True]
        and raw.get("cargoHandledTrustedPrincipal")=="handling-worker"
        and raw.get("cargoHandledTrustedAllowed") is True
        and effects_unchanged is True)

def service_boundary_observation(case, handling_denials, inspection_denials):
    """Bind both direct worker-only service calls to the same human actor and settled effects."""
    actor=case.get("actor")
    expected_status=401 if actor=="anonymous" else 403
    handling=deepcopy(handling_denials.get(actor,{}))
    inspection=deepcopy(inspection_denials.get(actor,{}))
    if (case.get("surface_id")!="SERVICE-04" or case.get("expected")!="deny"
            or actor not in ACTORS):
        raise UnsupportedCase()
    proofs=((handling,"native-handling-worker-v1"),(inspection,"native-inspection-worker-v1"))
    fixture_id=None
    for proof,driver in proofs:
        effect=proof.get("effects",{})
        if (proof.get("driver")!=driver or proof.get("actor")!=actor
                or proof.get("supported") is not True or proof.get("status")!=expected_status
                or proof.get("invocation_denied") is not True
                or proof.get("direct_service_denied") is not True
                or proof.get("protected_payload_absent") is not True
                or proof.get("independent_effects_unchanged") is not True
                or effect.get("settled") is not True or not effect.get("fixture_id")
                or effect.get("before_fixture")!=effect.get("fixture_id")
                or effect.get("after_fixture")!=effect.get("fixture_id")):
            raise UnsupportedCase()
        before=effect.get("before",{});after=effect.get("after",{})
        if set(before)!={"database","queue","business_audit"} or before!=after:
            raise UnsupportedCase()
        if any(not isinstance(before.get(name),dict) or not before[name]
                for name in ("database","queue","business_audit")):
            raise UnsupportedCase()
        if fixture_id is None:fixture_id=effect["fixture_id"]
        elif fixture_id!=effect["fixture_id"]:raise UnsupportedCase()
        if actor=="anonymous":
            if proof.get("identity") is not None:raise UnsupportedCase()
        else:
            identity=proof.get("identity",{})
            if (identity.get("server_verified") is not True
                    or identity.get("principal")!=USERS[actor]
                    or identity.get("roles")!=[actor]):
                raise UnsupportedCase()
    first=handling["effects"];second=inspection["effects"]
    if first["after"]!=second["before"]:
        raise UnsupportedCase()
    return {"driver":"native-service-boundary-v1","actor":actor,"supported":True,
        "status":expected_status,"invocation_denied":True,"direct_service_denied":True,
        "protected_payload_absent":True,
        "identity":None if actor=="anonymous" else deepcopy(handling["identity"]),
        "operations":["HandlingEventService.registerHandlingEvent","CargoInspectionService.inspectCargo"],
        "independent_effects_unchanged":True,
        "effects":{"settled":True,"fixture_id":fixture_id,"before_fixture":fixture_id,
            "after_fixture":fixture_id,"before":first["before"],"after":second["after"]}}

def booking_service_observation(case,raw):
    actor=case.get("actor");allowed=case.get("expected")=="allow"
    methods={"bookNewCargo","assignCargoToRoute","changeDestination"}
    if (case.get("surface_id")!="SERVICE-01" or actor not in ACTORS
            or case.get("expected") not in {"allow","deny"}
            or not isinstance(raw,dict) or raw.get("driver")!="native-booking-service-v1"
            or raw.get("actor")!=actor or raw.get("supported") is not True
            or raw.get("expected")!=case.get("expected") or raw.get("semantic_success") is not True
            or raw.get("authorized_effect_verified") is not allowed
            or raw.get("invocation_denied") is allowed
            or set(raw.get("operations",{}))!=methods):
        raise UnsupportedCase()
    expected_top=403 if not allowed else 200
    if raw.get("status")!=expected_top:raise UnsupportedCase()
    if actor=="anonymous":
        if raw.get("identity") is not None:raise UnsupportedCase()
    else:
        identity=raw.get("identity",{})
        if (identity.get("server_verified") is not True
                or identity.get("principal")!=USERS[actor]
                or identity.get("roles")!=[actor]):raise UnsupportedCase()
    expected_statuses={"bookNewCargo":201,"assignCargoToRoute":204,"changeDestination":204}
    fixture_id=None
    for method,proof in raw["operations"].items():
        effect=proof.get("effects",{})
        if (proof.get("protected_payload_absent") is not True
                or effect.get("settled") is not True or not effect.get("fixture_id")
                or effect.get("before_fixture")!=effect.get("fixture_id")
                or effect.get("after_fixture")!=effect.get("fixture_id")):
            raise UnsupportedCase()
        if fixture_id is None:fixture_id=effect["fixture_id"]
        elif fixture_id!=effect["fixture_id"]:raise UnsupportedCase()
        before=effect.get("before",{});after=effect.get("after",{})
        if set(before)!={"database","queue","business_audit"} or set(after)!=set(before):raise UnsupportedCase()
        if any(not isinstance(before.get(name),dict) or not before[name]
               or not isinstance(after.get(name),dict) or not after[name]
               for name in before):raise UnsupportedCase()
        if allowed:
            deltas=proof.get("business_invocation_deltas",{})
            expected_delta={"net.java.cargotracker.application.internal.DefaultBookingService#"+method:1}
            if (proof.get("status")!=expected_statuses[method]
                    or proof.get("invocation_denied") is not False
                    or proof.get("direct_service_denied") is not False
                    or proof.get("authorized_effect_verified") is not True
                    or proof.get("independent_effects_unchanged") is not False
                    or before["database"]==after["database"]
                    or before["queue"]!=after["queue"] or deltas!=expected_delta):raise UnsupportedCase()
        else:
            if (proof.get("status")!=403 or proof.get("invocation_denied") is not True
                    or proof.get("direct_service_denied") is not True
                    or proof.get("authorized_effect_verified") is not False
                    or proof.get("independent_effects_unchanged") is not True
                    or before!=after):raise UnsupportedCase()
    return {"driver":"native-booking-service-v1","actor":actor,"supported":True,
        "status":expected_top,"semantic_success":True,"authorized_effect_verified":allowed,
        "invocation_denied":not allowed,"direct_service_denied":not allowed,
        "protected_payload_absent":True,"identity":None if actor=="anonymous" else deepcopy(raw["identity"]),
        "operations":deepcopy(raw["operations"]),
        "effects":deepcopy(raw["operations"]["bookNewCargo"]["effects"])}


def booking_routes_observation(case,raw):
    actor=case.get("actor");allowed=case.get("expected")=="allow"
    if (case.get("surface_id")!="SERVICE-02" or actor not in ACTORS
            or case.get("expected") not in {"allow","deny"}
            or not isinstance(raw,dict) or raw.get("driver")!="native-booking-routes-v1"
            or raw.get("actor")!=actor or raw.get("supported") is not True
            or raw.get("expected")!=case.get("expected") or raw.get("semantic_success") is not True
            or raw.get("authorized_effect_verified") is not allowed
            or raw.get("invocation_denied") is allowed):
        raise UnsupportedCase()
    if actor=="anonymous":
        if raw.get("identity") is not None:raise UnsupportedCase()
    else:
        identity=raw.get("identity",{})
        if (identity.get("server_verified") is not True
                or identity.get("principal")!=USERS[actor]
                or identity.get("roles")!=[actor]):raise UnsupportedCase()
    effects=raw.get("effects",{})
    if (effects.get("settled") is not True or not effects.get("fixture_id")
            or effects.get("before_fixture")!=effects.get("fixture_id")
            or effects.get("after_fixture")!=effects.get("fixture_id")):raise UnsupportedCase()
    before=effects.get("before",{});after=effects.get("after",{})
    if set(before)!={"database","queue","business_audit"} or set(after)!=set(before):raise UnsupportedCase()
    if any(not isinstance(before.get(k),dict) or not before[k]
           or not isinstance(after.get(k),dict) or not after[k] for k in before):raise UnsupportedCase()
    identity_before=raw.get("routing_identity_before",{})
    identity_after=raw.get("routing_identity_after",{})
    expected_deltas={
        "net.java.cargotracker.application.internal.DefaultBookingService#requestPossibleRoutesForCargo":1,
        "net.java.cargotracker.infrastructure.routing.ExternalRoutingService#fetchRoutesForSpecification":1,
        "net.java.pathfinder.api.GraphTraversalService#findShortestPath":1}
    if allowed:
        if (raw.get("status")!=200 or type(raw.get("route_count")) is not int or raw["route_count"]<1
                or raw.get("direct_service_denied") is not False
                or raw.get("protected_payload_absent") is not True
                or raw.get("independent_effects_unchanged") is not False
                or before["database"]!=after["database"] or before["queue"]!=after["queue"]
                or raw.get("business_invocation_deltas")!=expected_deltas
                or raw.get("routing_identity_verified") is not True
                or identity_after.get("principal")!="routing"
                or identity_after.get("roles")!=["RoutingService"]
                or identity_after.get("path")!="/rest/graph-traversal/shortest-path"
                or type(identity_after.get("sequence")) is not int
                or identity_after.get("sequence")!=identity_before.get("sequence",0)+1):
            raise UnsupportedCase()
        status=200
    else:
        if (raw.get("status")!=403 or raw.get("direct_service_denied") is not True
                or raw.get("protected_payload_absent") is not True
                or raw.get("independent_effects_unchanged") is not True
                or raw.get("routing_identity_verified") is not True
                or identity_before!=identity_after or before!=after
                or raw.get("business_invocation_deltas")!={}):
            raise UnsupportedCase()
        status=403
    return {"driver":"native-booking-routes-v1","actor":actor,"supported":True,
        "status":status,"semantic_success":True,"authorized_effect_verified":allowed,
        "invocation_denied":not allowed,"direct_service_denied":not allowed,
        "protected_payload_absent":True,"identity":None if actor=="anonymous" else deepcopy(raw["identity"]),
        "route_count":raw.get("route_count"),"business_invocation_deltas":deepcopy(raw["business_invocation_deltas"]),
        "routing_identity_verified":True,"native_routing_identity":deepcopy(identity_after),
        "independent_effects_unchanged":not allowed,"effects":deepcopy(effects)}

def booking_facade_observation(case,raw):
    actor=case.get("actor");allowed=case.get("expected")=="allow"
    if (case.get("surface_id")!="SERVICE-03" or actor not in ACTORS
            or case.get("expected") not in {"allow","deny"}
            or not isinstance(raw,dict) or raw.get("driver")!="native-booking-facade-v1"
            or raw.get("actor")!=actor or raw.get("supported") is not True
            or raw.get("expected")!=case.get("expected") or raw.get("semantic_success") is not True
            or raw.get("authorized_effect_verified") is not allowed
            or raw.get("invocation_denied") is allowed
            or set(raw.get("operations",{}))!={"read-facade","read-missing"}):
        raise UnsupportedCase()
    if actor=="anonymous":
        if raw.get("identity") is not None:raise UnsupportedCase()
    else:
        identity=raw.get("identity",{})
        if (identity.get("server_verified") is not True
                or identity.get("principal")!=USERS[actor]
                or identity.get("roles")!=[actor]):raise UnsupportedCase()
    for name,proof in raw["operations"].items():
        effect=proof.get("effects",{})
        if (not isinstance(effect,dict) or effect.get("settled") is not True
                or not effect.get("fixture_id")
                or effect.get("before_fixture")!=effect.get("fixture_id")
                or effect.get("after_fixture")!=effect.get("fixture_id")
                or proof.get("protected_payload_absent") is not (not allowed or name=="read-missing")
                or proof.get("effects_unchanged") is not True):
            raise UnsupportedCase()
        before=effect.get("before",{});after=effect.get("after",{})
        if set(before)!={"database","queue","business_audit"} or set(after)!=set(before):
            raise UnsupportedCase()
        if before!=after:raise UnsupportedCase()
    first=raw["operations"]["read-facade"];missing=raw["operations"]["read-missing"]
    if allowed:
        counts=raw.get("list_counts",{})
        if (raw.get("status")!=200 or first.get("status")!=200
                or missing.get("status")!=404
                or raw.get("direct_service_denied") is not False
                or raw.get("read_effects_unchanged") is not True
                or raw.get("selected_tracking_id")!="ABC123"
                or any(type(counts.get(k)) is not int or counts[k]<1 for k in ("voyages","locations","cargos"))
                or type(counts.get("handling_events")) is not int or counts["handling_events"]<1):
            raise UnsupportedCase()
        status=200
    else:
        if (raw.get("status")!=403 or first.get("status")!=403 or missing.get("status")!=403
                or raw.get("direct_service_denied") is not True
                or raw.get("read_effects_unchanged") is not True
                or raw.get("selected_tracking_id") is not None
                or raw.get("list_counts")!={"voyages":None,"locations":None,"cargos":None,"handling_events":None}):
            raise UnsupportedCase()
        status=403
    return {"driver":"native-booking-facade-v1","actor":actor,"supported":True,
        "status":status,"semantic_success":True,"authorized_effect_verified":allowed,
        "invocation_denied":not allowed,"direct_service_denied":not allowed,
        "protected_payload_absent":not allowed,"identity":None if actor=="anonymous" else deepcopy(raw["identity"]),
        "missing_status":missing["status"],"selected_tracking_id":raw.get("selected_tracking_id"),
        "list_counts":deepcopy(raw.get("list_counts")),"read_effects_unchanged":True,
        "operations":deepcopy(raw["operations"])}


def load_model():
    raw=INVENTORY.read_bytes();inventory=json.loads(raw);model=json.loads(MANIFEST.read_text())
    validate_model(model,inventory,hashlib.sha256(raw).hexdigest())
    return model,inventory

def reviewed_handling_callback_retirement_receipt():
    """Verify the separately reviewed promotion against immutable run evidence."""
    try:
        validation_bytes=HANDLING_CALLBACK_PROMOTION_VALIDATION.read_bytes()
        review_bytes=HANDLING_CALLBACK_PROMOTION_REVIEW.read_bytes()
        gate_bytes=HANDLING_CALLBACK_GATE_EVIDENCE.read_bytes()
        candidate_bytes=HANDLING_CALLBACK_CANDIDATE_EVIDENCE.read_bytes()
        browser_bytes=HANDLING_CALLBACK_BROWSER_EVIDENCE.read_bytes()
        capture=load_handling_callback_source_evidence()
        hashes=(hashlib.sha256(validation_bytes).hexdigest(),hashlib.sha256(review_bytes).hexdigest(),
                hashlib.sha256(gate_bytes).hexdigest(),hashlib.sha256(candidate_bytes).hexdigest(),
                hashlib.sha256(browser_bytes).hexdigest())
        if hashes!=(HANDLING_CALLBACK_PROMOTION_VALIDATION_SHA256,HANDLING_CALLBACK_PROMOTION_REVIEW_SHA256,
                    HANDLING_CALLBACK_GATE_SHA256,HANDLING_CALLBACK_CANDIDATE_SHA256,HANDLING_CALLBACK_BROWSER_SHA256):return False
        receipt=json.loads(validation_bytes);gate=json.loads(gate_bytes)
        candidate=json.loads(candidate_bytes);browser=json.loads(browser_bytes)
        actions=list(HANDLING_CALLBACK_RETIREMENT_ACTIONS)
        if (receipt.get("task")!="KAN-15 handling callback retirement promotion review receipt"
                or receipt.get("status")!="APPROVED" or receipt.get("reviewer")!="/root/review_kan15_callback_final"
                or receipt.get("review_record")!="notes/agent-reviews/2026-11-17-kan15-handling-callback-promotion-review.md"
                or receipt.get("review_record_sha256")!=HANDLING_CALLBACK_PROMOTION_REVIEW_SHA256
                or receipt.get("gate_evidence_sha256")!=HANDLING_CALLBACK_GATE_SHA256
                or receipt.get("candidate_report_sha256")!=HANDLING_CALLBACK_CANDIDATE_SHA256
                or receipt.get("browser_report_sha256")!=HANDLING_CALLBACK_BROWSER_SHA256
                or receipt.get("legacy_capture_sha256")!=HANDLING_CALLBACK_CAPTURE_SHA256
                or receipt.get("actions")!=actions or receipt.get("actors")!=ACTORS
                or receipt.get("replacement_groups")!=HANDLING_CALLBACK_RETIREMENT_ACTIONS
                or receipt.get("candidate_checks")!=777 or receipt.get("browser_checks")!=958
                or receipt.get("browser_failures")!=0 or receipt.get("fixture_cleanup_verified") is not True
                or receipt.get("current_counts_before_promotion")!={"PASS":470}
                or receipt.get("retirement_counts_before_promotion")!={"RETIRED":44,"BLOCKED":32}
                or receipt.get("retirement_counts_after_promotion")!={"RETIRED":64,"BLOCKED":12}
                or receipt.get("rows_promoted")!=20 or receipt.get("other_retirement_rows_unchanged")!=56
                or receipt.get("pass_outcome_allowed") is not False or receipt.get("gate_exit_after_promotion")!=2):return False
        expected_actions=list(HANDLING_CALLBACK_RETIREMENT_ACTIONS)
        candidate_checks=candidate.get("checks",[]);browser_checks=browser.get("checks",[])
        if (candidate.get("status")!="PASS" or candidate.get("count")!=777 or len(candidate_checks)!=777
                or any(row.get("passed") is not True for row in candidate_checks)
                or len(candidate.get("handling_callback_retirement_observations",{}))!=20
                or len(browser_checks)!=958 or any(row.get("passed") is not True for row in browser_checks)
                or gate.get("execution")!="fresh-owned-runtime" or gate.get("current_counts")!={"PASS":470}
                or gate.get("retirement_counts")!={"RETIRED":44,"BLOCKED":32} or gate.get("gate_exit")!=2
                or gate.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or gate.get("provenance",{}).get("kind")!="fresh-owned-runtime"):
            return False
        if len(gate.get("retirement_results",[]))!=76 or any(row.get("outcome")=="PASS" for row in gate["retirement_results"]):return False
        observations=candidate["handling_callback_retirement_observations"]
        gate_observations=gate.get("retirement_observations",{})
        browser_retirements=browser.get("handling_callback_retirements",{})
        expected_keys={"RETIREMENT::"+action+"::"+actor for action in expected_actions for actor in ACTORS}
        if set(observations)!=expected_keys:return False
        for action in expected_actions:
            for actor in ACTORS:
                key="RETIREMENT::"+action+"::"+actor
                browser_actor=browser_retirements.get(actor,{})
                browser_callback=next((item for item in browser_actor.get("callbacks",[]) if item.get("legacy_id")==action),None)
                if key not in gate_observations or gate_observations[key]!=observations[key] or not isinstance(browser_callback,dict):return False
                proof=observations[key]
                if (browser_callback.get("submitted_shape_matches") is not True
                        or browser_callback.get("submitted_callback_value")!=proof.get("submitted_callback_value")
                        or browser_callback.get("response_status")!=proof.get("response_status")
                        or browser_callback.get("post_target_verified") is not True
                        or browser_callback.get("protected_payload_absent") is not True):return False
        replacement_rows={row.get("case"):row for row in gate.get("current_results",[]) if row.get("case","").startswith("REPLACEMENT::")}
        retirement_rows={row.get("case"):row for row in gate["retirement_results"]}
        for action in expected_actions:
            for actor in ACTORS:
                key="RETIREMENT::"+action+"::"+actor
                before=retirement_rows.get(key,{})
                proof=observations.get(key)
                if (before.get("outcome")!="BLOCKED" or before.get("specific_negative_entry_verified") is not True
                        or replacement_rows.get("REPLACEMENT::"+HANDLING_CALLBACK_RETIREMENT_ACTIONS[action]+"::"+actor,{}).get("outcome")!="PASS"):
                    return False
                verify_handling_callback_retirement_proof(action,actor,proof)
        return hashlib.sha256(HANDLING_CALLBACK_PROMOTION_REVIEW.read_bytes()).hexdigest()==HANDLING_CALLBACK_PROMOTION_REVIEW_SHA256
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):
        return False

def reviewed_handling_page_retirement_receipt():
    """Validate independent approval and all source-bound ACTION-35/40 run receipts."""
    try:
        validation_bytes=HANDLING_PAGE_PROMOTION_VALIDATION.read_bytes()
        review_bytes=HANDLING_PAGE_PROMOTION_REVIEW.read_bytes()
        gate_bytes=HANDLING_PAGE_GATE_EVIDENCE.read_bytes()
        candidate_bytes=HANDLING_PAGE_CANDIDATE_EVIDENCE.read_bytes()
        browser_bytes=HANDLING_PAGE_BROWSER_EVIDENCE.read_bytes()
        hashes=tuple(hashlib.sha256(value).hexdigest() for value in
            (validation_bytes,review_bytes,gate_bytes,candidate_bytes,browser_bytes))
        if hashes!=(HANDLING_PAGE_PROMOTION_VALIDATION_SHA256,HANDLING_PAGE_PROMOTION_REVIEW_SHA256,
                    HANDLING_PAGE_GATE_SHA256,HANDLING_PAGE_CANDIDATE_SHA256,HANDLING_PAGE_BROWSER_SHA256):return False
        receipt=json.loads(validation_bytes);review=review_bytes.decode();gate=json.loads(gate_bytes)
        candidate=json.loads(candidate_bytes);browser=json.loads(browser_bytes)
        actions=list(HANDLING_PAGE_RETIREMENT_ACTIONS);selected={"RETIREMENT::"+action+"::"+actor for action in actions for actor in ACTORS}
        if (receipt.get("task")!="KAN-15 handling page retirement promotion review receipt"
                or receipt.get("status")!="APPROVED" or receipt.get("reviewer")!="/root/review_kan15_handling_page"
                or receipt.get("review_record")!=str(HANDLING_PAGE_PROMOTION_REVIEW.relative_to(ROOT))
                or receipt.get("review_record_sha256")!=HANDLING_PAGE_PROMOTION_REVIEW_SHA256
                or receipt.get("gate_evidence_sha256")!=HANDLING_PAGE_GATE_SHA256
                or receipt.get("candidate_report_sha256")!=HANDLING_PAGE_CANDIDATE_SHA256
                or receipt.get("browser_report_sha256")!=HANDLING_PAGE_BROWSER_SHA256
                or receipt.get("run_id")!="kan15-handling-pages-d" or receipt.get("actions")!=actions
                or receipt.get("actors")!=ACTORS or receipt.get("replacement_groups")!=HANDLING_PAGE_RETIREMENT_ACTIONS
                or receipt.get("candidate_checks")!=777 or receipt.get("browser_checks")!=970
                or receipt.get("browser_failures")!=0 or receipt.get("fixture_cleanup_verified") is not True
                or receipt.get("current_counts_before_promotion")!={"PASS":470}
                or receipt.get("retirement_counts_before_promotion")!={"RETIRED":64,"BLOCKED":12}
                or receipt.get("retirement_counts_after_promotion")!={"RETIRED":72,"BLOCKED":4}
                or receipt.get("rows_promoted")!=8 or receipt.get("other_retirement_rows_unchanged")!=68
                or receipt.get("pass_outcome_allowed") is not False or receipt.get("gate_exit_after_promotion")!=2
                or "cross-origin" not in review or "wrong-context" not in review):return False
        candidate_checks=candidate.get("checks",[]);browser_checks=browser.get("checks",[])
        if (candidate.get("status")!="PASS" or candidate.get("count")!=777 or len(candidate_checks)!=777
                or any(row.get("passed") is not True for row in candidate_checks)
                or len(browser_checks)!=970 or any(row.get("passed") is not True for row in browser_checks)
                or gate.get("execution")!="fresh-owned-runtime" or gate.get("current_counts")!={"PASS":470}
                or gate.get("retirement_counts")!={"RETIRED":64,"BLOCKED":12} or gate.get("gate_exit")!=2
                or gate.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or gate.get("provenance",{}).get("kind")!="fresh-owned-runtime"):
            return False
        rows=gate.get("retirement_results",[])
        if len(rows)!=76 or any(row.get("outcome")=="PASS" for row in rows):return False
        selected_rows={row.get("case"):row for row in rows if row.get("case") in selected}
        if set(selected_rows)!=selected or any(row.get("outcome")!="BLOCKED" or row.get("specific_negative_entry_verified") is not True for row in selected_rows.values()):return False
        replacements={row.get("case"):row for row in gate.get("current_results",[]) if row.get("case","").startswith("REPLACEMENT::")}
        observations=gate.get("retirement_observations",{});browser_observations=browser.get("retirement_actions",{})
        if set(observations)&selected!=selected or set(browser_observations)&selected!=selected:return False
        for action in actions:
            for actor in ACTORS:
                key="RETIREMENT::"+action+"::"+actor
                proof=observations.get(key)
                if (browser_observations.get(key)!=proof
                        or replacements.get("REPLACEMENT::"+HANDLING_PAGE_RETIREMENT_ACTIONS[action]+"::"+actor,{}).get("outcome")!="PASS"):
                    return False
                verify_handling_page_retirement_proof(action,actor,proof)
        review_hash=hashlib.sha256(HANDLING_PAGE_PROMOTION_REVIEW.read_bytes()).hexdigest()
        return review_hash==HANDLING_PAGE_PROMOTION_REVIEW_SHA256
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):
        return False


def reviewed_action08_retirement_receipt():
    try:
        raw=ACTION08_RETIREMENT_VALIDATION.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ACTION08_RETIREMENT_VALIDATION_SHA256:
            return False
        receipt=json.loads(raw)
        review=receipt["review"]
        if (receipt.get("task")!="KAN-15 ACTION-08 specific retired-entry evidence"
                or receipt.get("candidate",{}).get("legacy_id")!="ACTION-08"
                or receipt.get("candidate",{}).get("replacement_id")!="cancel-editor"
                or review.get("status")!="APPROVED"
                or review.get("reviewer")!="/root/review_service04_adapter"
                or review.get("approved_outcome")!="RETIRED"
                or review.get("pass_outcome_allowed") is not False
                or review.get("review_record")!="notes/agent-reviews/2026-11-14-kan15-action08-retirement-review.md"
                or review.get("review_record_sha256")!=ACTION08_RETIREMENT_REVIEW_SHA256
                or hashlib.sha256(ACTION08_RETIREMENT_REVIEW.read_bytes()).hexdigest()!=ACTION08_RETIREMENT_REVIEW_SHA256):
            return False
        basis=receipt.get("basis",{})
        cleanup=basis.get("cleanup",{})
        browser=cleanup.get("browser",{})
        if (basis.get("fixture_status")!="PASS" or basis.get("native_checks")!=780
                or basis.get("browser_checks")!=841 or cleanup.get("native_container_removed") is not True
                or cleanup.get("private_files_removed") is not True or browser.get("container_removed") is not True
                or browser.get("network_removed") is not True or browser.get("errors")!=[]
                or basis.get("effective_current_counts")!={"PASS":470,"BLOCKED":0}
                or basis.get("raw_results_sha256")!=ACTION08_RAW_RESULTS_SHA256):
            return False
        required={"replacement_per_actor","specific_negative_entry","native_role_session",
                  "no_protected_payload","required_independent_effects","independent_review"}
        if set(receipt.get("required_evidence",{}))!=required:
            return False
        actors=receipt.get("actor_observations",[])
        by_actor={row.get("actor"):row for row in actors if isinstance(row,dict)}
        if set(by_actor)!=set(ACTORS) or len(actors)!=4:
            return False
        statuses={"anonymous":303,"Reader":403,"Operator":200,"Administrator":200}
        for actor,proof in by_actor.items():
            if (proof.get("source_status")!=statuses[actor]
                    or proof.get("source_path") is None
                    or re.fullmatch(r"/cargo-tracker/admin/changeDestination\.xhtml\?trackingId=[A-Z0-9]{8}",proof["source_path"]) is None
                    or proof.get("historical_source_component_id")!="j_idt8:j_idt23"
                    or proof.get("callback_implementation_absent") is not True
                    or proof.get("post_target_verified") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or proof.get("replacement_case_id")!="REPLACEMENT::cancel-editor::"+actor
                    or proof.get("replacement_outcome")!="PASS"
                    or proof.get("proof_sha256")!=ACTION08_PROOF_SHA256[actor]):
                return False
            if actor in {"anonymous","Reader"}:
                if proof.get("authorization_denied") is not True or proof.get("protected_payload_absent") is not True:
                    return False
                if actor=="anonymous":
                    if proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:
                        return False
                else:
                    identity=proof.get("identity",{})
                    if proof.get("source_status")!=403 or identity.get("server_verified") is not True or identity.get("principal")!="reader" or identity.get("roles")!=["Reader"]:
                        return False
            else:
                identity=proof.get("identity",{})
                principal="operator" if actor=="Operator" else "admin"
                if (identity.get("server_verified") is not True or identity.get("principal")!=principal
                        or identity.get("roles")!=[actor] or proof.get("current_form_verified") is not True
                        or proof.get("csrf_present") is not True or proof.get("viewstate_present") is not True
                        or proof.get("callback_response_absent") is not True):
                    return False
        return True
    except (OSError,KeyError,TypeError,ValueError):
        return False


def reviewed_action23_retirement_receipt():
    try:
        raw=ACTION23_RETIREMENT_VALIDATION.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ACTION23_RETIREMENT_VALIDATION_SHA256:return False
        receipt=json.loads(raw);review=receipt["review"];basis=receipt["basis"]
        review_bytes=ACTION23_RETIREMENT_REVIEW.read_bytes()
        evidence_bytes=ACTION23_FRESH_EVIDENCE.read_bytes()
        if (hashlib.sha256(review_bytes).hexdigest()!=ACTION23_RETIREMENT_REVIEW_SHA256
                or review.get("status")!="APPROVED" or review.get("reviewer")!="/root/review_action23_driver"
                or review.get("approved_outcome")!="RETIRED" or review.get("pass_outcome_allowed") is not False
                or review.get("review_record")!="notes/agent-reviews/2026-11-15-kan15-action23-retirement-review.md"
                or review.get("review_record_sha256")!=ACTION23_RETIREMENT_REVIEW_SHA256
                or receipt.get("task")!="KAN-15 ACTION-23 specific retired-entry evidence"
                or receipt.get("candidate",{}).get("legacy_id")!="ACTION-23"
                or receipt.get("candidate",{}).get("replacement_id")!="tracking-discovery"
                or hashlib.sha256(evidence_bytes).hexdigest()!=ACTION23_FRESH_EVIDENCE_SHA256
                or basis.get("fresh_evidence_sha256")!=ACTION23_FRESH_EVIDENCE_SHA256
                or basis.get("fixture_status")!="PASS" or basis.get("browser_checks")!=777
                or basis.get("effective_current_counts")!={"PASS":470}
                or basis.get("pre_review_retirement_counts")!={"RETIRED":4,"BLOCKED":72}
                or basis.get("pre_review_gate_exit")!=2
                or basis.get("legacy_fixture_cleanup_verified") is not True
                or basis.get("imported_code_attested") is not False):
            return False
        evidence=json.loads(evidence_bytes)
        if (evidence.get("provenance",{}).get("kind")!="fresh-owned-runtime"
                or evidence.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or evidence.get("current_counts")!={"PASS":470}
                or evidence.get("retirement_counts")!={"RETIRED":4,"BLOCKED":72}
                or evidence.get("gate_exit")!=2):
            return False
        source_hashes=action23_source_hashes()
        if basis.get("source_hashes")!=source_hashes:return False
        proof_map=evidence.get("retirement_observations",{})
        actors=receipt.get("actor_observations",[])
        by_actor={row.get("actor"):row for row in actors if isinstance(row,dict)}
        if set(by_actor)!=set(ACTORS) or len(actors)!=4:return False
        snapshot_hash=None
        for actor in ACTORS:
            proof=proof_map.get("RETIREMENT::ACTION-23::"+actor,{})
            row=by_actor[actor]
            canonical=json.dumps(proof,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
            expected_status=303 if actor=="anonymous" else 200
            if (row.get("proof_sha256")!=hashlib.sha256(canonical).hexdigest()
                    or row.get("replacement_case_id")!="REPLACEMENT::tracking-discovery::"+actor
                    or row.get("replacement_outcome")!="PASS"
                    or proof.get("driver")!="browser-retired-tracking-v1" or proof.get("legacy_id")!="ACTION-23"
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!="/cargo-tracker/admin/track.xhtml"
                    or proof.get("historical_source_component_id")!="trackingForm:trackIdInput"
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("response_status")!=expected_status or proof.get("post_target_verified") is not True
                    or proof.get("callback_implementation_absent") is not True
                    or proof.get("legacy_binding_discrepancy_verified") is not True
                    or proof.get("source_hashes")!=source_hashes
                    or proof.get("callback_response_absent") is not True
                    or proof.get("autocomplete_payload_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13):
                return False
            if snapshot_hash is None:snapshot_hash=proof["cargo_snapshot_sha256"]
            elif snapshot_hash!=proof["cargo_snapshot_sha256"]:return False
            if actor=="anonymous":
                if proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:return False
            else:
                identity=proof.get("identity",{})
                if (proof.get("authorization_denied") is not False
                        or proof.get("current_source_parameter")!="jakarta.faces.source"
                        or proof.get("current_form_verified") is not True
                        or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True
                        or proof.get("current_legacy_component_absent") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor]
                        or identity.get("roles")!=[actor]):
                    return False
        return True
    except (OSError,KeyError,TypeError,ValueError):
        return False




def reviewed_action26_retirement_receipt():
    try:
        raw=ACTION26_RETIREMENT_VALIDATION.read_bytes(); evidence_bytes=ACTION26_FRESH_EVIDENCE.read_bytes(); review_bytes=ACTION26_RETIREMENT_REVIEW.read_bytes()
        if (hashlib.sha256(raw).hexdigest()!=ACTION26_RETIREMENT_VALIDATION_SHA256
                or hashlib.sha256(evidence_bytes).hexdigest()!=ACTION26_FRESH_EVIDENCE_SHA256
                or hashlib.sha256(review_bytes).hexdigest()!=ACTION26_RETIREMENT_REVIEW_SHA256):return False
        receipt=json.loads(raw);evidence=json.loads(evidence_bytes);basis=receipt["basis"];review=receipt["review"]
        if (receipt.get("task")!="KAN-15 ACTION-26 specific retired-entry evidence"
                or receipt.get("candidate",{}).get("legacy_id")!="ACTION-26"
                or receipt.get("candidate",{}).get("replacement_id")!="booking-deadline"
                or basis.get("fresh_evidence_sha256")!=ACTION26_FRESH_EVIDENCE_SHA256
                or basis.get("fixture_status")!="PASS" or basis.get("browser_checks")!=777
                or basis.get("effective_current_counts")!={"PASS":470}
                or basis.get("pre_review_retirement_counts")!={"RETIRED":12,"BLOCKED":64}
                or basis.get("pre_review_gate_exit")!=2 or basis.get("legacy_fixture_cleanup_verified") is not True
                or basis.get("imported_code_attested") is not False
                or evidence.get("provenance",{}).get("kind")!="fresh-owned-runtime"
                or evidence.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or evidence.get("current_counts")!={"PASS":470}
                or evidence.get("retirement_counts")!={"RETIRED":12,"BLOCKED":64}
                or evidence.get("gate_exit")!=2
                or review.get("status")!="APPROVED" or review.get("reviewer")!="/root/review_action23_driver"
                or review.get("approved_outcome")!="RETIRED" or review.get("pass_outcome_allowed") is not False
                or review.get("review_record")!="notes/agent-reviews/2026-11-15-kan15-action26-retirement-review.md"
                or review.get("review_record_sha256")!=ACTION26_RETIREMENT_REVIEW_SHA256
                or basis.get("source_hashes")!=action26_source_hashes()):return False
        proof_map=evidence.get("retirement_observations",{});rows=receipt.get("actor_observations",[])
        by_actor={row.get("actor"):row for row in rows if isinstance(row,dict)}
        if set(by_actor)!=set(ACTORS) or len(rows)!=4:return False
        snapshot=None
        for actor in ACTORS:
            proof=proof_map.get("RETIREMENT::ACTION-26::"+actor,{});row=by_actor[actor]
            canonical=json.dumps(proof,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
            replacement=next((x for x in evidence.get("current_results",[]) if x.get("case")=="REPLACEMENT::booking-deadline::"+actor),{})
            if (row.get("proof_sha256")!=hashlib.sha256(canonical).hexdigest()
                    or row.get("replacement_case_id")!="REPLACEMENT::booking-deadline::"+actor
                    or row.get("replacement_outcome")!="PASS" or replacement.get("outcome")!="PASS"
                    or proof.get("driver")!="browser-retired-deadline-v1" or proof.get("legacy_id")!="ACTION-26"
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!="/cargo-tracker/booking/booking-date.xhtml"
                    or proof.get("historical_source_component_id")!="dateForm:deadline"
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("source_hashes")!=action26_source_hashes()
                    or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):return False
            if actor=="anonymous":
                if (proof.get("response_status")!=303 or proof.get("authorization_denied") is not True
                        or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None):return False
            elif actor=="Reader":
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=403 or proof.get("authorization_denied") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):return False
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("authorization_denied") is not False
                        or proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):return False
            if snapshot is None:snapshot=proof["cargo_snapshot_sha256"]
            elif snapshot!=proof["cargo_snapshot_sha256"]:return False
        return True
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):
        return False

def reviewed_action32_retirement_receipt():
    try:
        raw=ACTION32_RETIREMENT_VALIDATION.read_bytes();evidence_bytes=ACTION32_FRESH_EVIDENCE.read_bytes();review_bytes=ACTION32_RETIREMENT_REVIEW.read_bytes()
        if (hashlib.sha256(raw).hexdigest()!=ACTION32_RETIREMENT_VALIDATION_SHA256
                or hashlib.sha256(evidence_bytes).hexdigest()!=ACTION32_FRESH_EVIDENCE_SHA256
                or hashlib.sha256(review_bytes).hexdigest()!=ACTION32_RETIREMENT_REVIEW_SHA256):return False
        receipt=json.loads(raw);evidence=json.loads(evidence_bytes);basis=receipt["basis"];review=receipt["review"]
        rendered=action32_render_record()
        if (receipt.get("task")!="KAN-15 ACTION-32 specific retired-entry evidence"
                or receipt.get("candidate",{}).get("legacy_id")!="ACTION-32"
                or receipt.get("candidate",{}).get("replacement_id")!="booking-deadline"
                or basis.get("fresh_evidence_sha256")!=ACTION32_FRESH_EVIDENCE_SHA256
                or basis.get("render_evidence_sha256")!=ACTION32_RENDER_EVIDENCE_SHA256
                or basis.get("fixture_status")!="PASS" or basis.get("native_checks")!=777 or basis.get("browser_checks")!=848
                or basis.get("native_results_sha256")!=ACTION32_NATIVE_RESULTS_SHA256
                or basis.get("browser_results_sha256")!=ACTION32_BROWSER_RESULTS_SHA256
                or hashlib.sha256(ACTION32_NATIVE_RESULTS.read_bytes()).hexdigest()!=ACTION32_NATIVE_RESULTS_SHA256
                or hashlib.sha256(ACTION32_BROWSER_RESULTS.read_bytes()).hexdigest()!=ACTION32_BROWSER_RESULTS_SHA256
                or basis.get("effective_current_counts")!={"PASS":470}
                or basis.get("pre_review_retirement_counts")!={"RETIRED":16,"BLOCKED":60}
                or basis.get("pre_review_gate_exit")!=2 or basis.get("legacy_fixture_cleanup_verified") is not True
                or basis.get("imported_code_attested") is not False
                or evidence.get("provenance",{}).get("kind")!="fresh-owned-runtime"
                or evidence.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or evidence.get("current_counts")!={"PASS":470}
                or evidence.get("retirement_counts")!={"RETIRED":16,"BLOCKED":60}
                or evidence.get("gate_exit")!=2 or review.get("status")!="APPROVED"
                or review.get("reviewer")!="/root/review_action32_evidence"
                or review.get("approved_outcome")!="RETIRED" or review.get("pass_outcome_allowed") is not False
                or review.get("review_record")!="notes/agent-reviews/2026-11-15-kan15-action32-retirement-review.md"
                or review.get("review_record_sha256")!=ACTION32_RETIREMENT_REVIEW_SHA256
                or basis.get("source_hashes")!=action32_source_hashes()):return False
        proof_map=evidence.get("retirement_observations",{});rows=receipt.get("actor_observations",[])
        by_actor={row.get("actor"):row for row in rows if isinstance(row,dict)}
        if set(by_actor)!=set(ACTORS) or len(rows)!=4:return False
        snapshot=None
        for actor in ACTORS:
            proof=proof_map.get("RETIREMENT::ACTION-32::"+actor,{});row=by_actor[actor]
            canonical=json.dumps(proof,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
            replacement=next((x for x in evidence.get("current_results",[]) if x.get("case")=="REPLACEMENT::booking-deadline::"+actor),{})
            if (row.get("proof_sha256")!=hashlib.sha256(canonical).hexdigest()
                    or row.get("replacement_case_id")!="REPLACEMENT::booking-deadline::"+actor
                    or row.get("replacement_outcome")!="PASS" or replacement.get("outcome")!="PASS"
                    or proof.get("driver")!="browser-retired-destination-next-v1" or proof.get("legacy_id")!="ACTION-32"
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!="/cargo-tracker/booking/booking-destination.xhtml"
                    or proof.get("historical_source_component_id")!=rendered["component_id"]
                    or proof.get("historical_submitted_parameter")!=rendered["component_id"]
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=rendered["button_markup_sha256"]
                    or proof.get("source_hashes")!=action32_source_hashes()
                    or proof.get("current_post_handler_absent") is not True or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):return False
            if snapshot is None:snapshot=proof["cargo_snapshot_sha256"]
            elif snapshot!=proof["cargo_snapshot_sha256"]:return False
            if actor=="anonymous":
                if proof.get("response_status")!=303 or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:return False
            elif actor=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:return False
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("authorization_denied") is not False
                        or proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True or identity.get("server_verified") is not True
                        or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):return False
        return True
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):
        return False

def action273034_source_hashes():
    paths={"legacy_booking_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking.xhtml",
           "legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
           "legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    return {key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in paths.items()}

def reviewed_action273034_retirement_receipt():
    try:
        validation_bytes=ACTION273034_PROMOTION_VALIDATION.read_bytes()
        evidence_bytes=ACTION273034_CANDIDATE_EVIDENCE.read_bytes()
        browser_bytes=ACTION273034_BROWSER_RESULTS.read_bytes()
        render_bytes=ACTION273034_RENDER_EVIDENCE.read_bytes()
        review_bytes=ACTION273034_PROMOTION_REVIEW.read_bytes()
        if (hashlib.sha256(validation_bytes).hexdigest()!=ACTION273034_PROMOTION_VALIDATION_SHA256
                or hashlib.sha256(evidence_bytes).hexdigest()!=ACTION273034_CANDIDATE_EVIDENCE_SHA256
                or hashlib.sha256(browser_bytes).hexdigest()!=ACTION273034_BROWSER_RESULTS_SHA256
                or hashlib.sha256(render_bytes).hexdigest()!=ACTION273034_RENDER_EVIDENCE_SHA256
                or hashlib.sha256(review_bytes).hexdigest()!=ACTION273034_PROMOTION_REVIEW_SHA256):return False
        receipt=json.loads(validation_bytes);evidence=json.loads(evidence_bytes);browser=json.loads(browser_bytes)
        render=json.loads(render_bytes)
        if (receipt.get("task")!="KAN-15 ACTION-27/30/34 mapping promotion review receipt"
                or receipt.get("status")!="APPROVED" or receipt.get("reviewer")!="/root/review_current_capability_gate"
                or receipt.get("review_record")!="notes/agent-reviews/2026-11-16-kan15-actions273034-mapping-promotion-review.md"
                or receipt.get("review_record_sha256")!=ACTION273034_PROMOTION_REVIEW_SHA256
                or receipt.get("approved_outcome")!="RETIRED" or receipt.get("pass_outcome_allowed") is not False
                or receipt.get("actions")!=["ACTION-27","ACTION-30","ACTION-34"]
                or receipt.get("replacement_group")!="booking-single-page"
                or receipt.get("candidate_evidence_sha256")!=ACTION273034_CANDIDATE_EVIDENCE_SHA256
                or receipt.get("browser_results_sha256")!=ACTION273034_BROWSER_RESULTS_SHA256
                or receipt.get("legacy_render_evidence_sha256")!=ACTION273034_RENDER_EVIDENCE_SHA256
                or receipt.get("evidence_review_validation_sha256")!=hashlib.sha256((ROOT/"notes/evidence/kan-15-action273034-retirement/review-validation.json").read_bytes()).hexdigest()
                or receipt.get("browser_checks")!=872 or receipt.get("browser_failures")!=0
                or receipt.get("candidate_counts")!={"PASS":470}
                or receipt.get("retirement_counts_before_promotion")!={"RETIRED":20,"BLOCKED":56}
                or receipt.get("retirement_counts_after_promotion")!={"RETIRED":32,"BLOCKED":44}
                or receipt.get("fixture_cleanup_verified") is not True or receipt.get("actions_promoted") is not True
                or evidence.get("provenance",{}).get("kind")!="fresh-owned-runtime"
                or evidence.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or evidence.get("current_counts")!={"PASS":470}
                or evidence.get("retirement_counts")!={"RETIRED":20,"BLOCKED":56}
                or evidence.get("gate_exit")!=2 or render.get("source_hashes")!=action273034_source_hashes()):
            return False
        checks=browser.get("checks",[])
        if len(checks)!=872 or any(row.get("passed") is not True for row in checks):return False
        check_names={row.get("name") for row in checks}
        expected_checks={action+" rendered booking wizard action denied or inert "+actor
                         for action in ("ACTION-27","ACTION-30","ACTION-34") for actor in ACTORS}
        if not expected_checks.issubset(check_names):return False
        expected={"ACTION-27":{"source":"/cargo-tracker/booking/booking-date.xhtml","component":"dateForm:j_idt37"},
                  "ACTION-30":{"source":"/cargo-tracker/booking/booking-destination.xhtml","component":"j_idt29:j_idt35"},
                  "ACTION-34":{"source":"/cargo-tracker/booking/booking.xhtml","component":"j_idt29:j_idt36"}}
        proofs=evidence.get("retirement_observations",{});browser_proofs=browser.get("retirement_actions",{})
        current=evidence.get("current_results",[]);retirements=evidence.get("retirement_results",[])
        snapshot=None
        for action,identity in expected.items():
            obs=render.get("observations",{}).get(action,{})
            for actor in ACTORS:
                key="RETIREMENT::"+action+"::"+actor
                proof=proofs.get(key,{});raw=browser_proofs.get(key,{})
                replacement=next((row for row in current if row.get("case")=="REPLACEMENT::booking-single-page::"+actor),{})
                retirement=next((row for row in retirements if row.get("case")==key),{})
                status=303 if actor=="anonymous" else 403 if actor=="Reader" else 405
                if (replacement.get("outcome")!="PASS" or retirement.get("outcome")!="BLOCKED"
                        or retirement.get("specific_negative_entry_verified") is not True
                        or proof.get("driver")!="browser-retired-booking-wizard-v1" or proof.get("legacy_id")!=action
                        or proof.get("actor")!=actor or proof.get("method")!="POST" or proof.get("source_path")!=identity["source"]
                        or proof.get("historical_source_component_id")!=identity["component"]
                        or proof.get("historical_submitted_parameter")!=identity["component"]
                        or proof.get("historical_render_evidence_verified") is not True
                        or proof.get("historical_button_markup_sha256")!=obs.get("button_markup_sha256")
                        or proof.get("source_hashes")!=render.get("source_hashes")
                        or proof.get("response_status")!=status or proof.get("post_target_verified") is not True
                        or proof.get("callback_response_absent") is not True or proof.get("protected_payload_absent") is not True
                        or proof.get("independent_effects_unchanged") is not True
                        or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                        or proof.get("cargo_snapshot_sha256")!=raw.get("cargo_snapshot_sha256")):return False
                if snapshot is None:snapshot=proof["cargo_snapshot_sha256"]
                elif snapshot!=proof["cargo_snapshot_sha256"]:return False
                if actor=="anonymous":
                    if proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:return False
                elif actor=="Reader":
                    identity_proof=proof.get("identity",{})
                    if proof.get("authorization_denied") is not True or identity_proof.get("server_verified") is not True or identity_proof.get("principal")!=USERS[actor] or identity_proof.get("roles")!=[actor]:return False
                else:
                    identity_proof=proof.get("identity",{})
                    if (proof.get("authorization_denied") is not False or proof.get("current_form_verified") is not True
                            or proof.get("current_csrf_present") is not True or proof.get("current_viewstate_present") is not True
                            or identity_proof.get("server_verified") is not True or identity_proof.get("principal")!=USERS[actor]
                            or identity_proof.get("roles")!=[actor]):return False
        return True
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):
        return False

def action283133_source_hashes():
    paths={"legacy_booking_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking.xhtml",
           "legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
           "legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    return {key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in paths.items()}

def reviewed_action283133_retirement_receipt():
    try:
        validation_bytes=ACTION283133_PROMOTION_VALIDATION.read_bytes()
        evidence_bytes=ACTION283133_CANDIDATE_EVIDENCE.read_bytes()
        browser_bytes=ACTION283133_BROWSER_RESULTS.read_bytes()
        render_bytes=ACTION283133_RENDER_EVIDENCE.read_bytes()
        review_bytes=ACTION283133_PROMOTION_REVIEW.read_bytes()
        if (hashlib.sha256(validation_bytes).hexdigest()!=ACTION283133_PROMOTION_VALIDATION_SHA256
                or hashlib.sha256(evidence_bytes).hexdigest()!=ACTION283133_CANDIDATE_EVIDENCE_SHA256
                or hashlib.sha256(browser_bytes).hexdigest()!=ACTION283133_BROWSER_RESULTS_SHA256
                or hashlib.sha256(render_bytes).hexdigest()!=ACTION283133_RENDER_EVIDENCE_SHA256
                or hashlib.sha256(review_bytes).hexdigest()!=ACTION283133_PROMOTION_REVIEW_SHA256):return False
        receipt=json.loads(validation_bytes);evidence=json.loads(evidence_bytes);browser=json.loads(browser_bytes);render=json.loads(render_bytes)
        if (receipt.get("task")!="KAN-15 ACTION-28/31/33 mapping promotion review receipt"
                or receipt.get("status")!="APPROVED" or receipt.get("reviewer")!="/root/review_current_capability_gate"
                or receipt.get("review_record")!="notes/agent-reviews/2026-11-16-kan15-actions283133-mapping-promotion-review.md"
                or receipt.get("review_record_sha256")!=ACTION283133_PROMOTION_REVIEW_SHA256
                or receipt.get("approved_outcome")!="RETIRED" or receipt.get("pass_outcome_allowed") is not False
                or receipt.get("actions")!=["ACTION-28","ACTION-31","ACTION-33"]
                or receipt.get("replacement_group")!="booking-cancel"
                or receipt.get("candidate_evidence_sha256")!=ACTION283133_CANDIDATE_EVIDENCE_SHA256
                or receipt.get("browser_results_sha256")!=ACTION283133_BROWSER_RESULTS_SHA256
                or receipt.get("legacy_render_evidence_sha256")!=ACTION283133_RENDER_EVIDENCE_SHA256
                or receipt.get("browser_checks")!=908 or receipt.get("browser_failures")!=0
                or receipt.get("legacy_cancel_actions_returned_to_dashboard") is not True
                or receipt.get("native_checks")!=777
                or receipt.get("candidate_counts")!={"PASS":470}
                or receipt.get("retirement_counts_before_promotion")!={"RETIRED":32,"BLOCKED":44}
                or receipt.get("retirement_counts_after_promotion")!={"RETIRED":44,"BLOCKED":32}
                or receipt.get("fixture_cleanup_verified") is not True or receipt.get("actions_promoted") is not True
                or evidence.get("provenance",{}).get("kind")!="fresh-owned-runtime"
                or evidence.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or evidence.get("current_counts")!={"PASS":470}
                or evidence.get("retirement_counts")!={"RETIRED":32,"BLOCKED":44}
                or evidence.get("gate_exit")!=2 or render.get("source_hashes")!=action283133_source_hashes()):
            return False
        observations=render.get("observations",{})
        if set(observations)!={"ACTION-28","ACTION-31","ACTION-33"} or any(
                row.get("legacy_cancel_post_status")!=200
                or row.get("cancel_result_path")!="/cargo-tracker/admin/dashboard.xhtml"
                or row.get("cancel_returns_to_dashboard") is not True
                for row in observations.values()):return False
        checks=browser.get("checks",[])
        if len(checks)!=908 or any(row.get("passed") is not True for row in checks):return False
        check_names={row.get("name") for row in checks}
        expected_checks={action+" rendered booking wizard action denied or inert "+actor
                         for action in ("ACTION-28","ACTION-31","ACTION-33") for actor in ACTORS}
        if not expected_checks.issubset(check_names):return False
        expected={"ACTION-28":{"source":"/cargo-tracker/booking/booking-date.xhtml","component":"dateForm:j_idt38"},
                  "ACTION-31":{"source":"/cargo-tracker/booking/booking-destination.xhtml","component":"j_idt29:j_idt36"},
                  "ACTION-33":{"source":"/cargo-tracker/booking/booking.xhtml","component":"j_idt29:j_idt35"}}
        proofs=evidence.get("retirement_observations",{});browser_proofs=browser.get("retirement_actions",{})
        current=evidence.get("current_results",[]);retirements=evidence.get("retirement_results",[])
        snapshot=None
        for action,identity in expected.items():
            obs=render.get("observations",{}).get(action,{})
            for actor in ACTORS:
                key="RETIREMENT::"+action+"::"+actor
                proof=proofs.get(key,{});raw=browser_proofs.get(key,{})
                replacement=next((row for row in current if row.get("case")=="REPLACEMENT::booking-cancel::"+actor),{})
                retirement=next((row for row in retirements if row.get("case")==key),{})
                status=303 if actor=="anonymous" else 403 if actor=="Reader" else 405
                if (replacement.get("outcome")!="PASS" or retirement.get("outcome")!="BLOCKED"
                        or retirement.get("specific_negative_entry_verified") is not True
                        or proof.get("driver")!="browser-retired-booking-wizard-v1" or proof.get("legacy_id")!=action
                        or proof.get("actor")!=actor or proof.get("method")!="POST" or proof.get("source_path")!=identity["source"]
                        or proof.get("historical_source_component_id")!=identity["component"]
                        or proof.get("historical_submitted_parameter")!=identity["component"]
                        or proof.get("historical_render_evidence_verified") is not True
                        or proof.get("historical_button_markup_sha256")!=obs.get("button_markup_sha256")
                        or proof.get("source_hashes")!=render.get("source_hashes")
                        or proof.get("response_status")!=status or proof.get("post_target_verified") is not True
                        or proof.get("callback_response_absent") is not True or proof.get("protected_payload_absent") is not True
                        or proof.get("independent_effects_unchanged") is not True
                        or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                        or proof.get("cargo_snapshot_sha256")!=raw.get("cargo_snapshot_sha256")):return False
                if snapshot is None:snapshot=proof["cargo_snapshot_sha256"]
                elif snapshot!=proof["cargo_snapshot_sha256"]:return False
                if actor=="anonymous":
                    if proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:return False
                elif actor=="Reader":
                    identity_proof=proof.get("identity",{})
                    if proof.get("authorization_denied") is not True or identity_proof.get("server_verified") is not True or identity_proof.get("principal")!=USERS[actor] or identity_proof.get("roles")!=[actor]:return False
                else:
                    identity_proof=proof.get("identity",{})
                    if (proof.get("authorization_denied") is not False or proof.get("current_form_verified") is not True
                            or proof.get("current_csrf_present") is not True or proof.get("current_viewstate_present") is not True
                            or identity_proof.get("server_verified") is not True or identity_proof.get("principal")!=USERS[actor]
                            or identity_proof.get("roles")!=[actor]):return False
        return True
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):
        return False

def reviewed_action44_retirement_receipt():
    try:
        raw=ACTION44_RETIREMENT_VALIDATION.read_bytes()
        evidence_bytes=ACTION44_FRESH_EVIDENCE.read_bytes()
        review_bytes=ACTION44_RETIREMENT_REVIEW.read_bytes()
        if (hashlib.sha256(raw).hexdigest()!=ACTION44_RETIREMENT_VALIDATION_SHA256
                or hashlib.sha256(evidence_bytes).hexdigest()!=ACTION44_FRESH_EVIDENCE_SHA256
                or hashlib.sha256(review_bytes).hexdigest()!=ACTION44_RETIREMENT_REVIEW_SHA256):return False
        receipt=json.loads(raw); evidence=json.loads(evidence_bytes)
        basis=receipt["basis"]; review=receipt["review"]
        if (receipt.get("task")!="KAN-15 ACTION-44 specific retired-entry evidence"
                or receipt.get("candidate",{}).get("legacy_id")!="ACTION-44"
                or receipt.get("candidate",{}).get("replacement_id")!="tracking-discovery"
                or basis.get("fresh_evidence_sha256")!=ACTION44_FRESH_EVIDENCE_SHA256
                or basis.get("fixture_status")!="PASS" or basis.get("browser_checks")!=777
                or basis.get("effective_current_counts")!={"PASS":470}
                or basis.get("pre_review_retirement_counts")!={"RETIRED":8,"BLOCKED":68}
                or basis.get("pre_review_gate_exit")!=2 or basis.get("legacy_fixture_cleanup_verified") is not True
                or basis.get("imported_code_attested") is not False
                or evidence.get("provenance",{}).get("kind")!="fresh-owned-runtime"
                or evidence.get("provenance",{}).get("legacy_fixture_cleanup_verified") is not True
                or evidence.get("current_counts")!={"PASS":470}
                or evidence.get("retirement_counts")!={"RETIRED":8,"BLOCKED":68}
                or evidence.get("gate_exit")!=2
                or review.get("status")!="APPROVED" or review.get("reviewer")!="/root/review_action23_driver"
                or review.get("approved_outcome")!="RETIRED" or review.get("pass_outcome_allowed") is not False
                or review.get("review_record")!="notes/agent-reviews/2026-11-15-kan15-action44-retirement-review.md"
                or review.get("review_record_sha256")!=ACTION44_RETIREMENT_REVIEW_SHA256
                or basis.get("source_hashes")!=action44_source_hashes()):return False
        proof_map=evidence.get("retirement_observations",{}); rows=receipt.get("actor_observations",[])
        by_actor={row.get("actor"):row for row in rows if isinstance(row,dict)}
        if set(by_actor)!=set(ACTORS) or len(rows)!=4:return False
        snapshot=None
        for actor in ACTORS:
            proof=proof_map.get("RETIREMENT::ACTION-44::"+actor,{})
            row=by_actor[actor]
            canonical=json.dumps(proof,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
            replacement=next((x for x in evidence.get("current_results",[]) if x.get("case")=="REPLACEMENT::tracking-discovery::"+actor),{})
            if (row.get("proof_sha256")!=hashlib.sha256(canonical).hexdigest()
                    or row.get("replacement_case_id")!="REPLACEMENT::tracking-discovery::"+actor
                    or row.get("replacement_outcome")!="PASS" or replacement.get("outcome")!="PASS"
                    or proof.get("driver")!="browser-retired-public-tracking-v1" or proof.get("legacy_id")!="ACTION-44"
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!="/cargo-tracker/public/track.xhtml"
                    or proof.get("historical_source_component_id")!="trackingForm:trackingId"
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("response_status")!=200 or proof.get("post_target_verified") is not True
                    or proof.get("current_form_verified") is not True or proof.get("current_viewstate_present") is not True
                    or proof.get("current_csrf_present") is not False
                    or proof.get("current_legacy_component_absent") is not True
                    or proof.get("current_callback_implementation_absent") is not True
                    or proof.get("legacy_callback_implementation_verified") is not True
                    or proof.get("callback_response_absent") is not True
                    or proof.get("autocomplete_payload_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or proof.get("authorization_denied") is not False
                    or proof.get("redirect_is_configured_login") is not False
                    or proof.get("source_hashes")!=action44_source_hashes()
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):return False
            if actor=="anonymous":
                if proof.get("identity") is not None:return False
            else:
                identity=proof.get("identity",{})
                if (identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor]
                        or identity.get("roles")!=[actor]):return False
            if snapshot is None:snapshot=proof["cargo_snapshot_sha256"]
            elif snapshot!=proof["cargo_snapshot_sha256"]:return False
        return True
    except (OSError,KeyError,TypeError,ValueError):
        return False

def action23_source_hashes():
    paths={"legacy_admin_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/admin/track.xhtml",
           "legacy_track_bean_sha256":ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java",
           "candidate_admin_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/track.xhtml",
           "candidate_cargo_pages_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/CargoPages.java",
           "legacy_public_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/public/track.xhtml"}
    raw={key:path.read_bytes() for key,path in paths.items()}
    old_page=raw["legacy_admin_page_sha256"].decode("utf-8")
    old_bean=raw["legacy_track_bean_sha256"].decode("utf-8")
    new_page=raw["candidate_admin_page_sha256"].decode("utf-8")
    new_bean=raw["candidate_cargo_pages_sha256"].decode("utf-8")
    public_page=raw["legacy_public_page_sha256"].decode("utf-8")
    if ("id=\"trackIdInput\"" not in old_page or "completeMethod=\"#{track.completeTracking}\"" not in old_page
            or re.search(r"\bpublic\s+[^;{]+\bcompleteTracking\s*\(",old_bean)
            or not re.search(r"\bpublic\s+[^;{]+\bgetTrackingIds\s*\(",old_bean)
            or 'completeMethod="#{track.getTrackingIds}"' not in public_page or 'id="trackingId"' not in public_page or "completeTracking" in new_page
            or "trackIdInput" in new_page or "p:autoComplete" in new_page
            or "completeTracking" in new_bean or 'id="id"' not in new_page):
        raise UnsupportedCase()
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}
def action44_source_hashes():
    paths={"legacy_public_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/public/track.xhtml",
           "legacy_track_bean_sha256":ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java",
           "candidate_public_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/public/track.xhtml",
           "candidate_track_bean_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java"}
    raw={key:path.read_bytes() for key,path in paths.items()}
    old_page=raw["legacy_public_page_sha256"].decode("utf-8")
    old_bean=raw["legacy_track_bean_sha256"].decode("utf-8")
    new_page=raw["candidate_public_page_sha256"].decode("utf-8")
    new_bean=raw["candidate_track_bean_sha256"].decode("utf-8")
    if ('id="trackingId"' not in old_page or 'completeMethod="#{track.getTrackingIds}"' not in old_page
            or not re.search(r"\bpublic\s+List<TrackingId>\s+getTrackingIds\s*\(\s*String\s+query\s*\)",old_bean)
            or 'id="trackingId"' not in new_page or "completeMethod" in new_page
            or "p:autoComplete" in new_page or "getTrackingIds" in new_page
            or re.search(r"\bgetTrackingIds\s*\(",new_bean)):
        raise UnsupportedCase()
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}

def action26_source_hashes():
    paths={"legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
           "legacy_booking_bean_sha256":ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/domain/model/cargo/BookingBackingBean.java",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
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
            or "protected void doPost" in servlet
            or "/booking/booking-date.xhtml\tOperator,Administrator" not in access):
        raise UnsupportedCase()
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}

def action32_source_hashes():
    paths={"legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
           "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
           "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
           "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
    raw={key:path.read_bytes() for key,path in paths.items()}; old=raw["legacy_booking_destination_page_sha256"].decode(); servlet=raw["legacy_navigation_servlet_sha256"].decode(); routes=raw["candidate_access_routes_sha256"].decode()
    if ('<p:commandButton value="Next" action="booking-date" />' not in old
            or '"/booking/booking-destination.xhtml","/admin/book.xhtml"' not in servlet
            or "protected void doPost" in servlet or "/booking/booking-destination.xhtml\tOperator,Administrator" not in routes):raise UnsupportedCase()
    return {key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}

def action32_render_record():
    render_bytes=ACTION32_RENDER_EVIDENCE.read_bytes()
    if hashlib.sha256(render_bytes).hexdigest()!=ACTION32_RENDER_EVIDENCE_SHA256:raise UnsupportedCase()
    record=json.loads(render_bytes);obs=record.get("observation",{});markup=obs.get("button_markup","")
    if (record.get("task")!="KAN-15 ACTION-32 legacy rendered command identity"
            or record.get("source_hashes")!=action32_source_hashes()
            or obs.get("component_id")!="j_idt29:j_idt37" or obs.get("submitted_parameter")!="j_idt29:j_idt37"
            or obs.get("form_id")!="j_idt29" or obs.get("destination_view")!="/cargo-tracker/booking/booking-destination.xhtml"
            or obs.get("render_status")!=200 or obs.get("viewstate_flow_context_error") is not False
            or '<button id="j_idt29:j_idt37"' not in markup or ">Next</span>" not in markup
            or hashlib.sha256(markup.encode()).hexdigest()!=obs.get("button_markup_sha256")):
        raise UnsupportedCase()
    return {"component_id":obs["component_id"],"button_markup_sha256":obs["button_markup_sha256"],"source_hashes":record["source_hashes"]}

def validate_model(model,inventory,inventory_hash):
    if set(model)!={"schema_version","approval_record","approved_proposal_sha256","legacy_inventory_sha256","mapped_actions","pending_current_actions","replacement_capabilities","retirement_candidates","retirement_policy","public_current_capabilities"}:raise ValueError("Unknown or missing model field")
    if model.get("schema_version")!=2 or model.get("legacy_inventory_sha256")!=inventory_hash:raise ValueError("Unknown version or inventory drift")
    if model.get("approval_record")!="notes/decisions/2026-11-02-current-ui-acceptance.md" or model.get("approved_proposal_sha256")!="710b00d37001276e8bd60d806f9fe21ea66a39b7b47ae465122ca78da931da5a":raise ValueError("Unbound approval")
    if inventory_hash!=APPROVED_INVENTORY_SHA256:raise ValueError("Approved inventory changed")
    if {r["legacy_id"] for r in model["mapped_actions"]}!=APPROVED_MAPPED or {r["legacy_id"] for r in model["pending_current_actions"]}!=APPROVED_PENDING or {r["legacy_id"] for r in model["retirement_candidates"]}!=set(APPROVED_RETIREMENT_GROUP):raise ValueError("Approved mapping partition changed")
    if model["retirement_policy"]!=APPROVED_RETIREMENT_POLICY:raise ValueError("Approved retirement policy changed")
    expected_public=[{"capability_id":"public-typed-cargo-tracking","legacy_ids":["PAGE-25","ACTION-45"],"allowed_roles":["Reader","Operator","Administrator"],"anonymous":True,"read_only":True,"page_path":"/cargo-tracker/public/track.xhtml","lookup_method":"POST"}]
    if model.get("public_current_capabilities")!=expected_public:raise ValueError("Unapproved public current capability policy")
    public_action=next((r for r in model["mapped_actions"] if r.get("legacy_id")=="ACTION-45"),None)
    if public_action!={"legacy_id":"ACTION-45","capability_id":"public-typed-cargo-tracking","modern_source":"public/track.xhtml","modern_target":"/cargo-tracker/public/track.xhtml","modern_method":"POST"}:raise ValueError("Public typed lookup mapping drift")
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
        if old["domain_mutation"] or group is None or row["legacy_id"] not in group.get("legacy_ids",[]):raise ValueError("Unbound retirement")
        if row["legacy_id"]=="ACTION-08":
            if row.get("status")!="retired" or row.get("negative_driver")!="browser-retired-action-v1" or not reviewed_action08_retirement_receipt():raise ValueError("Retirement lacks its pinned independent evidence receipt")
        elif row["legacy_id"]=="ACTION-23" and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-tracking-v1" or not reviewed_action23_retirement_receipt():raise ValueError("ACTION-23 retirement lacks its pinned independent evidence receipt")
        elif row["legacy_id"]=="ACTION-44" and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-public-tracking-v1" or not reviewed_action44_retirement_receipt():raise ValueError("ACTION-44 retirement lacks its pinned independent evidence receipt")
        elif row["legacy_id"]=="ACTION-26" and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-deadline-v1" or not reviewed_action26_retirement_receipt():raise ValueError("ACTION-26 retirement lacks its pinned independent evidence receipt")
        elif row["legacy_id"]=="ACTION-32" and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-destination-next-v1" or not reviewed_action32_retirement_receipt():raise ValueError("ACTION-32 retirement lacks its pinned independent evidence receipt")
        elif row["legacy_id"] in {"ACTION-27","ACTION-30","ACTION-34"} and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-booking-wizard-v1" or not reviewed_action273034_retirement_receipt():raise ValueError("Booking wizard retirement lacks its pinned independent promotion receipt")
        elif row["legacy_id"] in {"ACTION-28","ACTION-31","ACTION-33"} and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-booking-wizard-v1" or not reviewed_action283133_retirement_receipt():raise ValueError("Booking cancel retirement lacks its pinned independent promotion receipt")
        elif row["legacy_id"] in HANDLING_CALLBACK_RETIREMENT_ACTIONS and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-rendered-handling-callback-shape-v1" or not reviewed_handling_callback_retirement_receipt():raise ValueError("Handling callback retirement lacks its pinned independent promotion receipt")
        elif row["legacy_id"] in HANDLING_CALLBACK_RETIREMENT_ACTIONS and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-rendered-handling-callback-shape-v1"}:raise ValueError("Unsupported handling callback retired-entry driver")
        elif row["legacy_id"] in HANDLING_PAGE_RETIREMENT_ACTIONS and row.get("status")=="retired":
            if row.get("negative_driver")!="browser-retired-handling-page-v1" or not reviewed_handling_page_retirement_receipt():raise ValueError("Handling page retirement lacks its pinned independent promotion receipt")
        elif row["legacy_id"] in HANDLING_PAGE_RETIREMENT_ACTIONS and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-retired-handling-page-v1"}:raise ValueError("Unsupported handling page retired-entry driver")
        elif row["legacy_id"]=="ACTION-23" and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-retired-tracking-v1"}:raise ValueError("Unsupported ACTION-23 retired-entry driver")
        elif row["legacy_id"]=="ACTION-44" and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-retired-public-tracking-v1"}:raise ValueError("Unsupported ACTION-44 retired-entry driver")
        elif row["legacy_id"]=="ACTION-26" and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-retired-deadline-v1"}:raise ValueError("Unsupported ACTION-26 retired-entry driver")
        elif row["legacy_id"]=="ACTION-32" and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-retired-destination-next-v1"}:raise ValueError("Unsupported ACTION-32 retired-entry driver")
        elif row["legacy_id"] in {"ACTION-27","ACTION-30","ACTION-34"} and row.get("status")=="candidate":
            if row.get("negative_driver") not in {"pending","browser-retired-booking-wizard-v1"}:raise ValueError("Unsupported booking wizard retired-entry driver")
        elif row.get("status")!="candidate" or row.get("negative_driver")!="pending":raise ValueError("Premature retirement")
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
    public_policy=model["public_current_capabilities"][0]
    public_ids=set(public_policy["legacy_ids"])
    cases=[]
    for old in build(inventory):
        if old["surface_id"] in retired:continue
        row=mapped.get(old["surface_id"]) or pending.get(old["surface_id"])
        case=deepcopy(old)
        binding=("pending" if old["surface_id"] in pending else
            "native-batch-worker" if old["surface_id"] in {"BG-01-MACHINE","BG-02-MACHINE"} else
            "native-batch-import" if old["surface_id"]=="BG-01" else
            "native-batch-processing" if old["surface_id"]=="BG-02" else
            "native-handling-worker" if old["surface_id"] in {"BG-03","BG-03-MACHINE"} else
            "native-inspection-worker" if old["surface_id"] in {"BG-04","BG-04-MACHINE"} else
            "native-notification-worker" if old["surface_id"] in {"BG-05","BG-05-MACHINE"} else
            "native-booking-service" if old["surface_id"]=="SERVICE-01" else
            "native-booking-routes" if old["surface_id"]=="SERVICE-02" else
            "native-booking-facade" if old["surface_id"]=="SERVICE-03" else
            "native-service-boundary" if old["surface_id"]=="SERVICE-04" else
            "native-staged-return" if old["surface_id"]=="ACTION-13" else
            "native-current-load" if old["surface_id"] in NATIVE_CURRENT_LOADS else
            "browser-current-navigation" if old["surface_id"] in {"ACTION-10","ACTION-11","ACTION-12","ACTION-21","ACTION-22","ACTION-24","ACTION-25","ACTION-45"} else
            "existing-runtime-driver")
        capability=row["capability_id"] if row else old["surface_id"].lower()
        case.update(id="CURRENT::"+old["id"],contract_version=2,kind="current",
            legacy_case_id=old["id"],legacy_contract=deepcopy(old),capability_id=capability,
            binding_status=binding)
        if row:
            source="index.xhtml" if old["surface_id"]!="ACTION-13" and old["actor"]=="anonymous" and old["expected"]=="deny" and row["modern_method"]=="GET" else row["modern_source"]
            case.update(path=row["modern_target"],method=row["modern_method"],current_source=source)
        if old["surface_id"] in public_ids:
            case.update(expected="allow",capability_id=public_policy["capability_id"])
            if old["surface_id"]=="PAGE-25":
                case.update(path=public_policy["page_path"],method="GET",
                    current_source="public/track.xhtml",binding_status="public-typed-tracking-page")
                if old["channel"]=="session":case["public_after_revocation"]=True
        cases.append(case)
    for group in model["replacement_capabilities"]:
        for actor in ACTORS:
            allowed=group["anonymous"] if actor=="anonymous" else actor in group["allowed_roles"]
            cases.append({"id":"REPLACEMENT::"+group["id"]+"::"+actor,"contract_version":2,"kind":"replacement","capability_id":group["id"],"channel":"capability","actor":actor,"expected":"allow" if allowed else "deny","write":False,"method":group["modern_method"],"semantic_requirement":group["requirement"],"requires_specific_driver":True,"binding_status":group["driver"],"legacy_ids":deepcopy(group["legacy_ids"])})
    if len({c["id"] for c in cases})!=len(cases):raise ValueError("Duplicate current case")
    return cases

def source_fingerprint():
    paths=subprocess.check_output(["git","ls-files","-co","--exclude-standard","--",".dockerignore","candidate","infrastructure/database","tests/candidate-runtime","tests/browser-workflows","tests/security","specifications/access-policy-inventory.json","specifications/current-capability-mapping-v2.json","notes/decisions/2026-11-02-current-ui-acceptance.md","notes/evidence/kan-15-bg06-scope/validation.json","notes/agent-reviews/2026-11-11-kan15-bg06-scope-review.md","notes/agent-reviews/2026-11-15-kan15-bg06-scope-refresh-review.md","notes/agent-reviews/2026-11-14-kan15-action08-retirement-review.md","notes/evidence/kan-15-action32-retirement/legacy-rendered-entry.json","notes/evidence/kan-15-action273034-retirement/legacy-rendered-actions.json","notes/evidence/kan-15-action283133-retirement/legacy-rendered-actions.json","notes/evidence/kan-15-handling-callback-retirement","notes/agent-reviews/2026-11-17-kan15-handling-callback-promotion-review.md"],cwd=ROOT,text=True).splitlines()
    digest=hashlib.sha256()
    for name in sorted(set(paths)):
        path=ROOT/name
        if path.is_file():digest.update(name.encode()+b"\0"+hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()

def reviewed_bg06_scope():
    receipt_path=ROOT/"notes/evidence/kan-15-bg06-scope/validation.json"
    receipt_bytes=receipt_path.read_bytes()
    receipt=json.loads(receipt_bytes)
    desired=json.loads((ROOT/"tests/security/desired-cases.json").read_text())
    promotions=validate_bg06_scope(receipt,desired,receipt_bytes)
    evidence=receipt["evidence"]
    provenance={"kind":"reviewed-fresh-scoped-runtime","driver":receipt["driver"],
        "scope_receipt_sha256":hashlib.sha256(receipt_bytes).hexdigest(),
        "runtime_receipt_sha256":receipt["runtime_receipt_sha256"],
        "gate_adapter_sha256":receipt["gate_adapter_sha256"],
        "run_id":evidence["run_id"],"started_at_utc":receipt["started_at_utc"],
        "completed_at_utc":receipt["completed_at_utc"]}
    return promotions,provenance

def apply_bg06_scoped_results(current_results,promotions,provenance):
    expected={"CURRENT::BG-06::"+actor+"::active" for actor in ACTORS}
    expected.add("CURRENT::BG-06-MACHINE::deployment-migration::active")
    if (not isinstance(promotions,dict) or set(promotions)!=expected
            or any(value!="PASS" for value in promotions.values())
            or not isinstance(provenance,dict)
            or provenance.get("kind")!="reviewed-fresh-scoped-runtime"
            or re.fullmatch("[0-9a-f]{64}",str(provenance.get("scope_receipt_sha256"))) is None):
        raise ValueError("Reviewed BG-06 scope promotion set or provenance is invalid")
    ids=[row.get("case") for row in current_results]
    if None in ids or len(ids)!=len(set(ids)) or not expected.issubset(ids):
        raise ValueError("Aggregate current results do not contain each exact BG-06 case once")
    output=[]
    for original in current_results:
        row=deepcopy(original)
        if row["case"] in expected:
            if row.get("outcome")!="BLOCKED":
                raise ValueError("BG-06 scoped receipt can promote only blocked canonical rows")
            row["outcome"]="PASS"
            row["reason"]="Passed by independently reviewed fresh BG-06 scoped verification; separate fixture"
            row["evidence_provenance"]=deepcopy(provenance)
        output.append(row)
    return output

def handling_page_retirement_source_evidence():
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
        if not match:raise UnsupportedCase()
        actions[action]={"outcome":"pm:secondScreen?transition=flip" if action=="ACTION-35" else "pm:firstScreen?transition=flip",
            "legacy_control_sha256":hashlib.sha256(match.group(0).encode()).hexdigest()}
    if ('"/eventLogger/eventLogger.xhtml","/mobile.xhtml"' not in servlet
            or "/eventLogger/eventLogger.xhtml\tOperator,Administrator" not in routes
            or 'id="handling"' not in current or "Report handling" not in current or "Event Logger" in current
            or 'outcome="pm:secondScreen?transition=flip"' in current or 'outcome="pm:firstScreen?transition=flip"' in current):
        raise UnsupportedCase()
    return {"actions":actions,"source_hashes":{key:hashlib.sha256(value).hexdigest() for key,value in raw.items()}}

def verify_handling_page_retirement_proof(legacy_id,actor,proof):
    if legacy_id not in HANDLING_PAGE_RETIREMENT_ACTIONS or actor not in ACTORS or not isinstance(proof,dict):raise UnsupportedCase()
    try:evidence=handling_page_retirement_source_evidence();source=evidence["actions"][legacy_id]
    except (OSError,KeyError,TypeError,ValueError,UnsupportedCase):raise UnsupportedCase()
    expected_status={"anonymous":303,"Reader":403,"Operator":303,"Administrator":303}[actor]
    expected_redirect="/login" if actor=="anonymous" else "/mobile.xhtml" if actor in {"Operator","Administrator"} else None
    if (proof.get("driver")!="browser-retired-handling-page-v1" or proof.get("legacy_id")!=legacy_id
            or proof.get("actor")!=actor or proof.get("method")!="GET"
            or proof.get("source_path")!="/cargo-tracker/eventLogger/eventLogger.xhtml"
            or proof.get("legacy_outcome")!=source["outcome"]
            or proof.get("legacy_control_sha256")!=source["legacy_control_sha256"]
            or proof.get("source_hashes")!=evidence["source_hashes"]
            or proof.get("source_control_identity_verified") is not True
            or proof.get("candidate_legacy_page_redirect_verified") is not True
            or not is_safe_handling_redirect(proof,expected_redirect)
            or proof.get("response_status")!=expected_status or proof.get("redirect_target")!=expected_redirect
            or proof.get("protected_payload_absent") is not True or proof.get("independent_effects_unchanged") is not True):
        raise UnsupportedCase()
    if actor=="anonymous":
        if proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:raise UnsupportedCase()
    elif actor=="Reader":
        identity=proof.get("identity",{})
        if proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:raise UnsupportedCase()
    else:
        identity=proof.get("identity",{})
        if (proof.get("authorization_denied") is not False or proof.get("replacement_served") is not True
                or proof.get("legacy_controls_absent") is not True or identity.get("server_verified") is not True
                or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
    return proof

def verify_handling_callback_retirement_proof(legacy_id,actor,proof):
    """Bind one actor's fresh rendered callback denial to pinned source evidence."""
    if legacy_id not in HANDLING_CALLBACK_RETIREMENT_ACTIONS or actor not in ACTORS or not isinstance(proof,dict):
        raise UnsupportedCase()
    try:
        evidence=load_handling_callback_source_evidence()
        rendered=evidence["actions"][legacy_id]
    except (OSError,KeyError,TypeError,ValueError):
        raise UnsupportedCase()
    allowed=actor in {"Operator","Administrator"}
    expected_status=303 if actor=="anonymous" else 403 if actor=="Reader" else 405
    expected_identity=None if actor=="anonymous" else {
        "server_verified":True,"principal":USERS[actor],"roles":[actor]}
    expected_parameters=list(rendered["parameter_names"])
    expected_viewstate="jakarta.faces.ViewState" if allowed else None
    if allowed:
        expected_parameters.extend(["csrf",expected_viewstate])
    before,after=proof.get("before",{}),proof.get("after",{})
    required_effects=("tables","queues","business_invocations")
    if (proof.get("driver")!="browser-rendered-handling-callback-shape-v1"
            or proof.get("legacy_id")!=legacy_id or proof.get("actor")!=actor
            or proof.get("method")!="POST" or proof.get("source_path")!="/cargo-tracker/eventLogger/eventLogger.xhtml"
            or proof.get("historical_source_component_id")!=rendered["source_component_id"]
            or proof.get("historical_source_parameter")!="javax.faces.source"
            or proof.get("behavior_event")!=rendered["behavior_event"]
            or proof.get("historical_execute")!=rendered["execute"]
            or proof.get("historical_render")!=rendered["render"]
            or proof.get("historical_render_evidence_verified") is not True
            or proof.get("source_capture_sha256")!=evidence["capture_sha256"]
            or proof.get("source_hashes")!=evidence["source_hashes"]
            or proof.get("legacy_parameter_names")!=rendered["parameter_names"]
            or proof.get("historical_callback_input_name")!=rendered["callback_input_name"]
            or proof.get("submitted_callback_value")!=rendered["selected_value"]
            or proof.get("rendered_callback_shape_verified") is not True
            or proof.get("exact_raw_legacy_replay") is not False
            or proof.get("dynamic_legacy_state_redacted") is not True
            or not isinstance(proof.get("submitted_parameter_names"),list)
            or any(not isinstance(item,str) for item in proof["submitted_parameter_names"])
            or len(proof["submitted_parameter_names"])!=len(set(proof["submitted_parameter_names"]))
            or set(proof["submitted_parameter_names"])!=set(expected_parameters)
            or proof.get("candidate_viewstate_parameter")!=expected_viewstate
            or proof.get("candidate_viewstate_present") is not allowed
            or proof.get("candidate_viewstate_submitted") is not allowed
            or proof.get("candidate_csrf_present") is not (actor!="anonymous")
            or proof.get("candidate_csrf_submitted") is not allowed
            or proof.get("response_status")!=expected_status or proof.get("post_target_verified") is not True
            or proof.get("authorization_denied") is not (actor in {"anonymous","Reader"})
            or proof.get("callback_response_absent") is not allowed
            or proof.get("protected_payload_absent") is not True
            or proof.get("redirect_is_configured_login") is not (actor=="anonymous")
            or proof.get("current_form_verified") is not allowed
            or proof.get("identity")!=expected_identity
            or proof.get("independent_effects_unchanged") is not True
            or not isinstance(before,dict) or not isinstance(after,dict)
            or before.get("fixture_id")!=after.get("fixture_id")
            or before.get("stage")!="handling-retired-callback:"+actor+":before"
            or after.get("stage")!="handling-retired-callback:"+actor+":after"
            or any(not before.get(key) or before.get(key)!=after.get(key) for key in required_effects)):
        raise UnsupportedCase()
    return deepcopy(proof)


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
        self.bg06_promotions=None;self.bg06_scope_provenance=None
        if live:
            self.bg06_promotions,self.bg06_scope_provenance=reviewed_bg06_scope()
            if source_fingerprint()!=before:raise RuntimeError("Inputs changed while loading canonical contracts")
            self.legacy=legacy.LiveSubsetCandidate()
            if source_fingerprint()!=before:raise RuntimeError("Runtime or contract inputs changed during fixture")
            self._run_fingerprint=before
            self.provenance={"kind":"fresh-owned-runtime","inputs_fingerprint":before,"canonical_contracts_sha256":self._contracts_fingerprint,"legacy_fixture_cleanup_verified":True,"imported_code_attested":False,"fingerprint_scope":"On-disk inputs and constructed canonical contracts; already imported Python code identity is not attested.","reviewed_bg06_scope":deepcopy(self.bg06_scope_provenance)}
    def execute(self,case):
        canonical=self.contracts.get(case.get("id"))
        if canonical is None or canonical!=case:raise UnsupportedCase()
        if case["kind"] not in {"current","replacement"} or self.legacy is None or self.provenance is None:
            raise UnsupportedCase()
        if case["kind"]=="current" and case.get("binding_status") not in {"existing-runtime-driver","native-current-load","browser-current-navigation","native-staged-return","native-batch-import","native-batch-processing","native-batch-worker","native-handling-worker","native-inspection-worker","native-notification-worker","native-service-boundary","native-booking-service","native-booking-routes","native-booking-facade","public-typed-tracking-page"}:
            raise UnsupportedCase()
        if not isinstance(self.provenance,dict) or self.provenance.get("kind")!="fresh-owned-runtime" or self.provenance.get("legacy_fixture_cleanup_verified") is not True or self.provenance.get("inputs_fingerprint")!=self._run_fingerprint or re.fullmatch("[0-9a-f]{64}",str(self._run_fingerprint)) is None:raise UnsupportedCase()
        if case["kind"]=="replacement":
            observation=replacement_observation(case,getattr(self.legacy,"replacement_observations",{}).get(case["id"],{}))
        elif case["binding_status"]=="native-batch-worker":
            observation=batch_worker_observation(case,getattr(self.legacy,"batch_processing_observation",{}))
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
        elif case["binding_status"]=="native-handling-worker":
            if case["actor"]=="worker-BG-03":
                observation=deepcopy(getattr(self.legacy,"handling_worker_observation",{}))
                identity=observation.get("native_identity",{})
                raw_producer=getattr(self.legacy,"remote_producer_raw_observation",{})
                producer_effects=getattr(self.legacy,"remote_producer_unauthorized_effects_unchanged",False)
                if (observation.get("driver")!="native-handling-worker-v1"
                        or observation.get("supported") is not True
                        or observation.get("status")!=200
                        or observation.get("machine_identity_verified") is not True
                        or observation.get("machine_scope")!=case.get("required_machine_scope")
                        or observation.get("authorized_adapter_events_verified") is not True
                        or observation.get("producer_boundary_verified") is not True
                        or not handling_producer_boundary_verified(raw_producer,producer_effects)
                        or observation.get("human_direct_denials_effects_unchanged") is not True
                        or identity.get("server_verified") is not True
                        or identity.get("principal")!="handling-worker"
                        or identity.get("roles")!=["HandlingWorker"]):
                    raise UnsupportedCase()
            else:
                observation=deepcopy(getattr(self.legacy,"handling_worker_denials",{}).get(case["actor"],{}))
                expected_status=401 if case["actor"]=="anonymous" else 403
                if (observation.get("driver")!="native-handling-worker-v1"
                        or observation.get("actor")!=case["actor"]
                        or observation.get("supported") is not True
                        or observation.get("status")!=expected_status
                        or observation.get("invocation_denied") is not True
                        or observation.get("direct_service_denied") is not True
                        or observation.get("independent_effects_unchanged") is not True):
                    raise UnsupportedCase()
        elif case["binding_status"]=="native-inspection-worker":
            if case["actor"]=="worker-BG-04":
                observation=deepcopy(getattr(self.legacy,"inspection_worker_observation",{}))
                identity=observation.get("native_identity",{})
                producer_raw=getattr(self.legacy,"cargo_handled_producer_raw_observation",{})
                producer_effects=getattr(self.legacy,"cargo_handled_producer_effects_unchanged",False)
                if (observation.get("driver")!="native-inspection-worker-v1"
                        or observation.get("supported") is not True
                        or observation.get("status")!=200
                        or observation.get("machine_identity_verified") is not True
                        or observation.get("machine_scope")!=case.get("required_machine_scope")
                        or observation.get("producer_origin_verified") is not True
                        or observation.get("correlation_verified") is not True
                        or observation.get("authorized_adapter_events_verified") is not True
                        or observation.get("producer_boundary_verified") is not True
                        or not cargo_handled_producer_boundary_verified(producer_raw,producer_effects)
                        or observation.get("human_direct_denials_effects_unchanged") is not True
                        or identity.get("server_verified") is not True
                        or identity.get("principal")!="inspection-worker"
                        or identity.get("roles")!=["InspectionWorker"]):
                    raise UnsupportedCase()
            else:
                observation=deepcopy(getattr(self.legacy,"inspection_worker_denials",{}).get(case["actor"],{}))
                expected_status=401 if case["actor"]=="anonymous" else 403
                if (observation.get("driver")!="native-inspection-worker-v1"
                        or observation.get("actor")!=case["actor"]
                        or observation.get("supported") is not True
                        or observation.get("status")!=expected_status
                        or observation.get("invocation_denied") is not True
                        or observation.get("direct_service_denied") is not True
                        or observation.get("independent_effects_unchanged") is not True):
                    raise UnsupportedCase()
        elif case["binding_status"]=="native-notification-worker":
            if case["actor"]=="worker-BG-05":
                observation=deepcopy(getattr(self.legacy,"notification_worker_observation",{}))
                identity=observation.get("native_identity",{})
                disposition=getattr(self.legacy,"rejection_disposition_observation",{})
                if (observation.get("driver")!="native-notification-worker-v1"
                        or observation.get("supported") is not True
                        or observation.get("status")!=200
                        or observation.get("machine_identity_verified") is not True
                        or observation.get("machine_scope")!=case.get("required_machine_scope")
                        or observation.get("consumer_bindings_verified") is not True
                        or observation.get("sanitized_logs_verified") is not True
                        or observation.get("queue_cycles_verified") is not True
                        or observation.get("producer_boundary_verified") is not True
                        or observation.get("rejection_producer_verified") is not True
                        or observation.get("final_disposition_verified") is not True
                        or disposition.get("trusted_broker_dead_letter_verified") is not True
                        or disposition.get("sanitized_rejection_audit_verified") is not True
                        or disposition.get("business_side_effects_unchanged") is not True
                        or identity.get("server_verified") is not True
                        or identity.get("principal")!="notification-worker"
                        or identity.get("roles")!=["NotificationWorker"]):
                    raise UnsupportedCase()
            else:
                observation=deepcopy(getattr(self.legacy,"notification_worker_denials",{}).get(case["actor"],{}))
                expected_status=401 if case["actor"]=="anonymous" else 403
                if (observation.get("driver")!="native-notification-worker-v1"
                        or observation.get("actor")!=case["actor"]
                        or observation.get("supported") is not True
                        or observation.get("status")!=expected_status
                        or observation.get("invocation_denied") is not True
                        or observation.get("direct_service_denied") is not True
                        or observation.get("independent_effects_unchanged") is not True):
                    raise UnsupportedCase()
        elif case["binding_status"]=="native-booking-service":
            observation=booking_service_observation(case,
                getattr(self.legacy,"booking_service_observations",{}).get(case["actor"],{}))
        elif case["binding_status"]=="native-booking-routes":
            observation=booking_routes_observation(case,
                getattr(self.legacy,"booking_service_route_observations",{}).get(case["actor"],{}))
        elif case["binding_status"]=="native-booking-facade":
            observation=booking_facade_observation(case,
                getattr(self.legacy,"booking_facade_observations",{}).get(case["actor"],{}))
        elif case["binding_status"]=="native-service-boundary":
            observation=service_boundary_observation(case,
                getattr(self.legacy,"handling_worker_denials",{}),
                getattr(self.legacy,"inspection_worker_denials",{}))
        elif case["binding_status"]=="native-staged-return":
            observation=return_observation(case,getattr(self.legacy,"current_observations",{}).get(case["id"],{}))
        elif case["binding_status"]=="native-current-load":
            observation=deepcopy(getattr(self.legacy,"current_observations",{}).get(case["id"],{}))
            if observation.get("current_load_driver")!="native-current-load-v1" or observation.get("invalid_inputs_verified") is not True:raise UnsupportedCase()
            if case["surface_id"]=="ACTION-15" and case["expected"]=="allow" and observation.get("route_details_verified") is not True:
                raise UnsupportedCase()
            if case["surface_id"]=="ACTION-18" and observation.get("route_alias_verified") is not True:raise UnsupportedCase()
            if case["expected"]=="allow" and (observation.get("selected_cargo_verified") is not True or observation.get("current_values_verified") is not True):raise UnsupportedCase()
        elif case["binding_status"]=="public-typed-tracking-page":
            observation=deepcopy(self.legacy.execute(deepcopy(canonical["legacy_contract"])))
            if (observation.get("supported") is not True or observation.get("status")!=200
                    or observation.get("semantic_success") is not True
                    or observation.get("protected_payload_absent") is not True):
                raise UnsupportedCase()
            if case["channel"]=="session" and (observation.get("identity") is not None
                    or observation.get("public_access_after_revocation") is not True
                    or observation.get("authenticated_before_revocation") is not True
                    or observation.get("revocation_verified") is not True):
                raise UnsupportedCase()
        elif case["binding_status"]=="browser-current-navigation":
            observation=deepcopy(getattr(self.legacy,"current_observations",{}).get(case["id"],{}))
            if case["surface_id"]=="ACTION-10":
                if observation.get("current_navigation_driver")!="browser-claimed-cargo-v1":raise UnsupportedCase()
                allowed_flags=("selected_cargo_verified","persisted_details_verified")
                denied_flags=("claimed_list_denied",)
            elif case["surface_id"] in {"ACTION-24","ACTION-45"}:
                if observation.get("current_navigation_driver")!="browser-lookup-v1":raise UnsupportedCase()
                if case["expected"]=="allow":
                    if case["surface_id"]=="ACTION-45":
                        if (observation.get("submission_status")!=200 or observation.get("invalid_inputs_verified") is not True
                                or observation.get("legacy_entry_verified") is not True or observation.get("protected_payload_absent") is not True
                                or observation.get("action_method")!="POST" or observation.get("action_path")!="/cargo-tracker/public/track.xhtml"
                                or observation.get("entry_page")!="public/track.xhtml" or observation.get("source_entry_verified") is not True):raise UnsupportedCase()
                    elif observation.get("submission_status") not in {302,303} or observation.get("invalid_inputs_verified") is not True or observation.get("csrf_checks_verified") is not True:raise UnsupportedCase()
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
            if case.get("capability_id")=="public-typed-cargo-tracking" and case["channel"]=="session":
                if observation.get("identity") is not None:raise UnsupportedCase()
            else:
                identity=observation.get("identity",{})
                if identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:raise UnsupportedCase()
        elif actor=="anonymous":
            if observation.get("identity") is not None:raise UnsupportedCase()
        elif actor=="routing-service":
            identity=observation.get("native_identity",{})
            if identity.get("principal")!="routing" or identity.get("roles")!=["RoutingService"] or observation.get("machine_identity_verified") is not True or observation.get("machine_scope")!=case.get("required_machine_scope"):raise UnsupportedCase()
        elif actor=="worker-BG-01":
            identity=observation.get("native_identity",{})
            if (identity.get("server_verified") is not True or identity.get("principal")!="batch-worker"
                    or identity.get("roles")!=["BatchWorker"] or observation.get("machine_identity_verified") is not True
                    or observation.get("machine_scope")!=BG01_MACHINE_SCOPE):
                raise UnsupportedCase()
        elif actor=="worker-BG-02":
            identity=observation.get("native_identity",{})
            if (identity.get("server_verified") is not True or identity.get("principal")!="batch-worker"
                    or identity.get("roles")!=["BatchWorker"] or observation.get("machine_identity_verified") is not True
                    or observation.get("machine_scope")!=BG02_MACHINE_SCOPE):
                raise UnsupportedCase()
        elif actor=="worker-BG-03":
            identity=observation.get("native_identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!="handling-worker" or identity.get("roles")!=["HandlingWorker"]:raise UnsupportedCase()
        elif actor=="worker-BG-04":
            identity=observation.get("native_identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!="inspection-worker" or identity.get("roles")!=["InspectionWorker"]:raise UnsupportedCase()
        elif actor=="worker-BG-05":
            identity=observation.get("native_identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!="notification-worker" or identity.get("roles")!=["NotificationWorker"]:raise UnsupportedCase()
        else:raise UnsupportedCase()
        if case["kind"]=="current" and case["binding_status"]!="native-staged-return" and (canonical["legacy_contract"]["channel"]=="action" or canonical["legacy_contract"].get("original_channel")=="action"):
            verify_action_proof(case,observation)
        observation["current_provenance"]=deepcopy(self.provenance)
        return observation
    def execute_retirement(self,case,replacement_results):
        legacy_id=case.get("legacy_id") if isinstance(case,dict) else None
        group={"ACTION-08":"cancel-editor","ACTION-23":"tracking-discovery","ACTION-44":"tracking-discovery","ACTION-26":"booking-deadline","ACTION-32":"booking-deadline","ACTION-27":"booking-single-page","ACTION-30":"booking-single-page","ACTION-34":"booking-single-page","ACTION-28":"booking-cancel","ACTION-31":"booking-cancel","ACTION-33":"booking-cancel",**HANDLING_CALLBACK_RETIREMENT_ACTIONS,**HANDLING_PAGE_RETIREMENT_ACTIONS}.get(legacy_id)
        allowed_retirements={"ACTION-08","ACTION-23","ACTION-44","ACTION-26","ACTION-32","ACTION-27","ACTION-30","ACTION-34","ACTION-28","ACTION-31","ACTION-33",*HANDLING_CALLBACK_RETIREMENT_ACTIONS,*HANDLING_PAGE_RETIREMENT_ACTIONS}
        if (not isinstance(case,dict) or legacy_id not in allowed_retirements
                or case.get("actor") not in ACTORS
                or case.get("replacement_case_id")!="REPLACEMENT::"+str(group)+"::"+str(case.get("actor"))
                or self.legacy is None or not isinstance(self.provenance,dict)
                or self.provenance.get("kind")!="fresh-owned-runtime"
                or self.provenance.get("legacy_fixture_cleanup_verified") is not True
                or self.provenance.get("inputs_fingerprint")!=self._run_fingerprint
                or re.fullmatch("[0-9a-f]{64}",str(self._run_fingerprint)) is None):
            raise UnsupportedCase()
        replacement=next((row for row in replacement_results if row.get("case")==case["replacement_case_id"]),None)
        if not isinstance(replacement,dict) or replacement.get("outcome")!="PASS":raise UnsupportedCase()
        actor=case["actor"]
        if legacy_id in HANDLING_CALLBACK_RETIREMENT_ACTIONS:
            callback_proof=deepcopy(getattr(self.legacy,"handling_callback_retirement_observations",{}).get(case["id"],{}))
            return verify_handling_callback_retirement_proof(legacy_id,actor,callback_proof)
        if legacy_id in HANDLING_PAGE_RETIREMENT_ACTIONS:
            page_proof=deepcopy(getattr(self.legacy,"retirement_observations",{}).get(case["id"],{}))
            return verify_handling_page_retirement_proof(legacy_id,actor,page_proof)
        proof=deepcopy(getattr(self.legacy,"retirement_observations",{}).get(case["id"],{}))
        if legacy_id=="ACTION-26":
            try:source_hashes=action26_source_hashes()
            except (OSError,UnsupportedCase):raise UnsupportedCase()
            if (proof.get("driver")!="browser-retired-deadline-v1" or proof.get("legacy_id")!="ACTION-26"
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!="/cargo-tracker/booking/booking-date.xhtml"
                    or proof.get("historical_source_component_id")!="dateForm:deadline"
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("source_hashes")!=source_hashes or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13):raise UnsupportedCase()
            if actor=="anonymous":
                if proof.get("response_status")!=303 or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:raise UnsupportedCase()
            elif actor=="Reader":
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=403 or proof.get("authorization_denied") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("authorization_denied") is not False
                        or proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
            return proof
        elif legacy_id in {"ACTION-28","ACTION-31","ACTION-33"}:
            try:
                raw=ACTION283133_RENDER_EVIDENCE.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=ACTION283133_RENDER_EVIDENCE_SHA256:raise UnsupportedCase()
                record=json.loads(raw);obs=record["observations"][legacy_id]
                source_hashes=record["source_hashes"]
                paths={"legacy_booking_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking.xhtml",
                       "legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
                       "legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
                       "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
                       "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
                       "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
                actual={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in paths.items()}
                if actual!=source_hashes:raise UnsupportedCase()
            except (OSError,KeyError,ValueError):raise UnsupportedCase()
            if (proof.get("driver")!="browser-retired-booking-wizard-v1" or proof.get("legacy_id")!=legacy_id
                    or proof.get("actor")!=actor or proof.get("method")!="POST" or proof.get("source_path")!=obs.get("source_path")
                    or proof.get("historical_source_component_id")!=obs.get("component_id")
                    or proof.get("historical_submitted_parameter")!=obs.get("component_id")
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=obs.get("button_markup_sha256")
                    or proof.get("source_hashes")!=source_hashes
                    or proof.get("current_post_handler_absent") is not True or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):raise UnsupportedCase()
            if actor=="anonymous":
                if proof.get("response_status")!=303 or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:raise UnsupportedCase()
            elif actor=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:raise UnsupportedCase()
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("authorization_denied") is not False
                        or proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
            return proof
        elif legacy_id in {"ACTION-27","ACTION-30","ACTION-34"}:
            try:
                raw=ACTION273034_RENDER_EVIDENCE.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=ACTION273034_RENDER_EVIDENCE_SHA256:raise UnsupportedCase()
                record=json.loads(raw);obs=record["observations"][legacy_id]
                source_hashes=record["source_hashes"]
                paths={"legacy_booking_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking.xhtml",
                       "legacy_booking_destination_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-destination.xhtml",
                       "legacy_booking_date_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/booking/booking-date.xhtml",
                       "candidate_booking_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/admin/book.xhtml",
                       "legacy_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
                       "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"}
                actual={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in paths.items()}
                if actual!=source_hashes:raise UnsupportedCase()
            except (OSError,KeyError,ValueError):raise UnsupportedCase()
            if (proof.get("driver")!="browser-retired-booking-wizard-v1" or proof.get("legacy_id")!=legacy_id
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!=obs.get("source_path")
                    or proof.get("historical_source_component_id")!=obs.get("component_id")
                    or proof.get("historical_submitted_parameter")!=obs.get("component_id")
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=obs.get("button_markup_sha256")
                    or proof.get("source_hashes")!=source_hashes
                    or proof.get("current_post_handler_absent") is not True or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None):raise UnsupportedCase()
            if actor=="anonymous":
                if proof.get("response_status")!=303 or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:raise UnsupportedCase()
            elif actor=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:raise UnsupportedCase()
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("authorization_denied") is not False
                        or proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True
                        or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
            return proof
        elif legacy_id=="ACTION-32":
            try:rendered=action32_render_record();source_hashes=action32_source_hashes()
            except (OSError,UnsupportedCase,KeyError,ValueError):raise UnsupportedCase()
            if (proof.get("driver")!="browser-retired-destination-next-v1" or proof.get("legacy_id")!="ACTION-32"
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!="/cargo-tracker/booking/booking-destination.xhtml"
                    or proof.get("historical_source_component_id")!=rendered["component_id"]
                    or proof.get("historical_submitted_parameter")!=rendered["component_id"]
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or proof.get("historical_render_evidence_verified") is not True
                    or proof.get("historical_button_markup_sha256")!=rendered["button_markup_sha256"]
                    or proof.get("source_hashes")!=source_hashes or proof.get("current_post_handler_absent") is not True
                    or proof.get("post_target_verified") is not True or proof.get("callback_response_absent") is not True
                    or proof.get("protected_payload_absent") is not True or proof.get("independent_effects_unchanged") is not True
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None
                    or type(proof.get("cargo_snapshot_count")) is not int or proof.get("cargo_snapshot_count")!=13):raise UnsupportedCase()
            if actor=="anonymous":
                if proof.get("response_status")!=303 or proof.get("authorization_denied") is not True or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None:raise UnsupportedCase()
            elif actor=="Reader":
                identity=proof.get("identity",{})
                if proof.get("response_status")!=403 or proof.get("authorization_denied") is not True or identity.get("server_verified") is not True or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]:raise UnsupportedCase()
            else:
                identity=proof.get("identity",{})
                if (proof.get("response_status")!=405 or proof.get("authorization_denied") is not False
                        or proof.get("current_form_verified") is not True or proof.get("current_csrf_present") is not True
                        or proof.get("current_viewstate_present") is not True or identity.get("server_verified") is not True
                        or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
            return proof
        elif legacy_id in {"ACTION-23","ACTION-44"}:
            if legacy_id=="ACTION-23":
                expected={"driver":"browser-retired-tracking-v1","path":"/cargo-tracker/admin/track.xhtml",
                    "component":"trackingForm:trackIdInput","source_hashes":action23_source_hashes()}
                source_verified=(proof.get("callback_implementation_absent") is True
                    and proof.get("legacy_binding_discrepancy_verified") is True)
            else:
                expected={"driver":"browser-retired-public-tracking-v1","path":"/cargo-tracker/public/track.xhtml",
                    "component":"trackingForm:trackingId","source_hashes":action44_source_hashes()}
                source_verified=(proof.get("current_callback_implementation_absent") is True
                    and proof.get("legacy_callback_implementation_verified") is True)
            if (proof.get("driver")!=expected["driver"] or proof.get("legacy_id")!=legacy_id
                    or proof.get("actor")!=actor or proof.get("method")!="POST"
                    or proof.get("source_path")!=expected["path"]
                    or proof.get("historical_source_component_id")!=expected["component"]
                    or proof.get("historical_source_parameter")!="javax.faces.source"
                    or not source_verified or proof.get("source_hashes")!=expected["source_hashes"]
                    or proof.get("post_target_verified") is not True
                    or proof.get("callback_response_absent") is not True
                    or proof.get("autocomplete_payload_absent") is not True
                    or proof.get("protected_payload_absent") is not True
                    or proof.get("independent_effects_unchanged") is not True
                    or re.fullmatch(r"[0-9a-f]{64}",str(proof.get("cargo_snapshot_sha256"))) is None
                    or type(proof.get("cargo_snapshot_count")) is not int
                    or proof.get("cargo_snapshot_count")<1):
                raise UnsupportedCase()
            if actor=="anonymous" and legacy_id=="ACTION-23":
                if (proof.get("response_status")!=303 or proof.get("authorization_denied") is not True
                        or proof.get("redirect_is_configured_login") is not True or proof.get("identity") is not None):raise UnsupportedCase()
            else:
                identity=proof.get("identity");prefix=proof.get("current_source_parameter")
                if (proof.get("response_status")!=200 or proof.get("authorization_denied") is not False
                        or prefix not in {"jakarta.faces.source","javax.faces.source"}
                        or proof.get("current_form_verified") is not True or proof.get("current_legacy_component_absent") is not True
                        or proof.get("current_viewstate_present") is not True
                        or (legacy_id=="ACTION-23" and proof.get("current_csrf_present") is not True)):
                    raise UnsupportedCase()
                if legacy_id=="ACTION-44" and (proof.get("current_callback_implementation_absent") is not True
                        or proof.get("redirect_is_configured_login") is not False):raise UnsupportedCase()
                if actor=="anonymous":
                    if identity is not None:raise UnsupportedCase()
                elif (not isinstance(identity,dict) or identity.get("server_verified") is not True
                        or identity.get("principal")!=USERS[actor] or identity.get("roles")!=[actor]):raise UnsupportedCase()
            return proof
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
            if row.get("status")=="retired" and row["legacy_id"]=="ACTION-08" and reviewed_action08_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-14-kan15-action08-retirement-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"]=="ACTION-23" and reviewed_action23_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-15-kan15-action23-retirement-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"]=="ACTION-44" and reviewed_action44_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-15-kan15-action44-retirement-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"]=="ACTION-26" and reviewed_action26_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-15-kan15-action26-retirement-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"]=="ACTION-32" and reviewed_action32_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-15-kan15-action32-retirement-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"] in {"ACTION-27","ACTION-30","ACTION-34"} and reviewed_action273034_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-16-kan15-actions273034-mapping-promotion-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"] in {"ACTION-28","ACTION-31","ACTION-33"} and reviewed_action283133_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-16-kan15-actions283133-mapping-promotion-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"] in HANDLING_CALLBACK_RETIREMENT_ACTIONS and reviewed_handling_callback_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-17-kan15-handling-callback-promotion-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            elif row.get("status")=="retired" and row["legacy_id"] in HANDLING_PAGE_RETIREMENT_ACTIONS and reviewed_handling_page_retirement_receipt():
                results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"RETIRED","specific_negative_entry_verified":True,"independent_review_verified":True,"review_record":"notes/agent-reviews/2026-11-17-kan15-handling-page-retirement-review.md","outcome_note":"Approved retired entry; RETIRED is never PASS"})
            else:
                try:
                    adapter.execute_retirement(case,current_results)
                    results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"BLOCKED","specific_negative_entry_verified":True,"outcome_note":"Fresh replacement and retired-entry evidence validated; independent review pending, so not RETIRED or PASS"})
                except UnsupportedCase:
                    results.append({"case":case["id"],"legacy_case_id":row["legacy_id"]+"::"+actor+"::active","replacement_case_id":case["replacement_case_id"],"outcome":"BLOCKED","reason":"Replacement and specific fresh negative-entry/review verifier pending; not RETIRED or PASS"})
    return results

def report(live=False):
    adapter=CurrentAdapter(live=live)
    cases=deepcopy(list(adapter.contracts.values()))
    current=run_cases(cases,adapter)
    if live:
        current=apply_bg06_scoped_results(current,adapter.bg06_promotions,adapter.bg06_scope_provenance)
    retirements=retirement_results(adapter._retirement_model,adapter,current)
    audit=run_cases(deepcopy(adapter.legacy_contracts),adapter.legacy if live else legacy.PendingCandidate())
    status=exit_code(current)
    if status==0 and any(r["outcome"]!="RETIRED" for r in retirements):status=2
    retirement_observations=deepcopy(getattr(adapter.legacy,"retirement_observations",{})) if live else {}
    if live:
        callback_observations=getattr(adapter.legacy,"handling_callback_retirement_observations",{})
        overlap=set(retirement_observations)&set(callback_observations)
        if overlap:raise ValueError("Handling callback observations overlap another retirement source")
        retirement_observations.update(deepcopy(callback_observations))
    return {"schema_version":2,"execution":"fresh-owned-runtime" if live else "not executed","current_counts":dict(Counter(r["outcome"] for r in current)),"current_results":current,"retirement_counts":dict(Counter(r["outcome"] for r in retirements)),"retirement_results":retirements,"retirement_observations":retirement_observations,"legacy_audit":{"total":len(audit),"counts":dict(Counter(r["outcome"] for r in audit)),"results":audit},"gate_exit":status,"provenance":adapter.provenance}
