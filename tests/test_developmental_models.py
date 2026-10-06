import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.developmental_models import simulate_mechanics, simulate_transport

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

    def test_mechanics_reports_piecewise_response_and_elastic_alternative(self):
        receipt, output = self.run_model(simulate_mechanics, self.config("mechanics_fixture.json"), "mechanics")
        report = json.loads((output / "mechanics_report.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["bundle_kind"], "dimensionless_mechanics_theory")
        self.assertGreater(report["outputs"]["peak_strain"], 0)
        self.assertAlmostEqual(report["outputs"]["dimensionless_relaxation_time"], 0.5)
        self.assertIn("elasticity", report["alternative_model"]["equation"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertTrue((output / "elastic_reference.csv").is_file())


if __name__ == "__main__":
    unittest.main()
