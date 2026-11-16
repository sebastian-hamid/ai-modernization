#!/usr/bin/env python3
"""Replay independent ACTION-27/30/34 mapping approval against retained evidence."""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from current_capabilities import (
    ROOT,load_model,reviewed_action273034_retirement_receipt,
    ACTION273034_CANDIDATE_EVIDENCE_SHA256,ACTION273034_PROMOTION_VALIDATION,
)
DEFAULT_INPUT=ROOT/"notes/evidence/kan-15-action273034-retirement/candidate-evidence.json"
DEFAULT_OUTPUT=ROOT/"notes/evidence/kan-15-action273034-retirement/current-capability-replay.json"
ACTIONS=("ACTION-27","ACTION-30","ACTION-34")
def sha(data):return hashlib.sha256(data).hexdigest()
def replay(input_path=DEFAULT_INPUT,output_path=DEFAULT_OUTPUT):
    model,_=load_model()
    if not reviewed_action273034_retirement_receipt():raise ValueError("ACTION-27/30/34 mapping promotion receipt is invalid")
    evidence_bytes=input_path.read_bytes();evidence=json.loads(evidence_bytes)
    if sha(evidence_bytes)!=ACTION273034_CANDIDATE_EVIDENCE_SHA256:raise ValueError("Fresh candidate evidence changed after review")
    if evidence.get("current_counts")!={"PASS":470} or evidence.get("gate_exit")!=2:raise ValueError("Fresh current-capability result differs from reviewed run")
    statuses={row["legacy_id"]:row["status"] for row in model["retirement_candidates"]}
    if any(statuses.get(action)!="retired" for action in ACTIONS):raise ValueError("Approved mapping actions are not all retired")
    results=[dict(row) for row in evidence.get("retirement_results",[])]
    rows=[row for row in results if any(row.get("case","").startswith("RETIREMENT::"+action+"::") for action in ACTIONS)]
    if len(rows)!=12 or any(row.get("outcome")!="BLOCKED" or row.get("specific_negative_entry_verified") is not True for row in rows):
        raise ValueError("Fresh evidence does not contain exactly twelve validated pending promotion rows")
    review_path=ROOT/"notes/agent-reviews/2026-11-16-kan15-actions273034-mapping-promotion-review.md"
    for row in rows:
        row.update(outcome="RETIRED",independent_review_verified=True,
            review_record=str(review_path.relative_to(ROOT)),outcome_note="Approved retired entry; RETIRED is never PASS")
    counts=dict(Counter(row["outcome"] for row in results))
    if counts!={"RETIRED":32,"BLOCKED":44}:raise ValueError("Unexpected replay retirement counts")
    result={
      "task":"KAN-15 ACTION-27/30/34 mapping promotion replay",
      "basis":"Offline replay of independent mapping approval against fresh owned-runtime evidence; no runtime or browser fixture launched.",
      "source_evidence":str(input_path.relative_to(ROOT)),
      "source_evidence_sha256":sha(evidence_bytes),
      "promotion_validation_sha256":sha(ACTION273034_PROMOTION_VALIDATION.read_bytes()),
      "review_record":str(review_path.relative_to(ROOT)),
      "review_record_sha256":sha(review_path.read_bytes()),
      "inputs_fingerprint_from_fresh_run":evidence.get("provenance",{}).get("inputs_fingerprint"),
      "current_counts":evidence["current_counts"],
      "retirement_counts_before_review":evidence["retirement_counts"],
      "retirement_counts_after_review":counts,
      "changed_cases":[row["case"] for row in rows],
      "retirement_results":results,
      "legacy_audit":evidence["legacy_audit"],
      "gate_exit":2,
      "remaining_blocked_retirement_cases":44,
      "limitations":[
        "The fresh live run is not repeated; candidate evidence, browser results and independent review are hash-pinned.",
        "Persisted effects and payload observations are validated assertions; raw before/after snapshots and HTTP bodies are not retained.",
        "RETIRED is not PASS; only ACTION-27, ACTION-30 and ACTION-34 rows change."
      ]
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2)+"\n")
    return result
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--input",type=Path,default=DEFAULT_INPUT);parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args();result=replay(args.input,args.output)
    print(json.dumps({key:result[key] for key in ("current_counts","retirement_counts_after_review","gate_exit")}))
