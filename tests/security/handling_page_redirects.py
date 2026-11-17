"""Strict validation for actor-specific legacy handling redirects."""
from urllib.parse import urljoin,urlsplit

def is_safe_handling_redirect(proof,expected_target):
    if not isinstance(proof,dict):return False
    origin=proof.get("application_origin");context=proof.get("application_context_path")
    if not isinstance(origin,str) or not isinstance(context,str):return False
    base=urlsplit(origin)
    if (base.scheme not in {"http","https"} or not base.netloc or base.username or base.password
            or base.path not in {"","/"} or base.query or base.fragment):return False
    if context and (not context.startswith("/") or context.endswith("/") or "//" in context
                    or any(part in {".",".."} for part in context.split("/"))):return False
    location=proof.get("redirect_location")
    if expected_target is None:
        return location in (None,"") and proof.get("redirect_target") is None
    if not isinstance(location,str) or not location:return False
    resolved=urlsplit(urljoin(origin+context+"/",location))
    return (resolved.scheme.lower()==base.scheme.lower() and resolved.netloc.lower()==base.netloc.lower()
            and not resolved.username and not resolved.password and resolved.path==context+expected_target
            and not resolved.query and not resolved.fragment and proof.get("redirect_target")==expected_target)
