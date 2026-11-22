#!/usr/bin/env python3
"""Disposable end-to-end KAN-31 PostgreSQL/WildFly quarantine verification."""
from __future__ import annotations
import hashlib
from concurrent.futures import ThreadPoolExecutor
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
RUN = secrets.token_hex(4)
PROJECT = "kan31q-" + RUN
IMAGE = "ai-modernization-kan31-quarantine:" + RUN
WORK = ROOT / ".work" / ("kan31-quarantine-" + RUN)
SECRETS = WORK / "secrets"
MIGRATIONS = WORK / "migrations"
OVERRIDE = WORK / "compose.override.yaml"
COMPOSE_FILE = ROOT / "infrastructure/database/compose.yaml"
BASE_URL = None
CONTAINER = None
HOST_PORT = None
OWNED = False
ENV = os.environ.copy()
ENV.update({"KAN22_SECRET_DIR": str(SECRETS), "KAN22_MIGRATIONS_DIR": str(MIGRATIONS), "KAN18_APP_IMAGE": IMAGE})
report = {"run": PROJECT, "status": "FAIL", "checks": {}, "cleanup": {}}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, newurl):
        return None

def run(label, args, timeout=120, check=True):
    result = subprocess.run(args, cwd=ROOT, env=ENV, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if WORK.exists():
        with (WORK / "run.log").open("a", encoding="utf-8") as log:
            log.write(f"\n## {label} exit={result.returncode}\n")
            log.write(result.stdout[-12000:])
    if check and result.returncode:
        raise RuntimeError(label + " failed: " + "\n".join(result.stdout.splitlines()[-20:]))
    return result

def compose(*args, timeout=120, check=True):
    return run("compose " + " ".join(args), ["docker", "compose", "-p", PROJECT,
        "-f", str(COMPOSE_FILE), "-f", str(OVERRIDE), *args], timeout=timeout, check=check)

def docker_exec(*args, timeout=30, check=True):
    return run("candidate exec", ["docker", "exec", *args], timeout=timeout, check=check)

def create_private_inputs():
    SECRETS.mkdir(parents=True, mode=0o700)
    SECRETS.chmod(0o700)
    values = {name: secrets.token_urlsafe(30) for name in
        ("bootstrap_password", "app_password", "migrator_password", "admin", "reader", "operator", "service")}
    for name in ("bootstrap_password", "app_password", "migrator_password"):
        path = SECRETS / name
        path.write_text(values[name] + "\n", encoding="utf-8")
        path.chmod(0o444)
    users = "#$REALM_NAME=ApplicationRealm$\n" + "".join(
        f"{name}={hashlib.md5((name + ':ApplicationRealm:' + values[name]).encode()).hexdigest()}\n"
        for name in ("admin", "reader", "operator", "service"))
    roles = chr(10).join(["admin=Administrator", "reader=Reader", "operator=Operator", "service=HandlingWorker", ""])
    for name, content in (("application-users.properties", users), ("application-roles.properties", roles)):
        path = SECRETS / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o444)
    shutil.copytree(ROOT / "infrastructure/database/migrations", MIGRATIONS)
    OVERRIDE.write_text('''services:
  candidate-app:
    build:
      dockerfile: tests/candidate-runtime/quarantine/Dockerfile
    environment:
      CARGO_HANDLING_ATTEMPT_TTL_MS: "5000"
      CARGO_HANDLING_QUARANTINE_MAX_BYTES: "100"
      CARGO_HANDLING_QUARANTINE_RETENTION_SECONDS: "600"
      CARGO_HANDLING_QUARANTINE_REDELIVERY_DELAY_MS: "2000"
      LAB_CANDIDATE_HOSTNAME: candidate-app
''', encoding="utf-8")
    return values

