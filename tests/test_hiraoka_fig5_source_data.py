import json
import re
import statistics
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaFigure5SourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["fig5_source_data"]
        self.records = [item for item in self.dataset["observations"]
                        if item["record_id"].startswith("hiraoka-fig5-")]
        self.coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}

    def test_four_moesm14_sheets_and_source_bytes_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-figure5-source")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("figure5.xlsx"))
        expected_hash = "6ceed8646a488132f4fe6f973abac3da1848d2258e27cecc19bee6a9a8ecd6e4"
        self.assertEqual(source["sha256"], expected_hash)
        self.assertEqual(snapshot["sha256"], expected_hash)
        self.assertEqual(snapshot["bytes"], 16200)
        self.assertEqual(self.audit["curated_sheets"], ["5F", "5G", "5I", "5K"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 48)
        self.assertEqual(len(self.records), 48)

    def test_recipient_fraction_panels_keep_exact_formula_counts_and_sample_units(self):
        expected = {
            ("5F", "dmso"): ([(4, 4), (10, 10), (5, 5), (20, 21), (6, 6), (5, 5)],
                               ["=G3/H3", "=G4/H4", "=G5/H5", "=G6/H6", "=G7/H7", "=G8/H8"], 6, "24h"),
            ("5F", "celecoxib"): ([(20, 27), (15, 15), (5, 6), (6, 6), (11, 20), (14, 19), (20, 24)],
                                    ["=I3/J3", "=I4/J4", "=I5/J5", "=I6/J6", "=I7/J7", "=I8/J8", "=I9/J9"], 7, "24h"),
            ("5G", "dmso"): ([(1, 4), (0, 10), (1, 5), (1, 5)],
                               ["=G3/H3", "=G4/H4", "=G5/H5", "=G6/H6"], 4, "24-48h"),
            ("5G", "celecoxib"): ([(11, 15), (8, 15), (3, 5), (14, 15), (11, 14)],
                                    ["=I3/J3", "=I4/J4", "=I5/J5", "=I6/J6", "=I7/J7"], 5, "24-48h"),
            ("5I", "dmso"): ([(3, 4), (10, 10), (4, 5), (4, 5)],
                               ["=G3/H3", "=G4/H4", "=G5/H5", "=G6/H6"], 4, "48h"),
            ("5I", "celecoxib"): ([(4, 21), (7, 15), (3, 6), (1, 15), (3, 19)],
                                    ["=I3/J3", "=I4/J4", "=I5/J5", "=I6/J6", "=I7/J7"], 5, "48h"),
        }
        audits = {(item["panel"], item["condition_slug"]): item
                  for item in self.audit["recipient_ratio_groups"]}
        for (panel, slug), (counts, formulas, n, time) in expected.items():
            records = [item for item in self.records
                       if item["record_id"].startswith(f"hiraoka-fig5-{panel[-1].lower()}-{slug}-")]
            self.assertEqual(len(records), n)
            self.assertTrue(all(item["independent_unit"]["kind"] == "pregnant_animal"
                                and item["independent_unit"]["id"] is None for item in records))
            self.assertEqual([item["observation"]["measurement_time"] for item in records], [time] * n)
            observed_formulas = []
            for item in records:
                basis = item["assay"]["functional_context"]["quantity_basis"]
                observed_formulas.append(re.search(r"Publisher formula (=\w+\d+/\w+\d+)", basis).group(1))
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertEqual(values, [numerator / denominator for numerator, denominator in counts])
            audit = audits[(panel, slug)]
            self.assertEqual(audit["recipient_mouse_n"], n)
            self.assertAlmostEqual(statistics.mean(values) * 100,
                                   audit["mean_of_recipient_fractions_percent"], places=5)
            self.assertAlmostEqual(statistics.stdev(values) / len(values) ** 0.5 * 100,
                                   audit["sample_sem_percentage_points"], places=5)
            self.assertIn(f"hiraoka-fig5-{panel[-1].lower()}-{slug}-coverage", self.coverage_ids)

        note_panels = {item["panel"]: item for item in self.audit["denominator_notes"]}
        self.assertIn("no withdrawal count/identity", note_panels["5G"]["qualification"])
        self.assertIn("denominator differ from 5F", note_panels["5I"]["qualification"])
        self.assertIn("susteined", self.audit["workbook_label_qualification"])
        self.assertIn("Exp labels do not establish recipient identity", self.audit["identity_and_interpretation_limit"])

    def test_panel_k_preserves_embryo_volume_values_and_literal_unit(self):
        expected = {
            "dmso": [15.4517, 13.0049, 11.9079, 11.3888, 5.5615, 8.54089, 8.0493, 3.62581],
            "celecoxib": [5.80369, 7.98266, 2.72849, 5.42478, 6.08588, 0.24099, 6.79284,
                          0.81868203125, 5.59502],
        }
        volume_audit = {item["condition_slug"]: item
                        for item in self.audit["panel_K_invasion_volume_groups"]}
        for slug, values in expected.items():
            records = sorted((item for item in self.records
                              if item["record_id"].startswith(f"hiraoka-fig5-k-{slug}-row")),
                             key=lambda item: int(item["record_id"].rsplit("row", 1)[1]))
            self.assertEqual([item["observation"]["value"] for item in records], values)
            self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                and item["independent_unit"]["id"] is None for item in records))
            self.assertTrue(all(item["assay"]["unit"] == "1E+05μm^3" for item in records))
            self.assertTrue(all(item["observation"]["measurement_time"] == "48h" for item in records))
            self.assertTrue(all("group-local" in item["independent_unit"]["hierarchy_note"]
                                for item in records))
            self.assertEqual(volume_audit[slug]["source_values"], values)
            self.assertAlmostEqual(volume_audit[slug]["mean"], statistics.mean(values), places=5)
            self.assertAlmostEqual(volume_audit[slug]["sample_sem"],
                                   statistics.stdev(values) / len(values) ** 0.5, places=5)
            self.assertIn(f"hiraoka-fig5-k-{slug}-coverage", self.coverage_ids)


if __name__ == "__main__":
    unittest.main()
