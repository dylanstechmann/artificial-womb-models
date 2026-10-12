import hashlib
import json
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-suppfig4.xlsx"
EXPECTED_SHA256 = "8d6039cd476b7ae09d76d9e9aa0807b49bcce918ead1d7e3797b4c3d73ee9e5d"


class HiraokaSupplementaryFig4EWorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["fig4e_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-suppfig4-source-data"]

    def test_hash_and_one_sheet_scope_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 10187)
        self.assertEqual(list(self.workbook_cells), ["4E"])
        self.assertEqual(self.audit["source_observation_rows"], 12)
        self.assertEqual(len(self.records), 12)

    def test_all_twelve_formula_cells_match_source_cache_and_candidate_values(self):
        sheet = self.workbook_cells["4E"]
        coverage = {item["coverage_id"]: item for item in self.dataset["cohort_coverage"]}
        checked = 0
        for group in self.audit["groups"]:
            slug = f"{group['dish_label'].lower()}-{group['marker_status']}-marker"
            for index, (cell, formula, numerator, denominator) in enumerate(zip(
                    group["source_row_cells"], group["source_formulas"], group["numerators"],
                    group["initially_loaded_denominators"]), start=1):
                with self.subTest(condition=slug, cell=cell):
                    source = sheet[cell]
                    self.assertEqual(source["formula"], formula)
                    self.assertAlmostEqual(source["value"], numerator / denominator, places=14)
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-suppfig4e-{slug}-exp{index}")
                    self.assertAlmostEqual(record["observation"]["value"], source["value"], places=14)
                    self.assertEqual(record["assay"]["unit"],
                                     "proportion (source morphogenesis category / initially loaded embryos)")
                    self.assertEqual(record["independent_unit"]["kind"], "other")
                    self.assertIsNone(record["independent_unit"]["id"])
                    checked += 1

            coverage_id = f"hiraoka-suppfig4e-{slug}-coverage"
            self.assertEqual(coverage[coverage_id]["denominator"]["value"], 3)
            self.assertEqual(group["independent_samples_n"], 3)
        self.assertEqual(checked, 12)

    def test_panel_remains_separate_from_persistent_ceiling_failure(self):
        self.assertIn("does not provide the starting denominator",
                      self.audit["separation_from_persistent_ceiling_failure"])
        self.assertEqual(self.audit["reported_comparisons"]["recalculation"], "No inferential test recalculated")


if __name__ == "__main__":
    unittest.main()
