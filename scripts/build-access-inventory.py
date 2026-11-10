#!/usr/bin/env python3
"""Source-only access inventory; does not deploy controls or call a live app."""
from pathlib import Path
import hashlib
import json
import posixpath
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"experiments/legacy-cargotracker"
WEB=SOURCE/"src/main/webapp"
JAVA=SOURCE/"src/main/java"
COMMIT="57fc7b32d2597e43b5e0d454e707e0146de5258a"
OUT=ROOT/"specifications/access-policy-inventory.json"
READ=["Reader","Operator","Administrator"]
WRITE=["Operator","Administrator"]

def require(ok,message):
    if not ok:raise RuntimeError(message)

def active(text):
    return re.sub(r"<!--.*?-->",lambda m:"\n"*m[0].count("\n"),text,flags=re.S)

def policy(path):
    if path.startswith("WEB-INF/") or path.startswith("META-INF/"):
        return "internal-template",[],False,"Deny direct HTTP access for every identity; includes do not bypass caller checks"
    if path in {"index.xhtml","public/about.xhtml"}:
        return "public",READ,True,"Public landing/about only; exclude operational data from rendering"
    if path in {"error.xhtml","error_404.xhtml"}:
        return "sanitized-error",READ,True,"Only generic errors public; no cargo details, stack traces or secret/session echo"
    if path.startswith(("booking/","eventLogger/")) or path in {"mobile.xhtml","admin/route.xhtml","admin/selectItinerary.xhtml","admin/changeDestination.xhtml"}:
        return "operator",WRITE,False,"Guard GET/POST/AJAX and service mutation before loading data or changing flow state"
    if path.startswith(("admin/","public/track")):
        return "read",READ,False,"Guard rendering, fragments and AJAX; mixed views must additionally guard operator actions"
    raise RuntimeError("Unclassified application page: "+path)

