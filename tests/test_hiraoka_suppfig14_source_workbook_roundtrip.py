import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from xlsx_source_utils import xlsx_sheet_cells


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"
WORKBOOK = ROOT / "artifacts/uterine-interface-2026-10-09/source-data-suppfig14.xlsx"
EXPECTED_SHA256 = "f95b4df0f6f04caa62cb637bf82c87b6628c0aca44f5af37a2a3b335c14ac450"


class HiraokaSupplementaryFig14WorkbookRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.audit = cls.inventory["source_mapping_audit"]["suppfig14_source_data"]
        cls.workbook_cells = xlsx_sheet_cells(WORKBOOK)
        cls.records = [item for item in cls.dataset["observations"]
                       if item["source"]["artifact_id"] == "hiraoka2025-suppfig14-source-data"]

    def test_hash_crc_sheet_and_84_record_scope_are_pinned(self):
        self.assertEqual(hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(WORKBOOK.stat().st_size, 12239)
        with zipfile.ZipFile(WORKBOOK) as archive:
            self.assertIsNone(archive.testzip())
        self.assertEqual(list(self.workbook_cells), ["14B"])
        self.assertEqual(self.audit["curated_sheets"], ["14B"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 84)
        self.assertEqual(len(self.records), 84)

    def test_every_normalized_observation_and_paired_raw_cell_matches(self):
        sheet = self.workbook_cells["14B"]
        groups = {group["condition_slug"]: group for group in self.audit["groups"]}
        baseline = groups["0h"]
        baseline_raw = [sheet[cell]["value"] for cell in baseline["raw_source_cells"]]
        reference_mean = sum(baseline_raw) / len(baseline_raw)
        self.assertAlmostEqual(reference_mean, self.audit["raw_normalization_note"]["reference_raw_0h_mean"], places=9)

        checked = 0
        for slug, group in groups.items():
            for index, pair in enumerate(group["paired_values"], start=1):
                with self.subTest(condition=slug, cell=pair["normalized_cell"]):
                    normalized = sheet[pair["normalized_cell"]]["value"]
                    raw = sheet[pair["raw_cell"]]["value"]
                    self.assertAlmostEqual(normalized, pair["normalized_value"], places=14)
                    self.assertAlmostEqual(raw, pair["raw_value"], places=12)
                    self.assertAlmostEqual(raw / reference_mean, normalized, delta=1.1e-6)
                    record = next(item for item in self.records if item["record_id"] ==
                                  f"hiraoka-suppfig14-b-{slug}-embryo{index}")
                    self.assertAlmostEqual(record["observation"]["value"], normalized, places=14)
                    self.assertEqual(record["independent_unit"]["kind"], "embryo")
                    self.assertIsNone(record["independent_unit"]["id"])
                    checked += 1
        self.assertEqual(checked, 84)
        self.assertEqual(len(self.audit["paired_raw_scale_values"]), 84)
        self.assertFalse(self.audit["raw_normalization_note"]["raw_values_are_additional_observations"])

    def test_source_normalization_note_and_no_inference_are_retained(self):
        note_cell = self.audit["raw_normalization_note"]["source_note_cell"]
        sheet_value = self.workbook_cells["14B"][note_cell]["value"]
        self.assertEqual(note_cell, "I48")
        self.assertNotIn("N48", self.workbook_cells["14B"])
        self.assertEqual(sheet_value,
                         self.audit["raw_normalization_note"]["source_note"])
        self.assertIn("Each raw value was normalized", sheet_value)
        self.assertIn("no p-value or inferential statistic was recalculated",
                      self.audit["statistical_annotations"].lower())
        self.assertIn("group-local", self.audit["identity_and_interpretation_limit"])
        self.assertTrue(all(record["observation"]["measurement_time"] in ("0h", "24h", "48h")
                            for record in self.records))


if __name__ == "__main__":
    unittest.main()
