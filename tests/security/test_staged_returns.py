import copy
import unittest
from staged_returns import return_observation
from contracts import UnsupportedCase

class StagedReturnTests(unittest.TestCase):
    tracking = "ABCDEFGH"
    editor = "/cargo-tracker/admin/changeDestination.xhtml?trackingId=ABCDEFGH"
    details = "/cargo-tracker/admin/show.xhtml?trackingId=ABCDEFGH"

    def case(self, actor):
        return {"actor": actor, "surface_id": "ACTION-13", "method": "GET",
                "path": "/cargo-tracker/admin/show.xhtml?trackingId={cargo}",
                "current_source": "admin/changeDestination.xhtml"}

    def allowed(self):
        return {
            "return_driver": "native-staged-return-v1", "tracking_id": self.tracking,
            "editor": {"method": "GET", "path": self.editor, "status": 200, "owned_form_verified": True},
            "save": {"method": "POST", "path": self.editor, "status": 303,
                     "location": self.details + "&jfwid=window%3A0",
                     "csrf_verified": True, "persisted_effect_verified": True,
                     "destination_invocation_delta": 1, "queues_unchanged": True,
                     "deadline_preserved": True, "other_cargos_unchanged": True},
            "details": {"method": "GET", "path": self.details, "status": 200,
                        "selected_details_verified": True},
        }

    def test_owned_save_and_same_cargo_return(self):
        for actor in ["Operator", "Administrator"]:
            result = return_observation(self.case(actor), self.allowed())
            self.assertEqual(result["status"], 200)
            self.assertEqual(result["evaluated_stage"], "details")

    def test_absolute_return_is_bound_to_exact_fixture_origin_and_context(self):
        proof = self.allowed()
        proof["fixture_base"] = "http://fixture:8080/cargo-tracker/"
        proof["save"]["location"] = "http://fixture:8080" + self.details + "&jfwid=window%3A0"
        self.assertEqual(return_observation(self.case("Operator"), proof)["status"], 200)
        for location in [
            "http://fixture:8081" + self.details,
            "https://fixture:8080" + self.details,
            "http://evil.example:8080" + self.details,
            "http://fixture:8080/other/show.xhtml?trackingId=ABCDEFGH",
            "//evil.example:8080" + self.details,
            "//fixture:8080" + self.details,
        ]:
            changed = copy.deepcopy(proof)
            changed["save"]["location"] = location
            with self.subTest(location=location), self.assertRaises(UnsupportedCase):
                return_observation(self.case("Operator"), changed)

    def test_wrong_return_cargo_external_target_and_missing_effects_fail(self):
        for field, value in [
            ("location", self.details.replace(self.tracking, "OTHERID1")),
            ("location", "https://evil.example" + self.details),
            ("location", self.details + "&trackingId=ABCDEFGH"),
            ("persisted_effect_verified", False),
            ("destination_invocation_delta", 2),
            ("queues_unchanged", False),
            ("csrf_verified", False),
        ]:
            proof = self.allowed()
            proof["save"][field] = value
            with self.subTest(field=field), self.assertRaises(UnsupportedCase):
                return_observation(self.case("Operator"), proof)

    def test_reader_editor_denial_and_direct_details_allow_are_distinct(self):
        proof = self.allowed()
        proof["editor"] = {"method": "GET", "path": self.editor, "status": 403,
                           "protected_payload_absent": True}
        proof["save"] = None
        proof["denied_entry_effects_unchanged"] = True
        result = return_observation(self.case("Reader"), proof)
        self.assertEqual(result["status"], 403)
        self.assertEqual(result["details"]["status"], 200)
        self.assertEqual(result["evaluated_stage"], "editor")
        for stage, field, value in [("editor", "status", 200), ("details", "status", 403),
                                    ("details", "selected_details_verified", False)]:
            altered = copy.deepcopy(proof)
            altered[stage][field] = value
            with self.subTest(stage=stage, field=field), self.assertRaises(UnsupportedCase):
                return_observation(self.case("Reader"), altered)

    def test_anonymous_requires_both_fixed_login_denials(self):
        proof = self.allowed()
        for stage in ["editor", "details"]:
            proof[stage] = {"method": "GET", "path": self.editor if stage == "editor" else self.details,
                            "status": 303, "protected_payload_absent": True,
                            "redirect_is_configured_login": True}
        proof["save"] = None
        proof["denied_entry_effects_unchanged"] = True
        self.assertEqual(return_observation(self.case("anonymous"), proof)["status"], 303)
        proof["details"]["redirect_is_configured_login"] = False
        with self.assertRaises(UnsupportedCase):
            return_observation(self.case("anonymous"), proof)
