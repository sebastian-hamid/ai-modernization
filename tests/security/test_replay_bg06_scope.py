import json
import unittest

from replay_bg06_scoped_gate import (
    BASE_GATE, DESIRED, SCOPE_RECEIPT, apply_promotions, build_replay,
    object_sha256, outcome_counts,
)


class Bg06ScopedReplayTests(unittest.TestCase):
    def setUp(self):
        self.promotions = {
            **{f"CURRENT::BG-06::{actor}::active": "PASS"
                for actor in ("anonymous", "Reader", "Operator", "Administrator")},
            "CURRENT::BG-06-MACHINE::deployment-migration::active": "PASS",
        }
        self.rows = [
            {"case": case, "outcome": "BLOCKED", "reason": "Required candidate adapter is unavailable"}
            for case in self.promotions
        ] + [
            {"case": "CURRENT::UNRELATED::active", "outcome": "PASS", "reason": None},
            {"case": "CURRENT::OTHER-BLOCK::active", "outcome": "BLOCKED", "reason": "No adapter"},
        ]

    def test_promotes_only_the_five_named_bg06_rows(self):
        before = [dict(row) for row in self.rows]
        after = apply_promotions(self.rows, self.promotions)
        promoted = {row["case"]: row for row in after}
        self.assertTrue(all(promoted[case]["outcome"] == "PASS" for case in self.promotions))
        self.assertEqual(promoted["CURRENT::UNRELATED::active"], before[-2])
        self.assertEqual(promoted["CURRENT::OTHER-BLOCK::active"], before[-1])
        self.assertEqual(outcome_counts(after), {"PASS": 6, "BLOCKED": 1})

    def test_rejects_missing_or_extra_promotion_contracts(self):
        with self.assertRaises(ValueError):
            apply_promotions(self.rows, {key: "PASS" for key in list(self.promotions)[:-1]})
        with self.assertRaises(ValueError):
            apply_promotions(self.rows, {**self.promotions, "CURRENT::OTHER::active": "PASS"})

    def test_rejects_promotion_when_baseline_is_not_blocked(self):
        altered = [dict(row) for row in self.rows]
        altered[0]["outcome"] = "PASS"
        with self.assertRaises(ValueError):
            apply_promotions(altered, self.promotions)

    def test_rejects_missing_or_duplicate_baseline_ids(self):
        with self.assertRaises(ValueError):
            apply_promotions([{"outcome": "BLOCKED"}], self.promotions)
        duplicate = self.rows + [dict(self.rows[0])]
        with self.assertRaises(ValueError):
            apply_promotions(duplicate, self.promotions)

    def test_reviewed_inputs_produce_only_the_five_case_count_delta(self):
        gate_bytes = BASE_GATE.read_bytes()
        scope_bytes = SCOPE_RECEIPT.read_bytes()
        gate = json.loads(gate_bytes)
        scope = json.loads(scope_bytes)
        desired = json.loads(DESIRED.read_text())
        prior_rows = json.loads(json.dumps(gate["current_results"]))
        result = build_replay(gate, scope, desired, gate_bytes, scope_bytes)
        self.assertEqual(result["previous_current_counts"], {"PASS": 449, "BLOCKED": 21})
        self.assertEqual(result["replayed_current_counts"], {"PASS": 454, "BLOCKED": 16})
        self.assertEqual(len(result["promoted_cases"]), 5)
        self.assertEqual(gate["current_results"], prior_rows)
        promoted_ids = {row["case"] for row in result["promoted_cases"]}
        untouched = [row for row in prior_rows if row["case"] not in promoted_ids]
        self.assertEqual(result["untouched_current_results_sha256"], object_sha256(untouched))
        self.assertEqual(result["legacy_counts_preserved"], {"PASS": 324, "BLOCKED": 178})
        self.assertEqual(result["retirement_counts_preserved"], {"BLOCKED": 76})
        self.assertEqual(result["legacy_results_sha256"], object_sha256(gate["legacy_audit"]["results"]))
        self.assertEqual(result["retirement_results_sha256"], object_sha256(gate["retirement_results"]))
        self.assertEqual(result["gate_exit"], 2)

    def test_reviewed_scope_digest_rejects_reconstructed_or_edited_receipt(self):
        gate_bytes = BASE_GATE.read_bytes()
        scope_bytes = SCOPE_RECEIPT.read_bytes() + b" "
        scope = json.loads(SCOPE_RECEIPT.read_text())
        desired = json.loads(DESIRED.read_text())
        gate = json.loads(gate_bytes)
        with self.assertRaisesRegex(ValueError, "reviewed artifact"):
            build_replay(gate, scope, desired, gate_bytes, scope_bytes)


if __name__ == "__main__":
    unittest.main()
