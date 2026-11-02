#!/usr/bin/env python3
"""Execute fresh candidate bindings; unsupported access contracts remain blocked."""
import argparse,json,importlib.util,re
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
        path=ROOT/"tests/browser-workflows/run_browser.py"
        spec=importlib.util.spec_from_file_location("live_candidate",path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        report=module.main()
        if report.get("status")!="PASS" or not report.get("owned_container_removed") or not report.get("private_files_removed"):raise RuntimeError("Live fixture failed or cleanup incomplete")
        browser=report.get("browser_checks",{});cleanup=report.get("browser_cleanup",{})
        if browser.get("passed") is not True or not browser.get("count") or cleanup.get("container_removed") is not True or cleanup.get("network_removed") is not True or cleanup.get("errors"):raise RuntimeError("Browser verification or cleanup incomplete")
        self.observations=report["access_observations"]
        self.contracts=bound_contracts()
    def execute(self,case):
        canonical=self.contracts.get(case.get("id"))
        if canonical is None or canonical!=case:raise UnsupportedCase()
        observation=self.observations.get(case["id"])
        if observation is None:raise UnsupportedCase()
        if case["surface_id"]=="ACTION-29":
            if observation.get("action_method")!="POST" or observation.get("action_path")!="/cargo-tracker/admin/book.xhtml" or observation.get("real_form_verified") is not True:raise UnsupportedCase()
            if case["channel"]=="session" and observation.get("form_owned_before_revocation") is not True:raise UnsupportedCase()
            if case["expected"]=="allow":
                proof=observation.get("processing_evidence",{})
                if observation.get("post_status") not in {302,303} or not isinstance(observation.get("tracking_id"),str) or re.fullmatch("[A-Z0-9]{8}",observation["tracking_id"]) is None or proof.get("database_changed") is not True or proof.get("book_new_cargo_invocation_delta")!=1 or proof.get("queue_unchanged") is not True or proof.get("independent_reader_persistence") is not True or proof.get("independent_reader_deadline") is not True:raise UnsupportedCase()
        if case["surface_id"]=="ACTION-09":
            tracking_id=observation.get("tracking_id")
            if not isinstance(tracking_id,str) or re.fullmatch("[A-Z0-9]{8}",tracking_id) is None or observation.get("action_method")!="POST" or observation.get("action_path")!="/cargo-tracker/admin/changeDestination.xhtml?trackingId="+tracking_id or observation.get("real_form_verified") is not True:raise UnsupportedCase()
            if case["channel"]=="session" and observation.get("form_owned_before_revocation") is not True:raise UnsupportedCase()
            if case["expected"]=="allow":
                proof=observation.get("processing_evidence",{})
                if observation.get("post_status") not in {302,303} or proof.get("database_changed") is not True or proof.get("change_destination_invocation_delta")!=1 or proof.get("queue_unchanged") is not True or proof.get("independent_reader_persistence") is not True or proof.get("independent_reader_deadline") is not True or proof.get("other_cargos_unchanged") is not True:raise UnsupportedCase()
        return observation

def bound_contracts():
    paths={
        "WS-01":("/cargo-tracker/tracking","HTTP Upgrade / send / close"),
        "WS-ORIGIN":("/cargo-tracker/tracking","HTTP Upgrade / send / close"),
        "API-01":("/cargo-tracker/rest/cargo","GET/HEAD"),
        "API-02":("/cargo-tracker/rest/handling/reports","POST"),
        "API-03":("/cargo-tracker/rest/graph-traversal/shortest-path","GET"),
        "API-03-SCOPED":("/cargo-tracker/rest/graph-traversal/shortest-path","GET"),
        "PRIVATE-01":("/cargo-tracker/WEB-INF/faces-config.xml","GET"),
        "PRIVATE-02":("/cargo-tracker/WEB-INF/glassfish-web.xml","GET"),
        "PRIVATE-03":("/cargo-tracker/WEB-INF/web.xml","GET"),
        "PRIVATE-04":("/cargo-tracker/WEB-INF/weblogic.xml","GET"),
        "PRIVATE-05":("/cargo-tracker/booking/todo.txt","GET"),
        "PAGE-03":("/cargo-tracker/admin/about.xhtml","GET"),
        "PAGE-06":("/cargo-tracker/admin/listClaimed.xhtml","GET"),
        "PAGE-07":("/cargo-tracker/admin/listNotRouted.xhtml","GET"),
        "PAGE-08":("/cargo-tracker/admin/listRouted.xhtml","GET"),
        "PAGE-22":("/cargo-tracker/index.xhtml","GET"),
        "PAGE-24":("/cargo-tracker/public/about.xhtml","GET"),
        "PAGE-04":("/cargo-tracker/admin/changeDestination.xhtml","GET"),
        "PAGE-05":("/cargo-tracker/admin/dashboard.xhtml","GET"),
        "PAGE-09":("/cargo-tracker/admin/map.xhtml","GET"),
        "PAGE-10":("/cargo-tracker/admin/mapFrame.html","GET"),
        "PAGE-11":("/cargo-tracker/admin/route.xhtml","GET"),
        "PAGE-12":("/cargo-tracker/admin/selectItinerary.xhtml","GET"),
        "PAGE-13":("/cargo-tracker/admin/show.xhtml","GET"),
        "PAGE-14":("/cargo-tracker/admin/track.xhtml","GET"),
        "PAGE-15":("/cargo-tracker/booking/booking-date.xhtml","GET"),
        "PAGE-16":("/cargo-tracker/booking/booking-destination.xhtml","GET"),
        "PAGE-17":("/cargo-tracker/booking/booking.xhtml","GET"),
        "PAGE-18":("/cargo-tracker/error.xhtml","GET"),
        "PAGE-19":("/cargo-tracker/error_404.xhtml","GET"),
        "PAGE-20":("/cargo-tracker/eventLogger/eventLogger.xhtml","GET"),
        "PAGE-21":("/cargo-tracker/eventLogger/root.xhtml","GET"),
        "PAGE-23":("/cargo-tracker/mobile.xhtml","GET"),
        "PAGE-25":("/cargo-tracker/public/track.xhtml","GET"),
        "PAGE-01":("/cargo-tracker/WEB-INF/templates/common/admin.xhtml","GET"),
        "PAGE-02":("/cargo-tracker/WEB-INF/templates/common/public.xhtml","GET")}
    cases=build(json.loads((ROOT/"specifications/access-policy-inventory.json").read_text()))
    classes={"PAGE-01":"internal-template","PAGE-02":"internal-template","PAGE-03":"read","PAGE-06":"read","PAGE-07":"read","PAGE-08":"read","PAGE-22":"public","PAGE-24":"public"}
    classes.update({'PAGE-04': 'operator', 'PAGE-05': 'read', 'PAGE-09': 'read', 'PAGE-10': 'read', 'PAGE-11': 'operator', 'PAGE-12': 'operator', 'PAGE-13': 'read', 'PAGE-14': 'read', 'PAGE-15': 'operator', 'PAGE-16': 'operator', 'PAGE-17': 'operator', 'PAGE-18': 'sanitized-error', 'PAGE-19': 'sanitized-error', 'PAGE-20': 'operator', 'PAGE-21': 'operator', 'PAGE-23': 'operator', 'PAGE-25': 'read'})
    bound={case["id"]:case for case in cases if paths.get(case["surface_id"])==(case.get("path"),case.get("method")) and (case["channel"]!="page" or case.get("classification")==classes.get(case["surface_id"]))}
    navigation={row["id"]:row for row in json.loads((ROOT/"tests/browser-workflows/navigation-actions.json").read_text())}
    for case in cases:
        row=navigation.get(case["surface_id"])
        if row and case["channel"]=="action" and case.get("callback")==row["callback"] and case.get("page_id")==row["page_id"] and case.get("method")=="GET" and case.get("path") is None and case.get("write") is False:
            allowed=row["anonymous"] if case["actor"]=="anonymous" else case["actor"] in row["allowed_roles"]
            if case["expected"]==("allow" if allowed else "deny"):bound[case["id"]]=case
    for case in cases:
        if case["surface_id"]=="ACTION-29" and case.get("callback")=="#{bookingBackingBean.register()}" and case.get("page_id")=="PAGE-15" and case.get("method")=="POST" and case.get("path") is None and case.get("write") is True and (case["channel"]=="action" or case["channel"]=="session" and case.get("original_channel")=="action"):
            bound[case["id"]]=case
    for case in cases:
        if case["surface_id"]=="ACTION-09" and case.get("callback")=="#{changeDestination.changeDestination()}" and case.get("page_id")=="PAGE-04" and case.get("method")=="POST" and case.get("path") is None and case.get("write") is True and (case["channel"]=="action" or case["channel"]=="session" and case.get("original_channel")=="action"):
            bound[case["id"]]=case
    return bound

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=ROOT/".work/kan14/candidate-results.json")
    ap.add_argument("--live-subset",action="store_true",help="Run fresh disposable candidate; unsupported catalogue cases remain BLOCKED")
    args=ap.parse_args()
    cases=build(json.loads((ROOT/"specifications/access-policy-inventory.json").read_text()))
    results=run_cases(cases,LiveSubsetCandidate() if args.live_subset else PendingCandidate())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"task":"KAN-14","adapter":"fresh browser-backed HTTP page/API/private subset" if args.live_subset else "not executed; use --live-subset for bounded coverage","counts":dict(Counter(r["outcome"] for r in results)),"results":results},indent=2)+"\n")
    print(dict(Counter(r["outcome"] for r in results)))
    raise SystemExit(exit_code(results))
