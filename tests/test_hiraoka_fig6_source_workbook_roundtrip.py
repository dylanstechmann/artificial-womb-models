import hashlib
import json
import unittest
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-fig6.xlsx"
EXPECTED_SHA256 = "ac868f78c32c1a612093c189a5345304497a8a6875ec1eae261c32d687f2ec7e"


class HiraokaFigure6WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["fig6_ijk_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-fig6-source-data"]

    def test_workbook_hash_tabs_and_full_64_record_scope_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 23386)
        self.assertEqual(sorted(self.workbook_cells), ["6F", "6G", "6H", "6I", "6J", "6K", "6M"])
        self.assertEqual(self.audit["curated_sheets"], ["6F", "6G", "6H", "6I", "6J", "6K", "6M"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 64)
        self.assertEqual(len(self.records), 64)

    def test_normalized_and_raw_fgh_pairs_match_original_cells(self):
        checked = 0
        for panel in self.audit["direct_measurement_panels"]:
            sheet = self.workbook_cells[panel["panel"]]
            groups = {group["condition_slug"]: group for group in panel["groups"]}
            dmso_raw = [sheet[cell]["value"] for cell in groups["dmso"]["raw_source_cells"]]
            reference_mean = sum(dmso_raw) / len(dmso_raw)
            for group in panel["groups"]:
                for index, pair in enumerate(group["paired_values"], start=1):
                    with self.subTest(panel=panel["panel"], cell=pair["normalized_cell"]):
                        normalized = sheet[pair["normalized_cell"]]["value"]
                        raw = sheet[pair["raw_cell"]]["value"]
                        self.assertAlmostEqual(normalized, pair["normalized_value"], places=14)
                        self.assertAlmostEqual(raw, pair["raw_value"], places=12)
                        self.assertAlmostEqual(raw / reference_mean, normalized, delta=1.1e-6)
                        record = next(item for item in self.records if item["record_id"] ==
                                      f"hiraoka-fig6-{panel['panel'][-1].lower()}-"
                                      f"{group['condition_slug']}-embryo{index}")
                        self.assertAlmostEqual(record["observation"]["value"], normalized, places=14)
                        checked += 1
        self.assertEqual(checked, 21)

    def test_ijk_formula_cells_and_6m_numeric_and_n_a_cells_match(self):
        checked = 0
        for panel in self.audit["panels"]:
            sheet = self.workbook_cells[panel["panel"]]
            for group in panel["groups"]:
                for index, row in enumerate(group["formula_rows"], start=1):
                    with self.subTest(panel=panel["panel"], cell=row["chart_cell"]):
                        chart = sheet[row["chart_cell"]]
                        numerator = sheet[row["numerator_cell"]]["value"]
                        denominator = sheet[row["denominator_cell"]]["value"]
                        self.assertEqual(chart["formula"], row["formula"])
                        self.assertEqual(numerator, row["numerator"])
                        self.assertEqual(denominator, row["denominator"])
                        self.assertAlmostEqual(chart["value"], numerator / denominator, places=14)
                        record = next(item for item in self.records if item["record_id"] ==
                                      f"hiraoka-fig6-{panel['panel'][-1].lower()}-"
                                      f"{group['condition_slug']}-exp{index}")
                        self.assertAlmostEqual(record["observation"]["value"], chart["value"], places=14)
                        checked += 1

        invasion = self.audit["invasion_volume_panel_6M"]
        for group in invasion["caption_sample_n_groups"]:
            for index, (cell, expected) in enumerate(zip(group["source_cells"], group["source_values"]), start=1):
                with self.subTest(panel="6M", cell=cell):
                    value = self.workbook_cells["6M"][cell]["value"]
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-fig6-m-{group['condition_slug']}-embryo{index}")
                    self.assertAlmostEqual(value, expected, places=14)
                    self.assertAlmostEqual(record["observation"]["value"], value, places=14)
                    checked += 1

        unavailable = invasion["nonnumeric_source_cells"][0]
        self.assertEqual(self.workbook_cells["6M"][unavailable["cell"]]["value"], "N/A")
        self.assertFalse(unavailable["numeric_observation_created"])
        self.assertFalse(any(item["record_id"].startswith("hiraoka-fig6-m-mk2206-100um")
                             for item in self.records))
        self.assertEqual(checked, 43)


if __name__ == "__main__":
    unittest.main()
