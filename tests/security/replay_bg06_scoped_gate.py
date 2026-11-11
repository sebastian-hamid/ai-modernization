#!/usr/bin/env python3
"""Replay the five reviewed BG-06 proofs into a supplemental current-gate view."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_GATE = ROOT / "notes/evidence/kan-15-bg02-filesystem-boundary/current-capability-gate.json"
SCOPE_RECEIPT = ROOT / "notes/evidence/kan-15-bg06-scope/validation.json"
ADAPTER = ROOT / "tests/security/run_bg06_scoped_gate.py"
DESIRED = ROOT / "tests/security/desired-cases.json"
OUTPUT = ROOT / "notes/evidence/kan-15-bg06-scope/current-capability-replay.json"
REVIEW_RECORD = ROOT / "notes/agent-reviews/2026-11-11-kan15-bg06-scope-review.md"
REVIEWED_BASE_GATE_SHA256 = "e8b0119a7e40a2d8af4c854aec084754d2b47aee94d291ab31e7e8f424981622"
REVIEWED_SCOPE_SHA256 = "1563504790c838d8c43fed9128dbc5356b8a9fcb8bbc3714e11525c016a0df13"
REVIEWED_RAW_RECEIPT_SHA256 = "e310e0fab53caad06d8072934865746dd12b15360700d3565f7164cd4da54f9b"
REVIEWED_ADAPTER_SHA256 = "ea70c54464939615712bd256fe820741b7f724d865be15d13db16e98f547048c"
REVIEW_RECORD_SHA256 = "82f14eb0028a6ed5fe8cc36a866d46d12106abc11c4ef3ff8432d6bc1153bf89"
ACTORS = ("anonymous", "Reader", "Operator", "Administrator")
HUMAN_SOURCE = ("No human-triggerable reseed or schema-DDL entry point; startup-only sample "
    "generator and ORM schema action must remain disabled")
MACHINE_SOURCE = ("Flyway deployment migrations using schema_migrator; startup sample seeding "
    "and ORM schema generation remain disabled")
MACHINE_SCOPE = "Flyway schema migration with server-verified schema_migrator identity"
SCHEMA_FILES = {
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha256(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def outcome_counts(rows: list[dict]) -> dict[str, int]:
    return dict(Counter(row["outcome"] for row in rows))


def apply_promotions(current_rows: list[dict], promotions: dict[str, str]) -> list[dict]:
    ids = [row.get("case") for row in current_rows]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("baseline current result IDs are missing or duplicated")
    if set(promotions) != {f"CURRENT::BG-06::{actor}::active" for actor in ACTORS} | {
            "CURRENT::BG-06-MACHINE::deployment-migration::active"}:
        raise ValueError("promotion set must contain exactly the five canonical BG-06 cases")
    rows = []
    found = set()
    for original in current_rows:
        row = dict(original)
        case_id = row["case"]
        if case_id in promotions:
            if row.get("outcome") != "BLOCKED" or promotions[case_id] != "PASS":
                raise ValueError("only a previously BLOCKED BG-06 row may be promoted to PASS")
            row["outcome"] = "PASS"
            row["reason"] = "Promoted by independently reviewed fresh scoped BG-06 evidence"
            found.add(case_id)
        rows.append(row)
    if found != set(promotions):
        raise ValueError("baseline does not contain every exact BG-06 promotion case")
    return rows


def require_source_hashes(hashes: dict, label: str) -> None:
    if not hashes:
        raise ValueError(label + " fingerprints are missing")
    for name, expected in hashes.items():
        path = ROOT / name
        if not path.is_file() or file_sha256(path) != expected:
            raise ValueError(label + " fingerprint mismatch: " + name)


def validate_scope(scope: dict, desired: dict, scope_bytes: bytes) -> dict[str, str]:
    if hashlib.sha256(scope_bytes).hexdigest() != REVIEWED_SCOPE_SHA256:
        raise ValueError("scoped receipt digest differs from the independently reviewed artifact")
    if file_sha256(REVIEW_RECORD) != REVIEW_RECORD_SHA256:
        raise ValueError("independent BG-06 review record differs from its reviewed revision")
    if (scope.get("schema_version") != 1 or scope.get("task") != "KAN-15 BG-06"
            or scope.get("driver") != "fresh-disposable-bg06-scoped-gate-v1"
            or scope.get("outcome") != "PASS" or scope.get("gate_exit") != 0):
        raise ValueError("scoped BG-06 receipt is not PASS")
    cases = scope.get("cases", [])
    expected = {f"CURRENT::BG-06::{actor}::active": ("BG-06", actor, "deny") for actor in ACTORS}
    expected["CURRENT::BG-06-MACHINE::deployment-migration::active"] = (
        "BG-06-MACHINE", "deployment-migration", "allow")
    if len(cases) != 5 or {row.get("case") for row in cases} != set(expected):
        raise ValueError("scoped receipt does not contain the exact five BG-06 case IDs")
    if any(row.get("outcome") != "PASS" for row in cases):
        raise ValueError("one or more scoped BG-06 cases did not pass")
    if scope.get("summary") != {"total": 5, "passed": 5, "blocked": 0} or scope.get("reasons"):
        raise ValueError("scoped receipt summary or validation reasons are inconsistent")

    desired_rows = {row.get("id"): row for row in desired.get("cases", [])}
    for case_id, (surface, actor, outcome) in expected.items():
        row = next(item for item in cases if item.get("case") == case_id)
        prefix = "CURRENT::"
        canonical = desired_rows.get(case_id.removeprefix(prefix))
        if (row.get("surface_id") != surface or row.get("actor") != actor
                or row.get("contract_expected") != outcome or canonical is None
                or canonical.get("surface_id") != surface or canonical.get("actor") != actor
                or canonical.get("expected") != outcome or canonical.get("write") is not True
                or canonical.get("path") is not None or canonical.get("method") != "GET"):
            raise ValueError("scoped or canonical BG-06 case contract mismatch: " + case_id)
        if surface == "BG-06":
            if (canonical.get("source") != HUMAN_SOURCE
                    or canonical.get("requires_trusted_worker_driver") is not True):
                raise ValueError("canonical human BG-06 contract fields changed: " + case_id)
        elif (canonical.get("source") != MACHINE_SOURCE
                or canonical.get("required_machine_scope") != MACHINE_SCOPE
                or canonical.get("requires_isolated_worker_fixture") is not True):
            raise ValueError("canonical BG-06 machine contract fields changed")

    evidence = scope.get("evidence", {})
    checks = evidence.get("checks", {})
    required_pass_checks = (
        "bg06_static_source_inventory", "bg06_human_boundary", "bg06_machine_boundary",
        "application_ddl_denied", "startup_no_orm_ddl_or_seed", "restart_preserves_data",
        "peer_network_listener_reachability", "remote_jndi_jms_protocol_authentication",
        "migration_machine_identity", "flyway_v2_populated_upgrade", "flyway_v3_runtime_grants",
        "populated_upgrade_preserves_imported_rows")
    if any(checks.get(name, {}).get("passed") is not True for name in required_pass_checks):
        raise ValueError("one or more BG-06 runtime evidence checks are absent or failed")
    humans = checks["bg06_human_boundary"].get("actors", {})
    if checks["bg06_human_boundary"].get("driver") != "bg06-fresh-role-aware-no-callable-surface-v1":
        raise ValueError("human boundary proof driver is unexpected")
    if set(humans) != set(ACTORS):
        raise ValueError("human actor evidence is incomplete")
    expected_principals = {"Reader": "reader", "Operator": "operator", "Administrator": "admin"}
    for actor in ACTORS:
        item = humans[actor]
        if (item.get("passed") is not True or item.get("expected") != "deny"
                or item.get("no_callable_seed_or_schema_entrypoint") is not True
                or item.get("database_effects_unchanged") is not True
                or item.get("application_database_ddl_denied") is not True):
            raise ValueError("human denial/effect evidence failed: " + actor)
        identity = item.get("identity")
        entry = item.get("entrypoint_evidence", {})
        if actor == "anonymous":
            if (identity is not None or entry.get("application_api_status") not in (302, 401)
                    or entry.get("remote_jndi_authentication_denied") is not True
                    or entry.get("remote_exported_namespace_access_denied") is not True):
                raise ValueError("anonymous denial identity/entrypoint evidence is incomplete")
        elif (identity.get("server_verified") is not True
                or identity.get("principal") != expected_principals[actor]
                or identity.get("roles") != [actor]
                or entry.get("remote_exported_leaf_names") != ["jms/RemoteConnectionFactory"]
                or entry.get("remote_seed_generator_binding_absent") is not True
                or entry.get("remote_connection_started") is not True):
            raise ValueError("authenticated actor identity/naming evidence is incorrect: " + actor)
    ddl = checks["application_ddl_denied"]
    if (ddl.get("driver") != "direct-postgresql-session-v1"
            or ddl.get("native_identity", {}).get("server_verified") is not True
            or ddl.get("native_identity", {}).get("principal") != "cargo_app"
            or ddl.get("database_effects_unchanged") is not True
            or set(ddl.get("attempts", {})) != {"persistent_schema_ddl", "temporary_table_ddl",
                "flyway_history_update", "migration_state_update"}
            or any(row.get("denied") is not True for row in ddl.get("attempts", {}).values())):
        raise ValueError("application-role DDL denial/unchanged-effect evidence is incomplete")
    if checks["startup_no_orm_ddl_or_seed"].get("marker_preserved") is not True:
        raise ValueError("startup marker was not preserved")
    machine = checks["migration_machine_identity"]
    identity = machine.get("native_identity", {})
    if (checks["bg06_machine_boundary"].get("driver") != "bg06-fresh-schema-migration-scope-v1"
            or identity.get("server_verified") is not True or identity.get("principal") != "schema_migrator"
            or identity.get("session_user") != "schema_migrator"
            or identity.get("current_user") != "schema_migrator"
            or identity.get("current_role") != "schema_migrator"
            or machine.get("migrations_only") is not True
            or machine.get("flyway_installed_by") != ["schema_migrator"] * 3
            or machine.get("sample_data_generator_invoked") is not False
            or machine.get("controlled_import_invoked") is not False):
        raise ValueError("migration identity/scope evidence is incomplete")
    protocol = checks["remote_jndi_jms_protocol_authentication"]
    if protocol.get("sends_performed") != 0 or protocol.get("consumers_created") != 0:
        raise ValueError("scope receipt unexpectedly includes JMS send/consume activity")
    cleanup = evidence.get("cleanup", {})
    for key in ("compose_down", "resource_check_passed", "peer_probe_removed", "jndi_probe_removed",
                "work_removed", "image_removed"):
        if cleanup.get(key) is not True:
            raise ValueError("fixture cleanup evidence failed: " + key)
    if (cleanup.get("secrets_preserved") is not False
            or any(cleanup.get(key) for key in ("residual_containers", "residual_networks", "residual_volumes"))):
        raise ValueError("fixture resources or generated secrets remain")

    source_hashes = evidence.get("source_sha256", {})
    schema_hashes = evidence.get("schema_sha256", {})
    require_source_hashes(source_hashes, "BG-06 source")
    require_source_hashes(schema_hashes, "BG-06 schema/fixture")
    if set(schema_hashes) != SCHEMA_FILES:
        raise ValueError("BG-06 schema/fixture fingerprint set differs from the reviewed 14 files")
    webapp_root = ROOT / "candidate/cargotracker/src/main/webapp"
    actual_webapp = {path.relative_to(ROOT).as_posix() for path in webapp_root.rglob("*") if path.is_file()}
    pinned_webapp = {name for name in source_hashes if name.startswith("candidate/cargotracker/src/main/webapp/")}
    if actual_webapp != pinned_webapp:
        raise ValueError("BG-06 deployed webapp source set differs from the scoped receipt")
    if file_sha256(ADAPTER) != REVIEWED_ADAPTER_SHA256 or scope.get("gate_adapter_sha256") != REVIEWED_ADAPTER_SHA256:
        raise ValueError("scoped gate adapter differs from the reviewed receipt")
    raw_sha = scope.get("runtime_receipt_sha256")
    if raw_sha != REVIEWED_RAW_RECEIPT_SHA256:
        raise ValueError("scoped receipt raw runtime digest differs from independent review")
    return {case_id: "PASS" for case_id in expected}


def build_replay(gate: dict, scope: dict, desired: dict, gate_bytes: bytes, scope_bytes: bytes) -> dict:
    if hashlib.sha256(gate_bytes).hexdigest() != REVIEWED_BASE_GATE_SHA256:
        raise ValueError("source current-capability gate differs from the reviewed aggregate checkpoint")
    if gate.get("execution") != "fresh-owned-runtime":
        raise ValueError("source gate is not a completed fresh-owned-runtime aggregate")
    current = gate.get("current_results", [])
    retirement = gate.get("retirement_results", [])
    legacy = gate.get("legacy_audit", {})
    if len(current) != 470 or len(retirement) != 76:
        raise ValueError("source aggregate case inventories differ from the reviewed checkpoint")
    if outcome_counts(current) != gate.get("current_counts"):
        raise ValueError("source current counts do not match its result rows")
    if outcome_counts(retirement) != gate.get("retirement_counts"):
        raise ValueError("source retirement counts do not match its result rows")
    if outcome_counts(legacy.get("results", [])) != legacy.get("counts"):
        raise ValueError("source legacy counts do not match its result rows")
    promotions = validate_scope(scope, desired, scope_bytes)
    replayed = apply_promotions(current, promotions)
    untouched_before = [row for row in current if row.get("case") not in promotions]
    untouched_after = [row for row in replayed if row.get("case") not in promotions]
    if untouched_before != untouched_after:
        raise ValueError("offline BG-06 replay changed a non-BG-06 current result")
    return {
        "schema_version": 1,
        "task": "KAN-15 BG-06 supplemental aggregate replay",
        "basis": "Offline replay of the independently reviewed fresh BG-06 scoped receipt; no new runtime or browser fixture was launched.",
        "source_gate_sha256": hashlib.sha256(gate_bytes).hexdigest(),
        "source_scoped_receipt_sha256": hashlib.sha256(scope_bytes).hexdigest(),
        "source_gate_fingerprint": gate.get("provenance", {}).get("inputs_fingerprint"),
        "source_scope_run_id": scope.get("evidence", {}).get("run_id"),
        "source_runtime_receipt_sha256": scope.get("runtime_receipt_sha256"),
        "source_gate_adapter_sha256": scope.get("gate_adapter_sha256"),
        "scope": "Exactly four human BG-06 seed/reseed/schema-DDL denials and BG-06-MACHINE Flyway migration identity.",
        "promoted_cases": [{"case": case_id, "previous": "BLOCKED", "replayed": "PASS"}
            for case_id in promotions],
        "previous_current_counts": gate["current_counts"],
        "replayed_current_counts": outcome_counts(replayed),
        "untouched_current_results_sha256": object_sha256(untouched_after),
        "legacy_counts_preserved": legacy["counts"],
        "legacy_results_sha256": object_sha256(legacy["results"]),
        "retirement_counts_preserved": gate["retirement_counts"],
        "retirement_results_sha256": object_sha256(retirement),
        "gate_exit": 2,
        "limitations": [
            "This supplemental replay does not alter the source gate or claim a new aggregate runtime run.",
            "All non-BG-06 current results, the historical audit, and all retirement results are preserved unchanged.",
            "The JMS evidence is connect/list-only and does not establish destination-level send/consume authorization.",
            "This evidence does not close full KAN-15.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, default=BASE_GATE)
    parser.add_argument("--scope", type=Path, default=SCOPE_RECEIPT)
    parser.add_argument("--desired", type=Path, default=DESIRED)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    gate_bytes = args.gate.read_bytes()
    scope_bytes = args.scope.read_bytes()
    gate = json.loads(gate_bytes)
    scope = json.loads(scope_bytes)
    desired = json.loads(args.desired.read_text())
    replay = build_replay(gate, scope, desired, gate_bytes, scope_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(replay, indent=2) + "\n")
    print(json.dumps({"previous": replay["previous_current_counts"],
        "replayed": replay["replayed_current_counts"], "gate_exit": replay["gate_exit"],
        "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
