#!/usr/bin/env python3
"""Replay reviewed handling callback retirement promotion against pinned evidence."""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from current_capabilities import (
    ROOT,load_model,reviewed_handling_callback_retirement_receipt,
    HANDLING_CALLBACK_GATE_EVIDENCE,HANDLING_CALLBACK_GATE_SHA256,
    HANDLING_CALLBACK_PROMOTION_VALIDATION,HANDLING_CALLBACK_PROMOTION_VALIDATION_SHA256,
    HANDLING_CALLBACK_PROMOTION_REVIEW,HANDLING_CALLBACK_PROMOTION_REVIEW_SHA256,
    HANDLING_CALLBACK_RETIREMENT_ACTIONS,ACTORS,
)
DEFAULT_OUTPUT=ROOT/"notes/evidence/kan-15-handling-callback-retirement/current-capability-replay.json"
def sha(data):return hashlib.sha256(data).hexdigest()
def replay(output_path=DEFAULT_OUTPUT):
    model,_=load_model()
    if not reviewed_handling_callback_retirement_receipt():raise ValueError("Handling callback promotion receipt is invalid")
    raw=HANDLING_CALLBACK_GATE_EVIDENCE.read_bytes();evidence=json.loads(raw)
    if sha(raw)!=HANDLING_CALLBACK_GATE_SHA256:raise ValueError("Fresh gate evidence changed after review")
    validation=HANDLING_CALLBACK_PROMOTION_VALIDATION.read_bytes();review=HANDLING_CALLBACK_PROMOTION_REVIEW.read_bytes()
    if sha(validation)!=HANDLING_CALLBACK_PROMOTION_VALIDATION_SHA256 or sha(review)!=HANDLING_CALLBACK_PROMOTION_REVIEW_SHA256:
        raise ValueError("Promotion decision evidence changed after review")
    if evidence.get("current_counts")!={"PASS":470} or evidence.get("retirement_counts")!={"RETIRED":44,"BLOCKED":32} or evidence.get("gate_exit")!=2:
        raise ValueError("Fresh current-capability result differs from reviewed run")
    statuses={row["legacy_id"]:row["status"] for row in model["retirement_candidates"]}
    actions=list(HANDLING_CALLBACK_RETIREMENT_ACTIONS)
    if any(statuses.get(action)!="retired" for action in actions):raise ValueError("Approved callback actions are not all retired")
    results=[dict(row) for row in evidence.get("retirement_results",[])]
    selected={"RETIREMENT::"+action+"::"+actor for action in actions for actor in ACTORS}
    rows=[row for row in results if row.get("case") in selected]
    if len(rows)!=20 or {row.get("case") for row in rows}!=selected or any(row.get("outcome")!="BLOCKED" or row.get("specific_negative_entry_verified") is not True for row in rows):
        raise ValueError("Fresh evidence does not contain exactly twenty validated pending promotion rows")
    for row in rows:
        row.update(outcome="RETIRED",independent_review_verified=True,
            review_record=str(HANDLING_CALLBACK_PROMOTION_REVIEW.relative_to(ROOT)),
            outcome_note="Approved retired entry; RETIRED is never PASS")
    counts=dict(Counter(row["outcome"] for row in results))
    if counts!={"RETIRED":64,"BLOCKED":12}:raise ValueError("Unexpected replay retirement counts")
    for row in results:
        if row.get("case") not in selected:
            source=next((item for item in evidence["retirement_results"] if item["case"]==row["case"]),None)
            if row!=source:raise ValueError("Replay changed a retirement row outside the reviewed scope")
    result={"task":"KAN-15 handling callback retirement promotion replay",
      "basis":"Offline replay of independent promotion approval against fresh owned-runtime evidence; no runtime/browser fixture launched.",
      "source_evidence":str(HANDLING_CALLBACK_GATE_EVIDENCE.relative_to(ROOT)),"source_evidence_sha256":sha(raw),
      "promotion_validation_sha256":sha(validation),"review_record":str(HANDLING_CALLBACK_PROMOTION_REVIEW.relative_to(ROOT)),
      "review_record_sha256":sha(review),"inputs_fingerprint_from_fresh_run":evidence.get("provenance",{}).get("inputs_fingerprint"),
      "current_counts":evidence["current_counts"],"retirement_counts_before_review":evidence["retirement_counts"],
      "retirement_counts_after_review":counts,"changed_cases":["RETIREMENT::"+a+"::"+actor for a in actions for actor in ACTORS],
      "retirement_results":results,"legacy_audit":evidence["legacy_audit"],"gate_exit":2,"remaining_blocked_retirement_cases":12,
      "limitations":["The fresh live run is not repeated; aggregate, candidate, browser and review evidence are hash-pinned.",
       "RETIRED is not PASS; only ACTION-36, ACTION-37, ACTION-38, ACTION-39 and ACTION-42 rows change."]}
    output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(json.dumps(result,indent=2)+"\n")
    return result
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    result=replay(parser.parse_args().output);print(json.dumps({key:result[key] for key in ("current_counts","retirement_counts_after_review","gate_exit")}))
