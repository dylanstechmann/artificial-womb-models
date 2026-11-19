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
from wombmodels.fault_benchmark import _schedules, _score_event, benchmark_fault_detectors
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
