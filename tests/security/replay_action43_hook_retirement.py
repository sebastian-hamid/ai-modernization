#!/usr/bin/env python3
"""Offline, hash-pinned replay of the user-approved ACTION-43 hook retirement."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

from current_capabilities import ROOT, load_model, reviewed_action43_hook_retirement_receipt
from contracts import exit_code

INPUT = ROOT / "notes/evidence/kan-15-handling-page-retirement/current-capability-replay.json"
OUTPUT = ROOT / "notes/evidence/kan-15-action43-hook/current-capability-replay.json"
INPUT_SHA256 = "4a315add4cecd70b2967a71c8dbf24e269e8b71fa8f6ce2e5f990e695bdabbb9"
CURRENT_GATE = ROOT / "notes/evidence/kan-15-handling-page-retirement/current-capability-gate.json"
CURRENT_GATE_SHA256 = "96c59c67f207af4cd5d6fb8364e4a7a3471c1fac339abe0534737ca36f72a74e"
ACTORS = ("anonymous", "Reader", "Operator", "Administrator")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replay(output_path=OUTPUT):
    if not reviewed_action43_hook_retirement_receipt():
        raise ValueError("ACTION-43 proof, independent review, or user retirement decision is invalid")
    model, _ = load_model()
    status = {row["legacy_id"]: row["status"] for row in model["retirement_candidates"]}
    if status.get("ACTION-43") != "retired":
        raise ValueError("ACTION-43 is not retired in the reviewed mapping")

    raw = INPUT.read_bytes()
    if sha(raw) != INPUT_SHA256:
        raise ValueError("Prior reviewed current-capability replay changed")
    prior = json.loads(raw)
    gate_raw = CURRENT_GATE.read_bytes()
    if sha(gate_raw) != CURRENT_GATE_SHA256 or prior.get("source_evidence_sha256") != CURRENT_GATE_SHA256:
        raise ValueError("Hash-pinned fresh current-capability source changed or is not the replay basis")
    gate = json.loads(gate_raw)
    current_results = gate.get("current_results", [])
    current_case_ids = [row.get("case") for row in current_results]
    if (gate.get("current_counts") != {"PASS": 470} or len(current_results) != 470
            or len(set(current_case_ids)) != 470 or any(row.get("outcome") != "PASS" for row in current_results)):
        raise ValueError("Fresh current-capability source does not contain exactly 470 unique PASS rows")
    if (prior.get("current_counts") != {"PASS": 470}
            or prior.get("retirement_counts_after_review") != {"RETIRED": 72, "BLOCKED": 4}
            or prior.get("gate_exit") != 2):
        raise ValueError("Prior effective gate does not match the reviewed ACTION-35/40 replay")

    rows = [dict(row) for row in prior["retirement_results"]]
    selected = {f"RETIREMENT::ACTION-43::{actor}" for actor in ACTORS}
    matches = [row for row in rows if row.get("case") in selected]
    if (len(matches) != 4 or {row.get("case") for row in matches} != selected
            or any(row.get("outcome") != "BLOCKED" for row in matches)):
        raise ValueError("Prior replay does not contain exactly four blocked ACTION-43 rows")

    for row in rows:
        if row.get("case") in selected:
            row.update(outcome="RETIRED", specific_negative_entry_verified=True,
                       independent_review_verified=True,
                       review_record="notes/agent-reviews/2026-11-17-kan15-action43-hook-review.md",
                       user_decision="notes/decisions/2026-11-17-action43-retirement.md",
                       outcome_note="Approved retirement of the old page hook only; RETIRED is never PASS")

    counts = dict(Counter(row["outcome"] for row in rows))
    if counts != {"RETIRED": 76}:
        raise ValueError("Unexpected retirement result counts after ACTION-43 replay")
    for row in rows:
        if row.get("case") not in selected:
            source = next((item for item in prior["retirement_results"] if item["case"] == row["case"]), None)
            if row != source:
                raise ValueError("Replay changed a retirement row outside ACTION-43")

    effective_results = current_results + rows
    gate_exit = exit_code(effective_results)
    if gate_exit != 0:
        raise ValueError("Effective current/retirement slice still contains blocked, failed, or errored cases")
    result = {
        "task": "KAN-15 ACTION-43 hook retirement replay",
        "basis": "Offline replay of user-approved, independently reviewed hook proof against retained fresh runtime/browser evidence; no fixture launched.",
        "source_replay": str(INPUT.relative_to(ROOT)),
        "source_replay_sha256": sha(raw),
        "hook_validation": "notes/evidence/kan-15-action43-hook/validation.json",
        "hook_validation_sha256": sha((ROOT / "notes/evidence/kan-15-action43-hook/validation.json").read_bytes()),
        "review_record": "notes/agent-reviews/2026-11-17-kan15-action43-hook-review.md",
        "review_record_sha256": sha((ROOT / "notes/agent-reviews/2026-11-17-kan15-action43-hook-review.md").read_bytes()),
        "user_decision": "notes/decisions/2026-11-17-action43-retirement.md",
        "user_decision_sha256": sha((ROOT / "notes/decisions/2026-11-17-action43-retirement.md").read_bytes()),
        "inputs_fingerprint_from_fresh_run": prior.get("inputs_fingerprint_from_fresh_run"),
        "current_counts": prior["current_counts"],
        "current_capability_source": str(CURRENT_GATE.relative_to(ROOT)),
        "current_capability_source_sha256": sha(gate_raw),
        "current_results": current_results,
        "retirement_counts_before_action43": prior["retirement_counts_after_review"],
        "retirement_counts_after_action43": counts,
        "changed_cases": sorted(selected),
        "retirement_results": rows,
        "legacy_audit": prior["legacy_audit"],
        "effective_current_retirement_gate_exit": gate_exit,
        "historical_audit_counts": prior["legacy_audit"]["counts"],
        "historical_audit_exit": exit_code(prior["legacy_audit"]["results"]),
        "limitations": [
            "No new runtime/browser fixture was launched; existing fresh evidence and decision/review artifacts are hash-pinned.",
            "Only the four ACTION-43 actor rows changed. Current capability outcomes, all other retirement rows, and the historical audit are preserved.",
            "The old HolderBean.initFlow method and flow resources remain. This classifies only the legacy page hook as RETIRED; RETIRED is never PASS.",
            "The preserved historical audit remains incomplete and is reported separately; no production verification is claimed."
        ]
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    final = replay()
    print(json.dumps({"current": final["current_counts"],
                      "retirement": final["retirement_counts_after_action43"],
                      "effective_gate_exit": final["effective_current_retirement_gate_exit"],
                      "historical_audit_exit": final["historical_audit_exit"]}, indent=2))