#!/usr/bin/env python3
"""Run limited real Cargo Tracker migration checks in a disposable lab runtime."""
from pathlib import Path
import hashlib,http.cookiejar,json,re,secrets,shutil,subprocess,tempfile,time,urllib.request,urllib.error,urllib.parse
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/".work/kan18"
NAME="ai-modernization-kan18"
IMAGE="ai-modernization-kan18:candidate"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def command(*args):return subprocess.check_output(args,stderr=subprocess.STDOUT,text=True,timeout=30).strip()
def finalize(container,paths,report):
    errors=[]
    if container:
        try:(WORK/"server.log").write_text(command("docker","logs",container))
        except Exception as error:errors.append("logs:"+type(error).__name__)
        try:
            command("docker","rm","-f",container)
            report["owned_container_removed"]=True
        except Exception as error:
            report["owned_container_removed"]=False
            errors.append("remove:"+type(error).__name__)
    for path in paths:
        try:
            if path.exists():path.unlink()
        except Exception as error:errors.append("private-cleanup:"+type(error).__name__)
    report["private_files_removed"]=all(not path.exists() for path in paths)
    report["cleanup_errors"]=errors
    if errors:report["status"]="FAIL"
    report["count"]=len(report["checks"])
    (WORK/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"checks":report["count"],"private_files_removed":report["private_files_removed"]}))
    return not errors

QUEUE_ATTRIBUTES={"MessageCount","DeliveringCount","ScheduledCount","MessagesAdded","MessagesAcknowledged","MessagesExpired","MessagesKilled","AcknowledgeAttempts"}
REQUIRED_QUEUES={"jms.queue."+name for name in ["HandlingEventRegistrationAttemptQueue","CargoHandledQueue","MisdirectedCargoQueue","DeliveredCargoQueue","RejectedRegistrationAttemptsQueue","DLQ","ExpiryQueue"]}
def validate_effects(snapshot):
    if not isinstance(snapshot,dict):raise RuntimeError("Invalid effects observation")
    tables=snapshot.get("tables");queues=snapshot.get("queues");calls=snapshot.get("business_invocations")
    if not isinstance(tables,dict) or not tables:raise RuntimeError("Missing database observation")
    for value in tables.values():
        if not isinstance(value,dict) or type(value.get("rows")) is not int or value["rows"]<0 or not re.fullmatch("[0-9a-f]{64}",str(value.get("sha256",""))):raise RuntimeError("Invalid database observation")
    if sum(value["rows"] for value in tables.values())==0:raise RuntimeError("Empty database observation")
    if not isinstance(queues,dict) or not REQUIRED_QUEUES.issubset(queues):raise RuntimeError("Missing broker observation")
    for queue in queues.values():
        if not isinstance(queue,dict) or not QUEUE_ATTRIBUTES.issubset(queue) or any(type(queue[a]) is not int or queue[a]<0 for a in QUEUE_ATTRIBUTES):raise RuntimeError("Invalid broker observation")
    if not isinstance(calls,dict) or not calls or any(type(n) is not int or n<0 for n in calls.values()):raise RuntimeError("Missing business invocation observation")
def settle_effects(capture,timeout=15,clock=time.monotonic,pause=time.sleep):
    limit=clock()+timeout;previous=None;equal=0
    while clock()<limit:
        current=capture();validate_effects(current)
        quiet=all(q["MessageCount"]==q["DeliveringCount"]==q["ScheduledCount"]==0 for q in current["queues"].values())
        equal=equal+1 if quiet and current==previous else 0
        if equal>=2:return current
        previous=current;pause(.5)
    raise RuntimeError("Independent observers did not settle")

