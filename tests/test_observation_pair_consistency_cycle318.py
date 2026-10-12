import copy
import json
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.observations import validate_dataset

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/observation_intake_fixture.json"
SCHEMA = ROOT / "schemas/observation-dataset.schema.json"


def same_time_dataset(template):
    data = copy.deepcopy(template)
    first = copy.deepcopy(data["observations"][0])
    second = copy.deepcopy(first)
    first["record_id"] = "same-time-measurement-a"
    second["record_id"] = "same-time-measurement-b"
    second["assay"]["endpoint"] = "synthetic paired endpoint B"
    data["observations"] = [first, second]
    data["transitions"] = []
    data["measurement_pairs"] = [{
        "pair_id": "synthetic-same-time-pair",
        "pair_type": "same_unit_same_time",
        "linkage_basis": "source_explicit",
        "source_artifact_id": first["source"]["artifact_id"],
        "members": [
            {"record_id": first["record_id"], "role": "synthetic endpoint A"},
            {"record_id": second["record_id"], "role": "synthetic endpoint B"},
        ],
        "source_locator": "Synthetic fixture only; no biological source row.",
        "note": "Synthetic contract case for same-unit/time invariants.",
    }]
    return data


class ObservationPairConsistencyCycle318Tests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_matching_unit_and_exact_time_are_required_and_accepted(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        description = schema["properties"]["measurement_pairs"]["items"]["properties"]["pair_type"]["description"]
        self.assertIn("exactly matching non-null measurement time and unit", description)
        validated = validate_dataset(same_time_dataset(self.template))
        self.assertEqual(validated["measurement_pairs"][0]["pair_type"], "same_unit_same_time")

    def test_same_unit_same_time_rejects_different_unit_ids(self):
        data = same_time_dataset(self.template)
        data["observations"][1]["independent_unit"]["id"] = "different-unit"
        with self.assertRaisesRegex(InputError, "shared, reported unit identifier"):
            validate_dataset(data)

    def test_same_unit_same_time_rejects_different_time_or_unit(self):
        for field, value in (("measurement_time", 3), ("measurement_time_unit", "other fixture unit")):
            with self.subTest(field=field):
                data = same_time_dataset(self.template)
                data["observations"][1]["observation"][field] = value
                with self.assertRaisesRegex(InputError, "exact shared reported measurement time and unit"):
                    validate_dataset(data)

    def test_same_unit_same_time_rejects_missing_time(self):
        data = same_time_dataset(self.template)
        data["observations"][1]["observation"].update(
            measurement_time=None, measurement_time_unit="")
        with self.assertRaisesRegex(InputError, "exact shared reported measurement time and unit"):
            validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
