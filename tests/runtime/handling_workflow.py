#!/usr/bin/env python3
# Ordered characterization of a disposable, seeded legacy runtime.
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import traceback
import unittest
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

CLIENT=None

class RuntimeClient:
    def __init__(self, base, server_log=None, container=None):
        self.base=base.rstrip("/")+"/"
        self.server_log=Path(server_log) if server_log else None
        self.container=container
        self.observations={}
        self.current=""

    def record(self, event):
        self.observations.setdefault(self.current,[]).append(event)

    def cargos(self):
        with urllib.request.urlopen(self.base+"rest/cargo",timeout=20) as response:
            if response.status!=200:
                raise RuntimeError(f"Cargo monitor returned {response.status}")
            return {row["trackingId"]:row for row in json.load(response)}

    def post(self, payload):
        request=urllib.request.Request(self.base+"rest/handling/reports",
            data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                status=response.status
        except urllib.error.HTTPError as response:
            status=response.code
            response.close()
        self.record({"request":payload,"http_status":status})
        return status

    def logs(self):
        if self.server_log:
            return self.server_log.read_text(errors="replace")
        return subprocess.check_output(["docker","logs",self.container],stderr=subprocess.STDOUT).decode(errors="replace")

    def state(self, tracking, **expected):
        deadline=time.monotonic()+20
        after=None
        while time.monotonic()<deadline:
            after=self.cargos()[tracking]
            if all(after[key]==value for key,value in expected.items()):
                self.record({"trackingId":tracking,"expected":expected,"observed":after})
                return after
            time.sleep(.25)
        raise AssertionError(f"JMS state did not converge for {tracking}: wanted {expected}; observed {after}")

class HandlingWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initial=CLIENT.cargos()
        if initial["ABC123"]["transportStatus"]!="IN_PORT" or initial["ABC123"]["lastKnownLocation"]!="USNYC":
            raise RuntimeError("This suite requires a freshly seeded disposable runtime, not an existing user session")
        if initial["JKL567"]["transportStatus"]!="ONBOARD_CARRIER":
            raise RuntimeError("Expected original JKL567 seed state")

    def setUp(self):
        CLIENT.current=self.id()

    def payload(self, **overrides):
        value={"trackingId":"ABC123","unLocode":"CNHKG",
               "completionTime":"2017-01-20 10:00","eventType":"RECEIVE"}
        value.update(overrides)
        return value

    def rejected_synchronously(self, payload, status):
        before=CLIENT.cargos()
        self.assertEqual(CLIENT.post(payload),status)
        self.assertEqual(CLIENT.cargos(),before)

    def rejected_asynchronously(self, payload, log_reason):
        before=CLIENT.cargos()
        offset=len(CLIENT.logs())
        self.assertEqual(CLIENT.post(payload),204)
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            recent=CLIENT.logs()[offset:]
            reasons=(log_reason,) if isinstance(log_reason,str) else log_reason
            if all(reason in recent for reason in reasons):
                CLIENT.record({"handler_failure_confirmed":log_reason})
                break
            time.sleep(.25)
        else:
            self.fail(f"No new handler failure containing {log_reason!r}; HTTP acceptance alone is not rejection evidence")
        # This is a bounded no-change observation, not a claim about dead-letter completion.
        for _ in range(4):
            self.assertEqual(CLIENT.cargos(),before)
            time.sleep(.25)
        CLIENT.record({"cargo_monitor_unchanged_for_seconds":1,"dead_letter_state":"not inspected"})

    def test_01_receive_load_unload_and_claim_along_seeded_route(self):
        # Separate completion DAYS avoid the legacy DATE-column precision limit.
        # Replay timestamps follow all seeded 2016 events without changing server time.
        journey=[
            ("RECEIVE","CNHKG",None,"IN_PORT",False),
            ("LOAD","CNHKG","0100S","ONBOARD_CARRIER",False),
            ("UNLOAD","USNYC","0100S","IN_PORT",False),
            ("LOAD","USNYC","0200T","ONBOARD_CARRIER",False),
            ("UNLOAD","USDAL","0200T","IN_PORT",False),
            ("LOAD","USDAL","0300A","ONBOARD_CARRIER",False),
            ("UNLOAD","FIHEL","0300A","IN_PORT",True),
            ("CLAIM","FIHEL",None,"CLAIMED",False),
        ]
        for day,(event,location,voyage,status,at_destination) in enumerate(journey,1):
            with self.subTest(event=event,location=location,day=day):
                payload=self.payload(eventType=event,unLocode=location,completionTime=f"2017-01-{day:02d} 10:00")
                if voyage:payload["voyageNumber"]=voyage
                self.assertEqual(CLIENT.post(payload),204)
                CLIENT.state("ABC123",transportStatus=status,lastKnownLocation=location,
                    routingStatus="ROUTED",misdirected=False,atDestination=at_destination)

    def test_02_missing_tracking_id_is_http_400(self):
        payload=self.payload()
        del payload["trackingId"]
        self.rejected_synchronously(payload,400)

    def test_03_short_tracking_id_is_http_400(self):
        self.rejected_synchronously(self.payload(trackingId="BAD"),400)

    def test_04_missing_completion_time_is_http_400(self):
        payload=self.payload()
        del payload["completionTime"]
        self.rejected_synchronously(payload,400)

    def test_05_invalid_location_length_is_http_400(self):
        self.rejected_synchronously(self.payload(unLocode="BAD"),400)

    def test_06_invalid_voyage_length_is_http_400(self):
        self.rejected_synchronously(self.payload(voyageNumber="BAD"),400)

    def test_07_unknown_event_type_currently_returns_http_500(self):
        # Known legacy API defect: a shape-valid unknown enum is not mapped to 400.
        self.rejected_synchronously(self.payload(eventType="BROKEN"),500)

    def test_08_unparsable_completion_time_currently_returns_http_500(self):
        self.rejected_synchronously(self.payload(completionTime="not-a-real-date!"),500)

    def test_09_unknown_cargo_is_queued_then_fails_lookup(self):
        self.rejected_asynchronously(self.payload(trackingId="UNKNOWN"),"UnknownCargoException")

    def test_10_unknown_location_is_queued_then_fails_lookup(self):
        self.rejected_asynchronously(self.payload(unLocode="ZZZZZ"),("NoResultException","JpaLocationRepository.find"))

    def test_11_unknown_voyage_is_queued_then_fails_lookup(self):
        self.rejected_asynchronously(self.payload(eventType="LOAD",voyageNumber="9999X"),("NoResultException","JpaVoyageRepository.find"))

    def test_12_load_without_voyage_is_queued_then_rejected(self):
        self.rejected_asynchronously(self.payload(eventType="LOAD"),"Voyage is required for event type LOAD")

    def test_13_receive_with_voyage_is_queued_then_rejected(self):
        self.rejected_asynchronously(self.payload(voyageNumber="0100S"),"Voyage is not allowed with event type RECEIVE")

    def test_14_invalid_calendar_date_is_currently_accepted(self):
        # SimpleDateFormat is lenient in the unchanged application.
        payload=self.payload(trackingId="JKL567",completionTime="2017-02-30 10:00")
        self.assertEqual(CLIENT.post(payload),204)
        CLIENT.state("JKL567",transportStatus="IN_PORT",lastKnownLocation="CNHKG",misdirected=True)

    def test_15_existing_off_route_voyage_is_accepted_and_flagged(self):
        # The legacy model does not forbid loading after a claim; record its current behavior.
        payload=self.payload(eventType="LOAD",voyageNumber="0100S",
            unLocode="FIHEL",completionTime="2017-01-09 10:00")
        self.assertEqual(CLIENT.post(payload),204)
        CLIENT.state("ABC123",transportStatus="ONBOARD_CARRIER",
            lastKnownLocation="FIHEL",misdirected=True)

class XmlResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.cases=[]
        self.started={}
        self.subtest_errors={}

    def startTest(self,test):
        self.started[test.id()]=time.monotonic()
        super().startTest(test)

    def case(self,test,kind=None,detail=None):
        name=test.id()
        node=ET.Element("testcase",classname=name.rsplit(".",1)[0],name=name.rsplit(".",1)[-1],
            time=f"{max(0.0,time.monotonic()-self.started.get(name,time.monotonic())):.3f}")
        if kind:ET.SubElement(node,kind).text=detail or ""
        self.cases.append(node)

    def addSuccess(self,test):
        super().addSuccess(test)
        self.case(test)

    def addFailure(self,test,err):
        super().addFailure(test,err)
        self.case(test,"failure","".join(traceback.format_exception(*err)))

    def addError(self,test,err):
        super().addError(test,err)
        self.case(test,"error","".join(traceback.format_exception(*err)))

    def addSkip(self,test,reason):
        super().addSkip(test,reason)
        self.case(test,"skipped",reason)

    def addSubTest(self,test,subtest,err):
        # A failed journey substep belongs to one journey case, not extra tests.
        super().addSubTest(test,subtest,err)
        if err is not None:
            self.subtest_errors.setdefault(test.id(),[]).append("".join(traceback.format_exception(*err)))

    def stopTest(self,test):
        errors=self.subtest_errors.get(test.id())
        if errors:
            self.case(test,"failure","\n".join(errors))
        super().stopTest(test)

def main():
    global CLIENT
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",required=True)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--server-log")
    source.add_argument("--container")
    parser.add_argument("--report-dir",required=True,type=Path)
    parser.add_argument("--allow-mutation",action="store_true",help="Required: this ordered suite changes sample cargos")
    args=parser.parse_args()
    if not args.allow_mutation:parser.error("Use --allow-mutation only for a disposable seeded runtime")
    parsed=urllib.parse.urlparse(args.base_url)
    if parsed.scheme!="http" or parsed.hostname not in {"localhost","127.0.0.1"}:
        parser.error("Only local HTTP lab endpoints are supported")
    CLIENT=RuntimeClient(args.base_url,args.server_log,args.container)
    args.report_dir.mkdir(parents=True,exist_ok=True)
    result=unittest.TextTestRunner(verbosity=2,resultclass=XmlResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(HandlingWorkflowTests))
    suite=ET.Element("testsuite",name="LegacyHandlingWorkflow",tests=str(len(result.cases)),
        failures=str(sum(case.find("failure") is not None for case in result.cases)),
        errors=str(sum(case.find("error") is not None for case in result.cases)),
        skipped=str(sum(case.find("skipped") is not None for case in result.cases)))
    for case in result.cases:suite.append(case)
    ET.ElementTree(suite).write(args.report_dir/"TEST-legacy-handling-workflow.xml",encoding="utf-8",xml_declaration=True)
    (args.report_dir/"observations.json").write_text(json.dumps({
        "verified_at":datetime.now(timezone.utc).isoformat(),"base_url":CLIENT.base,
        "fixture":"seeded application; ordered 2017 completion dates; unchanged application source",
        "observations":CLIENT.observations},indent=2)+"\n")
    return 0 if result.wasSuccessful() and result.testsRun==15 else 1

if __name__=="__main__":
    raise SystemExit(main())
