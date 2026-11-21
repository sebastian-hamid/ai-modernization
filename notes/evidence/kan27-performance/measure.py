#!/usr/bin/env python3
import concurrent.futures, http.cookiejar, json, re, statistics, subprocess, threading, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PASSWORDS={}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
class FormParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.forms=[]; self.current=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.current={"id":a.get("id"),"action":a.get("action") or "","fields":{},"submits":[]}
            self.forms.append(self.current)
        elif self.current is not None and tag=="input" and a.get("name"):
            self.current["fields"][a["name"]]=a.get("value","")
            if a.get("type","").lower() in ("submit","image"):
                self.current["submits"].append((a["name"],a.get("value","")))
        elif self.current is not None and tag=="button" and a.get("name"):
            self.current["submits"].append((a["name"],a.get("value","")))
    def handle_endtag(self,tag):
        if tag=="form": self.current=None

def opener():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),NoRedirect())
def request(op,base,path,data=None,headers=None):
    req=urllib.request.Request(base+path,data=data,headers=headers or {})
    try:r=op.open(req,timeout=15)
    except urllib.error.HTTPError as e:r=e
    with r:return r.status,r.read()
def login(op,base,username):
    status,body=request(op,base,"login")
    token=re.search(rb"name='csrf' value='([^']+)'",body)
    if status!=200 or not token: raise RuntimeError("login form/token missing")
    payload=urllib.parse.urlencode({"username":username,"password":PASSWORDS[username],"csrf":token.group(1).decode()}).encode()
    status,_=request(op,base,"login",payload,{"Content-Type":"application/x-www-form-urlencoded"})
    if status!=303: raise RuntimeError("candidate login failed with %s"%status)
def operation(base,kind,candidate,op=None):
    client=op or opener()
    if kind=="catalogue":
        if candidate and op is None: login(client,base,"operator")
        status,body=request(client,base,"rest/cargo")
        if status!=200: raise RuntimeError("cargo list HTTP %s"%status)
        cargo=json.loads(body)
        ids={row.get("trackingId") for row in cargo}
        if len(cargo)<4 or not {"ABC123","DEF789","JKL567","MNO456"}.issubset(ids):
            raise RuntimeError("unexpected seed catalogue")
        return {"status":status,"cargo_count":len(cargo)}
    if kind=="tracking_form":
        status,body=request(client,base,"public/track.xhtml")
        if status!=200: raise RuntimeError("tracking page HTTP %s"%status)
        parser=FormParser();parser.feed(body.decode(errors="replace"))
        forms=[f for f in parser.forms if f["id"]=="trackingForm"]
        if len(forms)!=1 or not forms[0]["submits"]: raise RuntimeError("tracking form not found")
        form=forms[0]
        keys=[k for k in form["fields"] if "trackingId" in k and "Result" not in k]
        if len(keys)!=1: raise RuntimeError("tracking ID field not unique: "+repr(keys))
        form["fields"][keys[0]]="ABC123"
        name,value=form["submits"][0]
        form["fields"][name]=value
        target=urllib.parse.urljoin(base,form["action"] or "public/track.xhtml")
        if not target.startswith(base): raise RuntimeError("tracking form target escaped app base")
        path=target[len(base):]
        status,result=request(client,base,path,urllib.parse.urlencode(form["fields"]).encode(),{"Content-Type":"application/x-www-form-urlencoded"})
        text=result.decode(errors="replace")
        success_marker=("tracking-result" in text) if candidate else ('id="result"' in text and "<strong>ABC123</strong>" in text)
        if status!=200 or "ABC123" not in text or not success_marker:
            raise RuntimeError("tracking form did not return ABC123 (HTTP %s)"%status)
        return {"status":status,"tracking_id":"ABC123"}
    raise ValueError(kind)

