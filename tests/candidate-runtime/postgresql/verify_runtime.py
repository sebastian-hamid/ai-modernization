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
MIGRATION_DIR = WORK / "migrations"
IMAGE = "ai-modernization-candidate-postgresql:" + PROJECT
PROBE_IMAGE = "postgres:18.6@sha256:e3d24f6906d0760bf4da0dae872415391ededefad23fd471c47dc53b0ddf3c42"
PROBE_CONTAINER = PROJECT + "-network-probe"
NAMING_PROBE_CONTAINER = PROJECT + "-jndi-probe"
NAMING_PROBE_SOURCE = ROOT / "tests/candidate-runtime/postgresql/RemoteJndiReachabilityProbe.java"
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
                        content=path.read_text()
                        candidates=[content.strip()]
                        for line in content.splitlines():
                            if "=" in line:
                                candidates.append(line.split("=",1)[1].strip())
                        for secret in candidates:
                            if secret:
                                tail=tail.replace(secret,"[REDACTED]")
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
    probe_credentials=SECRET_DIR/"remote-jndi.properties"
    probe_credentials.write_text("".join(name+".password="+pw+"\n" for name,pw in passwords.items()))
    probe_credentials.chmod(0o444)
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

def candidate_access_network(env):
    ids=run("Candidate access network lookup",["docker","network","ls","-q",
        "--filter","label=com.docker.compose.project="+PROJECT],env,timeout=30).stdout.strip().splitlines()
    matches=[]
    for network_id in ids:
        details=json.loads(run("Candidate network labels",["docker","network","inspect",network_id],env,timeout=30).stdout)
        if details and (details[0].get("Labels") or {}).get("com.docker.compose.network")=="candidate-host-access":
            matches.append(network_id)
    if len(matches)!=1:
        raise RuntimeError("Expected exactly one candidate-host-access network for peer probe")
    return matches[0]

def peer_tcp_probe(env):
    network_id=candidate_access_network(env)
    ports=(8080,8009,8443,9990,9993,3528,3529,4712,4713,5445,5455,5672,61616)
    script='set -eu; for port in 8080 8009 8443 9990 9993 3528 3529 4712 4713 5445 5455 5672 61616; do if timeout 3 bash -c "exec 3<>/dev/tcp/candidate-app/$port" >/dev/null 2>&1; then printf "%s=open\n" "$port"; else printf "%s=closed\n" "$port"; fi; done'
    result=run("Candidate peer TCP reachability probe",["docker","run","--rm","--name",PROBE_CONTAINER,
        "--label","com.docker.compose.project="+PROJECT,"--network",network_id,"--entrypoint","bash",
        PROBE_IMAGE,"-lc",script],env,timeout=60)
    observed={}
    for line in result.stdout.splitlines():
        if "=" in line:
            port,state=line.strip().split("=",1)
            if port.isdigit() and state in ("open","closed"):
                observed[port]=state=="open"
    if set(observed)!={str(port) for port in ports}:
        raise RuntimeError("Peer TCP probe did not report every expected port")
    return {"driver":"tcp-connect-from-disposable-peer-v1","peer_image":PROBE_IMAGE,
        "target":"candidate-app on candidate-host-access network",
        "reachable":observed,
        "interpretation":{"8080":"HTTP application listener; WildFly HTTP remoting, remote JNDI and JMS HTTP connector share this listener",
            "8009":"AJP","8443":"HTTPS","9990":"WildFly management HTTP","9993":"WildFly management HTTPS",
            "3528":"IIOP","3529":"IIOP TLS","4712":"transaction recovery","4713":"transaction status",
            "5445":"native messaging","5455":"messaging throughput","5672":"AMQP","61616":"Artemis TCP"}}

