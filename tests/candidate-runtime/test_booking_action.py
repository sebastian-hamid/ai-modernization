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
if __name__=="__main__":unittest.main()
