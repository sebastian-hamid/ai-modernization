"""Fresh replacement capabilities with explicit source and return permissions."""
from copy import deepcopy
import re
from contracts import UnsupportedCase

CANCELLATION_READ = "net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"

SUPPORTED_REPLACEMENTS = {
    "cancel-editor": ("GET", ["ACTION-08"]),
    "booking-cancel": ("GET", ["ACTION-28", "ACTION-31", "ACTION-33"]),
    "tracking-discovery": ("POST", ["ACTION-23", "ACTION-44"]),
}

def unchanged_samples(group, actor, before, after):
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise UnsupportedCase()
    fixture = before.get("fixture_id")
    if not isinstance(fixture, str) or re.fullmatch("[0-9a-f]{64}", fixture) is None:
        raise UnsupportedCase()
    if after.get("fixture_id") != fixture:
        raise UnsupportedCase()
    if before.get("stage") != group + ":" + actor + ":before":
        raise UnsupportedCase()
    if after.get("stage") != group + ":" + actor + ":after":
        raise UnsupportedCase()
    for channel in ("tables", "queues", "business_invocations"):
        if not isinstance(before.get(channel), dict) or not before[channel] or not isinstance(after.get(channel), dict):
            raise UnsupportedCase()
        if channel != "business_invocations" and before[channel] != after[channel]:
            raise UnsupportedCase()
    before_calls = before["business_invocations"]
    after_calls = after["business_invocations"]
    if after_calls.get(CANCELLATION_READ, 0) - before_calls.get(CANCELLATION_READ, 0) != 1:
        raise UnsupportedCase()
    if ({key:value for key,value in before_calls.items() if key != CANCELLATION_READ}
            != {key:value for key,value in after_calls.items() if key != CANCELLATION_READ}):
        raise UnsupportedCase()

def replacement_observation(case, proof):
    group = case["capability_id"]
    if group not in SUPPORTED_REPLACEMENTS or case.get("binding_status") != "browser-replacement-v1":
        raise UnsupportedCase()
    method, legacy_ids = SUPPORTED_REPLACEMENTS[group]
    if case.get("method") != method or case.get("legacy_ids") != legacy_ids:
        raise UnsupportedCase()
    tracking = proof.get("tracking_id")
    if re.fullmatch("[A-Z0-9]{8}", str(tracking)) is None:
        raise UnsupportedCase()
    if proof.get("replacement_driver") != "browser-replacement-v1" or proof.get("group") != group:
        raise UnsupportedCase()
    actor = case["actor"]
    if group == "tracking-discovery":
        return discovery_observation(case, proof)
    allowed = actor in {"Operator", "Administrator"}
    source = "/cargo-tracker/admin/book.xhtml"
    target = "/cargo-tracker/admin/dashboard.xhtml"
    if group == "cancel-editor":
        source = "/cargo-tracker/admin/changeDestination.xhtml?trackingId=" + tracking
        target = "/cargo-tracker/admin/show.xhtml?trackingId=" + tracking
    if proof.get("source_path") != source or proof.get("target_path") != target:
        raise UnsupportedCase()
    if proof.get("source_entry_verified") is not True or proof.get("return_access_verified") is not True:
        raise UnsupportedCase()
    unchanged_samples(group, actor, proof.get("before"), proof.get("after"))
    if proof.get("persisted_state_unchanged") is not True:
        raise UnsupportedCase()
    if allowed:
        if proof.get("source_status") != 200 or proof.get("target_status") != 200:
            raise UnsupportedCase()
        if proof.get("unsaved_edits_verified") is not True or proof.get("leave_navigation_verified") is not True:
            raise UnsupportedCase()
    else:
        if proof.get("source_status") != (403 if actor == "Reader" else 303):
            raise UnsupportedCase()
        if proof.get("source_payload_absent") is not True:
            raise UnsupportedCase()
        if actor == "Reader":
            if proof.get("target_status") != 200:
                raise UnsupportedCase()
        elif proof.get("target_status") != 303 or not all(proof.get(key) is True for key in (
                "source_login_verified", "target_login_verified", "target_payload_absent")):
            raise UnsupportedCase()
    result = deepcopy(proof)
    result.update(supported=True, semantic_success=allowed, invocation_denied=not allowed,
                  status=proof["target_status"] if allowed else proof["source_status"],
                  protected_payload_absent=proof.get("source_payload_absent", False),
                  evaluated_stage="return" if allowed else "source")
    return result

def discovery_observation(case, proof):
    actor = case["actor"]
    allowed = actor in {"Reader", "Operator", "Administrator"}
    listing = proof.get("list_proof", {})
    lookup = proof.get("lookup_proof", {})
    tracking = proof["tracking_id"]
    if listing.get("tracking_id") != tracking or lookup.get("tracking_id") != tracking:
        raise UnsupportedCase()
    if listing.get("current_navigation_driver") != "browser-claimed-cargo-v1":
        raise UnsupportedCase()
    if (listing.get("actual_target_path") != "/cargo-tracker/admin/show.xhtml"
            or not all(listing.get(key) is True for key in ("action_executed", "target_origin_verified"))
            or sorted(listing.get("query_keys", [])) not in (["trackingId"], ["jfwid", "trackingId"])):
        raise UnsupportedCase()
    if lookup.get("current_navigation_driver") != "browser-lookup-v1":
        raise UnsupportedCase()
    if (lookup.get("action_method"), lookup.get("action_path"), lookup.get("entry_page")) != (
            "POST", "/cargo-tracker/admin/track.xhtml", "admin/track.xhtml"):
        raise UnsupportedCase()
    if lookup.get("source_entry_verified") is not True:
        raise UnsupportedCase()
    if allowed:
        for item in (listing, lookup):
            if item.get("identity") != proof.get("identity") or item.get("status") != 200 or item.get("driver") != "click":
                raise UnsupportedCase()
            if not all(item.get(key) is True for key in ("semantic_success", "selected_cargo_verified", "persisted_details_verified")):
                raise UnsupportedCase()
        if listing.get("source_page") != "admin/listClaimed.xhtml":
            raise UnsupportedCase()
        if lookup.get("submission_status") not in {302, 303} or not all(lookup.get(key) is True for key in ("invalid_inputs_verified", "csrf_checks_verified")):
            raise UnsupportedCase()
    else:
        for item in (listing, lookup):
            if item.get("identity") is not None or item.get("status") != 303 or item.get("driver") != "direct":
                raise UnsupportedCase()
            if not all(item.get(key) is True for key in ("protected_payload_absent", "redirect_is_configured_login")):
                raise UnsupportedCase()
        if listing.get("source_page") != "index.xhtml":
            raise UnsupportedCase()
        if listing.get("claimed_list_denied") is not True or lookup.get("lookup_source_denied") is not True:
            raise UnsupportedCase()
    result = deepcopy(proof)
    result.update(supported=True, semantic_success=allowed, invocation_denied=not allowed,
                  status=200 if allowed else 303, protected_payload_absent=not allowed)
    return result
