import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("current_load_runtime",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class CurrentLoadTests(unittest.TestCase):
    cargo={"trackingId":"ABCDEFGH","originName":"Hong Kong","originCode":"CNHKG","destinationName":"New York","destinationCode":"USNYC","routingStatus":"NOT_ROUTED","transportStatus":"NOT_RECEIVED"}
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
