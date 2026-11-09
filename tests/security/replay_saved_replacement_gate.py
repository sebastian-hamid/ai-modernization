#!/usr/bin/env python3
"""Offline re-evaluation of retained same-run replacement proofs."""
import json
from collections import Counter
from pathlib import Path
from contracts import evaluate
from current_capabilities import build_current, load_model
from replacements import replacement_observation
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"notes/evidence/kan-15-bg05-gate"
def main():
 model,inventory=load_model(); cases=build_current(model,inventory)
 browser=json.loads((EVIDENCE/"browser-workflows.json").read_text())
 gate=json.loads((EVIDENCE/"current-capability-gate.json").read_text())
 prior={row["case"]:row for row in gate["current_results"]}; changed=[]
 for case in cases:
  if case["kind"]!="replacement": continue
  proof=browser["replacement_actions"].get(case["id"])
  if proof is None: continue
  observation=replacement_observation(case,proof); outcome,reason=evaluate(case,observation)
  old=prior[case["id"]]["outcome"]
  if old!=outcome: changed.append({"case":case["id"],"previous":old,"replayed":outcome,"reason":reason})
 if len(changed)!=6 or any(x["replayed"]!="PASS" for x in changed): raise SystemExit("Unexpected saved-proof replay delta: "+json.dumps(changed))
 counts=Counter(x["outcome"] for x in gate["current_results"]);counts.update({"PASS":6,"BLOCKED":-6})
 out={"task":"KAN-15 BG-05 saved replacement gate re-evaluation","basis":"Offline re-evaluation of retained same-fixture browser proof; no runtime or browser fixture launched.","source_gate_sha256":"502d94c53c86d48e9c9016788fd96ec0cda24630630444cbd9eda4abe400d398","source_browser_workflows_sha256":"eaf9d786125eb17c688e0d41a3e9cdd20b01a3e33b679180ef6578ad42e0e657","source_candidate_runtime_sha256":"3cecfdb178fab3fe0f7e5bbf538f3689463f8dab55a84a00c7da35c53e88a975","replay_scope":"handling-event, handling-voyage, and handling-completion replacement proofs for Operator and Administrator","changes":changed,"previous_current_counts":{"PASS":438,"BLOCKED":32},"replayed_current_counts":dict(counts),"retirement_counts":gate["retirement_counts"],"gate_exit":2,"note":"Preserves the original fresh-run fingerprint and results; this record only corrects harness evaluation of six saved proofs."}
 (EVIDENCE/"replacement-gate-replay.json").write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps({"replayed":len(changed),"counts":dict(counts)}))
if __name__=="__main__":main()
