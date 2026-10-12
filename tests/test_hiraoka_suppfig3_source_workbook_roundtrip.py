import hashlib
import json
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-suppfig3.xlsx"
EXPECTED_SHA256 = "89f198ad7fda5993cebc57814adbf4e6acc5c2fbe0a4fda462f28845b1a25162"


class HiraokaSupplementaryFig3WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["suppfig3_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-suppfig3-source-data"]

    def test_workbook_hash_tabs_and_full_record_scope_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 11759)
        self.assertEqual(sorted(self.workbook_cells), ["3C", "3D"])
        self.assertEqual(self.audit["curated_sheets"], ["3C", "3D"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 116)
        self.assertEqual(len(self.records), 116)

    def test_every_epi_and_te_count_matches_workbook_cell_row_and_candidate_record(self):
        checked = 0
        for group in self.audit["panel_groups"]:
            sheet = self.workbook_cells[group["worksheet"]]
            for index, (cell, expected, row_label) in enumerate(zip(
                    group["source_cells"], group["source_values"], group["source_row_labels"]), start=1):
                with self.subTest(sheet=group["worksheet"], cell=cell):
                    source = sheet[cell]["value"]
                    source_row_label = sheet[f"A{int(cell[1:])}"]["value"]
                    header = sheet[f"{cell[0]}1"]["value"]
                    self.assertEqual(source, expected)
                    self.assertEqual(source_row_label, row_label)
                    self.assertEqual(header, group["condition"])
                    record_id = (f"hiraoka-suppfig3-{group['panel'].lower()}-"
                                 f"{group['condition_slug']}-embryo{index}")
                    record = next(item for item in self.records if item["record_id"] == record_id)
                    self.assertEqual(record["observation"]["value"], source)
                    self.assertEqual(record["assay"]["endpoint"], group["endpoint"])
                    self.assertIsNone(record["independent_unit"]["id"])
                    checked += 1
        self.assertEqual(checked, 116)


if __name__ == "__main__":
    unittest.main()
