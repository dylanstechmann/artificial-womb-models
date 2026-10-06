import json
import math
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, sha256
from wombmodels.exchange import NOTICE, run_fixture, simulate, transition, validate_config

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/exchange_fixture.json").read_text())


class ExchangeTests(unittest.TestCase):
    def test_analytic_equilibrium_substrate_and_exponential_waste(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor_faults"] = []
        rows, result = run_fixture(config)
        for row in rows:
            self.assertAlmostEqual(row["substrate"], 1, places=12)
            self.assertAlmostEqual(row["waste"], 0.5 - 0.25 * math.exp(-row["dimensionless_time"]), places=12)
        self.assertFalse(result["physiologically_calibrated"])
        self.assertFalse(result["human_gestation_prediction"])

    def test_equal_rate_analytic_limit(self):
        substrate, waste, supplied, converted, cleared = transition(2, 1, 3, 0, 0.4, 0.4)
        self.assertAlmostEqual(substrate, 2 * math.exp(-1.2), places=13)
        self.assertAlmostEqual(waste, math.exp(-1.2) * (1 + 0.4 * 2 * 3), places=13)
        self.assertAlmostEqual(substrate + waste + cleared, 3, places=13)
        self.assertEqual(supplied, 0)

    def test_zero_conversion_and_clearance_limits(self):
        substrate, waste, supplied, converted, cleared = transition(2, 3, 4, 0.5, 0, 0)
        self.assertEqual((substrate, waste, supplied, converted, cleared), (4, 3, 2, 0, 0))
        substrate, waste, supplied, converted, cleared = transition(2, 3, 4, 0, 0.5, 0)
        self.assertAlmostEqual(substrate + waste, 5, places=13)
        self.assertEqual(cleared, 0)

    def test_balances_under_outage_and_near_equal_rates(self):
        for clearance in (0, 0.5, 0.500000000001, 0.499999999999, 1):
            config = fixture()
            config["rates"]["powered_clearance"] = clearance
            rows, result = run_fixture(config)
            for residual in result["balances"].values():
                self.assertLess(residual, 1e-10)
            for row in rows:
                self.assertGreaterEqual(min(row["substrate"], row["waste"], row["backup_reserve"]), 0)

    def test_outage_and_backup_depletion_boundaries_are_explicit(self):
        config = fixture()
        config["dimensionless_time"] = {"duration": 4, "output_step": 1}
        config["wall_outages"] = [{"start": 1.2, "end": 3.3}]
        config["initial"]["backup_reserve"] = 0.35
        config["monitor_faults"] = []
        rows, result = run_fixture(config)
        boundary = {round(row["dimensionless_time"], 9): row for row in rows}
        self.assertEqual(boundary[1.2]["power_source"], "backup")
        self.assertEqual(boundary[1.9]["power_source"], "none")
        self.assertEqual(boundary[3.3]["power_source"], "wall")
        self.assertEqual(boundary[1.9]["backup_reserve"], 0)
        self.assertAlmostEqual(rows[-1]["cumulative_input"], 0.5 * (4 - 1.4), places=12)

    def test_monitor_faults_use_half_open_intervals(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor"]["noise_sd"] = 0
        config["monitor_faults"] = [{"start": 1.2, "end": 1.8, "kind": "bias", "magnitude": 0.2}]
        rows, result = run_fixture(config)
        boundary = {row["dimensionless_time"]: row for row in rows}
        self.assertFalse(boundary[1.2]["sensor_sampled"])
        self.assertIsNone(boundary[1.2]["software_alarm"])
        self.assertTrue(boundary[1.25]["software_alarm"])
        self.assertFalse(boundary[1.8]["synthetic_sensor_fault"])
        self.assertIsNone(boundary[1.8]["software_alarm"])
        self.assertFalse(boundary[2]["software_alarm"])
        metrics = result["software_fault_metrics"]
        self.assertEqual(metrics["false_negative"], 0)
        self.assertEqual(metrics["false_positive"], 0)
        self.assertAlmostEqual(metrics["fault_intervals"][0]["dimensionless_detection_delay"], 0.05)
        self.assertEqual(sum(metrics[key] for key in ("true_positive", "false_positive", "true_negative", "false_negative")),
                         result["n_monitor_samples"])

    def test_fault_between_scheduled_samples_is_undetected(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor"]["noise_sd"] = 0
        config["monitor_faults"] = [{"start": 1.1, "end": 1.2, "kind": "dropout", "magnitude": 0}]
        _, result = run_fixture(config)
        metrics = result["software_fault_metrics"]
        self.assertIsNone(metrics["fault_intervals"][0]["first_alarm"])
        self.assertEqual(metrics["true_positive"], 0)

    def test_event_rows_do_not_consume_scheduled_noise_samples(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor_faults"] = []
        baseline, _ = run_fixture(config)
        # Below-threshold zero bias adds integration boundaries without changing S.
        config["monitor_faults"] = [{"start": 1.1, "end": 1.2, "kind": "bias", "magnitude": 0}]
        changed, _ = run_fixture(config)
        self.assertEqual([row["sensor_reading"] for row in baseline],
                         [row["sensor_reading"] for row in changed if row["sensor_sampled"]])

    def test_small_reserves_retain_scale_invariant_power_timing(self):
        config = fixture()
        config["dimensionless_time"] = {"duration": 10, "output_step": 1}
        config["wall_outages"] = [{"start": 0, "end": 10}]
        config["monitor_faults"] = []
        reference = None
        for scale in (1, 1e-16):
            config["initial"]["backup_reserve"] = scale
            config["rates"]["backup_draw"] = 1e-4 * scale
            rows, _ = run_fixture(config)
            power = [row["power_source"] for row in rows]
            if reference is None:
                reference = power
            self.assertEqual(power, reference)
            self.assertTrue(all(row["power_source"] == "backup" for row in rows[:-1]))
            self.assertAlmostEqual(rows[-1]["backup_reserve"] / scale, 0.999, places=12)

    def test_shared_power_loss_is_one_episode_across_sampling_cadences(self):
        config = fixture()
        config["initial"]["backup_reserve"] = 0
        config["wall_outages"] = [{"start": 1.1, "end": 3.3}]
        config["monitor_faults"] = []
        for step in (0.25, 0.01):
            config["dimensionless_time"]["output_step"] = step
            _, result = run_fixture(config)
            episodes = result["software_fault_metrics"]["fault_intervals"]
            self.assertEqual(len(episodes), 1)
            self.assertEqual((episodes[0]["start"], episodes[0]["end"], episodes[0]["kind"]),
                             (1.1, 3.3, "shared_power_loss"))

    def test_dropout_and_shared_power_loss_create_missing_readings(self):
        rows, result = run_fixture(fixture())
        by_time = {row["dimensionless_time"]: row for row in rows}
        self.assertIsNone(by_time[5]["sensor_reading"])
        self.assertIsNone(by_time[8.25]["sensor_reading"])
        self.assertIsNotNone(by_time[9]["sensor_reading"])
        self.assertIn("oracle", result["software_fault_metrics"]["detector"])

    def test_undetectable_bias_is_reported_as_false_negative(self):
        config = fixture()
        config["wall_outages"] = []
        config["monitor"]["noise_sd"] = 0
        config["monitor_faults"] = [{"start": 1, "end": 2, "kind": "bias", "magnitude": 0.01}]
        _, result = run_fixture(config)
        self.assertGreater(result["software_fault_metrics"]["false_negative"], 0)
        self.assertIsNone(result["software_fault_metrics"]["fault_intervals"][0]["first_alarm"])

    def test_noise_and_results_are_seed_deterministic(self):
        self.assertEqual(run_fixture(fixture()), run_fixture(fixture()))
        changed = fixture()
        changed["monitor"]["seed"] += 1
        self.assertNotEqual(run_fixture(fixture())[0], run_fixture(changed)[0])

    def test_nonfinite_boolean_negative_and_unknown_inputs_rejected(self):
        for invalid in (float("nan"), float("inf"), True, -0.1, "0.5", 10**1000):
            config = fixture()
            config["rates"]["conversion"] = invalid
            with self.assertRaises(InputError):
                validate_config(config)
        config = fixture()
        config["device_endpoint"] = "serial://example"
        with self.assertRaises(InputError):
            validate_config(config)

    def test_interval_overlap_bounds_and_infinite_backup_rejected(self):
        for outages in ([{"start": 1, "end": 2}, {"start": 1.5, "end": 3}],
                        [{"start": 2, "end": 1}], [{"start": 0, "end": 13}]):
            config = fixture()
            config["wall_outages"] = outages
            with self.assertRaises(InputError):
                validate_config(config)
        config = fixture()
        config["rates"]["backup_draw"] = 0
        with self.assertRaises(InputError):
            validate_config(config)

    def test_numerically_unresolvable_extreme_is_rejected(self):
        with self.assertRaisesRegex(InputError, "floating-point"):
            transition(1, 0, 1, 1, 1e-320, 1)

    def test_artifact_hashes_determinism_and_no_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = ROOT / "examples/exchange_fixture.json"
            first = simulate(source, root / "first")
            second = simulate(source, root / "second")
            self.assertEqual(first, second)
            for name, contract in first["outputs"].items():
                raw = (root / "first" / name).read_bytes()
                self.assertEqual(sha256(raw), contract["sha256"])
                self.assertEqual(len(raw), contract["size_bytes"])
                self.assertEqual(raw, (root / "second" / name).read_bytes())
            before = (root / "first" / "receipt.json").read_bytes()
            with self.assertRaises(InputError):
                simulate(source, root / "first")
            self.assertEqual(before, (root / "first" / "receipt.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