def percentile(values,p):
    values=sorted(values)
    return values[max(0,(len(values)*p+99)//100-1)]
def summarize(values):
    return {"count":len(values),"min_ms":round(min(values),2),"p50_ms":round(percentile(values,50),2),
        "p95_ms":round(percentile(values,95),2),"max_ms":round(max(values),2),"mean_ms":round(statistics.mean(values),2)}
def run_single(base,kind,candidate,n,warmups):
    op=opener()
    if candidate and kind=="catalogue": login(op,base,"operator")
    for _ in range(warmups): operation(base,kind,candidate,op if kind=="catalogue" else None)
    values=[]
    for _ in range(n):
        t=time.perf_counter();operation(base,kind,candidate,op if kind=="catalogue" else None);values.append((time.perf_counter()-t)*1000)
    return values
def run_concurrent(base,kind,candidate,total,workers):
    per_worker=total//workers
    def worker():
        op=opener()
        if candidate and kind=="catalogue": login(op,base,"operator")
        samples=[]
        for _ in range(per_worker):
            t=time.perf_counter();operation(base,kind,candidate,op if kind=="catalogue" else None);samples.append((time.perf_counter()-t)*1000)
        return samples
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        groups=list(pool.map(lambda _:worker(),range(workers)))
    return [value for group in groups for value in group]

def stats(container_ids):
    if not container_ids:return []
    cmd=["docker","stats","--no-stream","--format","{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.PIDs}}"]+container_ids
    out=subprocess.run(cmd,capture_output=True,text=True,timeout=20,check=True).stdout.strip()
    return [line.split("|") for line in out.splitlines() if "|" in line]
class Sampler:
    def __init__(self,ids):
        self.ids=ids;self.samples=[];self.stop=threading.Event()
        self.thread=threading.Thread(target=self.run,daemon=True)
    def run(self):
        while not self.stop.is_set():
            try:self.samples.append({"at":datetime.now(timezone.utc).isoformat(),"values":stats(self.ids)})
            except Exception as e:self.samples.append({"error":type(e).__name__})
            self.stop.wait(.5)
    def start(self):self.thread.start()
    def close(self):self.stop.set();self.thread.join(timeout=10)

def benchmark(base,candidate,ids,label,samples,warmups,workers):
    report={"label":label,"base_url":base,"runtime_containers":ids,"resource_samples_before":stats(ids),"workloads":{}}
    for kind in ("catalogue","tracking_form"):
        sampler=Sampler(ids);sampler.start()
        seq=run_single(base,kind,candidate,samples,warmups)
        concurrent=run_concurrent(base,kind,candidate,samples,workers)
        sampler.close()
        report["workloads"][kind]={"sequential":summarize(seq),"concurrency_5":summarize(concurrent),
            "samples_ms":{"sequential":seq,"concurrency_5":concurrent},
            "resource_samples_during":sampler.samples,"resource_samples_after":stats(ids)}
    return report

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Measure the KAN-27 read-only local workload")
    parser.add_argument("--base",required=True)
    parser.add_argument("--candidate",action="store_true")
    parser.add_argument("--containers",required=True,help="comma-separated container names or IDs for coarse Docker stats")
    parser.add_argument("--label",required=True)
    parser.add_argument("--credentials-file",help="private JSON mapping operator to its password; required with --candidate")
    parser.add_argument("--samples",type=int,default=100)
    parser.add_argument("--warmups",type=int,default=20)
    parser.add_argument("--workers",type=int,default=5)
    parser.add_argument("--output",help="write report JSON to this path; defaults to stdout")
    args=parser.parse_args()
    if args.candidate:
        if not args.credentials_file:
            parser.error("--credentials-file is required with --candidate")
        PASSWORDS=json.loads(Path(args.credentials_file).read_text())
        if "operator" not in PASSWORDS:
            parser.error("credentials JSON must contain operator")
    if args.samples < 1 or args.warmups < 0 or args.workers < 1 or args.samples % args.workers:
        parser.error("samples must be positive and divisible by workers; warmups cannot be negative")
    report=benchmark(args.base.rstrip("/")+"/",args.candidate,args.containers.split(","),args.label,
                     args.samples,args.warmups,args.workers)
    rendered=json.dumps(report,indent=2)
    if args.output:
        Path(args.output).write_text(rendered+"\n")
    else:
        print(rendered)