import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.growth_mechanics import analytic_failure, equilibrium_strain, growth_mechanics


ROOT = Path(__file__).resolve().parents[1]
WORLDS = ("paced", "damage_witness", "fixed_stiffness")


def fixture():
    return json.loads((ROOT / "examples/growth_mechanics_fixture.json").read_text(encoding="utf-8"))


class GrowthMechanicsTests(unittest.TestCase):
    def run_model(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = growth_mechanics(config_path, output)
        report = json.loads((output / "growth_mechanics_report.json").read_text(encoding="utf-8"))
        trajectories = {}
        for name in WORLDS:
            with (output / f"trajectory_{name}.csv").open(newline="", encoding="utf-8") as stream:
                trajectories[name] = list(csv.DictReader(stream))
        return receipt, report, trajectories, output

    def test_analytic_failure_matches_the_square_cube_crossover(self):
        config = fixture()
        _receipt, report, trajectories, _output = self.run_model(config)
        growth = {key: config["growth"][key] for key in
                  ("linear_rate", "load_exponent", "stiffness_exponent")}
        scaling = {key: config["scaling"][key] for key in
                   ("load_coefficient", "stiffness_coefficient")}
        analytic = analytic_failure(growth, scaling, config["chamber"]["strain_limit"])
        self.assertAlmostEqual(analytic["failure_size"], 1.5 ** 3, places=12)
        self.assertAlmostEqual(analytic["failure_time"], (1.5 ** 3 - 1) / 0.12, places=12)
        self.assertFalse(analytic["never_fails"])
        self.assertEqual(report["analytic_failure"]["failure_time"], analytic["failure_time"])
        # The tracked strain crosses the limit within two output steps of the
        # analytic equilibrium crossing.
        step = config["dimensionless_time"]["output_step"]
        self.assertLessEqual(report["timeline"]["paced_failure_time"]
                             - analytic["failure_time"], 2 * step)
        self.assertEqual(equilibrium_strain(growth, scaling, 0.0), 1.0 / 3.0)

    def test_damage_witness_shares_strain_and_differs_in_damage(self):
        _receipt, report, trajectories, _output = self.run_model(fixture())
        witness = report["damage_witness"]
        self.assertTrue(witness["strain_series_identical"])
        self.assertEqual(witness["max_abs_strain_difference"], 0.0)
        self.assertGreater(witness["relative_damage_difference"], 2.5)
        self.assertGreater(witness["final_damage_witness"], witness["final_damage_configured"])
        for left, right in zip(trajectories["paced"], trajectories["damage_witness"]):
            self.assertEqual(left["strain"], right["strain"])
        self.assertNotEqual(trajectories["paced"][-1]["cumulative_damage"],
                            trajectories["damage_witness"][-1]["cumulative_damage"])

    def test_accommodation_regimes_separate_in_the_observable_channel(self):
        _receipt, report, trajectories, _output = self.run_model(fixture())
        comparison = report["accommodation_comparison"]
        self.assertTrue(comparison["separated_in_observable_channel"])
        self.assertGreater(comparison["max_abs_strain_difference"], 0.5)
        timeline = report["timeline"]
        self.assertLess(timeline["fixed_stiffness_failure_time"],
                        timeline["paced_detection_time"])
        self.assertLess(timeline["fixed_stiffness_failure_time"],
                        timeline["paced_failure_time"])
        self.assertGreater(comparison["final_strain_fixed"],
                           comparison["final_strain_paced"])
        first = trajectories["paced"][0]
        fixed_first = trajectories["fixed_stiffness"][0]
        self.assertEqual(first["strain"], fixed_first["strain"])
        self.assertLess(float(trajectories["fixed_stiffness"][-1]["safety_margin"]), 0.0)

    def test_early_warning_window_in_the_mechanical_channel(self):
        _receipt, report, trajectories, _output = self.run_model(fixture())
        timeline = report["timeline"]
        self.assertLess(timeline["damage_onset_time"], timeline["paced_detection_time"])
        self.assertLess(timeline["paced_detection_time"], timeline["paced_failure_time"])
        self.assertGreater(timeline["cumulative_damage_at_detection"], 0.0)
        self.assertLess(report["timeline"]["final_safety_margin"], 0.0)
        # The reported margin is exactly the limit minus the measured strain.
        for row in trajectories["paced"]:
            self.assertAlmostEqual(float(row["safety_margin"]) + float(row["strain"]),
                                   0.5, places=9)

    def test_equilibrium_tracking_and_balance_residual(self):
        _receipt, report, trajectories, _output = self.run_model(fixture())
        for row in trajectories["paced"]:
            self.assertLess(abs(float(row["strain"]) - float(row["equilibrium_strain"])), 0.01)
        self.assertLess(report["balance"]["max_abs_trapezoid_residual"], 0.05)
        for name in WORLDS:
            damage = [float(row["cumulative_damage"]) for row in trajectories[name]]
            self.assertTrue(all(left <= right for left, right in zip(damage, damage[1:])))

    def test_deterministic_reproduction(self):
        config = fixture()
        _r1, _rep1, _t1, one = self.run_model(config)
        _r2, _rep2, _t2, two = self.run_model(config)
        for name in [f"trajectory_{world}.csv" for world in WORLDS] + [
                "growth_mechanics_report.json", "REPORT.md"]:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes())

    def test_control_world_with_flat_scaling_never_fails(self):
        config = fixture()
        config["growth"]["load_exponent"] = 0.5
        _receipt, report, trajectories, _output = self.run_model(config)
        self.assertTrue(report["analytic_failure"]["never_fails"])
        self.assertIsNone(report["timeline"]["paced_failure_time"])
        self.assertIsNone(report["timeline"]["paced_detection_time"])
        self.assertGreater(report["timeline"]["final_safety_margin"], 0.0)
        self.assertEqual(float(trajectories["paced"][-1]["cumulative_damage"]), 0.0)

    def test_rejects_malformed_configurations(self):
        for mutation, message in (
                (lambda c: c.update(schema_version=2), "schema_version"),
                (lambda c: c.update(fixture_notice="wrong"), "fixture_notice"),
                (lambda c: c["chamber"].update(safe_strain=0.6), "below strain_limit"),
                (lambda c: c["damage"].update(witness_rate=0.2), "different rate"),
                (lambda c: c["chamber"].update(viscosity=0.0), "viscosity"),
                (lambda c: c["growth"].pop("load_exponent"), "growth"),
                (lambda c: c["scaling"].update(stiffness_coefficient=0.0), "stiffness_coefficient"),
                (lambda c: c["dimensionless_time"].update(output_step=1e-6), "output intervals")):
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_model(config)

    def test_bundle_metadata_and_strict_verification(self):
        receipt, report, _trajectories, output = self.run_model(fixture())
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(receipt["bundle_kind"], "dimensionless_growth_mechanics_theory")
        self.assertEqual(receipt["metadata"]["structural_counterexample"], True)
        self.assertEqual(report["fixture_notice"], NOTICE)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(NOTICE, text)
        self.assertIn("## Damage witness", text)
        self.assertIn("## Limits", text)


if __name__ == "__main__":
    unittest.main()
