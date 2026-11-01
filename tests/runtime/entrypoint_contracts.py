#!/usr/bin/env python3
"""HTTP contracts and anonymous-access characterization of a disposable lab only."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import socket
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from handling_workflow import XmlResult

BASE=None
OBS=[]
SECURITY=[]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def request(path,method="GET",body=None,content_type="application/json",headers=None):
    # New opener, no cookie jar, Authorization header or inherited browser session.
    h={"Accept":"application/json"} if path.startswith("rest/") else {}
    if body is not None:h["Content-Type"]=content_type
    h.update(headers or {})
    req=urllib.request.Request(BASE+path,data=body,method=method,headers=h)
    try:response=urllib.request.build_opener(NoRedirect()).open(req,timeout=20)
    except urllib.error.HTTPError as error:response=error
    with response:
        data=response.read()
        OBS.append({"path":path,"method":method,"status":response.status,
                    "anonymous":True,"content_type":response.headers.get("Content-Type"),
                    "location":response.headers.get("Location"),"body_sha256":hashlib.sha256(data).hexdigest()})
        return response.status,data,response.headers

def payload(**overrides):
    data={"trackingId":"DEF789","eventType":"CUSTOMS","unLocode":"FIHEL","completionTime":"2030-01-01 10:00"}
    data.update(overrides)
    return data

class EntrypointTests(unittest.TestCase):
    def status(self,path,expected,method="GET",body=None,content_type="application/json",headers=None):
        status,data,h=request(path,method,body,content_type,headers)
        self.assertEqual(status,expected,(method,path,data[:200]))
        return data,h

    def test_monitor_schema_and_seed_ids(self):
        data,h=self.status("rest/cargo",200)
        self.assertIn("application/json",h.get("Content-Type",""))
        cargos=json.loads(data)
        self.assertTrue({"ABC123","DEF789","JKL567","MNO456"}.issubset({c["trackingId"] for c in cargos}))
        for c in cargos:
            self.assertTrue({"trackingId","routingStatus","transportStatus","misdirected","atDestination","origin","lastKnownLocation"}.issubset(c))
            self.assertIsInstance(c["misdirected"],bool)
            self.assertIsInstance(c["atDestination"],bool)

    def test_valid_customs_without_session_changes_state(self):
        status,data,h=request("rest/cargo")
        self.assertEqual(status,200)
        before=next(c for c in json.loads(data) if c["trackingId"]=="DEF789")
        self.assertNotEqual(before["lastKnownLocation"],"FIHEL","Requires untouched DEF789 or the existing smoke fixture")
        body=json.dumps(payload()).encode()
        self.status("rest/handling/reports",204,"POST",body)
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            status,data,h=request("rest/cargo")
            self.assertEqual(status,200)
            cargo=next(c for c in json.loads(data) if c["trackingId"]=="DEF789")
            if cargo["lastKnownLocation"]=="FIHEL" and cargo["transportStatus"]=="IN_PORT":break
            time.sleep(.25)
        else:self.fail("CUSTOMS state did not converge")
        self.assertNotEqual(cargo,before)
        SECURITY.append({"surface":"handling report write","anonymous_status":204,"state_change_verified":True,"finding":"Unauthenticated mutation"})

    def test_websocket_accepts_anonymous_cross_origin_handshake(self):
        parsed=urllib.parse.urlparse(BASE)
        key=base64.b64encode(b"0123456789abcdef").decode()
        path=parsed.path+"tracking"
        req=(f"GET {path} HTTP/1.1\r\nHost: {parsed.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: https://untrusted.example\r\n\r\n")
        with socket.create_connection((parsed.hostname,parsed.port or 80),timeout=10) as conn:
            conn.sendall(req.encode())
            response=b""
            while b"\r\n\r\n" not in response and len(response)<16384:
                chunk=conn.recv(4096)
                if not chunk:break
                response+=chunk
            # Complete the RFC 6455 close handshake; abrupt socket disposal can leave
            # this legacy server with a stale session that breaks later JMS transactions.
            mask=b"lab!"
            close_payload=b"\x03\xe8"
            conn.sendall(b"\x88\x82"+mask+bytes(v ^ mask[i % 4] for i,v in enumerate(close_payload)))
            conn.recv(4096)
        lines=response.split(b"\r\n")
        self.assertIn(b" 101 ",lines[0])
        accept=base64.b64encode(hashlib.sha1((key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest())
        headers={k.strip().lower():v.strip() for line in lines[1:] if b":" in line for k,v in [line.split(b":",1)]}
        self.assertEqual(headers.get(b"sec-websocket-accept"),accept)
        SECURITY.append({"surface":"tracking WebSocket","anonymous_status":101,"untrusted_origin_accepted":True,"finding":"Anonymous cross-origin handshake accepted; message delivery not covered"})

    def test_anonymous_details_contain_actual_cargo(self):
        data,h=self.status("admin/show.xhtml?trackingId=ABC123",200)
        self.assertIn(b"ABC123",data)
        self.assertIn(b"Origin",data)

    def test_monitor_head_has_no_body(self):
        data,h=self.status("rest/cargo",200,"HEAD")
        self.assertEqual(data,b"")

    def test_unacceptable_monitor_media_type(self):
        self.status("rest/cargo",406,headers={"Accept":"application/xml"})

    def test_mobile_redirect_stays_in_application(self):
        data,h=self.status("mobile.xhtml",302)
        target=urllib.parse.urlparse(h["Location"])
        self.assertEqual(target.netloc,urllib.parse.urlparse(BASE).netloc)
        self.assertIn("/eventLogger/eventLogger.xhtml",target.path)

    def test_anonymous_cross_origin_read_has_no_cors_grant(self):
        data,h=self.status("rest/cargo",200,headers={"Origin":"https://untrusted.example"})
        self.assertIsNone(h.get("Access-Control-Allow-Origin"))

    def test_routes_valid_structure_dates_and_voyages(self):
        for origin,dest in [("CNHKG","FIHEL"),("USCHI","SESTO")]:
            with self.subTest(origin=origin,destination=dest):
                data,h=self.status("rest/graph-traversal/shortest-path?"+urllib.parse.urlencode({"origin":origin,"destination":dest,"deadline":"2027-12-31"}),200)
                routes=json.loads(data)
                self.assertTrue(3<=len(routes)<=5)
                for route in routes:
                    edges=route["transitEdges"]
                    self.assertTrue(edges)
                    self.assertEqual(edges[0]["fromUnLocode"],origin)
                    self.assertEqual(edges[-1]["toUnLocode"],dest)
                    for edge in edges:
                        self.assertTrue(edge["voyageNumber"])
                        self.assertLess(edge["fromDate"],edge["toDate"])
                    for a,b in zip(edges,edges[1:]):
                        self.assertEqual(a["toUnLocode"],b["fromUnLocode"])
                        self.assertLess(a["toDate"],b["fromDate"])


def install_cases():
    def add(name,path,expected,method="GET",body=None,content_type="application/json",security=False):
        def test(self):
            data,h=self.status(path,expected,method,body,content_type)
            if security and expected in (200,204):SECURITY.append({"surface":path,"anonymous_status":expected,"finding":"Anonymous access allowed"})
        setattr(EntrypointTests,"test_"+name,test)
    pages=["index.xhtml","public/about.xhtml","public/track.xhtml","mobile.xhtml",
           "admin/dashboard.xhtml","admin/listNotRouted.xhtml","admin/listClaimed.xhtml","admin/map.xhtml","admin/about.xhtml",
           "admin/show.xhtml?trackingId=ABC123","admin/track.xhtml?trackingId=ABC123",
           "admin/selectItinerary.xhtml?trackingId=DEF789"]
    for n,path in enumerate(pages):
        expected=302 if path=="mobile.xhtml" else 500 if path.startswith("admin/track.xhtml") else 200
        add(f"page_{n:02d}",path,expected,security=path.startswith("admin/"))
    for n,path in enumerate(["admin/listRouted.xhtml","admin/route.xhtml?trackingId=DEF789","admin/changeDestination.xhtml?trackingId=ABC123","eventLogger/eventLogger.xhtml"]):
        add(f"direct_operational_page_{n}",path,500 if path.startswith("eventLogger/") else 200,security=True)
    for n,path in enumerate(["admin/show.xhtml","admin/show.xhtml?trackingId=UNKNOWN","admin/selectItinerary.xhtml?trackingId=UNKNOWN","admin/changeDestination.xhtml?trackingId=UNKNOWN"]):
        add(f"invalid_direct_id_{n}",path,500)

    for n,path in enumerate(["WEB-INF/web.xml","WEB-INF/templates/common/admin.xhtml","META-INF/MANIFEST.MF","no-such-page.xhtml","rest/no-such-resource","rest/cargo/ABC123"]):
        add(f"hidden_or_missing_{n}",path,404)
    add("anonymous_monitor","rest/cargo",200,security=True)
    for method in ["POST","PUT","DELETE","PATCH"]:add("monitor_disallows_"+method.lower(),"rest/cargo",405,method,None if method=="DELETE" else b"{}")
    for method in ["GET","PUT","DELETE"]:add("reports_disallow_"+method.lower(),"rest/handling/reports",405,method,b"{}" if method=="PUT" else None)
    invalid=[]
    for field in ["trackingId","completionTime","unLocode","eventType"]:
        value=payload();del value[field];invalid.append(("missing_"+field,value))
        for label,bad in [("null",None),("empty",""),("short","X")]:
            value=payload();value[field]=bad;invalid.append((label+"_"+field,value))
    for field,value in [("unLocode","CNHKGX"),("eventType","RECEIVEX"),("completionTime","2018-01-01 10:000"),("voyageNumber",""),("voyageNumber","X"),("voyageNumber","123456")]:
        invalid.append(("length_"+field+str(len(value)),payload(**{field:value})))
    for name,value in invalid:add(name,"rest/handling/reports",400,"POST",json.dumps(value).encode())
    for name,body,status,ct in [("empty_body",b"",400,"application/json"),("json_null",b"null",400,"application/json"),
            ("broken_json",b"{",400,"application/json"),("json_array",b"[]",400,"application/json"),
            ("text_body",b"invalid",415,"text/plain"),("xml_body",b"<report/>",415,"application/xml")]:
        add(name,"rest/handling/reports",status,"POST",body,ct)
    for name,value in [("lowercase_event",payload(eventType="receive")),("invalid_location_syntax",payload(unLocode="12345"))]:
        add(name,"rest/handling/reports",500,"POST",json.dumps(value).encode())
    for name,value in [("empty_object",{}),("object_tracking_id",payload(trackingId={"id":"ABC123"}))]:
        add(name,"rest/handling/reports",400,"POST",json.dumps(value).encode())
    for n,query in enumerate([{}, {"origin":"CNHKG"},{"destination":"FIHEL"},{"origin":"BAD","destination":"FIHEL"},{"origin":"CNHKG","destination":""},{"origin":"CNHKGX","destination":"FIHEL"}]):
        add("bad_route_"+str(n),"rest/graph-traversal/shortest-path?"+urllib.parse.urlencode(query),400)

install_cases()

def access_control_failed(findings):
    return bool(findings)

def main():
    global BASE
    p=argparse.ArgumentParser()
    p.add_argument("--base-url",required=True)
    p.add_argument("--report-dir",type=Path,required=True)
    p.add_argument("--allow-mutation",action="store_true")
    p.add_argument("--require-access-control",action="store_true",help="Fail when anonymous operational access is observed; legacy baseline is expected to fail")
    args=p.parse_args();BASE=args.base_url.rstrip("/")+"/"
    u=urllib.parse.urlparse(BASE)
    if u.scheme!="http" or u.hostname not in {"localhost","127.0.0.1"} or not args.allow_mutation:
        p.error("Requires local HTTP and --allow-mutation on an isolated disposable runtime")
    result=unittest.TextTestRunner(verbosity=2,resultclass=XmlResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(EntrypointTests))
    args.report_dir.mkdir(parents=True,exist_ok=True)
    suite=ET.Element("testsuite",name="EntrypointContracts",tests=str(len(result.cases)),failures=str(sum(c.find("failure") is not None for c in result.cases)),errors=str(sum(c.find("error") is not None for c in result.cases)),skipped=str(sum(c.find("skipped") is not None for c in result.cases)))
    suite.extend(result.cases)
    ET.ElementTree(suite).write(args.report_dir/"TEST-entrypoint-contracts.xml",encoding="utf-8",xml_declaration=True)
    (args.report_dir/"observations.json").write_text(json.dumps({"base_url":BASE,"requests":OBS,"security_findings":SECURITY,"security_assessment":"FAIL: anonymous operational access observed" if SECURITY else "No conclusion; inspect test completion"},indent=2)+"\n")
    if args.require_access_control and access_control_failed(SECURITY):
        print("ACCESS CONTROL REQUIREMENT FAILED:",len(SECURITY),"anonymous operational surfaces observed")
        return 1
    return 0 if result.wasSuccessful() else 1

if __name__=="__main__":raise SystemExit(main())
