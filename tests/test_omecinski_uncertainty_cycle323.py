from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "config" / "observations" / "omecinski_2023_invitro_gas_exchange_candidate.json"
SCHEMA = ROOT / "schemas" / "developmental-observation.schema.json"


class OmecinskiUncertaintyCycle323Tests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_source_neutral_plus_minus_records_validate_and_keep_unknown_types(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        summary_schema = schema["properties"]["observation"]["properties"]["summary_statistic"]
        self.assertIn("reported_plus_minus", summary_schema["properties"]["kind"]["enum"])
        validated = validate_dataset(copy.deepcopy(self.data))
        summaries = [item["observation"]["summary_statistic"] for item in validated["observations"]
                     if "summary_statistic" in item["observation"]]
        self.assertEqual([item["kind"] for item in summaries], ["reported_plus_minus"] * 4)
        self.assertTrue(all(item["plus_minus_type"] == "not_reported" for item in summaries))

    def test_saturation_does_not_inherit_n_from_the_other_summaries(self):
        validated = validate_dataset(copy.deepcopy(self.data))
        saturation = next(item for item in validated["observations"]
                          if item["record_id"] == "omecinski2023-preemieox-oxygen-saturation-summary")
        summary = saturation["observation"]["summary_statistic"]
        self.assertEqual((summary["estimate"], summary["plus_minus"]), (99.4, 0.4))
        self.assertIsNone(summary["reported_sample_size"])
        self.assertIn("does not state the denominator", summary["sample_size_scope"])
        self.assertIsNone(saturation["independent_unit"]["id"])
        self.assertEqual(validated["measurement_pairs"], [])

    def test_report_exports_all_three_unpaired_summaries_and_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
            saturation = next(row for row in rows if row["record_id"] == "omecinski2023-preemieox-oxygen-saturation-summary")
            self.assertEqual(json.loads(saturation["summary_statistic_json"])["reported_sample_size"], None)
            self.assertTrue(verify_bundle(bundle, strict=True)["bytes_verified"])

    def test_source_neutral_summary_rejects_negative_quantity_and_mismatched_estimate(self):
        cases = [
            ({"plus_minus": -0.1}, "cannot be negative"),
            ({"estimate": 99.5}, "must equal its reported estimate"),
            ({"plus_minus_type": "guess"}, "Unknown plus-minus type"),
        ]
        for change, message in cases:
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                summary = data["observations"][2]["observation"]["summary_statistic"]
                summary.update(change)
                with self.assertRaisesRegex(InputError, message):
                    validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
