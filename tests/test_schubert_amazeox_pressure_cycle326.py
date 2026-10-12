from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset

ROOT = Path(__file__).resolve().parents[1]


class AmazeOxPressureIntakeTests(unittest.TestCase):
    def setUp(self):
        self.candidate_path = ROOT / "config/observations/schubert_2026_amazeox_transfer_hydraulics_candidate.json"
        self.inventory_path = ROOT / "config/source_inventories/schubert_2026_amazeox_transfer_hydraulics.json"
        self.data = json.loads(self.candidate_path.read_text(encoding="utf-8"))
        self.inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))

    def test_pressure_records_preserve_mode_flow_and_threshold_qualification(self):
        validated = validate_dataset(self.data)
        records = {item["record_id"]: item for item in validated["observations"]}
        measured = records["amazeox-pressure-drop-dc-50"]
        self.assertEqual(measured["observation"]["value"], 14.9)
        self.assertEqual(measured["observation"]["measurement_conditions"], [
            {"name": "operating_mode", "value": "DC", "unit": "",
             "source_locator": "Methods > Experimental setup; pressure measured in dual-compartment mode"},
            {"name": "blood_flow_rate", "value": 50, "unit": "mL/min",
             "source_locator": "Results > Pressure loss"},
        ])
        exceedance = records["amazeox-pressure-limit-exceeded-dc-90"]
        self.assertEqual(exceedance["observation"]["value"], 90)
        self.assertEqual(exceedance["observation"]["source_qualifications"][0]["reference_value"], 20)
        self.assertEqual(exceedance["observation"]["source_qualifications"][0]["status_code"],
                         "criterion_exceeded")

    def test_unit_ambiguity_is_retained_without_inventing_a_190_flow_record(self):
        records = self.data["observations"]
        self.assertEqual(len(records), 7)
        self.assertFalse(any(item["record_id"].endswith("190") or
                             item["observation"]["value"] == 45.4 for item in records))
        ambiguity = self.inventory["pressure_test_scope"]["source_text_unit_mismatch"]
        self.assertEqual(ambiguity["reported_condition_literal"], "at 190 mmHg")
        self.assertEqual(ambiguity["methods_flow_range"], "50 to 190 mL/min in 10 mL/min increments")
        self.assertFalse(ambiguity["candidate_record_created"])

    def test_pressure_context_survives_observation_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "bundle"
            observation_report(self.candidate_path, bundle)
            with (bundle / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = {row["record_id"]: row for row in csv.DictReader(stream)}
            self.assertEqual(len(rows), 7)
            self.assertEqual(json.loads(rows["amazeox-pressure-drop-dc-50"]["measurement_conditions_json"])[1]["value"], 50)
            qualification = json.loads(rows["amazeox-pressure-limit-exceeded-dc-90"]["source_qualifications_json"])
            self.assertEqual(qualification[0]["reference_unit"], "mmHg")


if __name__ == "__main__":
    unittest.main()
