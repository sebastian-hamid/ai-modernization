#!/usr/bin/env python3
"""Run limited real Cargo Tracker migration checks in a disposable lab runtime."""
from pathlib import Path
import hashlib,http.cookiejar,json,re,secrets,shutil,subprocess,tempfile,time,urllib.request,urllib.error,urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
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

def route_date(value):
    # JSON-B in the pinned lab serializes java.util.Date with a UTC region suffix.
    if value.endswith("[UTC]"):
        value=value[:-5]
        parsed=datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds()!=0:raise ValueError("UTC suffix disagrees with offset")
        return parsed
    if "[" in value or "]" in value:raise ValueError("Unsupported date region")
    return datetime.fromisoformat(value)

def route_semantics(body):
    """Validate the sample planner response, not a claim of real timetable optimization."""
    try:
        values=json.loads(body)
        if not isinstance(values,list) or not values:return False
        for route in values:
            edges=route.get("transitEdges")
            if not isinstance(edges,list) or not edges or edges[0].get("fromUnLocode")!="CNHKG" or edges[-1].get("toUnLocode")!="FIHEL":return False
            previous_arrival=None
            for index,edge in enumerate(edges):
                if not all(isinstance(edge.get(key),str) and edge[key] for key in ["fromUnLocode","toUnLocode","voyageNumber","fromDate","toDate"]):return False
                if not re.fullmatch("[A-Z]{2}[A-Z0-9]{3}",edge["fromUnLocode"]) or not re.fullmatch("[A-Z]{2}[A-Z0-9]{3}",edge["toUnLocode"]):return False
                if index and edges[index-1]["toUnLocode"]!=edge["fromUnLocode"]:return False
                departure=route_date(edge["fromDate"]);arrival=route_date(edge["toDate"])
                if departure.tzinfo is None or arrival.tzinfo is None or departure>=arrival or (previous_arrival is not None and departure<previous_arrival):return False
                previous_arrival=arrival
        return True
    except (ValueError,TypeError,KeyError,AttributeError):return False

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
        def payload_absent(body):
            return not any(marker in body for marker in ["trackingId","ABC123","DEF789","JKL567","MNO456","Hong Kong","Helsinki"])
        private_resources={
            "PRIVATE-01":"WEB-INF/faces-config.xml","PRIVATE-02":"WEB-INF/glassfish-web.xml",
            "PRIVATE-03":"WEB-INF/web.xml","PRIVATE-04":"WEB-INF/weblogic.xml","PRIVATE-05":"booking/todo.txt"}
        packaged_entries=set(command("docker","exec",container,"jar","tf","/opt/jboss/wildfly/standalone/deployments/cargo-tracker.war").splitlines())
        report["private_resource_packaging"]={surface:path in packaged_entries for surface,path in private_resources.items()}
        def private_payload_absent(body):
            return payload_absent(body) and not any(marker in body for marker in ["<faces-config","<web-app","<glassfish-web-app","<weblogic-web-app","net.java.cargotracker"])
        for actor,who in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
            opener=sessions[who][1] if who else anonymous
            status,body,_=request(opener,"rest/cargo")
            observation={"supported":True,"status":status}
            if who:
                values=json.loads(body)
                meaningful=isinstance(values,list) and {"ABC123","DEF789","JKL567","MNO456"}.issubset({cargo["trackingId"] for cargo in values})
                check("Catalogue monitoring semantics: "+actor,status==200 and meaningful)
                observation.update({"identity":report["identities"][who],"semantic_success":meaningful})
            else:
                check("Catalogue anonymous monitoring denial has no payload",status==401 and payload_absent(body))
                observation["protected_payload_absent"]=payload_absent(body)
            head_status,head_body,_=request(opener,"rest/cargo",method="HEAD")
            check("Catalogue monitoring HEAD: "+actor,head_status==(200 if who else 401) and head_body=="")
            observation.update({"head_status":head_status,"head_body_empty":head_body==""})
            report["access_observations"]["API-01::"+actor+"::active"]=observation
            for number,template in [("01","admin"),("02","public")]:
                status,body,_=request(opener,"WEB-INF/templates/common/"+template+".xhtml")
                check("Private template denied without cargo: "+template+" "+actor,status==404 and payload_absent(body))
                observation={"supported":True,"status":status,"protected_payload_absent":payload_absent(body)}
                if who:observation["identity"]=report["identities"][who]
                report["access_observations"]["PAGE-"+number+"::"+actor+"::active"]=observation
            for surface,path in private_resources.items():
                status,body,_=request(opener,path)
                absent=private_payload_absent(body)
                check("Private metadata/source denied: "+surface+" "+actor,status==404 and absent)
                observation={"supported":True,"status":status,"protected_payload_absent":absent,"resource_packaged":report["private_resource_packaging"][surface]}
                if who:observation["identity"]=report["identities"][who]
                report["access_observations"][surface+"::"+actor+"::active"]=observation
        def effects():
            processes=command("docker","exec",container,"jcmd","-l").splitlines()
            candidates=[line.split()[0] for line in processes if "org.jboss.as.standalone" in line or "jboss-modules.jar" in line]
            if len(candidates)!=1:raise RuntimeError("Cannot identify unique app JVM")
            text=command("docker","exec",container,"java","-cp","/opt/jboss/observer-client","ReadEffects",candidates[0])
            return json.loads(text)
        def settled():return settle_effects(effects)
        route_path="rest/graph-traversal/shortest-path?origin=CNHKG&destination=FIHEL&deadline=2030-12-31"
        def routing_payload_absent(body):
            return payload_absent(body) and not any(marker in body for marker in ["transitEdges","voyageNumber","CNHKG","FIHEL"])
        for actor,who in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
            code,body,_=request(sessions[who][1] if who else anonymous,route_path)
            allowed=who in {"operator","admin"}
            if allowed:
                semantic=route_semantics(body)
                check("Catalogue real routing result: "+actor,code==200 and semantic)
                observation={"supported":True,"status":code,"semantic_success":semantic,"identity":report["identities"][who]}
            else:
                absent=routing_payload_absent(body)
                check("Catalogue routing denial without route payload: "+actor,code==(403 if who else 401) and absent)
                observation={"supported":True,"status":code,"protected_payload_absent":absent}
                if who:observation["identity"]=report["identities"][who]
            report["access_observations"]["API-03::"+actor+"::active"]=observation
        def basic_route(username,password,path=route_path,raw_header=None):
            import base64
            header=raw_header or "Basic "+base64.b64encode((username+":"+password).encode()).decode()
            req=urllib.request.Request(base+path,headers={"Authorization":header})
            try:res=urllib.request.build_opener(NoRedirect()).open(req,timeout=10)
            except urllib.error.HTTPError as failure:res=failure
            with res:return res.status,res.read(),res.headers
        sequence_before=effects()["routing_identity"].get("sequence",0)
        code,route_body,route_headers=basic_route("routing",routing_password)
        check("Native scoped routing account allowed",code==200 and route_semantics(route_body))
        routing_identity=effects()["routing_identity"]
        check("Server-native routing identity and exact role observed",routing_identity.get("principal")=="routing" and routing_identity.get("roles")==["RoutingService"] and routing_identity.get("sequence")==sequence_before+1 and routing_identity.get("path")=="/rest/graph-traversal/shortest-path")
        report["routing_machine_identity"]=routing_identity
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
        route_policy=next(row for row in json.loads((ROOT/"specifications/access-policy-inventory.json").read_text())["interfaces"] if row["id"]=="API-03")
        report["access_observations"]["API-03-SCOPED::routing-service::active"]={"supported":True,"status":code,"semantic_success":route_semantics(route_body),"machine_identity_verified":True,"machine_scope":route_policy["internal_caller"],"native_identity":routing_identity}
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
        report["access_observations"]["API-02::Operator::active"]={"supported":True,"status":204,"identity":report["identities"]["operator"],"semantic_success":True,"authorized_effect_verified":True,"processing_evidence":{"database_changed":positive_effects["tables"]!=after_denied["tables"],"worker_invocations_observed":True}}
        report["cargo_before"]=before;report["cargo_after"]=after
        check("Administrator fixture starts away from FIHEL",next(c for c in initial if c["trackingId"]=="MNO456")["lastKnownLocation"]!="FIHEL")
        payload=json.dumps({"trackingId":"MNO456","eventType":"CUSTOMS","unLocode":"FIHEL","completionTime":"2030-01-02 10:00"}).encode()
        admin_before=settled()
        check("Administrator report accepted",handling("admin")==204)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            code,body,_=request(sessions["reader"][1],"rest/cargo")
            if code==200 and next(c for c in json.loads(body) if c["trackingId"]=="MNO456")["lastKnownLocation"]=="FIHEL":break
            time.sleep(.25)
        else:raise AssertionError("Administrator handling did not persist")
        check("Administrator real asynchronous handling effect",True)
        admin_after=settled()
        check("Administrator independent persisted handling effect",admin_after["tables"]!=admin_before["tables"] and any(q["MessagesAdded"]>admin_before["queues"][name]["MessagesAdded"] for name,q in admin_after["queues"].items()) and any("registerHandlingEvent" in name and count>admin_before["business_invocations"].get(name,0) for name,count in admin_after["business_invocations"].items()))
        report["admin_handling_effects"]={"before":admin_before,"after":admin_after}
        report["access_observations"]["API-02::Administrator::active"]={"supported":True,"status":204,"identity":report["identities"]["admin"],"semantic_success":True,"authorized_effect_verified":True}


        def stale_client(jar):
            saved=client()[1];saved.addheaders=[("Cookie","JSESSIONID="+next(c.value for c in jar if c.name=="JSESSIONID"))]
            return saved
        actors=[("Reader","reader"),("Operator","operator"),("Administrator","admin")]
        def revoked_api_requests(actor,who,opener,token,state,before_sample):
            check("Revoked server identity: "+actor+" "+state,request(opener,"session")[0]==401)
            pending={}
            status,body,_=request(opener,"rest/cargo")
            head_status,head_body,_=request(opener,"rest/cargo",method="HEAD")
            check("Revoked monitoring GET/HEAD: "+actor+" "+state,status==401 and payload_absent(body) and head_status==401 and head_body=="")
            pending["API-01::"+actor+"::"+state]={"supported":True,"status":status,"protected_payload_absent":payload_absent(body),"identity":report["identities"][who],"authenticated_before_revocation":True,"revocation_verified":True,"head_status":head_status,"head_body_empty":head_body==""}
            if who!="reader":
                status,body,_=request(opener,route_path)
                check("Revoked routing GET: "+actor+" "+state,status==401 and routing_payload_absent(body))
                pending["API-03::"+actor+"::"+state]={"supported":True,"status":status,"protected_payload_absent":routing_payload_absent(body),"identity":report["identities"][who],"authenticated_before_revocation":True,"revocation_verified":True}
                check("Revoked valid handling POST: "+actor+" "+state,handling_as(opener,token)==401)
                pending["API-02::"+actor+"::"+state]=dict(last_handling)
            return pending
        def record_revocations(pending,before_sample,after_sample,who):
            for case,observation in pending.items():
                if case.startswith("API-02::"):observation=denial_observation(observation,before_sample,after_sample,who,True)
                report["access_observations"][case]=observation
        report["lifecycle_effects"]={}
        for actor,who in actors:
            jar,opener,token=login(who);saved=stale_client(jar)
            check("Role lifecycle positive monitoring: "+actor,request(opener,"rest/cargo")[0]==200)
            check("Actual role logout: "+actor,request(opener,"logout",b"",token)[0]==204)
            baseline=settled()
            pending=revoked_api_requests(actor,who,saved,token,"logged_out",baseline)
            after_sample=settled()
            check("Logout independent effects unchanged: "+actor,baseline==after_sample)
            record_revocations(pending,baseline,after_sample,who)
            report["lifecycle_effects"][who+"_logged_out"]={"before":baseline,"after":after_sample}
        expiring={}
        for actor,who in actors:
            jar,opener,token=login(who)
            check("Expiry lifecycle positive monitoring: "+actor,request(opener,"rest/cargo")[0]==200)
            expiring[who]=(stale_client(jar),token)
        # Every saved identity is left idle for at least75s after the last login.
        for unused in range(5):time.sleep(15)
        for actor,who in actors:
            saved,token=expiring[who]
            baseline=settled()
            pending=revoked_api_requests(actor,who,saved,token,"expired",baseline)
            after_sample=settled()
            check("Expiry independent effects unchanged: "+actor,baseline==after_sample)
            record_revocations(pending,baseline,after_sample,who)
            report["lifecycle_effects"][who+"_expired"]={"before":baseline,"after":after_sample,"idle_wait_seconds_minimum":75}
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