def sql(statement):
    script = 'exec psql -U db_bootstrap -d cargotracker -v ON_ERROR_STOP=1 -At -c "$1"'
    return run("isolated postgres query", ["docker", "compose", "-p", PROJECT,
        "-f", str(COMPOSE_FILE), "-f", str(OVERRIDE), "exec", "-T", "postgres",
        "sh", "-ec", script, "sh", statement], timeout=30).stdout.strip()

def management(command, check=True):
    if not CONTAINER: raise RuntimeError("Candidate container ID is not set")
    return docker_exec(CONTAINER, "/opt/jboss/wildfly/bin/jboss-cli.sh",
        "--connect", "--controller=127.0.0.1:9990", "--command=" + command,
        timeout=30, check=check).stdout

def queue_metrics(queue_name):
    output = management("/subsystem=messaging-activemq/server=default/runtime-queue=jms.queue." + queue_name + ":read-resource(include-runtime=true)")
    values = {}
    for key in ("message-count", "scheduled-count", "delivering-count", "messages-added", "messages-expired"):
        match = re.search(r'"?' + re.escape(key) + r'"?\s*=>\s*(\d+)', output, re.IGNORECASE)
        if match: values[key] = int(match.group(1))
    if "message-count" not in values:
        raise RuntimeError("Could not read queue metrics: " + output[-1200:])
    return values

def request(opener, url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try: response = opener.open(req, timeout=10)
    except urllib.error.HTTPError as error: response = error
    with response: return response.status, response.read().decode("utf-8", "replace")

def login(username, password):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect())
    status, body = request(opener, BASE_URL + "login")
    token = re.search(r"name=['\"]csrf['\"] value=['\"]([^'\"]+)", body)
    if status != 200 or token is None: raise RuntimeError("Login form unavailable for " + username)
    status, _ = request(opener, BASE_URL + "login",
        urllib.parse.urlencode({"username": username, "password": password, "csrf": token.group(1)}).encode(),
        {"Content-Type": "application/x-www-form-urlencoded"})
    if status not in (302, 303): raise RuntimeError("Login failed for " + username + " with HTTP " + str(status))
    return opener

def report_event(opener, tracking_id, request_id=None, unlocode="FIHEL"):
    status, session = request(opener, BASE_URL + "session")
    csrf = json.loads(session)["csrf"] if status == 200 else ""
    payload = json.dumps({"trackingId": tracking_id, "eventType": "LOAD",
        "unLocode": unlocode, "completionTime": "2030-01-01 10:00"}).encode()
    headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf}
    if request_id is not None: headers["Idempotency-Key"] = request_id
    status, body = request(opener, BASE_URL + "rest/handling/reports", payload, headers)
    return status, body


def replay_request(opener, entry_id):
    status, session = request(opener, BASE_URL + "session")
    csrf = json.loads(session)["csrf"] if status == 200 else ""
    return request(opener, BASE_URL + f"rest/handling/quarantine/replay?id={entry_id}",
        b"", {"X-CSRF-Token": csrf})


def fresh_admin_report(passwords, tracking_id, request_id, unlocode="FIHEL"):
    return report_event(login("admin", passwords["admin"]), tracking_id, request_id, unlocode)

def wait_for(label, predicate, seconds):
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last: return last
        time.sleep(1)
    raise RuntimeError(label + " timed out; last observation=" + repr(last))

def db_state():
    return sql("SELECT (SELECT count(*) FROM cargo.handling_attempt_quarantine)||'|'||"
        "(SELECT COALESCE(sum(payload_size_bytes),0) FROM cargo.handling_attempt_quarantine)||'|'||"
        "(SELECT capacity_alert_active FROM cargo.handling_quarantine_state WHERE singleton_id=1)")

def app_ready():
    try:
        status, _ = request(urllib.request.build_opener(NoRedirect()), BASE_URL + "login")
        return status == 200
    except OSError: return False

def check(name, passed, detail=None):
    report["checks"][name] = {"passed": bool(passed), "detail": detail}
    if not passed: raise AssertionError(name)

