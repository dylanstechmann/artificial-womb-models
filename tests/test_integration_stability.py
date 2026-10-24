"""Independent analytic and event-balance checks for the dimensionless solvers."""
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError
from wombmodels.acquisition_spec import acquisition_spec
from wombmodels.bundle_verification import verify_bundle
from wombmodels.growth_mechanics import _integrate as integrate_wall
from wombmodels.growth_scaling import _integrate as integrate_growth
from wombmodels.mechanical_twin import (_coupled_variant_run, _validate as validate_mechanical,
                                       FLUIDIC_COLUMNS, mechanical_twin)
from wombmodels.numerics import output_times
from wombmodels.spatial_delivery import _integrate as integrate_chain, spatial_delivery
from wombmodels.whole_path_twin import _validate, _variant_run, whole_path_twin


ROOT = Path(__file__).resolve().parents[1]


def twin_config(duration=1.05, step=0.3):
    config = json.loads((ROOT / "examples/mechanical_twin_fixture.json").read_text(encoding="utf-8"))
    config["dimensionless_time"] = {"duration": duration, "output_step": step}
    config["interval_boundaries"] = [step]
    config["growth"].update(linear_rate=0.2, surface_exponent=1)
    config["scaling"].update(capacity_coefficient=10, demand_coefficient=1)
    config["bulk"].update(washout=0, transfer=0)
    config["internal"].update(use=0, repair=0, progression_rate=0)
    config["control"].update(gain=0, rate_limit=0, supplement_max=0)
    config["reserve"].update(initial=0, draw=0)
    config["monitor"].update(cadence=step, noise_sd=0, faults=[])
    config["outages"] = []
    for variant in config["variants"].values():
        variant["serve_rate"] = 10
    return config


def without_wall(config):
    stripped = {key: value for key, value in config.items() if key != "wall"}
    stripped["variants"] = {name: {key: value for key, value in item.items()
                                   if key != "wall_coupling"}
                            for name, item in config["variants"].items()}
    return stripped


def run_twin(config, coupled=False):
    name = "living_interface"
    if coupled:
        fluidic, wall, couplings = validate_mechanical(config)
    else:
        fluidic = _validate(without_wall(config))
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, parsed, _analysis) = fluidic
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)
    if coupled:
        return _coupled_variant_run(name, dict(parsed[name], wall_coupling=couplings[name]),
                                     shared, duration, step, boundaries, wall)[0]
    return _variant_run(name, parsed[name], shared, duration, step, boundaries)[0]


