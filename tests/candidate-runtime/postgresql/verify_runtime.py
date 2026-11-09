#!/usr/bin/env python3
"""Disposable WildFly/PostgreSQL integration for the safe production descriptor."""
from __future__ import annotations
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / ".work/kan18-postgresql-runtime"
SECRET_DIR = WORK / "secrets"
PROJECT = "kan18pg-" + secrets.token_hex(5)
IMAGE = "ai-modernization-candidate-postgresql:" + PROJECT
COMPOSE_FILE = ROOT / "infrastructure/database/compose.yaml"
BASE = "http://127.0.0.1:8082/cargo-tracker/"
TABLES = ("location", "voyage", "cargo", "leg", "handling_event", "carrier_movement", "legacy_sequence_state")
USERS = {"reader":"Reader", "operator":"Operator", "admin":"Administrator"}

def run(label, args, env, timeout=90, check=True):
    try:
        result = subprocess.run(args, cwd=ROOT, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(label + " timed out") from error
    if check and result.returncode != 0:
        tail = "\n".join(result.stdout.splitlines()[-80:])
        secret_dir = env.get("KAN22_SECRET_DIR")
        if secret_dir:
            for path in Path(secret_dir).glob("*"):
                if path.is_file():
                    try:
                        secret = path.read_text().strip()
                        if secret:
                            tail = tail.replace(secret, "[REDACTED]")
                    except OSError:
                        pass
        raise RuntimeError(label + " failed (exit " + str(result.returncode) + ")\n" + tail)
    return result

def password_hash(username, password):
    import hashlib
    return hashlib.md5((username + ":ApplicationRealm:" + password).encode()).hexdigest()

def create_secrets():
    if WORK.exists():
        raise RuntimeError("Task work path already exists; inspect before reuse")
    SECRET_DIR.mkdir(parents=True, mode=0o700)
    values = {name: secrets.token_urlsafe(32) for name in ("bootstrap_password","app_password","migrator_password")}
    for name,value in values.items():
        path=SECRET_DIR/name
        path.write_text(value+"\n")
        path.chmod(0o444)
    passwords={name:secrets.token_urlsafe(32) for name in USERS}
    users="#$REALM_NAME=ApplicationRealm$\n"+"".join(name+"="+password_hash(name,pw)+"\n" for name,pw in passwords.items())
    roles="reader=Reader\noperator=Operator\nadmin=Administrator\n"
    for name,content in (("application-users.properties",users),("application-roles.properties",roles)):
        path=SECRET_DIR/name;path.write_text(content);path.chmod(0o444)
    return passwords

def query(env, sql, username="db_bootstrap", password_file=None, allow_failure=False):
    if password_file:
        shell='export PGPASSWORD="$(cat "$1")"; exec psql -h 127.0.0.1 -U "$2" -d cargotracker -v ON_ERROR_STOP=1 -At -c "$3"'
        args=["docker","compose","-p",PROJECT,"-f",str(COMPOSE_FILE),"exec","-T","postgres","sh","-ec",shell,"sh","/run/secrets/"+password_file,username,sql]
    else:
        args=["docker","compose","-p",PROJECT,"-f",str(COMPOSE_FILE),"exec","-T","postgres","psql","-U",username,"-d","cargotracker","-v","ON_ERROR_STOP=1","-At","-c",sql]
    return run("PostgreSQL query",args,env,timeout=30,check=not allow_failure)

def database_state(env):
    parts=[]
    for table in TABLES:
        parts.append("'"+table+"',(SELECT json_build_object('count',count(*),'digest',md5(COALESCE(string_agg(to_jsonb(t)::text,chr(10) ORDER BY to_jsonb(t)::text),''))) FROM cargo."+table+" AS t)")
    sql="SELECT json_build_object("+",".join(parts)+")::text"
    raw=query(env,sql).stdout.strip().splitlines()
    return json.loads(raw[-1])

def http_status(url, opener=None, data=None):
    request=urllib.request.Request(url,data=data,headers={"Content-Type":"application/x-www-form-urlencoded"} if data else {})
    try:
        response=(opener or urllib.request.build_opener(NoRedirect())).open(request,timeout=8)
    except urllib.error.HTTPError as error:
        response=error
    with response:
        return response.status,response.read().decode(errors="replace"),response.headers

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def main():
    if WORK.exists(): raise RuntimeError("Task work path already exists; inspect before reuse")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",8082))
    env=os.environ.copy()
    env["KAN22_SECRET_DIR"]=str(SECRET_DIR)
    env["KAN22_MIGRATIONS_DIR"]=str(ROOT/"infrastructure/database/migrations")
    env["KAN18_APP_IMAGE"]=IMAGE
    compose=["docker","compose","-p",PROJECT,"-f",str(COMPOSE_FILE)]
    project_filter="label=com.docker.compose.project="+PROJECT
    existing_containers=run("Compose container ownership check",["docker","ps","-aq","--filter",project_filter],env,timeout=30).stdout.strip()
    existing_networks=run("Compose network ownership check",["docker","network","ls","-q","--filter",project_filter],env,timeout=30).stdout.strip()
    existing_volumes=run("Compose volume ownership check",["docker","volume","ls","-q","--filter",project_filter],env,timeout=30).stdout.strip()
    existing_image=run("Candidate image ownership check",["docker","image","inspect",IMAGE],env,timeout=30,check=False)
    if existing_containers or existing_networks or existing_volumes or existing_image.returncode==0:
        raise RuntimeError("A resource for the unique task project/image already exists")
    try:
        passwords=create_secrets()
    except Exception:
        if WORK.exists(): shutil.rmtree(WORK)
        raise
    report={"task":"KAN-18/KAN-15 BG-06","status":"FAIL","checks":{},"cleanup":{"compose_down":False,"resource_check_passed":False,"residual_containers":[],"residual_networks":[],"residual_volumes":[],"work_removed":False,"image_removed":False,"secrets_preserved":False}}
    try:
        run("Candidate image build",compose+["--profile","candidate-app","build","candidate-app"],env,timeout=900)
        run("Fresh PostgreSQL startup",compose+["up","-d","--wait","--wait-timeout","120","postgres"],env,timeout=150)
        secret_read=run("PostgreSQL migrator secret readability",compose+["exec","-T","--user","postgres","postgres","sh","-ec","test -r /run/secrets/migrator_password && echo readable"],env,timeout=30,check=False)
        role_state=query(env,"SELECT rolname||':'||rolcanlogin||':'||COALESCE(left(rolpassword,4),'null') FROM pg_authid WHERE rolname='schema_migrator'").stdout.strip().splitlines()
        pg_logs=run("PostgreSQL initialization log",compose+["logs","--no-color","postgres"],env,timeout=30,check=False).stdout
        init_lines=[line for line in pg_logs.splitlines() if any(word in line.lower() for word in ("10-create-roles","permission denied","create role","error:"))][-20:]
        report["checks"]["migration_secret_bootstrap_diagnostics"]={"secret_readable":secret_read.returncode==0 and secret_read.stdout.strip().endswith("readable"),"role_state":role_state,"initialization_messages":init_lines}
        migrator_auth=query(env,"SELECT current_user",username="schema_migrator",password_file="migrator_password",allow_failure=True)
        report["checks"]["migration_identity_authentication"]={"passed":migrator_auth.returncode==0,"authenticated_as":migrator_auth.stdout.strip().splitlines()[-1] if migrator_auth.returncode==0 else None,"failure_code":"28P01" if "28P01" in migrator_auth.stdout else None}
        if migrator_auth.returncode: raise RuntimeError("schema_migrator secret did not authenticate through PostgreSQL")
        run("Fresh Flyway migrations",compose+["--profile","migrate","run","--rm","migrate"],env,timeout=180)
        history=query(env,"SELECT version||':'||success FROM cargo.flyway_schema_history ORDER BY installed_rank").stdout.strip().splitlines()
        report["checks"]["fresh_migrations"]={"passed":history==["1:true","2:true","3:true"],"versions":history}
        if not report["checks"]["fresh_migrations"]["passed"]: raise RuntimeError("Expected fresh V1/V2/V3 migration history")
        db_roles=query(env,"SELECT rolname||':'||rolsuper||':'||rolcreatedb||':'||rolcreaterole FROM pg_roles WHERE rolname IN ('schema_migrator','cargo_app','reader','operator','admin') ORDER BY rolname").stdout.strip().splitlines()
        report["checks"]["role_separation"]={"passed":db_roles==["cargo_app:false:false:false","schema_migrator:false:false:false"],"database_roles":db_roles}
        acl=query(env,"SELECT has_schema_privilege('schema_migrator','cargo','CREATE')||':'||has_schema_privilege('cargo_app','cargo','CREATE')||':'||has_table_privilege('cargo_app','cargo.flyway_schema_history','UPDATE')||':'||has_table_privilege('cargo_app','cargo.legacy_sequence_state','UPDATE')").stdout.strip().splitlines()
        report["checks"]["least_privilege_acl"]={"passed":acl==["true:false:false:false"],"observed":acl}
        before=database_state(env)
        if any(value["count"] for value in before.values()): raise RuntimeError("Fresh schema unexpectedly contains rows")
        marker="KAN18_"+secrets.token_hex(8).upper()
        insert="INSERT INTO cargo.location(id,name,unlocode) VALUES (900001,'"+marker+"','ZZTST')"
        result=query(env,insert,username="cargo_app",password_file="app_password",allow_failure=True)
        report["checks"]["runtime_dml"]={"passed":result.returncode==0}
        if result.returncode: raise RuntimeError("cargo_app could not persist a marker")
        denial_attempts={
            "persistent_schema_ddl":query(env,"CREATE TABLE cargo.kan18_ddl_probe(id integer)",username="cargo_app",password_file="app_password",allow_failure=True),
            "temporary_table_ddl":query(env,"CREATE TEMP TABLE kan18_temp_probe(id integer)",username="cargo_app",password_file="app_password",allow_failure=True),
            "flyway_history_update":query(env,"UPDATE cargo.flyway_schema_history SET success=success WHERE FALSE",username="cargo_app",password_file="app_password",allow_failure=True),
            "migration_state_update":query(env,"UPDATE cargo.legacy_sequence_state SET seq_count=seq_count WHERE FALSE",username="cargo_app",password_file="app_password",allow_failure=True)}
        report["checks"]["application_ddl_denied"]={name:(result.returncode!=0 and "permission denied" in result.stdout.lower()) for name,result in denial_attempts.items()}
        if not all(report["checks"]["application_ddl_denied"].values()): raise RuntimeError("cargo_app unexpectedly received schema/migration privileges")
        marked=database_state(env)
        run("Candidate app startup",compose+["--profile","candidate-app","up","-d","candidate-app"],env,timeout=120)
        deadline=time.monotonic()+180
        anonymous_status=0
        while time.monotonic()<deadline:
            try:
                anonymous_status,body,headers=http_status(BASE+"rest/cargo")
                if anonymous_status in (302,401): break
                if anonymous_status not in (404,500,502,503): break
            except Exception: pass
            time.sleep(2)
        report["checks"]["anonymous_api_denied"]={"passed":anonymous_status in (302,401),"status":anonymous_status}
        if not report["checks"]["anonymous_api_denied"]["passed"]: raise RuntimeError("Candidate app did not reach expected anonymous denial")
        after_start=database_state(env)
        marker_ok=query(env,"SELECT count(*) FROM cargo.location WHERE id=900001 AND name='"+marker+"'").stdout.strip().splitlines()==["1"]
        report["checks"]["startup_no_orm_ddl_or_seed"]={"passed":after_start==marked and marker_ok,"before":marked,"after":after_start,"marker_preserved":marker_ok}
        if not report["checks"]["startup_no_orm_ddl_or_seed"]["passed"]: raise RuntimeError("Application startup changed persisted data")
        report["checks"]["human_roles"]={}
        for username,role in USERS.items():
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),NoRedirect())
            code,login_body,_=http_status(BASE+"login",opener)
            token=re.search(r"name='csrf' value='([^']+)'",login_body)
            valid=code==200 and token is not None
            if valid:
                payload=urllib.parse.urlencode({"username":username,"password":passwords[username],"csrf":token.group(1)}).encode()
                login_status,_,_=http_status(BASE+"login",opener,payload)
                session_status,session_body,_=http_status(BASE+"session",opener)
                cargo_status,_,_=http_status(BASE+"rest/cargo",opener)
                try: identity=json.loads(session_body)
                except Exception: identity={}
                valid=(login_status==303 and session_status==200 and identity.get("principal")==username and role in identity.get("roles",[]) and cargo_status==200)
            state=database_state(env)
            report["checks"]["human_roles"][role]={"passed":valid and state==marked,"identity_verified":valid,"db_unchanged":state==marked}
            if not report["checks"]["human_roles"][role]["passed"]: raise RuntimeError("Human app identity check failed for "+role)
        run("Candidate app restart",compose+["restart","candidate-app"],env,timeout=90)
        time.sleep(12)
        restarted=database_state(env)
        report["checks"]["restart_preserves_data"]={"passed":restarted==marked and query(env,"SELECT count(*) FROM cargo.location WHERE id=900001 AND name='"+marker+"'").stdout.strip().splitlines()==["1"],"after_restart":restarted}
        if not report["checks"]["restart_preserves_data"]["passed"]: raise RuntimeError("Candidate restart changed persisted data")
        report["schema_hashes"]={}
        for relative in (".dockerignore","tests/candidate-runtime/postgresql/Dockerfile","tests/candidate-runtime/postgresql/module.xml","tests/candidate-runtime/postgresql/configure-datasource.cli","tests/candidate-runtime/postgresql/start.sh","tests/candidate-runtime/postgresql/verify_runtime.py","infrastructure/database/compose.yaml","infrastructure/database/bootstrap/10-create-roles.sh","infrastructure/database/migrations/V1__initial_schema.sql","infrastructure/database/migrations/V2__query_indexes_and_sequence_reconciliation.sql","infrastructure/database/migrations/V3__grant_application_runtime_privileges.sql","candidate/cargotracker/src/main/resources/META-INF/persistence.xml","candidate/cargotracker/src/main/java/net/java/cargotracker/application/util/SampleDataGenerator.java"):
            report["schema_hashes"][relative]=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
        report["versions"]={"postgres":"18.6","flyway":"13.12.1","wildfly":"42","jdbc":"42.7.14"}
        report["status"]="PASS" if all(x.get("passed") for x in report["checks"].values() if isinstance(x,dict) and "passed" in x) else "FAIL"
    except Exception as error:
        report["status"] = "FAIL"
        report["failure"] = str(error)
    finally:
        down_ok=False
        try:
            down=run("Owned Compose cleanup",compose+["--profile","candidate-app","--profile","migrate","down","--volumes","--remove-orphans"],env,timeout=120,check=False)
            down_ok=down.returncode==0
        except Exception:
            down_ok=False
        report["cleanup"]["compose_down"]=down_ok
        try:
            report["cleanup"]["residual_containers"]=run("Remaining owned container check",["docker","ps","-aq","--filter","label=com.docker.compose.project="+PROJECT],env,timeout=30).stdout.strip().splitlines()
            report["cleanup"]["residual_networks"]=run("Remaining owned network check",["docker","network","ls","-q","--filter","label=com.docker.compose.project="+PROJECT],env,timeout=30).stdout.strip().splitlines()
            report["cleanup"]["residual_volumes"]=run("Remaining owned volume check",["docker","volume","ls","-q","--filter","label=com.docker.compose.project="+PROJECT],env,timeout=30).stdout.strip().splitlines()
            report["cleanup"]["resource_check_passed"]=True
        except Exception:
            report["cleanup"]["resource_check_passed"]=False
        stack_clean=(down_ok and report["cleanup"]["resource_check_passed"]
            and not report["cleanup"]["residual_containers"]
            and not report["cleanup"]["residual_networks"]
            and not report["cleanup"]["residual_volumes"])
        if stack_clean:
            try:
                if WORK.exists(): shutil.rmtree(WORK)
                report["cleanup"]["work_removed"]=not WORK.exists()
            except Exception as error:
                report["cleanup"]["work_remove_error"]=str(error)
            report["cleanup"]["secrets_preserved"]=SECRET_DIR.exists()
            if WORK.exists():
                report["cleanup"]["retained_work_path"]=str(WORK)
            try:
                image_result=run("Owned candidate image cleanup",["docker","image","rm",IMAGE],env,timeout=45,check=False)
                report["cleanup"]["image_removed"]=(image_result.returncode==0 or "No such image" in image_result.stdout)
            except Exception as error:
                report["cleanup"]["image_removed"]=False
                report["cleanup"]["image_remove_error"]=str(error)
        else:
            report["cleanup"]["work_removed"]=False
            report["cleanup"]["secrets_preserved"]=SECRET_DIR.exists()
            report["cleanup"]["retained_work_path"]=str(WORK)
        cleanup_ok=(report["cleanup"]["compose_down"] and report["cleanup"]["resource_check_passed"]
            and not report["cleanup"]["residual_containers"] and not report["cleanup"]["residual_networks"]
            and not report["cleanup"]["residual_volumes"] and report["cleanup"]["work_removed"]
            and report["cleanup"]["image_removed"])
        if not cleanup_ok:
            report["status"]="FAIL"
            report["cleanup"]["failure"]="One or more owned-resource cleanup requirements were not met"
    output=ROOT/".work/kan18-postgresql-last-result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"checks":{k:v for k,v in report["checks"].items() if k!="human_roles"},"cleanup":report["cleanup"]}))
    cleanup_ok=(report["cleanup"]["compose_down"] and report["cleanup"]["resource_check_passed"]
        and not report["cleanup"]["residual_containers"] and not report["cleanup"]["residual_networks"]
        and not report["cleanup"]["residual_volumes"] and report["cleanup"]["work_removed"]
        and report["cleanup"]["image_removed"])
    return 0 if report["status"]=="PASS" and cleanup_ok else 1

if __name__=="__main__": raise SystemExit(main())
