import hashlib
import json
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/figure5.xlsx"
EXPECTED_SHA256 = "6ceed8646a488132f4fe6f973abac3da1848d2258e27cecc19bee6a9a8ecd6e4"


class HiraokaFigure5WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["fig5_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-figure5-source"
                       and item["record_id"].startswith("hiraoka-fig5-")]

    def test_hash_sheet_scope_and_record_count_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 16200)
        self.assertEqual(sorted(self.workbook_cells), ["5F", "5G", "5I", "5K"])
        self.assertEqual(self.audit["curated_sheets"], ["5F", "5G", "5I", "5K"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 48)
        self.assertEqual(len(self.records), 48)

    def test_recipient_formula_caches_counts_labels_and_records_match(self):
        checked = 0
        for group in self.audit["recipient_ratio_groups"]:
            sheet = self.workbook_cells[group["worksheet"]]
            for index, row in enumerate(group["formula_rows"], start=1):
                with self.subTest(panel=group["panel"], cell=row["chart_cell"]):
                    chart = sheet[row["chart_cell"]]
                    # The source uses shared formulas: followers store an empty
                    # shared-formula node, while the audit expands each relative reference.
                    self.assertIn(chart["formula"], (row["formula"], "="))
                    self.assertEqual(sheet[row["numerator_cell"]]["value"], row["numerator"])
                    self.assertEqual(sheet[row["denominator_cell"]]["value"], row["denominator"])
                    self.assertEqual(sheet[f"A{row['chart_cell'][1:]}"]["value"],
                                     row["source_row_label"])
                    expected_rate = row["numerator"] / row["denominator"]
                    self.assertAlmostEqual(chart["value"], row["cached_rate"], places=14)
                    self.assertAlmostEqual(chart["value"], expected_rate, places=14)

                    panel_slug = group["panel"][-1].lower()
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-fig5-{panel_slug}-{group['condition_slug']}-exp{index}")
                    self.assertAlmostEqual(record["observation"]["value"], chart["value"], places=14)
                    self.assertEqual(record["observation"]["measurement_time"],
                                     group["endpoint"].split(" ")[0])
                    context = record["assay"]["functional_context"]
                    self.assertIn(f"Publisher formula {row['formula']}", context["quantity_basis"])
                    self.assertIn(row["chart_cell"], context["source_locator"])
                    self.assertIn(row["numerator_cell"], context["source_locator"])
                    self.assertIn(row["denominator_cell"], context["source_locator"])
                    checked += 1
        self.assertEqual(checked, 31)

    def test_embryo_volumes_and_exclusion_notes_match_source(self):
        checked = 0
        sheet = self.workbook_cells["5K"]
        for group in self.audit["panel_K_invasion_volume_groups"]:
            for index, (cell, label, expected) in enumerate(zip(
                    group["source_cells"], group["source_row_labels"], group["source_values"]), start=1):
                with self.subTest(panel="5K", cell=cell):
                    self.assertAlmostEqual(sheet[cell]["value"], expected, places=14)
                    row_label = f"A{cell[1:]}"
                    self.assertEqual(sheet[row_label]["value"], label)
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-fig5-k-{group['condition_slug']}-row{index}")
                    self.assertAlmostEqual(record["observation"]["value"], sheet[cell]["value"], places=14)
                    self.assertEqual(record["assay"]["unit"], group["reported_unit"])
                    self.assertIn(f"sheet 5K cell {cell}",
                                  record["assay"]["functional_context"]["source_locator"])
                    checked += 1
        self.assertEqual(checked, 17)

        note_5g = self.workbook_cells["5G"]["G9"]["value"]
        note_5i = self.workbook_cells["5I"]["G9"]["value"]
        self.assertIn("excluded from the", note_5g)
        self.assertIn("denominators because", note_5g)
        self.assertIn("evaluation of shedding or retention at 48h was not available", note_5g)
        self.assertIn("number of experiments and the denominators", note_5i)
        self.assertIn("are different", note_5i)
        notes = {item["panel"]: item for item in self.audit["denominator_notes"]}
        self.assertTrue(all(notes[panel]["source_locator"].endswith("cell G9") for panel in ("5G", "5I")))


if __name__ == "__main__":
    unittest.main()
