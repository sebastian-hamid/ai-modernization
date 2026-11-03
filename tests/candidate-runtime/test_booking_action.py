import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("booking_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class BookingActionTests(unittest.TestCase):
    def test_only_local_unambiguous_success_redirect_yields_id(self):
        base="http://candidate:8080/cargo-tracker/"
        self.assertEqual(h.booking_tracking_id(base,303,"/cargo-tracker/admin/show.xhtml?trackingId=ABCDEFGH&jfwid=one"),"ABCDEFGH")
        for status,target in [(200,"admin/show.xhtml?trackingId=ABCDEFGH"),(500,"admin/show.xhtml?trackingId=ABCDEFGH"),(303,"https://untrusted.example/cargo-tracker/admin/show.xhtml?trackingId=ABCDEFGH"),(303,"admin/show.xhtml?trackingId=ABCDEFGH&trackingId=ABCDEFGH"),(303,"admin/show.xhtml?trackingId=ABCDEFGH&redirect=other"),(303,"admin/show.xhtml?trackingId=ABCDEFGH#other"),(303,"admin/show.xhtml?trackingId=short"),(303,"admin/show.xhtml?trackingId=ABCDEFGH&jfwid=")]:
            with self.subTest(target=target),self.assertRaises(AssertionError):h.booking_tracking_id(base,status,target)
    def test_real_form_required_and_encoded_view_state_preserved(self):
        body="".join('<input id="'+key+'"/>' for key in ["booking","booking:origin","booking:destination","booking:deadline","booking:submit"])+'<input name="jakarta.faces.ViewState" value="a&amp;b"/>'
        form=h.booking_form(body,"private-fixture-token")
        self.assertEqual(form["jakarta.faces.ViewState"],"a&b")
        self.assertEqual(form["booking:deadline"],"2030-12-31")
        with self.assertRaises(AssertionError):h.booking_form(body.replace('id="booking:origin"','id="other"'),"token")
    def samples(self):
        before={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},"queues":{name:{attribute:0 for attribute in h.QUEUE_ATTRIBUTES} for name in h.REQUIRED_QUEUES},"business_invocations":{"Booking#bookNewCargo":1}}
        after=copy.deepcopy(before);after["tables"]["CARGO"]={"rows":2,"sha256":"b"*64};after["business_invocations"]["Booking#bookNewCargo"]=2
        cargo={"trackingId":"ABCDEFGH","originCode":"CNHKG","destinationCode":"FIHEL","routingStatus":"NOT_ROUTED","transportStatus":"NOT_RECEIVED"}
        return before,after,cargo
    def test_actual_booking_positive_control_required(self):
        before,after,cargo=self.samples();self.assertTrue(h.booking_positive(before,after,cargo,"ABCDEFGH"))
        for mode in ["no_db","no_audit","two_bookings","queue","wrong_id","wrong_destination","wrong_status"]:
            before,after,cargo=self.samples()
            if mode=="no_db":after["tables"]=copy.deepcopy(before["tables"])
            elif mode=="no_audit":after["business_invocations"]=copy.deepcopy(before["business_invocations"])
            elif mode=="two_bookings":after["business_invocations"]["Booking#bookNewCargo"]=3
            elif mode=="queue":next(iter(after["queues"].values()))["MessagesAdded"]=1
            elif mode=="wrong_id":cargo["trackingId"]="OTHERID1"
            elif mode=="wrong_destination":cargo["destinationCode"]="USNYC"
            else:cargo["transportStatus"]="CLAIMED"
            with self.subTest(mode=mode):self.assertFalse(h.booking_positive(before,after,cargo,"ABCDEFGH"))
