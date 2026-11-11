#!/usr/bin/env python3
"""Run a fresh disposable BG-06 boundary fixture and validate its scoped gate receipt."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "tests/candidate-runtime/postgresql/verify_runtime.py"
RAW = ROOT / ".work/kan18-postgresql-last-result.json"
OUTPUT = ROOT / "notes/evidence/kan-15-bg06-scope/validation.json"
MACHINE_SCOPE = "Flyway schema migration with server-verified schema_migrator identity; separate from request users"
CANONICAL_MACHINE_SCOPE = "Flyway schema migration with server-verified schema_migrator identity"
HUMAN_CONTRACT_SOURCE = ("No human-triggerable reseed or schema-DDL entry point; startup-only sample "
    "generator and ORM schema action must remain disabled")
MACHINE_CONTRACT_SOURCE = ("Flyway deployment migrations using schema_migrator; startup sample seeding "
    "and ORM schema generation remain disabled")
EXPECTED_PRINCIPALS = {"Reader": "reader", "Operator": "operator", "Administrator": "admin"}
REQUIRED_SOURCE_FILES = {
    "tests/security/test_bg06_startup_boundary.py",
    "tests/security/run_bg06_scoped_gate.py",
    "candidate/cargotracker/src/main/java/net/java/cargotracker/application/util/SampleDataGenerator.java",
    "candidate/cargotracker/src/main/resources/META-INF/persistence.xml",
    "candidate/cargotracker/src/main/webapp/WEB-INF/web.xml",
    "candidate/cargotracker/src/main/webapp/WEB-INF/jboss-ejb3.xml",
    "candidate/cargotracker/deployment/wildfly/notification-disposition.cli",
    "infrastructure/database/compose.yaml",
    "tests/candidate-runtime/postgresql/verify_runtime.py",
    "tests/candidate-runtime/postgresql/RemoteJndiReachabilityProbe.java",
    "tests/security/desired-cases.json",
    "specifications/access-policy-inventory.json",
}
REQUIRED_SCHEMA_FILES = {
    ".dockerignore",
    "tests/candidate-runtime/postgresql/Dockerfile",
    "tests/candidate-runtime/postgresql/module.xml",
    "tests/candidate-runtime/postgresql/configure-datasource.cli",
    "tests/candidate-runtime/postgresql/start.sh",
    "tests/candidate-runtime/postgresql/verify_runtime.py",
    "tests/candidate-runtime/postgresql/RemoteJndiReachabilityProbe.java",
    "infrastructure/database/compose.yaml",
    "infrastructure/database/bootstrap/10-create-roles.sh",
    "infrastructure/database/migrations/V1__initial_schema.sql",
    "infrastructure/database/migrations/V2__query_indexes_and_sequence_reconciliation.sql",
    "infrastructure/database/migrations/V3__grant_application_runtime_privileges.sql",
    "candidate/cargotracker/src/main/resources/META-INF/persistence.xml",
    "candidate/cargotracker/src/main/java/net/java/cargotracker/application/util/SampleDataGenerator.java",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(report: dict) -> tuple[list[dict], list[str], dict]:
    reasons = []
    checks = report.get("checks", {})
    cleanup = report.get("cleanup", {})
    human = checks.get("bg06_human_boundary", {})
    machine = checks.get("bg06_machine_boundary", {})
    source_hashes = report.get("bg06_source_sha256", {})
    schema_hashes = report.get("schema_hashes", {})
    if report.get("task") != "KAN-18/KAN-15 BG-06" or report.get("status") != "PASS":
        reasons.append("fresh runtime report did not finish PASS")
    if not isinstance(report.get("run_id"), str) or not report["run_id"].startswith("kan18pg-"):
        reasons.append("fresh run identifier is missing")
    if not checks.get("bg06_static_source_inventory", {}).get("passed"):
        reasons.append("BG-06 source/JMS interface inventory failed")
    missing = REQUIRED_SOURCE_FILES - set(source_hashes)
    if missing:
        reasons.append("source fingerprint omits required files: " + ", ".join(sorted(missing)))
    for name, expected_hash in source_hashes.items():
        path = ROOT / name
        if not path.is_file() or digest(path) != expected_hash:
            reasons.append("source fingerprint no longer matches: " + name)
    if set(schema_hashes) != REQUIRED_SCHEMA_FILES:
        reasons.append("runtime schema/fixture fingerprint set is incomplete or unexpected")
    for name, expected_hash in schema_hashes.items():
        path = ROOT / name
        if not path.is_file() or digest(path) != expected_hash:
            reasons.append("runtime schema/fixture fingerprint no longer matches: " + name)
    webapp_prefix = "candidate/cargotracker/src/main/webapp/"
    actual_webapp_files = {path.relative_to(ROOT).as_posix()
        for path in (ROOT / "candidate/cargotracker/src/main/webapp").rglob("*") if path.is_file()}
    pinned_webapp_files = {name for name in source_hashes if name.startswith(webapp_prefix)}
    if actual_webapp_files != pinned_webapp_files:
        reasons.append("deployed webapp file inventory differs from the pinned BG-06 source set")
    if not human.get("passed") or human.get("driver") != "bg06-fresh-role-aware-no-callable-surface-v1":
        reasons.append("fresh human boundary adapter evidence is absent or failed")
    actor_rows = human.get("actors", {})
    expected_actors = {"anonymous", "Reader", "Operator", "Administrator"}
    if set(actor_rows) != expected_actors:
        reasons.append("human BG-06 actor set is incomplete")
    for actor in sorted(expected_actors & set(actor_rows)):
        row = actor_rows[actor]
        if row.get("passed") is not True or row.get("expected") != "deny":
            reasons.append(actor + " denial/effect evidence did not pass")
        if row.get("no_callable_seed_or_schema_entrypoint") is not True:
            reasons.append(actor + " lacks no-callable-entrypoint evidence")
        if row.get("database_effects_unchanged") is not True:
            reasons.append(actor + " changed or lacks database effect evidence")
        if row.get("application_database_ddl_denied") is not True:
            reasons.append(actor + " lacks application-role DDL denial evidence")
        identity = row.get("identity")
        if actor == "anonymous":
            if identity is not None:
                reasons.append("anonymous case unexpectedly has an authenticated identity")
            entry = row.get("entrypoint_evidence", {})
            if (entry.get("application_api_status") not in (302, 401)
                    or entry.get("remote_jndi_authentication_denied") is not True
                    or entry.get("remote_exported_namespace_access_denied") is not True):
                reasons.append("anonymous control-plane denial evidence is incomplete")
        else:
            if (identity.get("server_verified") is not True
                    or identity.get("principal") != EXPECTED_PRINCIPALS[actor]
                    or identity.get("roles") != [actor]):
                reasons.append(actor + " server-verified identity/role is wrong")
            entry = row.get("entrypoint_evidence", {})
            if (entry.get("remote_exported_leaf_names") != ["jms/RemoteConnectionFactory"]
                    or entry.get("remote_seed_generator_binding_absent") is not True
                    or entry.get("remote_connection_started") is not True):
                reasons.append(actor + " remote exported naming inventory is incomplete or unexpected")
    ddl = checks.get("application_ddl_denied", {})
    ddl_identity = ddl.get("native_identity", {})
    if (ddl.get("passed") is not True or ddl.get("driver") != "direct-postgresql-session-v1"
            or ddl_identity.get("server_verified") is not True
            or ddl_identity.get("principal") != "cargo_app"
            or any(row.get("denied") is not True for row in ddl.get("attempts", {}).values())
            or set(ddl.get("attempts", {})) != {"persistent_schema_ddl", "temporary_table_ddl",
                "flyway_history_update", "migration_state_update"}
            or ddl.get("database_effects_unchanged") is not True):
        reasons.append("application-role DDL/metadata denial or unchanged-effect evidence failed")
    for check_name in ("startup_no_orm_ddl_or_seed", "restart_preserves_data"):
        if checks.get(check_name, {}).get("passed") is not True:
            reasons.append(check_name + " did not preserve the database state")
    listeners = checks.get("peer_network_listener_reachability", {})
    reachable = listeners.get("reachable", {})
    if (listeners.get("passed") is not True
            or reachable.get("8080") is not True
            or any(reachable.get(str(port)) is not False for port in
                (8009, 8443, 9990, 9993, 3528, 3529, 4712, 4713, 5445, 5455, 5672, 61616))):
        reasons.append("management/private listener network probe failed")
    protocol = checks.get("remote_jndi_jms_protocol_authentication", {})
    if protocol.get("passed") is not True or protocol.get("database_state_unchanged") is not True:
        reasons.append("remote JNDI/JMS authentication and read-only probe failed")
    if not machine.get("passed") or machine.get("driver") != "bg06-fresh-schema-migration-scope-v1":
        reasons.append("fresh migration machine-scope adapter evidence is absent or failed")
    migration = checks.get("migration_machine_identity", {})
    native = migration.get("native_identity", {})
    if (migration.get("passed") is not True or migration.get("machine_scope") != MACHINE_SCOPE
            or native.get("server_verified") is not True or native.get("principal") != "schema_migrator"
            or native.get("session_user") != "schema_migrator"
            or native.get("current_user") != "schema_migrator"
            or native.get("current_role") != "schema_migrator"
            or migration.get("flyway_installed_by") != ["schema_migrator"] * 3
            or migration.get("migrations_only") is not True
            or migration.get("sample_data_generator_invoked") is not False
            or migration.get("controlled_import_invoked") is not False):
        reasons.append("migration identity or scope is incorrect")
    for check_name in ("flyway_v2_populated_upgrade", "flyway_v3_runtime_grants",
            "populated_upgrade_preserves_imported_rows"):
        if checks.get(check_name, {}).get("passed") is not True:
            reasons.append(check_name + " failed")
    required_cleanup = ("compose_down", "resource_check_passed", "peer_probe_removed",
        "jndi_probe_removed", "work_removed", "image_removed")
    if any(cleanup.get(key) is not True for key in required_cleanup):
        reasons.append("owned fixture cleanup is incomplete")
    if cleanup.get("secrets_preserved") is not False or any(cleanup.get(key) for key in
            ("residual_containers", "residual_networks", "residual_volumes")):
        reasons.append("owned resources or generated secrets remain")
    desired = json.loads((ROOT / "tests/security/desired-cases.json").read_text())
    case_specs = [(f"BG-06::{actor}::active", actor, "deny")
        for actor in ("anonymous", "Reader", "Operator", "Administrator")]
    desired_rows = {row.get("id"): row for row in desired.get("cases", [])}
    for case_id, actor, expected in case_specs:
        canonical = desired_rows.get(case_id)
        if (canonical is None or canonical.get("surface_id") != "BG-06"
                or canonical.get("actor") != actor or canonical.get("expected") != expected
                or canonical.get("write") is not True
                or canonical.get("requires_trusted_worker_driver") is not True
                or canonical.get("path") is not None or canonical.get("method") != "GET"
                or canonical.get("source") != HUMAN_CONTRACT_SOURCE):
            reasons.append("canonical human BG-06 case is missing or has changed: " + case_id)
    machine_case_id = "BG-06-MACHINE::deployment-migration::active"
    canonical_machine = desired_rows.get(machine_case_id)
    if (canonical_machine is None or canonical_machine.get("surface_id") != "BG-06-MACHINE"
            or canonical_machine.get("actor") != "deployment-migration"
            or canonical_machine.get("expected") != "allow"
            or canonical_machine.get("write") is not True
            or canonical_machine.get("requires_isolated_worker_fixture") is not True
            or canonical_machine.get("required_machine_scope") != CANONICAL_MACHINE_SCOPE
            or canonical_machine.get("path") is not None or canonical_machine.get("method") != "GET"
            or canonical_machine.get("source") != MACHINE_CONTRACT_SOURCE):
        reasons.append("canonical BG-06 machine migration case is missing or has changed")
    cases = [
        {"case": "CURRENT::" + case_id, "surface_id": "BG-06", "actor": actor,
         "contract_expected": expected, "outcome": "PASS" if actor_rows.get(actor, {}).get("passed") is True else "BLOCKED"}
        for case_id, actor, expected in case_specs
    ]
    machine_outcome = "PASS" if machine.get("passed") is True else "BLOCKED"
    cases.append({"case": "CURRENT::" + machine_case_id,
        "surface_id": "BG-06-MACHINE", "actor": "deployment-migration",
        "contract_expected": "allow", "outcome": machine_outcome})
    if reasons:
        cases = [{**row, "outcome": "BLOCKED"} for row in cases]
    summary = {"total": len(cases), "passed": sum(row["outcome"] == "PASS" for row in cases),
        "blocked": sum(row["outcome"] == "BLOCKED" for row in cases)}
    evidence = {"run_id": report.get("run_id"), "runtime_status": report.get("status"),
        "checks": {"bg06_static_source_inventory": checks.get("bg06_static_source_inventory"),
            "bg06_human_boundary": human, "bg06_machine_boundary": machine,
            "application_ddl_denied": ddl,
            "startup_no_orm_ddl_or_seed": checks.get("startup_no_orm_ddl_or_seed"),
            "restart_preserves_data": checks.get("restart_preserves_data"),
            "peer_network_listener_reachability": listeners,
            "remote_jndi_jms_protocol_authentication": protocol,
            "migration_machine_identity": migration,
            "flyway_v2_populated_upgrade": checks.get("flyway_v2_populated_upgrade"),
            "flyway_v3_runtime_grants": checks.get("flyway_v3_runtime_grants"),
            "populated_upgrade_preserves_imported_rows": checks.get("populated_upgrade_preserves_imported_rows")},
        "source_sha256": source_hashes, "schema_sha256": schema_hashes, "cleanup": cleanup}
    return cases, reasons, {"summary": summary, "evidence": evidence}


def main() -> int:
    started_ns = time.time_ns()
    started_at = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([sys.executable, str(RUNTIME)], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=2400)
    report = {}
    if RAW.is_file() and RAW.stat().st_mtime_ns >= started_ns:
        try:
            report = json.loads(RAW.read_text())
        except (OSError, json.JSONDecodeError):
            report = {}
    try:
        cases, reasons, validation = validate(report) if report else ([], ["no fresh parseable runtime receipt"], {"summary": {"total": 5, "passed": 0, "blocked": 5}, "evidence": {}})
    except Exception as error:
        cases = [{"case": "CURRENT::BG-06::"+actor+"::active", "surface_id": "BG-06",
            "actor": actor, "contract_expected": "deny", "outcome": "BLOCKED"}
            for actor in ("anonymous", "Reader", "Operator", "Administrator")]
        cases.append({"case": "CURRENT::BG-06-MACHINE::deployment-migration::active",
            "surface_id": "BG-06-MACHINE", "actor": "deployment-migration",
            "contract_expected": "allow", "outcome": "BLOCKED"})
        reasons = ["strict adapter rejected malformed receipt (" + type(error).__name__ + ")"]
        validation = {"summary": {"total": 5, "passed": 0, "blocked": 5}, "evidence": {}}
    if result.returncode != 0:
        reasons.append("fresh disposable runtime process exited " + str(result.returncode))
        cases = [{**row, "outcome": "BLOCKED"} for row in cases]
    validation["summary"] = {"total": len(cases),
        "passed": sum(row["outcome"] == "PASS" for row in cases),
        "blocked": sum(row["outcome"] == "BLOCKED" for row in cases)}
    gate_passed = result.returncode == 0 and not reasons and len(cases) == 5
    output = {"schema_version": 1, "task": "KAN-15 BG-06", "driver": "fresh-disposable-bg06-scoped-gate-v1",
        "started_at_utc": started_at, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "outcome": "PASS" if gate_passed else "BLOCKED", "gate_exit": 0 if gate_passed else 2,
        "cases": cases, "summary": validation["summary"], "reasons": reasons,
        "runtime_receipt_sha256": digest(RAW) if RAW.is_file() else None,
        "gate_adapter_sha256": digest(Path(__file__)),
        "runtime_exit_code": result.returncode,
        "evidence": validation["evidence"]}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"outcome": output["outcome"], "summary": output["summary"], "gate_exit": output["gate_exit"]}))
    return output["gate_exit"]


if __name__ == "__main__":
    raise SystemExit(main())
