from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "config" / "observations" / "omecinski_2023_invitro_gas_exchange_candidate.json"


class OmecinskiDeviceConstraintsCycle324Tests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_resistance_keeps_triplicate_test_count_and_unspecified_error_type(self):
        dataset = validate_dataset(self.data)
        record = next(item for item in dataset["observations"]
                      if item["record_id"] == "omecinski2023-preemieox-resistance-summary")
        summary = record["observation"]["summary_statistic"]
        self.assertEqual((summary["estimate"], summary["plus_minus"], summary["plus_minus_type"]),
                         (51, 0, "not_reported"))
        self.assertEqual(summary["reported_sample_size"], 3)
        self.assertIn("performed in triplicate", summary["sample_size_scope"])
        self.assertIn("not biological units", record["independent_unit"]["hierarchy_note"])
        self.assertIn("fluid-resistance apparatus", record["model_system"]["label"])

    def test_priming_volume_has_no_invented_denominator(self):
        dataset = validate_dataset(self.data)
        record = next(item for item in dataset["observations"]
                      if item["record_id"] == "omecinski2023-preemieox-priming-volume")
        self.assertEqual(record["observation"]["value"], 15)
        self.assertEqual(record["observation"]["replicate_role"], "not_reported")
        self.assertNotIn("summary_statistic", record["observation"])
        self.assertIsNone(record["independent_unit"]["id"])

    def test_device_constraints_export_without_fabricated_pairs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "candidate.json"
            source.write_text(json.dumps(self.data), encoding="utf-8")
            bundle = root / "bundle"
            observation_report(source, bundle)
            report = json.loads((bundle / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary_statistics"]["n_reported_plus_minus"], 4)
            self.assertEqual(report["measurement_pairing"]["n_pairs"], 0)
            with (bundle / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 5)
            self.assertTrue(verify_bundle(bundle, strict=True)["bytes_verified"])


if __name__ == "__main__":
    unittest.main()
