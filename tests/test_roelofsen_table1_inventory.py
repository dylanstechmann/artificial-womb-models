import csv
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/roelofsen_table1_papp_aggregate_source_cells.csv"
RATIO_INVENTORY = ROOT / "config/source_inventories/roelofsen_table1_papp_ratio_source_cells.csv"
SOURCE = ROOT / "artifacts/transport-collection-2026-10-09/roelofsen-fulltext-xml.xml"


class RoelofsenTable1InventoryTests(unittest.TestCase):
    def setUp(self):
        with INVENTORY.open(newline="", encoding="utf-8") as stream:
            self.rows = list(csv.DictReader(stream))
        with RATIO_INVENTORY.open(newline="", encoding="utf-8") as stream:
            self.ratios = list(csv.DictReader(stream))

    def test_all_fifteen_mean_sd_cells_match_transcribed_source_text(self):
        expected = [
            "7.9*10–06 ± 3.3*10–06", "1.1*10–06 ± 0.4*10–06",
            "7.1*10–06 ± 3.6*10–06", "7.7*10–06 ± 3.9*10–06",
            "8.9*10–06 ± 3.6*10–06",
            "2.3*10–05 ± 0.2*10–05", "2.1*10–06 ± 0.01*10–06",
            "1.5*10–05 ± 0.3*10–05", "2.3*10–05 ± 0.4*10–05",
            "1.8*10–05 ± 0.5*10–05",
            "2.4*10–05 ± 0.4*10–05", "2.04*10–06 ± 0.01*10–06",
            "1.6*10–05 ± 0.2*10–05", "2.5*10–05 ± 0.2*10–05",
            "1.2*10–05 ± 0.1*10–05",
        ]
        self.assertEqual(len(self.rows), 15)
        self.assertEqual([row["source_value_text"] for row in self.rows], expected)

    def test_group_n_time_and_conditions_are_preserved_separately(self):
        self.assertEqual([int(row["reported_n"]) for row in self.rows], [4] * 5 + [3] * 10)
        self.assertEqual([int(row["reported_time"]) for row in self.rows], [20] * 5 + [60] * 10)
        self.assertEqual([row["compound_addition_condition"] for row in self.rows],
                         ["mixture"] * 10 + ["separate_compounds"] * 5)
        self.assertTrue(all("assay-family caption-level N" in row["reported_n_unit"]
                            for row in self.rows))
        self.assertTrue(all("not independently specified by compound-cell" in row["sample_size_source_locator"]
                            for row in self.rows))

    def test_area_qualification_is_attached_only_to_ex_vivo_values(self):
        for row in self.rows[:5]:
            self.assertIn("unresolved_100x_area_unit_discrepancy", row["area_qualification"])
            self.assertIn("No rescaling", row["area_qualification"])
        for row in self.rows[5:]:
            self.assertIn("not_the_ex_vivo_area_discrepancy", row["area_qualification"])
        self.assertIn("row label inherited by rowspan", self.rows[10]["source_cell_locator"])

    def test_inventory_is_tied_to_the_pinned_source_bytes(self):
        actual_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.assertTrue(all(row["source_sha256"] == actual_hash for row in self.rows))
        self.assertTrue(all(row["source_sha256"] == actual_hash for row in self.ratios))

    def test_reported_ratio_cells_are_separate_from_what_if_scaling(self):
        self.assertEqual([row["reported_ratio_text"] for row in self.ratios],
                         ["0.35", "0.54", "0.47", "0.34", "0.50",
                          "0.34", "0.55", "0.45", "0.31", "0.75"])
        self.assertEqual([row["conditional_100x_ratio_if_larger_area_used"] for row in self.ratios],
                         ["35", "54", "47", "34", "50", "34", "55", "45", "31", "75"])
        self.assertTrue(all("not recalculated from displayed means" in row["ratio_interpretation"]
                            for row in self.ratios))
        amoxicillin_mix = self.ratios[1]
        self.assertAlmostEqual(float(amoxicillin_mix["ratio_of_displayed_means_derived"]),
                               1.1e-6 / 2.1e-6)
        self.assertAlmostEqual(float(amoxicillin_mix["reported_minus_derived_ratio"]),
                               0.54 - (1.1e-6 / 2.1e-6))
        self.assertNotEqual(amoxicillin_mix["reported_ratio"],
                            amoxicillin_mix["ratio_of_displayed_means_derived"])
        self.assertTrue(all("not substituted" in row["derived_ratio_interpretation"]
                            for row in self.ratios))
        self.assertTrue(all("what-if only" in row["intake_boundary"] for row in self.ratios))


if __name__ == "__main__":
    unittest.main()
