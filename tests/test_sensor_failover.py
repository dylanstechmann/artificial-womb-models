import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.exchange import NOTICE
from wombmodels.sensor_failover import sensor_failover
from wombmodels.whole_path_twin import whole_path_twin

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/sensor_failover_fixture.json").read_text(encoding="utf-8"))


class SensorFailoverTests(unittest.TestCase):
    def run_model(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = sensor_failover(path, output)
        report = json.loads((output / "sensor_failover_report.json").read_text(encoding="utf-8"))
        return receipt, report, output

    def test_declared_faults_trigger_confirmation_and_latched_fallback(self):
        _receipt, report, output = self.run_model(fixture())
        self.assertEqual(len(report["comparisons"]), 3)
        for comparison in report["comparisons"]:
            self.assertEqual(comparison["fault_samples"], 10)
            self.assertEqual(comparison["detected_fault_samples"], 8)
            self.assertEqual(comparison["undetected_fault_samples"], 2)
            self.assertEqual(comparison["false_alarm_samples"], 0)
            self.assertEqual(comparison["first_detection_time"], 4.5)
            self.assertTrue(comparison["fallback_ever_active"])
            self.assertGreater(comparison["max_absolute_bulk_difference"], 0)
        with (output / "sensor_observations.csv").open(newline="", encoding="utf-8") as stream:
            rows = [row for row in csv.DictReader(stream)
                    if row["variant"] == "living_interface"
                    and row["mode"] == "independent_sensor_freeze"]
        at_start = next(row for row in rows if float(row["dimensionless_time"]) == 4.0)
        self.assertEqual(at_start["disagreement_count"], "1")
        self.assertEqual(at_start["fault_detected"], "False")
        self.assertEqual(at_start["fallback_active"], "False")
        after_end = next(row for row in rows if float(row["dimensionless_time"]) == 8.0)
        self.assertEqual(after_end["declared_fault"], "")
        self.assertEqual(after_end["fallback_active"], "True")
        dropout = next(row for row in rows if float(row["dimensionless_time"]) == 16.0)
        self.assertEqual(dropout["primary_available"], "False")
        self.assertEqual(dropout["primary_reading"], "")
        self.assertEqual(dropout["absolute_residual"], "")
        self.assertFalse(report["sensor_contract"]["internal_tissue_observed_by_fallback"])

    def test_no_fault_single_sensor_is_exactly_the_canonical_twin(self):
        config = fixture()
        config["sensor_experiment"]["control_faults"] = []
        _receipt, report, output = self.run_model(config)
        self.assertTrue(report["no_fault_canonical_trajectories_match"])
        self.assertTrue(all(row["false_alarm_samples"] == 0 for row in report["comparisons"]))
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            canonical_config = {key: value for key, value in config.items() if key != "sensor_experiment"}
            path = base / "canonical.json"
            path.write_text(json.dumps(canonical_config), encoding="utf-8")
            whole_path_twin(path, base / "canonical")
            for name in config["variants"]:
                with (base / "canonical" / f"trajectory_{name}.csv").open(newline="") as stream:
                    expected = list(csv.DictReader(stream))
                with (output / f"trajectory_single_sensor_{name}.csv").open(newline="") as stream:
                    actual = list(csv.DictReader(stream))
                for actual_row, expected_row in zip(actual, expected):
                    for column in expected_row:
                        self.assertEqual(actual_row[column], expected_row[column], column)
                self.assertTrue(all(row["fallback_active"] == "False" for row in actual))

    def test_secondary_sensor_does_not_change_unfaulted_primary_path(self):
        config = fixture()
        config["sensor_experiment"]["control_faults"] = []
        config["sensor_experiment"]["disagreement_threshold"] = 1e-9
        config["sensor_experiment"]["confirmation_samples"] = 1
        _receipt, report, output = self.run_model(config)
        self.assertTrue(report["no_fault_canonical_trajectories_match"])
        self.assertTrue(all(row["fallback_ever_active"] for row in report["comparisons"]))
        self.assertTrue(all(row["false_alarm_samples"] > 0 for row in report["comparisons"]))
        with (output / "sensor_observations.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        primary = next(row for row in rows if row["mode"] == "single_sensor"
                       and row["variant"] == "living_interface"
                       and float(row["dimensionless_time"]) == 0.0)
        redundant = next(row for row in rows if row["mode"] == "independent_sensor_freeze"
                         and row["variant"] == "living_interface"
                         and float(row["dimensionless_time"]) == 0.0)
        self.assertEqual(primary["primary_reading"], redundant["primary_reading"])
        self.assertNotEqual(primary["secondary_reading"], redundant["primary_reading"])

    def test_modes_share_sensor_noise_and_pre_fallback_readings(self):
        _receipt, _report, output = self.run_model(fixture())
        with (output / "sensor_observations.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        for name in fixture()["variants"]:
            single = [row for row in rows if row["variant"] == name
                      and row["mode"] == "single_sensor"]
            redundant = [row for row in rows if row["variant"] == name
                         and row["mode"] == "independent_sensor_freeze"]
            for left, right in zip(single, redundant):
                for column in ("dimensionless_time", "declared_fault", "primary_available",
                               "primary_noise", "secondary_noise"):
                    self.assertEqual(left[column], right[column], (name, column))
                if float(left["dimensionless_time"]) <= 4.5:
                    for column in ("primary_reading", "secondary_reading", "absolute_residual"):
                        self.assertEqual(left[column], right[column], (name, column))

    def test_freeze_holds_supplement_not_internal_state(self):
        _receipt, _report, output = self.run_model(fixture())
        with (output / "trajectory_independent_sensor_freeze_living_interface.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        fallback = [row for row in rows if row["fallback_active"] == "True"]
        supplements = {row["supplement"] for row in fallback}
        self.assertEqual(len(supplements), 1)
        self.assertNotEqual(fallback[0]["cumulative_unserved"], fallback[-1]["cumulative_unserved"])
        self.assertNotEqual(fallback[0]["progression"], fallback[-1]["progression"])

    def test_deterministic_and_strictly_verified_publication(self):
        receipt, _report, first = self.run_model(fixture())
        _receipt, _report, second = self.run_model(fixture())
        self.assertEqual(receipt["bundle_kind"], "dimensionless_sensor_failover")
        self.assertEqual(receipt["metadata"]["n_modes"], 2)
        for path in first.iterdir():
            if path.name != "receipt.json":
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes(), path.name)
        checked = verify_bundle(first, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertIn("sensor-failover-model", checked["rerun_command"])
        self.assertIn(NOTICE, (first / "REPORT.md").read_text(encoding="utf-8"))

    def test_rejects_malformed_experiment_configuration(self):
        mutations = (
            (lambda c: c.pop("sensor_experiment"), "sensor_experiment"),
            (lambda c: c["sensor_experiment"].update(extra=1), "sensor_experiment"),
            (lambda c: c["sensor_experiment"].update(disagreement_threshold=0), "disagreement_threshold"),
            (lambda c: c["sensor_experiment"].update(disagreement_threshold=True), "disagreement_threshold"),
            (lambda c: c["sensor_experiment"].update(confirmation_samples=0), "confirmation_samples"),
            (lambda c: c["sensor_experiment"].update(confirmation_samples=1.5), "confirmation_samples"),
            (lambda c: c["sensor_experiment"]["control_faults"].__setitem__(
                0, {"start": 4.1, "end": 7, "kind": "bias", "magnitude": 0.5}), "output grid"),
            (lambda c: c["sensor_experiment"]["control_faults"].__setitem__(
                1, {"start": 16, "end": 18, "kind": "dropout", "magnitude": 1}), "Dropout magnitude"),
            (lambda c: c["sensor_experiment"]["control_faults"].__setitem__(
                0, {"start": 4, "end": 7, "kind": "stuck", "magnitude": 0.5}), "bias or dropout"),
        )
        for mutation, message in mutations:
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_model(config)

    def test_work_budget_failure_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            path = base / "config.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            output = base / "bundle"
            with patch("wombmodels.sensor_failover.MAX_TOTAL_SUBSTEPS", 1):
                with self.assertRaisesRegex(InputError, "Integration exceeds"):
                    sensor_failover(path, output)
            self.assertFalse(output.exists())

    def test_cli_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bundle"
            result = main(["sensor-failover-model", "--config",
                           str(ROOT / "examples/sensor_failover_fixture.json"), "--out", str(output)])
            self.assertEqual(result, 0)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])


if __name__ == "__main__":
    unittest.main()
