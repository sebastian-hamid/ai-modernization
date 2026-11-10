#!/usr/bin/env python3
"""Generate desired policy cases, not baseline-success expectations."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
ACTORS=["anonymous","Reader","Operator","Administrator"]

def build(inventory):
    cases=[]
    def add(surface,channel,actor,allowed,write=False,**extra):
        cases.append(dict(id=surface["id"]+"::"+actor+"::"+extra.get("session_state","active"),surface_id=surface["id"],channel=channel,actor=actor,expected="allow" if allowed else "deny",write=write,source=surface.get("source",surface.get("entry")),path=surface.get("path"),method=surface.get("method","GET"),**extra))
    for row in inventory["pages"]:
        for actor in ACTORS:
            allow=row["anonymous"] if actor=="anonymous" else actor in row["allowed_roles"]
            add(row,"page",actor,allow,classification=row["classification"])
        for actor in row["allowed_roles"]:
            if not row["anonymous"]:
                for state in ["logged_out","expired"]:add(row,"session",actor,False,session_state=state)
    for row in inventory["view_callbacks"]:
        for actor in ACTORS:
            allow=row["anonymous"] if actor=="anonymous" else actor in row["allowed_roles"]
            add(row,"action",actor,allow,write=row["domain_mutation"],callback=row["expression"],source_line=row["line"],page_id=row["page_id"],requires_real_browser_or_action_driver=True)
        if row["domain_mutation"]:
            for actor in row["allowed_roles"]:
                for state in ["logged_out","expired"]:
                    add(row,"session",actor,False,write=True,session_state=state,original_channel="action",callback=row["expression"],page_id=row["page_id"])
    for row in inventory["interfaces"]:
        channel="socket" if row["id"].startswith("WS") else "api"
        for actor in ACTORS:add(row,channel,actor,False if actor=="anonymous" else actor in row["allowed_roles"],write=row["id"]=="API-02")
        for actor in row["allowed_roles"]:
            for state in ["logged_out","expired"]:add(row,"session",actor,False,write=row["id"]=="API-02",session_state=state,original_channel=channel)
    for row in inventory["background"]+inventory["service_boundaries"]:
        human_row=dict(row)
        if row.get("human_case_source"):human_row["source"]=row["human_case_source"]
        for actor in ACTORS:add(human_row,"internal",actor,False if actor=="anonymous" else actor in row["allowed_roles"],write=row["id"] not in {"SERVICE-02","SERVICE-03"},requires_trusted_worker_driver=True)
    for n,row in enumerate(inventory["auxiliary_files"],1):
        copy=dict(row,id="PRIVATE-"+str(n).zfill(2))
        for actor in ACTORS:add(copy,"private",actor,False)
    # Origin handling requires an authenticated socket too; anonymous-only rejection is insufficient.
    socket=next(row for row in inventory["interfaces"] if row["id"]=="WS-01")
    for actor in socket["allowed_roles"]:
        add(dict(socket,id="WS-ORIGIN"),"socket",actor,False,origin="https://untrusted.example",requires_authenticated_identity=True)
    # Machine identities have distinct scopes, never inherited human/admin authority.
    for row in inventory["background"]:
        actor="deployment-migration" if row["id"]=="BG-06" else "worker-"+row["id"]
        machine_row=dict(row,id=row["id"]+"-MACHINE")
        if row.get("machine_case_source"):machine_row["source"]=row["machine_case_source"]
        add(machine_row,"internal",actor,True,write=True,required_machine_scope=row.get("machine_identity",row["identity"]),requires_isolated_worker_fixture=True)
    route=next(row for row in inventory["interfaces"] if row["id"]=="API-03")
    add(dict(route,id="API-03-SCOPED"),"api","routing-service",True,required_machine_scope=route["internal_caller"])
    return cases

if __name__=="__main__":
    source=json.loads((ROOT/"specifications/access-policy-inventory.json").read_text())
    cases=build(source)
    if len({c["id"] for c in cases})!=len(cases):raise RuntimeError("Duplicate case identifiers")
    (ROOT/"tests/security/desired-cases.json").write_text(json.dumps({"source":"specifications/access-policy-inventory.json","status":"Defined assertions; not executed candidate coverage","cases":cases},indent=2)+"\n")
    print("Defined",len(cases),"desired cases")
