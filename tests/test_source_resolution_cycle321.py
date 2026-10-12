from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "config" / "observations" / "omecinski_2023_invitro_gas_exchange_candidate.json"
SCHEMA = ROOT / "schemas" / "observation-dataset.schema.json"


class SourceResolutionCycle321Tests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_artifact_keeps_access_version_and_reuse_status_distinct(self):
        validated = validate_dataset(copy.deepcopy(self.data))
        resolution = validated["artifacts"][0]["source_resolution"]
        artifact_schema = json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["artifacts"]["items"]
        self.assertIn("source_resolution", artifact_schema["properties"])
        self.assertIn("version identity, full-text access, OA-subset membership, and reuse rights",
                      artifact_schema["properties"]["source_resolution"]["description"])
        self.assertEqual(resolution["version_type"], "author_manuscript")
        self.assertEqual(resolution["access_status"], "full_text_free_to_read")
        self.assertEqual(resolution["oa_subset_status"], "not_included")
        self.assertEqual(resolution["reuse_status"], "not_confirmed")
        self.assertIsNone(resolution["license_expression"])

    def test_intake_report_surfaces_unconfirmed_rights_without_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dataset_path = root / "candidate.json"
            dataset_path.write_text(json.dumps(self.data), encoding="utf-8")
            bundle = root / "bundle"
            observation_report(dataset_path, bundle)
            report = json.loads((bundle / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_review_status"], "candidate")
            self.assertEqual(report["source_resolution"]["n_reuse_unconfirmed"], 1)
            self.assertTrue(any("rights are unconfirmed" in warning for warning in report["warnings"]))
            verification = verify_bundle(bundle, strict=True)
            self.assertTrue(verification["bytes_verified"], verification["errors"])

    def test_license_label_cannot_be_guessed_while_status_is_unconfirmed(self):
        data = copy.deepcopy(self.data)
        data["artifacts"][0]["source_resolution"]["license_expression"] = "CC BY-NC-ND"
        with self.assertRaisesRegex(InputError, "must be null unless an explicit license"):
            validate_dataset(data)

    def test_explicit_license_requires_a_license_expression(self):
        data = copy.deepcopy(self.data)
        data["artifacts"][0]["source_resolution"]["reuse_status"] = "explicit_license"
        with self.assertRaisesRegex(InputError, "source license expression"):
            validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
