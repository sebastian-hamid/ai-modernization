"""Fresh replacement capabilities with explicit source and return permissions."""
from copy import deepcopy
import re
from contracts import UnsupportedCase

CANCELLATION_READ = "net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"

SUPPORTED_REPLACEMENTS = {
    "cancel-editor": ("GET", ["ACTION-08"]),
    "booking-cancel": ("GET", ["ACTION-28", "ACTION-31", "ACTION-33"]),
    "booking-deadline": ("POST", ["ACTION-26", "ACTION-32"]),
    "booking-single-page": ("POST", ["ACTION-27", "ACTION-30", "ACTION-34"]),
    "handling-single-page": ("GET", ["ACTION-35", "ACTION-40", "ACTION-43"]),
    "handling-cargo-voyage": ("POST", ["ACTION-36"]),
    "handling-location": ("POST", ["ACTION-37"]),
    "tracking-discovery": ("POST", ["ACTION-23", "ACTION-44"]),
}

def unchanged_samples(group, actor, before, after, expected_read_delta=1):
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
    if after_calls.get(CANCELLATION_READ, 0) - before_calls.get(CANCELLATION_READ, 0) != expected_read_delta:
        raise UnsupportedCase()
    if ({key:value for key,value in before_calls.items() if key != CANCELLATION_READ}
            != {key:value for key,value in after_calls.items() if key != CANCELLATION_READ}):
        raise UnsupportedCase()

BOOKING_WRITE = "net.java.cargotracker.application.internal.DefaultBookingService#bookNewCargo"

