import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from itertools import combinations

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.acquisition_spec import OBSERVABLES, _channel_requirements, acquisition_spec
from wombmodels.mechanical_twin import mechanical_twin
from wombmodels.platform_requirements import platform_requirements


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

    def channel_plan(self, post_values, pre_values=None):
        events = []
        names = ("a", "b", "c")
        for handoff, values in enumerate(post_values, 1):
            for name, value in zip(names, values):
                event = dict.fromkeys(OBSERVABLES, 0.0)
                event.update(variant=name, phase="post", handoff=handoff, wall_strain=value)
                events.append(event)
        if pre_values is not None:
            for name, value in zip(names, pre_values):
                event = dict.fromkeys(OBSERVABLES, 0.0)
                event.update(variant=name, phase="pre", handoff=1, wall_strain=value)
                events.append(event)
        rows, pairs = _channel_requirements(events, list(combinations(names, 2)), 0.1)
        return next(row for row in rows if row["channel"] == "wall_strain"), pairs

    def test_qualification_waits_until_every_pair_separates_at_once(self):
        channel, pairs = self.channel_plan([(1, 1, 2), (1, 2, 3)])
        self.assertEqual(pairs[("a", "c", "wall_strain")], 1)
        self.assertEqual(pairs[("a", "b", "wall_strain")], 2)
        self.assertEqual(channel["first_separated_handoff"], 2)
        self.assertTrue(channel["required"])

    def test_first_ever_separation_cannot_substitute_for_a_common_handoff(self):
        # Every pair differs at some point, but at each handoff two variants coincide.
        channel, pairs = self.channel_plan([(1, 1, 2), (2, 1, 1), (1, 2, 1)])
        self.assertTrue(all(value is not None for key, value in pairs.items()
                            if key[2] == "wall_strain"))
        self.assertEqual(channel["pairs_separated_ever"], 3)
        self.assertIsNone(channel["first_separated_handoff"])
        self.assertFalse(channel["required"])
        self.assertEqual(channel["excluded_reason"], "no_common_separated_handoff")

    def test_partial_separation_is_not_reported_as_never_separating(self):
        channel, _pairs = self.channel_plan([(1, 1, 2)])
        self.assertEqual(channel["pairs_separated_ever"], 2)
        self.assertEqual(channel["variant_pair_count"], 3)
        self.assertEqual(channel["excluded_reason"], "separates_only_some_pairs")
        self.assertFalse(channel["required"])

    def test_pre_handoff_separation_does_not_qualify_post_handoff_measurements(self):
        channel, _pairs = self.channel_plan([(1, 1, 1)], pre_values=(1, 2, 3))
        self.assertEqual(channel["excluded_reason"], "never_separates_any_pair")
        self.assertFalse(channel["required"])

    def test_no_discrimination_rejects_without_publishing_a_bundle(self):
        config = fixture()
        for variant in config["variants"].values():
            variant.update(serve_rate=1.0, internal_efficiency=0.5, wall_coupling=0.7)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            output = Path(temp) / "out"
            with self.assertRaisesRegex(InputError, "common handoff"):
                acquisition_spec(path, output)
            self.assertFalse(output.exists())

    def test_zero_reference_noise_has_no_multiplier_floor_and_needs_one_unit(self):
        config = fixture()
        config["monitor"]["noise_sd"] = 0
        _receipt, report, output = self.run_spec(config)
        self.assertEqual(report["resolution"]["floor_status"],
                         "not_applicable_zero_reference_noise")
        self.assertTrue(all(value is None for value
                            in report["resolution"]["channel_floor_multiplier"].values()))
        for row in report["noise_floor_sweep"]:
            self.assertTrue(row["analytic_separated_with_margin"])
            self.assertEqual(row["empirical_reliability"], 1.0)
        for channel in report["units_per_cohort"].values():
            self.assertTrue(all(row["analytic_units"] == 1 and row["confirmed"]
                                for row in channel["sweep"]))
        self.assertIn("floor not applicable", (output / "REPORT.md").read_text(encoding="utf-8"))
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_failed_seed_confirmation_is_reported_as_unconfirmed(self):
        config = fixture()
        config["spec"]["detection_sigma"] = 0.1
        _receipt, report, output = self.run_spec(config)
        failed = [row for data in report["units_per_cohort"].values() for row in data["sweep"]
                  if not row["capped"] and not row["confirmed"]]
        self.assertTrue(failed, "the weak guard must exercise failed empirical confirmation")
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("unconfirmed (reliability", text)
        for row in failed:
            self.assertIn(f"N={row['analytic_units']}, unconfirmed "
                          f"(reliability {row['empirical_reliability']:.6g})", text)

    def test_channel_specific_handoffs_use_their_own_twin_observations(self):
        config = fixture()
        config["interval_boundaries"] = [8, 10.5, 20]
        config["variants"]["staged"]["wall_coupling"] = 0.5
        _receipt, report, output = self.run_spec(config)
        timing = report["timing"]
        self.assertEqual(timing["channel_handoffs"],
                         {"wall_strain": 2, "deep_receipt_rate": 1, "progression": 1})
        self.assertEqual(timing["first_separated_handoff"], 1)
        self.assertEqual(timing["first_separated_time"], 8.0)
        self.assertEqual(timing["plan_complete_handoff"], 2)
        self.assertEqual(timing["plan_complete_time"], 10.5)
        self.assertEqual(timing["discrimination_timepoints"], 22)
        # Check against the source twin's published observations, not just
        # the acquisition report's own effect/margin arithmetic.
        source_config = {key: value for key, value in config.items() if key != "spec"}
        source_path = output.parent / "twin.json"
        source_path.write_text(json.dumps(source_config), encoding="utf-8")
        twin = output.parent / "twin"
        mechanical_twin(source_path, twin)
        events = {(row["variant"], int(row["handoff"])): row
                  for row in self.rows(twin, "boundary_events.csv") if row["phase"] == "post"}
        for channel, pairs in report["resolution"]["pairs"].items():
            handoff = timing["channel_handoffs"][channel]
            for label, values in pairs.items():
                first, second = label.split("|")
                a = float(events[(first, handoff)][channel])
                b = float(events[(second, handoff)][channel])
                expected_margin = abs(a - b) - 0.1 * max(abs(a), abs(b), 1e-12)
                self.assertEqual(values["effect"], abs(a - b))
                self.assertEqual(values["margin"], expected_margin)
                self.assertGreater(values["margin"], 0)
        worksheet = output.parent / "worksheet"
        platform_requirements(ROOT / "examples/platform_requirements_fixture.json", output, worksheet)
        consumed = json.loads((worksheet / "platform_requirements_report.json").read_text(encoding="utf-8"))
        for row in consumed["line_items"]:
            self.assertEqual(row["selected_handoff"], timing["channel_handoffs"][row["channel"]])
            self.assertEqual(row["selected_time"], timing["channel_times"][row["channel"]])
            self.assertEqual(row["discrimination_timepoints"], 22)
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
        self.assertTrue(verify_bundle(worksheet, strict=True)["bytes_verified"])

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
