#!/usr/bin/env python3
"""Offline re-evaluation of retained same-run replacement proofs."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from contracts import evaluate
from current_capabilities import batch_worker_observation, build_current, load_model
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
 parser.add_argument("--worker-log",type=Path)
 args=parser.parse_args()
 model,inventory=load_model(); cases=build_current(model,inventory)
 proof_report=json.loads(args.proofs.read_text())
 gate=json.loads(args.gate.read_text())
 proofs=proof_report.get("replacement_observations",proof_report.get("replacement_actions",{}))
 prior={row["case"]:row for row in gate["current_results"]}; changed=[]; rechecked=[]
 replay_groups={"handling-event","handling-voyage","handling-completion"}
 for case in cases:
  if (case["kind"]!="replacement" or case.get("capability_id") not in replay_groups
          or case.get("actor") not in {"Operator","Administrator"}): continue
  proof=proofs.get(case["id"])
  if proof is None: continue
  observation=replacement_observation(case,proof); outcome,reason=evaluate(case,observation)
  rechecked.append({"case":case["id"],"outcome":outcome})
  old=prior[case["id"]]["outcome"]
  if old!=outcome: changed.append({"case":case["id"],"previous":old,"replayed":outcome,"reason":reason})
 machine_identity=None
 processing=proof_report.get("batch_processing_observation")
 if processing is not None:
  machine_case=next(row for row in cases if row["id"]=="CURRENT::BG-01-MACHINE::worker-BG-01::active")
  observation=batch_worker_observation(machine_case,processing)
  outcome,reason=evaluate(machine_case,observation)
  rechecked.append({"case":machine_case["id"],"outcome":outcome})
  old=prior[machine_case["id"]]["outcome"]
  if old!=outcome: changed.append({"case":machine_case["id"],"previous":old,"replayed":outcome,"reason":reason})
  if args.worker_log is None: raise SystemExit("--worker-log is required when replaying BG-01-MACHINE")
  log=re.sub(r"\x1b\[[0-9;]*m","",args.worker_log.read_text(errors="replace"))
  started=set(re.findall(r"IMPORT_AUDIT event=started runId=([0-9a-f-]{36}) initiator=admin worker=batch-worker",log))
  finished=set(re.findall(r"IMPORT_AUDIT event=finished:COMPLETED runId=([0-9a-f-]{36}) initiator=admin worker=batch-worker",log))
  pairs=sorted(started & finished)
  if not processing.get("authorized_job_completed") or not pairs:
   raise SystemExit("Valid-job worker identity proof is not backed by matching server audit records")
  machine_identity={"case":machine_case["id"],"outcome":outcome,"machine_principal":"batch-worker",
      "machine_role":"BatchWorker","initiator_principal":processing["administrator_identity"]["principal"],
      "valid_job_audit_correlated":processing["authorized_job_completed"],
      "server_audit_pairs_in_fixture_log":len(pairs),"server_log_sha256":sha256(args.worker_log),
      "scope":machine_case["required_machine_scope"],
      "processing_evidence":{key:processing.get(key) for key in [
          "authorized_job_completed","directory_policy_verified",
          "valid_input_consumed","valid_event_persisted","valid_archive_verified",
          "invalid_input_consumed","invalid_failed_output_verified","business_side_effects_bounded"]}}
 expected_replacements={"REPLACEMENT::"+group+"::"+actor for group in
     ("handling-event","handling-voyage","handling-completion") for actor in ("Operator","Administrator")}
 expected_cases=expected_replacements|({"CURRENT::BG-01-MACHINE::worker-BG-01::active"} if processing is not None else set())
 if {row["case"] for row in rechecked}!=expected_cases or any(row["outcome"]!="PASS" for row in rechecked):
  raise SystemExit("Unexpected saved-proof re-evaluation: "+json.dumps(rechecked))
 counts=Counter(row["outcome"] for row in gate["current_results"])
 for row in changed:
  counts[row["previous"]]-=1
  counts[row["replayed"]]+=1
 out={"task":"KAN-15 current-capability proof re-evaluation",
      "basis":"Offline re-evaluation of retained same-fixture workflow and server-worker proofs; no runtime or browser fixture launched.",
      "source_gate_sha256":sha256(args.gate),
      "source_proofs_sha256":sha256(args.proofs),
      "source_inputs_fingerprint":gate.get("provenance",{}).get("inputs_fingerprint"),
      "replay_scope":"handling-event, handling-voyage, and handling-completion replacement proofs for Operator and Administrator"+("; BG-01-MACHINE batch worker identity" if machine_identity else ""),
      "machine_identity":machine_identity,
      "oracle_correction":{
       "handling_attempt_producer":"When its invocation metric is present, require exactly one publish per accepted handling event; older receipts without this metric remain explicitly unobserved.",
       "misdirected_notification":"Require MisdirectedCargoQueue, MisdirectedCargoConsumer, and NotificationWorkerAudit deltas to match exactly (zero or one)."},
      "rechecked_cases":rechecked,
      "changes":changed,
      "previous_current_counts":gate["current_counts"],
      "replayed_current_counts":dict(counts),
      "retirement_counts":gate["retirement_counts"],
      "gate_exit":2,
      "note":f"Preserves the fresh gate's original outcomes and fingerprint. This supplemental offline evaluation rechecks {len(rechecked)} same-run proofs; it does not claim the fresh gate itself produced these revised outcomes."}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps({"replayed":len(changed),"counts":dict(counts),"output":str(args.output)}))
if __name__=="__main__":main()
