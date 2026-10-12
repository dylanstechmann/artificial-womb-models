import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaFigure7HISourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["fig7_hi_source_data"]
        self.observations = [
            item for item in self.dataset["observations"]
            if item["source"]["artifact_id"] == "hiraoka2025-fig7-source-data"
        ]
        self.coverage = [
            item for item in self.dataset["cohort_coverage"]
            if item["source_artifact_id"] == "hiraoka2025-fig7-source-data"
        ]

    def test_moesm16_hash_and_panel_scope_are_pinned(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-fig7-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-fig7.xlsx"))
        expected_hash = "7f72cc20ca652dcdcfe7c2e894b350ac0c0309893cabe38ef1ac3c1d8ba2b2fb"
        self.assertEqual(source["sha256"], expected_hash)
        self.assertEqual(snapshot["sha256"], expected_hash)
        self.assertEqual(snapshot["bytes"], 17722)
        self.assertEqual(self.audit["curated_sheets"], ["7B", "7C", "7E", "7H", "7I"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(len(self.observations), 197)
        self.assertEqual(len(self.coverage), 15)

    def test_panel_h_retains_recipient_counts_without_mouse_identity(self):
        expected = {
            "vehicle-egfp": [15, 14, 13, 15],
            "celecoxib-egfp": [1, 8, 7, 0, 0, 0],
            "celecoxib-myr-akt1": [1, 3, 7, 14, 12, 9, 0],
        }
        for slug, counts in expected.items():
            records = [item for item in self.observations
                       if item["record_id"].startswith(f"hiraoka-fig7-h-{slug}-")]
            self.assertEqual([item["observation"]["value"] for item in records], counts)
            self.assertTrue(all(item["independent_unit"]["kind"] == "pregnant_animal"
                                and item["independent_unit"]["id"] is None
                                for item in records))
            self.assertTrue(all("not divided by 16" in item["assay"]["functional_context"]["quantity_basis"]
                                for item in records))

    def test_panel_i_site_weights_reconcile_only_at_group_total(self):
        expected = {
            "vehicle-egfp": (57, 5.41, 18.45, 13.402105),
            "celecoxib-egfp": (16, 4.43, 6.56, 5.26625),
            "celecoxib-myr-akt1": (46, 5.02, 13.11, 10.22),
        }
        for slug, (count, minimum, maximum, mean) in expected.items():
            records = [item for item in self.observations
                       if item["record_id"].startswith(f"hiraoka-fig7-i-{slug}-")]
            self.assertEqual(len(records), count)
            self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                and item["independent_unit"]["id"] is None
                                and item["independent_unit"]["parent_id"] is None
                                for item in records))
            self.assertTrue(all(item["observation"]["measurement_time"] == "dpc 5.5"
                                for item in records))
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(min(values), minimum)
            self.assertAlmostEqual(max(values), maximum)
            self.assertAlmostEqual(sum(values) / len(values), mean, places=5)

        reconciliations = self.audit["group_level_reconciliation"]
        self.assertEqual([item["sum_implantation_sites"] for item in
                          self.audit["panel_H_recipient_mouse_groups"]], [57, 16, 46])
        self.assertEqual([item["site_weight_rows"] for item in reconciliations], [57, 16, 46])
        self.assertTrue(all(item["group_total_matches"] for item in reconciliations))
        self.assertTrue(all(item["identity_linkage"] ==
                            "group-level count agreement only; no site-to-mouse crosswalk"
                            for item in reconciliations))
        self.assertIn("no individual site-to-mouse crosswalk",
                      self.audit["identity_and_interpretation_limit"])


if __name__ == "__main__":
    unittest.main()
