import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("route_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def table(attribute='class="route-candidate"',voyage="0100S"):
    return '<table '+attribute+'><thead><tr><th>Header</th></tr></thead><tbody><tr><td>'+voyage+'</td><td>CNHKG &amp; port</td><td>USNYC</td><td>departure</td><td>arrival</td></tr></tbody></table>'
class RoutingActionTests(unittest.TestCase):
    def test_exact_body_rows_decoded_and_correct_table_selected(self):
        body=table()+table('id="itinerary"',"0200T")
        self.assertEqual(h.route_tables(body),[[["0100S","CNHKG & port","USNYC","departure","arrival"]]])
        self.assertEqual(h.route_tables(body,"id","itinerary")[0][0][0],"0200T")
        self.assertEqual(h.route_tables("<table><tbody><tr><td>irrelevant</td></tr></tbody></table>"),[])
    def test_form_choice_requires_actual_matching_candidate_and_fields(self):
        body=table()+table(voyage="0200T")+'<form id="routing"><select id="routing:choice"><option value="0">one</option><option value="1">two</option></select><button id="routing:submit"></button><input name="jakarta.faces.ViewState" value="state&amp;one"/></form>'
        form,rows=h.routing_form(body,"test-token",1)
        self.assertEqual(form["routing:choice"],"1");self.assertEqual(form["jakarta.faces.ViewState"],"state&one")
        self.assertEqual(rows[0][0],"0200T")
        for html,choice in [(body,-1),(body,2),(body,True),(body.replace('value="1"','value="3"'),1),(body.replace('id="routing:submit"','id="other"'),0),(body.replace("<td>arrival</td>",""),0)]:
            with self.subTest(choice=choice),self.assertRaises(AssertionError):h.routing_form(html,"token",choice)
    def test_routing_control_requires_sql_audit_and_same_cargo_state(self):
        def fixture():
            before={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},"queues":{name:{attribute:0 for attribute in h.QUEUE_ATTRIBUTES} for name in h.REQUIRED_QUEUES},"business_invocations":{"Booking#assignCargoToRoute":1}}
            after=copy.deepcopy(before);after["tables"]["CARGO"]["sha256"]="b"*64;after["business_invocations"]["Booking#assignCargoToRoute"]=2
            old={"trackingId":"ABCDEFGH","originCode":"CNHKG","destinationCode":"USNYC","routingStatus":"NOT_ROUTED","transportStatus":"NOT_RECEIVED","lastKnownLocationCode":"Unknown"}
            return before,after,old,dict(old,routingStatus="ROUTED")
        before,after,old,cargo=fixture();self.assertTrue(h.routing_positive(before,after,old,cargo,"ABCDEFGH"))
        for mode in ["sql","audit","two","queue","id","origin","destination","routing","transport"]:
            before,after,old,cargo=fixture()
            if mode=="sql":after["tables"]=copy.deepcopy(before["tables"])
            elif mode=="audit":after["business_invocations"]["Booking#assignCargoToRoute"]=1
            elif mode=="two":after["business_invocations"]["Booking#assignCargoToRoute"]=3
            elif mode=="queue":next(iter(after["queues"].values()))["MessagesAdded"]=1
            elif mode=="id":cargo["trackingId"]="OTHERID1"
            elif mode=="origin":cargo["originCode"]="USCHI"
            elif mode=="destination":cargo["destinationCode"]="FIHEL"
            elif mode=="routing":cargo["routingStatus"]="NOT_ROUTED"
            else:cargo["transportStatus"]="CLAIMED"
            with self.subTest(mode=mode):self.assertFalse(h.routing_positive(before,after,old,cargo,"ABCDEFGH"))
if __name__=="__main__":unittest.main()
