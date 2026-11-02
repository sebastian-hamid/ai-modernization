#!/usr/bin/env python3
"""Owned app + Chromium fixture; no shared services, no browser credential persistence."""
from pathlib import Path
import importlib.util,json,subprocess,uuid,hashlib
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("candidate_runtime",ROOT/"tests/candidate-runtime/run_candidate.py")
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
WORK=ROOT/".work/kan19"
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
    if len(mapping)!=6 or len(expected)!=24 or set(proofs)!=set(expected):raise AssertionError("Missing or unexpected navigation action proof")
    users={"Reader":"reader","Operator":"operator","Administrator":"admin"}
    for key,(row,role) in expected.items():
        proof=proofs[key];allowed=row["anonymous"] if role=="anonymous" else role in row["allowed_roles"]
        source="index.xhtml" if role=="anonymous" and not row["anonymous"] else row["source_page"]
        direct=not allowed and (row["id"] in {"ACTION-02","ACTION-05"})
        if not (proof.get("supported") is True and proof.get("action_executed") is True and proof.get("target")==row["target"] and proof.get("source_page")==source and proof.get("driver")==("direct" if direct else "click")):raise AssertionError("Invalid navigation action driver")
        keys=proof.get("query_keys")
        if proof.get("target_origin_verified") is not True or proof.get("actual_target_path")!="/cargo-tracker/"+row["target"] or keys not in [[],["jfwid"]]:raise AssertionError("Unexpected navigation response URL")
        if direct and proof.get("control_hidden") is not True:raise AssertionError("Forbidden navigation control was exposed")
        if role!="anonymous":
            identity=proof.get("identity",{})
            if identity.get("server_verified") is not True or identity.get("principal")!=users[role] or role not in identity.get("roles",[]):raise AssertionError("Invalid native navigation identity")
        if allowed:
            if proof.get("status")!=200 or proof.get("semantic_success") is not True:raise AssertionError("Missing navigation destination semantics")
            if row["kind"] in {"list","live"} and proof.get("cargo_observed")!="ABC123":raise AssertionError("Missing actual cargo after navigation")
            if row["kind"]=="live" and proof.get("socket_live") is not True:raise AssertionError("Missing live navigation transport")
            if row["kind"] in {"booking","lookup"} and proof.get("form_observed") is not True:raise AssertionError("Missing navigation form")
            if role=="anonymous" and proof.get("protected_payload_absent") is not True:raise AssertionError("Public navigation leakage unchecked")
        elif proof.get("status")!=(303 if role=="anonymous" else 403) or proof.get("protected_payload_absent") is not True or role=="anonymous" and proof.get("redirect_is_configured_login") is not True:raise AssertionError("Invalid navigation denial")
    report["access_observations"].update(proofs)
    report["navigation_action_observations"]=proofs

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    name="ai-modernization-kan19-browser"
    if subprocess.run(["docker","inspect",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise RuntimeError("Browser container already exists")
    with (WORK/"browser-build.log").open("w") as log:
        build=subprocess.run(["docker","build","-t","ai-modernization-kan19:browser",str(ROOT/"tests/browser-workflows")],stdout=log,stderr=subprocess.STDOUT)
    if build.returncode:raise RuntimeError("Browser build failed")
    # Browser credentials travel over stdin to tmpfs, not env/argv/image or bind-mounted results.
    def browser(container,base,credentials,report):
        network=None;bid=None
        try:
            network=subprocess.check_output(["docker","network","create","--internal","ai-modernization-kan19-"+uuid.uuid4().hex[:12]],text=True).strip()
            subprocess.run(["docker","network","connect",network,container],check=True,capture_output=True)
            bid=subprocess.check_output(["docker","create","--name",name,"--init","--network",network,"--shm-size=512m","--tmpfs","/run:rw,noexec,nosuid,size=1m","--tmpfs","/out:rw,noexec,nosuid,size=8m","-i","ai-modernization-kan19:browser","sleep","infinity"],text=True).strip()
            subprocess.run(["docker","start",bid],check=True,capture_output=True)
            proc=subprocess.run(["docker","exec","-i",bid,"bash","-c","umask 077; cat > /run/credentials.json; node workflows.cjs"],input=json.dumps({"base":"http://"+app.NAME+":8080/cargo-tracker/","credentials":credentials,"fixture_tracking_id":report["page_fixture_tracking_id"]}),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
            # Store raw diagnostics privately; never publish browser HTML/traces/session dumps.
            (WORK/"browser.log").write_text(proc.stdout)
            (WORK/"results.json").write_text(subprocess.check_output(["docker","exec",bid,"cat","/out/results.json"],text=True))
            results=json.loads((WORK/"results.json").read_text())
            report["browser_checks"]={"count":len(results["checks"]),"passed":all(c["passed"] for c in results["checks"])}
            if proc.returncode or not report["browser_checks"]["passed"]:raise AssertionError("Real browser workflow failed; inspect sanitized .work/kan19/results.json")
            promote_live_pages(report,results)
            promote_socket_cases(report,results)
            promote_navigation_actions(report,results)
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
