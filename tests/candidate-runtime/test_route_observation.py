import copy,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("route_harness",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class RouteObservationTests(unittest.TestCase):
    def route(self):
        return [{"transitEdges":[{"fromUnLocode":"CNHKG","toUnLocode":"SESTO","voyageNumber":"0100S","fromDate":"2030-01-01T00:00:00Z","toDate":"2030-01-02T00:00:00Z"},{"fromUnLocode":"SESTO","toUnLocode":"FIHEL","voyageNumber":"0200T","fromDate":"2030-01-03T00:00:00Z","toDate":"2030-01-04T00:00:00Z"}]}]
    def test_connected_ordered_route_is_semantic_success(self):
        self.assertTrue(h.route_semantics(json.dumps(self.route())))
    def test_actual_jsonb_utc_region_dates_are_supported(self):
        route=self.route()
        for edge in route[0]["transitEdges"]:
            edge["fromDate"]+="[UTC]";edge["toDate"]+="[UTC]"
        self.assertTrue(h.route_semantics(json.dumps(route)))
    def test_unknown_malformed_or_inconsistent_region_dates_fail(self):
        for date in ["2030-01-01T00:00:00Z[unknown]","2030-01-01T00:00:00Z[UTC","2030-01-01T00:00:00+02:00[UTC]"]:
            route=self.route();route[0]["transitEdges"][0]["fromDate"]=date
            self.assertFalse(h.route_semantics(json.dumps(route)))
    def test_empty_or_malformed_200_response_is_not_semantic_success(self):
        for body in ["[]","{}","null","[null]","not-json",'[{"transitEdges":[]}]']:
            with self.subTest(body=body):self.assertFalse(h.route_semantics(body))
    def test_disconnected_or_wrong_endpoint_route_is_not_success(self):
        for index,key,value in [(0,"fromUnLocode","USNYC"),(1,"fromUnLocode","DEHAM"),(1,"toUnLocode","USNYC")]:
            route=self.route();route[0]["transitEdges"][index][key]=value
            self.assertFalse(h.route_semantics(json.dumps(route)))
    def test_invalid_time_or_missing_voyage_is_not_success(self):
        for index,key,value in [(0,"fromDate","garbage"),(0,"fromDate","2030-01-04T00:00:00Z"),(1,"fromDate","2030-01-01T00:00:00Z"),(0,"fromDate","2030-01-01T00:00:00"),(0,"voyageNumber","")]:
            route=self.route();route[0]["transitEdges"][index][key]=value
            self.assertFalse(h.route_semantics(json.dumps(route)))
if __name__=="__main__":unittest.main()
