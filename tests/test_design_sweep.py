import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.design_sweep import (
    AS_CONFIGURED_TIMING,
    CONFIGURED_FAULTS,
    FAULT_FREE_PROFILE,
    REFLECTED_TIMING,
    _reflect_intervals,
    sweep,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/exchange_fixture.json").read_text())


class DesignSweepTests(unittest.TestCase):
    def run_sweep(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = sweep(config_path, output, replicates=1)
        report = json.loads((output / "design_sweep_report.json").read_text(encoding="utf-8"))
        plan = json.loads((output / "sweep_plan.json").read_text(encoding="utf-8"))
        with (output / "design_summaries.csv").open(newline="", encoding="utf-8") as stream:
            summaries = list(csv.DictReader(stream))
        return receipt, report, plan, summaries

    def test_reflection_preserves_interval_lengths_and_orders_events(self):
        events = [
            {"start": 8.25, "end": 9.0, "kind": "dropout", "magnitude": 0},
            {"start": 1.5, "end": 2.5, "kind": "bias", "magnitude": 0.2},
        ]
        result = _reflect_intervals(events, 12)
        self.assertEqual(
            result,
            [
                {"start": 3.0, "end": 3.75, "kind": "dropout", "magnitude": 0},
                {"start": 9.5, "end": 10.5, "kind": "bias", "magnitude": 0.2},
            ],
        )
        self.assertEqual(
            sorted(item["end"] - item["start"] for item in result),
            sorted(event["end"] - event["start"] for event in events),
        )

    def test_sweep_crosses_fault_and_reflected_timing_profiles_with_bounded_receipt(self):
        receipt, report, plan, summaries = self.run_sweep(fixture())
        self.assertEqual(report["n_designs"], 36)
        self.assertEqual(report["n_synthetic_runs"], 36)
        self.assertEqual(len(summaries), 36)
        self.assertEqual(set(report["event_timing_profiles"]), {AS_CONFIGURED_TIMING, REFLECTED_TIMING})
        self.assertEqual(
            {item["monitor_fault_profile"] for item in report["design_summaries"]},
            {CONFIGURED_FAULTS, FAULT_FREE_PROFILE},
        )
        self.assertEqual(
            {item["event_timing_profile"] for item in report["design_summaries"]},
            {AS_CONFIGURED_TIMING, REFLECTED_TIMING},
        )
        self.assertEqual(len(plan["cadence_designs"]), 3)
        self.assertEqual(len(plan["noise_designs"]), 3)
        self.assertEqual(
            plan["event_schedules"][REFLECTED_TIMING]["wall_outages"],
            [{"start": 5.0, "end": 9.0}],
        )
        self.assertEqual(
            plan["event_schedules"][REFLECTED_TIMING]["monitor_faults_before_fault_removal_profile"],
            [
                {"start": 3.0, "end": 3.75, "kind": "dropout", "magnitude": 0.0},
                {"start": 9.5, "end": 10.5, "kind": "bias", "magnitude": 0.2},
            ],
        )
        self.assertLessEqual(plan["estimated_scheduled_samples"], plan["maximum_total_scheduled_samples"])
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        self.assertEqual(receipt["metadata"]["n_synthetic_runs"], 36)

    def test_sweep_without_events_omits_redundant_timing_and_fault_contrasts(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor_faults"] = []
        _receipt, report, plan, summaries = self.run_sweep(config)
        self.assertEqual(report["n_designs"], 9)
        self.assertEqual(report["n_synthetic_runs"], 9)
        self.assertEqual(report["event_timing_profiles"], [AS_CONFIGURED_TIMING])
        self.assertEqual(plan["monitor_fault_profiles"], [CONFIGURED_FAULTS])
        self.assertTrue(all(item["event_timing_profile"] == AS_CONFIGURED_TIMING for item in summaries))


if __name__ == "__main__":
    unittest.main()
