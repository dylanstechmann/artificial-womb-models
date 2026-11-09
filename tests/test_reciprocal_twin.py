import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.reciprocal_twin import reciprocal_twin

ROOT = Path(__file__).resolve().parents[1]


class ReciprocalTwinTests(unittest.TestCase):
    def run_model(self, config):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        config_path, out = base / "config.json", base / "bundle"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        receipt = reciprocal_twin(config_path, out)
        report = json.loads((out / "reciprocal_twin_report.json").read_text())
        return receipt, report, out

    def test_damage_feedback_separates_boundary_bulk(self):
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        receipt, report, out = self.run_model(config)
        self.assertEqual(receipt["bundle_kind"], "dimensionless_reciprocal_twin")
        self.assertTrue(any(pair["first_separated"]["bulk_stock"] is not None
                            for pair in report["pairwise_separation"]))
        for pair in report["pairwise_separation"]:
            self.assertEqual(pair["feedback_only_first_separated"], {"bulk_stock": 2})
            self.assertIsNone(pair["zero_feedback_first_separated"]["bulk_stock"])
            self.assertEqual(pair["first_separated"]["wall_strain"],
                             pair["zero_feedback_first_separated"]["wall_strain"])
        self.assertTrue(verify_bundle(out, strict=True)["bytes_verified"])
        self.assertIn(NOTICE, (out / "REPORT.md").read_text())
        config["feedback"]["leak_coefficient"] = 0
        _, baseline, _ = self.run_model(config)
        self.assertTrue(all(not pair["boundary_observables_ever_separate"]
                            for pair in baseline["pairwise_separation"]))

    def test_zero_feedback_does_not_change_fluidic_or_wall_path(self):
        from wombmodels.mechanical_twin import mechanical_twin
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        config["feedback"]["leak_coefficient"] = 0
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            reciprocal_config = base / "reciprocal.json"
            mechanical_config = base / "mechanical.json"
            reciprocal_config.write_text(json.dumps(config))
            mechanical = {k: v for k, v in config.items() if k != "feedback"}
            mechanical_config.write_text(json.dumps(mechanical))
            reciprocal_twin(reciprocal_config, base / "r")
            mechanical_twin(mechanical_config, base / "m")
            for name in config["variants"]:
                with (base / "r" / f"trajectory_{name}.csv").open(newline="") as f:
                    actual = list(csv.DictReader(f))
                with (base / "m" / f"trajectory_{name}.csv").open(newline="") as f:
                    expected = list(csv.DictReader(f))
                for column in expected[0]:
                    self.assertEqual([r[column] for r in actual], [r[column] for r in expected])

    def test_constant_damage_leak_matches_independent_exponential(self):
        from wombmodels.reciprocal_twin import _validate
        from wombmodels.whole_path_twin import _rk4_step
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        parsed, _wall, _couplings, coefficient = _validate(config)
        growth, scaling, bulk, internal, control, reserve, outages = parsed[3:10]
        variant = dict(parsed[14]["living_interface"], wall_damage_leak=coefficient,
                       wall_damage=0.7)
        parameters = (growth, scaling, bulk, internal, dict(control, gain=0),
                      reserve, outages, variant)
        # Isolate a nonzero stock under zero delivery/supplement and constant
        # damage. This checks the leak derivative, not just a zero-stock case.
        initial = [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        expected = 2.0 * math.exp(-(bulk["washout"] + bulk["transfer"]
                                    + coefficient * 0.7))
        errors = []
        for count in (10, 20, 40):
            state = initial[:]
            for index in range(count):
                state = _rk4_step(index / count, state, 1 / count, parameters,
                                  bulk["target"], operating=(0.0, 0.0))
            errors.append(abs(state[1] - expected))
        self.assertLess(errors[-1], 1e-7)
        self.assertLess(errors[1], errors[0] / 10)
        self.assertLess(errors[2], errors[1] / 10)

    def test_full_reciprocal_system_refinement_is_first_order(self):
        from wombmodels.reciprocal_twin import _FeedbackWall, _validate
        from wombmodels.whole_path_twin import _rk4_step, _variant_run
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        config["dimensionless_time"] = {"duration": 1.0, "output_step": 0.5}
        config["interval_boundaries"] = [0.5]
        config["growth"]["linear_rate"] = 0.0
        config["control"].update(gain=0.0, rate_limit=0.0, supplement_max=0.0)
        config["monitor"].update(noise_sd=0.0, cadence=0.5, faults=[])
        config["outages"] = []
        config["wall"].update(safe_strain=0.0, damage_rate=100.0,
                              stiffness_coefficient=3.0, viscosity=0.8)
        config["feedback"]["leak_coefficient"] = 10.0
        parsed, wall, couplings, coefficient = _validate(config)
        (duration, step, boundaries, growth, scaling, bulk, internal, control,
         reserve, outages, cadence, noise_sd, seed, faults, variants, _analysis) = parsed
        shared = (growth, scaling, bulk, internal, control, reserve, outages,
                  cadence, noise_sd, seed, faults)
        for name in sorted(variants):
            with self.subTest(variant=name):
                finals = []
                for refinement in (1, 2, 4, 8):
                    variant = dict(variants[name], wall_coupling=couplings[name],
                                   wall_damage_leak=coefficient, wall_damage=0.0,
                                   substep_refinement=refinement)
                    observer = _FeedbackWall(variant, growth, scaling, wall, duration)
                    rows, _, _ = _variant_run(name, variant, shared, duration, step,
                                              boundaries, observer=observer)
                    finals.append((rows[-1]["bulk_stock"], rows[-1]["wall_damage"]))
                errors = [abs(a - b) + abs(c - d)
                          for (a, c), (b, d) in zip(finals, finals[1:])]
                self.assertLess(errors[1], errors[0] * 0.6)
                self.assertLess(errors[2], errors[1] * 0.6)
                self.assertLess(errors[-1], 1e-4)

    def test_refinement_applies_to_event_free_segments(self):
        from unittest.mock import patch
        from wombmodels.reciprocal_twin import _FeedbackWall, _validate
        from wombmodels.whole_path_twin import _rk4_step, _variant_run
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        parsed, wall, couplings, coefficient = _validate(config)
        (duration, step, boundaries, growth, scaling, bulk, internal, control,
         reserve, outages, cadence, noise_sd, seed, faults, variants, _analysis) = parsed
        shared = (growth, scaling, bulk, internal, control, reserve, outages,
                  cadence, noise_sd, seed, faults)
        name = "living_interface"
        variant = dict(variants[name], wall_coupling=couplings[name],
                       wall_damage_leak=coefficient, wall_damage=0.0,
                       substep_refinement=2)
        observer = _FeedbackWall(variant, growth, scaling, wall, duration)
        with patch("wombmodels.whole_path_twin._rk4_step", wraps=_rk4_step) as rk:
            _variant_run(name, variant, shared, duration, step, boundaries, observer)
            spans = [call.args[2] for call in rk.call_args_list]
        self.assertTrue(all(span <= step / 2 for span in spans))
        self.assertTrue(any(span < step / 10 for span in spans))

    def test_excessive_reciprocal_work_fails_without_publication(self):
        from unittest.mock import patch
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            path = base / "config.json"
            output = base / "bundle"
            path.write_text(json.dumps(config), encoding="utf-8")
            with patch("wombmodels.whole_path_twin.MAX_TOTAL_SUBSTEPS", 1):
                with self.assertRaisesRegex(InputError, "Integration exceeds"):
                    reciprocal_twin(path, output)
            self.assertFalse(output.exists())

    def test_deterministic_publication(self):
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        _, _, first = self.run_model(config)
        _, _, second = self.run_model(config)
        for path in first.iterdir():
            if path.name != "receipt.json":
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes(), path.name)

    def test_rejects_malformed_configurations(self):
        mutations = (
            (lambda c: c["feedback"].update(leak_coefficient=101), "leak_coefficient"),
            (lambda c: c["feedback"].update(leak_coefficient=-1), "leak_coefficient"),
            (lambda c: c["feedback"].update(leak_coefficient=True), "leak_coefficient"),
            (lambda c: c["feedback"].update(extra=1), "feedback"),
            (lambda c: c.pop("feedback"), "feedback"),
            (lambda c: c["wall"].update(damage_rate=101), "damage_rate"),
            (lambda c: c["wall"].update(safe_strain=0.8), "safe_strain"),
            (lambda c: c["variants"]["staged"].pop("wall_coupling"), "wall_coupling"),
            (lambda c: c["bulk"].update(washout=101), "washout"),
            (lambda c: c["monitor"].update(noise_sd=-1), "noise_sd"),
            (lambda c: c["bulk"].update(washout=0, transfer=0), "positive bulk loss"),
        )
        for mutation, message in mutations:
            with self.subTest(message=message):
                config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_model(config)


if __name__ == "__main__":
    unittest.main()