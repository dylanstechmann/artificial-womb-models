import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaSupplementaryFig4ESourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["fig4e_source_data"]

    def test_moesm19_source_artifact_is_hash_pinned_and_scope_is_bounded(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-suppfig4-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-suppfig4.xlsx"))
        self.assertEqual(source["sha256"], "8d6039cd476b7ae09d76d9e9aa0807b49bcce918ead1d7e3797b4c3d73ee9e5d")
        self.assertEqual(snapshot["sha256"], source["sha256"])
        self.assertEqual(snapshot["bytes"], 10187)
        self.assertEqual(self.audit["source_observation_rows"], 12)
        self.assertIn("does not provide the starting denominator", self.audit["separation_from_persistent_ceiling_failure"])

    def test_four_96h_morphogenesis_fraction_groups_preserve_source_formulas(self):
        expected = {
            "plastic-with-marker": (["=5/44", "=4/39", "=6/58"], 10.654958, 0.355257),
            "plastic-without-marker": (["=4/44", "=3/39", "=5/58"], 8.467969, 0.410899),
            "pdms-with-marker": (["=4/35", "=6/62", "=5/48"], 10.507552, 0.507552),
            "pdms-without-marker": (["=3/35", "=6/62", "=3/48"], 8.166283, 1.009935),
        }
        labels = {
            "plastic-with-marker": "Plastic bottom; morphogenesis with marker expression",
            "plastic-without-marker": "Plastic bottom; morphogenesis without marker expression",
            "pdms-with-marker": "PDMS bottom; morphogenesis with marker expression",
            "pdms-without-marker": "PDMS bottom; morphogenesis without marker expression",
        }
        for slug, (formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-suppfig4e-{slug}-")]
            self.assertEqual(len(records), 3)
            self.assertTrue(all(item["source"]["artifact_id"] == "hiraoka2025-suppfig4-source-data"
                                for item in records))
            self.assertTrue(all(item["independent_unit"]["kind"] == "other"
                                and item["independent_unit"]["id"] is None for item in records))
            observed_formulas = [
                re.search(r"formula (=?\d+/\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(observed_formulas, formulas)
            self.assertTrue(all(item["observation"]["measurement_time"] == "96h" for item in records))
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            summary = next(item for item in self.audit["groups"] if item["condition"] == labels[slug])
            self.assertAlmostEqual(summary["mean_of_source_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)

        self.assertEqual(self.audit["reported_comparisons"]["with_marker_triangle_series"], "P=0.8281")
        self.assertEqual(self.audit["reported_comparisons"]["without_marker_square_series"], "P=0.7970")
        self.assertEqual(self.audit["reported_comparisons"]["recalculation"], "No inferential test recalculated")
        coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}
        self.assertTrue(all(f"hiraoka-suppfig4e-{slug}-coverage" in coverage_ids for slug in expected))


if __name__ == "__main__":
    unittest.main()
