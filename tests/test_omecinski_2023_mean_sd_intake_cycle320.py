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
CANDIDATE = ROOT / "config/observations/omecinski_2023_invitro_gas_exchange_candidate.json"
SCHEMA = ROOT / "schemas/developmental-observation.schema.json"


class OmecinskiDistributionIntakeCycle320Tests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_candidate_preserves_undefined_plus_minus_type_and_remains_a_group_summary(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        summary_schema = schema["properties"]["observation"]["properties"]["summary_statistic"]
        self.assertIn("mean_sd", summary_schema["properties"]["kind"]["enum"])
        validated = validate_dataset(copy.deepcopy(self.dataset))
        observation = validated["observations"][0]
        self.assertEqual(observation["observation"]["replicate_role"], "summary_only")
        summary = observation["observation"]["summary_statistic"]
        self.assertEqual(summary["kind"], "reported_plus_minus")
        self.assertEqual((summary["estimate"], summary["plus_minus"], summary["plus_minus_type"]),
                         (12.7, 0.9, "not_reported"))
        self.assertEqual(observation["observation"]["summary_statistic"]["reported_sample_size"], 9)
        self.assertIn("not an asserted biological n",
                      observation["observation"]["summary_statistic"]["sample_size_scope"])
        self.assertIsNone(observation["independent_unit"]["id"])

    def test_validator_exporter_and_receipt_preserve_source_neutral_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "candidate.json"
            source.write_text(json.dumps(self.dataset), encoding="utf-8")
            output = Path(directory) / "intake"
            observation_report(source, output)
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_review_status"], "candidate")
            self.assertEqual(report["summary_statistics"]["n_records"], 4)
            self.assertEqual(report["summary_statistics"]["n_mean_sd"], 0)
            self.assertEqual(report["summary_statistics"]["n_reported_plus_minus"], 4)
            self.assertEqual(report["summary_statistics"]["n_median_iqr"], 0)
            self.assertEqual(report["measurement_pairing"]["n_pairs"], 0)
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]["value"], "12.7")
            summary = json.loads(rows[0]["summary_statistic_json"])
            self.assertEqual(summary["plus_minus"], 0.9)
            self.assertEqual(summary["plus_minus_type"], "not_reported")
            self.assertEqual(summary["source_literal"], "12.7 ± 0.9 mL/min")
            result = verify_bundle(output, strict=True)
            self.assertTrue(result["bytes_verified"], result["errors"])
            self.assertEqual(result["scientific_review"], "not_established_by_this_tool")

    def test_mean_sd_contract_remains_available_and_rejects_invalid_shapes(self):
        cases = [
            ({"standard_deviation": -0.1}, "cannot be negative"),
            ({"mean": 13.0}, "must equal its reported mean"),
            ({"lower_quartile": 12.0}, "exactly its documented fields"),
        ]
        for change, message in cases:
            with self.subTest(change=change):
                data = copy.deepcopy(self.dataset)
                summary = data["observations"][0]["observation"]["summary_statistic"]
                summary.clear()
                summary.update({
                    "kind": "mean_sd", "mean": 12.7, "standard_deviation": 0.9,
                    "reported_sample_size": 9,
                    "sample_size_scope": "Synthetic source contract only.",
                    "sample_size_source_locator": "Synthetic fixture.",
                    "source_literal": "12.7 ± 0.9",
                })
                summary.update(change)
                with self.assertRaisesRegex(InputError, message):
                    validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
