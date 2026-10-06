import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.developmental_models import simulate_mechanics, simulate_transport
from wombmodels.numerical_verification import (
    _exact_transport_state,
    verify_transport_accuracy,
)

ROOT = Path(__file__).resolve().parents[1]


class DevelopmentalModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def config(self, name):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def run_model(self, function, config, name):
        config_path = self.root / f"{name}.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = self.root / f"{name}-bundle"
        receipt = function(config_path, output)
        return receipt, output

    def test_transport_reports_discrete_conservation_and_separate_reference(self):
        receipt, output = self.run_model(simulate_transport, self.config("transport_fixture.json"), "transport")
        report = json.loads((output / "transport_report.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["bundle_kind"], "dimensionless_transport_theory")
        self.assertLess(report["outputs"]["maximum_absolute_accounting_residual"], 1e-10)
        self.assertEqual(report["stage_context"]["stage_track"], "implantation_and_placentation")
        self.assertFalse(report["biological_measurements"])
        self.assertIn("single well-mixed", report["alternative_model"]["name"])
        self.assertTrue((output / "well_mixed_reference.csv").is_file())

    def test_transport_rejects_a_numerically_unstable_step(self):
        config = self.config("transport_fixture.json")
        config["dimensionless_time"]["step"] = 2.0
        config_path = self.root / "unstable.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(InputError, "positivity bound"):
            simulate_transport(config_path, self.root / "unstable-bundle")
        self.assertFalse((self.root / "unstable-bundle").exists())

    def test_transport_fast_mixing_approaches_capacity_matched_reference(self):
        differences = []
        for transfer in (20.0, 200.0):
            config = self.config("transport_fixture.json")
            config["initial"] = {"interface": 0.0, "core": 0.0}
            config["boundary_concentration"] = 1.0
            config["rates"] = {"boundary_exchange": 1.0,
                               "intercompartment_transport": transfer, "loss": 0.5}
            config["dimensionless_time"] = {"duration": 20.0, "step": 0.002}
            _receipt, output = self.run_model(simulate_transport, config, f"mixing-{transfer}")
            report = json.loads((output / "transport_report.json").read_text(encoding="utf-8"))
            reference = report["alternative_model"]["final_state"]
            core = report["outputs"]["final_core_state"]
            steady_core = transfer / ((transfer + 0.5) + 0.5 * (2 * transfer + 0.5))
            self.assertAlmostEqual(reference, 0.5, places=6)
            self.assertAlmostEqual(core, steady_core, places=6)
            self.assertEqual(report["alternative_model"]["capacity_relative_to_one_compartment"], 2.0)
            differences.append(abs(reference - core))
        self.assertLess(differences[1], 0.002)
        self.assertLess(differences[1], differences[0] / 5)

    def test_mechanics_reports_piecewise_response_and_elastic_alternative(self):
        receipt, output = self.run_model(simulate_mechanics, self.config("mechanics_fixture.json"), "mechanics")
        report = json.loads((output / "mechanics_report.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["bundle_kind"], "dimensionless_mechanics_theory")
        self.assertGreater(report["outputs"]["peak_strain"], 0)
        self.assertAlmostEqual(report["outputs"]["dimensionless_relaxation_time"], 0.5)
        self.assertIn("elasticity", report["alternative_model"]["equation"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertTrue((output / "elastic_reference.csv").is_file())

    def test_mechanics_matches_closed_form_response_at_load_boundaries(self):
        _receipt, output = self.run_model(
            simulate_mechanics, self.config("mechanics_fixture.json"), "mechanics-boundaries")
        with (output / "mechanics_trajectory.csv").open(newline="", encoding="utf-8") as stream:
            rows = {float(row["dimensionless_time"]): float(row["strain"])
                    for row in csv.DictReader(stream)}
        stress_response_at_four = (0.8 / 1.2) * (1 - math.exp(-2 * (4 - 1)))
        stress_response_at_five = stress_response_at_four * math.exp(-2 * (5 - 4))
        stress_response_at_seven = (stress_response_at_five * math.exp(-2 * (7 - 5))
                                    + (0.4 / 1.2) * (1 - math.exp(-2 * (7 - 5))))
        self.assertAlmostEqual(rows[1.0], 0.0, places=14)
        self.assertAlmostEqual(rows[4.0], stress_response_at_four, places=12)
        self.assertAlmostEqual(rows[5.0], stress_response_at_five, places=12)
        self.assertAlmostEqual(rows[7.0], stress_response_at_seven, places=12)
        self.assertAlmostEqual(rows[8.0], stress_response_at_seven * math.exp(-2), places=12)

    def test_exact_transport_reference_covers_zero_rates_and_unequal_transfer(self):
        self.assertEqual(_exact_transport_state(
            0.3, 0.8, 4.0, exchange=0.0, transport=0.0, loss=0.0, boundary=1.0), (0.3, 0.8))
        interface, core = _exact_transport_state(
            2.0, 0.0, 1.0, exchange=0.0, transport=2.0, loss=0.0, boundary=1.0)
        self.assertAlmostEqual(interface, 1.0 + math.exp(-4.0), places=13)
        self.assertAlmostEqual(core, 1.0 - math.exp(-4.0), places=13)
        first = _exact_transport_state(
            0.2, 0.9, 0.4, exchange=0.7, transport=0.3, loss=0.11, boundary=1.3)
        second = _exact_transport_state(
            first[0], first[1], 0.6, exchange=0.7, transport=0.3, loss=0.11, boundary=1.3)
        combined = _exact_transport_state(
            0.2, 0.9, 1.0, exchange=0.7, transport=0.3, loss=0.11, boundary=1.3)
        self.assertAlmostEqual(second[0], combined[0], places=13)
        self.assertAlmostEqual(second[1], combined[1], places=13)

    def test_transport_step_halving_report_shows_first_order_convergence(self):
        config_path = ROOT / "examples" / "transport_fixture.json"
        output = self.root / "transport-verification"
        receipt = verify_transport_accuracy(config_path, output)
        report = json.loads((output / "numerical_verification_report.json").read_text(encoding="utf-8"))
        curve = report["convergence"]
        self.assertEqual(receipt["bundle_kind"], "dimensionless_transport_numerical_verification")
        self.assertEqual(report["n_refinement_levels"], 5)
        self.assertFalse(report["biological_measurements"])
        self.assertEqual((output / "input_config.json").read_bytes(), config_path.read_bytes())
        self.assertTrue(all(row["max_abs_state_error"] > 0 for row in curve))
        self.assertTrue(all(right["max_abs_state_error"] < left["max_abs_state_error"]
                            for left, right in zip(curve, curve[1:])))
        self.assertTrue(all(0.8 < row["observed_order"] < 1.2 for row in curve[2:]))
        self.assertTrue((output / "transport_convergence.csv").is_file())
        self.assertTrue((output / "finest_step_trajectory.csv").is_file())

    def test_transport_verification_rejects_unstable_start_without_publishing(self):
        config = self.config("transport_fixture.json")
        config["dimensionless_time"]["step"] = 2.0
        config_path = self.root / "unstable-verification.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = self.root / "unstable-verification"
        with self.assertRaisesRegex(InputError, "positivity bound"):
            verify_transport_accuracy(config_path, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