class IntegrationStabilityTests(unittest.TestCase):
    def test_output_grid_retains_decimal_and_shortened_terminal_intervals(self):
        decimal = output_times(0.3, 0.1)
        self.assertEqual(len(decimal), 4)
        self.assertEqual(decimal[-1], 0.3)
        shortened = output_times(1.05, 0.3)
        self.assertEqual(len(shortened), 5)
        self.assertAlmostEqual(shortened[-2], 0.9)
        self.assertEqual(shortened[-1], 1.05)
        self.assertTrue(all(a < b for a, b in zip(shortened, shortened[1:])))

    def test_growing_inflow_integrates_the_actual_clock_and_terminal_time(self):
        # No sink: integral of D(t)=1+g*t is t+g*t^2/2 exactly.
        for duration, step in ((1.05, 0.3), (0.3, 0.1)):
            config = twin_config(duration, step)
            for row in run_twin(config):
                time = row["dimensionless_time"]
                self.assertAlmostEqual(row["bulk_stock"], time + 0.1 * time**2, places=12)
            growth = {"linear_rate": 0.2, "surface_exponent": 1}
            scaling = {"capacity_coefficient": 10, "demand_coefficient": 1}
            exchange = {"serve_rate": 10, "washout": 0, "transfer": 0, "repair": 0}
            worlds = {name: {"transfer_efficiency": 0.5, "use": 0}
                      for name in ("internal_world", "internal_witness")}
            rows = integrate_growth(duration, step, growth, scaling, exchange, worlds)
            self.assertEqual(rows[-1]["dimensionless_time"], duration)
            for row in rows:
                time = row["dimensionless_time"]
                self.assertAlmostEqual(row["bulk_stock"], time + 0.1 * time**2, places=12)

    def test_linear_wall_load_converges_to_independent_exact_solution(self):
        growth = {"linear_rate": 0.25, "load_exponent": 1, "stiffness_exponent": 0}
        scaling = {"load_coefficient": 1, "stiffness_coefficient": 1}
        chamber = {"viscosity": 1, "strain_limit": 3, "safe_strain": 0}
        exact = 1 + 0.25 * 3 - 0.25 * (1 - math.exp(-3))
        errors = []
        for step in (0.75, 0.25, 0.0625):
            rows = integrate_wall(3, step, growth, scaling, chamber, True, 0)
            errors.append(abs(rows[-1]["strain"] - exact))
        self.assertLess(errors[1], errors[0] / 3)
        self.assertLess(errors[2], errors[1] / 8)
        self.assertLess(errors[-1], 1e-8)

    def test_growth_wall_integrates_the_shortened_terminal_step(self):
        growth = {"linear_rate": 0.25, "load_exponent": 1, "stiffness_exponent": 0}
        scaling = {"load_coefficient": 1, "stiffness_coefficient": 1}
        chamber = {"viscosity": 1, "strain_limit": 3, "safe_strain": 0}
        rows = integrate_wall(1.05, 0.3, growth, scaling, chamber, True, 0)
        exact = 1 + 0.25 * 1.05 - 0.25 * (1 - math.exp(-1.05))
        self.assertEqual(rows[-1]["dimensionless_time"], 1.05)
        self.assertLess(abs(rows[-1]["strain"] - exact), 1e-6)

    def test_stiff_coupled_wall_matches_ramp_solution_without_changing_fluidics(self):
        config = twin_config()
        config["growth"]["linear_rate"] = 0
        config["wall"].update(load_coefficient=2, stiffness_coefficient=10,
                              stiffness_exponent=0, viscosity=0.01)
        coupled = run_twin(config, coupled=True)
        uncoupled = run_twin(config)
        self.assertEqual(len(coupled), len(uncoupled))
        for row, original in zip(coupled, uncoupled):
            self.assertEqual({key: row[key] for key in FLUIDIC_COLUMNS}, original)
            time = row["dimensionless_time"]
            # F=1, stock=t; strain'=(2*(t+c)-10*strain)/.01.
            exact = 0.08 + 0.2 * time - 0.0002 * (1 - math.exp(-1000 * time))
            self.assertLess(abs(row["wall_strain"] - exact), 1e-10)
            self.assertTrue(all(math.isfinite(value) for value in row.values()))

    def test_coupled_wall_refinement_converges_to_ramp_solution(self):
        errors = []
        exact = 0.4 + 3 - (1 - math.exp(-3))
        for step in (0.75, 0.25, 0.0625):
            config = twin_config(3, step)
            config["growth"]["linear_rate"] = 0
            config["wall"].update(load_coefficient=1, stiffness_coefficient=1,
                                  stiffness_exponent=0, viscosity=1)
            # A small fluidic rate lets output-step refinement also refine
            # the cubic forcing; there is no controller/noise confounder.
            for variant in config["variants"].values():
                variant["serve_rate"] = 0
            rows = run_twin(config, coupled=True)
            errors.append(abs(rows[-1]["wall_strain"] - exact))
        self.assertLess(errors[1], errors[0] / 3)
        self.assertLess(errors[2], errors[1] / 8)
        self.assertLess(errors[-1], 1e-7)

    def test_off_grid_outage_and_reserve_depletion_preserve_supply_balance(self):
        config = twin_config(1, 0.5)
        config["growth"]["linear_rate"] = 0
        config["outages"] = [{"start": 0.15, "end": 0.85}]
        config["reserve"].update(initial=0.2, draw=1, fraction=0.5)
        rows = run_twin(config)
        # Full power .15 + backup .2*.5 + restored full power .15.
        self.assertAlmostEqual(rows[-1]["bulk_stock"], 0.4, places=12)
        self.assertEqual(rows[-1]["reserve"], 0)
        self.assertEqual(rows[1]["delivered_flux"], 0)
        self.assertEqual(rows[-1]["delivered_flux"], 1)
        coupled = run_twin(config, coupled=True)
        for row, original in zip(coupled, rows):
            self.assertEqual({key: row[key] for key in FLUIDIC_COLUMNS}, original)

    def test_outage_endpoint_does_not_leak_into_previous_rk_stage(self):
        config = twin_config(1, 0.5)
        config["growth"]["linear_rate"] = 0
        config["outages"] = [{"start": 0.5, "end": 1}]
        rows = run_twin(config)
        self.assertAlmostEqual(rows[-1]["bulk_stock"], 0.5, places=12)
        self.assertEqual(rows[1]["delivered_flux"], 0)
        self.assertEqual(rows[-1]["delivered_flux"], 1)

    def test_repair_rate_is_included_in_fluidic_stability_bound(self):
        config = twin_config(1, 0.5)
        config["growth"]["linear_rate"] = 0
        config["internal"]["repair"] = 100
        config["outages"] = [{"start": 0, "end": 1}]
        rows = run_twin(config)
        self.assertAlmostEqual(rows[-1]["cumulative_unserved"],
                               (1 - math.exp(-100)) / 100, places=12)

    def test_excessive_wall_work_is_rejected_before_fluidic_integration_or_publication(self):
        config = twin_config()
        config["wall"].update(stiffness_coefficient=1000, viscosity=1e-6)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            output = Path(temp) / "out"
            with patch("wombmodels.whole_path_twin._rk4_step") as rk:
                with self.assertRaisesRegex(InputError, "Wall integration exceeds"):
                    mechanical_twin(path, output)
                rk.assert_not_called()
            self.assertFalse(output.exists())

    def test_fluidic_budget_rejects_before_integration_or_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(without_wall(twin_config())), encoding="utf-8")
            output = Path(temp) / "out"
            with patch("wombmodels.whole_path_twin.MAX_TOTAL_SUBSTEPS", 1):
                with patch("wombmodels.whole_path_twin._rk4_step") as rk:
                    with self.assertRaisesRegex(InputError, "Integration exceeds"):
                        whole_path_twin(path, output)
                    rk.assert_not_called()
            self.assertFalse(output.exists())

    def test_nonfinite_integration_fails_without_publishing_a_partial_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(without_wall(twin_config())), encoding="utf-8")
            output = Path(temp) / "out"
            with patch("wombmodels.whole_path_twin._rk4_step", return_value=[float("nan")] * 7):
                with self.assertRaisesRegex(InputError, "nonfinite state"):
                    whole_path_twin(path, output)
            self.assertFalse(output.exists())

    def test_spatial_chain_integrates_shortened_and_decimal_terminal_steps(self):
        chain = [{"loss": 1, "transfer": 0, "use": 0}]
        for duration, step in ((1.05, 0.3), (0.3, 0.1)):
            rows = integrate_chain(1, chain, duration, step)
            self.assertEqual(rows[-1]["dimensionless_time"], duration)
            self.assertLess(abs(rows[-1]["compartment_1"] - (1 - math.exp(-duration))), 3e-6)

    def test_hidden_stiff_compartment_does_not_create_an_observed_prefix_signal(self):
        config = json.loads((ROOT / "examples/spatial_delivery_fixture.json").read_text(encoding="utf-8"))
        config["witness_chain"][-1]["use"] = 100
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            output = Path(temp) / "out"
            spatial_delivery(path, output)
            report = json.loads((output / "spatial_delivery_report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["witness_comparison"]["observed_series_identical"])
            self.assertTrue(report["witness_comparison"]["observed_receipt_identical"])
            self.assertTrue(report["integration"]["shared_chain_substeps"])
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_acquisition_surveillance_counts_the_shortened_final_interval(self):
        config = json.loads((ROOT / "examples/acquisition_spec_fixture.json").read_text(encoding="utf-8"))
        config["dimensionless_time"]["duration"] = 40.25
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            output = Path(temp) / "out"
            acquisition_spec(path, output)
            report = json.loads((output / "acquisition_spec_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["timing"]["surveillance_timepoints"], 82)
            self.assertTrue(report["source_twin"]["one_way_coupling_verified"])
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])


if __name__ == "__main__":
    unittest.main()
