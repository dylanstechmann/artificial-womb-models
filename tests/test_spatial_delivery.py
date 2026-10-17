import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.spatial_delivery import _equilibrium, spatial_delivery


ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/spatial_delivery_fixture.json").read_text(encoding="utf-8"))


class SpatialDeliveryTests(unittest.TestCase):
    def run_model(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = spatial_delivery(config_path, output)
        report = json.loads((output / "spatial_delivery_report.json").read_text(encoding="utf-8"))
        trajectories = {}
        for name in ("configured_trajectory.csv", "witness_trajectory.csv"):
            with (output / name).open(newline="", encoding="utf-8") as stream:
                trajectories[name] = list(csv.DictReader(stream))
        with (output / "receipt_summary.csv").open(newline="", encoding="utf-8") as stream:
            summary = list(csv.DictReader(stream))
        return receipt, report, trajectories, summary, output

    def test_observed_series_identical_and_hidden_dimension_differs(self):
        _receipt, report, trajectories, _summary, _output = self.run_model(fixture())
        comparison = report["witness_comparison"]
        self.assertTrue(comparison["observed_series_identical"])
        self.assertEqual(sorted(comparison["max_abs_observed_differences"].values()), [0.0, 0.0])
        # The hidden segment is longer in the witness world: even the number of
        # unobserved compartments is unidentifiable from the boundary.
        self.assertEqual(report["compartments"], {"chain": 3, "witness_chain": 4})
        self.assertEqual(comparison["hidden_segment_lengths"], {"chain": 1, "witness_chain": 2})
        configured = trajectories["configured_trajectory.csv"]
        witness = trajectories["witness_trajectory.csv"]
        self.assertEqual(len(configured), len(witness))
        for left, right in zip(configured, witness):
            self.assertEqual(left["compartment_1"], right["compartment_1"])
            self.assertEqual(left["compartment_2"], right["compartment_2"])
            self.assertNotIn("compartment_4", left)
            self.assertIn("compartment_4", right)

    def test_internal_receipt_differs_below_observation(self):
        _receipt, report, _trajectories, summary, _output = self.run_model(fixture())
        comparison = report["witness_comparison"]
        self.assertGreater(comparison["relative_internal_receipt_difference"], 0.5)
        self.assertTrue(comparison["observed_receipt_identical"])
        self.assertEqual(comparison["observed_receipt_configured"],
                        comparison["observed_receipt_witness"])
        observed = [row for row in summary if row["observed"] == "True"]
        hidden = [row for row in summary if row["observed"] == "False"]
        self.assertEqual(len(observed), 4)
        self.assertEqual(len(hidden), 3)
        for position in (1, 2):
            rows = [row for row in observed if row["compartment"] == str(position)]
            self.assertEqual(rows[0]["final_stock"], rows[1]["final_stock"])
            self.assertEqual(rows[0]["cumulative_receipt"], rows[1]["cumulative_receipt"])
        configured_hidden = next(row for row in hidden if row["world"] == "chain")
        witness_hidden = [row for row in hidden if row["world"] == "witness_chain"]
        self.assertGreater(float(configured_hidden["cumulative_receipt"]),
                            sum(float(row["cumulative_receipt"]) for row in witness_hidden))

    def test_observed_receipt_invariance_and_cut_point(self):
        _receipt, report, _trajectories, _summary, _output = self.run_model(fixture())
        self.assertEqual(report["observed_depth"], 2)
        self.assertEqual(report["cut_point"]["resolved_compartments"], 2)
        self.assertIn("exchangeable", report["cut_point"]["exchangeable_below"])
        self.assertIn("number of hidden compartments", report["cut_point"]["exchangeable_below"])
        self.assertIn("transfer_", report["structural_identity"])

    def test_equilibrium_matches_closed_form(self):
        config = fixture()
        _receipt, report, _trajectories, _summary, _output = self.run_model(config)
        stocks = _equilibrium(config["boundary"]["excitation"], config["chain"])
        self.assertAlmostEqual(stocks[0], 1.0 / 1.7, places=12)
        self.assertAlmostEqual(stocks[1], 1.2 * (1.0 / 1.7) / 1.4, places=12)
        self.assertAlmostEqual(stocks[2], 0.9 * (1.2 * (1.0 / 1.7) / 1.4) / 1.6, places=12)
        self.assertEqual(report["equilibrium"]["closed_form_stocks"]["chain"], stocks)
        # The fast configured world sits at its closed-form equilibrium by the
        # final row; the slow hidden witness segment is nowhere near its own.
        self.assertLess(report["equilibrium"]["max_abs_final_deviation"]["chain"], 1e-3)
        self.assertGreater(report["equilibrium"]["max_abs_final_deviation"]["witness_chain"], 0.1)

    def test_balance_residual_small_and_deterministic_reproduction(self):
        config = fixture()
        _receipt, report, _trajectories, _summary, output_one = self.run_model(config)
        for world in ("chain", "witness_chain"):
            self.assertLess(report["balance"][world]["max_abs_trapezoid_residual"], 0.05)
        _r2, _rep2, _traj2, _sum2, output_two = self.run_model(config)
        for name in ("configured_trajectory.csv", "witness_trajectory.csv",
                     "receipt_summary.csv", "spatial_delivery_report.json", "REPORT.md"):
            self.assertEqual((output_one / name).read_bytes(), (output_two / name).read_bytes())

    def test_rejects_malformed_configurations(self):
        for mutation, message in (
                (lambda c: c.update(schema_version=2), "schema_version"),
                (lambda c: c.update(fixture_notice="wrong"), "fixture_notice"),
                (lambda c: c.update(observed_depth=3), "hidden segment"),
                (lambda c: c["chain"].__setitem__(2, {"loss": 0.1, "transfer": 0.5, "use": 1.5}),
                 "terminal compartment transfer"),
                (lambda c: c["witness_chain"][0].update(loss=0.5), "observed prefix"),
                (lambda c: c["witness_chain"].__setitem__(
                    3, {"loss": 0.05, "transfer": 0.2, "use": 0.05}),
                 "terminal compartment transfer"),
                (lambda c: (c["chain"].pop(), c["chain"].pop()), "list of 2"),
                (lambda c: c["chain"][1].pop("use"), "compartment 2 must contain")):
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_model(config)

    def test_bundle_metadata_and_strict_verification(self):
        receipt, report, _trajectories, _summary, output = self.run_model(fixture())
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(receipt["bundle_kind"], "dimensionless_spatial_delivery_theory")
        self.assertEqual(receipt["metadata"]["structural_counterexample"], True)
        self.assertEqual(report["fixture_notice"], NOTICE)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(NOTICE, text)
        self.assertIn("## Cut point", text)


if __name__ == "__main__":
    unittest.main()
