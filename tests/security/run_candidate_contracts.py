#!/usr/bin/env python3
"""Fail closed until real candidate adapters are implemented in the security slice."""
import argparse,json,importlib.util
from collections import Counter
from pathlib import Path
from contracts import UnsupportedCase,run_cases,exit_code
from generate_cases import ROOT,build
class PendingCandidate:
    def execute(self,case):
        raise UnsupportedCase()
class LiveSubsetCandidate:
    """Uses only explicit observations from a fresh disposable run, never archived PASS summaries."""
    def __init__(self):
        path=ROOT/"tests/candidate-runtime/run_candidate.py"
        spec=importlib.util.spec_from_file_location("live_candidate",path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        report=module.main()
        if report.get("status")!="PASS" or not report.get("owned_container_removed") or not report.get("private_files_removed"):raise RuntimeError("Live fixture failed or cleanup incomplete")
        self.observations=report["access_observations"]
    def execute(self,case):
        surface=case.get("surface_id")
        if surface=="API-02":
            valid=case.get("path")=="/cargo-tracker/rest/handling/reports" and case.get("method")=="POST" and case.get("expected")=="deny" and case.get("write") is True
        elif surface=="API-01":
            valid=case.get("path")=="/cargo-tracker/rest/cargo" and case.get("method")=="GET/HEAD" and case.get("write") is False and case.get("expected")==("deny" if case.get("actor")=="anonymous" else "allow")
        elif surface in {"PAGE-01","PAGE-02"}:
            template="admin" if surface=="PAGE-01" else "public"
            valid=case.get("path")=="/cargo-tracker/WEB-INF/templates/common/"+template+".xhtml" and case.get("method")=="GET" and case.get("classification")=="internal-template" and case.get("expected")=="deny" and case.get("write") is False
        else:valid=False
        if not valid:raise UnsupportedCase()
        observation=self.observations.get(case["id"])
        if observation is None:raise UnsupportedCase()
        return observation

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=ROOT/".work/kan14/candidate-results.json")
    ap.add_argument("--live-subset",action="store_true",help="Run fresh disposable candidate; unsupported catalogue cases remain BLOCKED")
    args=ap.parse_args()
    cases=build(json.loads((ROOT/"specifications/access-policy-inventory.json").read_text()))
    results=run_cases(cases,LiveSubsetCandidate() if args.live_subset else PendingCandidate())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"task":"KAN-14","adapter":"fresh live handling-denial subset" if args.live_subset else "not executed; use --live-subset for bounded coverage","counts":dict(Counter(r["outcome"] for r in results)),"results":results},indent=2)+"\n")
    print(dict(Counter(r["outcome"] for r in results)))
    raise SystemExit(exit_code(results))
