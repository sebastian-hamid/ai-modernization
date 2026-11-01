#!/usr/bin/env python3
"""Execute fresh candidate bindings; unsupported access contracts remain blocked."""
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
        self.contracts=bound_contracts()
    def execute(self,case):
        canonical=self.contracts.get(case.get("id"))
        if canonical is None or canonical!=case:raise UnsupportedCase()
        observation=self.observations.get(case["id"])
        if observation is None:raise UnsupportedCase()
        return observation

def bound_contracts():
    paths={
        "API-01":("/cargo-tracker/rest/cargo","GET/HEAD"),
        "API-02":("/cargo-tracker/rest/handling/reports","POST"),
        "API-03":("/cargo-tracker/rest/graph-traversal/shortest-path","GET"),
        "API-03-SCOPED":("/cargo-tracker/rest/graph-traversal/shortest-path","GET"),
        "PRIVATE-01":("/cargo-tracker/WEB-INF/faces-config.xml","GET"),
        "PRIVATE-02":("/cargo-tracker/WEB-INF/glassfish-web.xml","GET"),
        "PRIVATE-03":("/cargo-tracker/WEB-INF/web.xml","GET"),
        "PRIVATE-04":("/cargo-tracker/WEB-INF/weblogic.xml","GET"),
        "PRIVATE-05":("/cargo-tracker/booking/todo.txt","GET"),
        "PAGE-01":("/cargo-tracker/WEB-INF/templates/common/admin.xhtml","GET"),
        "PAGE-02":("/cargo-tracker/WEB-INF/templates/common/public.xhtml","GET")}
    cases=build(json.loads((ROOT/"specifications/access-policy-inventory.json").read_text()))
    return {case["id"]:case for case in cases if paths.get(case["surface_id"])==(case.get("path"),case.get("method")) and (not case["surface_id"].startswith("PAGE-") or case.get("classification")=="internal-template")}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=ROOT/".work/kan14/candidate-results.json")
    ap.add_argument("--live-subset",action="store_true",help="Run fresh disposable candidate; unsupported catalogue cases remain BLOCKED")
    args=ap.parse_args()
    cases=build(json.loads((ROOT/"specifications/access-policy-inventory.json").read_text()))
    results=run_cases(cases,LiveSubsetCandidate() if args.live_subset else PendingCandidate())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"task":"KAN-14","adapter":"fresh live API and private-template subset" if args.live_subset else "not executed; use --live-subset for bounded coverage","counts":dict(Counter(r["outcome"] for r in results)),"results":results},indent=2)+"\n")
    print(dict(Counter(r["outcome"] for r in results)))
    raise SystemExit(exit_code(results))
