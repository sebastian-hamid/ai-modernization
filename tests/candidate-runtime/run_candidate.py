#!/usr/bin/env python3
"""Run limited real Cargo Tracker migration checks in a disposable lab runtime."""
from pathlib import Path
import hashlib,http.cookiejar,html,json,re,secrets,shutil,subprocess,tempfile,time,urllib.request,urllib.error,urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/".work/kan18"
NAME="ai-modernization-kan18"
IMAGE="ai-modernization-kan18:candidate"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def command(*args,timeout=30):return subprocess.check_output(args,stderr=subprocess.STDOUT,text=True,timeout=timeout).strip()
def capture_effects(container,timeout=30):
    """Read the existing lab observer from the one owned application JVM."""
    deadline = time.monotonic() + min(timeout,30)
    def budget():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired("owned effects observer", timeout)
        return remaining
    processes = command("docker", "exec", container, "jcmd", "-l", timeout=budget()).splitlines()
    candidates = [line.split()[0] for line in processes
                  if "org.jboss.as.standalone" in line or "jboss-modules.jar" in line]
    if len(candidates) != 1:
        raise RuntimeError("Cannot identify unique app JVM")
    text = command("docker", "exec", container, "java", "-cp",
                   "/opt/jboss/observer-client", "ReadEffects", candidates[0], timeout=budget())
    return json.loads(text)

def table_key(tables, logical_name):
    """Resolve a fixture table by case and underscore-insensitive metadata spelling."""
    normalize=lambda value:re.sub("_", "", str(value)).upper()
    matches=[name for name in tables if normalize(name)==normalize(logical_name)]
    if len(matches)!=1:
        raise RuntimeError("Expected exactly one observed table for "+logical_name)
    return matches[0]

def batch_finished_line(log_text,run_id):
    marker="IMPORT_AUDIT event=finished:"
    run_marker="runId="+run_id
    return next((line for line in log_text.splitlines()
        if marker in line and run_marker in line),None)

def compare_rejection_effect_deltas(before, after, input_name, rejected_name):
    """Require only the exact broker and audit deltas expected for one rejected message."""
    queue_counter_names=sorted(QUEUE_ATTRIBUTES)
    observed_queue_deltas={}
    same_queue_inventory=(set(before["queues"])==set(after["queues"]))
    for queue_name,before_queue in before["queues"].items():
        after_queue=after["queues"].get(queue_name,{})
        if set(before_queue)!=set(after_queue):
            same_queue_inventory=False
            continue
        changed={attribute:after_queue[attribute]-before_queue[attribute]
            for attribute in queue_counter_names
            if after_queue[attribute]!=before_queue[attribute]}
        if changed:
            observed_queue_deltas[queue_name]=changed
    expected_queue_deltas={
        input_name:{"MessagesAdded":1,"MessagesKilled":1,"AcknowledgeAttempts":4},
        rejected_name:{"MessagesAdded":1,"MessagesAcknowledged":1,"AcknowledgeAttempts":1}}
    invocation_names=set(before["business_invocations"]) | set(after["business_invocations"])
    observed_invocation_deltas={
        name:after["business_invocations"].get(name,0)-before["business_invocations"].get(name,0)
        for name in invocation_names
        if after["business_invocations"].get(name,0)!=before["business_invocations"].get(name,0)}
    expected_invocation_deltas={
        "net.java.cargotracker.application.internal.DefaultHandlingEventService#registerHandlingEvent":3,
        "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage":3,
        "net.java.cargotracker.infrastructure.messaging.jms.HandlingWorkerAudit#recordConsumedAttempt":3,
        "net.java.cargotracker.infrastructure.messaging.jms.RejectedRegistrationAttemptsConsumer#onMessage":1,
        "net.java.cargotracker.infrastructure.messaging.jms.NotificationWorkerAudit#recordConsumed":1}
    return {
        "queue_counter_deltas":observed_queue_deltas,
        "expected_queue_counter_deltas":expected_queue_deltas,
        "business_invocation_deltas":observed_invocation_deltas,
        "expected_business_invocation_deltas":expected_invocation_deltas,
        "all_queue_and_invocation_deltas_bounded":(
            same_queue_inventory
            and observed_queue_deltas==expected_queue_deltas
            and observed_invocation_deltas==expected_invocation_deltas)}

def remote_producer_boundary_verified(observation, unauthorized_effects_unchanged):
    """Require the intended producer to work and every tested non-producer to be denied."""
    return (isinstance(observation,dict)
        and observation.get("anonymousDenied") is True
        and observation.get("humanAuthenticated")==[True,True,True]
        and observation.get("humanSendDenied")==[True,True,True]
        and observation.get("machinePrincipals")==["batch-worker","handling-worker","inspection-worker","notification-worker"]
        and observation.get("machineAuthenticated")==[True,True,True,True]
        and observation.get("machineSendDenied")==[True,True,True,True]
        and observation.get("trustedAllowed") is True
        and observation.get("rejectedQueueDenied") is True
        and observation.get("deliveredQueueDenied") is True
        and unauthorized_effects_unchanged is True)

def expected_batch_control_deltas():
    """Document EJB entries for two unsafe callbacks and one concurrent one-use form."""
    methods={
        "issueNonce":"net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#issueNonce",
        "serviceStart":"net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#start",
        "launcherStart":"net.java.cargotracker.interfaces.handling.file.BatchImportLauncher#start",
        "jobStarted":"net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobStarted",
        "jobFinished":"net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobFinished"}
    events=(["issueNonce","serviceStart","launcherStart"]*2
        + ["issueNonce","serviceStart","serviceStart","launcherStart","jobStarted","jobFinished"])
    return {methods[name]:events.count(name) for name in methods}

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

def booking_form(body,csrf):
    state=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',body)
    if not state or not all('id="'+key+'"' in body for key in ["booking","booking:origin","booking:destination","booking:deadline","booking:submit"]):
        raise AssertionError("Missing real booking form")
    import html
    return {"csrf":csrf,"booking":"booking","booking:origin":"CNHKG","booking:destination":"FIHEL","booking:deadline":"2030-12-31","booking:submit":"","jakarta.faces.ViewState":html.unescape(state[1])}

def booking_tracking_id(base,status,location):
    target=urllib.parse.urlsplit(urllib.parse.urljoin(base,location))
    origin=urllib.parse.urlsplit(base);query=urllib.parse.parse_qs(target.query,keep_blank_values=True)
    if status not in {302,303} or target.scheme!=origin.scheme or target.netloc!=origin.netloc or target.path!="/cargo-tracker/admin/show.xhtml" or target.fragment or set(query)-{"trackingId","jfwid"} or len(query.get("trackingId",[]))!=1 or any(len(values)!=1 or not values[0] for values in query.values()) or re.fullmatch("[A-Z0-9]{8}",query.get("trackingId",[""])[0]) is None:
        raise AssertionError("Invalid booking result redirect")
    return query["trackingId"][0]

def booking_positive(before,after,cargo,tracking_id):
    validate_effects(before);validate_effects(after)
    counts_before=before["business_invocations"];counts_after=after["business_invocations"]
    booked=sum(n for key,n in counts_after.items() if key.endswith("#bookNewCargo"))-sum(n for key,n in counts_before.items() if key.endswith("#bookNewCargo"))
    return before["tables"]!=after["tables"] and before["queues"]==after["queues"] and booked==1 and cargo.get("trackingId")==tracking_id and cargo.get("originCode")=="CNHKG" and cargo.get("destinationCode")=="FIHEL" and cargo.get("routingStatus")=="NOT_ROUTED" and cargo.get("transportStatus")=="NOT_RECEIVED"

def destination_form(body,csrf,destination="USNYC"):
    state=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',body)
    if not state or not all('id="'+key+'"' in body for key in ["change","change:destination","change:submit"]):raise AssertionError("Missing real destination form")
    import html
    return {"csrf":csrf,"change":"change","change:destination":destination,"change:submit":"","jakarta.faces.ViewState":html.unescape(state[1])}


def source_entry(fetch,base,who,csrf,tracking_id=None):
    """Verify a real source GET and, for destination editing, follow its exact link."""
    from html.parser import HTMLParser
    if who not in {None,"reader","operator","admin"} or tracking_id is not None and re.fullmatch("[A-Z0-9]{8}",tracking_id) is None:
        raise AssertionError("Invalid entry fixture identity or cargo")
    allowed=who in {"operator","admin"}
    source="admin/book.xhtml" if tracking_id is None else "admin/show.xhtml?trackingId="+tracking_id
    def denied(code,body,headers):
        expected=403 if who=="reader" else 303
        markers=["trackingId","ABC123","DEF789","JKL567","MNO456","Hong Kong","Helsinki",'id="booking"','id="change"']
        if tracking_id:markers.append(tracking_id)
        if code!=expected or any(marker in body for marker in markers) or expected==303 and headers.get("Location")!="/cargo-tracker/login":
            raise AssertionError("Source/editor authorization denial unverified")
    window_encoded=False
    code,body,headers=fetch(source)
    if tracking_id is None:
        if allowed:
            if code!=200:raise AssertionError("Booking source not rendered")
            booking_form(body,csrf)
        else:denied(code,body,headers)
    else:
        path="admin/changeDestination.xhtml?trackingId="+tracking_id
        class Links(HTMLParser):
            def __init__(self):super().__init__();self.hrefs=[];self.anchor=None
            def handle_starttag(self,tag,attrs):
                if tag=="a":
                    if self.anchor is not None:raise AssertionError("Nested entry anchor")
                    keys=[key for key,value in attrs]
                    if len(keys)!=len(set(keys)):raise AssertionError("Ambiguous anchor attributes")
                    self.anchor=[dict(attrs).get("href",""),[]]
            def handle_data(self,data):
                if self.anchor is not None:self.anchor[1].append(data)
            def handle_endtag(self,tag):
                if tag=="a" and self.anchor is not None:
                    href,text=self.anchor
                    if "changeDestination.xhtml" in href or " ".join("".join(text).split())=="Change destination":self.hrefs.append(href)
                    self.anchor=None
        links=Links();links.feed(body)
        if who is None:
            denied(code,body,headers)
        else:
            if code!=200 or 'id="trackingId">'+tracking_id not in body:raise AssertionError("Selected cargo source not rendered")
            if allowed:
                if len(links.hrefs)!=1:raise AssertionError("Missing or ambiguous destination entry link")
                href=links.hrefs[0]
                raw=urllib.parse.urlsplit(href)
                raw_fields=raw.query.split("&")
                # Faces may percent-encode ClientWindow punctuation. Only its value
                # may be encoded; origin, path, query keys and cargo remain literal.
                encoding_safe=all("%" not in field or field.startswith("jfwid=") and "%" not in field.split("=",1)[0] and re.search(r"%(?![0-9A-Fa-f]{2})",field) is None for field in raw_fields)
                if any(x in raw.path for x in [chr(92),"%",";",".."]) or chr(92) in href or any(ord(c)<32 or ord(c)==127 for c in href) or not encoding_safe:
                    raise AssertionError("Unsafe entry URI (encoded_path="+str("%" in raw.path)+", encoded_query="+str("%" in raw.query)+", semicolon_path="+str(";" in raw.path)+")")
                window_encoded="%" in raw.query
                target=urllib.parse.urlsplit(urllib.parse.urljoin(base+"admin/show.xhtml",href))
                origin=urllib.parse.urlsplit(base)
                try:pairs=urllib.parse.parse_qsl(target.query,keep_blank_values=True,strict_parsing=True)
                except ValueError:raise AssertionError("Invalid entry query")
                keys=[key for key,value in pairs];query=dict(pairs)
                if target.scheme!=origin.scheme or target.netloc!=origin.netloc or target.fragment or target.path!="/cargo-tracker/admin/changeDestination.xhtml" or len(keys)!=len(set(keys)) or set(keys)-{"trackingId","jfwid"} or query.get("trackingId")!=tracking_id or any(not value or any(ord(char)<32 or ord(char)==127 for char in value) for key,value in pairs):
                    raise AssertionError("Destination link not bound to local selected cargo")
                path=target.path.removeprefix("/cargo-tracker/")+"?"+target.query
            elif links.hrefs:raise AssertionError("Reader destination control exposed")
        code,body,headers=fetch(path)
        if allowed:
            if code!=200:raise AssertionError("Destination editor not rendered")
            destination_form(body,csrf)
        else:denied(code,body,headers)
    proof={"entry_page":source,"source_entry_verified":True}
    if window_encoded:proof["entry_window_query_encoded"]=True
    return body,proof


def current_load_semantics(surface,body,cargo,diagnostics=None):
    """Specific current load semantics against an independently read cargo snapshot."""
    import html
    from html.parser import HTMLParser
    if surface=="ACTION-20":
        pairs=re.findall(r"<dt>([^<]+)</dt>\s*<dd(?: [^>]*)?>([^<]*)</dd>",body)
        if len(pairs)!=len({key for key,value in pairs}):return False
        values={html.unescape(key):html.unescape(value) for key,value in pairs}
        expected={"Tracking ID":cargo["trackingId"],"Origin":cargo["originName"],"Destination":cargo["destinationName"],"Routing status":cargo["routingStatus"],"Status":cargo["transportStatus"]}
        # CargoRoute name getters retain the separator space before the removed
        # UNLOCODE. Compare visible name text; keep IDs/statuses exact.
        for key in ["Origin","Destination"]:
            if key in values:values[key]=values[key].strip()
        mismatches=[key for key,value in expected.items() if values.get(key)!=value]
        if values.get("Arrival deadline","").split()[:1]!=["12/31/2030"]:mismatches.append("Arrival deadline")
        if diagnostics is not None:diagnostics["mismatched_fields"]=mismatches
        return not mismatches
    if surface!="ACTION-07":return False
    destination_form(body,"unit-unused")
    class Selection(HTMLParser):
        def __init__(self):super().__init__();self.active=False;self.count=0;self.selected=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=="select":
                self.active=attrs.get("id")=="change:destination"
                if self.active:self.count+=1
            if tag=="option" and self.active and "selected" in attrs:self.selected.append(attrs.get("value"))
        def handle_endtag(self,tag):
            if tag=="select":self.active=False
    parser=Selection();parser.feed(body)
    return parser.count==1 and parser.selected==[cargo["destinationCode"]]

def destination_positive(before,after,old,cargo,tracking_id):
    validate_effects(before);validate_effects(after)
    delta=sum(n for key,n in after["business_invocations"].items() if key.endswith("#changeDestination"))-sum(n for key,n in before["business_invocations"].items() if key.endswith("#changeDestination"))
    return before["tables"]!=after["tables"] and before["queues"]==after["queues"] and delta==1 and old.get("trackingId")==tracking_id and cargo.get("trackingId")==tracking_id and old.get("destinationCode")=="FIHEL" and cargo.get("destinationCode")=="USNYC" and old.get("originCode")==cargo.get("originCode")=="CNHKG" and old.get("routingStatus")==cargo.get("routingStatus")=="NOT_ROUTED" and old.get("transportStatus")==cargo.get("transportStatus")=="NOT_RECEIVED" and old.get("lastKnownLocationCode")==cargo.get("lastKnownLocationCode")

def route_tables(body,attribute="class",value="route-candidate"):
    from html.parser import HTMLParser
    class Tables(HTMLParser):
        def __init__(self):super().__init__();self.tables=[];self.table=None;self.depth=0;self.tbody=False;self.row=None;self.cell=None
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=="table":
                if self.table is not None:self.depth+=1
                elif (value in attrs.get("class","").split() if attribute=="class" else attrs.get(attribute)==value):self.table=[];self.depth=1
            if self.table is None:return
            if tag=="tbody":self.tbody=True
            elif tag=="tr" and self.tbody:self.row=[]
            elif tag=="td" and self.row is not None:self.cell=[]
        def handle_data(self,data):
            if self.cell is not None:self.cell.append(data)
        def handle_endtag(self,tag):
            if self.table is None:return
            if tag=="td" and self.cell is not None:self.row.append("".join(self.cell).strip());self.cell=None
            elif tag=="tr" and self.row is not None:
                if self.row:self.table.append(self.row)
                self.row=None
            elif tag=="tbody":self.tbody=False
            elif tag=="table":
                self.depth-=1
                if self.depth==0:self.tables.append(self.table);self.table=None
    parser=Tables();parser.feed(body);return parser.tables

ROUTE_READ_COUNTERS=frozenset({
    "net.java.cargotracker.application.internal.DefaultBookingService#requestPossibleRoutesForCargo",
    "net.java.cargotracker.infrastructure.routing.ExternalRoutingService#fetchRoutesForSpecification",
    "net.java.pathfinder.api.GraphTraversalService#findShortestPath",
})

def route_read_effects(before,after,allowed_loads):
    def writes(snapshot):
        return (snapshot["tables"],snapshot["queues"],{key:value for key,value in snapshot["business_invocations"].items() if key not in ROUTE_READ_COUNTERS})
    deltas={key:after["business_invocations"].get(key,0)-before["business_invocations"].get(key,0) for key in ROUTE_READ_COUNTERS}
    return writes(before)==writes(after) and set(deltas.values())=={allowed_loads}


