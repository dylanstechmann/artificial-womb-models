import hashlib
import json
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-suppfig1.xlsx"
EXPECTED_SHA256 = "f34b1385968afa5039fb14a35face0da30ec71ef79754a1aeeaa517b3fbff097"


class HiraokaSupplementaryFig1WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audits = cls.inventory["source_mapping_audit"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-suppfig1-source-data"]

    def test_hash_and_all_six_workbook_tabs_are_pinned_and_curated(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 17937)
        self.assertEqual(sorted(self.workbook_cells), ["1B", "1C", "1D", "1E", "1F", "1G"])
        audit = self.audits["fig1b_source_data"]
        self.assertEqual(audit["curated_sheets"], ["1B", "1C", "1D", "1E", "1F", "1G"])
        self.assertEqual(audit["unreviewed_sheets"], [])
        self.assertEqual(len(self.records), 78)

    def test_all_seventy_eight_source_formula_rows_match_cached_values_and_observations(self):
        slug_prefix = {
            "B": "{slug}", "C": "{slug}", "D": "estrogen-{slug}",
            "E": "endometrium-{slug}", "F": "embryo-{slug}",
            "G": "hatching-{slug}",
        }
        checked = 0
        for letter in "BCDEFG":
            sheet_name = f"1{letter}"
            audit = self.audits[f"fig1{letter.lower()}_source_data"]
            groups = audit.get("group_summaries", audit.get("groups", []))
            sheet = self.workbook_cells[sheet_name]
            for group in groups:
                self.assertEqual(sheet[group["source_column"]]["value"],
                                 "PMGS" if letter in ("E", "F") and group["condition_slug"] == "pmsg"
                                 else group.get("condition", group.get("figure_label")))
                id_slug = slug_prefix[letter].format(slug=group["condition_slug"])
                for index, (cell, formula, numerator, denominator) in enumerate(zip(
                        group["source_row_cells"], group["source_formulas"],
                        group["numerators"], group["initially_loaded_denominators"]), start=1):
                    with self.subTest(sheet=sheet_name, cell=cell):
                        source = sheet[cell]
                        expected_value = numerator / denominator
                        self.assertEqual(source["formula"], formula)
                        self.assertAlmostEqual(source["value"], expected_value, places=14)
                        record_id = f"hiraoka-suppfig1{letter.lower()}-{id_slug}-exp{index}"
                        record = next(item for item in self.records if item["record_id"] == record_id)
                        self.assertAlmostEqual(record["observation"]["value"], source["value"], places=14)
                        self.assertIn(formula, record["assay"]["functional_context"]["quantity_basis"])
                        self.assertIsNone(record["independent_unit"]["id"])
                        checked += 1
        self.assertEqual(checked, 78)

    def test_pmgs_workbook_label_remains_distinct_from_caption_pmsg(self):
        for key, sheet_name in (("fig1e_source_data", "1E"), ("fig1f_source_data", "1F")):
            audit = self.audits[key]
            self.assertIn("PMGS", audit["label_qualification"])
            self.assertIn("PMSG", audit["label_qualification"])
            pmsg_group = next(group for group in audit["groups"] if group["condition_slug"] == "pmsg")
            self.assertEqual(self.workbook_cells[sheet_name][pmsg_group["source_column"]]["value"], "PMGS")


if __name__ == "__main__":
    unittest.main()
