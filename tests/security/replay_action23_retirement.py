#!/usr/bin/env python3
"""Replay independent ACTION-23 retirement approval against retained fresh evidence."""
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
from current_capabilities import ROOT,load_model,reviewed_action23_retirement_receipt
DEFAULT_INPUT=ROOT/"notes/evidence/kan-15-action23-retirement/candidate-evidence.json"
DEFAULT_OUTPUT=ROOT/"notes/evidence/kan-15-action23-retirement/current-capability-replay.json"
def sha(data):return hashlib.sha256(data).hexdigest()
def replay(input_path=DEFAULT_INPUT,output_path=DEFAULT_OUTPUT):
    model,_=load_model()
    if not reviewed_action23_retirement_receipt():raise ValueError("ACTION-23 independent evidence receipt is invalid")
    evidence_bytes=input_path.read_bytes()
    evidence=json.loads(evidence_bytes)
    if sha(evidence_bytes)!=__import__("current_capabilities").ACTION23_FRESH_EVIDENCE_SHA256:
        raise ValueError("Fresh candidate evidence changed after review")
    if evidence.get("current_counts")!={"PASS":470} or evidence.get("gate_exit")!=2:
        raise ValueError("Retained current gate evidence is not the reviewed fresh 470 PASS run")
    statuses={row["legacy_id"]:row["status"] for row in model["retirement_candidates"]}
    if statuses.get("ACTION-23")!="retired":raise ValueError("ACTION-23 is not approved as retired in the current mapping")
    results=[dict(row) for row in evidence.get("retirement_results",[])]
    action23=[row for row in results if row.get("case","").startswith("RETIREMENT::ACTION-23::")]
    if len(action23)!=4 or any(row.get("outcome")!="BLOCKED" or row.get("specific_negative_entry_verified") is not True for row in action23):
        raise ValueError("Source evidence does not contain exactly four validated pending ACTION-23 rows")
    for row in action23:
        row.update(outcome="RETIRED",independent_review_verified=True,
            review_record="notes/agent-reviews/2026-11-15-kan15-action23-retirement-review.md",
            outcome_note="Approved retired entry; RETIRED is never PASS")
    counts=dict(Counter(row["outcome"] for row in results))
    if counts!={"RETIRED":8,"BLOCKED":68}:raise ValueError("Unexpected retirement replay counts")
    result={"task":"KAN-15 ACTION-23 retirement review replay",
      "basis":"Offline replay of independent review against retained fresh owned-runtime evidence; no runtime or browser fixture launched.",
      "source_evidence":str(input_path.relative_to(ROOT)),"source_evidence_sha256":sha(evidence_bytes),
      "validation_receipt_sha256":sha(__import__("current_capabilities").ACTION23_RETIREMENT_VALIDATION.read_bytes()),
      "review_record":"notes/agent-reviews/2026-11-15-kan15-action23-retirement-review.md",
      "review_record_sha256":sha(__import__("current_capabilities").ACTION23_RETIREMENT_REVIEW.read_bytes()),
      "inputs_fingerprint_from_fresh_run":evidence.get("provenance",{}).get("inputs_fingerprint"),
      "current_counts":evidence["current_counts"],"retirement_counts_before_review":evidence["retirement_counts"],
      "retirement_counts_after_review":counts,"changed_cases":[row["case"] for row in action23],
      "retirement_results":results,"legacy_audit":evidence["legacy_audit"],
      "gate_exit":2,"remaining_blocked_retirement_cases":68,
      "limitations":["The fresh live run is not repeated; exact evidence and review bytes are SHA-256 pinned.","RETIRED is not PASS.","ACTION-44 remains BLOCKED and is not conflated with ACTION-23."]}
    output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(json.dumps(result,indent=2)+"\n")
    return result
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--input",type=Path,default=DEFAULT_INPUT);parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT);args=parser.parse_args()
    result=replay(args.input,args.output)
    print(json.dumps({k:result[k] for k in ("current_counts","retirement_counts_after_review","gate_exit")}))