def remote_jndi_jms_probe(env):
    network_id=candidate_access_network(env)
    credential_path=SECRET_DIR/"remote-jndi.properties"
    command='set -eu; mkdir -p /tmp/kan18-jndi-probe; javac -cp /opt/jboss/wildfly/bin/client/jboss-client.jar -d /tmp/kan18-jndi-probe /tmp/RemoteJndiReachabilityProbe.java; exec java -cp /tmp/kan18-jndi-probe:/opt/jboss/wildfly/bin/client/jboss-client.jar lab.fixture.RemoteJndiReachabilityProbe remote+http://candidate-app:8080 /run/remote-jndi.properties'
    result=run("Remote JNDI/JMS read-only protocol probe",["docker","run","--rm","--name",NAMING_PROBE_CONTAINER,
        "--label","com.docker.compose.project="+PROJECT,"--network",network_id,
        "--mount","type=bind,src="+str(NAMING_PROBE_SOURCE.resolve())+",dst=/tmp/RemoteJndiReachabilityProbe.java,readonly",
        "--mount","type=bind,src="+str(credential_path.resolve())+",dst=/run/remote-jndi.properties,readonly",
        "--entrypoint","bash",IMAGE,"-lc",command],env,timeout=90)
    observations={}
    seen=set()
    well_formed=True
    expected_fields={"lookup","connection_started","authentication_denial","jms_closed","naming_closed","failure"}
    for line in result.stdout.splitlines():
        if not line.startswith("PROBE_RESULT "):
            continue
        fields=line.split()
        if len(fields)!=8 or fields[1] in seen:
            well_formed=False
            continue
        seen.add(fields[1])
        pairs=[field.split("=",1) for field in fields[2:] if "=" in field]
        values=dict(pairs)
        bool_fields=("lookup","connection_started","authentication_denial","jms_closed","naming_closed")
        if (len(pairs)!=6 or set(values)!=expected_fields
                or any(values.get(key) not in ("true","false") for key in bool_fields)
                or not values.get("failure")):
            well_formed=False
            continue
        observations[fields[1]]={"factory_lookup_succeeded":values["lookup"]=="true",
            "jms_connection_started":values["connection_started"]=="true",
            "authentication_denial":values["authentication_denial"]=="true",
            "jms_closed":values["jms_closed"]=="true","naming_closed":values["naming_closed"]=="true",
            "failure_class":None if values["failure"]=="none" else values["failure"]}
    expected={"reader","operator","admin","anonymous","invalid"}
    valid_roles_allowed=all(observations.get(user,{}).get("factory_lookup_succeeded") is True
        and observations.get(user,{}).get("jms_connection_started") is True
        for user in ("reader","operator","admin"))
    anonymous_denied=(not observations.get("anonymous",{}).get("jms_connection_started",False)
        and observations.get("anonymous",{}).get("authentication_denial",False))
    invalid_denied=(not observations.get("invalid",{}).get("jms_connection_started",False)
        and observations.get("invalid",{}).get("authentication_denial",False))
    resources_closed=(set(observations)==expected and all(row["jms_closed"] and row["naming_closed"] for row in observations.values()))
    return {"driver":"remote-http-remoting-jndi-jms-connect-v1","provider":"remote+http://candidate-app:8080",
        "operations":["lookup jms/RemoteConnectionFactory","create JMS context","start connection","close context"],
        "sends_performed":0,"consumers_created":0,"observations":observations,
        "valid_app_roles_connect":valid_roles_allowed,"anonymous_connection_denied":anonymous_denied,
        "invalid_credential_connection_denied":invalid_denied,"client_resources_closed":resources_closed,
        "all_probes_reported":set(observations)==expected,"well_formed_unique_results":well_formed,
        "database_state_unchanged":None,
        "passed":set(observations)==expected and well_formed and valid_roles_allowed and anonymous_denied and invalid_denied and resources_closed}

def cleanup_owned_probe_container(env,name):
    ids=run("Owned probe cleanup lookup",["docker","ps","-aq","--filter","name=^/"+name+"$"],env,timeout=30).stdout.strip().splitlines()
    for container_id in ids:
        details=json.loads(run("Owned probe ownership verification",["docker","container","inspect",container_id],env,timeout=30).stdout)
        labels=(details[0].get("Config") or {}).get("Labels") or {}
        if labels.get("com.docker.compose.project")!=PROJECT:
            return False,"Probe name resolved to a resource outside this unique project"
        run("Owned probe container cleanup",["docker","rm","-f",container_id],env,timeout=30,check=False)
    remaining=run("Owned probe residual check",["docker","ps","-aq","--filter","name=^/"+name+"$"],env,timeout=30).stdout.strip()
    return not remaining,None if not remaining else "Owned probe container remains"

def database_state(env):
    parts=[]
    for table in TABLES:
        parts.append("'"+table+"',(SELECT json_build_object('count',count(*),'digest',md5(COALESCE(string_agg(to_jsonb(t)::text,chr(10) ORDER BY to_jsonb(t)::text),''))) FROM cargo."+table+" AS t)")
    sql="SELECT json_build_object("+",".join(parts)+")::text"
    raw=query(env,sql).stdout.strip().splitlines()
    return json.loads(raw[-1])

def json_query(env, sql):
    raw=query(env,sql).stdout.strip().splitlines()
    if not raw:
        raise RuntimeError("PostgreSQL JSON query returned no rows")
    return json.loads(raw[-1])

def prepare_migrations():
    if MIGRATION_DIR.exists():
        raise RuntimeError("Task migration path already exists")
    MIGRATION_DIR.mkdir(parents=True)
    source=ROOT/"infrastructure/database/migrations"
    for path in source.glob("V*.sql"):
        shutil.copyfile(path,MIGRATION_DIR/path.name)
    callback="""INSERT INTO lab_observer.flyway_session_observation
        (session_user_name,current_user_name,current_role_name,observed_at)
        VALUES (session_user,current_user,current_role,clock_timestamp());
"""
    callback_path=MIGRATION_DIR/"afterEachMigrate.sql"
    callback_path.write_text(callback)
    return hashlib.sha256(callback_path.read_bytes()).hexdigest()

