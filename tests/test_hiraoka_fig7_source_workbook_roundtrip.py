import hashlib
import json
import math
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-fig7.xlsx"
EXPECTED_SHA256 = "7f72cc20ca652dcdcfe7c2e894b350ac0c0309893cabe38ef1ac3c1d8ba2b2fb"
class HiraokaFigure7WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["fig7_hi_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-fig7-source-data"]

    def test_pinned_workbook_and_all_five_tabs_are_the_audited_source(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 17722)
        self.assertEqual(sorted(self.workbook_cells), ["7B", "7C", "7E", "7H", "7I"])
        self.assertEqual(self.audit["curated_sheets"], ["7B", "7C", "7E", "7H", "7I"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 197)
        self.assertEqual(len(self.records), 197)

    def test_formula_panels_match_workbook_formula_count_cells_and_observations(self):
        checked = 0
        for group in self.audit["panel_BC_per_recipient_groups"]:
            sheet = self.workbook_cells[group["worksheet"]]
            panel = group["panel"].lower()
            for row in group["formula_rows"]:
                with self.subTest(sheet=group["worksheet"], cell=row["chart_cell"]):
                    chart = sheet[row["chart_cell"]]
                    numerator = sheet[row["numerator_cell"]]["value"]
                    denominator = sheet[row["denominator_cell"]]["value"]
                    self.assertEqual(chart["formula"], row["formula"])
                    self.assertEqual(numerator, row["numerator"])
                    self.assertEqual(denominator, row["denominator"])
                    self.assertAlmostEqual(chart["value"], row["cached_rate"], places=14)
                    self.assertGreater(denominator, 0)
                    self.assertAlmostEqual(numerator / denominator, chart["value"], places=14)
                    exp_number = int(row["source_row_label"].split()[-1])
                    record = next(item for item in self.records if item["record_id"] ==
                                   f"hiraoka-fig7-{panel}-{group['condition_slug']}-exp{exp_number}")
                    self.assertAlmostEqual(record["observation"]["value"], chart["value"], places=14)
                    self.assertIn(f"{row['numerator_cell']}={row['numerator']}",
                                  record["assay"]["functional_context"]["quantity_basis"])
                    checked += 1
        self.assertEqual(checked, 30)

    def test_panel_e_h_i_measurements_match_exact_source_cells(self):
        checked = 0
        for group in self.audit["panel_E_invading_volume_groups"]:
            for index, (cell, expected) in enumerate(zip(group["source_cells"], group["source_values"]), start=1):
                with self.subTest(sheet="7E", cell=cell):
                    source_value = self.workbook_cells["7E"][cell]["value"]
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-fig7-e-{group['condition_slug']}-row{int(cell[1:])}")
                    self.assertAlmostEqual(source_value, expected, places=12)
                    self.assertAlmostEqual(record["observation"]["value"], source_value, places=12)
                    checked += 1

        for group in self.audit["panel_H_recipient_mouse_groups"]:
            for cell, expected in zip(group["source_cells"], group["implantation_site_counts"]):
                with self.subTest(sheet="7H", cell=cell):
                    source_value = self.workbook_cells["7H"][cell]["value"]
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-fig7-h-{group['condition_slug']}-row{int(cell[1:])}")
                    self.assertEqual(source_value, expected)
                    self.assertEqual(record["observation"]["value"], source_value)
                    checked += 1

        for group in self.audit["panel_I_site_weight_groups"]:
            for index, cell in enumerate(group["source_cells"], start=1):
                with self.subTest(sheet="7I", cell=cell):
                    source_value = self.workbook_cells["7I"][cell]["value"]
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-fig7-i-{group['condition_slug']}-site{index}")
                    self.assertTrue(math.isfinite(source_value))
                    self.assertAlmostEqual(record["observation"]["value"], source_value, places=12)
                    checked += 1

        self.assertEqual(checked, 167)


if __name__ == "__main__":
    unittest.main()
