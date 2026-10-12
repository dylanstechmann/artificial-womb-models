import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


RATIO_FORMULAS = {
    ("9A", "30-percent-ksr"): ["=15/15", "=13/14", "=14/15"],
    ("9A", "20-percent-fbs-no-hi"): ["=4/4", "=7/7", "=14/15", "=6/6", "=8/15", "=8/14", "=10/14"],
    ("9A", "20-percent-fbs-hi"): ["=2/6", "=3/6", "=5/6"],
    ("9A", "30-percent-fbs-no-hi"): ["=1/9", "=6/11", "=4/11"],
    ("9A", "30-percent-fbs-hi"): ["=6/13", "=3/19", "=6/21"],
    ("9B", "30-percent-ksr"): ["=13/15", "=12/14", "=12/15"],
    ("9B", "20-percent-fbs-no-hi"): ["=8/15", "=3/15", "=3/14"],
    ("9B", "20-percent-fbs-hi"): ["=0/6", "=1/6", "=2/6"],
    ("9B", "30-percent-fbs-no-hi"): ["=0/9", "=2/11", "=2/11"],
    ("9B", "30-percent-fbs-hi"): ["=0/13", "=2/19", "=0/21"],
    ("9C", "30-percent-ksr"): ["=14/15", "=6/6", "=11/12"],
    ("9C", "20-percent-fbs-no-hi-second-lot"): ["=8/9", "=13/15", "=11/12", "=8/12"],
    ("9D", "30-percent-ksr"): ["=12/15", "=5/6", "=11/12"],
    ("9D", "20-percent-fbs-no-hi-second-lot"): ["=7/9", "=2/15", "=3/12", "=4/12"],
    ("9I", "fbs-egfp-aav"): ["=9/12", "=13/15", "=8/10"],
    ("9I", "fbs-myrakt1-aav"): ["=16/18", "=11/15", "=13/14"],
    ("9J", "fbs-egfp-aav"): ["=2/12", "=4/15", "=3/10"],
    ("9J", "fbs-myrakt1-aav"): ["=5/18", "=5/15", "=3/14"],
}


