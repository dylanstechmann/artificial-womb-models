import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.exchange import simulate
from wombmodels.identifiability import analyze

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/exchange_fixture.json").read_text())


class IdentifiabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = fixture()
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.simulation = self.root / "simulation"
        simulate(self.config_path, self.simulation)

    def test_report_uses_scheduled_readings_and_keeps_biological_scope_false(self):
        output = self.root / "analysis"
        analyze(self.config_path, self.simulation / "trajectory.csv", output)
        report = json.loads((output / "observability_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["n_scheduled_readings"], 49)
        self.assertEqual(report["observation_contract"].split(";")[0],
                         "Only scheduled sensor readings and the modeled power-source intervals are used")
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        self.assertIn("trajectory_sha256", json.loads((output / "source_manifest.json").read_text()))

    def test_trajectory_from_a_different_sampling_schedule_is_rejected(self):
        mismatched = fixture()
        mismatched["dimensionless_time"]["output_step"] = 0.3
        mismatched_path = self.root / "mismatched.json"
        mismatched_path.write_text(json.dumps(mismatched), encoding="utf-8")
        with self.assertRaisesRegex(InputError, "cadence"):
            analyze(mismatched_path, self.simulation / "trajectory.csv", self.root / "rejected")
        self.assertFalse((self.root / "rejected").exists())


if __name__ == "__main__":
    unittest.main()