class DestinationActionTests(unittest.TestCase):
    def test_destination_real_form_and_replay_intent(self):
        body="".join('<input id="'+key+'"/>' for key in ["change","change:destination","change:submit"])+'<input name="jakarta.faces.ViewState" value="state&amp;one"/>'
        form=h.destination_form(body,"test-token")
        self.assertEqual(form["change:destination"],"USNYC");self.assertEqual(form["jakarta.faces.ViewState"],"state&one")
        self.assertEqual(h.destination_form(body,"test-token","FIHEL")["change:destination"],"FIHEL")
        with self.assertRaises(AssertionError):h.destination_form(body.replace('id="change:submit"','id="wrong"'),"token")
    def test_destination_requires_same_cargo_real_effect_and_preserved_state(self):
        def fixture():
            before={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},"queues":{name:{attribute:0 for attribute in h.QUEUE_ATTRIBUTES} for name in h.REQUIRED_QUEUES},"business_invocations":{"Booking#changeDestination":1}}
            after=copy.deepcopy(before);after["tables"]["CARGO"]["sha256"]="b"*64;after["business_invocations"]["Booking#changeDestination"]=2
            old={"trackingId":"ABCDEFGH","originCode":"CNHKG","destinationCode":"FIHEL","routingStatus":"NOT_ROUTED","transportStatus":"NOT_RECEIVED","lastKnownLocationCode":"Unknown"}
            cargo=dict(old,destinationCode="USNYC")
            return before,after,old,cargo
        before,after,old,cargo=fixture();self.assertTrue(h.destination_positive(before,after,old,cargo,"ABCDEFGH"))
        for mode in ["no_sql","no_audit","two_changes","queue","new_id","wrong_origin","wrong_destination","transport"]:
            before,after,old,cargo=fixture()
            if mode=="no_sql":after["tables"]=copy.deepcopy(before["tables"])
            elif mode=="no_audit":after["business_invocations"]["Booking#changeDestination"]=1
            elif mode=="two_changes":after["business_invocations"]["Booking#changeDestination"]=3
            elif mode=="queue":next(iter(after["queues"].values()))["MessagesAdded"]=1
            elif mode=="new_id":cargo["trackingId"]="OTHERID1"
            elif mode=="wrong_origin":cargo["originCode"]="USCHI"
            elif mode=="wrong_destination":cargo["destinationCode"]="FIHEL"
            else:cargo["transportStatus"]="CLAIMED"
            with self.subTest(mode=mode):self.assertFalse(h.destination_positive(before,after,old,cargo,"ABCDEFGH"))

