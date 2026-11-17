"""Build and verify hook-specific retirement evidence for KAN-15 ACTION-43."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "notes/evidence/kan-15-handling-page-retirement"
OUTPUT = ROOT / "notes/evidence/kan-15-action43-hook/validation.json"
SOURCE_REVISION = "ffcb67714f77866e7659d4547909ebb3305f901e"
LEGACY_REVISION = "57fc7b32d2597e43b5e0d454e707e0146de5258a"
PINNED = {
    "candidate-runtime-results.json": "637f8b53c5a52c5e799b99516ffa8136492cbbb39110ab63845f6e69bc3f8ff1",
    "browser-results.json": "eac9cf910aa529352709d74952d6e068a7aa8c5044f96c5ddf0f2825543609f6",
    "current-capability-gate.json": "96c59c67f207af4cd5d6fb8364e4a7a3471c1fac339abe0534737ca36f72a74e",
}
LEGACY_PAGE = Path("experiments/legacy-cargotracker/src/main/webapp/mobile.xhtml")
CANDIDATE_PAGE = Path("candidate/cargotracker/src/main/webapp/mobile.xhtml")
HOLDER_BEAN = Path("candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/handling/mobile/HolderBean.java")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_hook_markup(legacy, candidate, candidate_facelets, bean):
    binding = '<f:viewAction action="#{holderBean.initFlow}" />'
    if legacy.count(binding) != 1:
        raise ValueError("The legacy mobile view no longer contains the exact ACTION-43 hook")
    bound = [name for name, content in candidate_facelets if "#{holderBean.initFlow}" in content]
    if bound:
        raise ValueError("The old initFlow hook remains bound from candidate Facelets: " + ", ".join(bound))
    if ('id="handling"' not in candidate or 'action="#{handlingPages.submit}"' not in candidate
            or "Report handling" not in candidate or "<f:viewAction" in candidate):
        raise ValueError("The candidate mobile page is not the expected direct handling form")
    # Record that the method remains. This proof concerns the old page hook, not
    # removal of all old flow classes or resources.
    method_retained = bool(re.search(r"public\s+String\s+initFlow\s*\(\)", bean))
    if not method_retained:
        raise ValueError("Candidate HolderBean changed; review the proof boundary")
    return binding, bound, method_retained


def source_evidence():
    legacy = (ROOT / LEGACY_PAGE).read_text()
    candidate = (ROOT / CANDIDATE_PAGE).read_text()
    facelets = sorted((ROOT / "candidate/cargotracker/src/main/webapp").rglob("*.xhtml"))
    facelet_contents = [(str(p.relative_to(ROOT)), p.read_text()) for p in facelets]
    bean = (ROOT / HOLDER_BEAN).read_text()
    binding, bound, method_retained = validate_hook_markup(legacy, candidate, facelet_contents, bean)
    paths = (LEGACY_PAGE, CANDIDATE_PAGE, HOLDER_BEAN)
    return {
        "legacy_action": "ACTION-43", "legacy_path": "/cargo-tracker/mobile.xhtml",
        "legacy_source_revision": LEGACY_REVISION,
        "legacy_binding": binding, "legacy_binding_count": 1,
        "candidate_same_url_is_replacement": True,
        "candidate_init_flow_facelet_bindings": bound,
        "candidate_handling_form_present": True,
        "candidate_holderbean_initflow_method_retained": method_retained,
        "source_hashes": {str(p): sha256((ROOT / p).read_bytes()) for p in paths},
        "candidate_facelet_count_scanned": len(facelets),
        "candidate_facelet_paths_scanned": [name for name, _ in facelet_contents],
    }


def runtime_evidence():
    artifact_hashes = {}
    for name, expected in PINNED.items():
        raw = (RUN / name).read_bytes()
        if sha256(raw) != expected:
            raise ValueError("Fresh KAN-15 source evidence changed: " + name)
        artifact_hashes[name] = {"path": str((RUN / name).relative_to(ROOT)), "sha256": expected}
    candidate = json.loads((RUN / "candidate-runtime-results.json").read_text())
    browser = json.loads((RUN / "browser-results.json").read_text())
    gate = json.loads((RUN / "current-capability-gate.json").read_text())
    if (candidate.get("status") != "PASS" or candidate.get("count") != 777
            or candidate.get("owned_container_removed") is not True
            or candidate.get("private_files_removed") is not True or candidate.get("cleanup_errors") != []):
        raise ValueError("Fresh candidate runtime or cleanup evidence is incomplete")
    if len(browser.get("checks", [])) != 970 or any(x.get("passed") is not True for x in browser["checks"]):
        raise ValueError("Fresh browser suite is incomplete or has failures")
    if gate.get("execution") != "fresh-owned-runtime" or gate.get("current_counts") != {"PASS": 470}:
        raise ValueError("Fresh capability gate does not show all current cases passing")
    blocked = {x.get("case") for x in gate.get("retirement_results", []) if x.get("outcome") == "BLOCKED"}
    expected_blocked = {f"RETIREMENT::ACTION-43::{a}" for a in ("anonymous", "Reader", "Operator", "Administrator")}
    if not expected_blocked.issubset(blocked):
        raise ValueError("Fresh gate no longer records ACTION-43 as BLOCKED")

    actors = {}
    results = browser.get("replacement_actions", {})
    statuses = {"anonymous": 303, "Reader": 403, "Operator": 200, "Administrator": 200}
    for actor, status in statuses.items():
        proof = results.get("REPLACEMENT::handling-single-page::" + actor)
        if not isinstance(proof, dict) or proof.get("source_path") != "/cargo-tracker/mobile.xhtml" or proof.get("source_status") != status:
            raise ValueError("Missing same-path handling replacement proof for " + actor)
        before, after = proof.get("before", {}), proof.get("after", {})
        business_before = before.get("business_invocations", {})
        business_after = after.get("business_invocations", {})
        deltas = {key: business_after.get(key, 0) - business_before.get(key, 0)
                  for key in set(business_before) | set(business_after)
                  if business_after.get(key, 0) != business_before.get(key, 0)}
        expected_read = "net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"
        same = (before.get("fixture_id") == after.get("fixture_id")
                and before.get("tables") == after.get("tables")
                and before.get("queues") == after.get("queues")
                and deltas == {expected_read: 1})
        if not same or not before.get("tables") or not before.get("queues") or not business_before:
            raise ValueError("Replacement request changed domain/queue effects or had unexpected service effects for " + actor)
        row = {"status": status, "effects_unchanged": True}
        if actor == "anonymous":
            if proof.get("source_login_verified") is not True or proof.get("protected_payload_absent") is not True:
                raise ValueError("Anonymous replacement did not redirect to login without protected content")
            row.update(login_redirect_verified=True, protected_payload_absent=True)
        elif actor == "Reader":
            identity = proof.get("identity", {})
            if proof.get("protected_payload_absent") is not True or identity != {"server_verified": True, "principal": "reader", "roles": ["Reader"]}:
                raise ValueError("Reader denial or server identity is incomplete")
            row.update(protected_payload_absent=True, server_identity=identity)
        else:
            identity = proof.get("identity", {})
            expected_identity = {"server_verified": True, "principal": "operator" if actor == "Operator" else "admin", "roles": [actor]}
            flags = ("entry_link_verified", "entry_chain_verified", "all_fields_same_form", "unsaved_edits_verified",
                     "invalid_calendar_rejected", "missing_voyage_rejected", "leave_navigation_verified", "persisted_state_unchanged")
            if identity != expected_identity or not all(proof.get(f) is True for f in flags):
                raise ValueError("Authorized replacement workflow or identity evidence is incomplete for " + actor)
            row.update(server_identity=identity, replacement_form_and_workflow_verified=True)
        actors[actor] = row
    return {"run_id": "kan15-handling-pages-d", "source_revision": SOURCE_REVISION,
            "candidate_checks": 777, "browser_checks": 970, "current_capability_counts": gate["current_counts"],
            "cleanup_verified": True, "artifact_hashes": artifact_hashes, "actor_observations": actors}


def build_validation():
    prior = json.loads((ROOT / "notes/evidence/kan-16-anonymous-operational-access/validation.json").read_text())
    run = prior["fresh_candidate_run"]
    if run.get("run_id") != "kan15-handling-pages-d" or run.get("source_revision") != SOURCE_REVISION:
        raise ValueError("Fresh run identity/source revision does not match the hook evidence scope")
    source = source_evidence()
    inventory = json.loads((ROOT / "specifications/access-policy-inventory.json").read_text())
    if inventory.get("source_commit") != LEGACY_REVISION or inventory.get("source_sha256", {}).get("src/main/webapp/mobile.xhtml") != source["source_hashes"][str(LEGACY_PAGE)]:
        raise ValueError("Historical mobile page differs from the approved source inventory")
    for rel in (CANDIDATE_PAGE, HOLDER_BEAN):
        committed = subprocess.run(["git", "show", f"{SOURCE_REVISION}:{rel.as_posix()}"], cwd=ROOT,
                                   check=True, capture_output=True).stdout
        if sha256(committed) != source["source_hashes"][str(rel)]:
            raise ValueError("Current source differs from the exact fresh-run revision: " + str(rel))
    return {
        "task": "KAN-15 ACTION-43 old initFlow page-hook proof",
        "result": "HOOK_SPECIFIC_PROOF_VERIFIED_PENDING_USER_RETIREMENT_DECISION",
        "date": "2026-11-17", "source_evidence": source, "fresh_run_evidence": runtime_evidence(),
        "limits": [
            "The historical f:viewAction binding is absent from candidate Facelets; the same URL serves the role-protected current handling page.",
            "The HolderBean.initFlow method and old flow resources remain in the candidate; this proves only that the old page hook is unbound.",
            "The fresh run did not instrument direct Java method invocation counts. Runtime replacement checks are combined with source-bound Facelet inspection; no production behavior is claimed.",
            "ACTION-43 remains BLOCKED pending independent review and the user's retirement decision. RETIRED would never count as PASS.",
        ],
    }


def main():
    receipt = build_validation()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"result": receipt["result"], "output": str(OUTPUT.relative_to(ROOT)),
                      "candidate_checks": 777, "browser_checks": 970}, indent=2))


if __name__ == "__main__":
    main()