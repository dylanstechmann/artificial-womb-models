import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.acquisition_spec import acquisition_spec


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("wall_strain", "deep_receipt_rate", "progression")
EXCLUDED_NEVER = ("delivered_flux", "served_fraction", "bulk_stock", "cumulative_unserved")
PAIRS = ("living_interface|staged", "living_interface|synthetic", "staged|synthetic")


def fixture():
    return json.loads((ROOT / "examples/acquisition_spec_fixture.json").read_text(encoding="utf-8"))


class AcquisitionSpecTests(unittest.TestCase):
    def run_spec(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = acquisition_spec(config_path, output)
        report = json.loads((output / "acquisition_spec_report.json").read_text(encoding="utf-8"))
        return receipt, report, output

    def rows(self, output, name):
        with (output / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def test_required_channels_are_computed_from_the_run(self):
        _receipt, report, _output = self.run_spec(fixture())
        by_channel = {row["channel"]: row for row in report["channel_requirements"]}
        required = [row["channel"] for row in report["channel_requirements"] if row["required"]]
        self.assertEqual(required, list(REQUIRED))
        for channel in REQUIRED:
            self.assertTrue(by_channel[channel]["instrumentable"])
            self.assertEqual(by_channel[channel]["first_separated_handoff"], 1)
        for channel in EXCLUDED_NEVER:
            self.assertEqual(by_channel[channel]["excluded_reason"], "never_separates_any_pair")
            self.assertIsNone(by_channel[channel]["first_separated_handoff"])
            self.assertFalse(by_channel[channel]["separates_all_pairs"])
        self.assertEqual(by_channel["wall_damage"]["excluded_reason"],
                         "derived_not_directly_instrumentable")
        self.assertFalse(by_channel["wall_damage"]["required"])
        # The pairwise grid agrees: required channels separate every pair at handoff 1.
        for row in report["pairwise_first_separated"]:
            if row["channel"] in REQUIRED:
                self.assertEqual(row["first_separated_handoff"], 1)
            elif row["channel"] in EXCLUDED_NEVER:
                self.assertIsNone(row["first_separated_handoff"])

    def test_analytic_floor_reproduces_from_the_report_numbers(self):
        _receipt, report, _output = self.run_spec(fixture())
        resolution = report["resolution"]
        noise = resolution["reference_noise_sd"]
        sigma = resolution["detection_sigma"]
        tolerance = resolution["separation_tolerance"]
        for channel, pairs in resolution["pairs"].items():
            self.assertEqual(sorted(pairs), list(PAIRS))
            for label, values in pairs.items():
                self.assertAlmostEqual(values["margin"],
                                       values["effect"] - tolerance * values["scale"], places=12)
                self.assertAlmostEqual(values["floor_multiplier"],
                                       values["margin"] / (sigma * math.sqrt(2) * noise),
                                       places=12)
            binding = report["binding_pair"][channel]
            self.assertEqual(binding["pair"],
                             min(pairs, key=lambda label: pairs[label]["margin"]))
            self.assertEqual(resolution["channel_floor_multiplier"][channel],
                            pairs[binding["pair"]]["floor_multiplier"])

    def test_floor_guard_predicts_the_empirical_sweep(self):
        _receipt, report, _output = self.run_spec(fixture())
        confidence = report["spec_parameters"]["cohort_confidence"]
        sweep = report["noise_floor_sweep"]
        self.assertEqual(len(sweep), len(REQUIRED) * len(PAIRS)
                         * len(report["spec_parameters"]["noise_multipliers"]))
        for row in sweep:
            floor = row["analytic_floor_multiplier"]
            self.assertEqual(row["analytic_separated_with_margin"],
                             floor is not None and row["multiplier"] <= floor)
            # The k-sigma guard is conservative: an analytic margin implies empirical separation.
            if row["analytic_separated_with_margin"]:
                self.assertTrue(row["separated_at_confidence"], row)
        quietest = min(report["spec_parameters"]["noise_multipliers"])
        for row in sweep:
            if row["multiplier"] == quietest:
                self.assertTrue(row["separated_at_confidence"])
        # The binding pair loses single-unit separation at 4x reference noise.
        binding = next(row for row in sweep
                       if row["channel"] == "wall_strain" and row["pair"] == "staged|synthetic"
                       and row["multiplier"] == 4.0)
        self.assertFalse(binding["analytic_separated_with_margin"])
        self.assertLess(binding["empirical_reliability"], confidence)

    def test_units_per_cohort_confirmed_at_every_noise_level(self):
        _receipt, report, _output = self.run_spec(fixture())
        sigma = report["spec_parameters"]["detection_sigma"]
        noise = report["resolution"]["reference_noise_sd"]
        self.assertGreater(noise, 0.0)
        for channel, data in report["units_per_cohort"].items():
            self.assertEqual(data["binding_pair"], report["binding_pair"][channel]["pair"])
            previous_units = 0
            for row in data["sweep"]:
                expected = max(1, math.ceil(2.0 * (sigma * row["multiplier"] * noise
                                                  / data["margin"]) ** 2))
                self.assertEqual(row["analytic_units"], expected)
                self.assertGreaterEqual(row["analytic_units"], previous_units)
                previous_units = row["analytic_units"]
                # Analytic cohort sizes are confirmed empirically whenever not capped.
                self.assertTrue(row["capped"] or row["confirmed"], row)

    def test_timing_and_horizons(self):
        _receipt, report, _output = self.run_spec(fixture())
        timing = report["timing"]
        self.assertEqual(timing["sampling_cadence"], 0.5)
        self.assertEqual(timing["monitor_cadence"], 1.0)
        self.assertEqual(timing["first_separated_handoff"], 1)
        self.assertEqual(timing["first_separated_time"], 10.0)
        self.assertEqual(timing["discrimination_timepoints"], 21)
        self.assertEqual(timing["surveillance_timepoints"], 81)
        self.assertAlmostEqual(timing["capacity_crossover_time"], 14.9625, places=3)
        self.assertEqual(timing["wall_limit_crossing_times"],
                         {"living_interface": 14.0, "staged": 1.5, "synthetic": 0.5})

    def test_dmp_contract_mapping(self):
        _receipt, report, _output = self.run_spec(fixture())
        contract = report["dmp_contract"]
        self.assertFalse(contract["D_delivery_at_boundary"]["discriminates_allocations"])
        self.assertTrue(contract["M_internal_receipt"]["discriminates_allocations"])
        self.assertTrue(contract["P_progression"]["discriminates_allocations"])
        self.assertTrue(contract["W_chamber_wall_mechanics"]["discriminates_allocations"])
        self.assertEqual(contract["D_delivery_at_boundary"]["channels"],
                         ["delivered_flux", "served_fraction", "bulk_stock"])
        self.assertEqual(contract["M_internal_receipt"]["channels"],
                         ["deep_receipt_rate", "cumulative_unserved"])
        self.assertEqual(report["source_twin"]["one_way_coupling_verified"], True)
        self.assertEqual(report["source_twin"]["n_variants"], 3)
        self.assertEqual(report["source_twin"]["n_intervals"], 4)
        self.assertEqual(report["source_twin"]["result_kind"], "dimensionless_mechanical_twin")

    def test_deterministic_reproduction(self):
        config = fixture()
        _r1, _rep1, one = self.run_spec(config)
        _r2, _rep2, two = self.run_spec(config)
        names = ["input_config.json", "channel_requirements.csv", "pairwise_first_separated.csv",
                 "noise_floor_sweep.csv", "units_per_cohort.csv",
                 "acquisition_spec_report.json", "REPORT.md"]
        for name in names:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes(), name)

    def test_rejects_malformed_configurations(self):
        for mutation, message in (
                (lambda c: c.pop("spec"), "config"),
                (lambda c: c["spec"].pop("detection_sigma"), "spec"),
                (lambda c: c["spec"].update(cohort_confidence=1.0), "below 1"),
                (lambda c: c["spec"].update(confirm_seeds=0), "integer in"),
                (lambda c: c["spec"].update(confirm_seeds="x"), "integer in"),
                (lambda c: c["spec"].update(noise_multipliers=[]), "1 to 12"),
                (lambda c: c["spec"].update(noise_multipliers=[4, 0.5]), "ascending"),
                (lambda c: c["spec"].update(noise_multipliers=[0]), "noise multiplier"),
                (lambda c: c["spec"].update(detection_sigma=0.0), "detection_sigma"),
                (lambda c: c["wall"].pop("viscosity"), "wall")):
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_spec(config)

    def test_bundle_metadata_and_strict_verification(self):
        receipt, report, output = self.run_spec(fixture())
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(receipt["bundle_kind"], "dimensionless_acquisition_spec")
        self.assertEqual(receipt["metadata"]["n_required_channels"], 3)
        self.assertEqual(receipt["metadata"]["n_variants"], 3)
        self.assertEqual(report["fixture_notice"], NOTICE)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(NOTICE, text)
        self.assertIn("## Required channels (procurement)", text)
        self.assertIn("## Resolution and cohort sweep", text)
        self.assertIn("## Limits", text)
        self.assertEqual(len(self.rows(output, "channel_requirements.csv")), 8)
        self.assertEqual(len(self.rows(output, "pairwise_first_separated.csv")), 24)
        self.assertEqual(len(self.rows(output, "noise_floor_sweep.csv")), 45)
        self.assertEqual(len(self.rows(output, "units_per_cohort.csv")), 15)


if __name__ == "__main__":
    unittest.main()