def migration_history(env):
    return json_query(env,"SELECT COALESCE(json_agg(json_build_object('version',version,'description',description,'type',type,'script',script,'checksum',checksum,'installed_by',installed_by,'success',success) ORDER BY installed_rank),'[]'::json)::text FROM cargo.flyway_schema_history")

def migration_session_observations(env):
    return json_query(env,"SELECT COALESCE(json_agg(json_build_object('session_user',session_user_name,'current_user',current_user_name,'current_role',current_role_name,'observed_at',observed_at::text) ORDER BY observed_at),'[]'::json)::text FROM lab_observer.flyway_session_observation")

def schema_catalog_state(env):
    queries={
      "relations":"SELECT COALESCE(json_agg(json_build_object('name',c.relname,'kind',c.relkind) ORDER BY c.relname),'[]'::json)::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='cargo' AND c.relkind IN ('r','S','p','v','m')",
      "columns":"SELECT COALESCE(json_agg(json_build_object('table',table_name,'column',column_name,'type',data_type,'nullable',is_nullable,'default',column_default) ORDER BY table_name,ordinal_position),'[]'::json)::text FROM information_schema.columns WHERE table_schema='cargo'",
      "constraints":"SELECT COALESCE(json_agg(json_build_object('table',cl.relname,'name',c.conname,'type',c.contype,'definition',pg_get_constraintdef(c.oid,true),'deferrable',c.condeferrable,'deferred',c.condeferred,'validated',c.convalidated) ORDER BY cl.relname,c.conname),'[]'::json)::text FROM pg_constraint c JOIN pg_class cl ON cl.oid=c.conrelid JOIN pg_namespace n ON n.oid=cl.relnamespace WHERE n.nspname='cargo'",
      "indexes":"SELECT COALESCE(json_agg(json_build_object('table',tbl.relname,'name',idx.relname,'definition',pg_get_indexdef(i.indexrelid),'valid',i.indisvalid,'ready',i.indisready,'unique',i.indisunique) ORDER BY idx.relname),'[]'::json)::text FROM pg_index i JOIN pg_class idx ON idx.oid=i.indexrelid JOIN pg_class tbl ON tbl.oid=i.indrelid JOIN pg_namespace n ON n.oid=tbl.relnamespace WHERE n.nspname='cargo'",
      "triggers":"SELECT COALESCE(json_agg(json_build_object('table',cl.relname,'name',t.tgname,'enabled',t.tgenabled,'definition',pg_get_triggerdef(t.oid,true)) ORDER BY cl.relname,t.tgname),'[]'::json)::text FROM pg_trigger t JOIN pg_class cl ON cl.oid=t.tgrelid JOIN pg_namespace n ON n.oid=cl.relnamespace WHERE n.nspname='cargo' AND NOT t.tgisinternal",
      "routines":"SELECT COALESCE(json_agg(json_build_object('name',p.proname,'arguments',pg_get_function_identity_arguments(p.oid),'definition',pg_get_functiondef(p.oid)) ORDER BY p.proname),'[]'::json)::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='cargo'",
      "owners":"SELECT COALESCE(json_agg(json_build_object('name',c.relname,'kind',c.relkind,'owner',pg_get_userbyid(c.relowner),'acl',c.relacl::text) ORDER BY c.relname),'[]'::json)::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='cargo' AND c.relkind IN ('r','S','i','p','v','m')",
      "schema":"SELECT json_build_object('owner',pg_get_userbyid(n.nspowner),'acl',n.nspacl::text,'app_usage',has_schema_privilege('cargo_app','cargo','USAGE'),'app_create',has_schema_privilege('cargo_app','cargo','CREATE'),'migrator_usage',has_schema_privilege('schema_migrator','cargo','USAGE'),'migrator_create',has_schema_privilege('schema_migrator','cargo','CREATE'))::text FROM pg_namespace n WHERE n.nspname='cargo'",
      "table_grants":"SELECT COALESCE(json_agg(json_build_object('table',table_name,'privilege',privilege_type,'grantable',is_grantable,'grantor',grantor) ORDER BY table_name,privilege_type),'[]'::json)::text FROM information_schema.role_table_grants WHERE table_schema='cargo' AND grantee='cargo_app'",
      "protected_table_privileges":"SELECT json_build_object('history_select',has_table_privilege('cargo_app','cargo.flyway_schema_history','SELECT'),'history_insert',has_table_privilege('cargo_app','cargo.flyway_schema_history','INSERT'),'history_update',has_table_privilege('cargo_app','cargo.flyway_schema_history','UPDATE'),'history_delete',has_table_privilege('cargo_app','cargo.flyway_schema_history','DELETE'),'state_select',has_table_privilege('cargo_app','cargo.legacy_sequence_state','SELECT'),'state_insert',has_table_privilege('cargo_app','cargo.legacy_sequence_state','INSERT'),'state_update',has_table_privilege('cargo_app','cargo.legacy_sequence_state','UPDATE'),'state_delete',has_table_privilege('cargo_app','cargo.legacy_sequence_state','DELETE'))::text",
      "sequence_privileges":"SELECT json_build_object('app_usage',has_sequence_privilege('cargo_app','cargo.cargotracker_id_seq','USAGE'),'app_select',has_sequence_privilege('cargo_app','cargo.cargotracker_id_seq','SELECT'),'app_update',has_sequence_privilege('cargo_app','cargo.cargotracker_id_seq','UPDATE'),'migrator_usage',has_sequence_privilege('schema_migrator','cargo.cargotracker_id_seq','USAGE'),'migrator_select',has_sequence_privilege('schema_migrator','cargo.cargotracker_id_seq','SELECT'),'migrator_update',has_sequence_privilege('schema_migrator','cargo.cargotracker_id_seq','UPDATE'))::text",
      "sequence_state":"SELECT json_build_object('last_value',last_value,'is_called',is_called)::text FROM cargo.cargotracker_id_seq",
      "roles":"SELECT COALESCE(json_agg(json_build_object('name',rolname,'superuser',rolsuper,'createdb',rolcreatedb,'createrole',rolcreaterole,'replication',rolreplication,'login',rolcanlogin) ORDER BY rolname),'[]'::json)::text FROM pg_roles WHERE rolname IN ('schema_migrator','cargo_app','reader','operator','admin')",
      "history":"SELECT COALESCE(json_agg(json_build_object('version',version,'description',description,'type',type,'script',script,'checksum',checksum,'installed_by',installed_by,'success',success) ORDER BY installed_rank),'[]'::json)::text FROM cargo.flyway_schema_history",
    }
    return {key:json_query(env,sql) for key,sql in queries.items()}