def main(passwords):
    global BASE_URL, CONTAINER, HOST_PORT
    with socket.socket() as port_probe:
        port_probe.bind(("127.0.0.1", 0))
        HOST_PORT = port_probe.getsockname()[1]
    ENV["KAN22_CANDIDATE_BIND_PORT"] = str(HOST_PORT)
    report["host_port"] = HOST_PORT
    print("building isolated PostgreSQL-backed candidate", flush=True)
    run("candidate image build", ["docker", "build", "--no-cache", "--progress=plain", "-f",
        "tests/candidate-runtime/quarantine/Dockerfile", "-t", IMAGE, "."], timeout=900)
    print("starting isolated PostgreSQL and applying Flyway", flush=True)
    compose("up", "-d", "--wait", "--wait-timeout", "120", "postgres", timeout=180)
    compose("--profile", "migrate", "run", "--rm", "migrate", timeout=180)
    migration_version = sql("SELECT version FROM cargo.flyway_schema_history WHERE success ORDER BY installed_rank DESC LIMIT 1")
    check("Flyway V6 applied", migration_version == "6", migration_version)
    print("starting disposable WildFly candidate", flush=True)
    compose("--profile", "candidate-app", "up", "-d", "candidate-app", timeout=180)
    port_output = compose("port", "candidate-app", "8080").stdout.strip().splitlines()[-1]
    port = int(port_output.rsplit(":", 1)[1])
    BASE_URL = f"http://127.0.0.1:{port}/cargo-tracker/"
    wait_for("candidate HTTP startup", app_ready, 150)
    container = compose("ps", "-q", "candidate-app").stdout.strip()
    if not container: raise RuntimeError("Candidate container ID unavailable")
    CONTAINER = container
    report["candidate_container"] = container
    jcmd = "/opt/java/openjdk/bin/jcmd"
    jvm_list = docker_exec(CONTAINER, jcmd, "-l").stdout
    pid_match = next((match for line in jvm_list.splitlines() if "jcmd" not in line.lower() and (match := re.match(r"^(\d+)\s+", line))), None)
    if not pid_match: raise RuntimeError("WildFly JVM was not listed by jcmd: " + jvm_list[-500:])
    vm_properties = docker_exec(CONTAINER, jcmd, pid_match.group(1), "VM.system_properties").stdout
    cap = re.search(r"(?m)^cargo\.handling\.quarantine\.max\.bytes=(.+)$", vm_properties)
    retention = re.search(r"(?m)^cargo\.handling\.quarantine\.retention\.seconds=(.+)$", vm_properties)
    redelivery = re.search(r"(?m)^cargo\.handling\.quarantine\.redelivery\.delay\.ms=(.+)$", vm_properties)
    check("runtime quarantine capacity override", cap is not None and cap.group(1).strip() == "100", vm_properties[-1200:])
    check("runtime retention override", retention is not None and retention.group(1).strip() == "600", vm_properties[-1200:])
    check("runtime quarantine redelivery override", redelivery is not None and redelivery.group(1).strip() == "2000", vm_properties[-1200:])
    settings = management("/subsystem=messaging-activemq/server=default/address-setting=jms.queue.HandlingAttemptQuarantineIntakeQueue:read-resource")
    check("broker uses the externally configured pending-message retry delay", re.search(r"redelivery-delay.*env\.CARGO_HANDLING_QUARANTINE_REDELIVERY_DELAY_MS", settings, re.IGNORECASE) is not None, settings[-1200:])
    admin = login("admin", passwords["admin"])
    reader = login("reader", passwords["reader"])
    operator = login("operator", passwords["operator"])
    service = login("service", passwords["service"])
    anonymous = urllib.request.build_opener(NoRedirect())
    status, _ = request(anonymous, BASE_URL + "rest/handling/quarantine")
    check("anonymous quarantine API denied", status == 401, status)
    status, _ = request(reader, BASE_URL + "rest/handling/quarantine")
    check("Reader quarantine API denied", status == 403, status)
    status, _ = request(operator, BASE_URL + "rest/handling/quarantine")
    check("Operator quarantine API denied", status == 403, status)
    status, _ = request(service, BASE_URL + "rest/handling/quarantine")
    check("service-role quarantine API denied", status == 403, status)
    status, body = request(admin, BASE_URL + "rest/handling/quarantine")
    check("Administrator quarantine API allowed", status == 200, {"status": status, "body": body[:1000]})
    check("empty quarantine is reported", json.loads(body).get("entries") == [], body[:250])

    source = "/subsystem=messaging-activemq/server=default/runtime-queue=jms.queue.HandlingEventRegistrationAttemptQueue"
    intake = "/subsystem=messaging-activemq/server=default/runtime-queue=jms.queue.HandlingAttemptQuarantineIntakeQueue"
    result = management(intake + ":pause")
    check("quarantine intake pauses for exhausted-message check", "success" in result.lower(), result[-250:])
    exhausted_key = "kan31-" + RUN + "-exhausted"
    exhausted_status, exhausted_body = report_event(admin, "NOCARGO_EXHAUST", exhausted_key)
    check("exhausted test submission accepted", exhausted_status == 204, exhausted_body[:250])
    exhausted_pending = wait_for("exhausted message routed durably to intake", lambda: (
        (lambda metrics: metrics if metrics["message-count"] >= 1 else None)(queue_metrics("HandlingAttemptQuarantineIntakeQueue"))
    ), 25)
    source_after_exhaust = queue_metrics("HandlingEventRegistrationAttemptQueue")
    check("handler retry exhaustion transfers to quarantine intake",
        exhausted_pending["message-count"] == 1 and source_after_exhaust["message-count"] == 0,
        {"intake": exhausted_pending, "source": source_after_exhaust})
    management(intake + ":resume")
    exhausted_sql = chr(36) * 2 + "NOCARGO_EXHAUST" + chr(36) * 2
    wait_for("exhausted message persisted for review", lambda: sql(
        "SELECT count(*) FROM cargo.handling_attempt_quarantine WHERE tracking_id=" + exhausted_sql) == "1", 15)
    deleted_exhausted = sql("DELETE FROM cargo.handling_attempt_quarantine WHERE tracking_id=" + exhausted_sql + " RETURNING id")
    check("exhausted attempt recorded in quarantine before isolated cleanup", bool(deleted_exhausted), deleted_exhausted)
    result = management(source + ":pause")
    check("source queue can be paused", "success" in result.lower(), result[-250:])
    key = "kan31-" + RUN + "-same"
    before_duplicate = queue_metrics("HandlingEventRegistrationAttemptQueue")
    with ThreadPoolExecutor(max_workers=2) as pool:
        duplicate_responses = list(pool.map(
            lambda _: fresh_admin_report(passwords, "NOCARGO1", key), range(2)))
    duplicate_metrics = queue_metrics("HandlingEventRegistrationAttemptQueue")
    check("concurrent same-ID/same-payload requests enqueue once",
        all(status == 204 for status, _ in duplicate_responses)
        and duplicate_metrics["messages-added"] - before_duplicate["messages-added"] == 1
        and duplicate_metrics["message-count"] == 1, duplicate_metrics)
    changed_status, changed_body = report_event(admin, "NOCARGO1", key, "SESTO")
    after_changed_payload = queue_metrics("HandlingEventRegistrationAttemptQueue")
    check("same-ID/changed-payload request is rejected without enqueue",
        changed_status == 409 and after_changed_payload["messages-added"] == duplicate_metrics["messages-added"],
        {"status": changed_status, "body": changed_body[:200], "queue": after_changed_payload})
    ledger_key = chr(36) * 2 + key + chr(36) * 2
    ledger_count = sql("SELECT count(*) FROM cargo.handling_request_idempotency WHERE request_id=" + ledger_key)
    check("same request identity is durably reserved once", ledger_count == "1", ledger_count)
    time.sleep(7)
    management(source + ":resume")
    first = wait_for("first expired attempt in PostgreSQL", lambda: (lambda state: state if state.startswith("1|") else None)(db_state()), 30)
    first_size = int(first.split("|")[1])
    check("first expired event stored below cap", first_size < 100, first)
    report["first_expired_attempt"] = {"db_state": first, "queue": queue_metrics("HandlingAttemptQuarantineIntakeQueue")}

    result = management(source + ":pause")
    check("source queue paused for capacity case", "success" in result.lower(), result[-250:])
    report_event(admin, "NOCARGO2")
    report_event(admin, "NOCARGO4")
    time.sleep(7)
    management(source + ":resume")
    pending = wait_for("full-capacity alert and pending intake", lambda: (
        (lambda state: state if state.startswith("1|") and state.endswith("|true") else None)(db_state())
    ), 25)
    pending_count = wait_for("both blocked messages are durably tracked", lambda: (
        (lambda value: value if value == "2" else None)(sql("SELECT count(*) FROM cargo.handling_quarantine_pending"))
    ), 10)
    pending_queue = queue_metrics("HandlingAttemptQuarantineIntakeQueue")
    check("capacity failure leaves both attempts durably pending", pending_count == "2" and pending_queue["message-count"] >= 2,
        {"db": pending, "pendingCount": pending_count, "queue": pending_queue})
    status, body = request(admin, BASE_URL + "rest/handling/quarantine")
    snapshot = json.loads(body)
    check("Administrator observes full alert, stored payload and both pending messages", status == 200
        and snapshot["capacityAlertActive"] and snapshot["storedPayloadBytes"] == first_size
        and snapshot["pendingIntakeCount"] == 2, snapshot)

    print("replacing the disposable WildFly candidate while intake is full", flush=True)
    old_container = CONTAINER
    compose("up", "-d", "--force-recreate", "candidate-app", timeout=180)
    new_container = compose("ps", "-q", "candidate-app").stdout.strip()
    check("candidate container was replaced", bool(new_container) and new_container != old_container,
        {"before": old_container, "after": new_container})
    CONTAINER = new_container
    wait_for("candidate HTTP startup after container replacement", app_ready, 150)
    admin = login("admin", passwords["admin"])
    reader = login("reader", passwords["reader"])
    operator = login("operator", passwords["operator"])
    service = login("service", passwords["service"])
    after_restart = db_state()
    pending_after_restart = queue_metrics("HandlingAttemptQuarantineIntakeQueue")
    check("PostgreSQL quarantine and alert survive container replacement", after_restart.endswith("|true") and after_restart.split("|")[0] == "1", after_restart)
    check("persistent Artemis intake survives container replacement", pending_after_restart["message-count"] >= 2
        and sql("SELECT count(*) FROM cargo.handling_quarantine_pending") == "2", pending_after_restart)

    expired = sql("UPDATE cargo.handling_attempt_quarantine SET expires_at=CURRENT_TIMESTAMP - INTERVAL '1 second' WHERE tracking_id='NOCARGO1' RETURNING id")
    check("retention is given an expired stored attempt to purge", bool(expired), expired)
    first_transfer = wait_for("one pending attempt transfers while the second remains blocked", lambda: (
        (lambda state: (lambda tracking, pending, queue: {"state": state, "tracking": tracking,
            "pending": pending, "queue": queue} if state.endswith("|true") and tracking in ("NOCARGO2", "NOCARGO4")
            and pending == "1" and queue["message-count"] >= 1 else None)(
                sql("SELECT tracking_id FROM cargo.handling_attempt_quarantine LIMIT 1"),
                sql("SELECT count(*) FROM cargo.handling_quarantine_pending"),
                queue_metrics("HandlingAttemptQuarantineIntakeQueue")))(db_state())
    ), 45)
    check("alert stays active while another intake message remains pending", first_transfer["pending"] == "1"
        and first_transfer["queue"]["message-count"] >= 1 and first_transfer["tracking"] in ("NOCARGO2", "NOCARGO4"), first_transfer)
    status, body = request(admin, BASE_URL + "rest/handling/quarantine")
    partial_snapshot = json.loads(body)
    check("Administrator sees one remaining blocked message and active alert", status == 200
        and partial_snapshot["capacityAlertActive"] and partial_snapshot["pendingIntakeCount"] == 1, partial_snapshot)
    freed = sql("UPDATE cargo.handling_attempt_quarantine SET expires_at=CURRENT_TIMESTAMP - INTERVAL '1 second' WHERE tracking_id='" + first_transfer["tracking"] + "' RETURNING id")
    check("retention frees the first transferred payload", bool(freed), freed)
    report["after_capacity_freed"] = wait_for("last pending message transfers and clears alert", lambda: (
        (lambda state: state if state.startswith("1|") and state.endswith("|false")
            and sql("SELECT count(*) FROM cargo.handling_quarantine_pending") == "0"
            and queue_metrics("HandlingAttemptQuarantineIntakeQueue")["message-count"] == 0 else None)(db_state())
    ), 45)
    status, body = request(admin, BASE_URL + "rest/handling/quarantine")
    snapshot = json.loads(body)
    remaining_tracking = snapshot["entries"][0]["trackingId"] if snapshot["entries"] else None
    check("Administrator sees recovered capacity and final entry", status == 200 and not snapshot["capacityAlertActive"]
        and snapshot["pendingIntakeCount"] == 0 and remaining_tracking in ("NOCARGO2", "NOCARGO4")
        and remaining_tracking != first_transfer["tracking"], snapshot)


    source_pause = management(source + ":pause")
    check("source queue pauses before explicit replay", "success" in source_pause.lower(), source_pause[-250:])
    entry_id = snapshot["entries"][0]["id"]
    anonymous = urllib.request.build_opener(NoRedirect())
    status, _ = replay_request(anonymous, entry_id)
    check("anonymous quarantine replay denied", status == 401, status)
    status, _ = replay_request(reader, entry_id)
    check("Reader quarantine replay denied", status == 403, status)
    status, _ = replay_request(operator, entry_id)
    check("Operator quarantine replay denied", status == 403, status)
    status, _ = replay_request(service, entry_id)
    check("service-role quarantine replay denied", status == 403, status)
    replay_request_id = snapshot["entries"][0]["requestId"]
    before_replay_queue = queue_metrics("HandlingEventRegistrationAttemptQueue")
    status, replay_body = replay_request(admin, entry_id)
    check("Administrator explicitly replays quarantined attempt", status == 202, replay_body[:250])
    after_replay_queue = queue_metrics("HandlingEventRegistrationAttemptQueue")
    audit_count = sql("SELECT count(*) FROM cargo.handling_quarantine_replay_audit")
    check("replay enqueue is audited once and removes the active quarantine payload",
        after_replay_queue["messages-added"] - before_replay_queue["messages-added"] == 1
        and after_replay_queue["message-count"] == before_replay_queue["message-count"] + 1
        and audit_count == "1" and sql("SELECT count(*) FROM cargo.handling_attempt_quarantine WHERE id=" + str(entry_id)) == "0",
        {"queue": after_replay_queue, "auditRows": audit_count})
    status, _ = replay_request(admin, entry_id)
    check("duplicate manual replay is rejected", status == 409
        and sql("SELECT count(*) FROM cargo.handling_quarantine_replay_audit") == "1", status)

    time.sleep(7)
    management(source + ":resume")
    replayed_row = wait_for("failed replay can be quarantined again under the same request ID", lambda: (
        (lambda row: row if row and row != str(entry_id) else None)(sql(
            "SELECT id FROM cargo.handling_attempt_quarantine WHERE request_id='" + replay_request_id + "' LIMIT 1"))
    ), 20)
    replayed_entry_id = int(replayed_row)
    replay_state = sql("SELECT state FROM cargo.handling_request_idempotency WHERE request_id='" + replay_request_id + "'")
    check("replayed request re-enters quarantine with a new payload row and stable identity",
        replayed_entry_id != entry_id and replay_state == "QUARANTINED"
        and sql("SELECT count(*) FROM cargo.handling_quarantine_replay_audit") == "1",
        {"oldEntryId": entry_id, "newEntryId": replayed_entry_id, "requestIdState": replay_state})
    result = management(source + ":pause")
    check("source queue pauses after replay re-quarantine", "success" in result.lower(), result[-250:])

    before_distinct = queue_metrics("HandlingEventRegistrationAttemptQueue")
    before_ledger = sql("SELECT count(*) FROM cargo.handling_request_idempotency")
    distinct_a = report_event(admin, "NOCARGO3", "kan31-" + RUN + "-distinct-a")
    distinct_b = report_event(admin, "NOCARGO3", "kan31-" + RUN + "-distinct-b")
    after_distinct = queue_metrics("HandlingEventRegistrationAttemptQueue")
    after_ledger = sql("SELECT count(*) FROM cargo.handling_request_idempotency")
    check("different IDs accept identical event fields as distinct submissions",
        distinct_a[0] == 204 and distinct_b[0] == 204
        and after_distinct["messages-added"] - before_distinct["messages-added"] == 2
        and int(after_ledger) - int(before_ledger) == 2,
        {"responses": [distinct_a[0], distinct_b[0]], "queue": after_distinct, "ledgerRows": after_ledger})

    sql("CREATE OR REPLACE FUNCTION cargo.kan31_delay_quarantine_delete() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "BEGIN IF OLD.id=" + str(replayed_entry_id) + " THEN PERFORM pg_advisory_lock(987654321); "
        "PERFORM pg_sleep(12); PERFORM pg_advisory_unlock(987654321); END IF; RETURN OLD; END; $$")
    sql("CREATE TRIGGER kan31_delay_quarantine_delete BEFORE DELETE ON cargo.handling_attempt_quarantine "
        "FOR EACH ROW EXECUTE FUNCTION cargo.kan31_delay_quarantine_delete()")
    sql("UPDATE cargo.handling_attempt_quarantine SET expires_at=CURRENT_TIMESTAMP - INTERVAL '1 second'")
    wait_for("retention worker is deliberately delayed inside the delete trigger", lambda: (
        "locked" if sql("SELECT pg_try_advisory_lock(987654321)") == "f" else None
    ), 20)
    status, body = request(admin, BASE_URL + "rest/handling/quarantine")
    delayed_snapshot = json.loads(body)
    check("expired payload is hidden before delayed cleanup", status == 200 and delayed_snapshot["entries"] == []
        and delayed_snapshot["storedPayloadBytes"] == 0
        and sql("SELECT count(*) FROM cargo.handling_attempt_quarantine WHERE id=" + str(replayed_entry_id)) == "1",
        delayed_snapshot)
    status, _ = replay_request(admin, replayed_entry_id)
    check("expired payload cannot be replayed while cleanup is delayed", status == 409, status)
    cleaned = wait_for("retention job removes expired quarantine row", lambda: sql(
        "SELECT count(*) FROM cargo.handling_attempt_quarantine") == "0", 18)
    check("scheduled retention removes the expired replay payload", cleaned is not None)
    sql("DROP TRIGGER kan31_delay_quarantine_delete ON cargo.handling_attempt_quarantine")
    sql("DROP FUNCTION cargo.kan31_delay_quarantine_delete()")
    check("replay audit survives payload retention cleanup", sql("SELECT count(*) FROM cargo.handling_quarantine_replay_audit") == "1")
    report["status"] = "PASS"