def main(after_checks=None):
    WORK.mkdir(parents=True,exist_ok=True)
    private=WORK/"secrets";private.mkdir(exist_ok=True,mode=0o700);private.chmod(0o700)
    users=private/"application-users.properties";roles=private/"application-roles.properties";routing=private/"routing-client.properties"
    if users.exists() or roles.exists() or routing.exists():raise RuntimeError("Private files exist; inspect before reuse")
    if subprocess.run(["docker","inspect",NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise RuntimeError("Task container already exists")
    credentials={who:secrets.token_urlsafe(28) for who in ["reader","operator","admin"]}
    routing_password=secrets.token_urlsafe(28)
    container=None;checks=[]
    report={"task":"KAN-18/KAN-15","scope":"Real Cargo Tracker candidate: monitoring/handling/session plus Faces list/booking/details/destination routes","checks":checks,"status":"FAIL","identities":{},"access_observations":{}}
    def check(name,condition):
        checks.append({"name":name,"passed":bool(condition)})
        if not condition:raise AssertionError(name)
    def client():
        jar=http.cookiejar.CookieJar()
        return jar,urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),NoRedirect())
    base=None
    def request(opener,path,data=None,token=None,method=None):
        headers={}
        if token:headers["X-CSRF-Token"]=token
        if isinstance(data,dict):data=urllib.parse.urlencode(data).encode();headers["Content-Type"]="application/x-www-form-urlencoded"
        req=urllib.request.Request(base+path,data=data,headers=headers,method=method)
        try:res=opener.open(req,timeout=10)
        except urllib.error.HTTPError as error:res=error
        with res:return res.status,res.read().decode(),res.headers
    def login(who):
        jar,opener=client()
        code,body,_=request(opener,"login")
        match=re.search("name='csrf' value='([^']+)'",body);check("Login form with token: "+who,code==200 and match is not None)
        old=next(c.value for c in jar if c.name=="JSESSIONID")
        code,_,_=request(opener,"login",{"username":who,"password":credentials[who],"csrf":match[1]})
        check("Container login succeeds: "+who,code==303)
        new=next(c.value for c in jar if c.name=="JSESSIONID")
        check("Session ID rotates: "+who,old!=new)
        code,body,_=request(opener,"session")
        role={"reader":"Reader","operator":"Operator","admin":"Administrator"}[who]
        check("Server principal and role: "+who,code==200 and json.loads(body)["principal"]==who and role in json.loads(body)["roles"])
        identity=json.loads(body)
        report["identities"][who]={"server_verified":True,"principal":identity["principal"],"roles":identity["roles"]}
        return jar,opener,identity["csrf"]
    try:
        users.write_text("#$REALM_NAME=ApplicationRealm$\n"+"".join(who+"="+hashlib.md5((who+":ApplicationRealm:"+pw).encode()).hexdigest()+"\n" for who,pw in {**credentials,"routing":routing_password}.items()))
        roles.write_text("reader=Reader\noperator=Operator\nadmin=Administrator\nrouting=RoutingService\n")
        routing.write_text("username=routing\npassword="+routing_password+"\n")
        users.chmod(0o600);roles.chmod(0o600);routing.chmod(0o600)
        context=Path(tempfile.mkdtemp(prefix="context-",dir=WORK))
        for relative in ["candidate/security","candidate/cargotracker","tests/candidate-runtime"]:
            target=context/relative
            shutil.copytree(ROOT/relative,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns("target","__pycache__"))
        with (WORK/"image-build.log").open("w") as log:
            proc=subprocess.run(["docker","build","--progress=plain","-f",str(context/"tests/candidate-runtime/Dockerfile"),"-t",IMAGE,str(context)],stdout=log,stderr=subprocess.STDOUT)
        check("Pinned runtime fixture builds",proc.returncode==0)
        report["image_id"]=command("docker","image","inspect","--format","{{.Id}}",IMAGE)
        guard=subprocess.run(["docker","run","--rm",IMAGE],capture_output=True,text=True)
        check("Disposable image refuses absent opt-in",guard.returncode==2 and "Disposable lab opt-in required" in guard.stderr)
        container=command("docker","run","-d","--name",NAME,"--label","ai-modernization.task=KAN-18","--init","-e","DISPOSABLE_CANDIDATE_LAB=true","-p","127.0.0.1::8080","--mount",f"type=bind,src={private},dst=/run/kan18,readonly",IMAGE)
        with tempfile.TemporaryDirectory(prefix="domain-reports-",dir=WORK) as temporary:
            command("docker","cp",container+":/opt/jboss/lab-evidence/surefire",temporary+"/surefire")
            suites=[ET.parse(path).getroot() for path in Path(temporary).rglob("TEST-*.xml")]
            report["domain_tests"]={key:sum(int(suite.get(key,"0")) for suite in suites) for key in ["tests","failures","errors","skipped"]}
            report["domain_tests"]["empty_legacy_todo_retained"]=True
            check("35 candidate domain tests execute",report["domain_tests"]["tests"]==35 and all(report["domain_tests"][key]==0 for key in ["failures","errors","skipped"]))
        port=int(command("docker","port",container,"8080/tcp").rsplit(":",1)[1])
        base=f"http://127.0.0.1:{port}/cargo-tracker/"
        deadline=time.monotonic()+150
        anonymous=client()[1]
        while time.monotonic()<deadline:
            try:
                if request(anonymous,"login")[0]==200:break
            except OSError:pass
            time.sleep(1)
        else:raise RuntimeError("Fixture deployment not ready")
        check("Anonymous monitoring denied",request(anonymous,"rest/cargo")[0]==401)
        check("Anonymous handling denied",request(anonymous,"rest/handling/reports",b"{}")[0]==401)
        check("Anonymous operational page navigates to login",request(anonymous,"admin/dashboard.xhtml")[0]==303)
        check("Anonymous tracking endpoint denied",request(anonymous,"tracking")[0]==401)
        check("Private source note denied",request(anonymous,"booking/todo.txt")[0]==404)
        sessions={who:login(who) for who in credentials}
        route_path="rest/graph-traversal/shortest-path?origin=CNHKG&destination=FIHEL&deadline=2030-12-31"
        check("Anonymous routing API denied",request(anonymous,route_path)[0]==401)
        check("Reader routing API denied",request(sessions["reader"][1],route_path)[0]==403)
        check("Operator routing API allowed",request(sessions["operator"][1],route_path)[0]==200)
        check("Administrator routing API allowed",request(sessions["admin"][1],route_path)[0]==200)
        def basic_route(username,password,path=route_path,raw_header=None):
            import base64
            header=raw_header or "Basic "+base64.b64encode((username+":"+password).encode()).decode()
            req=urllib.request.Request(base+path,headers={"Authorization":header})
            try:res=urllib.request.build_opener(NoRedirect()).open(req,timeout=10)
            except urllib.error.HTTPError as failure:res=failure
            with res:return res.status,res.read(),res.headers
        code,_,route_headers=basic_route("routing",routing_password)
        check("Native scoped routing account allowed",code==200)
        from http.cookies import SimpleCookie
        cookie=SimpleCookie();cookie.load(route_headers.get("Set-Cookie",""))
        reusable=False
        if "JSESSIONID" in cookie:
            req=urllib.request.Request(base+route_path,headers={"Cookie":"JSESSIONID="+cookie["JSESSIONID"].value})
            try:res=urllib.request.build_opener(NoRedirect()).open(req,timeout=10)
            except urllib.error.HTTPError as rejected:res=rejected
            with res:reusable=res.status!=401
        check("Routing Basic retains no usable session",not reusable)
        check("Wrong routing service password denied",basic_route("routing","incorrect")[0]==401)
        check("Human Basic credentials cannot impersonate service",basic_route("operator",credentials["operator"])[0]==403)
        check("Malformed Basic rejected",basic_route("","",raw_header="Basic !!!")[0]==401)
        check("Routing identity cannot use monitoring API",basic_route("routing",routing_password,path="rest/cargo")[0]==401)
        check("Invalid route locations controlled",request(sessions["operator"][1],"rest/graph-traversal/shortest-path?origin=XXXXX&destination=FIHEL")[0]==400)
        check("Invalid route deadline controlled",request(sessions["operator"][1],"rest/graph-traversal/shortest-path?origin=CNHKG&destination=FIHEL&deadline=2030-02-30")[0]==400)

        def cargos(opener):
            code,body,_=request(opener,"rest/cargo")
            check("Authenticated monitoring",code==200)
            return json.loads(body)
        for who in ["operator","admin"]:cargos(sessions[who][1])
        initial=cargos(sessions["reader"][1])
        check("Original four seeded cargos",{"ABC123","DEF789","JKL567","MNO456"}.issubset({c["trackingId"] for c in initial}))
        before=next(c for c in initial if c["trackingId"]=="DEF789")
        payload=json.dumps({"trackingId":"DEF789","eventType":"RECEIVE","unLocode":"FIHEL","completionTime":"2030-01-01 10:00"}).encode()
        # Content type must be JSON on real handling path.
        last_handling={}
        def handling_as(opener,token=None):
            req=urllib.request.Request(base+"rest/handling/reports",data=payload,headers={"Content-Type":"application/json",**({"X-CSRF-Token":token} if token else {})})
            try:r=opener.open(req,timeout=10)
            except urllib.error.HTTPError as error:r=error
            with r:
                body=r.read().decode("utf-8",errors="replace")
                last_handling.update({"status":r.status,"protected_payload_absent":not any(marker in body for marker in ["trackingId","ABC123","DEF789","JKL567","MNO456","Hong Kong","Helsinki"])})
                return r.status

        def handling(who,token=True):
            return handling_as(sessions[who][1],sessions[who][2] if token is True else token or None)
        # A real rendered Operator booking view supplies a callback for cross-role replay.
        code,book_html,_=request(sessions["operator"][1],"admin/book.xhtml")
        book_state=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',book_html)
        check("Actual booking callback fixture renders",code==200 and book_state is not None)
        before_book=cargos(sessions["reader"][1])
        book_form={"booking":"booking","booking:origin":"CNHKG","booking:destination":"FIHEL","booking:deadline":"2030-12-31","booking:submit":"","jakarta.faces.ViewState":book_state[1]}
        def effects():
            processes=command("docker","exec",container,"jcmd","-l").splitlines()
            candidates=[line.split()[0] for line in processes if "org.jboss.as.standalone" in line or "jboss-modules.jar" in line]
            if len(candidates)!=1:raise RuntimeError("Cannot identify unique app JVM")
            text=command("docker","exec",container,"java","-cp","/opt/jboss/observer-client","ReadEffects",candidates[0])
            return json.loads(text)
        def settled():return settle_effects(effects)
        before_denied=settled()
        check("Anonymous valid handling denied",handling_as(anonymous)==401)
        anonymous_denial=dict(last_handling)
        check("Reader handling denied",handling("reader")==403)
        reader_denial=dict(last_handling)
        check("Operator handling requires CSRF",handling("operator",False)==403)
        check("Operator incorrect CSRF denied",handling("operator","incorrect")==403)
        check("Reader valid forged booking callback denied",request(sessions["reader"][1],"admin/book.xhtml",{**book_form,"csrf":sessions["reader"][2]})[0]==403)
        check("Operator missing-CSRF booking callback denied",request(sessions["operator"][1],"admin/book.xhtml",book_form)[0]==403)

        after_denied=settled()
        check("Denied REST reports leave independent DB queue invocation snapshots unchanged",before_denied==after_denied)
        report["scoped_denied_effects"]={"scope":"Anonymous/Reader/missing-or-wrong-CSRF handling POST; Reader/missing-CSRF booking callback","before":before_denied,"after":after_denied,"independent_snapshots_match":before_denied==after_denied}
        report["denied_write_absence_verified"]=False # Entire catalogue remains unverified.
        def denial_observation(response,before_sample,after_sample,who=None,revoked=False):
            fixture=container
            observation={"supported":True,**response,"effects":{"settled":True,"fixture_id":fixture,"before_fixture":fixture,"after_fixture":fixture,
                "before":{"database":before_sample["tables"],"queue":before_sample["queues"],"business_audit":before_sample["business_invocations"]},
                "after":{"database":after_sample["tables"],"queue":after_sample["queues"],"business_audit":after_sample["business_invocations"]}}}
            if who:observation["identity"]=report["identities"][who]
            if revoked:observation.update({"authenticated_before_revocation":True,"revocation_verified":True})
            return observation
        report["access_observations"]["API-02::anonymous::active"]=denial_observation(anonymous_denial,before_denied,after_denied)
        report["access_observations"]["API-02::Reader::active"]=denial_observation(reader_denial,before_denied,after_denied,"reader")


        check("Denied report leaves monitor unchanged",next(c for c in cargos(sessions["reader"][1]) if c["trackingId"]=="DEF789")==before)
        check("Denied booking callback leaves cargo list unchanged",cargos(sessions["reader"][1])==before_book)
        check("Operator report accepted",handling("operator")==204)
        deadline=time.monotonic()+30;after=before
        while time.monotonic()<deadline:
            code,body,_=request(sessions["reader"][1],"rest/cargo")
            if code==200:
                after=next(c for c in json.loads(body) if c["trackingId"]=="DEF789")
                if after["lastKnownLocation"]=="FIHEL" and after["transportStatus"]=="IN_PORT":break
            time.sleep(.25)
        check("Real JPA/JMS handling changes cargo",after!=before and after["lastKnownLocation"]=="FIHEL" and after["transportStatus"]=="IN_PORT")

        positive_effects=settled()
        check("DB observer detects allowed persisted handling",positive_effects["tables"]!=after_denied["tables"])
        check("Cumulative broker observer detects allowed processing",positive_effects["queues"]!=after_denied["queues"] and any(q["MessagesAdded"]>after_denied["queues"][name]["MessagesAdded"] for name,q in positive_effects["queues"].items()))
        check("Business invocation observer detects allowed processing",positive_effects["business_invocations"]!=after_denied["business_invocations"] and any("registerHandlingEvent" in name and count>after_denied["business_invocations"].get(name,0) for name,count in positive_effects["business_invocations"].items()))
        for worker in ["HandlingEventRegistrationAttemptConsumer","CargoHandledConsumer"]:
            check("MDB invocation observer connected: "+worker,any(worker+"#onMessage" in name and count>after_denied["business_invocations"].get(name,0) for name,count in positive_effects["business_invocations"].items()))
        report["scoped_denied_effects"]["positive_control"]=positive_effects
        report["cargo_before"]=before;report["cargo_after"]=after
        check("Administrator fixture starts away from FIHEL",next(c for c in initial if c["trackingId"]=="MNO456")["lastKnownLocation"]!="FIHEL")
        payload=json.dumps({"trackingId":"MNO456","eventType":"CUSTOMS","unLocode":"FIHEL","completionTime":"2030-01-02 10:00"}).encode()
        check("Administrator report accepted",handling("admin")==204)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            code,body,_=request(sessions["reader"][1],"rest/cargo")
            if code==200 and next(c for c in json.loads(body) if c["trackingId"]=="MNO456")["lastKnownLocation"]=="FIHEL":break
            time.sleep(.25)
        else:raise AssertionError("Administrator handling did not persist")
        check("Administrator real asynchronous handling effect",True)

        def stale_client(jar):
            saved=client()[1];saved.addheaders=[("Cookie","JSESSIONID="+next(c.value for c in jar if c.name=="JSESSIONID"))]
            return saved
        logout_jar,logout_actor,logout_token=login("operator")
        logout_replay=stale_client(logout_jar)
        check("Mutation-capable identity logout",request(logout_actor,"logout",b"",logout_token)[0]==204)
        logout_before=settled()
        check("Logged-out Operator identity revoked",request(logout_replay,"session")[0]==401)
        check("Logged-out valid handling replay denied",handling_as(logout_replay,logout_token)==401)
        logout_denial=dict(last_handling)
        logout_after=settled()
        check("Logout replay leaves independent effects unchanged",logout_before==logout_after)
        report["access_observations"]["API-02::Operator::logged_out"]=denial_observation(logout_denial,logout_before,logout_after,"operator",True)
        report["logout_denied_effects"]={"before":logout_before,"after":logout_after,"independent_snapshots_match":logout_before==logout_after}
        expiry_jar,expiry_actor,expiry_token=login("operator")
        expiry_replay=stale_client(expiry_jar)
        # Lab sessions are one minute. No HTTP request refreshes this isolated session.
        for unused in range(5):time.sleep(15)
        expiry_before=settled()
        check("Expired Operator identity revoked",request(expiry_replay,"session")[0]==401)
        check("Expired valid handling replay denied",handling_as(expiry_replay,expiry_token)==401)
        expiry_denial=dict(last_handling)
        expiry_after=settled()
        check("Expiry replay leaves independent effects unchanged",expiry_before==expiry_after)
        report["access_observations"]["API-02::Operator::expired"]=denial_observation(expiry_denial,expiry_before,expiry_after,"operator",True)
        report["expiry_denied_effects"]={"before":expiry_before,"after":expiry_after,"independent_snapshots_match":expiry_before==expiry_after,"idle_wait_seconds":75}
        sessions["reader"]=login("reader")
        jar,reader,csrf=sessions["reader"]
        stale=client()[1];stale.addheaders=[("Cookie","JSESSIONID="+next(c.value for c in jar if c.name=="JSESSIONID"))]
        check("Logout succeeds",request(reader,"logout",b"",csrf)[0]==204)
        check("Old authenticated cookie revoked",request(stale,"rest/cargo")[0]==401)
        if after_checks:after_checks(container,base,credentials,report)
        report["status"]="PASS"
    except Exception as error:
        report["error_type"]=type(error).__name__
        raise
    finally:
        if not finalize(container,[users,roles,routing],report):
            raise RuntimeError("Fixture cleanup incomplete; inspect sanitized results")

    return report

if __name__=="__main__":main()
