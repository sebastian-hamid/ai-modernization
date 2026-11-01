"""Fail-closed oracle for candidate adapters. Unit doubles do not prove application security."""
class UnsupportedCase(Exception):pass

def evaluate(case,observation):
    if not observation.get("supported",False):return "BLOCKED","Required candidate adapter/observer is unavailable"
    status=observation.get("status")
    if case["expected"]=="deny":
        if case["channel"]=="private":valid=status in {403,404}
        elif case["channel"]=="socket":valid=status in {401,403} and observation.get("upgraded") is False
        elif case["channel"] in {"api","session"} and case.get("original_channel",case["channel"]) in {"api","socket"}:
            valid=status==(401 if case["actor"]=="anonymous" or case["channel"]=="session" else 403)
        elif case["channel"] in {"page","session","action"}:
            valid=status==(401 if case["actor"]=="anonymous" or case["channel"]=="session" else 403)
            if status in {302,303}:
                valid=(case["actor"]=="anonymous" or case["channel"]=="session") and observation.get("redirect_is_configured_login") is True
        else:valid=observation.get("invocation_denied") is True
        if case["channel"]=="session" and case.get("original_channel")=="socket":
            if observation.get("upgraded") is not False:return "FAIL","Revoked socket credentials allowed or did not disprove upgrade"
            if observation.get("post_revocation_frame_received") is True:return "FAIL","Revoked socket received protected frames"
            if observation.get("existing_socket_closed") is not True or observation.get("post_revocation_frame_received") is not False:
                return "BLOCKED","Existing socket closure and no post-revocation frames must be observed"
        if not valid:return "FAIL","Expected authorization denial, not success, arbitrary redirect or server error"
        if observation.get("protected_payload_absent") is not True:return "BLOCKED","Denial payload leakage must be inspected"
        if case["channel"]=="session":
            if observation.get("authenticated_before_revocation") is not True or observation.get("revocation_verified") is not True:
                return "BLOCKED","Logout/expiry lifecycle has not been exercised"
        if case.get("write"):
            effects=observation.get("effects")
            if not effects or effects.get("settled") is not True:return "BLOCKED","Fresh database/queue/audit observations after worker settlement required"
            for domain in ["database","queue","business_audit"]:
                before=effects.get("before",{}).get(domain);after=effects.get("after",{}).get(domain)
                if not isinstance(before,dict) or not before or not isinstance(after,dict) or not after:
                    return "BLOCKED","Missing independent side-effect channel: "+domain
                if before!=after:return "FAIL","Denied action changed "+domain
            if not effects.get("fixture_id") or effects.get("before_fixture")!=effects["fixture_id"] or effects.get("after_fixture")!=effects["fixture_id"]:
                return "BLOCKED","Observer samples must belong to the same isolated fixture"
        if case["actor"] in {"Reader","Operator","Administrator"}:
            identity=observation.get("identity",{})
            if identity.get("server_verified") is not True or not identity.get("principal") or case["actor"] not in identity.get("roles",[]):
                return "BLOCKED","Denied role must be verified (before revocation for session cases)"
        return "PASS","Desired denial observed with required evidence"
    if case["actor"]=="anonymous":
        if observation.get("protected_payload_absent") is False:return "FAIL","Public response leaked protected data"
        if observation.get("protected_payload_absent") is not True:return "BLOCKED","Public response requires a no-leak inspection"
    # Successful responses on an open legacy endpoint are not proof of a role-aware login.
    if case.get("required_machine_scope"):
        if observation.get("machine_identity_verified") is not True or observation.get("machine_scope")!=case["required_machine_scope"]:
            return "BLOCKED","Scoped machine identity must be independently verified"
    elif case["actor"]!="anonymous":
        identity=observation.get("identity",{})
        if identity.get("server_verified") is not True or not identity.get("principal") or case["actor"] not in identity.get("roles",[]):
            return "BLOCKED","Authenticated principal/role must be verified by server evidence"
    if case["channel"] in {"page","api","action","socket"}:
        if case["channel"]=="socket": valid=status==101
        else: valid=isinstance(status,int) and 200<=status<300
        if not valid:return "FAIL","Allowed request did not complete successfully"
    if observation.get("semantic_success") is not True:return "FAIL","Allowed workflow result or real data/event effect missing"
    if case["channel"]=="socket" and observation.get("authorized_frame_received") is not True:return "BLOCKED","Handshake alone does not prove authorized message delivery"
    if case.get("write") and observation.get("authorized_effect_verified") is not True:return "BLOCKED","Allowed mutation/worker effect not verified"
    return "PASS","Allowed workflow and identity evidence observed"

def run_cases(cases,adapter):
    output=[]
    for case in cases:
        try:state,reason=evaluate(case,adapter.execute(case))
        except (UnsupportedCase,NotImplementedError):state,reason="BLOCKED","Required candidate adapter is unavailable"
        except Exception as error:state,reason="ERROR",type(error).__name__ # Do not leak credentials from adapter exception text.
        output.append({"case":case["id"],"outcome":state,"reason":reason})
    return output

def exit_code(results):
    if not results:return 2
    if any(x["outcome"] in {"FAIL","ERROR"} for x in results):return 1
    if any(x["outcome"]=="BLOCKED" for x in results):return 2
    return 0
