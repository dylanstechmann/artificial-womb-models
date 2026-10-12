import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle304"
DATA = ROOT / "config/observations/eixarch_2026_ep09_40_hpa_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchEP0940HPACycle304Tests(unittest.TestCase):
    def test_primary_poster_and_crossref_snapshots_are_pinned(self):
        assessment = json.loads((ART / "hpa-intake-and-linkage-cycle304.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256((ART / "ep09-40-poster-source.pdf").read_bytes()).hexdigest(), assessment["source"]["poster_sha256"])
        self.assertEqual(hashlib.sha256((ART / "crossref-ep09-40.json").read_bytes()).hexdigest(), assessment["source"]["crossref_sha256"])
        self.assertEqual(assessment["source"]["doi"], "10.1002/uog.70305_746")
        self.assertEqual(assessment["source"]["page"], "261-262")
        self.assertEqual(assessment["source"]["relation"], {})

    def test_candidate_preserves_six_analyte_group_summaries(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(len(data["observations"]), 12)
        expected = {
            "acth": (47.2, 29.4, "p < 0.001"),
            "corticosterone": (0.42, 0.67, "p = 0.5 (ns)"),
            "cortisol": (4.9, 2.1, "p = 0.007"),
            "cortisone": (7.3, 1.1, "p < 0.001"),
            "cortol": (1.4, 0.11, "p < 0.001"),
            "progesterone": (1.35, 0.06, "p < 0.001"),
        }
        for slug, (baseline, h72, p_value) in expected.items():
            before = next(o for o in data["observations"] if o["record_id"] == f"ep09-40-{slug}-0h")
            after = next(o for o in data["observations"] if o["record_id"] == f"ep09-40-{slug}-72h")
            self.assertEqual(before["observation"]["value"], baseline)
            self.assertEqual(after["observation"]["value"], h72)
            for row in (before, after):
                self.assertIsNone(row["observation"]["summary_statistic"]["reported_sample_size"])
                self.assertIn(p_value, row["observation"]["measurement_uncertainty"])
                self.assertIn("not a pairwise", row["observation"]["measurement_uncertainty"])
                self.assertEqual(row["observation"]["replicate_role"], "summary_only")

    def test_cohort_n_is_not_reused_as_timepoint_n(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        coverage = data["cohort_coverage"][0]
        self.assertEqual(coverage["denominator"]["value"], 16)
        self.assertIn("timepoint-specific", coverage["selection_definition"])
        self.assertTrue(all(o["observation"]["summary_statistic"]["reported_sample_size"] is None for o in data["observations"]))
        self.assertIn("all-start denominator", " ".join(data["limitations"]))

    def test_possible_poster_overlap_does_not_establish_identity_or_pool_counts(self):
        assessment = json.loads((ART / "hpa-intake-and-linkage-cycle304.json").read_text(encoding="utf-8"))
        compatibility = assessment["cross_poster_compatibility"]
        self.assertEqual(compatibility["EP09_22"]["cases_within_EP09_40_GA_range"], 2)
        self.assertTrue(compatibility["EP09_22"]["all_durations_at_least_72h"])
        self.assertFalse(compatibility["counts_may_be_summed"])
        self.assertFalse(compatibility["independent_replication_established"])

    def test_candidate_validation_receipt_matches_current_input(self):
        assessment = json.loads((ART / "hpa-intake-and-linkage-cycle304.json").read_text(encoding="utf-8"))
        receipt = json.loads((ART / "validate-ep09-40-final/receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(assessment["candidate_intake"]["validation_input_sha256"], receipt["input_sha256"])
        self.assertEqual(assessment["candidate_intake"]["validation_status"], "passed; local poster hash verified; PRE (0 h) label preserved")

    def test_source_inventory_keeps_poster_record_distinct(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(r for r in inventory["records"] if r["record_id"] == "eixarch_2026_isuog_hpa_dynamics_EP09_40")
        self.assertEqual(record["cohort_size"]["value"], 16)
        self.assertEqual(record["machine_readable_candidate_intake"]["record_count"], 12)
        self.assertEqual(record["transition_events"], [])
        self.assertFalse(inventory["cohort_linkage_screen"]["poster_overlap_screen_cycle304"]["counts_may_be_summed"])


if __name__ == "__main__":
    unittest.main()
