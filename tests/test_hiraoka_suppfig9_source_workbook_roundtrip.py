import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-suppfig9.xlsx"
EXPECTED_SHA256 = "cef46750fe037ce8dbd1776835b5b8b9a7b48d5e56df16f4bea17dbf438f02ae"


class HiraokaSupplementaryFig9WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["suppfig9_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-suppfig9-source-data"]

    def test_hash_crc_and_all_eight_populated_sheet_scopes_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 19976)
        with zipfile.ZipFile(WORKBOOK) as archive:
            self.assertIsNone(archive.testzip())
        expected_sheets = ["9A", "9B", "9C", "9D", "9G", "9I", "9J", "9K"]
        self.assertEqual(sorted(self.workbook_cells), expected_sheets)
        self.assertEqual(self.audit["curated_sheets"], expected_sheets)
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 80)
        self.assertEqual(len(self.records), 80)

    def test_all_sixty_formula_rows_match_source_formula_cache_and_records(self):
        checked = 0
        for group in self.audit["recipient_ratio_groups"]:
            sheet = self.workbook_cells[group["worksheet"]]
            for index, row in enumerate(group["formula_rows"], start=1):
                with self.subTest(sheet=group["worksheet"], cell=row["source_cell"]):
                    source = sheet[row["source_cell"]]
                    self.assertEqual(source["formula"], row["source_formula"])
                    self.assertEqual(source["value"], row["fraction"])
                    self.assertEqual(row["numerator"] / row["denominator"], source["value"])
                    record_id = (f"hiraoka-suppfig9-{group['panel'][-1].lower()}-"
                                 f"{group['condition_slug']}-exp{index}")
                    record = next(item for item in self.records if item["record_id"] == record_id)
                    self.assertEqual(record["observation"]["value"], source["value"])
                    self.assertEqual(record["assay"]["functional_context"]["source_locator"].split("cell ")[1].split(";")[0],
                                     row["source_cell"])
                    checked += 1
        self.assertEqual(checked, 60)

    def test_all_normalized_and_paired_raw_cox2_cells_match_once(self):
        checked = 0
        groups = {group["condition_slug"]: group for group in self.audit["cox2_area_groups"]}
        baseline_raw = [self.workbook_cells["9G"][cell]["value"]
                        for cell in groups["30-percent-ksr"]["raw_source_cells"]]
        reference_mean = sum(baseline_raw) / len(baseline_raw)
        for slug, group in groups.items():
            for index, pair in enumerate(group["paired_row_values"], start=1):
                with self.subTest(condition=slug, cell=pair["normalized_cell"]):
                    normalized = self.workbook_cells["9G"][pair["normalized_cell"]]["value"]
                    raw = self.workbook_cells["9G"][pair["raw_cell"]]["value"]
                    self.assertAlmostEqual(normalized, pair["normalized_value"], places=14)
                    self.assertAlmostEqual(raw, pair["raw_value"], places=12)
                    self.assertAlmostEqual(raw / reference_mean, normalized, delta=1.1e-12)
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-suppfig9-g-{slug}-embryo{index}")
                    self.assertAlmostEqual(record["observation"]["value"], normalized, places=14)
                    checked += 1
        self.assertEqual(checked, 11)
        self.assertIn("not counted as additional biological observations", self.audit["cox2_raw_scale_note"])

    def test_nine_volume_cells_and_unresolved_9b_and_9ij_limits_are_preserved(self):
        checked = 0
        for group in self.audit["invasion_volume_groups"]:
            for index, (cell, expected) in enumerate(zip(group["source_cells"], group["source_values"]), start=1):
                with self.subTest(sheet="9K", cell=cell):
                    source_value = self.workbook_cells["9K"][cell]["value"]
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-suppfig9-k-{group['condition_slug']}-embryo{index}")
                    self.assertAlmostEqual(source_value, expected, places=14)
                    self.assertAlmostEqual(record["observation"]["value"], source_value, places=14)
                    self.assertEqual(record["assay"]["unit"], "1E+05μm^3")
                    self.assertEqual(record["observation"]["measurement_time"], "unreported")
                    checked += 1
        self.assertEqual(checked, 9)
        self.assertIn("no count or identity", self.audit["panel_9b_exclusion_note"].lower())
        self.assertIn("n=3 vs4", self.audit["caption_workbook_n_mismatch"])
        self.assertIn("No fourth value or identity was located", self.audit["caption_workbook_n_mismatch"])


if __name__ == "__main__":
    unittest.main()
