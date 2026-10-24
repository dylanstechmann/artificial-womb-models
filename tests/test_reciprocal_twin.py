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

    def test_deterministic_publication(self):
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        _, _, first = self.run_model(config)
        _, _, second = self.run_model(config)
        for path in first.iterdir():
            if path.name != "receipt.json":
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes(), path.name)

    def test_rejects_bad_feedback(self):
        config = json.loads((ROOT / "examples/reciprocal_twin_fixture.json").read_text())
        config["feedback"]["leak_coefficient"] = 101
        with self.assertRaises(InputError):
            self.run_model(config)


if __name__ == "__main__":
    unittest.main()