class SourceEntryTests(unittest.TestCase):
    base="http://candidate:8080/cargo-tracker/"
    target="ABCDEFGH"
    def booking(self):
        return "".join('<input id="'+key+'"/>' for key in ["booking","booking:origin","booking:destination","booking:deadline","booking:submit"])+'<input name="jakarta.faces.ViewState" value="state"/>'
    def destination(self):
        return "".join('<input id="'+key+'"/>' for key in ["change","change:destination","change:submit"])+'<input name="jakarta.faces.ViewState" value="state"/>'
    def details(self,href="/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&amp;jfwid=one"):
        return '<dd id="trackingId">ABCDEFGH</dd><a href="'+href+'">Change destination</a>'
    def run_entry(self,responses,who="operator",target="ABCDEFGH"):
        calls=[]
        def request(path):
            calls.append(path)
            if not responses:raise AssertionError("Unexpected request")
            return responses.pop(0)
        body,proof=h.source_entry(request,self.base,who,"token",target)
        return body,proof,calls
    def test_follows_rendered_link_for_same_cargo_and_saves_source(self):
        body,proof,calls=self.run_entry([(200,self.details(),{}),(200,self.destination(),{})])
        self.assertEqual(calls,["admin/show.xhtml?trackingId=ABCDEFGH","admin/changeDestination.xhtml?trackingId=ABCDEFGH&jfwid=one"])
        self.assertEqual(proof,{"entry_page":"admin/show.xhtml?trackingId=ABCDEFGH","source_entry_verified":True})
        self.assertEqual(body,self.destination())
    def test_percent_encoded_window_query_is_valid_but_encoded_paths_are_not(self):
        href="/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&amp;jfwid=window%3A0"
        body,proof,calls=self.run_entry([(200,self.details(href),{}),(200,self.destination(),{})])
        self.assertEqual(calls[-1],"admin/changeDestination.xhtml?trackingId=ABCDEFGH&jfwid=window%3A0")
        for href in ["/cargo-tracker/admin/%63hangeDestination.xhtml?trackingId=ABCDEFGH","/cargo-tracker/admin/changeDestination.xhtml;other?trackingId=ABCDEFGH","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&jfwid=bad%ZZ","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&jfwid=bad%0Avalue","/cargo-tracker/admin/changeDestination.xhtml?trackingId=%41BCDEFGH","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&jf%77id=window","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&jfwid=bad"+chr(92)+"value"]:
            with self.subTest(href=href),self.assertRaises(AssertionError):self.run_entry([(200,self.details(href),{}),(200,self.destination(),{})])
    def test_rejects_unsafe_wrong_cargo_missing_and_duplicate_links(self):
        for href in ["https://evil.example/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH","/cargo-tracker/admin/changeDestination.xhtml?trackingId=OTHERID1","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&trackingId=ABCDEFGH","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&extra=one","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH#fragment","/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH&jfwid=","/cargo-tracker/admin/route.xhtml?trackingId=ABCDEFGH"]:
            with self.subTest(href=href),self.assertRaises(AssertionError):
                self.run_entry([(200,self.details(href),{}),(200,self.destination(),{})])
        for body in ['<dd id="trackingId">ABCDEFGH</dd>',self.details()+self.details(),self.details().replace('id="trackingId">ABCDEFGH','id="trackingId">OTHERID1')]:
            with self.subTest(body=body),self.assertRaises(AssertionError):self.run_entry([(200,body,{})])
    def test_reader_hidden_link_then_direct_editor_denial(self):
        body,proof,calls=self.run_entry([(200,'<dd id="trackingId">ABCDEFGH</dd>',{}),(403,"Denied",{})],who="reader")
        self.assertEqual(calls[-1],"admin/changeDestination.xhtml?trackingId=ABCDEFGH")
        self.assertTrue(proof["source_entry_verified"])
        with self.assertRaises(AssertionError):self.run_entry([(200,self.details(),{})],who="reader")
    def test_anonymous_requires_fixed_login_and_no_cargo_leak(self):
        rows=[(303,"",{"Location":"/cargo-tracker/login"})]*2
        self.assertTrue(self.run_entry(rows,who=None)[1]["source_entry_verified"])
        for code,body,headers in [(200,"",{}),(303,"",{"Location":"https://evil.example/login"}),(303,"ABCDEFGH",{"Location":"/cargo-tracker/login"})]:
            with self.subTest(code=code,body=body),self.assertRaises(AssertionError):self.run_entry([(code,body,headers)],who=None)
    def test_booking_allowed_and_denied_real_source_responses(self):
        for who in ["operator","admin"]:
            body,proof,calls=self.run_entry([(200,self.booking(),{})],who=who,target=None)
            self.assertEqual(calls,["admin/book.xhtml"]);self.assertEqual(proof["entry_page"],"admin/book.xhtml")
        for who,response in [("reader",(403,"Denied",{})),(None,(303,"",{"Location":"/cargo-tracker/login"}))]:
            self.assertTrue(self.run_entry([response],who=who,target=None)[1]["source_entry_verified"])
        for response in [(200,"missing form",{}),(303,"",{"Location":"/cargo-tracker/login"})]:
            with self.assertRaises(AssertionError):self.run_entry([response],target=None)
    def test_source_success_does_not_mask_failed_editor_or_invalid_identity(self):
        for response in [(500,"",{}),(200,"missing form",{}),(303,"",{"Location":"/cargo-tracker/login"})]:
            with self.assertRaises(AssertionError):self.run_entry([(200,self.details(),{}),response])
        for who,target in [("other","ABCDEFGH"),("operator","short")]:
            with self.assertRaises(AssertionError):self.run_entry([],who=who,target=target)

if __name__=="__main__":unittest.main()
