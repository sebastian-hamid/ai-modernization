import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("handling_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class HandlingActionTests(unittest.TestCase):
    def test_form_requires_real_offered_cargo_location_and_fields(self):
        ids=["handling","handling:cargo","handling:type","handling:location","handling:time","handling:voyage","handling:submit"]
        body="".join('<input id="'+key+'"/>' for key in ids)+'<select><option value="ABCDEFGH">cargo</option><option value="USCHI">port</option></select><input name="jakarta.faces.ViewState" value="state&amp;one"/>'
        form=h.handling_form(body,"test-token","ABCDEFGH","USCHI","2030-01-03 10:00")
        self.assertEqual(form["handling:cargo"],"ABCDEFGH");self.assertEqual(form["handling:location"],"USCHI");self.assertEqual(form["handling:type"],"CUSTOMS")
        self.assertEqual(form["handling:voyage"],"");self.assertEqual(form["jakarta.faces.ViewState"],"state&one")
        for html,cargo,location in [(body,"OTHERID1","USCHI"),(body,"ABCDEFGH","DEHAM"),(body.replace('id="handling:submit"','id="other"'),"ABCDEFGH","USCHI")]:
            with self.subTest(cargo=cargo,location=location),self.assertRaises(AssertionError):h.handling_form(html,"token",cargo,location,"2030-01-03 10:00")
    def test_async_control_requires_every_real_channel_and_correct_cargo(self):
        def fixture():
            before={"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},"queues":{name:{attribute:0 for attribute in h.QUEUE_ATTRIBUTES} for name in h.REQUIRED_QUEUES},"business_invocations":{name:1 for name in ["Handler#submitReport","Service#registerHandlingEvent","lab.HandlingEventRegistrationAttemptConsumer#onMessage","lab.CargoHandledConsumer#onMessage"]}}
            after=copy.deepcopy(before);after["tables"]["CARGO"]["sha256"]="b"*64
            for name in after["business_invocations"]:after["business_invocations"][name]=2
            for name in ["jms.queue.HandlingEventRegistrationAttemptQueue","jms.queue.CargoHandledQueue"]:
                after["queues"][name]["MessagesAdded"]=1;after["queues"][name]["MessagesAcknowledged"]=1
            old={"trackingId":"ABCDEFGH","originCode":"CNHKG","destinationCode":"USNYC","routingStatus":"ROUTED","transportStatus":"NOT_RECEIVED","lastKnownLocationCode":"Unknown"}
            return before,after,old,dict(old,transportStatus="IN_PORT",lastKnownLocationCode="USCHI")
        before,after,old,cargo=fixture();self.assertTrue(h.handling_positive(before,after,old,cargo,"ABCDEFGH","USCHI"))
        modes=["sql","submit","register","registration_worker","inspection_worker","queue_add","queue_ack","duplicate","id","location","status","destination"]
        for mode in modes:
            before,after,old,cargo=fixture()
            if mode=="sql":after["tables"]=copy.deepcopy(before["tables"])
            elif mode in {"submit","register","registration_worker","inspection_worker"}:
                suffix={"submit":"#submitReport","register":"#registerHandlingEvent","registration_worker":"HandlingEventRegistrationAttemptConsumer#onMessage","inspection_worker":"CargoHandledConsumer#onMessage"}[mode]
                for key in after["business_invocations"]:
                    if key.endswith(suffix):after["business_invocations"][key]=1
            elif mode=="queue_add":after["queues"]["jms.queue.CargoHandledQueue"]["MessagesAdded"]=0
            elif mode=="queue_ack":after["queues"]["jms.queue.HandlingEventRegistrationAttemptQueue"]["MessagesAcknowledged"]=0
            elif mode=="duplicate":after["business_invocations"]["Service#registerHandlingEvent"]=3
            elif mode=="id":cargo["trackingId"]="OTHERID1"
            elif mode=="location":cargo["lastKnownLocationCode"]="FIHEL"
            elif mode=="status":cargo["transportStatus"]="NOT_RECEIVED"
            else:cargo["destinationCode"]="FIHEL"
            with self.subTest(mode=mode):self.assertFalse(h.handling_positive(before,after,old,cargo,"ABCDEFGH","USCHI"))
if __name__=="__main__":unittest.main()
