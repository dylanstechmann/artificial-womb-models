import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.exchange import simulate
from wombmodels.identifiability import analyze

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/exchange_fixture.json").read_text())


class IdentifiabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = fixture()
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.simulation = self.root / "simulation"
        simulate(self.config_path, self.simulation)

    def test_report_uses_scheduled_readings_and_keeps_biological_scope_false(self):
        output = self.root / "analysis"
        analyze(self.config_path, self.simulation / "trajectory.csv", output)
        report = json.loads((output / "observability_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["n_scheduled_readings"], 49)
        self.assertEqual(report["observation_contract"].split(";")[0],
                         "Only scheduled sensor readings, the receipt-bound fixture configuration, and its modeled power-source event schedule are used")
        forecast = report["noise_aware_state_model"]["prospective_forecast"]
        self.assertTrue(forecast["estimable"])
        self.assertGreater(forecast["n_training_readings"], 4)
        self.assertGreater(forecast["n_scored_readings"], 0)
        self.assertIsNotNone(forecast["baseline_last_observation_rmse"])
        self.assertEqual(report["schema_version"], 2)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        self.assertIn("trajectory_sha256", json.loads((output / "source_manifest.json").read_text()))
        self.assertIn("simulation_receipt_sha256", json.loads((output / "source_manifest.json").read_text()))

    def test_trajectory_from_a_different_sampling_schedule_is_rejected(self):
        mismatched = fixture()
        mismatched["dimensionless_time"]["output_step"] = 0.3
        mismatched_path = self.root / "mismatched.json"
        mismatched_path.write_text(json.dumps(mismatched), encoding="utf-8")
        with self.assertRaisesRegex(InputError, "cadence"):
            analyze(mismatched_path, self.simulation / "trajectory.csv", self.root / "rejected")
        self.assertFalse((self.root / "rejected").exists())

    def test_future_readings_score_the_forecast_but_do_not_change_training_fit(self):
        original_output = self.root / "original-analysis"
        original = analyze(self.config_path, self.simulation / "trajectory.csv", original_output)
        original_report = json.loads((original_output / "observability_report.json").read_text())
        trajectory_path = self.simulation / "trajectory.csv"
        with trajectory_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        split = self.config["dimensionless_time"]["duration"] * 0.7
        changed = 0
        for row in rows:
            if row["sensor_sampled"] == "True" and row["sensor_reading"] and float(row["dimensionless_time"]) > split:
                row["sensor_reading"] = str(float(row["sensor_reading"]) + 25.0)
                changed += 1
        self.assertGreater(changed, 0)
        with trajectory_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        trajectory_bytes = trajectory_path.read_bytes()
        receipt_path = self.simulation / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["outputs"]["trajectory.csv"] = {
            "sha256": hashlib.sha256(trajectory_bytes).hexdigest(),
            "size_bytes": len(trajectory_bytes),
        }
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        changed_output = self.root / "changed-analysis"
        analyze(self.config_path, trajectory_path, changed_output)
        changed_report = json.loads((changed_output / "observability_report.json").read_text())
        original_forecast = original_report["noise_aware_state_model"]["prospective_forecast"]
        changed_forecast = changed_report["noise_aware_state_model"]["prospective_forecast"]
        self.assertEqual(original_forecast["state_fit"]["parameters"],
                         changed_forecast["state_fit"]["parameters"])
        self.assertNotEqual(original_forecast["fixture_scale_rmse"], changed_forecast["fixture_scale_rmse"])

    def test_missing_scheduled_reading_is_rejected_even_with_a_fresh_receipt_hash(self):
        trajectory_path = self.simulation / "trajectory.csv"
        with trajectory_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        removed = False
        retained = []
        for row in rows:
            if not removed and row["sensor_sampled"] == "True" and row["dimensionless_time"] == "0.25":
                removed = True
                continue
            retained.append(row)
        self.assertTrue(removed)
        with trajectory_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(retained)
        raw = trajectory_path.read_bytes()
        receipt_path = self.simulation / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["outputs"]["trajectory.csv"] = {"sha256": hashlib.sha256(raw).hexdigest(),
                                                   "size_bytes": len(raw)}
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(InputError, "scheduled sensor timestamps"):
            analyze(self.config_path, trajectory_path, self.root / "missing-reading")
        self.assertFalse((self.root / "missing-reading").exists())


if __name__ == "__main__":
    unittest.main()