def durable_state(env):
    return {"rows":database_state(env),"catalog":schema_catalog_state(env)}

def seed_populated_v1_schema(env):
    sql="""BEGIN;
INSERT INTO cargo.location(id,name,unlocode) VALUES
  (7001,'BG06 migration origin','ZZMIG'),
  (7007,'BG06 migration destination','ZZDST');
INSERT INTO cargo.voyage(id,voyage_number) VALUES
  (7002,'BG06MIG');
INSERT INTO cargo.cargo(id,tracking_id,origin_id,spec_origin_id,spec_destination_id,
                         spec_arrival_deadline,last_known_location_id,calculated_at,
                         routing_status,transport_status,misdirected,unloaded_at_dest)
  VALUES (7003,'BG06-MIGRATION-CARGO',7001,7001,7007,'2030-01-01',
          7001,'2026-01-01 00:00:00','NOT_ROUTED','NOT_RECEIVED',FALSE,FALSE);
INSERT INTO cargo.leg(id,load_location_id,unload_location_id,voyage_id,cargo_id,load_time,unload_time)
  VALUES (7004,7001,7001,7002,7003,'2016-01-01 00:00:00','2016-01-02 00:00:00');
INSERT INTO cargo.handling_event(id,completion_date,registration_date,type,cargo_id,location_id)
  VALUES (7005,'2016-01-01','2016-01-01','RECEIVE',7003,7001);
UPDATE cargo.cargo SET last_event_id=7005 WHERE id=7003;
INSERT INTO cargo.carrier_movement(id,arrival_time,departure_time,arrival_location_id,departure_location_id,voyage_id)
  VALUES (7006,'2016-01-02 00:00:00','2016-01-01 00:00:00',7001,7001,7002);
INSERT INTO cargo.legacy_sequence_state(seq_name,seq_count) VALUES ('BG06_SYNTHETIC',8000);
COMMIT;"""
    return query(env,sql)

def migration_identity_valid(history,observations,expected_versions):
    return ( [row.get("version") for row in history]==expected_versions
        and all(row.get("success") is True and row.get("installed_by")=="schema_migrator" for row in history)
        and len(observations)==len(expected_versions)
        and all(row.get("session_user")=="schema_migrator"
                and row.get("current_user")=="schema_migrator"
                and row.get("current_role")=="schema_migrator" for row in observations))