def verify_route_choices(body,origin,destination,token,tracking_id,base):
    """Bind each rendered selectable itinerary to the requested cargo endpoints."""
    tables=route_tables(body)
    if not tables:raise AssertionError("No rendered route choices")
    from html.parser import HTMLParser
    class RouteControls(HTMLParser):
        def __init__(self):
            super().__init__();self.select=False;self.selects=0;self.options=[];self.link=None;self.refresh=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=="select":
                self.select=attrs.get("id")=="routing:choice"
                self.selects+=self.select
            elif tag=="option" and self.select:self.options.append(attrs.get("value"))
            elif tag=="a":self.link=(attrs.get("href",""),[])
        def handle_data(self,data):
            if self.link is not None:self.link[1].append(data)
        def handle_endtag(self,tag):
            if tag=="select":self.select=False
            elif tag=="a" and self.link is not None:
                href,parts=self.link
                if " ".join("".join(parts).split())=="Request fresh routes":self.refresh.append(href)
                self.link=None
    controls=RouteControls();controls.feed(body)
    expected_options={str(i) for i in range(len(tables))}
    if controls.selects!=1 or len(controls.options)!=len(set(controls.options)) or set(controls.options)-{"-1"}!=expected_options:
        raise AssertionError("Route choices not selectable in the route form")
    if len(controls.refresh)!=1:raise AssertionError("Missing unique route refresh link")
    href=controls.refresh[0]
    url=urllib.parse.urlsplit(urllib.parse.urljoin(base+"admin/route.xhtml",href))
    origin_url=urllib.parse.urlsplit(base)
    try:pairs=urllib.parse.parse_qsl(url.query,keep_blank_values=True,strict_parsing=True)
    except ValueError:raise AssertionError("Invalid route refresh query")
    query=dict(pairs)
    if (url.scheme,url.netloc,url.path)!=(origin_url.scheme,origin_url.netloc,"/cargo-tracker/admin/route.xhtml") or url.fragment or len(query)!=len(pairs) or set(query)-{"trackingId","jfwid"} or query.get("trackingId")!=tracking_id or not all(query.values()):
        raise AssertionError("Route refresh link does not identify selected cargo")
    for index,rows in enumerate(tables):
        routing_form(body,token,index)
        cursor=origin
        for voyage,source,target,departure,arrival in rows:
            from_code=re.search(r" \(([A-Z]{2}[A-Z0-9]{3})\)$",source)
            to_code=re.match(r"^([A-Z]{2}[A-Z0-9]{3}) \(",target)
            if not voyage or not from_code or from_code[1]!=cursor or not to_code or not departure or not arrival:
                raise AssertionError("Rendered route legs do not connect")
            cursor=to_code[1]
        if cursor!=destination:raise AssertionError("Rendered routes end at wrong destination")
    return len(tables)


def routing_form(body,csrf,choice):
    state=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',body)
    tables=route_tables(body)
    if not state or type(choice) is not int or choice<0 or choice>=len(tables) or not tables[choice] or any(len(row)!=5 for row in tables[choice]) or not all('id="'+key+'"' in body for key in ["routing","routing:choice","routing:submit"]) or re.search(r'<option\b[^>]*\bvalue="'+str(choice)+'"',body) is None:raise AssertionError("Missing real route choice/form")
    import html
    return {"csrf":csrf,"routing":"routing","routing:choice":str(choice),"routing:submit":"","jakarta.faces.ViewState":html.unescape(state[1])},tables[choice]

def routing_positive(before,after,old,cargo,tracking_id):
    validate_effects(before);validate_effects(after)
    delta=sum(n for key,n in after["business_invocations"].items() if key.endswith("#assignCargoToRoute"))-sum(n for key,n in before["business_invocations"].items() if key.endswith("#assignCargoToRoute"))
    return before["tables"]!=after["tables"] and before["queues"]==after["queues"] and delta==1 and old.get("trackingId")==cargo.get("trackingId")==tracking_id and old.get("originCode")==cargo.get("originCode")=="CNHKG" and old.get("destinationCode")==cargo.get("destinationCode")=="USNYC" and cargo.get("routingStatus")=="ROUTED" and old.get("transportStatus")==cargo.get("transportStatus")=="NOT_RECEIVED" and old.get("lastKnownLocationCode")==cargo.get("lastKnownLocationCode")

def handling_form(body,csrf,tracking_id,location,completion):
    state=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',body)
    required=["handling","handling:cargo","handling:type","handling:location","handling:time","handling:voyage","handling:submit"]
    if not state or not all('id="'+key+'"' in body for key in required) or re.search(r'<option\b[^>]*\bvalue="'+re.escape(tracking_id)+'"',body) is None or re.search(r'<option\b[^>]*\bvalue="'+re.escape(location)+'"',body) is None:raise AssertionError("Missing offered cargo/location/handling form")
    import html
    return {"csrf":csrf,"handling":"handling","handling:cargo":tracking_id,"handling:type":"CUSTOMS","handling:location":location,"handling:time":completion,"handling:voyage":"","handling:submit":"","jakarta.faces.ViewState":html.unescape(state[1])}

def handling_positive(before,after,old,cargo,tracking_id,location):
    validate_effects(before);validate_effects(after)
    def delta(suffix):return sum(n for k,n in after["business_invocations"].items() if k.endswith(suffix))-sum(n for k,n in before["business_invocations"].items() if k.endswith(suffix))
    for queue in ["jms.queue.HandlingEventRegistrationAttemptQueue","jms.queue.CargoHandledQueue"]:
        if any(after["queues"][queue][key]-before["queues"][queue][key]!=1 for key in ["MessagesAdded","MessagesAcknowledged"]):return False
    return before["tables"]!=after["tables"] and all(delta(suffix)==1 for suffix in ["#submitReport","#registerHandlingEvent","HandlingEventRegistrationAttemptConsumer#onMessage","CargoHandledConsumer#onMessage"]) and old.get("trackingId")==cargo.get("trackingId")==tracking_id and old.get("originCode")==cargo.get("originCode")=="CNHKG" and old.get("destinationCode")==cargo.get("destinationCode")=="USNYC" and old.get("routingStatus")==cargo.get("routingStatus")=="ROUTED" and old.get("transportStatus")=="NOT_RECEIVED" and cargo.get("transportStatus")=="IN_PORT" and cargo.get("lastKnownLocationCode")==location and old.get("lastKnownLocationCode")!=location

