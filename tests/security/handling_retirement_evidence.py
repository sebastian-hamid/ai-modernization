"""Pinned rendered legacy callback request shapes and candidate alias source evidence for KAN-15."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/"notes/evidence/kan-15-handling-callback-retirement/legacy-rendered-callbacks.json"
CAPTURE_SHA256="a0f2eb78c8f3c0698f35fd5b2c2cec109a9c2eecc608ae78742c6961a4d113cb"
CALLBACKS={
    "ACTION-36":{"source_component_id":"firstScreen:firstForm:trackingId","behavior_event":"valueChange","partial_event":"change","execute":"firstScreen:firstForm:trackingId","render":"firstScreen:firstForm firstScreen:nextBtn","callback_input_name":"firstScreen:firstForm:trackingId","selected_value":"ABC123"},
    "ACTION-37":{"source_component_id":"firstScreen:firstForm:portCode","behavior_event":"valueChange","partial_event":"change","execute":"firstScreen:firstForm:portCode","render":"firstScreen:nextBtn","callback_input_name":"firstScreen:firstForm:portCode","selected_value":"USCHI"},
    "ACTION-38":{"source_component_id":"firstScreen:firstForm:eventType","behavior_event":"valueChange","partial_event":"change","execute":"firstScreen:firstForm:eventType","render":"firstScreen:firstForm:panelVoyage firstScreen:nextBtn","callback_input_name":"firstScreen:firstForm:eventType","selected_value":"LOAD"},
    "ACTION-39":{"source_component_id":"firstScreen:firstForm:voyage","behavior_event":"valueChange","partial_event":"change","execute":"firstScreen:firstForm:voyage","render":"firstScreen:nextBtn","callback_input_name":"firstScreen:firstForm:voyage","selected_value":"0100S"},
    "ACTION-42":{"source_component_id":"secondScreen:j_idt31:completionDate","behavior_event":"dateSelect","partial_event":"dateSelect","execute":"secondScreen:j_idt31:completionDate","render":"secondScreen:j_idt28:subBtn","callback_input_name":"secondScreen:j_idt31:completionDate_input","selected_value":"11-17-2026"},
}
SOURCE_FILES={
    "legacy_handling_page_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/eventLogger/eventLogger.xhtml",
    "legacy_handling_flow_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/eventLogger/eventLogger-flow.xml",
    "legacy_flow_starter_sha256":ROOT/"experiments/legacy-cargotracker/src/main/webapp/mobile.xhtml",
    "legacy_handling_bean_sha256":ROOT/"experiments/legacy-cargotracker/src/main/java/net/java/cargotracker/interfaces/handling/mobile/EventBackingBean.java",
    "candidate_navigation_servlet_sha256":ROOT/"candidate/cargotracker/src/main/java/net/java/cargotracker/interfaces/booking/web/LegacyNavigationServlet.java",
    "candidate_access_routes_sha256":ROOT/"candidate/cargotracker/src/main/webapp/WEB-INF/access-routes.tsv",
    "candidate_handling_page_sha256":ROOT/"candidate/cargotracker/src/main/webapp/mobile.xhtml",
}

def load_source_evidence():
    raw=CAPTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CAPTURE_SHA256:
        raise ValueError("Legacy callback capture changed after the observed run")
    capture=json.loads(raw)
    capture_script=ROOT/"notes/evidence/kan-15-handling-callback-retirement/capture-rendered-callbacks.cjs"
    if (not capture_script.is_file()
            or hashlib.sha256(capture_script.read_bytes()).hexdigest()!=capture.get("capture_script_sha256")):
        raise ValueError("Rendered callback capture script differs from its pinned hash")
    if (capture.get("legacy_source_revision")!="57fc7b32d2597e43b5e0d454e707e0146de5258a"
            or capture.get("entry_path")!="/cargo-tracker/mobile.xhtml"
            or capture.get("rendered_flow_path")!="/cargo-tracker/eventLogger/eventLogger.xhtml"
            or capture.get("entry_response_status")!=200
            or capture.get("capture_method")!="Playwright browser-generated request capture; dynamic ViewState and ClientWindow values redacted"
            or capture.get("privacy")!={"raw_viewstate_retained":False,"session_cookie_retained":False,"passwords_retained":False}):
        raise ValueError("Legacy callback capture scope or privacy changed")
    raw_sources={key:path.read_bytes() for key,path in SOURCE_FILES.items()}
    source_hashes={key:hashlib.sha256(value).hexdigest() for key,value in raw_sources.items()}
    if capture.get("source_hashes")!=source_hashes:
        raise ValueError("Legacy callback or candidate source changed after capture")
    rows=capture.get("callbacks",[])
    by_id={row.get("legacy_id"):row for row in rows if isinstance(row,dict)}
    if set(by_id)!=set(CALLBACKS) or len(rows)!=len(CALLBACKS):
        raise ValueError("Legacy callback capture does not cover the exact action set")
    for action,expected in CALLBACKS.items():
        row=by_id[action]
        if any(row.get(key)!=value for key,value in expected.items()):
            raise ValueError("Legacy rendered callback differs for "+action)
        if (row.get("method")!="POST" or row.get("path")!="/cargo-tracker/eventLogger/eventLogger.xhtml"
                or row.get("content_type")!="application/x-www-form-urlencoded; charset=UTF-8"
                or row.get("faces_request")!="partial/ajax" or row.get("ajax") is not True
                or row.get("response_status")!=200 or row.get("viewstate_present") is not True
                or row.get("clientwindow_present") is not True):
            raise ValueError("Legacy rendered request transport shape differs for "+action)
        parameters=row.get("parameters",[])
        names=[item.get("name") for item in parameters if isinstance(item,dict)]
        if (names!=row.get("parameter_names") or len(names)!=len(set(names))
                or "javax.faces.source" not in names
                or row["callback_input_name"] not in names
                or "javax.faces.ViewState" not in names or "javax.faces.ClientWindow" not in names):
            raise ValueError("Legacy request parameter inventory differs for "+action)
        values={item["name"]:item.get("value") for item in parameters}
        if (values.get("javax.faces.source")!=row["source_component_id"]
                or values.get("javax.faces.behavior.event")!=row["behavior_event"]
                or values.get("javax.faces.partial.event")!=row["partial_event"]
                or values.get("javax.faces.partial.execute")!=row["execute"]
                or values.get("javax.faces.partial.render")!=row["render"]
                or values.get(row["callback_input_name"])!=row["selected_value"]
                or values.get("javax.faces.ViewState")!="<present; value redacted>"
                or values.get("javax.faces.ClientWindow")!="<present; value redacted>"):
            raise ValueError("Legacy request parameter values differ for "+action)
    page=raw_sources["legacy_handling_page_sha256"].decode()
    page_bindings=(
        'listener="#{eventBackingBean.updateVoyage}"',
        'listener="#{eventBackingBean.updateListener}"',
        'listener="#{eventBackingBean.updateListenerEvent}"',
        'listener="#{eventBackingBean.timeSet()}"',
    )
    servlet=raw_sources["candidate_navigation_servlet_sha256"].decode()
    routes=raw_sources["candidate_access_routes_sha256"].decode()
    if (any(binding not in page for binding in page_bindings)
            or '"/eventLogger/eventLogger.xhtml","/mobile.xhtml"' not in servlet
            or '"/eventLogger/root.xhtml","/mobile.xhtml"' not in servlet
            or "doPost(" in servlet
            or "/eventLogger/eventLogger.xhtml	Operator,Administrator" not in routes):
        raise ValueError("Legacy callback or candidate navigation source mapping changed")
    return {"capture":capture,"capture_sha256":CAPTURE_SHA256,
            "source_hashes":source_hashes,"actions":by_id}
