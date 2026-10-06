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
    _combine_statistics,
    _fit_statistics,
    _interval_statistics,
    _leave_one_replicate_out,
    _reflect_intervals,
    sweep,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/exchange_fixture.json").read_text())


class DesignSweepTests(unittest.TestCase):
    def run_sweep(self, config, *, replicates=1):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = sweep(config_path, output, replicates=replicates)
        report = json.loads((output / "design_sweep_report.json").read_text(encoding="utf-8"))
        plan = json.loads((output / "sweep_plan.json").read_text(encoding="utf-8"))
        with (output / "design_summaries.csv").open(newline="", encoding="utf-8") as stream:
            summaries = list(csv.DictReader(stream))
        with (output / "design_sweep.csv").open(newline="", encoding="utf-8") as stream:
            runs = list(csv.DictReader(stream))
        return receipt, report, plan, summaries, runs

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

    def test_leave_one_seed_out_fit_uses_other_replicate_sufficient_statistics(self):
        base = [
            {"powered_exposure": 1.0, "conversion_exposure": 0.0, "observed_change": 2.0},
            {"powered_exposure": 0.0, "conversion_exposure": 1.0, "observed_change": -0.5},
            {"powered_exposure": 1.0, "conversion_exposure": 1.0, "observed_change": 1.5},
        ]
        groups = []
        residual_pattern = (-0.1, -0.1, 0.1)
        for offset in (-1.0, 0.0, 1.0):
            rows = [dict(item, observed_change=item["observed_change"] + offset * residual)
                    for item, residual in zip(base, residual_pattern)]
            groups.append(_interval_statistics(rows))
        fitted = _fit_statistics(_combine_statistics(groups[1:]))
        self.assertTrue(fitted["estimable"])
        self.assertAlmostEqual(fitted["parameter_estimates"]["powered_input"], 2.0, places=12)
        self.assertAlmostEqual(fitted["parameter_estimates"]["conversion"], -0.5, places=12)
        holdouts = _leave_one_replicate_out(groups)
        self.assertEqual(len(holdouts), 3)
        self.assertTrue(all(item["estimable"] for item in holdouts))
        self.assertTrue(all(item["training_replicates"] == 2 for item in holdouts))
        self.assertTrue(all(item["fixture_scale_rmse"] >= 0 for item in holdouts))
        for item, expected in zip(holdouts, (0.1, 0.0, 0.1)):
            self.assertAlmostEqual(item["fixture_scale_rmse"], expected, places=10)

    def test_sweep_crosses_fault_and_reflected_timing_profiles_with_bounded_receipt(self):
        receipt, report, plan, summaries, runs = self.run_sweep(fixture(), replicates=2)
        self.assertEqual(report["n_designs"], 36)
        self.assertEqual(report["n_synthetic_runs"], 72)
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
        self.assertEqual(plan["temporal_holdout_training_fraction"], 0.7)
        self.assertEqual(plan["prospective_forecast_training_cutoff"],
                         "0.7 × dimensionless duration (not 70% of interval count)")
        self.assertIn("not a forecast", report["temporal_holdout_contract"])
        self.assertIn("No future sensor values enter its predictors", report["prospective_forecast_contract"])
        holdout_runs = [item for item in runs if item["temporal_holdout_estimable"] == "True"]
        self.assertTrue(holdout_runs)
        self.assertTrue(all(item["temporal_holdout_n_intervals"] for item in holdout_runs))
        self.assertTrue(all(item["temporal_holdout_fixture_scale_rmse"] != "" for item in holdout_runs))
        forecasts = [item for item in runs if item["prospective_forecast_estimable"] == "True"]
        self.assertTrue(forecasts)
        self.assertTrue(all(int(item["prospective_forecast_training_readings"]) > 4 for item in forecasts))
        self.assertTrue(all(int(item["prospective_forecast_scored_readings"]) > 0 for item in forecasts))
        self.assertTrue(all(item["prospective_forecast_rmse"] != "" for item in forecasts))
        self.assertTrue(all(item["prospective_forecast_last_value_baseline_rmse"] != "" for item in forecasts))
        for item in forecasts:
            available = item["prospective_forecast_prediction_interval_available"] == "True"
            self.assertEqual(item["prospective_forecast_coverage_95"] != "", available)
            self.assertEqual(item["prospective_forecast_mean_interval_width_95"] != "", available)
            if not available:
                self.assertIn("covariance", item["prospective_forecast_prediction_interval_reason"])
        for item in summaries:
            self.assertLessEqual(int(item["prospective_forecast_interval_available_replicates"]),
                                 int(item["prospective_forecast_estimable_replicates"]))
        self.assertTrue(all(item["prospective_forecast_estimable_replicates"] in {"0", "1", "2"}
                            for item in summaries))
        self.assertTrue(all(item["temporal_holdout_estimable_replicates"] in {"0", "1", "2"}
                            for item in summaries))
        self.assertIn("one fixture", report["cross_replicate_holdout_contract"])
        cross_holdout_runs = [item for item in runs
                              if item["cross_replicate_holdout_estimable"] == "True"]
        self.assertTrue(cross_holdout_runs)
        self.assertTrue(all(item["cross_replicate_holdout_training_replicates"] == "1"
                            for item in cross_holdout_runs))
        self.assertTrue(all(item["cross_replicate_holdout_fixture_scale_rmse"] != ""
                            for item in cross_holdout_runs))
        self.assertTrue(any(int(item["cross_replicate_holdout_estimable_replicates"]) == 2
                            for item in summaries))
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
        self.assertEqual(receipt["metadata"]["n_synthetic_runs"], 72)

    def test_sweep_without_events_omits_redundant_timing_and_fault_contrasts(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor_faults"] = []
        _receipt, report, plan, summaries, runs = self.run_sweep(config)
        self.assertEqual(report["n_designs"], 9)
        self.assertEqual(report["n_synthetic_runs"], 9)
        self.assertEqual(report["event_timing_profiles"], [AS_CONFIGURED_TIMING])
        self.assertEqual(plan["monitor_fault_profiles"], [CONFIGURED_FAULTS])
        self.assertTrue(all(item["event_timing_profile"] == AS_CONFIGURED_TIMING for item in summaries))
        self.assertTrue(all(item["cross_replicate_holdout_estimable"] == "False" for item in runs))


if __name__ == "__main__":
    unittest.main()