def v2_effects(before,after,data_before,data_after,history_before,history_after,observations):
    expected={"idx_cargo_origin_id":("cargo","origin_id"),
        "idx_cargo_spec_destination_id":("cargo","spec_destination_id"),
        "idx_leg_cargo_id":("leg","cargo_id"),
        "idx_handling_event_cargo_dates":("handling_event","cargo_id, completion_date, registration_date"),
        "idx_carrier_movement_voyage_id":("carrier_movement","voyage_id")}
    old={row["name"]:row for row in before["indexes"]}
    new={row["name"]:row for row in after["indexes"]}
    added=set(new)-set(old)
    expected_definitions={name:"CREATE INDEX "+name+" ON cargo."+table+" USING btree ("+columns+")"
        for name,(table,columns) in expected.items()}
    definitions_ok=(added==set(expected) and all(new[name]["valid"] and new[name]["ready"]
        and new[name]["definition"]==expected_definitions[name]
        and not new[name]["unique"]
        for name in expected)) and all(new.get(name)==row for name,row in old.items())
    owners_old={row["name"]:row for row in before["owners"]}
    owners_new={row["name"]:row for row in after["owners"]}
    owners_ok=(set(owners_new)-set(owners_old)==set(expected)
        and all(owners_new[name]==row for name,row in owners_old.items())
        and all(owners_new[name]["owner"]=="schema_migrator" for name in expected))
    stable=("relations","columns","constraints","triggers","routines","schema","table_grants",
        "protected_table_privileges","sequence_privileges","roles")
    stable_ok=all(before[key]==after[key] for key in stable)
    history_ok=(history_after[:len(history_before)]==history_before
        and [row["version"] for row in history_after]==["1","2"]
        and migration_identity_valid(history_after,observations,["1","2"]))
    high_water=max(7007,8000)
    sequence_ok=after["sequence_state"]=={"last_value":high_water,"is_called":True}
    data_ok=data_before==data_after
    return {"passed":definitions_ok and owners_ok and stable_ok and history_ok and sequence_ok and data_ok,
        "data_preserved":data_ok,"new_index_names":sorted(added),"expected_indexes":expected,
        "index_definitions_valid":definitions_ok,"owners_delta_valid":owners_ok,
        "catalog_other_than_indexes_history_sequence_unchanged":stable_ok,
        "sequence_before":before["sequence_state"],"sequence_after":after["sequence_state"],
        "expected_high_water":high_water,"history":history_after,"session_observations":observations,
        "high_water_branch":"legacy_sequence_state (entity-id maximum branch separately covered by KAN-22)"}

