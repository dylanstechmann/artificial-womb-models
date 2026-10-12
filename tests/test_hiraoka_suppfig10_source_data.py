import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


EXPECTED = {
    "dmso": (["=3/29", "=2/26", "=2/14"], [3 / 29, 2 / 26, 2 / 14]),
    "celecoxib": (["=3/25", "=2/19", "=2/28"], [3 / 25, 2 / 19, 2 / 28]),
}


class HiraokaSupplementaryFig10SourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["suppfig10_source_data"]
        self.records = [item for item in self.dataset["observations"]
                        if item["record_id"].startswith("hiraoka-suppfig10-b-")]
        self.coverage = {item["coverage_id"]: item for item in self.dataset["cohort_coverage"]
                         if item["coverage_id"].startswith("hiraoka-suppfig10-b-")}

    def test_moesm21_hash_and_full_sheet_scope_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-suppfig10-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-suppfig10.xlsx"))
        expected_hash = "f2ff92109116958a43bca744cf51a2a5d1fc6c2218866e7d7373fbbe849d6dc4"
        self.assertEqual(source["sha256"], expected_hash)
        self.assertEqual(snapshot["sha256"], expected_hash)
        self.assertEqual(snapshot["bytes"], 9918)
        self.assertEqual(self.audit["curated_sheets"], ["10B"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 6)
        self.assertEqual(len(self.records), 6)
        self.assertEqual(len(self.coverage), 2)

    def test_exact_formula_rows_and_biological_sample_n_are_distinct(self):
        audits = {item["condition_slug"]: item for item in self.audit["groups"]}
        for slug, (formulas, expected_values) in EXPECTED.items():
            with self.subTest(condition=slug):
                records = [item for item in self.records
                           if item["record_id"].startswith(f"hiraoka-suppfig10-b-{slug}-")]
                records.sort(key=lambda item: int(item["record_id"].rsplit("row", 1)[1]))
                self.assertEqual([item["observation"]["value"] for item in records], expected_values)
                observed_formulas = [re.search(r"publisher formula (=\d+/\d+)",
                                               item["assay"]["functional_context"]["quantity_basis"]).group(1)
                                     for item in records]
                self.assertEqual(observed_formulas, formulas)
                self.assertTrue(all(item["independent_unit"]["kind"] == "other"
                                    and item["independent_unit"]["id"] is None
                                    and item["independent_unit"]["parent_id"] is None
                                    for item in records))
                self.assertTrue(all(item["observation"]["measurement_time"] == "96h" for item in records))
                self.assertTrue(all("distinct from caption n=3" in item["assay"]["functional_context"]["quantity_basis"]
                                    for item in records))
                coverage = self.coverage[f"hiraoka-suppfig10-b-{slug}-coverage"]
                self.assertEqual(coverage["denominator"]["value"], 3)
                self.assertIn("three source ratio rows", coverage["population_frame"])
                self.assertEqual(audits[slug]["workbook_formula_rows"], 3)
                self.assertEqual(audits[slug]["source_formulas"], formulas)

    def test_spelling_and_reported_nonsignificant_annotation_are_preserved(self):
        self.assertIn("Celexoxib", self.audit["workbook_label_qualification"])
        self.assertIn("Celecoxib", self.audit["workbook_label_qualification"])
        self.assertIn("P=0.7312 (ns)", self.audit["reported_statistics"])
        self.assertIn("No inferential p-value was recalculated", self.audit["reported_statistics"])
        self.assertAlmostEqual(self.audit["groups"][0]["mean_fraction_percent"], 10.774283, places=6)
        self.assertAlmostEqual(self.audit["groups"][1]["mean_fraction_percent"], 9.889724, places=6)


if __name__ == "__main__":
    unittest.main()
