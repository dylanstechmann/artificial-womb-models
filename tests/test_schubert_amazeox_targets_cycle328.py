from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset

ROOT = Path(__file__).resolve().parents[1]


class AmazeOxTargetProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.candidate_path = ROOT / "config/observations/schubert_2026_amazeox_target_audited_candidate.json"
        self.inventory_path = ROOT / "config/source_inventories/schubert_2026_amazeox_target_provenance_cycle328.json"
        self.data = json.loads(self.candidate_path.read_text(encoding="utf-8"))
        self.inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))

    def test_table_and_results_targets_remain_separate_while_all_observations_stay_below(self):
        validate_dataset(self.data)
        oxygen = [item for item in self.data["observations"]
                  if item["record_id"].startswith("amazeox-o2-transfer-")]
        self.assertEqual(len(oxygen), 5)
        expected = {55.82, 55.96, 59.04, 59.19}
        for item in oxygen:
            qualifications = item["observation"]["source_qualifications"]
            self.assertEqual({item["reference_value"] for item in qualifications}, expected)
            self.assertTrue(all(item["observation"]["value"] < qualification["reference_value"]
                                for qualification in qualifications))

    def test_reported_target_difference_and_table_rate_arithmetic_are_preserved(self):
        discrepancies = self.inventory["oxygen_target_discrepancy"]
        self.assertEqual([item["absolute_difference_mL_O2_L_blood"] for item in discrepancies],
                         [0.14, 0.15])
        arithmetic = self.inventory["arithmetic_check"]
        self.assertAlmostEqual(arithmetic["table_values_times_mean_UV_flow_mL_O2_min"]["24_week"], 3.717612)
        self.assertAlmostEqual(arithmetic["table_values_times_mean_UV_flow_mL_O2_min"]["28_week"], 6.518016)
        self.assertIn("does not explain", arithmetic["interpretation"])

    def test_target_qualifications_export_without_replacing_observed_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "bundle"
            observation_report(self.candidate_path, bundle)
            report = json.loads((bundle / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_qualifications"]["n_declarations"], 21)
            with (bundle / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = {row["record_id"]: row for row in csv.DictReader(stream)}
            self.assertEqual(float(rows["amazeox-o2-transfer-dc-150"]["value"]), 30.69)
            qualifications = json.loads(rows["amazeox-o2-transfer-dc-150"]["source_qualifications_json"])
            self.assertEqual({item["reference_value"] for item in qualifications}, {55.82, 55.96, 59.04, 59.19})


if __name__ == "__main__":
    unittest.main()
