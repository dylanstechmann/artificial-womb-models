import hashlib
import json
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-suppfig10.xlsx"
EXPECTED_SHA256 = "f2ff92109116958a43bca744cf51a2a5d1fc6c2218866e7d7373fbbe849d6dc4"


class HiraokaSupplementaryFig10WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["suppfig10_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-suppfig10-source-data"]

    def test_hash_and_sheet_scope_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 9918)
        self.assertEqual(list(self.workbook_cells), ["10B"])
        self.assertEqual(self.audit["curated_sheets"], ["10B"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 6)
        self.assertEqual(len(self.records), 6)

    def test_each_formula_cell_cache_and_candidate_record_match(self):
        sheet = self.workbook_cells["10B"]
        checked = 0
        for group in self.audit["groups"]:
            header_cell = f"{group['source_cells'][0][0]}1"
            self.assertEqual(sheet[header_cell]["value"], group["workbook_label"])
            for index, (cell, formula, numerator, denominator, expected_value) in enumerate(zip(
                    group["source_cells"], group["source_formulas"], group["numerators"],
                    group["formula_denominators"], group["source_fractions"]), start=1):
                with self.subTest(condition=group["condition_slug"], cell=cell):
                    source = sheet[cell]
                    self.assertEqual(source["formula"], formula)
                    self.assertAlmostEqual(source["value"], expected_value, places=14)
                    self.assertAlmostEqual(numerator / denominator, source["value"], places=14)
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-suppfig10-b-{group['condition_slug']}-row{index}")
                    self.assertAlmostEqual(record["observation"]["value"], source["value"], places=14)
                    self.assertEqual(record["independent_unit"]["kind"], "other")
                    self.assertIsNone(record["independent_unit"]["id"])
                    self.assertEqual(record["assay"]["functional_context"]["source_locator"].split("cell ")[1].split(";")[0], cell)
                    checked += 1
        self.assertEqual(checked, 6)

    def test_caption_sample_n_and_source_formula_denominators_stay_separate(self):
        self.assertIn("Celexoxib", self.audit["workbook_label_qualification"])
        self.assertIn("Celecoxib", self.audit["workbook_label_qualification"])
        for group in self.audit["groups"]:
            self.assertEqual(group["biologically_independent_sample_n"], 3)
            self.assertEqual(len(group["formula_denominators"]), 3)
            self.assertTrue(all(value != 3 for value in group["formula_denominators"]))
            coverage_id = f"hiraoka-suppfig10-b-{group['condition_slug']}-coverage"
            coverage = next(item for item in self.dataset["cohort_coverage"]
                            if item["coverage_id"] == coverage_id)
            self.assertEqual(coverage["denominator"]["value"], 3)
            self.assertIn("distinct from each formula denominator",
                          coverage["denominator"]["reported_label"].lower())


if __name__ == "__main__":
    unittest.main()
