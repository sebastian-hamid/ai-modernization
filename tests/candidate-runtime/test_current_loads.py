import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("current_load_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class CurrentLoadTests(unittest.TestCase):
    cargo={"trackingId":"ABCDEFGH","originName":"Hong Kong","originCode":"CNHKG","destinationName":"New York","destinationCode":"USNYC","routingStatus":"NOT_ROUTED","transportStatus":"NOT_RECEIVED"}
    def test_selectable_routes_bind_both_endpoints(self):
        form='<form id="routing"><input name="jakarta.faces.ViewState" value="state"><select id="routing:choice"><option value="0">Route 1</option></select><button id="routing:submit">Assign</button></form>'
        link='<a href="/cargo-tracker/admin/route.xhtml?trackingId=ABCDEFGH&amp;jfwid=one%3A0">Request fresh routes</a>'
        body=link+'<table class="route-candidate"><tbody><tr><td>V100</td><td>Hong Kong (CNHKG)</td><td>USNYC (New York)</td><td>Departure</td><td>Arrival</td></tr></tbody></table>'+form
        self.assertEqual(h.verify_route_choices(body,"CNHKG","USNYC","token","ABCDEFGH","http://fixture/cargo-tracker/"),1)
        for bad in (body.replace("CNHKG","CNSHA"),body.replace("USNYC","FIHEL"),body.replace('value="0"','value="1"'),body.replace('id="routing:choice"','id="other"')+'<input id="routing:choice">',body.replace('ABCDEFGH','OTHERID1'),body.replace('/cargo-tracker/admin/route.xhtml?','https://evil.example/cargo-tracker/admin/route.xhtml?'),form):
            with self.subTest(bad=bad),self.assertRaises(AssertionError):
                h.verify_route_choices(bad,"CNHKG","USNYC","token","ABCDEFGH","http://fixture/cargo-tracker/")

    def test_route_read_audit_distinguishes_planner_calls_from_writes(self):
        before={"tables":{"cargo":1},"queues":{"handling":1},"business_invocations":{"assignCargoToRoute":1}}
        after=copy.deepcopy(before)
        after["business_invocations"].update({
            "net.java.cargotracker.application.internal.DefaultBookingService#requestPossibleRoutesForCargo":4,
            "net.java.cargotracker.infrastructure.routing.ExternalRoutingService#fetchRoutesForSpecification":4,
            "net.java.pathfinder.api.GraphTraversalService#findShortestPath":4,
        })
        self.assertTrue(h.route_read_effects(before,after,4))
        self.assertFalse(h.route_read_effects(before,after,3))
        for field in ["tables","queues","business_invocations"]:
            altered=copy.deepcopy(after);altered[field]["unexpected"]=1
            self.assertFalse(h.route_read_effects(before,altered,4))

    def test_details_require_exact_selected_values_and_deadline(self):
        values={"Tracking ID":"ABCDEFGH","Origin":"Hong Kong ","Destination":"New York ","Routing status":"NOT_ROUTED","Status":"NOT_RECEIVED","Arrival deadline":"12/31/2030 12:00:00 AM"}
        render=lambda fields:"".join("<dt>"+k+"</dt><dd>"+v+"</dd>" for k,v in fields.items())
        self.assertTrue(h.current_load_semantics("ACTION-20",render(values),self.cargo))
        for key in values:
            bad=dict(values);bad[key]="OTHER"
            with self.subTest(key=key):self.assertFalse(h.current_load_semantics("ACTION-20",render(bad),self.cargo))
        self.assertFalse(h.current_load_semantics("ACTION-20",render(values)+render(values),self.cargo))
    def test_real_getter_labels_have_only_names_with_trailing_space(self):
        values={"Tracking ID":"ABCDEFGH","Origin":"Hong Kong ","Destination":"New York ","Routing status":"NOT_ROUTED","Status":"NOT_RECEIVED","Arrival deadline":"12/31/2030 12:00:00 AM"}
        body="".join("<dt>"+key+"</dt><dd>"+value+"</dd>" for key,value in values.items())
        self.assertTrue(h.current_load_semantics("ACTION-20",body,self.cargo))
        diagnostic={}
        self.assertFalse(h.current_load_semantics("ACTION-20",body.replace("New York ","Helsinki "),self.cargo,diagnostic))
        self.assertEqual(diagnostic,{"mismatched_fields":["Destination"]})
        self.assertFalse(h.current_load_semantics("ACTION-20",body.replace("New York ","New York (FIHEL)"),self.cargo))
    def form(self,options):
        return "".join('<input id="'+key+'"/>' for key in ["change","change:submit"])+'<input name="jakarta.faces.ViewState" value="state"/><select id="change:destination">'+options+"</select>"
    def test_destination_must_be_current_selected_value_not_just_available_option(self):
        good='<option value="FIHEL">Helsinki</option><option value="USNYC" selected="selected">New York</option>'
        self.assertTrue(h.current_load_semantics("ACTION-07",self.form(good),self.cargo))
        for options in [good.replace('value="USNYC" selected="selected"','value="FIHEL" selected="selected"'),good.replace(' selected="selected"',''),good+good]:
            self.assertFalse(h.current_load_semantics("ACTION-07",self.form(options),self.cargo))
    def test_unknown_surface_or_missing_real_form_cannot_pass(self):
        self.assertFalse(h.current_load_semantics("ACTION-99","",self.cargo))
        with self.assertRaises(AssertionError):h.current_load_semantics("ACTION-07","No form",self.cargo)
