import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.observations import observation_report, validate_dataset

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/observation_intake_fixture.json"
SCHEMA = ROOT / "schemas/observation-dataset.schema.json"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"


def fixture_pair(dataset):
    first, second = dataset["observations"][:2]
    return {
        "pair_id": "fixture-interface-pair",
        "pair_type": "interface_sides",
        "linkage_basis": "source_explicit",
        "source_artifact_id": first["source"]["artifact_id"],
        "members": [
            {"record_id": first["record_id"], "role": "source-labeled side A"},
            {"record_id": second["record_id"], "role": "source-labeled side B"},
        ],
        "source_locator": "Synthetic fixture only; no biological source row.",
        "note": "Synthetic contract case for reference validation and export.",
    }


class ObservationMeasurementPairsCycle317Tests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_schema_and_runtime_accept_explicit_source_linked_pairs(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        pair_schema = schema["properties"]["measurement_pairs"]
        self.assertEqual(pair_schema["maxItems"], 5000)
        self.assertIn("matching group labels, timestamps, or values do not create pairs",
                      pair_schema["description"])
        data = copy.deepcopy(self.dataset)
        data["measurement_pairs"] = [fixture_pair(data)]
        validated = validate_dataset(data)
        self.assertEqual(len(validated["measurement_pairs"]), 1)

    def test_pair_export_preserves_record_members_roles_and_locator(self):
        data = copy.deepcopy(self.dataset)
        pair = fixture_pair(data)
        data["measurement_pairs"] = [pair]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "dataset.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            output = Path(directory) / "intake"
            observation_report(source, output)
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["measurement_pairing"]["n_pairs"], 1)
            self.assertEqual(report["measurement_pairing"]["n_members"], 2)
            with (output / "measurement_pairs.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["record_ids"], ";".join(
                member["record_id"] for member in pair["members"]))
            self.assertEqual(json.loads(rows[0]["member_roles"]),
                             [member["role"] for member in pair["members"]])
            self.assertEqual(rows[0]["source_locator"], pair["source_locator"])

    def test_pair_rejects_unknown_records_duplicate_members_and_wrong_artifact(self):
        data = copy.deepcopy(self.dataset)
        pair = fixture_pair(data)
        pair["members"][1]["record_id"] = "missing-record"
        data["measurement_pairs"] = [pair]
        with self.assertRaisesRegex(InputError, "unknown observation record"):
            validate_dataset(data)

        data = copy.deepcopy(self.dataset)
        pair = fixture_pair(data)
        pair["members"][1]["record_id"] = pair["members"][0]["record_id"]
        data["measurement_pairs"] = [pair]
        with self.assertRaisesRegex(InputError, "distinct valid record IDs"):
            validate_dataset(data)

        data = copy.deepcopy(self.dataset)
        pair = fixture_pair(data)
        pair["source_artifact_id"] = "missing-artifact"
        data["measurement_pairs"] = [pair]
        with self.assertRaisesRegex(InputError, "unknown source artifact"):
            validate_dataset(data)

    def test_omitted_pairs_remain_empty(self):
        data = copy.deepcopy(self.dataset)
        validated = validate_dataset(data)
        self.assertEqual(validated["measurement_pairs"], [])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "dataset.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            output = Path(directory) / "intake"
            observation_report(source, output)
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["measurement_pairing"]["n_pairs"], 0)
            with (output / "measurement_pairs.csv").open(newline="", encoding="utf-8") as stream:
                self.assertEqual(list(csv.DictReader(stream)), [])

    def test_eixarch_candidate_remains_unpaired_and_byte_unchanged(self):
        expected_sha256 = "4174517e06e55ac6ab9c27e2ecbd8346510552c2184e52022fa476717e948159"
        raw = CANDIDATE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_sha256)
        data = json.loads(raw)
        validated = validate_dataset(copy.deepcopy(data))
        self.assertEqual(validated["measurement_pairs"], [])
        self.assertEqual(len(validated["observations"]), 50)
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), expected_sha256)


if __name__ == "__main__":
    unittest.main()
