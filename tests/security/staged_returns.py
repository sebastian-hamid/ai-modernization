"""ACTION-13 editor and readable-details policy, with explicit response stages."""
from copy import deepcopy
import re
from urllib.parse import urlsplit, parse_qsl
from contracts import UnsupportedCase

def return_observation(case, proof):
    if (case.get("surface_id") != "ACTION-13" or case.get("method") != "GET"
            or case.get("path") != "/cargo-tracker/admin/show.xhtml?trackingId={cargo}"
            or case.get("current_source") != "admin/changeDestination.xhtml"):
        raise UnsupportedCase()
    actor = case["actor"]
    tracking = proof.get("tracking_id")
    if re.fullmatch("[A-Z0-9]{8}", str(tracking)) is None:
        raise UnsupportedCase()
    editor = proof.get("editor", {})
    details = proof.get("details", {})
    editor_path = "/cargo-tracker/admin/changeDestination.xhtml?trackingId=" + tracking
    details_path = "/cargo-tracker/admin/show.xhtml?trackingId=" + tracking
    if proof.get("return_driver") != "native-staged-return-v1":
        raise UnsupportedCase()
    if (editor.get("method"), editor.get("path")) != ("GET", editor_path):
        raise UnsupportedCase()
    if (details.get("method"), details.get("path")) != ("GET", details_path):
        raise UnsupportedCase()
    permitted_editor = actor in {"Operator", "Administrator"}
    permitted_details = actor in {"Reader", "Operator", "Administrator"}
    save = proof.get("save")
    if permitted_editor:
        if editor.get("status") != 200 or editor.get("owned_form_verified") is not True:
            raise UnsupportedCase()
        if not isinstance(save, dict):
            raise UnsupportedCase()
        if (save.get("method"), save.get("path")) != ("POST", editor_path):
            raise UnsupportedCase()
        location = urlsplit(save.get("location", ""))
        try:
            pairs = parse_qsl(location.query, keep_blank_values=True, strict_parsing=True)
        except ValueError:
            raise UnsupportedCase()
        query = dict(pairs)
        origin_valid = not location.scheme and not location.netloc
        if location.scheme or location.netloc:
            fixture = urlsplit(proof.get("fixture_base", ""))
            origin_valid = (
                fixture.scheme in {"http", "https"}
                and bool(fixture.netloc) and fixture.username is None and fixture.password is None
                and fixture.path == "/cargo-tracker/" and not fixture.query and not fixture.fragment
                and (location.scheme, location.netloc) == (fixture.scheme, fixture.netloc)
                and location.username is None and location.password is None
            )
        if (save.get("status") not in {302, 303}
                or not origin_valid or location.fragment
                or location.path != details_path.split("?")[0]
                or len(query) != len(pairs) or set(query) - {"trackingId", "jfwid"}
                or query.get("trackingId") != tracking or not all(query.values())):
            raise UnsupportedCase()
        required = ("csrf_verified", "persisted_effect_verified", "deadline_preserved", "other_cargos_unchanged")
        if any(save.get(key) is not True for key in required):
            raise UnsupportedCase()
        if save.get("destination_invocation_delta") != 1 or type(save.get("destination_invocation_delta")) is not int:
            raise UnsupportedCase()
        if save.get("queues_unchanged") is not True:
            raise UnsupportedCase()
    else:
        expected = 403 if actor == "Reader" else 303
        if editor.get("status") != expected or editor.get("protected_payload_absent") is not True:
            raise UnsupportedCase()
        if actor == "anonymous" and editor.get("redirect_is_configured_login") is not True:
            raise UnsupportedCase()
        if save is not None or proof.get("denied_entry_effects_unchanged") is not True:
            raise UnsupportedCase()
    if permitted_details:
        if details.get("status") != 200 or details.get("selected_details_verified") is not True:
            raise UnsupportedCase()
    elif details.get("status") != 303 or not all(details.get(key) is True for key in ("protected_payload_absent", "redirect_is_configured_login")):
        raise UnsupportedCase()
    result = deepcopy(proof)
    result.update(supported=True, status=details["status"] if permitted_editor else editor["status"],
                  semantic_success=permitted_editor, evaluated_stage="details" if permitted_editor else "editor",
                  protected_payload_absent=editor.get("protected_payload_absent", False),
                  redirect_is_configured_login=editor.get("redirect_is_configured_login", False))
    return result
