#!/usr/bin/env python3
"""Desired-security RED checks. Owns one disposable runtime; never targets a supplied URL."""
import base64,hashlib,json,socket,subprocess,time,urllib.error,urllib.request
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
IMAGE="sha256:899f3ae0a00cc80fd9e8dd49d9104da4baf4aad81167754ac51c8c3b7a160e84"
NAME="ai-modernization-kan14"
OUT=ROOT/".work/kan14"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**kw):return None
def docker(*args):
    return subprocess.check_output(["docker",*args],text=True).strip()
def request(base,path,method="GET",body=None):
    req=urllib.request.Request(base+path,data=body,method=method,
        headers={"Content-Type":"application/json"} if body else {})
    try:r=urllib.request.build_opener(NoRedirect()).open(req,timeout=10)
    except urllib.error.HTTPError as e:r=e
    with r:return r.status,r.read(),r.headers
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cid=None;results=[];report={"task":"KAN-14","purpose":"Desired security, expected RED on unchanged historical application","image_id":IMAGE}
    try:
        # Docker rejects an existing name. Never remove someone else's container.
        cid=docker("run","-d","--name",NAME,"--label","ai-modernization.task=KAN-14",
                   "-p","127.0.0.1::8080",IMAGE)
        port=int(docker("port",cid,"8080/tcp").rsplit(":",1)[1])
        base=f"http://127.0.0.1:{port}/cargo-tracker/"
        deadline=time.monotonic()+180
        while True:
            try:
                if request(base,"rest/cargo")[0]==200:break
            except (OSError,urllib.error.URLError):pass
            if time.monotonic()>deadline:raise RuntimeError("Disposable runtime not ready")
            time.sleep(1)
        report["container_id"]=cid
        def record(name,status,allowed,**extra):
            results.append(dict(case=name,status=status,outcome="PASS" if allowed else "FAIL",**extra))
        # Exact public pages must remain reachable.
        for path in ["index.xhtml","public/about.xhtml"]:
            status,body,h=request(base,path)
            record("public:"+path,status,status==200)
        for path in ["public/track.xhtml","admin/dashboard.xhtml","admin/show.xhtml?trackingId=ABC123","admin/mapFrame.html",
                     "rest/cargo","rest/graph-traversal/shortest-path?origin=CNHKG&destination=FIHEL&deadline=2030-12-31"]:
            status,body,h=request(base,path)
            # No login exists in historical app; do not treat arbitrary flow redirects as login.
            record("anonymous-denied:"+path,status,status in {401,403},
                   body_sha256=hashlib.sha256(body).hexdigest(),
                   cargo_marker_present=b"ABC123" in body)
        before=json.loads(request(base,"rest/cargo")[1])
        before=next(c for c in before if c["trackingId"]=="DEF789")
        if before["lastKnownLocation"]=="FIHEL":raise RuntimeError("Disposable fixture is not fresh")
        payload={"trackingId":"DEF789","eventType":"RECEIVE","unLocode":"FIHEL","completionTime":"2030-01-01 10:00"}
        status,body,h=request(base,"rest/handling/reports","POST",json.dumps(payload).encode())
        deadline=time.monotonic()+25;after=before
        while time.monotonic()<deadline:
            after=next(c for c in json.loads(request(base,"rest/cargo")[1]) if c["trackingId"]=="DEF789")
            if after["lastKnownLocation"]=="FIHEL" and after["transportStatus"]=="IN_PORT":break
            time.sleep(.25)
        # Positive mutation proves a security defect; absence alone cannot prove no queued work.
        record("anonymous-write-denied",status,status==401 and after==before,
               before=before,after=after,mutation_observed=after!=before,
               no_effect_assertion_verified=False,
               limitation="Monitor is not an independent database/queue/audit observer; no PASS for denied-write contract from this probe")
        if results[-1]["outcome"]=="PASS":results[-1]["outcome"]="BLOCKED"
        key=base64.b64encode(b"0123456789abcdef").decode()
        with socket.create_connection(("127.0.0.1",port),timeout=10) as conn:
            conn.sendall((f"GET /cargo-tracker/tracking HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: https://untrusted.example\r\n\r\n").encode())
            response=b""
            while b"\r\n\r\n" not in response:
                chunk=conn.recv(4096)
                if not chunk or len(response)>16384:break
                response+=chunk
            status=int(response.split(b" ",2)[1])
            if status==101:
                mask=b"lab!";payload=b"\x03\xe8"
                conn.sendall(b"\x88\x82"+mask+bytes(v^mask[i%4] for i,v in enumerate(payload)))
                conn.recv(4096)
        record("anonymous-cross-origin-websocket-denied",status,status in {401,403},
               limitation="Upgrade only; authorized frames and authenticated Origin checks require candidate adapter")
    except Exception as e:
        results.append({"case":"infrastructure","outcome":"ERROR","reason":type(e).__name__})
        raise
    finally:
        if cid:
            try:
                logs=subprocess.check_output(["docker","logs",cid],stderr=subprocess.STDOUT,text=True)
                (OUT/"legacy-runtime.log").write_text(logs)
                report["registration_log_present"]="Registered handling event" in logs
            finally:
                docker("rm","-f",cid)
                report["owned_container_removed"]=True
        report["results"]=results
        report["counts"]=dict(Counter(r["outcome"] for r in results))
        (OUT/"legacy-results.json").write_text(json.dumps(report,indent=2)+"\n")
        print(report["counts"])
    return 1 if any(r["outcome"] in {"FAIL","ERROR"} for r in results) else 2 if any(r["outcome"]=="BLOCKED" for r in results) else 0
if __name__=="__main__":raise SystemExit(main())