class HiraokaSupplementaryFig9SourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["suppfig9_source_data"]
        self.records = [item for item in self.dataset["observations"]
                        if item["record_id"].startswith("hiraoka-suppfig9-")]
        self.coverage = {item["coverage_id"]: item for item in self.dataset["cohort_coverage"]
                         if item["coverage_id"].startswith("hiraoka-suppfig9-")}

    def test_moesm20_hash_and_all_populated_sheets_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-suppfig9-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-suppfig9.xlsx"))
        expected_hash = "cef46750fe037ce8dbd1776835b5b8b9a7b48d5e56df16f4bea17dbf438f02ae"
        self.assertEqual(source["sha256"], expected_hash)
        self.assertEqual(snapshot["sha256"], expected_hash)
        self.assertEqual(snapshot["bytes"], 19976)
        self.assertEqual(self.audit["curated_sheets"], ["9A", "9B", "9C", "9D", "9G", "9I", "9J", "9K"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(self.audit["source_observation_rows"], 80)
        self.assertEqual(len(self.records), 80)
        self.assertEqual(len(self.coverage), 22)

    def test_ratio_formulas_are_exact_and_exp_labels_remain_unlinked(self):
        audits = {(item["panel"], item["condition_slug"]): item
                  for item in self.audit["recipient_ratio_groups"]}
        for key, formulas in RATIO_FORMULAS.items():
            with self.subTest(panel=key[0], condition=key[1]):
                panel, slug = key
                audit = audits[key]
                self.assertEqual(audit["source_formulas"], formulas)
                letter = panel[-1].lower()
                records = [item for item in self.records
                           if item["record_id"].startswith(f"hiraoka-suppfig9-{letter}-{slug}-")]
                records.sort(key=lambda item: int(item["record_id"].rsplit("exp", 1)[1]))
                observed = [re.search(r"publisher formula (=\d+/\d+)",
                                      item["assay"]["functional_context"]["quantity_basis"]).group(1)
                            for item in records]
                self.assertEqual(observed, formulas)
                self.assertTrue(all(item["independent_unit"]["kind"] == "pregnant_animal"
                                    and item["independent_unit"]["id"] is None
                                    and item["independent_unit"]["parent_id"] is None
                                    for item in records))
                self.assertTrue(all("not establish identity" in item["independent_unit"]["hierarchy_note"]
                                    for item in records))
                self.assertIn(f"hiraoka-suppfig9-{letter}-{slug}-coverage", self.coverage)

    def test_caption_workbook_mismatch_and_bioassay_source_qualifications_are_preserved(self):
        mismatch = self.audit["caption_workbook_n_mismatch"]
        self.assertIn("n=3 vs4", mismatch)
        self.assertIn("three numeric formula rows in each group", mismatch)
        self.assertIn("No fourth value or identity was located", mismatch)
        for panel in ("i", "j"):
            coverage = self.coverage[f"hiraoka-suppfig9-{panel}-fbs-myrakt1-aav-coverage"]
            self.assertEqual(coverage["denominator"]["value"], 4)
            self.assertIn("only three formula rows", coverage["population_frame"])
            records = [item for item in self.records
                       if item["record_id"].startswith(f"hiraoka-suppfig9-{panel}-fbs-myrakt1-aav-")]
            self.assertEqual(len(records), 3)
            self.assertTrue(all("fourth value" in item["limitations"][0] for item in records))

        self.assertIn("no count or identity", self.audit["panel_9b_exclusion_note"])
        panel_b_records = [item for item in self.records if item["record_id"].startswith("hiraoka-suppfig9-b-")]
        self.assertTrue(all(any("histology-fixed attached embryos" in text for text in item["limitations"])
                            for item in panel_b_records))
        self.assertEqual(self.audit["statistical_annotations"]["panel_9K"],
                         "Two-tailed unpaired Student t-test; article Results report P=0.0906; no p-value recalculated.")

    def test_normalized_cox2_and_invasion_values_keep_their_source_scales(self):
        expected_normalized = {
            "30-percent-ksr": [1.7852165061467387, 0.4774097564795239, 0.7432464176650223,
                                2.1042204995693368, 0.4796022237882703, 0.8084723201002271, 0.6018322762508809],
            "20-percent-fbs-no-hi": [0.06358155195364498, 0.10907524861013233, 0.014799154334038054,
                                     0.010414219716545298],
        }
        cox_audits = {item["condition_slug"]: item for item in self.audit["cox2_area_groups"]}
        raw_pairs = self.audit["cox2_raw_scale_pairs"]
        self.assertEqual(len(raw_pairs), 11)
        self.assertEqual(self.audit["source_observation_rows"], 80)
        for slug, values in expected_normalized.items():
            records = [item for item in self.records
                       if item["record_id"].startswith(f"hiraoka-suppfig9-g-{slug}-")]
            records.sort(key=lambda item: int(item["record_id"].rsplit("embryo", 1)[1]))
            self.assertEqual([item["observation"]["value"] for item in records], values)
            self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                and item["independent_unit"]["id"] is None for item in records))
            self.assertEqual(cox_audits[slug]["normalized_source_values"], values)
        self.assertIn("not counted as additional biological observations", self.audit["cox2_raw_scale_note"])

        expected_k = {"fbs-egfp-aav": [0.043258701171875, 0.72394296875, 1.39113, 0.65590296875],
                      "fbs-myrakt1-aav": [1.06995, 2.31882, 1.05804, 3.63967, 1.39951]}
        k_audits = {item["condition_slug"]: item for item in self.audit["invasion_volume_groups"]}
        for slug, values in expected_k.items():
            records = [item for item in self.records
                       if item["record_id"].startswith(f"hiraoka-suppfig9-k-{slug}-")]
            records.sort(key=lambda item: int(item["record_id"].rsplit("embryo", 1)[1]))
            self.assertEqual([item["observation"]["value"] for item in records], values)
            self.assertTrue(all(item["assay"]["unit"] == "1E+05μm^3" for item in records))
            self.assertTrue(all(item["observation"]["measurement_time"] == "unreported" for item in records))
            self.assertEqual(k_audits[slug]["source_values"], values)


if __name__ == "__main__":
    unittest.main()