if __name__ == "__main__":
    try:
        if WORK.exists(): raise RuntimeError("Unique work directory already exists; inspect it before reuse")
        WORK.mkdir(parents=True, mode=0o700)
        OWNED = True
        collision = subprocess.run(["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + PROJECT],
            capture_output=True, text=True, timeout=30).stdout.strip()
        if collision: raise RuntimeError("Unique Compose project collision")
        passwords = create_private_inputs()
        main(passwords)
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = type(error).__name__ + ": " + str(error)[:1200]
    finally:
        if OWNED:
            try:
                ids = subprocess.run(["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + PROJECT],
                    capture_output=True, text=True, timeout=30).stdout.split()
                if ids:
                    logs = subprocess.run(["docker", "logs", "--tail", "600", ids[0]],
                        capture_output=True, text=True, timeout=30)
                    with (WORK / "run.log").open("a", encoding="utf-8") as log:
                        log.write("\n## isolated candidate logs\n" + logs.stdout[-16000:] + logs.stderr[-5000:])
                    server_log = subprocess.run(["docker", "cp", ids[0] + ":/opt/jboss/wildfly/standalone/log/server.log", str(WORK / "server.log")], capture_output=True, text=True, timeout=30)
                    report["cleanup"]["server_log_captured"] = server_log.returncode == 0
            except Exception as error:
                report["cleanup"]["log_capture_error"] = type(error).__name__
            try:
                cleanup = subprocess.run(["docker", "compose", "-p", PROJECT, "-f", str(COMPOSE_FILE),
                    "-f", str(OVERRIDE), "--profile", "candidate-app", "--profile", "migrate",
                    "down", "--volumes", "--remove-orphans"], cwd=ROOT, env=ENV, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
                report["cleanup"]["compose_down"] = cleanup.returncode == 0
                with (WORK / "run.log").open("a", encoding="utf-8") as log:
                    log.write("\n## cleanup\n" + cleanup.stdout[-5000:])
            except Exception as error:
                report["cleanup"]["compose_down_error"] = type(error).__name__
            try:
                containers = subprocess.run(["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + PROJECT],
                    capture_output=True, text=True, timeout=30).stdout.split()
                networks = subprocess.run(["docker", "network", "ls", "-q", "--filter", "label=com.docker.compose.project=" + PROJECT],
                    capture_output=True, text=True, timeout=30).stdout.split()
                volumes = subprocess.run(["docker", "volume", "ls", "-q", "--filter", "label=com.docker.compose.project=" + PROJECT],
                    capture_output=True, text=True, timeout=30).stdout.split()
                report["cleanup"]["no_project_resources_remain"] = not containers and not networks and not volumes
                report["cleanup"]["residual_resources"] = {"containers": containers, "networks": networks, "volumes": volumes}
            except Exception as error:
                report["cleanup"]["resource_check_error"] = type(error).__name__
            try:
                inspected = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True,
                    text=True, timeout=20).returncode == 0
                removed = subprocess.run(["docker", "image", "rm", IMAGE], capture_output=True,
                    text=True, timeout=30).returncode == 0 if inspected else True
                report["cleanup"]["image_removed"] = removed
            except Exception as error:
                report["cleanup"]["image_remove_error"] = type(error).__name__
            if SECRETS.exists():
                try:
                    for secret in SECRETS.iterdir(): secret.chmod(0o600)
                    shutil.rmtree(SECRETS)
                    report["cleanup"]["private_credentials_removed"] = not SECRETS.exists()
                except Exception as error:
                    report["cleanup"]["private_cleanup_error"] = type(error).__name__
            report["cleanup"]["private_credentials_removed"] = not SECRETS.exists()
            if WORK.exists():
                (WORK / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2), flush=True)
