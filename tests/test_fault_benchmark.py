import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.fault_benchmark import (
    MAX_REPLICATES, _calibrate, _fit_policies, _paired_outcomes, _schedules, _score_event, benchmark_fault_detectors,
)
from wombmodels.numerics import output_times

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "common_cause_fault_fixture.json"


class FaultBenchmarkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.config = Path(temp.name) / "fixture.json"
        self.output = Path(temp.name) / "results"
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.fixture["dimensionless_time"]["duration"] = 8
        self.fixture["interval_boundaries"] = [2, 4, 6]
        self.fixture["outages"] = []
        self.fixture["monitor"].update(seed=-3, noise_sd=0, faults=[])
        self.fixture["fault_experiment"]["actuator_noise_sd"] = 0
        faults = self.fixture["fault_experiment"]["control_faults"]
        for event, start in zip(faults, (0.5, 3, 5)):
            event.update(start=start, end=start + 1)
        self.write_fixture()

    def write_fixture(self):
        self.config.write_text(json.dumps(self.fixture, indent=2) + "\n", encoding="utf-8")

    def read_records(self, name):
        with (self.output / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def test_noiseless_detectors_and_matched_design(self):
        benchmark_fault_detectors(self.config, self.output, replicates=2)
        report = json.loads((self.output / "benchmark_report.json").read_bytes())
        self.assertEqual(report["simulation_runs"], 48)
        with (self.output / "benchmark_runs.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), report["simulation_runs"])
        for condition in report["conditions"]:
            self.assertEqual((condition["control_runs"], condition["false_alarm_controls"]), (2, 0))
            self.assertEqual(condition["events"], 6)
            augmented = condition["mode"] == "balance_augmented_freeze"
            self.assertEqual(condition["detected"], 6 if augmented else 2)
            self.assertEqual(condition["missed"], 0 if augmented else 4)
            for kind, metrics in condition["by_fault_kind"].items():
                expected = 2 if augmented or kind == "primary_bias" else 0
                self.assertEqual((metrics["detected"], metrics["events"]), (expected, 2))
                self.assertEqual(metrics["median_detection_delay"], 0.5 if expected else None)
        for replicate in ("1", "2"):
            subset = [row for row in rows if row["replicate"] == replicate]
            seeds = {int(row["noise_seed"]) for row in subset}
            self.assertEqual(seeds, {4 if replicate == "1" else 8})
            for template_index in ("1", "2", "3"):
                events = [row for row in subset if row["template_index"] == template_index]
                self.assertEqual(len(events), 6)
                self.assertEqual(len({(row["start"], row["end"]) for row in events}), 1)
                start, end = float(events[0]["start"]), float(events[0]["end"])
                self.assertNotIn(start, {0, 0.5, 3, 5})
                self.assertEqual(end - start, 1)

    def test_first_alarm_boundaries_and_paired_credit(self):
        for alarm, control, expected in [
            (None, None, ("no_alarm", None)), (0, 0, ("pre_fault_alarm", None)),
            (4.5, None, ("late_alarm", None)), (2, None, ("detected", 0)),
            (4, 4.5, ("detected", 2)), (4, 4, ("control_as_early", None)),
            (3, 2.5, ("control_as_early", None)),
        ]:
            with self.subTest(alarm=alarm, control=control):
                self.assertEqual(_score_event(alarm, control, 2, 4), expected)

    def test_short_terminal_step_and_replicate_prefix(self):
        template = {"kind": "common_sensor_dropout", "start": 1, "end": 2, "magnitude": 0}
        times = output_times(4.25, 0.5)
        schedule = _schedules([template], times, 0.5, 31, 6)
        self.assertEqual(_schedules([template], times, 0.5, 31, 2), schedule[:2])
        self.assertEqual({events[0]["start"] for events in schedule[:5]}, {0.5, 1.5, 2, 2.5, 3})
        for (event,) in schedule:
            self.assertEqual(event["end"] - event["start"], 1)
            self.assertLessEqual(event["end"], 4)

    def test_noise_false_alarms_reproduction_and_exclusive_output(self):
        self.fixture["monitor"]["noise_sd"] = 0.5
        self.fixture["fault_experiment"]["disagreement_threshold"] = 1e-12
        self.write_fixture()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["benchmark-fault-detectors", "--config", str(self.config),
                                   "--out", str(self.output), "--replicates", "1"]), 0)
        report = json.loads((self.output / "benchmark_report.json").read_bytes())
        for condition in report["conditions"]:
            self.assertEqual(condition["false_alarm_controls"], 1)
            self.assertEqual(condition["outcomes"], {"pre_fault_alarm": 3})
            self.assertIsNone(condition["median_detection_delay"])
        verification = verify_bundle(self.output, strict=True)
        self.assertTrue(verification["bytes_verified"], verification["errors"])
        self.assertIn("--config source_config.json --replicates 1", verification["rerun_command"])
        self.assertEqual((self.output / "source_config.json").read_bytes(), self.config.read_bytes())
        other = self.output.with_name("rerun")
        benchmark_fault_detectors(self.output / "source_config.json", other, replicates=1)
        for file in self.output.iterdir():
            self.assertEqual(file.read_bytes(), (other / file.name).read_bytes(), file.name)
        with self.assertRaisesRegex(InputError, "already exists"):
            benchmark_fault_detectors(self.config, self.output, replicates=1)

    def test_calibration_grid_ties_first_sample_alarm_and_unmet_target(self):
        experiment = self.fixture["fault_experiment"]
        for quiet_from, expected, target_met in [(1, 1, True), (2, 2, True), (5, 4, False)]:
            with self.subTest(quiet_from=quiet_from):
                def first_alarm(variant, shared, grid, mode, settings, faults):
                    self.assertEqual(faults, [])
                    factor = settings["disagreement_threshold"] / experiment["disagreement_threshold"]
                    for key in ("balance_threshold", "actuator_threshold"):
                        self.assertEqual(settings[key], experiment[key] * factor)
                    self.assertEqual(settings["confirmation_samples"], experiment["confirmation_samples"])
                    return 0.0 if shared == "noisier control" and factor < quiet_from else None

                with patch("wombmodels.fault_benchmark._first_alarm", side_effect=first_alarm):
                    policy, rows = _calibrate({}, (), "disagreement_freeze", experiment,
                                              [(10, "quiet control"), (14, "noisier control")], 4,
                                              [{"threshold_multiplier": factor} for factor in (1, 2, 4)])
                self.assertEqual(policy["threshold_multiplier"], expected)
                self.assertEqual(policy["calibration_target_met"], target_met)
                self.assertEqual([(row["threshold_multiplier"], row["noise_seed"]) for row in rows],
                                 [(factor, seed) for factor in (1, 2, 4) for seed in (10, 14)])

    def test_calibrated_cli_separates_streams_and_preserves_paired_evaluation(self):
        self.fixture["monitor"]["noise_sd"] = 0.06
        self.write_fixture()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["benchmark-fault-detectors", "--config", str(self.config), "--out",
                                   str(self.output), "--replicates", "2", "--calibrate-thresholds"]), 0)
        report = json.loads((self.output / "benchmark_report.json").read_bytes())
        calibration = self.read_records("calibration_runs.csv")
        evaluation = self.read_records("benchmark_runs.csv")
        self.assertEqual((report["schema_version"], report["calibration_runs"], report["evaluation_runs"]),
                         (2, 216, 96))
        self.assertEqual((len(calibration), len(evaluation)), (216, 96))
        self.assertEqual(report["simulation_runs"], len(calibration) + len(evaluation))
        self.assertEqual(len(report["conditions"]), 12)
        for data, count in [(calibration, 12), (evaluation, 2)]:
            self.assertEqual(len({row["noise_seed"] for row in data}), count)
        def streams(rows):
            return {int(row["noise_seed"]) + channel for row in rows for channel in range(4)}
        # The negative fixture seed uses abs(-3)..0. The original benchmark starts at 4.
        original_streams = set(range(4 + 4 * MAX_REPLICATES))
        self.assertTrue(original_streams.isdisjoint(streams(calibration) | streams(evaluation)))
        self.assertTrue(streams(calibration).isdisjoint(streams(evaluation)))
        paired_columns = ("mode", "noise_multiplier", "sensor_noise_sd", "actuator_noise_sd", "replicate",
                          "noise_seed", "template_index", "fault_kind", "magnitude", "start", "end")
        def pairs(policy):
            return [tuple(row[key] for key in paired_columns) for row in evaluation if row["threshold_policy"] == policy]
        self.assertCountEqual(pairs("fixed"), pairs("calibrated"))
        for group in report["conditions"]:
            if group["threshold_policy"] == "fixed":
                self.assertEqual(group["threshold_multiplier"], 1)
                continue
            fitted_on = [row for row in calibration
                         if row["mode"] == group["mode"] and int(row["noise_multiplier"]) == group["noise_multiplier"]]
            counts = {}
            for factor in (1, 2, 4):
                candidate = [r for r in fitted_on if int(r["threshold_multiplier"]) == factor]
                self.assertEqual(len({r["noise_seed"] for r in candidate}), 12)
                counts[factor] = sum(r["first_alarm"] != "" for r in candidate)
            quiet = [factor for factor, alarms in counts.items() if alarms == 0]
            self.assertEqual(group["threshold_multiplier"], min(quiet) if quiet else 4)
            self.assertEqual(group["calibration_target_met"], bool(quiet))
        verified = verify_bundle(self.output, strict=True)
        self.assertTrue(verified["bytes_verified"], verified["errors"])
        self.assertIn("--replicates 2 --calibrate-thresholds", verified["rerun_command"])
        other = self.output.with_name("rerun")
        benchmark_fault_detectors(self.output / "source_config.json", other, replicates=2, calibrate_thresholds=True)
        for file in self.output.iterdir():
            self.assertEqual(file.read_bytes(), (other / file.name).read_bytes(), file.name)

    def test_calibration_work_budget_includes_fitting_before_simulation(self):
        with patch("wombmodels.fault_benchmark.MAX_BENCHMARK_SUBSTEPS", 10000), \
                patch("wombmodels.fault_benchmark._fault_run") as run, self.assertRaisesRegex(InputError, "work budget"):
            benchmark_fault_detectors(self.config, self.output, replicates=1, calibrate_thresholds=True)
        run.assert_not_called()
        with self.assertRaisesRegex(InputError, "boolean"):
            benchmark_fault_detectors(self.config, self.output, calibrate_thresholds="false")
        self.assertFalse(self.output.exists())

    def test_actuator_fit_leaves_sensor_thresholds_at_the_shared_fit(self):
        experiment = self.fixture["fault_experiment"]
        for minimum, expected, met in [(1, 1, True), (2, 2, True), (5, 4, False)]:
            with self.subTest(minimum=minimum):
                def first_alarm(variant, shared, grid, mode, settings, faults):
                    self.assertEqual((mode, faults), ("balance_augmented_freeze", []))
                    sensor = settings["disagreement_threshold"] / experiment["disagreement_threshold"]
                    self.assertEqual(settings["balance_threshold"], sensor * experiment["balance_threshold"])
                    self.assertEqual(settings["confirmation_samples"], experiment["confirmation_samples"])
                    if sensor < 4 or settings["actuator_threshold"] < minimum * experiment["actuator_threshold"]:
                        return 0.0
                    return None

                with patch("wombmodels.fault_benchmark._first_alarm", side_effect=first_alarm):
                    (joint, separate), records = _fit_policies({}, (), "balance_augmented_freeze", experiment,
                                                               [(4, ())], 4, compare_actuator=True)
                self.assertEqual((joint["sensor_threshold_multiplier"], joint["actuator_threshold_multiplier"]), (4, 4))
                self.assertEqual((separate["sensor_threshold_multiplier"], separate["actuator_threshold_multiplier"]),
                                 (4, expected))
                self.assertEqual(separate["calibration_target_met"], met)
                self.assertEqual([(r["sensor_threshold_multiplier"], r["actuator_threshold_multiplier"])
                                  for r in records], [(1, 1), (2, 2), (4, 4), (4, 1), (4, 2), (4, 4)])

    def test_actuator_comparison_publishes_two_matched_policies_on_fresh_seeds(self):
        self.fixture["monitor"]["noise_sd"] = 0.06
        self.fixture["fault_experiment"]["actuator_noise_sd"] = 0.01
        self.write_fixture()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["benchmark-fault-detectors", "--config", str(self.config), "--out",
                                   str(self.output), "--replicates", "2", "--compare-actuator-thresholds"]), 0)
        report = json.loads((self.output / "benchmark_report.json").read_bytes())
        calibration = self.read_records("calibration_runs.csv")
        evaluation = self.read_records("benchmark_runs.csv")
        self.assertEqual(report["schema_version"], 3)
        self.assertEqual((len(calibration), len(evaluation)), (216, 48))
        self.assertEqual((report["calibration_runs"], report["evaluation_runs"], report["simulation_runs"]),
                         (216, 48, 264))
        # Four fixture streams, then the original 32 evaluation seeds, 12 training
        # seeds and another 32 evaluation seeds. Each seed reserves four channels.
        self.assertEqual({int(r["noise_seed"]) for r in calibration}, set(range(132, 180, 4)))
        self.assertEqual({int(r["noise_seed"]) for r in evaluation}, {308, 312})
        identity = ("noise_multiplier", "noise_seed", "replicate", "template_index", "start", "end", "magnitude")
        paired = [[tuple(r[k] for k in identity) for r in evaluation if r["threshold_policy"] == policy]
                  for policy in ("shared", "separate_actuator")]
        self.assertCountEqual(*paired)
        self.assertEqual(len(report["conditions"]), 6)
        self.assertEqual(len(report["paired_outcomes"]), 12)
        for pair in report["paired_outcomes"]:
            self.assertEqual(sum(pair[key] for key in ("both", "shared_only", "separate_actuator_only", "neither")), 2)
        for condition in report["conditions"]:
            self.assertEqual(condition["mode"], "balance_augmented_freeze")
            subset = [r for r in calibration if int(r["noise_multiplier"]) == condition["noise_multiplier"]
                      and r["threshold_policy"] == condition["threshold_policy"]]
            quiet = []
            for factor in (1, 2, 4):
                candidate = [r for r in subset if int(r["actuator_threshold_multiplier"]) == factor]
                self.assertEqual(len({r["noise_seed"] for r in candidate}), 12)
                if all(r["first_alarm"] == "" for r in candidate):
                    quiet.append(factor)
            self.assertEqual(condition["actuator_threshold_multiplier"], min(quiet) if quiet else 4)
            self.assertEqual(condition["calibration_target_met"], bool(quiet))
            if condition["threshold_policy"] == "separate_actuator":
                self.assertEqual({int(r["sensor_threshold_multiplier"]) for r in subset},
                                 {condition["sensor_threshold_multiplier"]})
        checked = verify_bundle(self.output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertIn("--replicates 2 --compare-actuator-thresholds", checked["rerun_command"])

    def test_paired_outcomes_count_control_alarms_and_match_reordered_fault_templates(self):
        shared, separate = [], []
        for template, left, right in [(None, "quiet", "false_alarm"), (1, "detected", "control_as_early"),
                                      (2, "no_alarm", "detected"), (3, "detected", "detected")]:
            case = {"noise_multiplier": 4, "noise_seed": 42, "template_index": template,
                    "fault_kind": "actuator_offset" if template else "none"}
            shared.append({**case, "threshold_policy": "shared", "outcome": left})
            separate.append({**case, "threshold_policy": "separate_actuator", "outcome": right})
        results = {r["fault_kind"]: r for r in _paired_outcomes(shared + list(reversed(separate)))}
        fault, control = results["actuator_offset"], results["none"]
        self.assertEqual((fault["both"], fault["shared_only"], fault["separate_actuator_only"], fault["neither"]),
                         (1, 1, 1, 0))
        self.assertEqual((control["counted_outcome"], control["separate_actuator_only"]), ("false_alarm", 1))

    def test_actuator_comparison_bounds_both_fits_and_rejects_ambiguous_options(self):
        with patch("wombmodels.fault_benchmark.MAX_BENCHMARK_SUBSTEPS", 30000), \
                patch("wombmodels.fault_benchmark._fault_run") as run, self.assertRaisesRegex(InputError, "work budget"):
            benchmark_fault_detectors(self.config, self.output, replicates=1, compare_actuator_thresholds=True)
        run.assert_not_called()
        with self.assertRaisesRegex(InputError, "one threshold comparison"):
            benchmark_fault_detectors(self.config, self.output, calibrate_thresholds=True, compare_actuator_thresholds=True)
        with self.assertRaisesRegex(InputError, "boolean"):
            benchmark_fault_detectors(self.config, self.output, compare_actuator_thresholds="false")
        self.assertFalse(self.output.exists())

    def test_invalid_or_excessive_work_never_publishes(self):
        for value in (True, 0, 33, 1.5):
            with self.subTest(replicates=value), self.assertRaisesRegex(InputError, "replicates"):
                benchmark_fault_detectors(self.config, self.output, replicates=value)
        self.fixture["dimensionless_time"]["duration"] = 1000
        self.write_fixture()
        with patch("wombmodels.fault_benchmark._fault_run") as run, \
                self.assertRaisesRegex(InputError, "work budget"):
            benchmark_fault_detectors(self.config, self.output)
        run.assert_not_called()
        self.fixture["dimensionless_time"]["duration"] = 8
        faults = self.fixture["fault_experiment"]["control_faults"]
        self.fixture["fault_experiment"]["control_faults"] = [{**faults[0], "start": 0, "end": 8}]
        self.write_fixture()
        with self.assertRaisesRegex(InputError, "held-out grid window"):
            benchmark_fault_detectors(self.config, self.output, replicates=1)
        self.fixture["fault_experiment"]["control_faults"] = []
        self.write_fixture()
        with self.assertRaisesRegex(InputError, "at least one control fault"):
            benchmark_fault_detectors(self.config, self.output, replicates=1)
        self.assertFalse(self.output.exists())
