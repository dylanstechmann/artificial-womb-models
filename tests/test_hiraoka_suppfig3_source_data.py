import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


EXPECTED = {
    "e375": ([19, 14, 12, 19, 16, 15, 27, 23, 25], [41, 45, 69, 60, 51, 68, 56, 43, 47], "E3.75"),
    "sole-culture-24h": ([27, 20, 24, 17, 21, 24, 17, 21, 32, 18, 24, 25, 25, 21, 26, 23],
                         [50, 53, 49, 57, 47, 63, 47, 54, 58, 57, 53, 52, 52, 49, 59, 55], "24h"),
    "coculture-no-contact-24h": ([24, 27, 27, 21, 23, 27, 26, 22, 17, 20, 29, 25, 21, 14, 27],
                                 [75, 78, 66, 59, 54, 87, 59, 67, 58, 75, 66, 45, 51, 45, 54], "24h"),
    "coculture-contact-unattached-24h": ([22, 23, 29, 28, 30, 17, 26, 27], [91, 115, 74, 82, 87, 60, 85, 84], "24h"),
    "coculture-contact-attached-24h": ([16, 30, 29, 20, 33, 37], [99, 118, 118, 78, 122, 88], "24h"),
    "e45": ([31, 32, 35, 31], [123, 111, 122, 126], "E4.5"),
}


class HiraokaSupplementaryFig3SourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["suppfig3_source_data"]
        self.records = [item for item in self.dataset["observations"]
                        if item["record_id"].startswith("hiraoka-suppfig3-")]
        self.coverage = {item["coverage_id"]: item for item in self.dataset["cohort_coverage"]
                         if item["coverage_id"].startswith("hiraoka-suppfig3-")}

    def test_moesm18_hash_and_sheet_scope_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-suppfig3-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-suppfig3.xlsx"))
        expected_hash = "89f198ad7fda5993cebc57814adbf4e6acc5c2fbe0a4fda462f28845b1a25162"
        self.assertEqual(source["sha256"], expected_hash)
        self.assertEqual(snapshot["sha256"], expected_hash)
        self.assertEqual(snapshot["bytes"], 11759)
        self.assertEqual(self.audit["curated_sheets"], ["3C", "3D"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 116)
        self.assertEqual(len(self.records), 116)

    def test_all_epi_te_values_are_transcribed_without_cross_group_identity(self):
        for slug, (epi, te, time) in EXPECTED.items():
            for panel, values, endpoint, compartment in (
                ("c", epi, "EPI cell count per embryo", "Embryonic EPI"),
                ("d", te, "TE cell count per embryo", "Embryonic TE"),
            ):
                records = [item for item in self.records
                           if item["record_id"].startswith(f"hiraoka-suppfig3-{panel}-{slug}-")]
                records.sort(key=lambda item: int(item["record_id"].rsplit("embryo", 1)[1]))
                expected_n = len(values)
                self.assertEqual([item["observation"]["value"] for item in records], values)
                self.assertEqual([item["observation"]["measurement_time"] for item in records], [time] * expected_n)
                self.assertTrue(all(item["assay"]["endpoint"] == endpoint for item in records))
                self.assertTrue(all(item["assay"]["unit"] == "cells" for item in records))
                self.assertTrue(all(item["assay"]["functional_context"]["compartment"] == compartment
                                    for item in records))
                self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                    and item["independent_unit"]["id"] is None
                                    and item["independent_unit"]["parent_id"] is None
                                    for item in records))
                self.assertTrue(all("does not establish identity" in item["independent_unit"]["hierarchy_note"]
                                    for item in records))
                coverage_id = f"hiraoka-suppfig3-{panel}-{slug}-coverage"
                self.assertIn(coverage_id, self.coverage)
                self.assertEqual(self.coverage[coverage_id]["denominator"]["value"], expected_n)
                self.assertEqual(self.coverage[coverage_id]["disposition_completeness"], "partial")

        self.assertEqual(sum(len(value[0]) for value in EXPECTED.values()), 58)
        self.assertEqual(sum(len(value[1]) for value in EXPECTED.values()), 58)
        self.assertEqual(len(self.coverage), 12)
        self.assertIn("one-way anova/tukey", self.audit["caption_qualification"].lower())
        self.assertIn("p-values were not recalculated", self.audit["identity_and_interpretation_limit"])


if __name__ == "__main__":
    unittest.main()