def positive_booking_samples(before, after, actor, expected_fixture):
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise UnsupportedCase()
    fixture = before.get("fixture_id")
    if not isinstance(fixture, str) or re.fullmatch("[0-9a-f]{64}", fixture) is None or after.get("fixture_id") != fixture:
        raise UnsupportedCase()
    if before.get("stage") != "booking-positive:"+actor+":before" or after.get("stage") != "booking-positive:"+actor+":after":
        raise UnsupportedCase()
    if (not isinstance(before.get("tables"), dict) or not before["tables"]
            or not isinstance(after.get("tables"), dict) or not after["tables"]
            or before["tables"] == after["tables"]):
        raise UnsupportedCase()
    if fixture != expected_fixture:
        raise UnsupportedCase()
    if not isinstance(before.get("queues"), dict) or not before["queues"] or before["queues"] != after.get("queues"):
        raise UnsupportedCase()
    a, b = before.get("business_invocations"), after.get("business_invocations")
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise UnsupportedCase()
    if b.get(BOOKING_WRITE, 0) - a.get(BOOKING_WRITE, 0) != 1 or b.get(CANCELLATION_READ, 0) - a.get(CANCELLATION_READ, 0) != 1:
        raise UnsupportedCase()
    if ({key:value for key,value in a.items() if key not in {BOOKING_WRITE,CANCELLATION_READ}}
            != {key:value for key,value in b.items() if key not in {BOOKING_WRITE,CANCELLATION_READ}}):
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
    if group == "handling-location":
        if proof.get("source_path") != "/cargo-tracker/mobile.xhtml":
            raise UnsupportedCase()
        unchanged_samples(group, actor, proof.get("before"), proof.get("after"), expected_read_delta=1)
        if actor != "anonymous":
            identity=proof.get("identity",{})
            expected={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
            if identity.get("server_verified") is not True or identity.get("principal") != expected or identity.get("roles") != [actor]:
                raise UnsupportedCase()
        if allowed:
            flags=("valid_location_option","valid_location_selection","required_location_rejected",
                   "forged_location_rejected","persisted_cargo_routed")
            if proof.get("source_status") != 200 or not all(proof.get(k) is True for k in flags):
                raise UnsupportedCase()
        else:
            if proof.get("source_status") != (403 if actor == "Reader" else 303) or proof.get("protected_payload_absent") is not True:
                raise UnsupportedCase()
            if actor == "anonymous" and proof.get("source_login_verified") is not True:
                raise UnsupportedCase()
        result=deepcopy(proof)
        result.update(supported=True,semantic_success=allowed,invocation_denied=not allowed,
                      status=proof["source_status"],protected_payload_absent=not allowed,evaluated_stage="source")
        return result
    if group == "handling-cargo-voyage":
        if proof.get("source_path") != "/cargo-tracker/mobile.xhtml":
            raise UnsupportedCase()
        unchanged_samples(group, actor, proof.get("before"), proof.get("after"), expected_read_delta=1)
        if actor != "anonymous":
            identity=proof.get("identity",{})
            expected={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
            if identity.get("server_verified") is not True or identity.get("principal") != expected or identity.get("roles") != [actor]:
                raise UnsupportedCase()
        if allowed:
            flags=("valid_cargo_option","known_voyage_option","valid_cargo_selection","load_requires_voyage","unload_requires_voyage",
                   "valid_voyage_selection","forged_cargo_rejected","forged_voyage_rejected","persisted_cargo_routed")
            if proof.get("source_status") != 200 or not all(proof.get(k) is True for k in flags):
                raise UnsupportedCase()
        else:
            if proof.get("source_status") != (403 if actor == "Reader" else 303) or proof.get("protected_payload_absent") is not True:
                raise UnsupportedCase()
            if actor == "anonymous" and proof.get("source_login_verified") is not True:
                raise UnsupportedCase()
        result=deepcopy(proof)
        result.update(supported=True,semantic_success=allowed,invocation_denied=not allowed,
                      status=proof["source_status"],protected_payload_absent=not allowed,evaluated_stage="source")
        return result
    if group == "handling-single-page":
        if (proof.get("source_path") != "/cargo-tracker/mobile.xhtml"
                or proof.get("entry_source") != "admin/dashboard.xhtml"):
            raise UnsupportedCase()
        unchanged_samples(group, actor, proof.get("before"), proof.get("after"), expected_read_delta=1)
        if actor != "anonymous":
            identity=proof.get("identity",{})
            expected={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
            if identity.get("server_verified") is not True or identity.get("principal") != expected or identity.get("roles") != [actor]:
                raise UnsupportedCase()
        if allowed:
            flags=("dashboard_url_verified","entry_link_verified","entry_chain_verified","all_fields_same_form","unsaved_edits_verified","invalid_calendar_rejected",
                   "missing_voyage_rejected","leave_navigation_verified","persisted_state_unchanged")
            if proof.get("source_status") != 200 or proof.get("return_status") != 200 or proof.get("return_path") != "/cargo-tracker/admin/dashboard.xhtml" or not all(proof.get(k) is True for k in flags):
                raise UnsupportedCase()
        else:
            if proof.get("return_status") is not None or proof.get("source_status") != (403 if actor == "Reader" else 303) or proof.get("protected_payload_absent") is not True:
                raise UnsupportedCase()
            if actor == "anonymous" and proof.get("source_login_verified") is not True:
                raise UnsupportedCase()
        result=deepcopy(proof)
        result.update(supported=True,semantic_success=allowed,invocation_denied=not allowed,
                      status=proof["source_status"],protected_payload_absent=not allowed,evaluated_stage="source")
        return result
    if group in {"booking-deadline", "booking-single-page"}:
        if proof.get("source_path") != "/cargo-tracker/admin/book.xhtml" or proof.get("source_entry_verified") is not True:
            raise UnsupportedCase()
        unchanged_samples(group, actor, proof.get("before"), proof.get("after"), expected_read_delta=0)
        if actor != "anonymous":
            identity=proof.get("identity",{})
            expected={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
            if identity.get("server_verified") is not True or identity.get("principal") != expected or actor not in identity.get("roles",[]):
                raise UnsupportedCase()
        if allowed:
            if proof.get("valid_booking_created") is not True or proof.get("source_status") != 200 or proof.get("invalid_deadline_rejected") is not True:
                raise UnsupportedCase()
            if proof.get("booking_post_status") not in {302,303} or proof.get("booking_location_verified") is not True or proof.get("booking_result_tracking_id") != proof.get("tracking_id"):
                raise UnsupportedCase()
            if proof.get("independent_persisted_booking") is not True or proof.get("positive_effects_verified") is not True:
                raise UnsupportedCase()
            positive_booking_samples(proof.get("positive_before"),proof.get("positive_after"),actor,proof.get("before",{}).get("fixture_id"))
            if group == "booking-single-page" and proof.get("all_fields_same_form") is not True:
                raise UnsupportedCase()
        else:
            if proof.get("valid_booking_created") is not False or proof.get("source_status") != (403 if actor == "Reader" else 303) or proof.get("source_payload_absent") is not True:
                raise UnsupportedCase()
            if actor == "anonymous" and proof.get("source_login_verified") is not True:
                raise UnsupportedCase()
        result = deepcopy(proof)
        result.update(supported=True, semantic_success=allowed, invocation_denied=not allowed,
                      status=proof["source_status"], protected_payload_absent=not allowed,
                      evaluated_stage="source")
        return result
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