def main():
    require(subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()==COMMIT,"Wrong source revision")
    require(not subprocess.check_output(["git","status","--porcelain"],cwd=SOURCE),"Historical source is modified")
    pages=[];callbacks=[];flows=[];digests={}
    attrs=re.compile(r"\b(action|actionListener|listener|completeMethod|outcome|onclick|onload)\s*=\s*([\"\x27])(.*?)\2",re.S)
    for p in sorted(WEB.rglob("*")):
        if not p.is_file():continue
        relative=p.relative_to(WEB).as_posix()
        if p.suffix in {".xhtml",".html",".htm"}:
            group,roles,anonymous,enforce=policy(relative)
            ident="PAGE-"+str(len(pages)+1).zfill(2)
            pages.append(dict(id=ident,path="/cargo-tracker/"+relative,source=p.relative_to(SOURCE).as_posix(),classification=group,allowed_roles=roles,anonymous=anonymous,enforcement=enforce,test_location="candidate HTTP/browser policy suite (KAN-14)",test_groups=["PAGE-DIRECT","JSF-AJAX","RENDER-NO-LEAK"],implemented=False))
            text=active(p.read_text())
            for m in attrs.finditer(text):
                expression=m[3]
                if m[1] in {"onclick","onload"} and "#{" not in expression:continue
                bound=re.search(r"#\{(\w+)\.(\w+)",expression)
                key=(bound[1]+"."+bound[2]) if bound else None
                mutation=key in {"bookingBackingBean.register","changeDestination.changeDestination","itinerarySelection.assignItinerary","eventBackingBean.handleEventSubmission","cargoAdmin.register","cargoAdmin.assignItinerary","cargoAdmin.changeDestination","registration.register"}
                operator=mutation or (key and key.startswith(("changeDestinationDialog.","itinerarySelection.","changeDestination.","bookingBackingBean.","eventBackingBean.","holderBean."))) or expression.startswith("booking")
                target_roles=WRITE if operator else roles
                callback_anonymous=False if key or operator else anonymous
                # Navigation inherits both source-view and destination constraints.
                # Relative outcomes on a Reader-visible view can lead to Operator-only pages.
                if not key and ":" not in expression and m[1] in {"action","outcome"}:
                    target=expression.split("?",1)[0]
                    target=posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join(posixpath.dirname(relative),target))
                    if not (WEB/target).is_file() and (WEB/(target+".xhtml")).is_file():target+=".xhtml"
                    if (WEB/target).is_file() and target.endswith((".xhtml",".html")):
                        _,destination_roles,destination_anonymous,_=policy(target)
                        if group=="internal-template":
                            target_roles=destination_roles
                            callback_anonymous=destination_anonymous
                        else:
                            target_roles=[role for role in target_roles if role in destination_roles]
                            callback_anonymous=callback_anonymous and destination_anonymous
                testgroup="DENIED-NO-SIDE-EFFECT" if mutation else "JSF-AJAX"
                callbacks.append(dict(id="ACTION-"+str(len(callbacks)+1).zfill(2),page_id=ident,source=p.relative_to(SOURCE).as_posix(),line=text[:m.start()].count("\n")+1,attribute=m[1],expression=expression,bean_method=key,domain_mutation=mutation,allowed_roles=target_roles,anonymous=callback_anonymous,direct_template_request_allowed=False if group=="internal-template" else None,enforcement="Authorize backing action/getter and business service before execution; never trust a hidden button",test_location="candidate browser/action policy suite (KAN-14)",test_groups=[testgroup,"SESSION-EXPIRED","DIRECT-REPLAY"],implemented=False))
                if mutation:callbacks[-1]["method"]="POST"
        if p.name.endswith("-flow.xml"):
            flows.append(dict(source=p.relative_to(SOURCE).as_posix(),path="/cargo-tracker/"+relative,allowed_roles=[],flow_entry_roles=WRITE,raw_metadata_http_allowed=False,anonymous=False,enforcement="Deny direct XML metadata to every HTTP caller; protect flow entry and each view/callback; flow-return targets are navigation, not permissions",test_location="candidate browser flow suite (KAN-14)",test_groups=["FLOW-BYPASS","SESSION-EXPIRED"],return_expressions=re.findall(r"<from-outcome>(.*?)</from-outcome>",active(p.read_text()),re.S)))
        if p.suffix in {".xhtml",".html",".xml"}:digests[p.relative_to(SOURCE).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    # Account for non-page files too: static candidates, internal metadata and source notes.
    auxiliary=[]
    for p in sorted(WEB.rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(WEB).as_posix()
        digests[p.relative_to(SOURCE).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
        if p.suffix in {".xhtml",".html",".htm"} or p.name.endswith("-flow.xml") or p.relative_to(WEB).parts[0] in {"resources","images"}:continue
        auxiliary.append(dict(path="/cargo-tracker/"+rel,source=p.relative_to(SOURCE).as_posix(),classification="private-metadata-or-source-note",allowed_roles=[],anonymous=False,enforcement="Deny direct access to metadata/source notes, including booking/todo.txt; no public default allow",test_location="candidate resource policy suite (KAN-14)",test_groups=["RESOURCE-BYPASS"]))
    # Include every Java source hash so newly added resource/callback annotations cannot be hidden.
    annotations=[];declared_rest={};declared_sockets=[]
    for p in sorted(JAVA.rglob("*.java")):
        text=p.read_text();rel=p.relative_to(SOURCE).as_posix();digests[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
        paths=re.findall(r'@Path\("([^"]+)"\)',text)
        if paths:
            cls=re.search(r'public class (\w+)',text)
            require(cls is not None,"Unresolved REST class")
            declared_rest[cls[1]]="".join(paths)
        declared_sockets.extend(re.findall(r'@ServerEndpoint\("([^"]+)"\)',text))
        for n,line in enumerate(text.splitlines(),1):
            if re.search(r"@(Path|ApplicationPath|ServerEndpoint|Schedule|Startup|MessageDriven|OnOpen|OnClose)\b|@Observes",line):
                annotations.append(dict(source=rel,line=n,declaration=line.strip()))
    for p in [SOURCE/"pom.xml",*sorted((SOURCE/"src/main/resources").rglob("*"))]:
        if p.is_file():digests[p.relative_to(SOURCE).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    require(declared_rest=={"CargoMonitoringService":"/cargo","HandlingReportService":"/handling/reports","GraphTraversalService":"/graph-traversal/shortest-path"},"REST declarations changed: classify before generating")
    require(declared_sockets==["/tracking"],"WebSocket declarations changed")
    interfaces=[
        dict(id="API-01",method="GET/HEAD",path="/cargo-tracker/rest/cargo",allowed_roles=READ,anonymous=False,entry="CargoMonitoringService.getAllCargo",service="Direct CargoRepository.findAll",test_groups=["API-READ","NO-LOGIN-HTML","RENDER-NO-LEAK"]),
        dict(id="API-02",method="POST",path="/cargo-tracker/rest/handling/reports",allowed_roles=WRITE,anonymous=False,entry="HandlingReportService.submitReport",service="ApplicationEvents.receivedHandlingEventRegistrationAttempt -> registration consumer/service",test_groups=["API-WRITE","DENIED-NO-SIDE-EFFECT","CSRF","SESSION-EXPIRED"]),
        dict(id="API-03",method="GET",path="/cargo-tracker/rest/graph-traversal/shortest-path",allowed_roles=WRITE,anonymous=False,entry="GraphTraversalService.findShortestPath",service="ExternalRoutingService.fetchRoutesForSpecification internal HTTP caller",internal_caller="Scoped routing service identity; exact credential propagation/capability mapping to resolve in KAN-13/KAN-15",test_groups=["INTERNAL-CALLER","API-READ","LEAST-PRIVILEGE"]),
        dict(id="WS-01",method="HTTP Upgrade / send / close",path="/cargo-tracker/tracking",allowed_roles=READ,anonymous=False,entry="RealtimeCargoTrackingService.onOpen/onCargoInspected/onClose",test_groups=["WS-UPGRADE","WS-ORIGIN","WS-DATA","SESSION-EXPIRED","WS-DISCONNECT"]),
    ]
    for row in interfaces:row.update(enforcement="Server HTTP/upgrade boundary plus application/repository/event boundary before access; no role claims from payload",test_location="candidate API/WebSocket policy suite (KAN-14)",implemented=False)
    background=[
        dict(id="BG-01",entry="UploadDirectoryScanner.processFiles -> EventFilesProcessorJob",control="Administrator controls enablement/trigger; disabled in candidate until controlled invocation is implemented",identity="Trusted scheduler/batch worker; no implied logged-in human principal",test_groups=["BATCH-TRIGGER","BATCH-FS","DENIED-NO-SIDE-EFFECT"]),
        dict(id="BG-02",entry="/tmp/uploads -> EventItemReader -> EventItemWriter; /tmp/archive and /tmp/failed",control="Administrator-controlled ingestion; OS/container filesystem ACLs restrict upload/archive/failed paths to dedicated worker and approved administration tooling",identity="Trusted filesystem producer and batch worker, not untrusted HTTP caller",test_groups=["BATCH-FS","BATCH-REPLAY","LEAST-PRIVILEGE"]),
        dict(id="BG-03",entry="HandlingEventRegistrationAttemptQueue -> HandlingEventRegistrationAttemptConsumer",control="Only authorized operator/admin submission adapters and trusted batch worker may enqueue; broker/JNDI access restricts arbitrary producers",identity="Dedicated server worker authority; human identity does not automatically propagate through ObjectMessage",test_groups=["JMS-PRODUCER","DENIED-NO-SIDE-EFFECT","BATCH-REPLAY"]),
        dict(id="BG-04",entry="CargoHandledQueue -> CargoHandledConsumer -> inspectCargo -> CargoInspected",control="Trusted registration-service producer and inspection worker; no public direct invocation",identity="Server worker; audit origin/correlation to be designed, not trusted role fields in payload",test_groups=["JMS-PRODUCER","WS-DATA","LEAST-PRIVILEGE"]),
        dict(id="BG-05",entry="DeliveredCargoQueue / MisdirectedCargoQueue / RejectedRegistrationAttemptsQueue consumers",control="Trusted producer/consumer bindings and sanitized restricted logs; rejection producer/final disposition still unverified",identity="Server workers",test_groups=["JMS-PRODUCER","LOG-NO-LEAK"]),
        dict(id="BG-06",entry="SampleDataGenerator.loadSampleData and ORM startup schema creation",control="Disable destructive reseeding/schema creation in deployed candidate; controlled installation/migration process only",identity="Deployment/migration identity separate from request users",test_groups=["STARTUP-NO-DELETE","LEAST-PRIVILEGE"],human_case_source="No human-triggerable reseed or schema-DDL entry point; startup-only sample generator and ORM schema action must remain disabled",machine_case_source="Flyway deployment migrations using schema_migrator; startup sample seeding and ORM schema generation remain disabled",machine_identity="Flyway schema migration with server-verified schema_migrator identity"),
    ]
    for row in background:row.update(allowed_roles=["Administrator"] if row["id"] in {"BG-01","BG-02"} else [],human_roles_apply_to="Controlled import initiation only; worker/deployment invocation has separate machine authority",anonymous=False,enforcement="Admin control plane plus least-privilege scheduler/broker/filesystem/deployment controls; not a servlet-role check on an MDB",test_location="candidate internal/batch/deployment policy suite (KAN-14 and later resilience tasks)",implemented=False)
    business=[
        ("SERVICE-01","BookingService.bookNewCargo / assignCargoToRoute / changeDestination",WRITE,"BookingBackingBean, Registration, CargoAdmin, facade and direct business invocation","DENIED-NO-SIDE-EFFECT"),
        ("SERVICE-02","BookingService.requestPossibleRoutesForCargo and routing facade",WRITE,"ItinerarySelection.load runs on GET/preRender as well as AJAX; internal routing identity required","INTERNAL-CALLER"),
        ("SERVICE-03","Read-only booking facade, CargoRepository/HandlingEventRepository reads",READ,"CargoDetails, ListCargo, Track, CargoMonitoringService and read getters","RENDER-NO-LEAK"),
        ("SERVICE-04","HandlingEventService.registerHandlingEvent / CargoInspectionService.inspectCargo",[],"Only trusted worker invocation; deny exposed request path; do not assume original caller roles propagate","JMS-PRODUCER"),
    ]
    services=[dict(id=i,entry=entry,allowed_roles=roles,anonymous=False,enforcement=notes,test_location="candidate application boundary suite (KAN-14)",test_groups=[group,"LEAST-PRIVILEGE"],implemented=False) for i,entry,roles,notes,group in business]
    result=dict(issue="KAN-12",source_commit=COMMIT,scope="Source inventory and desired-policy mapping only; no access control or candidate tests implemented",pages=pages,view_callbacks=callbacks,flows=flows,interfaces=interfaces,background=background,auxiliary_files=auxiliary,service_boundaries=services,annotation_inventory=annotations,source_sha256=digests,resource_policy=dict(source_paths=[p.relative_to(WEB).as_posix() for p in sorted(WEB.rglob('*')) if p.is_file() and p.relative_to(WEB).parts[0] in {'resources','images'}],enforcement="Public only after verifying static non-sensitive content required for login/public views; dynamic JSF resources must not bypass bean/action authentication",test_location="candidate resource policy suite (KAN-14)",test_groups=["STATIC-ALLOWLIST","RESOURCE-BYPASS"]),default_policy="Deny unclassified application entrypoints; require deliberate classification when source inventory changes")
    require(len(pages)==len(list(WEB.rglob('*.xhtml')))+len(list(WEB.rglob('*.html'))),"Page census mismatch")
    require(any(x['path'].endswith('/admin/mapFrame.html') for x in pages),"Missing iframe entrypoint")
    require({x['entry'].split('.')[0] for x in interfaces if x['id'].startswith('API')}=={'CargoMonitoringService','HandlingReportService','GraphTraversalService'},"REST inventory differs")
    OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(pages=len(pages),callbacks=len(callbacks),flows=len(flows),interfaces=len(interfaces),background=len(background),service_boundaries=len(services),static_files=len(result['resource_policy']['source_paths']),source_files_hashed=len(digests))))

if __name__=="__main__":main()
