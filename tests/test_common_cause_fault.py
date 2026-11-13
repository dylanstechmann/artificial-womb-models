import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.common_cause_fault import MODES, common_cause_fault
from wombmodels.exchange import NOTICE
from wombmodels.sensor_failover import sensor_failover
from wombmodels.whole_path_twin import whole_path_twin

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/common_cause_fault_fixture.json").read_text(encoding="utf-8"))


def only_fault(config, kind):
    config["fault_experiment"]["control_faults"] = [
        item for item in config["fault_experiment"]["control_faults"] if item["kind"] == kind]
    return config


class CommonCauseFaultTests(unittest.TestCase):
    def run_model(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = common_cause_fault(path, output)
        report = json.loads((output / "common_cause_fault_report.json").read_text(encoding="utf-8"))
        return receipt, report, output

    @staticmethod
    def observations(output, mode, variant="living_interface"):
        with (output / "fault_observations.csv").open(newline="", encoding="utf-8") as stream:
            return [row for row in csv.DictReader(stream)
                    if row["mode"] == mode and row["variant"] == variant]

    @staticmethod
    def trajectory(output, mode, variant="living_interface"):
        with (output / f"trajectory_{mode}_{variant}.csv").open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def test_declared_three_fault_fixture_discriminates_hidden_fault_classes(self):
        _receipt, report, output = self.run_model(fixture())
        self.assertEqual(report["model_family"], "dimensionless_whole_path_common_cause_fault_experiment")
        self.assertEqual(report["qualification_status"], "dimensionless_software_checks_passed")
        self.assertEqual(len(report["comparisons"]), 3)
        for comparison in report["comparisons"]:
            disagreement = comparison["disagreement_freeze"]
            augmented = comparison["balance_augmented_freeze"]
            self.assertEqual(disagreement["per_fault_kind"]["primary_bias"]["fault_samples"], 6)
            self.assertEqual(disagreement["per_fault_kind"]["primary_bias"]["detected_fault_samples"], 4)
            for kind in ("common_sensor_bias", "actuator_offset"):
                self.assertEqual(disagreement["per_fault_kind"][kind]["fault_samples"], 7)
                self.assertEqual(disagreement["per_fault_kind"][kind]["detected_fault_samples"], 0)
                self.assertIsNone(disagreement["per_fault_kind"][kind]["first_detection_time"])
            for kind, expected in (("primary_bias", (6, 4)),
                                   ("common_sensor_bias", (7, 5)),
                                   ("actuator_offset", (7, 5))):
                result = augmented["per_fault_kind"][kind]
                self.assertEqual((result["fault_samples"], result["detected_fault_samples"]), expected)
            self.assertEqual(disagreement["false_alarm_samples"], 0)
            self.assertEqual(augmented["false_alarm_samples"], 0)
            self.assertEqual(disagreement["detected_fault_samples"], 4)
            self.assertEqual(augmented["detected_fault_samples"], 14)
            self.assertTrue(augmented["actuator_isolation_ever_active"])
            self.assertFalse(disagreement["actuator_isolation_ever_active"])

        pairwise = self.observations(output, "disagreement_freeze")
        augmented = self.observations(output, "balance_augmented_freeze")
        for kind in ("common_sensor_bias", "actuator_offset"):
            rows = [row for row in pairwise if row["declared_fault"] == kind]
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(row["fault_detected"] == "False" for row in rows))
        self.assertTrue(all(float(row["pairwise_residual"]) < 0.12
                            for row in pairwise if row["declared_fault"] == "common_sensor_bias"))
        at_primary = next(row for row in augmented if float(row["dimensionless_time"]) == 3.0)
        self.assertEqual(at_primary["consecutive_fault_count"], "1")
        self.assertEqual(at_primary["fault_detected"], "False")
        confirmed = next(row for row in augmented if float(row["dimensionless_time"]) == 3.5)
        self.assertEqual(confirmed["consecutive_fault_count"], "2")
        self.assertEqual(confirmed["fault_detected"], "True")
        self.assertEqual(confirmed["fallback_active"], "True")

    def test_isolated_common_sensor_bias_defeats_only_pairwise_disagreement(self):
        _receipt, report, output = self.run_model(only_fault(fixture(), "common_sensor_bias"))
        comparison = report["comparisons"][0]
        disagreement = comparison["disagreement_freeze"]
        augmented = comparison["balance_augmented_freeze"]
        self.assertFalse(disagreement["fallback_ever_active"])
        self.assertEqual(disagreement["detected_fault_samples"], 0)
        self.assertEqual(disagreement["max_absolute_bulk_difference"], 0)
        self.assertEqual(augmented["per_fault_kind"]["common_sensor_bias"]["first_detection_time"], 8.5)
        self.assertEqual(augmented["per_fault_kind"]["common_sensor_bias"]["detected_fault_samples"], 5)
        single = self.trajectory(output, "single_sensor")
        redundant = self.trajectory(output, "disagreement_freeze")
        self.assertEqual(redundant, single)
        observations = self.observations(output, "balance_augmented_freeze")
        first = next(row for row in observations if float(row["dimensionless_time"]) == 8.0)
        second = next(row for row in observations if float(row["dimensionless_time"]) == 8.5)
        self.assertEqual((first["consecutive_fault_count"], first["fault_detected"]), ("1", "False"))
        self.assertEqual((second["consecutive_fault_count"], second["fault_detected"]), ("2", "True"))
        self.assertGreater(float(second["balance_residual"]), 0.55)
        self.assertLess(float(second["pairwise_residual"]), 0.12)

        _receipt, _report, no_fault = self.run_model(only_fault(fixture(), "not_declared"))
        canonical_final = self.trajectory(no_fault, "single_sensor")[-1]["bulk_stock"]
        augmented_final = self.trajectory(output, "balance_augmented_freeze")[-1]["bulk_stock"]
        self.assertLessEqual(abs(float(augmented_final) - float(canonical_final)), 0.004)
        self.assertEqual(single[-1]["bulk_stock"], canonical_final)

    def test_isolated_actuator_offset_is_metered_frozen_and_isolated(self):
        _receipt, report, output = self.run_model(only_fault(fixture(), "actuator_offset"))
        comparison = report["comparisons"][0]
        disagreement = comparison["disagreement_freeze"]
        augmented = comparison["balance_augmented_freeze"]
        self.assertFalse(disagreement["fallback_ever_active"])
        self.assertEqual(disagreement["detected_fault_samples"], 0)
        self.assertEqual(disagreement["max_absolute_bulk_difference"], 0)
        self.assertEqual(augmented["per_fault_kind"]["actuator_offset"]["first_detection_time"], 14.5)
        self.assertEqual(augmented["per_fault_kind"]["actuator_offset"]["detected_fault_samples"], 5)
        self.assertTrue(augmented["actuator_isolation_ever_active"])
        self.assertEqual(self.trajectory(output, "disagreement_freeze"),
                         self.trajectory(output, "single_sensor"))

        observations = self.observations(output, "balance_augmented_freeze")
        start = next(row for row in observations if float(row["dimensionless_time"]) == 14.0)
        confirmation = next(row for row in observations if float(row["dimensionless_time"]) == 14.5)
        self.assertGreater(float(start["actuator_residual"]), 0.35)
        self.assertEqual(start["fault_detected"], "False")
        self.assertEqual(confirmation["fault_detected"], "True")
        self.assertEqual(confirmation["actuator_isolated"], "True")
        self.assertEqual(confirmation["applied_supplement"], confirmation["commanded_supplement"])
        for row in observations:
            if float(row["dimensionless_time"]) > 14.5:
                self.assertEqual(row["actuator_isolated"], "True")
                self.assertEqual(row["delivered_supplement"], row["commanded_supplement"])
        isolated_rows = [row for row in self.trajectory(output, "balance_augmented_freeze")
                         if row["actuator_isolated"] == "True"]
        self.assertTrue(isolated_rows)
        self.assertTrue(all(row["delivered_supplement"] == row["commanded_supplement"]
                            for row in isolated_rows))
        self.assertGreater(augmented["max_absolute_bulk_difference"], 0.18)

    def test_no_fault_single_sensor_matches_canonical_twin_byte_for_byte(self):
        config = only_fault(fixture(), "not_declared")
        _receipt, report, output = self.run_model(config)
        self.assertIs(report["no_fault_canonical_trajectories_match"], True)
        self.assertTrue(all(not comparison[mode]["fallback_ever_active"]
                            for comparison in report["comparisons"] for mode in MODES[1:]))
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            canonical_config = {key: value for key, value in config.items() if key != "fault_experiment"}
            path = base / "canonical.json"
            path.write_text(json.dumps(canonical_config), encoding="utf-8")
            whole_path_twin(path, base / "canonical")
            for name in config["variants"]:
                with (base / "canonical" / f"trajectory_{name}.csv").open(newline="") as stream:
                    expected = list(csv.DictReader(stream))
                actual = self.trajectory(output, "single_sensor", name)
                self.assertEqual(len(actual), len(expected))
                for actual_row, expected_row in zip(actual, expected):
                    for column in expected_row:
                        self.assertEqual(actual_row[column], expected_row[column], column)
        observations = self.observations(output, "single_sensor")
        for row in observations:
            self.assertAlmostEqual(float(row["balance_residual"]), abs(float(row["primary_noise"])), places=12)
            self.assertAlmostEqual(float(row["actuator_residual"]),
                                   abs(float(row["actuator_meter_noise"])), places=12)

    def test_primary_fault_mode_is_equivalent_to_t28_sensor_failover(self):
        config = fixture()
        config["fault_experiment"]["control_faults"] = [
            {"start": 4, "end": 7, "kind": "primary_bias", "magnitude": 0.5},
            {"start": 16, "end": 18, "kind": "primary_dropout", "magnitude": 0},
        ]
        _receipt, _report, output = self.run_model(config)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            old_output = base / "t28"
            sensor_failover(ROOT / "examples/sensor_failover_fixture.json", old_output)
            for name in config["variants"]:
                with (old_output / f"trajectory_independent_sensor_freeze_{name}.csv").open(newline="") as stream:
                    expected = list(csv.DictReader(stream))
                actual = self.trajectory(output, "disagreement_freeze", name)
                for actual_row, expected_row in zip(actual, expected):
                    for column in expected_row:
                        self.assertEqual(actual_row[column], expected_row[column], (name, column))
            with (old_output / "sensor_observations.csv").open(newline="") as stream:
                old = [row for row in csv.DictReader(stream)
                       if row["variant"] == "living_interface" and row["mode"] == "independent_sensor_freeze"]
        new = self.observations(output, "disagreement_freeze")
        for start in (4.0, 16.0):
            old_detection = next(float(row["dimensionless_time"]) for row in old
                                 if float(row["dimensionless_time"]) >= start and row["fault_detected"] == "True")
            new_detection = next(float(row["dimensionless_time"]) for row in new
                                 if float(row["dimensionless_time"]) >= start and row["fault_detected"] == "True")
            self.assertEqual(new_detection, old_detection)
        dropout = next(row for row in new if float(row["dimensionless_time"]) == 16.0)
        self.assertEqual(dropout["primary_available"], "False")
        self.assertEqual(dropout["secondary_available"], "True")
        self.assertEqual(dropout["primary_reading"], "")
        self.assertEqual(dropout["pairwise_residual"], "")

    def test_common_sensor_dropout_is_visible_to_both_fallbacks(self):
        config = fixture()
        config["fault_experiment"]["control_faults"] = [
            {"start": 16, "end": 18, "kind": "common_sensor_dropout", "magnitude": 0}]
        _receipt, report, output = self.run_model(config)
        for mode in MODES[1:]:
            comparison = report["comparisons"][0][mode]
            result = comparison["per_fault_kind"]["common_sensor_dropout"]
            self.assertEqual((result["fault_samples"], result["detected_fault_samples"]), (5, 3))
            self.assertEqual(result["first_detection_time"], 16.5)
            row = next(row for row in self.observations(output, mode)
                       if float(row["dimensionless_time"]) == 16.0)
            self.assertEqual(row["primary_available"], "False")
            self.assertEqual(row["secondary_available"], "False")
            self.assertEqual(row["primary_reading"], "")
            self.assertEqual(row["secondary_reading"], "")

    def test_hidden_internal_state_is_not_a_fallback_observable(self):
        _receipt, report, _output = self.run_model(fixture())
        hidden = report["hidden_internal_state_check"]
        self.assertIs(hidden["internal_tissue_observed_by_fallback"], False)
        self.assertIs(hidden["internal_channels_differ"], True)
        self.assertIs(hidden["boundary_channels_identical_before_fallback"], True)
        self.assertIs(hidden["sensor_balance_actuator_residuals_identical_before_fallback"], True)
        self.assertIs(hidden["unobservable_without_internal_channels"], True)
        self.assertEqual(hidden["pre_fallback_samples_compared"], 81)

    def test_deterministic_and_strictly_verified_publication(self):
        receipt, _report, first = self.run_model(fixture())
        _receipt, _report, second = self.run_model(fixture())
        self.assertEqual(receipt["bundle_kind"], "dimensionless_common_cause_fault")
        self.assertEqual(receipt["metadata"]["n_modes"], 3)
        trajectory_files = [path for path in first.iterdir() if path.name.startswith("trajectory_")]
        self.assertEqual(len(trajectory_files), 9)
        for path in first.iterdir():
            if path.name != "receipt.json":
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes(), path.name)
        checked = verify_bundle(first, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertIn("common-cause-fault-model", checked["rerun_command"])
        self.assertIn(NOTICE, (first / "REPORT.md").read_text(encoding="utf-8"))
        self.assertTrue((first / "source_config.json").is_file())

    def test_rejects_malformed_experiment_configuration(self):
        mutations = (
            (lambda c: c.pop("fault_experiment"), "fault_experiment"),
            (lambda c: c["fault_experiment"].update(extra=1), "fault_experiment"),
            (lambda c: c["fault_experiment"].update(disagreement_threshold=0), "disagreement_threshold"),
            (lambda c: c["fault_experiment"].update(balance_threshold=10.1), "balance_threshold"),
            (lambda c: c["fault_experiment"].update(actuator_threshold=True), "actuator_threshold"),
            (lambda c: c["fault_experiment"].update(actuator_noise_sd=1.1), "actuator_noise_sd"),
            (lambda c: c["fault_experiment"].update(confirmation_samples=0), "confirmation_samples"),
            (lambda c: c["fault_experiment"].update(confirmation_samples=21), "confirmation_samples"),
            (lambda c: c["fault_experiment"].update(confirmation_samples=1.5), "confirmation_samples"),
            (lambda c: c["fault_experiment"].update(fallback_policy="other"), "fallback_policy"),
            (lambda c: c["fault_experiment"]["control_faults"].__setitem__(
                0, {"start": 3.1, "end": 5.5, "kind": "primary_bias", "magnitude": 0.5}), "output grid"),
            (lambda c: c["fault_experiment"]["control_faults"].__setitem__(
                1, {"start": 5.0, "end": 11, "kind": "common_sensor_bias", "magnitude": 0.5}), "nonoverlapping"),
            (lambda c: c["fault_experiment"]["control_faults"].__setitem__(
                0, {"start": 3, "end": 5.5, "kind": "stuck", "magnitude": 0.5}), "control faults kind"),
            (lambda c: c["fault_experiment"]["control_faults"].__setitem__(
                0, {"start": 3, "end": 5.5, "kind": "primary_dropout", "magnitude": 1}), "Dropout magnitude"),
            (lambda c: c["fault_experiment"]["control_faults"].__setitem__(
                0, {"start": 3, "end": 5.5, "kind": "common_sensor_dropout", "magnitude": 1}), "Dropout magnitude"),
        )
        for mutation, message in mutations:
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_model(config)
        config = fixture()
        config["fault_experiment"]["control_faults"] = [
            {"start": index, "end": index + 0.5, "kind": "primary_bias", "magnitude": 0.1}
            for index in range(17)]
        with self.assertRaisesRegex(InputError, "at most 16"):
            self.run_model(config)

    def test_work_budget_failure_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            path = base / "config.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            output = base / "bundle"
            with patch("wombmodels.common_cause_fault.MAX_TOTAL_SUBSTEPS", 1):
                with self.assertRaisesRegex(InputError, "Integration exceeds"):
                    common_cause_fault(path, output)
            self.assertFalse(output.exists())

    def test_cli_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bundle"
            result = main(["common-cause-fault-model", "--config",
                           str(ROOT / "examples/common_cause_fault_fixture.json"), "--out", str(output)])
            self.assertEqual(result, 0)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])


if __name__ == "__main__":
    unittest.main()