def v3_effects(before,after,data_before,data_after,history_before,history_after,observations):
    stable=("relations","columns","constraints","indexes","triggers","routines","schema","roles",
        "sequence_state","protected_table_privileges")
    stable_ok=all(before[key]==after[key] for key in stable)
    owners_before={row["name"]:row for row in before["owners"]}
    owners_after={row["name"]:row for row in after["owners"]}
    same_owners=(set(owners_before)==set(owners_after)
        and all(owners_before[name]["kind"]==owners_after[name]["kind"]
            and owners_before[name]["owner"]==owners_after[name]["owner"] for name in owners_before))
    acl_changed={name for name in owners_before if owners_before[name]["acl"]!=owners_after[name]["acl"]}
    expected_acl={"location","voyage","cargo","leg","handling_event","carrier_movement","cargotracker_id_seq"}
    acl_ok=same_owners and acl_changed==expected_acl
    expected={(table,priv) for table in ("location","voyage","cargo","leg","handling_event","carrier_movement")
        for priv in ("SELECT","INSERT","UPDATE","DELETE")}
    actual={(row["table"],row["privilege"]) for row in after["table_grants"]}
    grants_ok=(actual==expected and len(after["table_grants"])==len(expected)
        and all(row["grantable"]=="NO" and row["grantor"]=="schema_migrator" for row in after["table_grants"]))
    sequence=after["sequence_privileges"]
    seq_ok=sequence["app_usage"] and sequence["app_select"] and sequence["app_update"]
    protected_ok=not any(after["protected_table_privileges"].values())
    history_ok=(history_after[:len(history_before)]==history_before
        and [row["version"] for row in history_after]==["1","2","3"]
        and migration_identity_valid(history_after,observations,["1","2","3"]))
    data_ok=data_before==data_after
    return {"passed":stable_ok and acl_ok and grants_ok and seq_ok and protected_ok and history_ok and data_ok,
        "history":history_after,"session_observations":observations,"data_preserved":data_ok,
        "catalog_other_than_history_and_app_grants_unchanged":stable_ok,
        "owner_preservation":same_owners,"changed_acl_objects":sorted(acl_changed),
        "application_table_grants_exact":grants_ok,"application_table_grants":after["table_grants"],
        "application_sequence_privileges":sequence,"history_and_legacy_state_privileges_absent":protected_ok}

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
    env["KAN22_MIGRATIONS_DIR"]=str(MIGRATION_DIR)
    env["KAN18_APP_IMAGE"]=IMAGE
    compose=["docker","compose","-p",PROJECT,"-f",str(COMPOSE_FILE)]
    project_filter="label=com.docker.compose.project="+PROJECT
    existing_containers=run("Compose container ownership check",["docker","ps","-aq","--filter",project_filter],env,timeout=30).stdout.strip()
    existing_networks=run("Compose network ownership check",["docker","network","ls","-q","--filter",project_filter],env,timeout=30).stdout.strip()
    existing_volumes=run("Compose volume ownership check",["docker","volume","ls","-q","--filter",project_filter],env,timeout=30).stdout.strip()
    existing_image=run("Candidate image ownership check",["docker","image","inspect",IMAGE],env,timeout=30,check=False)
    existing_probe=run("Peer probe name collision check",["docker","ps","-aq","--filter","name=^/"+PROBE_CONTAINER+"$"],env,timeout=30).stdout.strip()
    existing_naming_probe=run("JNDI probe name collision check",["docker","ps","-aq","--filter","name=^/"+NAMING_PROBE_CONTAINER+"$"],env,timeout=30).stdout.strip()
    if existing_containers or existing_networks or existing_volumes or existing_image.returncode==0 or existing_probe or existing_naming_probe:
        raise RuntimeError("A resource for the unique task project/image already exists")
    try:
        passwords=create_secrets()
        callback_hash=prepare_migrations()
    except Exception:
        if WORK.exists(): shutil.rmtree(WORK)
        raise
    report={"task":"KAN-18/KAN-15 BG-06","status":"FAIL","checks":{},"fixture_inputs":{"flyway_after_each_migrate_callback_sha256":callback_hash},"machine_scope":"Flyway schema migration with server-verified schema_migrator identity; separate from request users","instrumentation_scope":"lab_observer is harness-only instrumentation for server-observed Flyway sessions, not a product schema effect","cleanup":{"compose_down":False,"resource_check_passed":False,"residual_containers":[],"residual_networks":[],"residual_volumes":[],"peer_probe_removed":False,"jndi_probe_removed":False,"work_removed":False,"image_removed":False,"secrets_preserved":False}}
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
        query(env,"CREATE SCHEMA lab_observer AUTHORIZATION db_bootstrap; CREATE TABLE lab_observer.flyway_session_observation(session_user_name text NOT NULL,current_user_name text NOT NULL,current_role_name text NOT NULL,observed_at timestamptz NOT NULL); GRANT USAGE ON SCHEMA lab_observer TO schema_migrator; GRANT INSERT ON lab_observer.flyway_session_observation TO schema_migrator")
        run("Flyway V1 migration",compose+["--profile","migrate","run","--rm","-e","FLYWAY_TARGET=1","migrate"],env,timeout=180)
        history_v1=migration_history(env); observations_v1=migration_session_observations(env)
        catalog_v1=schema_catalog_state(env); data_v1=database_state(env)
        v1_ok=(migration_identity_valid(history_v1,observations_v1,["1"])
            and len(data_v1)==len(TABLES) and all(row["count"]==0 for row in data_v1.values()))
        report["checks"]["flyway_v1_session"]={"passed":v1_ok,"history":history_v1,"session_observation":observations_v1,"empty_business_schema":data_v1}
        if not v1_ok: raise RuntimeError("V1 session identity/history or empty-schema baseline failed")
        seed_populated_v1_schema(env)
        data_before_v2=database_state(env); catalog_before_v2=schema_catalog_state(env)
        expected_counts={"location":2,"voyage":1,"cargo":1,"leg":1,"handling_event":1,"carrier_movement":1,"legacy_sequence_state":1}
        import_ok=({name:row["count"] for name,row in data_before_v2.items()}==expected_counts
            and catalog_before_v2==catalog_v1)
        report["checks"]["synthetic_import_before_upgrade"]={"passed":import_ok,"rows":data_before_v2,"catalog_unchanged":catalog_before_v2==catalog_v1,"sequence_inputs":{"max_entity_id":7007,"legacy_sequence_state":8000,"expected_high_water":8000,"branch_exercised":"legacy_sequence_state"}}
        if not import_ok: raise RuntimeError("Synthetic import changed V1 catalog or row counts diverged")
        run("Flyway V2 migration",compose+["--profile","migrate","run","--rm","-e","FLYWAY_TARGET=2","migrate"],env,timeout=180)
        history_v2=migration_history(env); observations_v2=migration_session_observations(env)
        catalog_v2=schema_catalog_state(env); data_after_v2=database_state(env)
        v2_check=v2_effects(catalog_before_v2,catalog_v2,data_before_v2,data_after_v2,history_v1,history_v2,observations_v2)
        report["checks"]["flyway_v2_populated_upgrade"]=v2_check
        if not v2_check["passed"]: raise RuntimeError("V2 populated-schema migration did not match exact expected effects")
        run("Flyway V3 migration",compose+["--profile","migrate","run","--rm","-e","FLYWAY_TARGET=3","migrate"],env,timeout=180)
        history_v3=migration_history(env); observations_v3=migration_session_observations(env)
        catalog_v3=schema_catalog_state(env); data_after_v3=database_state(env)
        v3_check=v3_effects(catalog_v2,catalog_v3,data_after_v2,data_after_v3,history_v2,history_v3,observations_v3)
        report["checks"]["flyway_v3_runtime_grants"]=v3_check
        if not v3_check["passed"]: raise RuntimeError("V3 grant migration changed objects outside allowed ACL/history delta")
        identity_ok=(migration_identity_valid(history_v3,migration_session_observations(env),["1","2","3"])
            and migrator_auth.stdout.strip().splitlines()[-1]=="schema_migrator")
        report["checks"]["migration_machine_identity"]={"passed":identity_ok,"machine_identity_verified":identity_ok,
            "native_identity":{"server_verified":identity_ok,"principal":"schema_migrator","session_user":"schema_migrator","current_user":"schema_migrator","current_role":"schema_migrator"},
            "machine_scope":"Flyway schema migration with server-verified schema_migrator identity; separate from request users",
            "flyway_installed_by":[row["installed_by"] for row in history_v3],"session_observations":migration_session_observations(env),
            "migrations_only":True,"sample_data_generator_invoked":False,"controlled_import_invoked":False}
        if not identity_ok: raise RuntimeError("Actual Flyway session identity evidence did not match schema_migrator")
        row_preservation={"passed":data_after_v3==data_before_v2,"before_migrations":data_before_v2,"after_v3":data_after_v3}
        report["checks"]["populated_upgrade_preserves_imported_rows"]=row_preservation
        if not row_preservation["passed"]: raise RuntimeError("Imported synthetic row contents changed across V2/V3")
        db_roles=catalog_v3["roles"]
        role_names={row["name"] for row in db_roles}
        role_separation=(role_names=={"cargo_app","schema_migrator"}
            and all(not row["superuser"] and not row["createdb"] and not row["createrole"] for row in db_roles))
        report["checks"]["role_separation"]={"passed":role_separation,"database_roles":db_roles}
        if not role_separation: raise RuntimeError("Database roles are not separated least-privilege identities")
        acl_ok=(catalog_v3["schema"]["migrator_create"] and catalog_v3["schema"]["app_usage"]
            and not catalog_v3["schema"]["app_create"] and not any(catalog_v3["protected_table_privileges"].values())
            and v3_check["application_table_grants_exact"] and v3_check["application_sequence_privileges"]["app_usage"]
            and v3_check["application_sequence_privileges"]["app_select"] and v3_check["application_sequence_privileges"]["app_update"])
        report["checks"]["least_privilege_acl"]={"passed":acl_ok,"schema":catalog_v3["schema"],"protected_table_privileges":catalog_v3["protected_table_privileges"],"application_table_grants":catalog_v3["table_grants"],"application_sequence_privileges":catalog_v3["sequence_privileges"]}
        if not acl_ok: raise RuntimeError("Application or migration ACLs diverge from policy")
        marker="KAN18_"+secrets.token_hex(8).upper()
        insert="INSERT INTO cargo.location(name,unlocode) VALUES ('"+marker+"','ZZTST') RETURNING id"
        marker_result=query(env,insert,username="cargo_app",password_file="app_password",allow_failure=True)
        marker_lines=marker_result.stdout.strip().splitlines()
        marker_id=int(marker_lines[0]) if marker_lines and marker_lines[0].isdigit() else None
        expected_marker_id=8001
        report["checks"]["runtime_dml"]={"passed":marker_result.returncode==0 and marker_id==expected_marker_id,"generated_id":marker_id,"expected_generated_id":expected_marker_id}
        if not report["checks"]["runtime_dml"]["passed"]: raise RuntimeError("cargo_app could not persist the expected sequence-generated ID")
        denial_attempts={
            "persistent_schema_ddl":query(env,"CREATE TABLE cargo.kan18_ddl_probe(id integer)",username="cargo_app",password_file="app_password",allow_failure=True),
            "temporary_table_ddl":query(env,"CREATE TEMP TABLE kan18_temp_probe(id integer)",username="cargo_app",password_file="app_password",allow_failure=True),
            "flyway_history_update":query(env,"UPDATE cargo.flyway_schema_history SET success=success WHERE FALSE",username="cargo_app",password_file="app_password",allow_failure=True),
            "migration_state_update":query(env,"UPDATE cargo.legacy_sequence_state SET seq_count=seq_count WHERE FALSE",username="cargo_app",password_file="app_password",allow_failure=True)}
        report["checks"]["application_ddl_denied"]={name:(result.returncode!=0 and "permission denied" in result.stdout.lower()) for name,result in denial_attempts.items()}
        if not all(report["checks"]["application_ddl_denied"].values()): raise RuntimeError("cargo_app unexpectedly received schema/migration privileges")
        marked=durable_state(env)
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
        peer_probe=peer_tcp_probe(env)
        private_listeners_closed=all(not peer_probe["reachable"][str(port)]
            for port in (8009,8443,9990,9993,3528,3529,4712,4713,5445,5455,5672,61616))
        peer_probe["management_and_private_listener_ports_closed"]=private_listeners_closed
        peer_probe["http_and_remoting_port_reachable"]=peer_probe["reachable"]["8080"]
        peer_probe["passed"]=peer_probe["http_and_remoting_port_reachable"] and private_listeners_closed
        report["checks"]["peer_network_listener_reachability"]=peer_probe
        protocol_before=durable_state(env)
        protocol_probe=remote_jndi_jms_probe(env)
        protocol_after=durable_state(env)
        protocol_probe["database_state_unchanged"]=protocol_before==protocol_after
        protocol_probe["passed"]=protocol_probe["passed"] and protocol_probe["database_state_unchanged"]
        report["checks"]["remote_jndi_jms_protocol_authentication"]=protocol_probe
        after_start=durable_state(env)
        marker_ok=query(env,"SELECT count(*) FROM cargo.location WHERE id="+str(marker_id)+" AND name='"+marker+"'").stdout.strip().splitlines()==["1"]
        report["checks"]["startup_no_orm_ddl_or_seed"]={"passed":after_start==marked and marker_ok,"before":marked,"after":after_start,"marker_preserved":marker_ok}
        if not report["checks"]["startup_no_orm_ddl_or_seed"]["passed"]: raise RuntimeError("Application startup changed persisted data")
        report["checks"]["human_roles"]={}
        for username,role in USERS.items():
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),NoRedirect())
            login_page_status,login_body,_=http_status(BASE+"login",opener)
            token=re.search(r"name='csrf' value='([^']+)'",login_body)
            login_status=session_status=cargo_status=None
            identity={}
            if login_page_status==200 and token is not None:
                payload=urllib.parse.urlencode({"username":username,"password":passwords[username],"csrf":token.group(1)}).encode()
                login_status,_,_=http_status(BASE+"login",opener,payload)
                session_status,session_body,_=http_status(BASE+"session",opener)
                cargo_status,_,_=http_status(BASE+"rest/cargo",opener)
                try: identity=json.loads(session_body)
                except Exception: identity={}
            identity_ok=(login_status==303 and session_status==200
                and identity.get("principal")==username and role in identity.get("roles",[]))
            valid=identity_ok and cargo_status==200
            state=durable_state(env)
            role_passed=valid and state==marked
            report["checks"]["human_roles"][role]={"passed":role_passed,"identity_verified":identity_ok,
                "durable_state_unchanged":state==marked,"login_page_status":login_page_status,
                "csrf_present":token is not None,"login_status":login_status,"session_status":session_status,
                "observed_principal":identity.get("principal"),"observed_roles":identity.get("roles"),
                "cargo_api_status":cargo_status}
        if not all(result["passed"] for result in report["checks"]["human_roles"].values()):
            raise RuntimeError("One or more human application role checks failed")
        run("Candidate app restart",compose+["restart","candidate-app"],env,timeout=90)
        time.sleep(12)
        restarted=durable_state(env)
        report["checks"]["restart_preserves_data"]={"passed":restarted==marked and query(env,"SELECT count(*) FROM cargo.location WHERE id="+str(marker_id)+" AND name='"+marker+"'").stdout.strip().splitlines()==["1"],"after_restart":restarted}
        if not report["checks"]["restart_preserves_data"]["passed"]: raise RuntimeError("Candidate restart changed persisted data")
        report["schema_hashes"]={}
        for relative in (".dockerignore","tests/candidate-runtime/postgresql/Dockerfile","tests/candidate-runtime/postgresql/module.xml","tests/candidate-runtime/postgresql/configure-datasource.cli","tests/candidate-runtime/postgresql/start.sh","tests/candidate-runtime/postgresql/verify_runtime.py","tests/candidate-runtime/postgresql/RemoteJndiReachabilityProbe.java","infrastructure/database/compose.yaml","infrastructure/database/bootstrap/10-create-roles.sh","infrastructure/database/migrations/V1__initial_schema.sql","infrastructure/database/migrations/V2__query_indexes_and_sequence_reconciliation.sql","infrastructure/database/migrations/V3__grant_application_runtime_privileges.sql","candidate/cargotracker/src/main/resources/META-INF/persistence.xml","candidate/cargotracker/src/main/java/net/java/cargotracker/application/util/SampleDataGenerator.java"):
            report["schema_hashes"][relative]=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
        report["versions"]={"postgres":"18.6","flyway":"13.12.1","wildfly":"42","jdbc":"42.7.14"}
        report["status"]="PASS" if all(x.get("passed") for x in report["checks"].values() if isinstance(x,dict) and "passed" in x) else "FAIL"
    except Exception as error:
        report["status"] = "FAIL"
        report["failure"] = str(error)
    finally:
        for cleanup_key,container_name in (("jndi_probe_removed",NAMING_PROBE_CONTAINER),("peer_probe_removed",PROBE_CONTAINER)):
            try:
                removed,cleanup_error=cleanup_owned_probe_container(env,container_name)
                report["cleanup"][cleanup_key]=removed
                if cleanup_error:
                    report["cleanup"][cleanup_key.replace("_removed","_remove_error")]=cleanup_error
            except Exception as error:
                report["cleanup"][cleanup_key]=False
                report["cleanup"][cleanup_key.replace("_removed","_remove_error")]=str(error)
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
        cleanup_ok=(report["cleanup"]["jndi_probe_removed"] and report["cleanup"]["peer_probe_removed"] and report["cleanup"]["compose_down"] and report["cleanup"]["resource_check_passed"]
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
