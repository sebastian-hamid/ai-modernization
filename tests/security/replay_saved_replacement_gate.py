#!/usr/bin/env python3
"""Offline re-evaluation of retained same-run replacement proofs."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from contracts import evaluate
from current_capabilities import build_current, load_model
from replacements import replacement_observation
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"notes/evidence/kan-15-bg05-gate"

def sha256(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--gate",type=Path,default=EVIDENCE/"current-capability-gate.json")
 parser.add_argument("--proofs",type=Path,default=EVIDENCE/"browser-workflows.json")
 parser.add_argument("--output",type=Path,default=EVIDENCE/"replacement-gate-replay.json")
 args=parser.parse_args()
 model,inventory=load_model(); cases=build_current(model,inventory)
 proof_report=json.loads(args.proofs.read_text())
 gate=json.loads(args.gate.read_text())
 proofs=proof_report.get("replacement_observations",proof_report.get("replacement_actions",{}))
 prior={row["case"]:row for row in gate["current_results"]}; changed=[]
 for case in cases:
  if case["kind"]!="replacement": continue
  proof=proofs.get(case["id"])
  if proof is None: continue
  observation=replacement_observation(case,proof); outcome,reason=evaluate(case,observation)
  old=prior[case["id"]]["outcome"]
  if old!=outcome: changed.append({"case":case["id"],"previous":old,"replayed":outcome,"reason":reason})
 if len(changed)!=6 or any(x["replayed"]!="PASS" for x in changed):
  raise SystemExit("Unexpected saved-proof replay delta: "+json.dumps(changed))
 counts=Counter(row["outcome"] for row in gate["current_results"])
 for row in changed:
  counts[row["previous"]]-=1
  counts[row["replayed"]]+=1
 out={"task":"KAN-15 same-run replacement proof re-evaluation",
      "basis":"Offline re-evaluation of retained same-fixture browser proofs; no runtime or browser fixture launched.",
      "source_gate_sha256":sha256(args.gate),
      "source_proofs_sha256":sha256(args.proofs),
      "source_inputs_fingerprint":gate.get("provenance",{}).get("inputs_fingerprint"),
      "replay_scope":"handling-event, handling-voyage, and handling-completion replacement proofs for Operator and Administrator",
      "oracle_correction":{
       "handling_attempt_producer":"When its invocation metric is present, require exactly one publish per accepted handling event; older receipts without this metric remain explicitly unobserved.",
       "misdirected_notification":"Require MisdirectedCargoQueue, MisdirectedCargoConsumer, and NotificationWorkerAudit deltas to match exactly (zero or one)."},
      "changes":changed,
      "previous_current_counts":gate["current_counts"],
      "replayed_current_counts":dict(counts),
      "retirement_counts":gate["retirement_counts"],
      "gate_exit":2,
      "note":"Preserves the fresh gate's original outcomes and fingerprint. This supplemental offline evaluation corrects harness interpretation of six same-run proofs; it does not claim the fresh gate itself produced these revised outcomes."}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps({"replayed":len(changed),"counts":dict(counts),"output":str(args.output)}))
if __name__=="__main__":main()
