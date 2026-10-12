import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


EXPECTED_NORMALIZED = {
    "0h": [1.226762, 0.815907, 0.910026, 0.998342, 0.888323, 1.141454, 1.019186],
    "24h-pbs": [1.278764, 0.962027, 1.109007, 1.257275, 0.938605, 1.078923],
    "24h-myr-akt1": [2.380894, 3.506017, 2.043099, 4.113274, 1.661469, 2.023975, 2.68044,
                     1.690263, 3.095807, 1.561333, 1.922335, 2.910793, 1.947906, 2.363703],
    "48h-pbs": [1.614624, 2.440201, 1.307128, 2.361984, 1.894616, 0.958159, 0.876289,
                1.839176, 1.234283, 0.860603, 1.826928, 1.223324],
    "48h-myr-akt1": [4.9771, 2.282908, 2.151185, 3.112782, 2.403671, 2.288065, 2.152044,
                     2.57923, 1.999263, 2.366497, 2.677001, 2.800988, 2.34157, 3.232257,
                     3.602284, 1.287574, 2.261634, 2.62414, 2.682159, 2.086505, 1.166165,
                     1.321955, 2.098539, 1.359559, 1.338501, 1.327972, 2.028702, 0.982871,
                     1.745487, 1.133073, 6.37942, 3.617111, 2.945389, 1.405114, 1.601087,
                     1.618277, 1.995395, 2.200608, 1.377824, 3.067657, 2.360265, 4.784995,
                     2.68044, 3.511174, 1.232994],
}

EXPECTED_RAW_0H = [5.709, 3.797, 4.235, 4.646, 4.134, 5.312, 4.743]


class HiraokaSupplementaryFig14SourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["suppfig14_source_data"]
        self.records = [item for item in self.dataset["observations"]
                        if item["record_id"].startswith("hiraoka-suppfig14-b-")]
        self.coverage = {item["coverage_id"]: item for item in self.dataset["cohort_coverage"]
                         if item["coverage_id"].startswith("hiraoka-suppfig14-b-")}

    def test_moesm22_hash_sheet_and_caption_counts_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-suppfig14-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-suppfig14.xlsx"))
        expected_hash = "f95b4df0f6f04caa62cb637bf82c87b6628c0aca44f5af37a2a3b335c14ac450"
        self.assertEqual(source["sha256"], expected_hash)
        self.assertEqual(snapshot["sha256"], expected_hash)
        self.assertEqual(snapshot["bytes"], 12239)
        self.assertEqual(self.audit["curated_sheets"], ["14B"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 84)
        self.assertEqual(len(self.records), 84)
        self.assertEqual(len(self.coverage), 5)

    def test_all_normalized_values_and_paired_raw_values_are_retained_once(self):
        audit_groups = {item["condition_slug"]: item for item in self.audit["groups"]}
        for slug, expected in EXPECTED_NORMALIZED.items():
            with self.subTest(condition=slug):
                records = [item for item in self.records
                           if item["record_id"].startswith(f"hiraoka-suppfig14-b-{slug}-")]
                records.sort(key=lambda item: int(item["record_id"].rsplit("embryo", 1)[1]))
                self.assertEqual([item["observation"]["value"] for item in records], expected)
                self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                    and item["independent_unit"]["id"] is None
                                    and item["independent_unit"]["parent_id"] is None
                                    for item in records))
                self.assertEqual(audit_groups[slug]["normalized_source_values"], expected)
                self.assertEqual(len(audit_groups[slug]["raw_source_values"]), len(expected))
                self.assertEqual(self.coverage[f"hiraoka-suppfig14-b-{slug}-coverage"]["denominator"]["value"],
                                 len(expected))

        self.assertEqual(len(self.audit["paired_raw_scale_values"]), 84)
        raw_note = self.audit["raw_normalization_note"]
        self.assertEqual(raw_note["paired_raw_normalized_rows"], 84)
        self.assertFalse(raw_note["raw_values_are_additional_observations"])
        self.assertEqual(audit_groups["0h"]["raw_source_values"], EXPECTED_RAW_0H)
        raw_mean = sum(EXPECTED_RAW_0H) / len(EXPECTED_RAW_0H)
        self.assertAlmostEqual(raw_note["reference_raw_0h_mean"], raw_mean, places=9)
        for pair in self.audit["paired_raw_scale_values"]:
            self.assertAlmostEqual(pair["raw_value"] / raw_mean, pair["normalized_value"], delta=1.1e-6)

    def test_source_tests_and_limits_are_not_promoted_to_later_outcomes(self):
        self.assertIn("two-tailed unpaired Student t-tests", self.audit["statistical_annotations"])
        self.assertIn("no p-value or inferential statistic was recalculated", self.audit["statistical_annotations"])
        self.assertIn("group-local", self.audit["identity_and_interpretation_limit"])
        self.assertIn("do not establish birth", self.audit["identity_and_interpretation_limit"])
        self.assertTrue(all(item["observation"]["measurement_time"] in ("0h", "24h", "48h")
                            for item in self.records))


if __name__ == "__main__":
    unittest.main()
