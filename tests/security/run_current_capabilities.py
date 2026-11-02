#!/usr/bin/env python3
"""Separate current-capability gate; no archival observations or retirement override."""
import argparse,json
from pathlib import Path
from current_capabilities import ROOT,report
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--live-subset",action="store_true",help="Run one fresh disposable native/browser fixture")
    parser.add_argument("--output",type=Path,default=ROOT/".work/kan15-current-capabilities/results.json")
    args=parser.parse_args()
    result=report(live=args.live_subset)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["current_counts","retirement_counts","gate_exit"]}))
    raise SystemExit(result["gate_exit"])