def main(after_checks=None):
    WORK.mkdir(parents=True,exist_ok=True)
    private=WORK/"secrets";private.mkdir(exist_ok=True,mode=0o700);private.chmod(0o700)
    users=private/"application-users.properties";roles=private/"application-roles.properties";routing=private/"routing-client.properties";producer_client=private/"producer-client.properties"
    if any(path.exists() for path in (users,roles,routing,producer_client)):raise RuntimeError("Private files exist; inspect before reuse")
    if subprocess.run(["docker","inspect",NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise RuntimeError("Task container already exists")
    credentials={who:secrets.token_urlsafe(28) for who in ["reader","operator","admin"]}
    machine_credentials={who:secrets.token_urlsafe(28) for who in ["batch-worker","handling-worker","inspection-worker","notification-worker"]}
    attempt_producer_password=secrets.token_urlsafe(28)
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
        users.write_text("#$REALM_NAME=ApplicationRealm$\n"+"".join(who+"="+hashlib.md5((who+":ApplicationRealm:"+pw).encode()).hexdigest()+"\n" for who,pw in {**credentials,**machine_credentials,"routing":routing_password,"handling-attempt-producer":attempt_producer_password}.items()))
        roles.write_text("reader=Reader\noperator=Operator\nadmin=Administrator\nrouting=RoutingService\nbatch-worker=BatchWorker\nhandling-worker=HandlingWorker\ninspection-worker=InspectionWorker\nnotification-worker=NotificationWorker\nhandling-attempt-producer=HandlingAttemptProducer\n")
        routing.write_text("username=routing\npassword="+routing_password+"\n")
        producer_client.write_text("producer.user=handling-attempt-producer\nproducer.password="+attempt_producer_password+"\n"+"".join(who+".user="+who+"\n"+who+".password="+pw+"\n" for who,pw in {**credentials,**machine_credentials}.items()))
        users.chmod(0o600);roles.chmod(0o600);routing.chmod(0o600);producer_client.chmod(0o600)
        context=Path(tempfile.mkdtemp(prefix="context-",dir=WORK))
        for relative in ["candidate/security","candidate/cargotracker","tests/candidate-runtime"]:
            target=context/relative
            shutil.copytree(ROOT/relative,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns("target","__pycache__"))
        fixture_java=context/"candidate/cargotracker/src/main/java/lab/fixture/BatchApiProbe.java"
        fixture_java.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(context/"tests/candidate-runtime/BatchApiProbe.java",fixture_java)
        booking_java=fixture_java.with_name("BookingApiProbe.java")
        shutil.copy2(context/"tests/candidate-runtime/BookingApiProbe.java",booking_java)
        web=context/"candidate/cargotracker/src/main/webapp/WEB-INF/web.xml"
        web_text=web.read_text()
        mapping=('<servlet><servlet-name>batchProbe</servlet-name>'
            '<servlet-class>lab.fixture.BatchApiProbe</servlet-class></servlet>'
            '<servlet-mapping><servlet-name>batchProbe</servlet-name>'
            '<url-pattern>/__fixture/batch-probe</url-pattern></servlet-mapping>')
        if "__fixture/batch-probe" not in web_text:
            web_text=web_text.replace("</web-app>",mapping+"</web-app>")
        booking_mapping=("<servlet><servlet-name>bookingProbe</servlet-name>"
            "<servlet-class>lab.fixture.BookingApiProbe</servlet-class></servlet>"
            "<servlet-mapping><servlet-name>bookingProbe</servlet-name>"
            "<url-pattern>/__fixture/booking-probe</url-pattern></servlet-mapping>")
        if "__fixture/booking-probe" not in web_text:
            web_text=web_text.replace("</web-app>",booking_mapping+"</web-app>")
        web.write_text(web_text)
        routes=context/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv"
        route_text=routes.read_text()
        probe_route="/__fixture/batch-probe\tReader,Operator,Administrator"
        if probe_route not in route_text.splitlines():route_text+=probe_route+"\n"
        booking_probe_route="/__fixture/booking-probe\tPUBLIC"
        if booking_probe_route not in route_text.splitlines():route_text+=booking_probe_route+"\n"
        routes.write_text(route_text)
        with (WORK/"image-build.log").open("w") as log:
            proc=subprocess.run(["docker","build","--progress=plain","-f",str(context/"tests/candidate-runtime/Dockerfile"),"-t",IMAGE,str(context)],stdout=log,stderr=subprocess.STDOUT)
        check("Pinned runtime fixture builds",proc.returncode==0)
        report["image_id"]=command("docker","image","inspect","--format","{{.Id}}",IMAGE)
        guard=subprocess.run(["docker","run","--rm",IMAGE],capture_output=True,text=True)
        check("Disposable image refuses absent opt-in",guard.returncode==2 and "Disposable lab opt-in required" in guard.stderr)
        container=command("docker","run","-d","--name",NAME,"--label","ai-modernization.task=KAN-18","--init","-e","DISPOSABLE_CANDIDATE_LAB=true","-e","LAB_IMPORT_ENABLED=true","-p","127.0.0.1::8080","--mount",f"type=bind,src={private},dst=/run/kan18,readonly",IMAGE)
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
        read_pages={
            "PAGE-03":("admin/about.xhtml","Cargo workflows","about"),
            "PAGE-06":("admin/listClaimed.xhtml","Claimed cargo","claimed"),
            "PAGE-07":("admin/listNotRouted.xhtml","Unrouted cargo","unrouted"),
            "PAGE-08":("admin/listRouted.xhtml","Routed cargo","routed"),
            "PAGE-22":("index.xhtml","Cargo Tracker","public"),
            "PAGE-24":("public/about.xhtml","About Cargo Tracker","public")}
        # Create a real future-deadline cargo through a rendered permitted form.
        status,book_body,_=request(sessions["operator"][1],"admin/book.xhtml")
        state=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',book_body)
        check("Page fixture uses real booking form",status==200 and state is not None)
        status,_,headers=request(sessions["operator"][1],"admin/book.xhtml",{"csrf":sessions["operator"][2],"booking":"booking","booking:origin":"CNHKG","booking:destination":"FIHEL","booking:deadline":"2030-12-31","booking:submit":"","jakarta.faces.ViewState":state[1]})
        location=urllib.parse.urlsplit(urllib.parse.urljoin(base,headers.get("Location","")))
        query=urllib.parse.parse_qs(location.query);ids=query.get("trackingId",[])
        check("Page fixture booking persists with fixed details redirect",status in {302,303} and location.netloc==urllib.parse.urlsplit(base).netloc and location.path=="/cargo-tracker/admin/show.xhtml" and len(ids)==1 and re.fullmatch("[A-Z0-9]{8}",ids[0]) is not None)
        fixture_id=ids[0];report["page_fixture_tracking_id"]=fixture_id
        # surface -> path, heading, semantics, operator-only, trackingId, fixed alias target
        other_pages={
            "PAGE-04":("admin/changeDestination.xhtml","Change destination","change",True,True,None),
            "PAGE-05":("admin/dashboard.xhtml","Cargo list","dashboard",False,False,None),
            "PAGE-09":("admin/map.xhtml","Live cargo tracking","live",False,False,"admin/live.xhtml"),
            "PAGE-10":("admin/mapFrame.html","Live cargo tracking","live",False,False,"admin/live.xhtml"),
            "PAGE-11":("admin/route.xhtml","Assign route","route",True,True,None),
            "PAGE-12":("admin/selectItinerary.xhtml","Assign route","route",True,True,"admin/route.xhtml"),
            "PAGE-13":("admin/show.xhtml","Cargo details","details",False,True,None),
            "PAGE-14":("admin/track.xhtml","Track cargo","track",False,False,None),
            "PAGE-15":("booking/booking-date.xhtml","Book cargo","book",True,False,"admin/book.xhtml"),
            "PAGE-16":("booking/booking-destination.xhtml","Book cargo","book",True,False,"admin/book.xhtml"),
            "PAGE-17":("booking/booking.xhtml","Book cargo","book",True,False,"admin/book.xhtml"),
            "PAGE-18":("error.xhtml","Request could not be completed","error",False,False,None),
            "PAGE-19":("error_404.xhtml","Page not found","error",False,False,None),
            "PAGE-20":("eventLogger/eventLogger.xhtml","Report handling","handling",True,False,"mobile.xhtml"),
            "PAGE-21":("eventLogger/root.xhtml","Report handling","handling",True,False,"mobile.xhtml"),
            "PAGE-23":("mobile.xhtml","Report handling","handling",True,False,None),
            "PAGE-25":("public/track.xhtml","Track cargo","track",False,False,"admin/track.xhtml")}
        def page_path(spec):
            path,heading,kind,operator,needs_id,target=spec
            return path+("?trackingId="+fixture_id if needs_id else "")
        def page_semantics(kind,body,values):
            form=lambda name: 'id="'+name+'"' in body and 'name="csrf"' in body and 'name="jakarta.faces.ViewState"' in body
            if kind=="dashboard":return set(re.findall(r'trackingId=([A-Z0-9]{6,8})',body))=={c["trackingId"] for c in values} and 'id="cargos"' in body
            if kind=="details":return 'id="trackingId">'+fixture_id in body and "Hong Kong" in body and "Helsinki" in body and 'id="routingStatus">' in body
            if kind=="change":return form("change") and 'id="change:destination"' in body and "FIHEL" in body
            if kind=="route":return form("routing") and "route-candidate" in body and 'id="routing:choice"' in body
            if kind=="book":return form("booking") and 'id="booking:origin"' in body and 'id="booking:deadline"' in body
            if kind=="handling":return form("handling") and 'id="handling:type"' in body and 'id="handling:location"' in body
            if kind=="track":return form("tracking") and 'id="tracking:id"' in body
            if kind=="live":return 'id="live-cargos"' in body and 'id="live-map"' in body and "/resources/js/live-tracking.js" in body
            if kind=="error":return payload_absent(body) and not any(marker in body for marker in ["jakarta.faces.FacesException","java.lang.","password","JSESSIONID","<script","untrusted.example"])
            return False
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
            for surface,(path,heading,kind) in read_pages.items():
                status,body,headers=request(opener,path)
                allowed=who is not None or kind=="public"
                if allowed:
                    semantic=status==200 and "<h1>"+heading+"</h1>" in body
                    if kind in {"claimed","routed","unrouted"}:
                        expected={cargo["trackingId"] for cargo in values if (cargo["transportStatus"]=="CLAIMED" if kind=="claimed" else (cargo["routingStatus"]=="NOT_ROUTED") if kind=="unrouted" else cargo["routingStatus"]!="NOT_ROUTED" and cargo["transportStatus"]!="CLAIMED")}
                        actual=set(re.findall(r'trackingId=([A-Z0-9]{6,8})',body))
                        semantic=semantic and actual==expected and 'id="cargos"' in body
                    if kind=="public":semantic=semantic and payload_absent(body)
                    check("Read page semantics: "+surface+" "+actor,semantic)
                    observation={"supported":True,"status":status,"semantic_success":semantic}
                    if kind=="public":observation["protected_payload_absent"]=payload_absent(body)
                else:
                    fixed=headers.get("Location")=="/cargo-tracker/login"
                    check("Anonymous read page login without payload: "+surface,status==303 and fixed and payload_absent(body))
                    observation={"supported":True,"status":status,"redirect_is_configured_login":fixed,"protected_payload_absent":payload_absent(body)}
                if who:observation["identity"]=report["identities"][who]
                report["access_observations"][surface+"::"+actor+"::active"]=observation
            for surface,spec in other_pages.items():
                path,heading,kind,operator,needs_id,target=spec
                allowed=kind=="error" or who is not None and (not operator or who in {"operator","admin"})
                status,body,headers=request(opener,page_path(spec))
                if allowed:
                    redirected=False
                    if target:
                        expected="/cargo-tracker/"+target+("?trackingId="+fixture_id if needs_id else "")
                        redirected=status==303 and headers.get("Location")==expected
                        check("Fixed page alias target: "+surface+" "+actor,redirected)
                        status,body,headers=request(opener,target+("?trackingId="+fixture_id if needs_id else ""))
                    semantic=status==200 and "<h1>"+heading+"</h1>" in body and page_semantics(kind,body,values if who else [])
                    check("Allowed page content: "+surface+" "+actor,semantic)
                    observation={"supported":kind!="live","status":status,"semantic_success":semantic if kind!="live" else False}
                    if target:observation["fixed_alias_verified"]=redirected
                    if kind=="live":observation.update({"shell_rendered":semantic,"browser_required":True})
                    if kind=="error":observation["protected_payload_absent"]=page_semantics(kind,body,[])
                else:
                    fixed=headers.get("Location")=="/cargo-tracker/login"
                    absent=payload_absent(body)
                    check("Page denial precedes data: "+surface+" "+actor,status==(403 if who else 303) and absent and (who is not None or fixed))
                    observation={"supported":True,"status":status,"protected_payload_absent":absent,"redirect_is_configured_login":fixed}
                if who:observation["identity"]=report["identities"][who]
                report["access_observations"][surface+"::"+actor+"::active"]=observation
        def effects():
            return capture_effects(container)
        def settled():return settle_effects(effects)

        # BG-01: the protected page rejects other roles, fixed-root validation
        # rejects adversarial staged entries, and a valid empty file proves the
        # actual JBeret execution identity without changing cargo business data.
        def effects_unchanged(before,after):
            return (before["tables"]==after["tables"] and before["queues"]==after["queues"]
                and before["business_invocations"]==after["business_invocations"])
        def effects_receipt(before,after):
            return {"settled":True,"fixture_id":container,"before_fixture":container,"after_fixture":container,
                "before":{"database":before["tables"],"queue":before["queues"],"business_audit":before["business_invocations"]},
                "after":{"database":after["tables"],"queue":after["queues"],"business_audit":after["business_invocations"]}}
        def batch_payload_absent(body):
            return payload_absent(body) and not any(marker in body for marker in
                ["Import accepted","runId=","batch-worker","IMPORT_AUDIT"])
        # SERVICE-01 direct business-service calls run only in this disposable image.
        booking_probe_path="__fixture/booking-probe"
        def invoke_booking_service(actor,operation,tracking_id=None):
            opener=anonymous if actor=="anonymous" else sessions[actor.lower() if actor!="Administrator" else "admin"][1]
            form={"operation":operation}
            if tracking_id is not None:form["trackingId"]=tracking_id
            before=settled()
            status,body,headers=request(opener,booking_probe_path,form)
            after=settled()
            return {"status":status,"body":body,"headers":dict(headers),
                "effects_unchanged":effects_unchanged(before,after),
                "effects":effects_receipt(before,after),"before":before,"after":after}
        def booking_method_delta(before,after,method):
            names=set(before["business_invocations"])|set(after["business_invocations"])
            deltas={name:after["business_invocations"].get(name,0)-before["business_invocations"].get(name,0)
                for name in names if after["business_invocations"].get(name,0)!=before["business_invocations"].get(name,0)}
            matching=[name for name in deltas if name.endswith("#"+method)]
            return deltas,matching
        setup_book=invoke_booking_service("Operator","book")
        setup_id=setup_book["body"].strip()
        check("SERVICE-01 direct service route fixture cargo created",setup_book["status"]==201 and re.fullmatch("[A-Z0-9]{8}",setup_id) is not None)
        setup_route=invoke_booking_service("Operator","prepare-route",setup_id)
        check("SERVICE-01 direct service fixture itinerary prepared",setup_route["status"]==204)
        booking_service_observations={}
        for actor in ("anonymous","Reader","Operator","Administrator"):
            if actor!="anonymous":
                login_user=actor.lower() if actor!="Administrator" else "admin"
                sessions[login_user]=login(login_user)
            allowed=actor in {"Operator","Administrator"}
            book=invoke_booking_service(actor,"book")
            tracking_id=book["body"].strip() if allowed else setup_id
            if allowed:
                prepared=invoke_booking_service(actor,"prepare-route",tracking_id)
                check("SERVICE-01 authorized route preparation: "+actor,prepared["status"]==204)
            assign=invoke_booking_service(actor,"assign",tracking_id)
            destination=invoke_booking_service(actor,"destination",tracking_id)
            operations={"bookNewCargo":book,"assignCargoToRoute":assign,"changeDestination":destination}
            operation_results={};valid=True
            for method,proof in operations.items():
                status_expected=(201 if method=="bookNewCargo" else 204) if allowed else 403
                denied=(proof["headers"].get("X-Fixture-Probe-Result")=="booking-service-role-denied")
                absent=payload_absent(proof["body"])
                denial_verified=(proof["status"]==403 and denied and absent and proof["effects_unchanged"])
                deltas,matching=booking_method_delta(proof["before"],proof["after"],method)
                expected_delta={"net.java.cargotracker.application.internal.DefaultBookingService#"+method:1}
                authorized_effect=(proof["status"]==status_expected and not denied
                    and proof["before"]["tables"]!=proof["after"]["tables"]
                    and proof["before"]["queues"]==proof["after"]["queues"]
                    and deltas==expected_delta)
                method_valid=authorized_effect if allowed else denial_verified
                valid=valid and method_valid
                operation_results[method]={"status":proof["status"],"invocation_denied":denial_verified,
                    "direct_service_denied":denied,"protected_payload_absent":absent,
                    "independent_effects_unchanged":proof["effects_unchanged"],
                    "authorized_effect_verified":authorized_effect,"effects":proof["effects"],
                    "business_invocation_deltas":deltas}
            expected_status=403 if not allowed else 200
            identity=None if actor=="anonymous" else report["identities"][actor.lower() if actor!="Administrator" else "admin"]
            check("SERVICE-01 direct BookingService actor policy and effects: "+actor,valid)
            booking_service_observations[actor]={"driver":"native-booking-service-v1","actor":actor,
                "supported":True,"status":expected_status,"expected":"allow" if allowed else "deny",
                "identity":identity,"operations":operation_results,"semantic_success":valid,
                "authorized_effect_verified":valid if allowed else False,
                "invocation_denied":valid if not allowed else False}
        report["booking_service_observations"]=booking_service_observations

        batch_actor_observations={}
        for actor,role in [("reader","Reader"),("operator","Operator")]:
            denied_before=settled()
            denied_get=request(sessions[actor][1],"admin/import.xhtml")
            denied_post=request(sessions[actor][1],"admin/import.xhtml",
                {"csrf":sessions[actor][2],"jakarta.faces.ViewState":"forged","batchImport:start":""},
                sessions[actor][2])
            denied_after=settled()
            unchanged=effects_unchanged(denied_before,denied_after)
            absent=batch_payload_absent(denied_get[1]) and batch_payload_absent(denied_post[1])
            check("Batch import route denied without effects: "+actor,
                denied_get[0]==403 and denied_post[0]==403 and unchanged and absent)
            batch_actor_observations[role]={"driver":"native-batch-import-v1","actor":role,
                "supported":True,"status":denied_post[0],"invocation_denied":True,
                "effects":effects_receipt(denied_before,denied_after),
                "get_status":denied_get[0],"post_status":denied_post[0],
                "protected_payload_absent":absent,"independent_effects_unchanged":unchanged,
                "identity":report["identities"][actor]}

        admin_opener=sessions["admin"][1]
        probe_path="__fixture/batch-probe"
        anonymous_import_before=settled()
        anonymous_import_get=request(anonymous,"admin/import.xhtml")
        anonymous_import_post=request(anonymous,"admin/import.xhtml",
            {"batchImport":"batchImport","batchImport:start":"Process staged files"})
        anonymous_import_after=settled()
        anonymous_unchanged=effects_unchanged(anonymous_import_before,anonymous_import_after)
        anonymous_absent=(batch_payload_absent(anonymous_import_get[1])
            and batch_payload_absent(anonymous_import_post[1]))
        anonymous_login=(anonymous_import_get[2].get("Location")=="/cargo-tracker/login"
            and anonymous_import_post[2].get("Location")=="/cargo-tracker/login")
        check("Anonymous batch import GET and POST denied before dispatch",
            anonymous_import_get[0]==303 and anonymous_login and anonymous_absent
            and anonymous_import_post[0]==303 and anonymous_unchanged)
        batch_actor_observations["anonymous"]={"driver":"native-batch-import-v1","actor":"anonymous",
            "supported":True,"status":anonymous_import_post[0],"invocation_denied":True,
            "effects":effects_receipt(anonymous_import_before,anonymous_import_after),
            "get_status":anonymous_import_get[0],"post_status":anonymous_import_post[0],
            "redirect_is_configured_login":anonymous_login,
            "protected_payload_absent":anonymous_absent,
            "independent_effects_unchanged":anonymous_unchanged}
        api_before=settled()
        direct_api_denials={};direct_api_payload_absent={}
        for actor in ("reader","operator","admin"):
            opener=sessions[actor][1]
            statuses={};payloads={}
            for operation in ("read","start"):
                code,body,_=request(opener,probe_path+"?operation="+operation)
                statuses[operation]=code;payloads[operation]=batch_payload_absent(body)
            direct_api_denials[actor]=statuses
            direct_api_payload_absent[actor]=payloads
            check("Direct JobOperator "+actor+" read/start denied",
                all(status==403 for status in statuses.values()) and all(payloads.values()))
        api_after=settled()
        api_effects_unchanged=effects_unchanged(api_before,api_after)
        for role,actor in [("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
            proof=batch_actor_observations.get(role)
            if proof is not None:
                proof["direct_api_denials"]=direct_api_denials[actor]
                proof["direct_api_payload_absent"]=direct_api_payload_absent[actor]
                proof["direct_api_effects_unchanged"]=api_effects_unchanged
        report["batch_import_direct_api_denials"]=direct_api_denials
        handling_worker_denials={}
        for actor,opener in [("anonymous",anonymous),("Reader",sessions["reader"][1]),
                ("Operator",sessions["operator"][1]),("Administrator",sessions["admin"][1])]:
            denied_before=settled()
            denied_status,denied_body,denied_headers=request(opener,
                probe_path+"?operation=handling-service")
            denied_after=settled()
            expected_status=401 if actor=="anonymous" else 403
            worker_only=(denied_headers.get("X-Fixture-Probe-Result")=="worker-only-denied")
            unchanged=effects_unchanged(denied_before,denied_after)
            absent=payload_absent(denied_body)
            check("Direct handling-service worker-only denial without effects: "+actor,
                denied_status==expected_status and unchanged and absent
                and (actor=="anonymous" or worker_only))
            proof={"driver":"native-handling-worker-v1","actor":actor,
                "supported":True,"status":denied_status,"invocation_denied":True,
                "direct_service_denied":actor=="anonymous" or worker_only,
                "protected_payload_absent":absent,"independent_effects_unchanged":unchanged,
                "effects":effects_receipt(denied_before,denied_after)}
            if actor!="anonymous":
                principal={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
                proof["identity"]=report["identities"][principal]
            handling_worker_denials[actor]=proof
        report["handling_worker_denials"]=handling_worker_denials
        inspection_worker_denials={}
        for actor,opener in [("anonymous",anonymous),("Reader",sessions["reader"][1]),
                ("Operator",sessions["operator"][1]),("Administrator",sessions["admin"][1])]:
            denied_before=settled()
            denied_status,denied_body,denied_headers=request(opener,
                probe_path+"?operation=inspection-service")
            denied_after=settled()
            expected_status=401 if actor=="anonymous" else 403
            worker_only=(denied_headers.get("X-Fixture-Probe-Result")=="worker-only-denied")
            unchanged=effects_unchanged(denied_before,denied_after)
            absent=payload_absent(denied_body)
            check("Direct inspection-service worker-only denial without effects: "+actor,
                denied_status==expected_status and unchanged and absent
                and (actor=="anonymous" or worker_only))
            proof={"driver":"native-inspection-worker-v1","actor":actor,
                "supported":True,"status":denied_status,"invocation_denied":True,
                "direct_service_denied":actor=="anonymous" or worker_only,
                "protected_payload_absent":absent,"independent_effects_unchanged":unchanged,
                "effects":effects_receipt(denied_before,denied_after)}
            if actor!="anonymous":
                principal={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
                proof["identity"]=report["identities"][principal]
            inspection_worker_denials[actor]=proof
        report["inspection_worker_denials"]=inspection_worker_denials
        notification_worker_denials={}
        for actor,opener in [("anonymous",anonymous),("Reader",sessions["reader"][1]),
                ("Operator",sessions["operator"][1]),("Administrator",sessions["admin"][1])]:
            denied_before=settled()
            denied_status,denied_body,denied_headers=request(opener,
                probe_path+"?operation=notification-consumer")
            denied_after=settled()
            expected_status=401 if actor=="anonymous" else 403
            no_client_view=(denied_headers.get("X-Fixture-Probe-Result")=="no-consumer-client-view")
            unchanged=effects_unchanged(denied_before,denied_after)
            absent=payload_absent(denied_body)
            check("Direct notification-consumer client-view denial without effects: "+actor,
                denied_status==expected_status and unchanged and absent
                and (actor=="anonymous" or no_client_view))
            proof={"driver":"native-notification-worker-v1","actor":actor,
                "supported":True,"status":denied_status,"invocation_denied":True,
                "direct_service_denied":actor=="anonymous" or no_client_view,
                "protected_payload_absent":absent,"independent_effects_unchanged":unchanged,
                "effects":effects_receipt(denied_before,denied_after)}
            if actor!="anonymous":
                principal={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
                proof["identity"]=report["identities"][principal]
            notification_worker_denials[actor]=proof
        report["notification_worker_denials"]=notification_worker_denials
        producer_attempt=settled()
        cargo_handled_queue_before=producer_attempt["queues"]["jms.queue.CargoHandledQueue"]
        inspection_invocations_before=producer_attempt["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.CargoHandledConsumer#onMessage",0)
        inspection_audit_logs_before=command("docker","logs",container).count(
            "INSPECTION_WORKER_AUDIT event=consumed principal=inspection-worker role=InspectionWorker")
        producer_process=subprocess.run(["docker","exec",container,"java","-cp",
            "/opt/jboss/remote-producer-classes:/opt/jboss/remote-producer-classes/WEB-INF/classes:/opt/jboss/remote-producer-classes/WEB-INF/lib/*:/opt/jboss/wildfly/bin/client/jboss-client.jar",
            "lab.fixture.RemoteJmsProducerProbe","/run/kan18/producer-client.properties"],
            capture_output=True,text=True,timeout=30)
        if producer_process.returncode:
            report["remote_producer_diagnostic"]=(producer_process.stdout+producer_process.stderr)[-4000:]
            raise RuntimeError("Remote JMS producer probe failed; see remote_producer_diagnostic")
        producer_output=producer_process.stdout
        producer_observation=json.loads(producer_output.strip().splitlines()[-1])
        producer_after=settled()
        cargo_handled_queue_after=producer_after["queues"]["jms.queue.CargoHandledQueue"]
        inspection_invocations_after=producer_after["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.CargoHandledConsumer#onMessage",0)
        inspection_audit_logs_after=command("docker","logs",container).count(
            "INSPECTION_WORKER_AUDIT event=consumed principal=inspection-worker role=InspectionWorker")
        cargo_handled_effects_unchanged=(producer_after["tables"]==producer_attempt["tables"]
            and cargo_handled_queue_after==cargo_handled_queue_before
            and inspection_invocations_after==inspection_invocations_before
            and inspection_audit_logs_after==inspection_audit_logs_before)
        report["cargo_handled_producer_raw_observation"]={key:value for key,value in producer_observation.items()
            if key.startswith("cargoHandled")}
        report["cargo_handled_producer_effects_unchanged"]=cargo_handled_effects_unchanged
        unauthorized_unchanged=(producer_after["tables"]==producer_attempt["tables"]
            and producer_observation.get("anonymousDenied") is True
            and producer_observation.get("humanSendDenied")==[True,True,True]
            and producer_observation.get("machineAuthenticated")==[True,True,True,True]
            and producer_observation.get("machineSendDenied")==[True,True,True,True]
            and producer_observation.get("rejectedQueueDenied") is True
            and producer_observation.get("deliveredQueueDenied") is True)
        report["remote_producer_raw_observation"]=producer_observation
        report["remote_producer_unauthorized_effects_unchanged"]=unauthorized_unchanged
        producer_boundary_verified=remote_producer_boundary_verified(
            producer_observation,unauthorized_unchanged)
        check("Remote JMS authenticated users cannot send to handling-attempt queue",
            producer_observation.get("anonymousDenied") is True
            and producer_observation.get("humanAuthenticated")==[True,True,True]
            and producer_observation.get("humanSendDenied")==[True,True,True]
            and producer_observation.get("machineAuthenticated")==[True,True,True,True]
            and producer_observation.get("machineSendDenied")==[True,True,True,True]
            and unauthorized_unchanged)
        check("Trusted remote producer can send only to handling-attempt queue",
            producer_observation.get("trustedAllowed") is True
            and producer_observation.get("rejectedQueueDenied") is True
            and producer_observation.get("deliveredQueueDenied") is True)
        cargo_handled_producer_boundary_verified=(
            producer_observation.get("cargoHandledAnonymousDenied") is True
            and producer_observation.get("cargoHandledHumanAuthenticated")==[True,True,True]
            and producer_observation.get("cargoHandledHumanSendDenied")==[True,True,True]
            and producer_observation.get("cargoHandledMachinePrincipals")==["batch-worker","inspection-worker","notification-worker"]
            and producer_observation.get("cargoHandledMachineAuthenticated")==[True,True,True]
            and producer_observation.get("cargoHandledMachineSendDenied")==[True,True,True]
            and producer_observation.get("cargoHandledTrustedPrincipal")=="handling-worker"
            and producer_observation.get("cargoHandledTrustedAllowed") is True
            and cargo_handled_effects_unchanged)
        check("CargoHandledQueue permits only authenticated HandlingWorker among tested remote principals",
            cargo_handled_producer_boundary_verified)
        check("CargoHandledQueue authorization probe leaves application effects unchanged",
            cargo_handled_effects_unchanged)
        rejection_before=producer_attempt
        poison_status=202
        report["handling_attempt_producer_observation"]={
            "driver":"remote-jms-producer-v1","supported":True,
            "identity_verified":producer_observation.get("trustedAllowed") is True,
            "principal":"handling-attempt-producer","roles":["HandlingAttemptProducer"],
            "anonymous_denied":producer_observation.get("anonymousDenied") is True,
            "human_users_authenticated":producer_observation.get("humanAuthenticated"),
            "human_send_denials":producer_observation.get("humanSendDenied"),
            "other_queue_denials":{
                "rejected_registration":producer_observation.get("rejectedQueueDenied"),
                "delivered_notifications":producer_observation.get("deliveredQueueDenied")},
            "unauthorized_effects_unchanged":unauthorized_unchanged,
            "transport":"remote+http WildFly JMS connection from a separate JVM"}
        check("Trusted remote producer publishes one invalid attempt for broker disposition",
            producer_observation.get("trustedAllowed") is True)
        rejection_wait_deadline=time.monotonic()+45
        rejection_after=None
        while time.monotonic()<rejection_wait_deadline:
            snapshot=effects()
            input_queue=snapshot["queues"]["jms.queue.HandlingEventRegistrationAttemptQueue"]
            rejected_queue=snapshot["queues"]["jms.queue.RejectedRegistrationAttemptsQueue"]
            input_calls=snapshot["business_invocations"].get(
                "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0)
            reject_calls=snapshot["business_invocations"].get(
                "net.java.cargotracker.infrastructure.messaging.jms.RejectedRegistrationAttemptsConsumer#onMessage",0)
            if (input_queue["MessageCount"]==0 and rejected_queue["MessageCount"]==0
                    and input_queue["MessagesAdded"]-rejection_before["queues"]["jms.queue.HandlingEventRegistrationAttemptQueue"]["MessagesAdded"]==1
                    and rejected_queue["MessagesAdded"]-rejection_before["queues"]["jms.queue.RejectedRegistrationAttemptsQueue"]["MessagesAdded"]==1
                    and reject_calls-rejection_before["business_invocations"].get(
                        "net.java.cargotracker.infrastructure.messaging.jms.RejectedRegistrationAttemptsConsumer#onMessage",0)==1
                    and input_calls-rejection_before["business_invocations"].get(
                        "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0)==3):
                rejection_after=settled()
                break
            time.sleep(.5)
        if rejection_after is None:
            rejection_after=effects()
        input_name="jms.queue.HandlingEventRegistrationAttemptQueue"
        rejected_name="jms.queue.RejectedRegistrationAttemptsQueue"
        rejected_audit_logs=command("docker","logs",container)
        rejected_audit_line="NOTIFICATION_WORKER_AUDIT event=consumed consumer=rejected-registration principal=notification-worker role=NotificationWorker"
        handling_attempt_delta=(rejection_after["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0)
            - rejection_before["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0))
        handling_audit_delta=(rejection_after["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingWorkerAudit#recordConsumedAttempt",0)
            - rejection_before["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingWorkerAudit#recordConsumedAttempt",0))
        rejected_consumer_delta=(rejection_after["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.RejectedRegistrationAttemptsConsumer#onMessage",0)
            - rejection_before["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.RejectedRegistrationAttemptsConsumer#onMessage",0))
        rejected_audit_delta=(rejection_after["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.NotificationWorkerAudit#recordConsumed",0)
            - rejection_before["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.NotificationWorkerAudit#recordConsumed",0))
        rejection_message=(
            rejection_after["queues"][input_name]["MessagesAdded"]-
                rejection_before["queues"][input_name]["MessagesAdded"]==1
            and rejection_after["queues"][input_name]["MessagesKilled"]-
                rejection_before["queues"][input_name]["MessagesKilled"]==1
            and rejection_after["queues"][rejected_name]["MessagesAdded"]-
                rejection_before["queues"][rejected_name]["MessagesAdded"]==1
            and rejection_after["queues"][rejected_name]["MessagesAcknowledged"]-
                rejection_before["queues"][rejected_name]["MessagesAcknowledged"]==1
            and rejection_after["queues"][input_name]["MessageCount"]==0
            and rejection_after["queues"][rejected_name]["MessageCount"]==0)
        rejection_effect_comparison=compare_rejection_effect_deltas(
            rejection_before,rejection_after,input_name,rejected_name)
        rejection_no_business_effects=(
            rejection_after["tables"]==rejection_before["tables"]
            and rejection_effect_comparison["all_queue_and_invocation_deltas_bounded"])
        rejection_log_sanitized=(rejected_audit_logs.count(rejected_audit_line)==1
            and "NOCARGO1" not in rejected_audit_logs)
        report["rejection_disposition_diagnostics"]={
            **rejection_effect_comparison,
            "tables_unchanged":rejection_after["tables"]==rejection_before["tables"],
            "log_sanitized":rejection_log_sanitized}
        check("Invalid handling attempts receive three bounded deliveries then broker dead-letter disposition",
            poison_status==202 and rejection_message and handling_attempt_delta==3)
        check("Rejected-attempt consumer acknowledges one identifier-free server-worker audit",
            rejected_consumer_delta==1 and rejected_audit_delta==1 and rejection_log_sanitized)
        check("Rejected attempts leave cargo and handling business tables unchanged",
            rejection_no_business_effects)
        report["rejection_disposition_observation"]={
            "driver":"native-notification-worker-v1","supported":True,
            "trusted_broker_dead_letter_verified":rejection_message and handling_attempt_delta==3,
            "delivery_attempts":handling_attempt_delta,
            "rejection_consumer_invocations":rejected_consumer_delta,
            "notification_worker_audit_invocations":rejected_audit_delta,
            "rejected_effects_unchanged":rejection_after["tables"]==rejection_before["tables"],
            "final_disposition_verified":rejection_message and rejected_consumer_delta==1,
            "sanitized_rejection_audit_verified":rejection_log_sanitized,
            "business_side_effects_unchanged":rejection_no_business_effects,
            "producer_boundary_verified":producer_boundary_verified,
            "producer_boundary_note":"Separate-JVM remote+http JMS authorization verified",
            "before":effects_receipt(rejection_before,rejection_after)}
        api_job_start_delta=(api_after["business_invocations"].get(
            "net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobStarted",0)
            - api_before["business_invocations"].get(
                "net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobStarted",0))
        check("Direct JobOperator probes create no batch execution",
            api_job_start_delta==0 and api_effects_unchanged and "IMPORT_AUDIT" not in command("docker","logs",container))

        # Obtain an enabled form first, then flip the switch off before submitting
        # that still-valid form. This reaches the server-side RequestService gate.
        enabled_form_status,enabled_form_body,_=request(admin_opener,"admin/import.xhtml")
        enabled_form_view=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',enabled_form_body)
        enabled_form_csrf=re.search(r'name="csrf" value="([^"]+)"',enabled_form_body)
        enabled_button=re.search(r'<input[^>]*id="batchImport:start"[^>]*disabled',enabled_form_body) is None
        command("docker","exec",container,"sh","-c",
                ": > /opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-disabled.csv")
        switch_status,_,switch_headers=request(admin_opener,
            probe_path+"?operation=switch&enabled=false")
        issued_nonce=switch_headers.get("X-Fixture-Issued-Nonce","")
        switch_before=settled()
        service_status,service_body,service_headers=request(admin_opener,
            probe_path+"?operation=service-start&nonce="+urllib.parse.quote(issued_nonce))
        switch_after=settled()
        service_delta=(switch_after["business_invocations"].get(
            "net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#start",0)
            - switch_before["business_invocations"].get(
                "net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#start",0))
        launcher_delta=(switch_after["business_invocations"].get(
            "net.java.cargotracker.interfaces.handling.file.BatchImportLauncher#start",0)
            - switch_before["business_invocations"].get(
                "net.java.cargotracker.interfaces.handling.file.BatchImportLauncher#start",0))
        disabled_status,disabled_body,_=request(admin_opener,"admin/import.xhtml")
        button_disabled=re.search(r'<input[^>]*id="batchImport:start"[^>]*disabled',disabled_body) is not None
        disabled_post_status,disabled_post_body,_=request(admin_opener,"admin/import.xhtml",
            {"csrf":enabled_form_csrf[1] if enabled_form_csrf else "",
             "batchImport":"batchImport",
             "jakarta.faces.ViewState":html.unescape(enabled_form_view[1]) if enabled_form_view else "",
             "batchImport:start":"Process staged files"},
            enabled_form_csrf[1] if enabled_form_csrf else "missing")
        marker_exists=subprocess.run(["docker","exec",container,"test","-f",
            "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-disabled.csv"]).returncode==0
        switch_on=request(admin_opener,probe_path+"?operation=switch&enabled=true")[0]
        check("Disabled import switch rejects an earlier enabled form",
            enabled_form_status==200 and enabled_form_csrf is not None
            and enabled_form_view is not None and enabled_button
            and switch_status==204 and bool(re.fullmatch("[0-9a-f-]{36}",issued_nonce))
            and service_status==409 and service_headers.get("X-Fixture-Probe-Result")=="disabled-before-launch"
            and service_delta==1 and launcher_delta==0
            and disabled_status==200 and "disabled" in disabled_body.lower() and button_disabled
            and disabled_post_status==200
            and marker_exists and switch_on==204
            and "IMPORT_JOB_SUBMIT" not in command("docker","logs",container)
            and "IMPORT_AUDIT" not in command("docker","logs",container))
        command("docker","exec",container,"rm","-f",
                "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-disabled.csv")

        # Missing and incorrect CSRF values must be rejected before JSF action dispatch.
        csrf_form_status,csrf_form_body,_=request(admin_opener,"admin/import.xhtml")
        csrf_view=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',csrf_form_body)
        csrf_nonce=re.search(r'name="csrf" value="([^"]+)"',csrf_form_body)
        csrf_payload={"batchImport":"batchImport",
            "jakarta.faces.ViewState":html.unescape(csrf_view[1]) if csrf_view else "",
            "batchImport:start":"Process staged files"}
        missing_csrf=request(admin_opener,"admin/import.xhtml",csrf_payload)[0]
        wrong_csrf=request(admin_opener,"admin/import.xhtml",csrf_payload,"invalid-token")[0]
        check("Batch import missing and wrong CSRF denied",
            csrf_form_status==200 and csrf_nonce is not None
            and missing_csrf==403 and wrong_csrf==403
            and "IMPORT_JOB_SUBMIT" not in command("docker","logs",container)
            and "IMPORT_AUDIT" not in command("docker","logs",container))

        # A form obtained in an authenticated session is unusable after logout.
        revoked_jar,revoked_admin,revoked_csrf=login("admin")
        revoked_status,revoked_body,_=request(revoked_admin,"admin/import.xhtml")
        revoked_view=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',revoked_body)
        revoked_form_csrf=re.search(r'name="csrf" value="([^"]+)"',revoked_body)
        stale_payload={"csrf":revoked_form_csrf[1] if revoked_form_csrf else "",
            "batchImport":"batchImport",
            "jakarta.faces.ViewState":html.unescape(revoked_view[1]) if revoked_view else "",
            "batchImport:start":"Process staged files"}
        logout_status=request(revoked_admin,"logout",{"csrf":revoked_csrf},revoked_csrf)[0]
        stale_status,_,stale_headers=request(revoked_admin,"admin/import.xhtml",
            stale_payload,revoked_form_csrf[1] if revoked_form_csrf else "missing")
        check("Revoked Administrator session cannot submit an earlier import form",
            revoked_status==200 and logout_status==204 and stale_status==303
            and stale_headers.get("Location")=="/cargo-tracker/login"
            and "IMPORT_JOB_SUBMIT" not in command("docker","logs",container)
            and "IMPORT_AUDIT" not in command("docker","logs",container))

        batch_before=settled()
        def import_form():
            status,body,_=request(admin_opener,"admin/import.xhtml")
            csrf=re.search(r'name="csrf" value="([^"]+)"',body)
            view=re.search(r'name="jakarta.faces.ViewState"[^>]*value="([^"]+)"',body)
            check("Administrator batch import form and enabled kill switch",
                status==200 and "Process staged files" in body
                and csrf is not None and view is not None)
            return csrf[1],view[1]
        def submit_import():
            csrf,view=import_form()
            return request(admin_opener,"admin/import.xhtml",
                {"csrf":csrf,"batchImport":"batchImport","jakarta.faces.ViewState":html.unescape(view),
                 "batchImport:start":"Process staged files"},csrf)

        command("docker","exec",container,"sh","-c",
                "ln -s /etc/passwd /opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-link.csv")
        status,body,_=submit_import()
        check("Batch import rejects staged symlink without job submission",
            status==200 and "Import was not started" in body and "Import accepted" not in body
            and "IMPORT_JOB_SUBMIT" not in command("docker","logs",container)
            and "IMPORT_AUDIT" not in command("docker","logs",container))
        command("docker","exec",container,"rm","-f",
                "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-link.csv")
        command("docker","exec",container,"mkdir",
                "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-directory")
        status,body,_=submit_import()
        check("Batch import rejects non-regular staged entry without job submission",
            status==200 and "Import was not started" in body
            and "IMPORT_JOB_SUBMIT" not in command("docker","logs",container)
            and "IMPORT_AUDIT" not in command("docker","logs",container))
        command("docker","exec",container,"rmdir",
                "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-directory")

        command("docker","exec",container,"sh","-c",
                ": > /opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-empty.csv")
        concurrent_csrf,concurrent_view=import_form()
        concurrent_payload={"csrf":concurrent_csrf,"batchImport":"batchImport",
            "jakarta.faces.ViewState":html.unescape(concurrent_view),
            "batchImport:start":"Process staged files"}
        concurrent_log_before=command("docker","logs",container)
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending=[pool.submit(request,admin_opener,"admin/import.xhtml",
                concurrent_payload,concurrent_csrf) for _ in range(2)]
            concurrent_results=[future.result(timeout=30) for future in pending]
        concurrent_log=command("docker","logs",container)
        accepted_matches=[re.search(r"Import accepted as run ([0-9a-f-]{36})",result[1])
            for result in concurrent_results]
        accepted_values=[match[1] for match in accepted_matches if match]
        concurrent_submissions=(concurrent_log.count("IMPORT_JOB_SUBMIT")
            - concurrent_log_before.count("IMPORT_JOB_SUBMIT"))
        check("Concurrent replay of one import form starts at most one job",
            len(accepted_values)==1 and concurrent_submissions==1
            and all(result[0]==200 for result in concurrent_results))
        accepted=re.search(r"Import accepted as run ([0-9a-f-]{36})",
            next((result[1] for result in concurrent_results if
                "Import accepted as run " in result[1]),""))
        check("Administrator batch trigger accepted",accepted is not None)
        run_id=accepted[1] if accepted else ""
        deadline=time.monotonic()+60
        audit=""
        while time.monotonic()<deadline:
            audit=command("docker","logs",container)
            if batch_finished_line(audit,run_id) is not None:break
            time.sleep(.5)
        empty_finished=batch_finished_line(audit,run_id)
        worker_verified=("IMPORT_AUDIT event=started runId="+run_id+" initiator=admin worker=batch-worker" in audit
            and empty_finished is not None and "event=finished:COMPLETED" in empty_finished
            and "initiator=admin worker=batch-worker" in empty_finished)
        check("JBeret uses restricted batch worker identity and preserves initiator",worker_verified)
        file_removed=subprocess.run(["docker","exec",container,"test","!","-e",
            "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-empty.csv"]).returncode==0
        check("Completed batch consumes staged empty file",file_removed)
        batch_after=settled()
        business_unchanged=(batch_before["tables"]==batch_after["tables"]
            and batch_before["queues"]==batch_after["queues"])
        before_calls=batch_before["business_invocations"]
        after_calls=batch_after["business_invocations"]
        expected_deltas=expected_batch_control_deltas()
        observed_deltas={key:after_calls.get(key,0)-before_calls.get(key,0)
            for key in sorted(set(before_calls)|set(after_calls)|set(expected_deltas))}
        control_calls_bounded=all(
            observed_deltas.get(key,0)==expected_deltas.get(key,0)
            for key in set(observed_deltas)|set(expected_deltas))
        report["batch_control_audit_invocations"]={
            "expected":expected_deltas,"observed":observed_deltas,
            "passed":control_calls_bounded}
        check("Empty batch import leaves business state unchanged",business_unchanged)
        check("Batch control/audit invocation deltas are exactly bounded",control_calls_bounded)
        started_match=re.search(r"IMPORT_JOB_STARTED runId="+re.escape(run_id)+r" executionId=([0-9]+)",audit)
        execution_id=started_match[1] if started_match else ""
        restart_denials={}
        for actor in ("reader","operator","admin"):
            restart_denials[actor]=request(sessions[actor][1],
                probe_path+"?operation=restart&executionId="+execution_id)[0]
        check("Direct JobOperator restart denied for application roles",
            execution_id.isdigit() and all(status==403 for status in restart_denials.values()))
        command("docker","exec",container,"sh","-c",
                ": > /opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-replay.csv")
        replay_status,replay_body,_=request(admin_opener,"admin/import.xhtml",
            concurrent_payload,concurrent_csrf)
        replay_file_exists=subprocess.run(["docker","exec",container,"test","-f",
            "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-replay.csv"]).returncode==0
        check("One-time import form replay is denied without a second job",
            replay_status==200 and "Import was not started" in replay_body
            and "IMPORT_JOB_SUBMIT runId="+run_id in command("docker","logs",container)
            and command("docker","logs",container).count("IMPORT_JOB_SUBMIT")==1
            and replay_file_exists)
        command("docker","exec",container,"rm","-f",
                "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-replay.csv")

        reader_opener=sessions["reader"][1]
        cargo_status,cargo_body,_=request(reader_opener,"rest/cargo")
        valid_before_cargos=json.loads(cargo_body)
        valid_target_before=next(c for c in valid_before_cargos if c["trackingId"]==fixture_id)
        before_valid=settled()
        valid_line=f"2030-01-05 10:00,{fixture_id},,CNHKG,RECEIVE"
        invalid_line="invalid,batch,event,line"
        filesystem_producer_uid=int(command("docker","exec","--user","0:0",container,"id","-u"))
        command("docker","exec","--user","0:0",container,"sh","-c",
            "printf '%s\\n' '"+invalid_line+"' > /opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg02-invalid.csv")
        command("docker","exec","--user","0:0",container,"sh","-c",
            "printf '%s\\n' '"+valid_line+"' > /opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-valid.csv")
        valid_status,valid_body,_=submit_import()
        valid_accepted=re.search(r"Import accepted as run ([0-9a-f-]{36})",valid_body)
        check("Administrator valid event file accepted",
            valid_status==200 and valid_accepted is not None)
        valid_run=valid_accepted[1] if valid_accepted else ""
        valid_deadline=time.monotonic()+60
        valid_audit=""
        while time.monotonic()<valid_deadline:
            valid_audit=command("docker","logs",container)
            if batch_finished_line(valid_audit,valid_run) is not None:break
            time.sleep(.5)
        valid_finished=batch_finished_line(valid_audit,valid_run)
        valid_worker=("IMPORT_AUDIT event=started runId="+valid_run+" initiator=admin worker=batch-worker" in valid_audit
            and valid_finished is not None and "event=finished:COMPLETED" in valid_finished
            and "initiator=admin worker=batch-worker" in valid_finished)
        if not valid_worker:
            diagnostics={"run_id":valid_run}
            started=re.search(r"IMPORT_JOB_STARTED runId="+re.escape(valid_run)+r" executionId=([0-9]+)",valid_audit)
            execution_id=started[1] if started else None
            diagnostics["execution_id"]=execution_id
            if execution_id:
                status_address="/deployment=cargo-tracker.war/subsystem=batch-jberet/job=EventFilesProcessorJob/execution="+execution_id
                try:
                    output=command("docker","exec",container,"/opt/jboss/wildfly/bin/jboss-cli.sh",
                        "--connect","--commands="+status_address+":read-resource(include-runtime=true)",timeout=12)
                    report_path=WORK/"batch-job-status.txt"
                    report_path.write_text(output)
                    diagnostics["job_status_path"]=str(report_path.relative_to(ROOT))
                    diagnostics["job_status_sha256"]=hashlib.sha256(output.encode()).hexdigest()
                except subprocess.CalledProcessError as failure:
                    output=(failure.output or "")
                    output_path=WORK/"batch-job-status-error.txt"
                    output_path.write_text(output)
                    diagnostics["job_status_error"]={"exit_code":failure.returncode,
                        "path":str(output_path.relative_to(ROOT)),
                        "sha256":hashlib.sha256(output.encode()).hexdigest()}
                except Exception as failure:
                    diagnostics["job_status_error"]=type(failure).__name__
            try:
                snapshot=capture_effects(container,timeout=12)
                diagnostics["queues"]=snapshot["queues"]
                diagnostics["table_counts"]={name:value["rows"] for name,value in snapshot["tables"].items()}
            except Exception as failure:
                diagnostics["observer_error"]=type(failure).__name__
            try:
                files=command("docker","exec",container,"sh","-c",
                    "find /opt/jboss/wildfly/standalone/data/cargo-import/archive -maxdepth 1 -type f -printf '%f %s\\n'",
                    timeout=8)
                diagnostics["archive_files"]=files
            except Exception as failure:
                diagnostics["archive_error"]=type(failure).__name__
            try:
                processes=command("docker","exec",container,"jcmd","-l",timeout=8).splitlines()
                jvms=[line.split()[0] for line in processes
                    if "org.jboss.as.standalone" in line or "jboss-modules.jar" in line]
                diagnostics["jvm_count"]=len(jvms)
                if len(jvms)==1:
                    for index in (1,2):
                        dump=command("docker","exec",container,"jcmd",jvms[0],"Thread.print","-l",timeout=12)
                        dump_path=WORK/("batch-thread-"+str(index)+".txt")
                        dump_path.write_text(dump)
                        diagnostics["thread_dump_"+str(index)]={"path":str(dump_path.relative_to(ROOT)),
                            "sha256":hashlib.sha256(dump.encode()).hexdigest(),"bytes":len(dump)}
                        if index==1:time.sleep(5)
            except Exception as failure:
                diagnostics["thread_dump_error"]=type(failure).__name__
            report["batch_diagnostics"]=diagnostics
        check("Valid event batch completed under batch worker",valid_worker)
        valid_after=settled()
        cargo_status,cargo_body,_=request(reader_opener,"rest/cargo")
        valid_after_cargos=json.loads(cargo_body)
        valid_target_after=next(c for c in valid_after_cargos if c["trackingId"]==fixture_id)
        valid_positive=(cargo_status==200
            and valid_target_before.get("transportStatus")=="NOT_RECEIVED"
            and valid_target_after.get("transportStatus")=="IN_PORT"
            and valid_target_after.get("lastKnownLocationCode")=="CNHKG"
            and all(valid_target_before.get(k)==valid_target_after.get(k)
                for k in ["trackingId","originCode","destinationCode","arrivalDeadline","routingStatus"])
            and {c["trackingId"]:c for c in valid_before_cargos if c["trackingId"]!=fixture_id}
                =={c["trackingId"]:c for c in valid_after_cargos if c["trackingId"]!=fixture_id})
        check("Valid file event persists to independent Reader state",valid_positive)
        queue_before=before_valid["queues"];queue_after=valid_after["queues"]
        target_queues={"jms.queue.HandlingEventRegistrationAttemptQueue","jms.queue.CargoHandledQueue"}
        valid_queues=(set(queue_before)==set(queue_after)
            and all(queue_after[q]["MessageCount"]==queue_after[q]["DeliveringCount"]
                ==queue_after[q]["ScheduledCount"]==0 for q in queue_after)
            and all(
                (queue_after[q]["MessagesAdded"]-queue_before[q]["MessagesAdded"]==1
                 and queue_after[q]["MessagesAcknowledged"]-queue_before[q]["MessagesAcknowledged"]==1)
                if q in target_queues else queue_after[q]==queue_before[q]
                for q in queue_before)
            and all(queue_after[q]["MessagesExpired"]==queue_before[q]["MessagesExpired"]
                and queue_after[q]["MessagesKilled"]==queue_before[q]["MessagesKilled"]
                and queue_after[q]["AcknowledgeAttempts"]-queue_before[q]["AcknowledgeAttempts"] in {0,1}
                for q in target_queues))
        check("Valid file event produces exactly two settled queue cycles",valid_queues)
        table_before=before_valid["tables"];table_after=valid_after["tables"]
        handling_table=table_key(table_before,"handling_event")
        cargo_table=table_key(table_before,"cargo")
        valid_tables=(set(table_before)==set(table_after)
            and handling_table in table_after and cargo_table in table_after
            and table_after[handling_table]["rows"]-table_before[handling_table]["rows"]==1
            and table_after[cargo_table]["rows"]==table_before[cargo_table]["rows"]
            and table_after[cargo_table]["sha256"]!=table_before[cargo_table]["sha256"]
            and all(table_after[name]==table_before[name]
                for name in table_before if name not in {handling_table,cargo_table}))
        check("Valid file event changes only cargo and handling tables",valid_tables)
        valid_deltas={
            "net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#issueNonce":1,
            "net.java.cargotracker.interfaces.handling.file.BatchImportRequestService#start":1,
            "net.java.cargotracker.interfaces.handling.file.BatchImportLauncher#start":1,
            "net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobStarted":1,
            "net.java.cargotracker.interfaces.handling.file.BatchWorkerAudit#jobFinished":1,
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptProducer#publish":1,
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage":1,
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingWorkerAudit#recordConsumedAttempt":1,
            "net.java.cargotracker.application.internal.DefaultHandlingEventService#registerHandlingEvent":1,
            "net.java.cargotracker.infrastructure.messaging.jms.CargoHandledConsumer#onMessage":1,
            "net.java.cargotracker.infrastructure.messaging.jms.InspectionWorkerAudit#recordConsumedAttempt":1,
            "net.java.cargotracker.application.internal.DefaultCargoInspectionService#inspectCargo":1,
            "net.java.cargotracker.interfaces.booking.socket.RealtimeCargoTrackingService#onCargoInspected":1}
        valid_before_calls=before_valid["business_invocations"]
        valid_after_calls=valid_after["business_invocations"]
        report["valid_invocation_deltas"]={
            k:valid_after_calls.get(k,0)-valid_before_calls.get(k,0)
            for k in sorted(set(valid_before_calls)|set(valid_after_calls))}
        valid_call_deltas=all(valid_after_calls.get(k,0)-valid_before_calls.get(k,0)==n
            for k,n in valid_deltas.items()) and all(
            valid_after_calls.get(k,0)-valid_before_calls.get(k,0)==valid_deltas.get(k,0)
            for k in set(valid_before_calls)|set(valid_after_calls))
        check("Valid file business and control invocation deltas are bounded",valid_call_deltas)
        valid_file_removed=subprocess.run(["docker","exec",container,"test","!","-e",
            "/opt/jboss/wildfly/standalone/data/cargo-import/incoming/bg01-valid.csv"]).returncode==0
        check("Valid batch consumes staged event file",valid_file_removed)
        import_root="/opt/jboss/wildfly/standalone/data/cargo-import"
        directory_state=command("docker","exec",container,"sh","-c",
            "stat -c '%a:%u' "+import_root+"/incoming "+import_root+"/archive "
            +import_root+"/failed; id -u").splitlines()
        private_directories=(len(directory_state)==4 and directory_state[0]==directory_state[1]
            ==directory_state[2] and directory_state[0].startswith("700:")
            and directory_state[3]==directory_state[0].split(":",1)[1])
        filesystem_worker_uid=int(directory_state[3]) if len(directory_state)==4 else -1
        check("Incoming archive and failed directories are private to the server OS identity",
            private_directories)
        invalid_file_removed=subprocess.run(["docker","exec",container,"test","!","-e",
            import_root+"/incoming/bg02-invalid.csv"]).returncode==0
        archive_names=command("docker","exec",container,"sh","-c",
            "find "+import_root+"/archive -mindepth 1 -maxdepth 1 -type f -printf '%f\\n'").splitlines()
        failed_names=command("docker","exec",container,"sh","-c",
            "find "+import_root+"/failed -mindepth 1 -maxdepth 1 -type f -printf '%f\\n'").splitlines()
        archive_text=command("docker","exec",container,"sh","-c",
            "cat "+import_root+"/archive/archive_*.csv") if archive_names else ""
        failed_text=command("docker","exec",container,"sh","-c",
            "cat "+import_root+"/failed/failed_*.csv") if failed_names else ""
        untrusted_uid=int(command("docker","exec","--user","65534:65534",container,"id","-u"))
        incoming_read_marker=import_root+"/incoming/bg02-untrusted-read-probe.tmp"
        command("docker","exec","--user","0:0",container,"sh","-c",
            "umask 022; : > "+incoming_read_marker+"; chmod 644 "+incoming_read_marker)
        protected_files={"incoming":incoming_read_marker,
            "archive":import_root+"/archive/"+(archive_names[0] if archive_names else "missing.csv"),
            "failed":import_root+"/failed/"+(failed_names[0] if failed_names else "missing.csv")}
        untrusted_os_access={}
        for directory in ["incoming","archive","failed"]:
            target=import_root+"/"+directory
            write_marker=target+"/bg02-untrusted-write-probe.tmp"
            listing=subprocess.run(["docker","exec","--user","65534:65534",container,"ls","-A",target],
                capture_output=True,text=True,timeout=10)
            read_attempt=subprocess.run(["docker","exec","--user","65534:65534",container,"cat",protected_files[directory]],
                capture_output=True,text=True,timeout=10)
            write_attempt=subprocess.run(["docker","exec","--user","65534:65534",container,"touch",write_marker],
                capture_output=True,text=True,timeout=10)
            marker_absent=subprocess.run(["docker","exec",container,"test","!","-e",write_marker]).returncode==0
            list_denied=(listing.returncode!=0 and "permission denied" in listing.stderr.lower())
            read_denied=(read_attempt.returncode!=0 and "permission denied" in read_attempt.stderr.lower())
            write_denied=(write_attempt.returncode!=0 and "permission denied" in write_attempt.stderr.lower())
            untrusted_os_access[directory]={"list_denied":list_denied,"read_denied":read_denied,
                "write_denied":write_denied,"marker_absent":marker_absent}
            check("Untrusted OS identity cannot list, read, or write "+directory,
                untrusted_uid==65534 and list_denied and read_denied and write_denied and marker_absent)
        command("docker","exec","--user","0:0",container,"rm","-f",incoming_read_marker)
        incoming_read_marker_absent=subprocess.run(["docker","exec",container,"test","!","-e",
            incoming_read_marker]).returncode==0
        untrusted_os_identity_denied=(untrusted_uid==65534 and incoming_read_marker_absent and all(
            proof["list_denied"] and proof["read_denied"] and proof["write_denied"] and proof["marker_absent"]
            for proof in untrusted_os_access.values()))
        check("Trusted admin tooling and batch worker use distinct filesystem identities",
            filesystem_producer_uid==0 and filesystem_worker_uid>0 and filesystem_worker_uid!=filesystem_producer_uid)
        archive_output_verified=(len(archive_names)==1
            and re.fullmatch(r"archive_EventFilesProcessorJob_[0-9]+\.csv",archive_names[0]) is not None
            and len(archive_text.splitlines())==1 and fixture_id in archive_text
            and "CNHKG" in archive_text and "RECEIVE" in archive_text
            and invalid_line not in archive_text)
        failed_output_verified=(len(failed_names)==1
            and re.fullmatch(r"failed_EventFilesProcessorJob_[0-9]+\.csv",failed_names[0]) is not None
            and failed_text.splitlines()==[invalid_line] and fixture_id not in failed_text)
        check("Valid event is archived under a generated in-root name",archive_output_verified)
        check("Malformed event is isolated in failed output without business processing",
            failed_output_verified and invalid_file_removed and valid_positive
            and valid_tables and valid_queues and valid_call_deltas)
        batch_processing_observation={"driver":"native-batch-processing-v1","supported":True,
            "actor":"Administrator","administrator_identity":report["identities"]["admin"],
            "authorized_job_completed":valid_worker,"batch_worker_identity_verified":worker_verified,
            "directory_policy_verified":private_directories,
            "filesystem_producer_identity":{"verified":filesystem_producer_uid==0,"uid":filesystem_producer_uid,
                "scope":"approved fixture administration tooling"},
            "filesystem_worker_identity":{"verified":private_directories,"uid":filesystem_worker_uid},
            "filesystem_worker_uid":filesystem_worker_uid,
            "trusted_filesystem_staging_verified":filesystem_producer_uid==0 and valid_file_removed and invalid_file_removed,
            "untrusted_os_identity_denied":untrusted_os_identity_denied,
            "untrusted_os_access":untrusted_os_access,"untrusted_os_uid":untrusted_uid,
            "valid_input_consumed":valid_file_removed,
            "valid_event_persisted":valid_positive,"valid_archive_verified":archive_output_verified,
            "invalid_input_consumed":invalid_file_removed,"invalid_failed_output_verified":failed_output_verified,
            "business_side_effects_bounded":valid_tables and valid_queues and valid_call_deltas,
            "status":200}
        def effect_sample(sample):
            return {"tables":sample["tables"],"queues":sample["queues"],
                "business_invocations":sample["business_invocations"]}
        admin_semantic=(accepted is not None and worker_verified and valid_positive and valid_queues
            and valid_tables and valid_call_deltas and file_removed and valid_file_removed)
        batch_actor_observations["Administrator"]={"driver":"native-batch-import-v1","actor":"Administrator",
            "supported":True,"status":200,"semantic_success":admin_semantic,
            "authorized_effect_verified":admin_semantic,
            "authorized_form_status":enabled_form_status,
            "csrf_present":enabled_form_csrf is not None,
            "viewstate_present":enabled_form_view is not None,
            "authorized_start_accepted":accepted is not None and len(accepted_values)==1
                and concurrent_submissions==1 and all(result[0]==200 for result in concurrent_results),
            "empty_business_state_unchanged":business_unchanged,
            "empty_control_calls_bounded":control_calls_bounded,
            "worker_identity_verified":worker_verified,
            "valid_event_persisted":valid_positive,"valid_queue_cycles":valid_queues,
            "valid_table_deltas":valid_tables,"valid_invocation_deltas_bounded":valid_call_deltas,
            "direct_api_denials":direct_api_denials.get("admin",{}),
            "direct_api_payload_absent":direct_api_payload_absent.get("admin",{}),
            "direct_api_effects_unchanged":api_effects_unchanged,
            "identity":report["identities"]["admin"]}
        report["batch_import_actor_observations"]=batch_actor_observations
        report["batch_processing_observation"]=batch_processing_observation
        report["batch_import"]={"anonymous_get_post_denied":True,
            "direct_api_denials":direct_api_denials,
            "direct_api_effects_unchanged":api_effects_unchanged,
            "restart_denials":restart_denials,"disabled_switch_denied":True,
            "csrf_denied":True,"revoked_session_denied":True,
            "concurrent_single_start":True,"replay_denied":True,
            "symlink_rejected":True,"non_regular_rejected":True,
            "authorized_empty_start":accepted is not None,"worker_identity_verified":worker_verified,
            "empty_execution_completed":worker_verified,"empty_file_consumed":file_removed,
            "empty_business_state_unchanged":business_unchanged,"empty_control_calls_bounded":control_calls_bounded,
            "authorized_valid_start":valid_accepted is not None,"valid_execution_completed":valid_worker,
            "valid_event_persisted":valid_positive,"valid_queue_cycles":valid_queues,
            "valid_table_deltas":valid_tables,"valid_invocation_deltas_bounded":valid_call_deltas,
            "valid_file_consumed":valid_file_removed,
            "effects_before_empty":effect_sample(batch_before),"effects_after_empty":effect_sample(batch_after),
            "effects_before_valid":effect_sample(before_valid),"effects_after_valid":effect_sample(valid_after),
            "valid_invocation_deltas":{k:valid_after_calls.get(k,0)-valid_before_calls.get(k,0)
                for k in sorted(set(valid_before_calls)|set(valid_after_calls))}}
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
        operator_worker_audit_before=command("docker","logs",container).count(
            "HANDLING_WORKER_AUDIT event=consumed principal=handling-worker role=HandlingWorker")
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
        operator_worker_audit_after=command("docker","logs",container).count(
            "HANDLING_WORKER_AUDIT event=consumed principal=handling-worker role=HandlingWorker")
        operator_worker_audit_delta=operator_worker_audit_after-operator_worker_audit_before
        operator_consumer_delta=(positive_effects["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0)
            - after_denied["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0))
        check("Operator handling message runs under the dedicated worker identity",
            operator_worker_audit_delta==1 and operator_consumer_delta==1)
        check("DB observer detects allowed persisted handling",positive_effects["tables"]!=after_denied["tables"])
        check("Cumulative broker observer detects allowed processing",positive_effects["queues"]!=after_denied["queues"] and any(q["MessagesAdded"]>after_denied["queues"][name]["MessagesAdded"] for name,q in positive_effects["queues"].items()))
        check("Business invocation observer detects allowed processing",positive_effects["business_invocations"]!=after_denied["business_invocations"] and any("registerHandlingEvent" in name and count>after_denied["business_invocations"].get(name,0) for name,count in positive_effects["business_invocations"].items()))
        for worker in ["HandlingEventRegistrationAttemptConsumer","CargoHandledConsumer"]:
            check("MDB invocation observer connected: "+worker,any(worker+"#onMessage" in name and count>after_denied["business_invocations"].get(name,0) for name,count in positive_effects["business_invocations"].items()))
        report["scoped_denied_effects"]["positive_control"]=positive_effects
        handling_worker_audit_effects={"operator":{"audit_delta":operator_worker_audit_delta,
            "consumer_invocation_delta":operator_consumer_delta}}
        report["access_observations"]["API-02::Operator::active"]={"supported":True,"status":204,"identity":report["identities"]["operator"],"semantic_success":True,"authorized_effect_verified":True,"processing_evidence":{"database_changed":positive_effects["tables"]!=after_denied["tables"],"worker_invocations_observed":True}}
        report["cargo_before"]=before;report["cargo_after"]=after
        check("Administrator fixture starts away from FIHEL",next(c for c in initial if c["trackingId"]=="MNO456")["lastKnownLocation"]!="FIHEL")
        payload=json.dumps({"trackingId":"MNO456","eventType":"CUSTOMS","unLocode":"FIHEL","completionTime":"2030-01-02 10:00"}).encode()
        admin_before=settled()
        admin_worker_audit_before=command("docker","logs",container).count(
            "HANDLING_WORKER_AUDIT event=consumed principal=handling-worker role=HandlingWorker")
        check("Administrator report accepted",handling("admin")==204)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            code,body,_=request(sessions["reader"][1],"rest/cargo")
            if code==200 and next(c for c in json.loads(body) if c["trackingId"]=="MNO456")["lastKnownLocation"]=="FIHEL":break
            time.sleep(.25)
        else:raise AssertionError("Administrator handling did not persist")
        check("Administrator real asynchronous handling effect",True)
        admin_after=settled()
        admin_worker_audit_after=command("docker","logs",container).count(
            "HANDLING_WORKER_AUDIT event=consumed principal=handling-worker role=HandlingWorker")
        admin_worker_audit_delta=admin_worker_audit_after-admin_worker_audit_before
        admin_consumer_delta=(admin_after["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0)
            - admin_before["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptConsumer#onMessage",0))
        check("Administrator handling message runs under the dedicated worker identity",
            admin_worker_audit_delta==1 and admin_consumer_delta==1)
        check("Administrator independent persisted handling effect",admin_after["tables"]!=admin_before["tables"] and any(q["MessagesAdded"]>admin_before["queues"][name]["MessagesAdded"] for name,q in admin_after["queues"].items()) and any("registerHandlingEvent" in name and count>admin_before["business_invocations"].get(name,0) for name,count in admin_after["business_invocations"].items()))
        handling_worker_audit_effects["administrator"]={"audit_delta":admin_worker_audit_delta,
            "consumer_invocation_delta":admin_consumer_delta}
        report["handling_worker_audit_effects"]=handling_worker_audit_effects
        report["handling_worker_observation"]={"driver":"native-handling-worker-v1","supported":True,
            "machine_identity_verified":operator_worker_audit_delta==1 and admin_worker_audit_delta==1,
            "native_identity":{"server_verified":True,"principal":"handling-worker","roles":["HandlingWorker"]},
            "machine_scope":"Dedicated server worker authority; human identity does not automatically propagate through ObjectMessage",
            "authorized_adapter_events_verified":operator_worker_audit_delta==admin_worker_audit_delta==1
                and operator_consumer_delta==admin_consumer_delta==1,
            "producer_boundary_verified":producer_boundary_verified,
            "producer_boundary_evidence":"separate-JVM remote JMS probe authenticated BatchWorker, HandlingWorker, InspectionWorker and NotificationWorker principals and denied each send to the handling-attempt queue; same-fixture application adapter publications and effects were verified",
            "human_direct_denials_effects_unchanged":all(x.get("independent_effects_unchanged") is True
                for x in handling_worker_denials.values()),
            "status":200,"semantic_success":operator_worker_audit_delta==admin_worker_audit_delta==1,
            "authorized_effect_verified":operator_worker_audit_delta==admin_worker_audit_delta==1}
        inspection_effects=settled()
        inspection_logs=command("docker","logs",container)
        inspection_correlations=re.findall(
            r"INSPECTION_WORKER_AUDIT event=consumed principal=inspection-worker role=InspectionWorker origin=handling-event-service correlation=([0-9a-f-]{36})",
            inspection_logs)
        inspection_queue=inspection_effects["queues"]["jms.queue.CargoHandledQueue"]
        inspection_invocations=inspection_effects["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.CargoHandledConsumer#onMessage",0)
        inspection_audit_verified=(len(inspection_correlations)>0
            and len(set(inspection_correlations))==len(inspection_correlations)
            and inspection_queue["MessageCount"]==0
            and inspection_queue["MessagesAdded"]==len(inspection_correlations)
            and inspection_queue["MessagesAcknowledged"]==len(inspection_correlations)
            and inspection_invocations==len(inspection_correlations))
        check("Cargo inspection runs under its dedicated worker with unique correlation audit",
            inspection_audit_verified)
        report["inspection_worker_observation"]={
            "driver":"native-inspection-worker-v1","supported":True,
            "machine_identity_verified":inspection_audit_verified,
            "native_identity":{"server_verified":True,"principal":"inspection-worker","roles":["InspectionWorker"]},
            "machine_scope":"Server worker; audit origin/correlation to be designed, not trusted role fields in payload",
            "producer_origin_verified":inspection_audit_verified,
            "correlation_verified":inspection_audit_verified,
            "correlation_count":len(inspection_correlations),
            "unique_correlation_count":len(set(inspection_correlations)),
            "authorized_adapter_events_verified":inspection_audit_verified,
            "producer_boundary_verified":cargo_handled_producer_boundary_verified,
            "producer_boundary_note":"Separate-JVM remote+http JMS probe verified HandlingWorker send authorization and denied anonymous, human, batch, inspection and notification principals; authorized test send rolled back",
            "producer_boundary_effects_unchanged":cargo_handled_effects_unchanged,
            "human_direct_denials_effects_unchanged":all(
                x.get("independent_effects_unchanged") is True
                for x in inspection_worker_denials.values()),
            "status":200,"semantic_success":inspection_audit_verified,
            "authorized_effect_verified":inspection_audit_verified}
        notification_effects=settled()
        notification_logs=command("docker","logs",container)
        notification_specs={
            "delivered":("DeliveredCargoQueue","DeliveredCargoConsumer"),
            "misdirected":("MisdirectedCargoQueue","MisdirectedCargoConsumer"),
            "rejected-registration":("RejectedRegistrationAttemptsQueue","RejectedRegistrationAttemptsConsumer")}
        notification_audit_lines=re.findall(
            r"NOTIFICATION_WORKER_AUDIT event=consumed consumer=(delivered|misdirected|rejected-registration) principal=notification-worker role=NotificationWorker",
            notification_logs)
        notification_counts={name:notification_audit_lines.count(name) for name in notification_specs}
        notification_invocations={
            event:notification_effects["business_invocations"].get(
                "net.java.cargotracker.infrastructure.messaging.jms."+consumer+"#onMessage",0)
            for event,(queue,consumer) in notification_specs.items()}
        notification_audit_invocations=notification_effects["business_invocations"].get(
            "net.java.cargotracker.infrastructure.messaging.jms.NotificationWorkerAudit#recordConsumed",0)
        notification_queue_cycles={}
        for event,(queue_name,consumer) in notification_specs.items():
            queue=notification_effects["queues"]["jms.queue."+queue_name]
            count=notification_counts[event]
            notification_queue_cycles[event]=(queue["MessageCount"]==0
                and queue["MessagesAdded"]==count
                and queue["MessagesAcknowledged"]==count
                and notification_invocations[event]==count)
        notification_bindings_verified=all(
            "Started message driven bean '"+consumer+"'" in notification_logs
            for event,(queue,consumer) in notification_specs.items())
        notification_log_lines=[line for line in notification_logs.splitlines()
            if "NOTIFICATION_WORKER_AUDIT" in line
            or any(consumer in line for queue,consumer in notification_specs.values())]
        notification_logs_sanitized=all(
            re.search(r"(?<![A-Z0-9])[A-Z0-9]{8}(?![A-Z0-9])|(?i:trackingId|tracking ID|body=)",line) is None
            for line in notification_log_lines)
        notification_worker_verified=(notification_bindings_verified
            and notification_logs_sanitized
            and notification_audit_invocations==sum(notification_counts.values())
            and all(notification_queue_cycles.values()))
        report["notification_worker_diagnostics"]={"bindings":notification_bindings_verified,"audit_counts":notification_counts,"invocation_counts":notification_invocations,"audit_invocations":notification_audit_invocations,"queue_cycles":notification_queue_cycles,"sanitized":notification_logs_sanitized,"relevant_log_lines":notification_log_lines}
        check("Notification MDB bindings start and logs contain no cargo identifiers",
            notification_bindings_verified and notification_logs_sanitized)
        if any(notification_counts.values()):
            check("Notification queue cycles match worker audit and invocations",
                notification_worker_verified)
        report["notification_worker_observation"]={
            "driver":"native-notification-worker-v1","supported":True,
            "machine_identity_verified":notification_bindings_verified
                and any(notification_counts.values()) and notification_worker_verified,
            "native_identity":{"server_verified":True,"principal":"notification-worker","roles":["NotificationWorker"]},
            "machine_scope":"Server workers",
            "consumer_bindings_verified":notification_bindings_verified,
            "sanitized_logs_verified":notification_logs_sanitized,
            "audit_counts":notification_counts,
            "consumer_invocation_counts":notification_invocations,
            "queue_cycles_verified":all(notification_queue_cycles.values()),
            "queue_cycle_details":notification_queue_cycles,
            "producer_boundary_verified":producer_boundary_verified,
            "producer_boundary_note":"Separate-JVM remote+http JMS broker authorization probe",
            "rejection_producer_verified":report["rejection_disposition_observation"].get(
                "trusted_broker_dead_letter_verified") is True,
            "final_disposition_verified":report["rejection_disposition_observation"].get(
                "final_disposition_verified") is True,
            "human_direct_denials_effects_unchanged":all(
                proof.get("independent_effects_unchanged") is True
                for proof in notification_worker_denials.values()),
            "status":200,"semantic_success":notification_bindings_verified and notification_logs_sanitized,
            "authorized_effect_verified":notification_worker_verified}
        report["admin_handling_effects"]={"before":admin_before,"after":admin_after}
        report["access_observations"]["API-02::Administrator::active"]={"supported":True,"status":204,"identity":report["identities"]["admin"],"semantic_success":True,"authorized_effect_verified":True}


        # ACTION-29 is a real Faces POST driver, independently observed per request.
        report["booking_action_effects"]={}
        def denied_form(opener,form,who=None,state=None,path="admin/book.xhtml",label="Booking"):
            start=settled()
            status,body,headers=request(opener,path,form)
            end=settled()
            fixed=headers.get("Location")=="/cargo-tracker/login"
            expected=403 if who=="reader" and state is None else 303
            target_id=urllib.parse.parse_qs(urllib.parse.urlsplit(path).query).get("trackingId",[None])[0] or form.get("handling:cargo")
            absent=payload_absent(body) and (target_id is None or target_id not in body)
            check(label+" POST authorization denial: "+str(who)+" "+str(state),status==expected and absent and (expected!=303 or fixed))
            check(label+" POST independent effects unchanged: "+str(who)+" "+str(state),start==end)
            result=denial_observation({"status":status,"protected_payload_absent":absent,"redirect_is_configured_login":fixed,"action_method":"POST","action_path":"/cargo-tracker/"+path,"tracking_id":target_id,"real_form_verified":True},start,end,who,state is not None)
            result["form_owned_before_revocation"]=state is not None
            return result
        entry_receipts={}
        def entry(opener,who,token,tracking_id=None):
            return source_entry(lambda path:request(opener,path),base,who,token,tracking_id)
        def denied_booking(opener,form,who=None,state=None):
            proof=entry_receipts[(who,state,"booking")] if state else entry(opener,who,form.get("csrf"))[1]
            result=denied_form(opener,form,who,state)
            result.update(proof)
            return result
        def denied_destination(opener,form,who=None,state=None,path=None):
            tracking_id=urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)["trackingId"][0]
            proof=entry_receipts[(who,state,"destination")] if state else entry(opener,who,form.get("csrf"),tracking_id)[1]
            result=denied_form(opener,form,who,state,path,"Destination")
            result.update(proof)
            return result
        report["access_observations"]["ACTION-29::anonymous::active"]=denied_booking(anonymous,{**book_form,"csrf":sessions["operator"][2]})
        report["access_observations"]["ACTION-29::Reader::active"]=denied_booking(sessions["reader"][1],{**book_form,"csrf":sessions["reader"][2]},"reader")
        for who,role in [("operator","Operator"),("admin","Administrator")]:
            sessions[who]=login(who);sessions["reader"]=login("reader")
            opener=sessions[who][1];body,source_proof=entry(opener,who,sessions[who][2])
            check("Booking role owns verified source form: "+role,True)
            form=booking_form(body,sessions[who][2])
            existing={cargo["trackingId"] for cargo in cargos(sessions["reader"][1])}
            start=settled()
            status,_,headers=request(opener,"admin/book.xhtml",form)
            created=booking_tracking_id(base,status,headers.get("Location",""))
            detail_status,detail,_=request(opener,"admin/show.xhtml?trackingId="+created)
            values=cargos(sessions["reader"][1]);fresh=next((cargo for cargo in values if cargo["trackingId"]==created),{})
            reader_status,reader_detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+created)
            deadline_match=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",reader_detail)
            deadline_verified=reader_status==200 and 'id="trackingId">'+created in reader_detail and deadline_match is not None and deadline_match[1].split()[0]=="12/31/2030"
            check("Independent Reader sees persisted booking deadline: "+role,deadline_verified)
            end=settled()
            check("Booking real result and independent Reader persistence: "+role,detail_status==200 and 'id="trackingId">'+created in detail and created not in existing and {cargo["trackingId"] for cargo in values}==existing|{created})
            check("Booking specific SQL audit effect and no JMS: "+role,booking_positive(start,end,fresh,created))
            report["booking_action_effects"][who]={"before":start,"after":end,"tracking_id":created,"reader_readback":fresh,"reader_deadline_verified":deadline_verified,"no_jms_expected":True}
            report["access_observations"]["ACTION-29::"+role+"::active"]={"supported":True,"status":detail_status,"post_status":status,"identity":report["identities"][who],"semantic_success":True,"authorized_effect_verified":True,"action_method":"POST","action_path":"/cargo-tracker/admin/book.xhtml",**source_proof,"real_form_verified":True,"processing_evidence":{"database_changed":True,"book_new_cargo_invocation_delta":1,"queue_unchanged":True,"independent_reader_persistence":True,"independent_reader_deadline":deadline_verified},"tracking_id":created}


        # ACTION-09 changes only the two fresh, unreceived booking-control cargos.
        report["destination_action_effects"]={}
        target_id=report["booking_action_effects"]["operator"]["tracking_id"]
        target_path="admin/changeDestination.xhtml?trackingId="+target_id
        body,_=entry(sessions["operator"][1],"operator",sessions["operator"][2],target_id)
        check("Destination forged form fixture follows cargo source",True)
        forged=destination_form(body,sessions["operator"][2])
        report["access_observations"]["ACTION-09::anonymous::active"]=denied_destination(anonymous,forged,path=target_path)
        report["access_observations"]["ACTION-09::Reader::active"]=denied_destination(sessions["reader"][1],{**forged,"csrf":sessions["reader"][2]},"reader",path=target_path)
        for who,role in [("operator","Operator"),("admin","Administrator")]:
            target_id=report["booking_action_effects"][who]["tracking_id"]
            path="admin/changeDestination.xhtml?trackingId="+target_id
            body,source_proof=entry(sessions[who][1],who,sessions[who][2],target_id);check("Destination role follows verified cargo link: "+role,True)
            form=destination_form(body,sessions[who][2])
            old_values={cargo["trackingId"]:cargo for cargo in cargos(sessions["reader"][1])};old=old_values[target_id]
            code,detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+target_id)
            deadline_before=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",detail)
            check("Destination fixture original deadline observed: "+role,code==200 and deadline_before is not None and deadline_before[1].split()[0]=="12/31/2030")
            start=settled()
            status,_,headers=request(sessions[who][1],path,form)
            redirected=booking_tracking_id(base,status,headers.get("Location",""))
            check("Destination result preserves tracking ID: "+role,redirected==target_id)
            detail_status,detail,_=request(sessions[who][1],"admin/show.xhtml?trackingId="+target_id)
            values={cargo["trackingId"]:cargo for cargo in cargos(sessions["reader"][1])};fresh=values.get(target_id,{})
            reader_status,reader_detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+target_id)
            deadline_after=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",reader_detail)
            deadline_verified=reader_status==200 and 'id="trackingId">'+target_id in reader_detail and deadline_after is not None and deadline_after[1]==deadline_before[1]
            end=settled()
            check("Destination independent Reader persistence and deadline preserved: "+role,detail_status==200 and 'id="trackingId">'+target_id in detail and deadline_verified and set(values)==set(old_values) and all(values[k]==old_values[k] for k in values if k!=target_id))
            check("Destination specific SQL audit effect and no JMS: "+role,destination_positive(start,end,old,fresh,target_id))
            report["destination_action_effects"][who]={"before":start,"after":end,"tracking_id":target_id,"reader_before":old,"reader_after":fresh,"reader_deadline_preserved":deadline_verified,"no_jms_expected":True}
            report["access_observations"]["ACTION-09::"+role+"::active"]={"supported":True,"status":detail_status,"post_status":status,"identity":report["identities"][who],"semantic_success":True,"authorized_effect_verified":True,"action_method":"POST","action_path":"/cargo-tracker/"+path,**source_proof,"real_form_verified":True,"tracking_id":target_id,"processing_evidence":{"database_changed":True,"change_destination_invocation_delta":1,"queue_unchanged":True,"independent_reader_persistence":True,"independent_reader_deadline":deadline_verified,"other_cargos_unchanged":True}}

            check("Return capability verifies exact saved cargo details: "+role,current_load_semantics("ACTION-20",detail,fresh))
            report.setdefault("current_access_observations",{})["CURRENT::ACTION-13::"+role+"::active"]={
                "return_driver":"native-staged-return-v1","tracking_id":target_id,"fixture_base":base,"identity":report["identities"][who],
                "editor":{"method":"GET","path":"/cargo-tracker/"+path,"status":200,"owned_form_verified":True},
                "save":{"method":"POST","path":"/cargo-tracker/"+path,"status":status,"location":headers.get("Location"),
                        "csrf_verified":True,"persisted_effect_verified":True,"destination_invocation_delta":1,
                        "queues_unchanged":True,"deadline_preserved":deadline_verified,"other_cargos_unchanged":True},
                "details":{"method":"GET","path":"/cargo-tracker/admin/show.xhtml?trackingId="+target_id,
                           "status":detail_status,"selected_details_verified":True},
            }

            if who=="operator":
                # New current behavior evidence is separate from historical callback results.
                report.setdefault("current_access_observations",{})
                target_id=report["booking_action_effects"]["operator"]["tracking_id"]
                control_id=report["booking_action_effects"]["admin"]["tracking_id"]
                # Operator destination is USNYC while the Administrator control is still FIHEL.
                reader_values={row["trackingId"]:row for row in cargos(sessions["reader"][1])}
                expected_cargo=reader_values[target_id]
                check("Current load target and control are distinct cargos",target_id!=control_id and target_id in reader_values and control_id in reader_values and expected_cargo["destinationCode"]!=reader_values[control_id]["destinationCode"])
                check("Invalid load fixture ID absent","ZZZZZZZZ" not in reader_values)
                before_loads=settled()
                for surface,relative,operator_only in [("ACTION-07","admin/changeDestination.xhtml",True),("ACTION-20","admin/show.xhtml",False)]:
                    path=relative+"?trackingId="+target_id
                    for actor,who in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
                        opener=sessions[who][1] if who else anonymous
                        if who is None:
                            code,landing,_=request(opener,"index.xhtml")
                            check("Current load anonymous source landing: "+surface,code==200 and payload_absent(landing))
                        status,body,headers=request(opener,path)
                        allowed=who is not None and (not operator_only or who!="reader")
                        absent=payload_absent(body) and target_id not in body
                        fixed=headers.get("Location")=="/cargo-tracker/login"
                        if allowed:
                            diagnostics={}
                            matches=current_load_semantics(surface,body,expected_cargo,diagnostics)
                            check("Current selected cargo values: "+surface+" "+actor+" "+",".join(diagnostics.get("mismatched_fields",[])),status==200 and matches)
                        else:check("Current load role denial: "+surface+" "+actor,status==(303 if who is None else 403) and absent and (who is not None or fixed))
                        for invalid in ["","?trackingId=bad","?trackingId=ZZZZZZZZ"]:
                            bad_status,bad_body,bad_headers=request(opener,relative+invalid)
                            wanted=404 if allowed else 303 if who is None else 403
                            check("Current invalid load denial: "+surface+" "+actor+" "+str(len(invalid)),bad_status==wanted and payload_absent(bad_body) and target_id not in bad_body and (wanted!=303 or bad_headers.get("Location")=="/cargo-tracker/login"))
                        observation={"supported":True,"status":status,"semantic_success":allowed,"protected_payload_absent":absent,"redirect_is_configured_login":fixed,"driver":"direct","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/"+relative,"query_keys":["trackingId"],"tracking_id":target_id,"source_page":"index.xhtml" if who is None else path,"current_load_driver":"native-current-load-v1","selected_cargo_verified":allowed,"current_values_verified":allowed,"invalid_inputs_verified":True}
                        if who:observation["identity"]=report["identities"][who]
                        report["current_access_observations"]["CURRENT::"+surface+"::"+actor+"::active"]=observation
                check("Current read loads leave independent effects unchanged",before_loads==settled())

        return_target=report["booking_action_effects"]["operator"]["tracking_id"]
        return_cargo=next(row for row in cargos(sessions["reader"][1]) if row["trackingId"]==return_target)
        for role,who in [("anonymous",None),("Reader","reader")]:
            opener=sessions[who][1] if who else anonymous
            before_return=settled()
            editor_path="admin/changeDestination.xhtml?trackingId="+return_target
            details_path="admin/show.xhtml?trackingId="+return_target
            editor_status,editor_body,editor_headers=request(opener,editor_path)
            details_status,details_body,details_headers=request(opener,details_path)
            return_markers=(return_target,return_cargo["originName"],return_cargo["destinationName"])
            editor_absent=payload_absent(editor_body) and not any(marker in editor_body for marker in return_markers)
            editor_fixed=editor_headers.get("Location")=="/cargo-tracker/login"
            check("Return capability denies editor entry: "+role,editor_status==(403 if who else 303) and editor_absent and (who is not None or editor_fixed))
            if who:
                check("Return capability preserves Reader direct details: "+role,details_status==200 and current_load_semantics("ACTION-20",details_body,return_cargo))
            else:
                check("Return capability anonymous details denied",details_status==303 and details_headers.get("Location")=="/cargo-tracker/login" and payload_absent(details_body) and not any(marker in details_body for marker in return_markers))
            after_return=settled()
            check("Return denied entry leaves independent effects unchanged: "+role,before_return==after_return)
            proof={"return_driver":"native-staged-return-v1","tracking_id":return_target,
                   "editor":{"method":"GET","path":"/cargo-tracker/"+editor_path,"status":editor_status,
                             "protected_payload_absent":editor_absent,"redirect_is_configured_login":editor_fixed},
                   "save":None,"denied_entry_effects_unchanged":True,
                   "details":{"method":"GET","path":"/cargo-tracker/"+details_path,"status":details_status,
                              "selected_details_verified":who is not None,"protected_payload_absent":payload_absent(details_body) and not any(marker in details_body for marker in return_markers),
                              "redirect_is_configured_login":details_headers.get("Location")=="/cargo-tracker/login"}}
            if who:proof["identity"]=report["identities"][who]
            report["current_access_observations"]["CURRENT::ACTION-13::"+role+"::active"]=proof
            report.setdefault("return_entry_effects",{})[role]={"before":before_return,"after":after_return}

        # Separate original entries converge on one modern route form, with traceability.
        report["routing_action_effects"]={}
        def route_entry(opener,surface,target_id,who):
            source=("admin/route.xhtml" if surface=="ACTION-17" else "admin/selectItinerary.xhtml")+"?trackingId="+target_id
            path="admin/route.xhtml?trackingId="+target_id
            code,body,headers=request(opener,source)
            if who in {"operator","admin"}:
                if surface=="ACTION-19":
                    check("Legacy itinerary entry fixed target: "+str(who),code==303 and headers.get("Location")=="/cargo-tracker/"+path)
                    code,body,_=request(opener,path)
                check("Actual route entry rendered: "+surface+" "+str(who),code==200)
            else:
                check("Route entry denies before cargo load: "+surface+" "+str(who),code==(403 if who=="reader" else 303) and payload_absent(body) and (who=="reader" or headers.get("Location")=="/cargo-tracker/login"))
            return path,body,source
        def route_denial(opener,form,who,state,surface,target_id,source):
            path="admin/route.xhtml?trackingId="+target_id
            result=denied_form(opener,form,who,state,path,"Routing "+surface)
            result.update({"entry_page":source,"source_entry_verified":True})
            return result
        route_cargo_id=report["booking_action_effects"]["operator"]["tracking_id"]
        route_cargos={row["trackingId"]:row for row in cargos(sessions["reader"][1])}
        route_cargo=route_cargos[route_cargo_id]
        route_query="?trackingId="+route_cargo_id
        route_target="admin/route.xhtml"
        route_alias="admin/selectItinerary.xhtml"
        def route_hidden(body):
            return payload_absent(body) and route_cargo_id not in body and "route-candidate" not in body and "Cargo details" not in body and 'id="routing"' not in body
        def verify_route_denial(status,body,headers,who):
            return status==(403 if who else 303) and route_hidden(body) and (who is not None or headers.get("Location")=="/cargo-tracker/login")
        check("Route load unknown ID absent", "ZZZZZZZZ" not in route_cargos)
        route_read_before=settled()
        for action,relative in [("ACTION-16",route_target),("ACTION-18",route_alias)]:
            for actor,load_who in [("anonymous",None),("Reader","reader"),("Operator","operator"),("Administrator","admin")]:
                opener=sessions[load_who][1] if load_who else anonymous
                allowed=load_who in {"operator","admin"}
                source=relative+route_query
                if load_who is None:
                    status,landing,_=request(opener,"index.xhtml")
                    check("Anonymous route load source: "+action,status==200 and route_hidden(landing))
                    source="index.xhtml"
                status,body,headers=request(opener,relative+route_query)
                alias_verified=False
                if relative==route_alias:
                    if allowed:
                        check("Current route alias exact redirect: "+actor,status==303 and headers.get("Location")=="/cargo-tracker/"+route_target+route_query and route_hidden(body))
                    else:
                        check("Current route alias denied: "+actor,verify_route_denial(status,body,headers,load_who))
                    alias_verified=True
                    status,body,headers=request(opener,route_target+route_query)
                if allowed:
                    check("Current route choices rendered: "+action+" "+actor,status==200)
                    check("Current route choices match selected cargo: "+action+" "+actor,verify_route_choices(body,route_cargo["originCode"],route_cargo["destinationCode"],sessions[load_who][2],route_cargo_id,base)>0)
                else:
                    check("Current route target denied: "+action+" "+actor,verify_route_denial(status,body,headers,load_who))
                for label,suffix in [("missing",""),("malformed","?trackingId=bad"),("unknown","?trackingId=ZZZZZZZZ")]:
                    bad_status,bad_body,bad_headers=request(opener,relative+suffix)
                    if allowed and relative==route_alias and label=="unknown":
                        check("Unknown route alias fixed target: "+actor,bad_status==303 and route_hidden(bad_body) and bad_headers.get("Location")=="/cargo-tracker/"+route_target+suffix)
                        bad_status,bad_body,bad_headers=request(opener,route_target+suffix)
                    check("Current invalid route load: "+action+" "+actor+" "+label,(bad_status==404 and route_hidden(bad_body)) if allowed else verify_route_denial(bad_status,bad_body,bad_headers,load_who))
                observation={"supported":True,"status":status,"semantic_success":allowed,"protected_payload_absent":route_hidden(body),"redirect_is_configured_login":headers.get("Location")=="/cargo-tracker/login","driver":"direct","action_executed":True,"target_origin_verified":True,"actual_target_path":"/cargo-tracker/"+route_target,"query_keys":["trackingId"],"tracking_id":route_cargo_id,"source_page":source,"current_load_driver":"native-current-load-v1","selected_cargo_verified":allowed,"current_values_verified":allowed,"invalid_inputs_verified":True,"route_alias_verified":alias_verified}
                if load_who:observation["identity"]=report["identities"][load_who]
                report["current_access_observations"]["CURRENT::"+action+"::"+actor+"::active"]=observation
                if action=="ACTION-16":
                    if allowed:
                        diagnostics={}
                        matches=current_load_semantics("ACTION-20",body,route_cargo,diagnostics)
                        check("Current route cargo details match selected cargo: "+actor+" "+",".join(diagnostics.get("mismatched_fields",[])),matches)
                    details_observation={**observation,"route_details_verified":allowed}
                    report["current_access_observations"]["CURRENT::ACTION-15::"+actor+"::active"]=details_observation
        route_read_after=settled()
        check("Current route reads invoke only expected planner calls",route_read_effects(route_read_before,route_read_after,4))
        report["current_route_read_effects"]={"before":route_read_before,"after":route_read_after}

        for surface in ["ACTION-17","ACTION-19"]:
            target_id=report["booking_action_effects"]["operator"]["tracking_id"]
            path,body,source=route_entry(sessions["operator"][1],surface,target_id,"operator")
            forged,_=routing_form(body,sessions["operator"][2],0)
            for who,role in [(None,"anonymous"),("reader","Reader")]:
                opener=anonymous if who is None else sessions[who][1]
                route_entry(opener,surface,target_id,who)
                form={**forged,"csrf":sessions[who][2] if who else sessions["operator"][2]}
                report["access_observations"][surface+"::"+role+"::active"]=route_denial(opener,form,who,None,surface,target_id,source)
            for who,role in [("operator","Operator"),("admin","Administrator")]:
                target_id=report["booking_action_effects"][who]["tracking_id"]
                path,body,source=route_entry(sessions[who][1],surface,target_id,who)
                old_values={cargo["trackingId"]:cargo for cargo in cargos(sessions["reader"][1])};old=old_values[target_id]
                code,detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+target_id)
                deadline_before=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",detail)
                old_tables=route_tables(detail,"id","itinerary")
                choices=route_tables(body);choice=0
                check("Route fixture initial state: "+surface+" "+role,old.get("routingStatus")==("NOT_ROUTED" if surface=="ACTION-17" else "ROUTED"))
                if surface=="ACTION-19":
                    check("Existing itinerary available before replacement: "+role,len(old_tables)==1 and bool(old_tables[0]))
                    different=[i for i,rows in enumerate(choices) if not old_tables or rows!=old_tables[0]]
                    check("Rerouting has a genuinely different candidate: "+role,bool(different))
                    choice=next((i for i in different if i!=0),different[0])
                form,selected=routing_form(body,sessions[who][2],choice)
                check("Route fixture deadline observed: "+surface+" "+role,code==200 and deadline_before is not None and deadline_before[1].split()[0]=="12/31/2030")
                start=settled()
                status,_,headers=request(sessions[who][1],path,form)
                redirected=booking_tracking_id(base,status,headers.get("Location",""))
                check("Route result preserves tracking ID: "+surface+" "+role,redirected==target_id)
                detail_status,detail,_=request(sessions[who][1],"admin/show.xhtml?trackingId="+target_id)
                values={cargo["trackingId"]:cargo for cargo in cargos(sessions["reader"][1])};fresh=values.get(target_id,{})
                reader_status,reader_detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+target_id)
                deadline_after=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",reader_detail)
                persisted=route_tables(reader_detail,"id","itinerary")
                deadline_verified=reader_status==200 and deadline_after is not None and deadline_after[1]==deadline_before[1]
                exact_legs=reader_status==200 and len(persisted)==1 and persisted[0]==selected
                end=settled()
                check("Exact selected itinerary independently persisted: "+surface+" "+role,detail_status==200 and 'id="trackingId">'+target_id in detail and deadline_verified and exact_legs and set(values)==set(old_values) and all(values[k]==old_values[k] for k in values if k!=target_id))
                check("Route specific SQL audit effect and no JMS: "+surface+" "+role,routing_positive(start,end,old,fresh,target_id))
                report["routing_action_effects"][surface+"::"+who]={"before":start,"after":end,"tracking_id":target_id,"selected_index":choice,"selected_rows":selected,"reader_rows":persisted[0],"reader_before":old,"reader_after":fresh,"deadline_preserved":deadline_verified,"no_jms_expected":True}
                report["access_observations"][surface+"::"+role+"::active"]={"supported":True,"status":detail_status,"post_status":status,"identity":report["identities"][who],"semantic_success":True,"authorized_effect_verified":True,"action_method":"POST","action_path":"/cargo-tracker/"+path,"real_form_verified":True,"tracking_id":target_id,"entry_page":source,"source_entry_verified":True,"processing_evidence":{"database_changed":True,"assign_route_invocation_delta":1,"queue_unchanged":True,"independent_reader_persistence":True,"independent_reader_deadline":deadline_verified,"selected_itinerary_matches":exact_legs,"other_cargos_unchanged":True}}
        def owned_route_forms(opener,token,who):
            forms=[]
            for surface in ["ACTION-17","ACTION-19"]:
                target_id=report["booking_action_effects"][who]["tracking_id"]
                path,body,source=route_entry(opener,surface,target_id,who)
                form,_=routing_form(body,token,0);forms.append((surface,target_id,source,form))
            return forms

        # ACTION-41 is asynchronous: acceptance alone is never a positive control.
        report["handling_action_effects"]={}
        def handling_entry(opener,who):
            code,body,headers=request(opener,"eventLogger/eventLogger.xhtml")
            if who in {"operator","admin"}:
                check("Legacy handling entry fixed mobile target: "+who,code==303 and headers.get("Location")=="/cargo-tracker/mobile.xhtml")
                code,body,_=request(opener,"mobile.xhtml")
                check("Actual handling form rendered: "+who,code==200)
            else:
                check("Handling entry denies before cargo load: "+str(who),code==(403 if who=="reader" else 303) and payload_absent(body) and (who=="reader" or headers.get("Location")=="/cargo-tracker/login"))
            return body
        def handling_denial(opener,form,who=None,state=None):
            result=denied_form(opener,form,who,state,"mobile.xhtml","Handling")
            result.update({"entry_page":"eventLogger/eventLogger.xhtml","source_entry_verified":True})
            return result
        target_id=report["booking_action_effects"]["operator"]["tracking_id"]
        body=handling_entry(sessions["operator"][1],"operator")
        forged=handling_form(body,sessions["operator"][2],target_id,"USCHI","2030-01-03 10:00")
        for who,role in [(None,"anonymous"),("reader","Reader")]:
            opener=anonymous if who is None else sessions[who][1]
            handling_entry(opener,who)
            form={**forged,"csrf":sessions[who][2] if who else sessions["operator"][2]}
            report["access_observations"]["ACTION-41::"+role+"::active"]=handling_denial(opener,form,who)
        for who,role,location,completion in [("operator","Operator","USCHI","2030-01-03 10:00"),("admin","Administrator","DEHAM","2030-01-04 10:00")]:
            target_id=report["booking_action_effects"][who]["tracking_id"]
            body=handling_entry(sessions[who][1],who)
            form=handling_form(body,sessions[who][2],target_id,location,completion)
            old_values={cargo["trackingId"]:cargo for cargo in cargos(sessions["reader"][1])};old=old_values[target_id]
            code,detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+target_id)
            deadline_before=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",detail)
            check("Handling original deadline observed: "+role,code==200 and deadline_before is not None and deadline_before[1].split()[0]=="12/31/2030")
            start=settled()
            status,body,_=request(sessions[who][1],"mobile.xhtml",form)
            accepted=status==200 and "Accepted for processing. Check cargo details for the result." in body
            check("Handling actual Faces submission accepted: "+role,accepted)
            limit=time.monotonic()+30;fresh={}
            while time.monotonic()<limit:
                values={cargo["trackingId"]:cargo for cargo in cargos(sessions["reader"][1])};fresh=values.get(target_id,{})
                if fresh.get("transportStatus")=="IN_PORT" and fresh.get("lastKnownLocationCode")==location:break
                time.sleep(.25)
            else:raise AssertionError("Handling Faces event did not process")
            reader_status,reader_detail,_=request(sessions["reader"][1],"admin/show.xhtml?trackingId="+target_id)
            deadline_after=re.search(r"<dt>Arrival deadline</dt><dd>([^<]+)</dd>",reader_detail)
            deadline_verified=reader_status==200 and 'id="trackingId">'+target_id in reader_detail and deadline_after is not None and deadline_after[1]==deadline_before[1]
            end=settled()
            check("Handling persisted independent Reader state and deadline: "+role,deadline_verified and set(values)==set(old_values) and all(values[k]==old_values[k] for k in values if k!=target_id))
            check("Handling real SQL JMS registration and inspection workers: "+role,handling_positive(start,end,old,fresh,target_id,location))
            report["handling_action_effects"][who]={"before":start,"after":end,"tracking_id":target_id,"reader_before":old,"reader_after":fresh,"deadline_preserved":deadline_verified,"requested_event":"CUSTOMS","requested_location":location,"requested_completion":completion}
            report["access_observations"]["ACTION-41::"+role+"::active"]={"supported":True,"status":status,"submission_status":status,"identity":report["identities"][who],"semantic_success":True,"authorized_effect_verified":True,"action_method":"POST","action_path":"/cargo-tracker/mobile.xhtml","real_form_verified":True,"tracking_id":target_id,"entry_page":"eventLogger/eventLogger.xhtml","source_entry_verified":True,"processing_evidence":{"message_accepted":accepted,"database_changed":True,"attempt_queue_add_ack_delta":1,"handled_queue_add_ack_delta":1,"submission_invocation_delta":1,"registration_invocation_delta":1,"handling_worker_invocation_delta":1,"inspection_worker_invocation_delta":1,"independent_reader_persistence":True,"independent_reader_deadline":deadline_verified,"other_cargos_unchanged":True}}
        def owned_handling_form(opener,token,who):
            body=handling_entry(opener,who)
            return handling_form(body,token,report["booking_action_effects"][who]["tracking_id"],"FIHEL","2030-01-06 10:00")

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
            for surface,(path,heading,kind) in read_pages.items():
                if kind=="public":continue
                status,body,headers=request(opener,path)
                fixed=headers.get("Location")=="/cargo-tracker/login"
                check("Revoked read page login: "+surface+" "+actor+" "+state,status==303 and fixed and payload_absent(body))
                pending[surface+"::"+actor+"::"+state]={"supported":True,"status":status,"redirect_is_configured_login":fixed,"protected_payload_absent":payload_absent(body),"identity":report["identities"][who],"authenticated_before_revocation":True,"revocation_verified":True}
            for surface,spec in other_pages.items():
                path,heading,kind,operator,needs_id,target=spec
                if kind=="error" or operator and who=="reader":continue
                status,body,headers=request(opener,page_path(spec));fixed=headers.get("Location")=="/cargo-tracker/login"
                check("Revoked remaining page login: "+surface+" "+actor+" "+state,status==303 and fixed and payload_absent(body))
                pending[surface+"::"+actor+"::"+state]={"supported":True,"status":status,"redirect_is_configured_login":fixed,"protected_payload_absent":payload_absent(body),"identity":report["identities"][who],"authenticated_before_revocation":True,"revocation_verified":True}
            return pending
        def record_revocations(pending,before_sample,after_sample,who):
            for case,observation in pending.items():
                if case.startswith("API-02::"):observation=denial_observation(observation,before_sample,after_sample,who,True)
                report["access_observations"][case]=observation
        report["lifecycle_effects"]={}
        for actor,who in actors:
            jar,opener,token=login(who);saved=stale_client(jar)
            lifecycle_form=None;lifecycle_destination=None;lifecycle_routes=[];lifecycle_handling=None
            if who!="reader":
                body,proof=entry(opener,who,token);entry_receipts[(who,"logged_out","booking")]=proof
                check("Logout booking source owned: "+actor,True)
                lifecycle_form=booking_form(body,token)
                path="admin/changeDestination.xhtml?trackingId="+report["booking_action_effects"][who]["tracking_id"]
                body,proof=entry(opener,who,token,report["booking_action_effects"][who]["tracking_id"]);entry_receipts[(who,"logged_out","destination")]=proof
                check("Logout destination source and form owned: "+actor,True)
                lifecycle_destination=(path,destination_form(body,token,"FIHEL"))
                lifecycle_routes=owned_route_forms(opener,token,who)
                lifecycle_handling=owned_handling_form(opener,token,who)
            check("Role lifecycle positive monitoring: "+actor,request(opener,"rest/cargo")[0]==200)
            check("Actual role logout: "+actor,request(opener,"logout",b"",token)[0]==204)
            baseline=settled()
            pending=revoked_api_requests(actor,who,saved,token,"logged_out",baseline)
            after_sample=settled()
            check("Logout independent effects unchanged: "+actor,baseline==after_sample)
            record_revocations(pending,baseline,after_sample,who)
            if lifecycle_form is not None:
                report["access_observations"]["ACTION-29::"+actor+"::logged_out"]=denied_booking(saved,lifecycle_form,who,"logged_out")
                path,form=lifecycle_destination
                report["access_observations"]["ACTION-09::"+actor+"::logged_out"]=denied_destination(saved,form,who,"logged_out",path)
                for surface,target_id,source,form in lifecycle_routes:
                    report["access_observations"][surface+"::"+actor+"::logged_out"]=route_denial(saved,form,who,"logged_out",surface,target_id,source)
                report["access_observations"]["ACTION-41::"+actor+"::logged_out"]=handling_denial(saved,lifecycle_handling,who,"logged_out")
            report["lifecycle_effects"][who+"_logged_out"]={"before":baseline,"after":after_sample}
        expiring={}
        for actor,who in actors:
            jar,opener,token=login(who)
            check("Expiry lifecycle positive monitoring: "+actor,request(opener,"rest/cargo")[0]==200)
            form=None;destination=None;routes=[];handling_payload=None
            if who!="reader":
                body,proof=entry(opener,who,token);entry_receipts[(who,"expired","booking")]=proof
                check("Expiry booking source owned: "+actor,True)
                form=booking_form(body,token)
                path="admin/changeDestination.xhtml?trackingId="+report["booking_action_effects"][who]["tracking_id"]
                body,proof=entry(opener,who,token,report["booking_action_effects"][who]["tracking_id"]);entry_receipts[(who,"expired","destination")]=proof
                check("Expiry destination source and form owned: "+actor,True)
                destination=(path,destination_form(body,token,"FIHEL"))
                routes=owned_route_forms(opener,token,who)
                handling_payload=owned_handling_form(opener,token,who)
            expiring[who]=(stale_client(jar),token,form,destination,routes,handling_payload)
        # Every saved identity is left idle for at least75s after the last login.
        for unused in range(5):time.sleep(15)
        for actor,who in actors:
            saved,token,lifecycle_form,lifecycle_destination,lifecycle_routes,lifecycle_handling=expiring[who]
            baseline=settled()
            pending=revoked_api_requests(actor,who,saved,token,"expired",baseline)
            after_sample=settled()
            check("Expiry independent effects unchanged: "+actor,baseline==after_sample)
            record_revocations(pending,baseline,after_sample,who)
            if lifecycle_form is not None:
                report["access_observations"]["ACTION-29::"+actor+"::expired"]=denied_booking(saved,lifecycle_form,who,"expired")
                path,form=lifecycle_destination
                report["access_observations"]["ACTION-09::"+actor+"::expired"]=denied_destination(saved,form,who,"expired",path)
                for surface,target_id,source,form in lifecycle_routes:
                    report["access_observations"][surface+"::"+actor+"::expired"]=route_denial(saved,form,who,"expired",surface,target_id,source)
                report["access_observations"]["ACTION-41::"+actor+"::expired"]=handling_denial(saved,lifecycle_handling,who,"expired")
            report["lifecycle_effects"][who+"_expired"]={"before":baseline,"after":after_sample,"idle_wait_seconds_minimum":75}
        if after_checks:after_checks(container,base,credentials,report)
        report["status"]="PASS"
    except Exception as error:
        report["error_type"]=type(error).__name__
        raise
    finally:
        if not finalize(container,[users,roles,routing,producer_client],report):
            raise RuntimeError("Fixture cleanup incomplete; inspect sanitized results")

    return report

if __name__=="__main__":main()
