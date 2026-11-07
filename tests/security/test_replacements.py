import copy
import unittest
from contracts import UnsupportedCase
from replacements import replacement_observation

class ReplacementTests(unittest.TestCase):
    def case(self, group="cancel-editor", actor="Operator"):
        ids = {"cancel-editor":["ACTION-08"], "booking-cancel":["ACTION-28","ACTION-31","ACTION-33"], "tracking-discovery":["ACTION-23","ACTION-44"], "booking-deadline":["ACTION-26","ACTION-32"], "booking-single-page":["ACTION-27","ACTION-30","ACTION-34"]}
        method="POST" if group in {"booking-deadline","booking-single-page","tracking-discovery"} else "GET"
        return {"capability_id":group,"actor":actor,"binding_status":"browser-replacement-v1",
                "method":method,"legacy_ids":ids[group]}

    def cancellation(self, group="cancel-editor", actor="Operator"):
        allowed = actor in {"Operator","Administrator"}
        sample = {"fixture_id":"a"*64,"tables":{"CARGO":{"rows":1,"sha256":"b"*64}},
                  "queues":{"handling":{"MessagesAdded":1}},
                  "business_invocations":{"save":1,"net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo":5}}
        before = {**copy.deepcopy(sample),"stage":group+":"+actor+":before"}
        after = {**copy.deepcopy(sample),"stage":group+":"+actor+":after"}
        after["business_invocations"]["net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"]=6
        source = "/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH"
        target = "/cargo-tracker/admin/show.xhtml?trackingId=ABCDEFGH"
        if group=="booking-cancel":
            source="/cargo-tracker/admin/book.xhtml"
            target="/cargo-tracker/admin/dashboard.xhtml"
        return {"replacement_driver":"browser-replacement-v1","group":group,"tracking_id":"ABCDEFGH",
                "source_path":source,"target_path":target,"source_entry_verified":True,
                "return_access_verified":True,"persisted_state_unchanged":True,
                "source_status":200 if allowed else 403 if actor=="Reader" else 303,
                "target_status":303 if actor=="anonymous" else 200,
                "unsaved_edits_verified":allowed,"leave_navigation_verified":allowed,
                "source_payload_absent":not allowed,"source_login_verified":actor=="anonymous",
                "target_payload_absent":actor=="anonymous","target_login_verified":actor=="anonymous",
                "before":before,"after":after}

    def test_cancellations_bind_each_actor_source_and_return(self):
        for group in ["cancel-editor","booking-cancel"]:
            for actor in ["anonymous","Reader","Operator","Administrator"]:
                result=replacement_observation(self.case(group,actor),self.cancellation(group,actor))
                self.assertEqual(result["semantic_success"],actor in {"Operator","Administrator"})
                self.assertEqual(result["invocation_denied"],actor in {"anonymous","Reader"})
                if actor=="Reader":
                    self.assertEqual(result["status"],403)
                    self.assertEqual(result["target_status"],200)

    def test_unsaved_changes_and_fresh_effect_channels_are_required(self):
        for mode in ["changed","missing","fixture","stage","edits","target","extra-read","extra-call"]:
            proof=self.cancellation()
            if mode=="changed":proof["after"]["tables"]["CARGO"]["rows"]=2
            elif mode=="missing":proof["after"]["queues"]={}
            elif mode=="fixture":proof["after"]["fixture_id"]="c"*64
            elif mode=="stage":proof["after"]["stage"]="cancel-editor:Reader:after"
            elif mode=="edits":proof["unsaved_edits_verified"]=False
            elif mode=="target":proof["target_path"]=proof["target_path"].replace("ABCDEFGH","OTHERID1")
            elif mode=="extra-read":proof["after"]["business_invocations"]["net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"]=7
            else:proof["after"]["business_invocations"]["unexpected"]=1
            with self.subTest(mode=mode),self.assertRaises(UnsupportedCase):
                replacement_observation(self.case(),proof)

    def test_reader_return_permissions_and_anonymous_no_leak_remain_required(self):
        for actor,field,value in [("Reader","target_status",403),("Reader","source_status",200),
                                  ("anonymous","source_login_verified",False),
                                  ("anonymous","target_payload_absent",False)]:
            proof=self.cancellation(actor=actor)
            proof[field]=value
            with self.subTest(actor=actor,field=field),self.assertRaises(UnsupportedCase):
                replacement_observation(self.case(actor=actor),proof)

    def booking(self, group="booking-deadline", actor="Operator"):
        sample={"fixture_id":"d"*64,"tables":{"CARGO":{"rows":1,"sha256":"e"*64}},
                "queues":{"handling":{"MessagesAdded":1}},
                "business_invocations":{"net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo":4,"other":2}}
        before={**copy.deepcopy(sample),"stage":group+":"+actor+":before"}
        after={**copy.deepcopy(sample),"stage":group+":"+actor+":after"}
        after["business_invocations"]["net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"]=4
        allowed=actor in {"Operator","Administrator"}
        proof={"replacement_driver":"browser-replacement-v1","group":group,"tracking_id":"ABCDEFGH",
               "source_path":"/cargo-tracker/admin/book.xhtml","source_entry_verified":True,
               "source_status":200 if allowed else 403 if actor=="Reader" else 303,
               "invalid_deadline_rejected":allowed,"valid_booking_created":allowed,
               "source_payload_absent":not allowed,"source_login_verified":actor=="anonymous",
               "before":before,"after":after}
        if allowed:
            positive_before={"fixture_id":"d"*64,"stage":"booking-positive:"+actor+":before",
                "tables":{"CARGO":{"rows":1,"sha256":"1"*64}},"queues":{"handling":{"MessagesAdded":1}},
                "business_invocations":{"net.java.cargotracker.application.internal.DefaultBookingService#bookNewCargo":2,
                    "net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo":5,"other":3}}
            positive_after=copy.deepcopy(positive_before)
            positive_after["stage"]="booking-positive:"+actor+":after"
            positive_after["tables"]["CARGO"]={"rows":2,"sha256":"2"*64}
            positive_after["business_invocations"]["net.java.cargotracker.application.internal.DefaultBookingService#bookNewCargo"]=3
            positive_after["business_invocations"]["net.java.cargotracker.interfaces.booking.rest.CargoMonitoringService#getAllCargo"]=6
            proof.update(booking_post_status=303,booking_location_verified=True,booking_result_tracking_id="ABCDEFGH",
                independent_persisted_booking=True,positive_effects_verified=True,
                positive_before=positive_before,positive_after=positive_after)
        if group=="booking-single-page":proof["all_fields_same_form"]=allowed
        if actor!="anonymous":
            principal={"Reader":"reader","Operator":"operator","Administrator":"admin"}[actor]
            proof["identity"]={"server_verified":True,"principal":principal,"roles":[actor]}
        return proof

    def test_booking_groups_require_denials_validation_form_and_effects(self):
        for group in ["booking-deadline","booking-single-page"]:
            for actor in ["anonymous","Reader","Operator","Administrator"]:
                proof=self.booking(group,actor)
                result=replacement_observation(self.case(group,actor),proof)
                allowed=actor in {"Operator","Administrator"}
                self.assertEqual(result["semantic_success"],allowed)
                self.assertEqual(result["invocation_denied"],not allowed)
                changed=copy.deepcopy(proof)
                changed["after"]["tables"]["CARGO"]["rows"]=2
                with self.subTest(group=group,actor=actor),self.assertRaises(UnsupportedCase):
                    replacement_observation(self.case(group,actor),changed)
            proof=self.booking(group,"Operator")
            proof["invalid_deadline_rejected"]=False
            with self.assertRaises(UnsupportedCase):
                replacement_observation(self.case(group,"Operator"),proof)
        proof=self.booking("booking-single-page","Operator")
        proof["all_fields_same_form"]=False
        with self.assertRaises(UnsupportedCase):
            replacement_observation(self.case("booking-single-page","Operator"),proof)
        for field,value in [("booking_post_status",200),("booking_location_verified",False),("booking_result_tracking_id","OTHERID1"),
                            ("independent_persisted_booking",False),("positive_effects_verified",False)]:
            proof=self.booking("booking-deadline","Operator");proof[field]=value
            with self.subTest(field=field),self.assertRaises(UnsupportedCase):
                replacement_observation(self.case("booking-deadline","Operator"),proof)
        proof=self.booking("booking-single-page","Operator")
        proof["positive_after"]["tables"]["CARGO"]["sha256"]="1"*64
        proof["positive_after"]["tables"]["CARGO"]["rows"]=1
        with self.assertRaises(UnsupportedCase):
            replacement_observation(self.case("booking-single-page","Operator"),proof)
        proof=self.booking("booking-deadline","Operator")
        proof["positive_after"].pop("tables")
        with self.assertRaises(UnsupportedCase):
            replacement_observation(self.case("booking-deadline","Operator"),proof)
        proof=self.booking("booking-deadline","Operator")
        proof["positive_before"]["fixture_id"]="a"*64
        with self.assertRaises(UnsupportedCase):
            replacement_observation(self.case("booking-deadline","Operator"),proof)

    def test_discovery_requires_actual_list_and_typed_lookup_of_same_cargo(self):
        identity={"server_verified":True,"principal":"reader","roles":["Reader"]}
        common={"tracking_id":"ABCDEFGH","status":200,"driver":"click","identity":identity,
                "semantic_success":True,"selected_cargo_verified":True,"persisted_details_verified":True}
        listing={**common,"current_navigation_driver":"browser-claimed-cargo-v1","source_page":"admin/listClaimed.xhtml",
                 "actual_target_path":"/cargo-tracker/admin/show.xhtml","action_executed":True,
                 "target_origin_verified":True,"query_keys":["trackingId"]}
        lookup={**common,"current_navigation_driver":"browser-lookup-v1","action_method":"POST",
                "action_path":"/cargo-tracker/admin/track.xhtml","entry_page":"admin/track.xhtml",
                "source_entry_verified":True,"submission_status":303,
                "invalid_inputs_verified":True,"csrf_checks_verified":True}
        proof={"replacement_driver":"browser-replacement-v1","group":"tracking-discovery",
               "tracking_id":"ABCDEFGH","identity":identity,"list_proof":listing,"lookup_proof":lookup}
        case={"capability_id":"tracking-discovery","actor":"Reader","binding_status":"browser-replacement-v1",
              "method":"POST","legacy_ids":["ACTION-23","ACTION-44"]}
        self.assertTrue(replacement_observation(case,proof)["semantic_success"])
        for target,key,value in [("lookup_proof","tracking_id","OTHERID1"),
                                 ("lookup_proof","invalid_inputs_verified",False),
                                 ("list_proof","actual_target_path","/other")]:
            changed=copy.deepcopy(proof)
            changed[target][key]=value
            with self.subTest(target=target,key=key),self.assertRaises(UnsupportedCase):
                replacement_observation(case,changed)
