from __future__ import annotations

import csv
import copy
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.observations import observation_report, validate_dataset

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "observation_intake_fixture.json"


class MeasurementConditionIntakeTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_source_linked_conditions_export_and_partition_exact_groups(self):
        first = self.data["observations"][0]
        first["observation"]["measurement_conditions"] = [{
            "name": "blood_flow_rate", "value": 50, "unit": "mL/min",
            "source_locator": "Methods > operating point 1",
        }]
        second = copy.deepcopy(first)
        second["record_id"] = "synthetic-flow-100"
        second["observation"]["measurement_conditions"][0]["value"] = 100
        second["observation"]["measurement_conditions"][0]["source_locator"] = (
            "Methods > operating point 2")
        self.data["observations"] = [first, second]
        self.data["transitions"] = []
        self.data["measurement_pairs"] = []

        validate_dataset(self.data)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "dataset.json"
            source.write_text(json.dumps(self.data), encoding="utf-8")
            bundle = Path(temporary) / "bundle"
            observation_report(source, bundle)
            report = json.loads((bundle / "observation_intake_report.json").read_text())
            self.assertEqual(report["measurement_conditions"], {
                "n_records_with_conditions": 2,
                "n_condition_declarations": 2,
                "interpretation": "source-linked test context; conditions do not establish replicates or measurement pairs",
            })
            with (bundle / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(json.loads(rows[0]["measurement_conditions_json"]),
                             first["observation"]["measurement_conditions"])
            with (bundle / "interval_groups.csv").open(newline="", encoding="utf-8") as stream:
                groups = list(csv.DictReader(stream))
            self.assertEqual(len(groups), 2)
            self.assertNotEqual(groups[0]["measurement_conditions_json"],
                                groups[1]["measurement_conditions_json"])

    def test_conditions_reject_duplicate_names_and_boolean_values(self):
        for conditions, message in (
            ([{"name": "mode", "value": "SC", "unit": "", "source_locator": "Methods"},
              {"name": "mode", "value": "DC", "unit": "", "source_locator": "Methods"}],
             "names must be unique"),
            ([{"name": "blood_flow", "value": True, "unit": "mL/min", "source_locator": "Methods"}],
             "finite numeric or reported text"),
        ):
            with self.subTest(conditions=conditions):
                data = copy.deepcopy(self.data)
                data["observations"][0]["observation"]["measurement_conditions"] = conditions
                with self.assertRaisesRegex(InputError, message):
                    validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
