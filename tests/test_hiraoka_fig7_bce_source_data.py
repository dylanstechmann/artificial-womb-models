import json
import re
import statistics
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaFigure7BCESourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["fig7_hi_source_data"]
        self.observations = [
            item for item in self.dataset["observations"]
            if item["source"]["artifact_id"] == "hiraoka2025-fig7-source-data"
        ]
        self.coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}

    def test_panels_b_and_c_preserve_formula_count_cells_and_caption_units(self):
        self.assertEqual(self.audit["curated_sheets"], ["7B", "7C", "7E", "7H", "7I"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 197)
        expected = {
            ("B", "dmso-egfp"): ("DMSO+EGFP", [(6, 6), (6, 6), (5, 6), (5, 6), (11, 12)],
                                   ["=H3/I3", "=H4/I4", "=H5/I5", "=H6/I6", "=H7/I7"], 91.666667, 3.726780),
            ("B", "celecoxib-egfp"): ("Celecoxib+EGFP", [(10, 14), (7, 10), (5, 6), (5, 6), (9, 12)],
                                        ["=J3/K3", "=J4/K4", "=J5/K5", "=J6/K6", "=J7/K7"], 76.619048, 2.859523),
            ("B", "celecoxib-myr-akt1"): ("Celecoxib+myr-AKT1", [(12, 15), (10, 14), (11, 12), (11, 12), (10, 12)],
                                           ["=L3/M3", "=L4/M4", "=L5/M5", "=L6/M6", "=L7/M7"], 83.619048, 3.816511),
            ("C", "dmso-egfp"): ("DMSO+EGFP", [(5, 6), (5, 6), (4, 6), (5, 6), (11, 12)],
                                   ["=H3/I3", "=H4/I4", "=H5/I5", "=H6/I6", "=H7/I7"], 81.666667, 4.082483),
            ("C", "celecoxib-egfp"): ("Celecoxib+EGFP", [(3, 14), (3, 10), (1, 6), (2, 6), (3, 12)],
                                        ["=J3/K3", "=J4/K4", "=J5/K5", "=J6/K6", "=J7/K7"], 25.285714, 2.968466),
            ("C", "celecoxib-myr-akt1"): ("Celecoxib+myr-AKT1", [(6, 15), (6, 14), (6, 12), (9, 12), (6, 12)],
                                           ["=L3/M3", "=L4/M4", "=L5/M5", "=L6/M6", "=L7/M7"], 51.571429, 6.179294),
        }
        audit = {(item["panel"], item["condition_slug"]): item
                 for item in self.audit["panel_BC_per_recipient_groups"]}
        for (panel, slug), (condition, counts, formulas, mean_pct, sem_pp) in expected.items():
            records = [item for item in self.observations
                       if item["record_id"].startswith(f"hiraoka-fig7-{panel.lower()}-{slug}-")]
            self.assertEqual(len(records), 5)
            self.assertTrue(all(item["independent_unit"]["kind"] == "pregnant_animal"
                                and item["independent_unit"]["id"] is None for item in records))
            self.assertEqual([item["observation"]["measurement_time"] for item in records],
                             ["24h"] * 5 if panel == "B" else ["48h"] * 5)
            observed_formulas = []
            for item in records:
                context = item["assay"]["functional_context"]["quantity_basis"]
                observed_formulas.append(re.search(r"Publisher formula (=\w+\d+/\w+\d+)", context).group(1))
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertEqual(values, [n / d for n, d in counts])
            self.assertAlmostEqual(statistics.mean(values) * 100, mean_pct, places=5)
            self.assertAlmostEqual(statistics.stdev(values) / len(values) ** 0.5 * 100, sem_pp, places=5)
            summary = audit[(panel, slug)]
            self.assertEqual(summary["condition"], condition)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_pct, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)
            self.assertIn(f"hiraoka-fig7-{panel.lower()}-{slug}-coverage", self.coverage_ids)

        self.assertIn("Exp labels do not establish recipient identity",
                      self.audit["identity_and_interpretation_limit"])

    def test_panel_e_preserves_all_embryo_values_and_the_literal_axis_unit(self):
        expected = {
            "dmso-egfp": [11.7662, 5.04978, 7.15198, 7.62224, 6.34805, 9.2296, 8.52779,
                           12.259, 9.93159, 7.00824, 12.7909, 7.33057, 9.95868],
            "celecoxib-egfp": [7.34489, 5.47283, 6.71118, 3.0781, 4.94501, 9.59988, 0.87956,
                               4.60958, 2.00789, 7.65262],
            "celecoxib-myr-akt1": [6.03271, 8.53588, 6.98481, 7.09849, 12.1121, 13.5369,
                                    6.1544, 7.6299],
        }
        audits = {item["condition_slug"]: item for item in self.audit["panel_E_invading_volume_groups"]}
        for slug, source_values in expected.items():
            records = sorted((item for item in self.observations
                              if item["record_id"].startswith(f"hiraoka-fig7-e-{slug}-row")),
                             key=lambda item: int(item["record_id"].rsplit("row", 1)[1]))
            self.assertEqual(len(records), len(source_values))
            self.assertEqual([item["observation"]["value"] for item in records], source_values)
            self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                and item["independent_unit"]["id"] is None
                                and item["independent_unit"]["parent_id"] is None for item in records))
            self.assertTrue(all(item["assay"]["unit"] == "1E+05μm^3" for item in records))
            self.assertTrue(all(item["observation"]["measurement_time"] == "not stated"
                                for item in records))
            self.assertTrue(all("group-local" in item["independent_unit"]["hierarchy_note"]
                                for item in records))
            self.assertEqual(audits[slug]["source_values"], source_values)
            self.assertAlmostEqual(audits[slug]["mean"], statistics.mean(source_values), places=5)
            self.assertAlmostEqual(audits[slug]["sample_sem"],
                                   statistics.stdev(source_values) / len(source_values) ** 0.5, places=5)
            self.assertIn(f"hiraoka-fig7-e-{slug}-coverage", self.coverage_ids)

        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(len(self.observations), 197)


if __name__ == "__main__":
    unittest.main()
