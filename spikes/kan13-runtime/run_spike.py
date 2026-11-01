#!/usr/bin/env python3
"""Build/run/remove an isolated KAN-13 capability runtime. Never targets the legacy demo."""
import argparse
import base64
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
SPIKE=Path(__file__).resolve().parent
WORK=ROOT/".work/kan13"
EVIDENCE=ROOT/"notes/evidence/kan-13-runtime"
IMAGE="ai-modernization-kan13:runtime"
NAME="ai-modernization-kan13"

def require(ok,message):
    if not ok:raise RuntimeError(message)

def command(args,**kwargs):
    return subprocess.check_output(list(map(str,args)),stderr=subprocess.STDOUT,**kwargs)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--port",type=int,default=8085)
    args=parser.parse_args();require(1024<=args.port<=65535,"Choose an unprivileged local port")
    WORK.mkdir(parents=True,exist_ok=True);EVIDENCE.mkdir(parents=True,exist_ok=True)
    # Refuse existing containers, rather than deleting/reusing anyone's runtime.
    exists=subprocess.run(["docker","inspect",NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    require(exists.returncode!=0,"A KAN-13 container already exists; inspect it before retrying")
    credentials={name:secrets.token_urlsafe(28) for name in ["reader","operator","admin"]}
    private=WORK/"secrets";private.mkdir(mode=0o700,exist_ok=True);private.chmod(0o700)
    properties=private/"application-users.properties";roles=private/"application-roles.properties"
    require(not properties.exists() and not roles.exists(),"Private realm files already exist; inspect before replacing")
    base=f"http://127.0.0.1:{args.port}/kan13-runtime/"
    report={"verified_at":datetime.now(timezone.utc).isoformat(),"base_url":base,"scope":"Isolated minimal capability WAR, not migrated Cargo Tracker or full access policy","checks":[],"http_observations":[],"outcome":"FAIL"}
    container=None
    def check(name,ok,detail=None):
        report["checks"].append({"name":name,"passed":bool(ok),"detail":detail})
        require(ok,"Check failed: "+name)
    def request(path,who=None,method="GET",bad_password=False):
        headers={"Accept":"application/json"}
        if who:
            password="wrong-credential" if bad_password else credentials[who]
            headers["Authorization"]="Basic "+base64.b64encode((who+":"+password).encode()).decode()
        req=urllib.request.Request(base+path,method=method,headers=headers)
        try:response=urllib.request.urlopen(req,timeout=10)
        except urllib.error.HTTPError as error:response=error
        with response:
            data=response.read()
            report["http_observations"].append({"path":path,"method":method,"identity":who or "anonymous","bad_password":bad_password,"status":response.status})
            return response.status,data
    def status(who="reader"):
        code,data=request("api/status",who);require(code==200,"Status unavailable to permitted role")
        return json.loads(data)
    def complete_probe(who):
        code,data=request("api/probe",who,"POST");check(who+" allowed submit",code==202,{"http_status":code})
        created=json.loads(data);deadline=time.monotonic()+30;state=None;batch=None
        while time.monotonic()<deadline:
            code,data=request("api/probe/"+created["id"],"reader")
            require(code==200,"Reader cannot retrieve persisted record")
            state=json.loads(data)
            code,data=request("api/batch/"+str(created["batchExecution"]),"reader")
            require(code==200,"Batch status unavailable")
            batch=json.loads(data)["status"]
            if state["jpa"] and state["messageSeen"] and state["batchSeen"] and batch=="COMPLETED":break
            time.sleep(.25)
        check(who+" JPA/JMS/batch complete",state is not None and state["jpa"] and state["messageSeen"] and state["batchSeen"] and batch=="COMPLETED",{"record":state,"batch_status":batch})
    try:
        # This is WildFly ApplicationRealm's native digest format, not an app password store.
        properties.write_text("#$REALM_NAME=ApplicationRealm$\n"+"".join(
            name+"="+hashlib.md5((name+":ApplicationRealm:"+password).encode()).hexdigest()+"\n" for name,password in credentials.items()))
        roles.write_text("reader=Reader\noperator=Operator\nadmin=Administrator\n")
        properties.chmod(0o600);roles.chmod(0o600)
        with (WORK/"image-build.log").open("w") as log:
            build=subprocess.run(["docker","build","--progress=plain","-t",IMAGE,str(SPIKE)],stdout=log,stderr=subprocess.STDOUT)
        require(build.returncode==0,"Image build failed; see .work/kan13/image-build.log")
        report["image_id"]=command(["docker","image","inspect","--format","{{.Id}}",IMAGE],text=True).strip()
        report["runtime_java"]=command(["docker","run","--rm",IMAGE,"java","-version"],text=True).strip()
        report["runtime_uid"]=command(["docker","run","--rm",IMAGE,"id","-u"],text=True).strip()
        check("Non-root runtime",report["runtime_uid"]!="0")
        require('25.0.5' in report["runtime_java"],"Unexpected runtime Java maintenance version")
        container=command(["docker","run","-d","--name",NAME,"--label","ai-modernization.task=KAN-13","--init",
            "-p",f"127.0.0.1:{args.port}:8080","--mount",f"type=bind,src={private},dst=/run/kan13,readonly",IMAGE],text=True).strip()
        require(re.fullmatch(r"[0-9a-f]{64}",container) is not None,"Unexpected container identity")
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            try:
                code,data=request("api/status")
                if code==401:break
            except (OSError,urllib.error.URLError):pass
            time.sleep(1)
        else:raise RuntimeError("Isolated deployment not ready; see .work/kan13/server.log")
        check("Anonymous API denied",request("api/status")[0]==401)
        check("Wrong password denied",request("api/status","reader",bad_password=True)[0]==401)
        for who in credentials:
            observed=status(who);check(who+" permitted read on Java 25",observed["javaFeature"]==25 and observed["javaVersion"].startswith("25.0.5"),observed)
        check("Anonymous Faces denied",request("faces.xhtml")[0]==401)
        code,html=request("faces.xhtml","reader")
        check("Faces/CDI expression rendered",code==200 and b"KAN13_FACES_OK" in html and b"#{facesProbe.message}" not in html,{"http_status":code})
        before=status()["records"]
        check("Reader mutation denied",request("api/probe","reader","POST")[0]==403)
        check("Anonymous mutation denied",request("api/probe",method="POST")[0]==401)
        check("Denied requests did not create records",status()["records"]==before)
        complete_probe("operator");complete_probe("admin")
        check("Exactly two authorized records",status()["records"]==before+2)
        check("Missing record returns 404",request("api/probe/not-present","reader")[0]==404)
        check("Unsupported method rejected",request("api/status","reader","DELETE")[0]==405)
        war=WORK/"kan13-runtime.war"
        command(["docker","cp",container+":/opt/jboss/wildfly/standalone/deployments/kan13-runtime.war",war])
        report["war_sha256"]=hashlib.sha256(war.read_bytes()).hexdigest()
        with zipfile.ZipFile(war) as archive:
            major=int.from_bytes(archive.read("WEB-INF/classes/lab/spike/ProbeResource.class")[6:8],"big")
        check("Compiled Java 25 bytecode",major==69,{"class_major":major})
        report["build_inputs_sha256"]={p.relative_to(SPIKE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SPIKE.rglob("*")) if p.is_file() and (p.relative_to(SPIKE).parts[0]=="src" or p.name in {"Dockerfile","pom.xml","start.sh"})}
        report["outcome"]="PASS"
    except Exception as error:
        report["failure"]=str(error)
    finally:
        cleanup_errors=[]
        if container and re.fullmatch(r"[0-9a-f]{64}",container):
            try:(WORK/"server.log").write_bytes(command(["docker","logs",container]))
            except Exception:cleanup_errors.append("Could not collect runtime log")
            try:command(["docker","rm","-f",container])
            except Exception:cleanup_errors.append("Task container cleanup failed; inspect the KAN-13 container")
        for p in [properties,roles]:
            try:
                if p.exists():p.unlink()
            except Exception:cleanup_errors.append("Private realm-file cleanup failed; inspect ignored .work/kan13/secrets")
        report["cleanup"]={"status":"PASS" if not cleanup_errors else "FAIL","errors":cleanup_errors,"scope":"Only task-owned container and temporary realm files; historical services untouched"}
        if cleanup_errors:
            report["outcome"]="FAIL"
            report["failure"]="; ".join(cleanup_errors)
        failed_checks=[entry for entry in report["checks"] if not entry["passed"]]
        extra_failure=report["outcome"]!="PASS" and (not failed_checks or bool(cleanup_errors))
        failure_count=len(failed_checks)+int(extra_failure)
        (EVIDENCE/"results.json").write_text(json.dumps(report,indent=2)+"\n")
        suite=ET.Element("testsuite",name="KAN13RuntimeCapabilities",tests=str(len(report["checks"])+int(extra_failure)),failures=str(failure_count),errors="0",skipped="0")
        for entry in report["checks"]:
            case=ET.SubElement(suite,"testcase",name=entry["name"])
            if not entry["passed"]:ET.SubElement(case,"failure").text=report.get("failure","Capability assertion failed")
        if extra_failure:
            case=ET.SubElement(suite,"testcase",name="spike completion")
            ET.SubElement(case,"failure").text=report.get("failure","Runtime spike failed")
        ET.ElementTree(suite).write(EVIDENCE/"TEST-kan13-runtime.xml",encoding="utf-8",xml_declaration=True)
    print(json.dumps({"outcome":report["outcome"],"checks":len(report["checks"]),"failure":report.get("failure"),"evidence":str(EVIDENCE)}))
    return 0 if report["outcome"]=="PASS" else 1

if __name__=="__main__":raise SystemExit(main())
