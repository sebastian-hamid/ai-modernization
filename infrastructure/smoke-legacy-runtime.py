#!/usr/bin/env python3
# Exercise the locally seeded baseline over HTTP without changing application code.
import argparse
from datetime import datetime
from html.parser import HTMLParser
import http.cookiejar
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


BASE = "http://127.0.0.1:8081/cargo-tracker/"
class Forms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms=[]
        self.current=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.current={"id":a.get("id"),"action":a["action"],"fields":{},"buttons":[]}
            self.forms.append(self.current)
        elif self.current is not None and tag=="input" and a.get("name"):
            self.current["fields"][a["name"]]=a.get("value","")
        elif self.current is not None and tag=="button" and a.get("name"):
            self.current["buttons"].append(a["name"])
    def handle_endtag(self,tag):
        if tag=="form":self.current=None
parser=argparse.ArgumentParser()
parser.add_argument("--base-url",default=BASE,help="Local Cargo Tracker URL; CI uses its isolated port 8080")
parser.add_argument("--exercise-handling",action="store_true",help="Mutates seeded DEF789; requires its initial NOT_RECEIVED state")
args=parser.parse_args()
BASE=args.base_url.rstrip('/')+'/'
require(urllib.parse.urlparse(BASE).hostname in {'localhost','127.0.0.1'}, 'Only local lab endpoints are supported')
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(path):
    with opener.open(BASE+path,timeout=20) as r:
        require(r.status==200, (path,r.status))
        return r.read().decode()
def cargos():
    return {c["trackingId"]:c for c in json.loads(get("rest/cargo"))}
before=cargos()
require({"ABC123","DEF789","JKL567","MNO456"}.issubset(before), 'Required setup invariant failed')
out={"verified_at":datetime.now().isoformat(),"base_url":BASE,"seeded_cargos":before,"checks":[]}
for path in ["","public/track.xhtml","admin/dashboard.xhtml","mobile.xhtml"]:
    html=get(path)
    require("<html" in html.lower(), path)
    out["checks"].append({"check":"page","path":path,"status":200})
html=get("public/track.xhtml")
forms=Forms()
forms.feed(html)
form=next(f for f in forms.forms if f["id"]=="trackingForm")
fields=form["fields"]
fields["trackingForm:trackingId_input"]="ABC123"
fields[form["buttons"][0]]=form["buttons"][0]
request=urllib.request.Request(urllib.parse.urljoin(BASE,form["action"]),data=urllib.parse.urlencode(fields).encode())
with opener.open(request,timeout=20) as r:tracked=r.read().decode()
require('id="result"' in tracked and "<strong>ABC123</strong>" in tracked, "Tracking did not render ABC123")
out["checks"].append({"check":"public_tracking_form","trackingId":"ABC123","status":"passed"})
routes=json.loads(get("rest/graph-traversal/shortest-path?origin=CNHKG&destination=FIHEL&deadline=2027-12-31"))
require(3<=len(routes)<=5, len(routes))
for candidate in routes:
    edges=candidate["transitEdges"]
    require(edges[0]["fromUnLocode"]=="CNHKG", edges[0])
    require(edges[-1]["toUnLocode"]=="FIHEL", edges[-1])
    for a,b in zip(edges,edges[1:]):require(a["toUnLocode"]==b["fromUnLocode"], 'Required setup invariant failed')
out["checks"].append({"check":"route_graph","candidate_count":len(routes),"status":"passed","note":"Random routes/dates; asserted structural invariants only"})
if args.exercise_handling:
    require(before["DEF789"]["transportStatus"]=="NOT_RECEIVED", "Restart the disposable lab to restore seed data before this mutating check")
    payload={"completionTime":"2026-10-22 10:00","trackingId":"DEF789","eventType":"RECEIVE","unLocode":"CNHKG"}
    request=urllib.request.Request(BASE+"rest/handling/reports",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with opener.open(request,timeout=20) as r:require(r.status==204, r.status)
    for attempt in range(40):
        after=cargos()["DEF789"]
        if after["transportStatus"]=="IN_PORT" and after["lastKnownLocation"]=="CNHKG":break
        time.sleep(.5)
    else:raise AssertionError("Accepted report did not update cargo through JMS")
    out["checks"].append({"check":"asynchronous_handling","input":payload,"accepted_http":204,"before":before["DEF789"],"after":after,"status":"passed"})
else:
    out["checks"].append({"check":"asynchronous_handling","status":"not exercised; use --exercise-handling on fresh seed state"})
root=Path(__file__).resolve().parent.parent
path=root/"notes/evidence"/("runtime-smoke-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".json")
path.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"checks":out["checks"],"evidence":str(path)},indent=2))
