import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaFigure6IJKSourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["fig6_ijk_source_data"]

    def test_moesm15_hash_scope_and_later_assay_withdrawal_limits_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-fig6-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-fig6.xlsx"))
        self.assertEqual(source["sha256"], "ac868f78c32c1a612093c189a5345304497a8a6875ec1eae261c32d687f2ec7e")
        self.assertEqual(snapshot["sha256"], source["sha256"])
        self.assertEqual(snapshot["bytes"], 23386)
        self.assertEqual(self.audit["curated_sheets"], ["6F", "6G", "6H", "6I", "6J", "6K", "6M"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 64)
        self.assertEqual(self.audit["source_observation_rows_added"], 34)
        self.assertIn("do not identify recipients", self.audit["cross_panel_limit"])
        self.assertIn("Do not infer them by subtraction", self.audit["withdrawal_limit"])

    def test_thirty_recipient_formula_rows_preserve_panel_specific_denominators(self):
        expected = {
            ("6I", "dmso"): ("DMSO", ["=H3/I3", "=H4/I4", "=H5/I5", "=H6/I6"], 95.833333, 4.166667),
            ("6I", "mk2206-10um"): ("MK-2206 (10 μM)", ["=J3/K3", "=J4/K4", "=J5/K5"], 91.035354, 1.885503),
            ("6I", "mk2206-100um"): ("MK-2206 (100 μM)", ["=L3/M3", "=L4/M4", "=L5/M5"], 79.470899, 11.986083),
            ("6J", "dmso"): ("DMSO", ["=H3/I3", "=H4/I4", "=H5/I5", "=H6/I6"], 9.166667, 4.166667),
            ("6J", "mk2206-10um"): ("MK-2206 (10 μM)", ["=J3/K3", "=J4/K4", "=J5/K5"], 11.215686, 5.627963),
            ("6J", "mk2206-100um"): ("MK-2206 (100 μM)", ["=L3/M3", "=L4/M4", "=L5/M5"], 100.0, 0.0),
            ("6K", "dmso"): ("DMSO", ["=H3/I3", "=H4/I4", "=H5/I5", "=H6/I6"], 87.083333, 5.788518),
            ("6K", "mk2206-10um"): ("MK-2206 (10 μM)", ["=J3/K3", "=J4/K4", "=J5/K5"], 81.018519, 3.240741),
            ("6K", "mk2206-100um"): ("MK-2206 (100 μM)", ["=L3/M3", "=L4/M4", "=L5/M5"], 0.0, 0.0),
        }
        self.assertEqual(self.audit["source_observation_rows"], 64)
        panel_audits = {panel["panel"].lower(): panel for panel in self.audit["panels"]}
        for (panel, slug), (condition, formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-fig6-{panel[1:].lower()}-{slug}-")]
            self.assertEqual(len(records), len(formulas))
            self.assertTrue(all(item["source"]["artifact_id"] == "hiraoka2025-fig6-source-data"
                                for item in records))
            self.assertTrue(all(item["independent_unit"]["kind"] == "pregnant_animal"
                                and item["independent_unit"]["id"] is None for item in records))
            observed_formulas = [
                re.search(r"formula (=\w+\d+/\w+\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            pa = panel_audits[panel.lower()]
            summary = next(item for item in pa["groups"] if item["condition"] == condition)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)
            cov_id = f"hiraoka-fig6-{panel[1:].lower()}-{slug}-coverage"
            self.assertIn(cov_id, {item["coverage_id"] for item in self.dataset["cohort_coverage"]})

        self.assertIn("no count or identity map", self.audit["panels"][1]["denominator_note"])
        self.assertIn("initially-loaded denominator", self.audit["panels"][2]["denominator_note"])


if __name__ == "__main__":
    unittest.main()
