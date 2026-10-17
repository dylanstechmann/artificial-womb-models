import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.growth_scaling import analytic_crossover, growth_scaling


ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/growth_scaling_fixture.json").read_text(encoding="utf-8"))


class GrowthScalingTests(unittest.TestCase):
    def run_model(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = growth_scaling(config_path, output)
        report = json.loads((output / "growth_scaling_report.json").read_text(encoding="utf-8"))
        with (output / "trajectory.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        return receipt, report, rows, output

    def test_crossover_matches_analytic_margin(self):
        config = fixture()
        _receipt, report, rows, _output = self.run_model(config)
        growth = {"linear_rate": config["growth"]["linear_rate"],
                  "surface_exponent": config["growth"]["surface_exponent"]}
        scaling = {"capacity_coefficient": config["scaling"]["capacity_coefficient"],
                   "demand_coefficient": config["scaling"]["demand_coefficient"]}
        analytic = analytic_crossover(growth, scaling)
        self.assertAlmostEqual(analytic["crossover_size"], 1.5 ** 3, places=12)
        self.assertAlmostEqual(analytic["crossover_time"], (1.5 ** 3 - 1) / 0.12, places=12)
        self.assertFalse(analytic["margin_never_closes"])
        self.assertAlmostEqual(report["crossover"]["crossover_time"],
                               analytic["crossover_time"], places=12)
        # The first output row below the margin is within one output step.
        self.assertLessEqual(report["timeline"]["first_underserved_time"]
                             - analytic["crossover_time"],
                             config["dimensionless_time"]["output_step"])
        self.assertGreaterEqual(float(rows[0]["capacity_margin"]), 1.0)
        self.assertLess(float(rows[-1]["capacity_margin"]), 1.0)

    def test_delivered_flux_is_bounded_by_demand_and_capacity(self):
        _receipt, _report, rows, _output = self.run_model(fixture())
        self.assertGreater(len(rows), 100)
        for row in rows:
            delivered = float(row["delivered_flux"])
            demand = float(row["demand"])
            capacity = float(row["capacity"])
            served = float(row["served_fraction"])
            request = float(row["request_fraction"])
            self.assertLessEqual(delivered, demand + 1e-12)
            self.assertLessEqual(delivered, capacity + 1e-12)
            self.assertGreaterEqual(delivered, 0.0)
            self.assertGreaterEqual(served, 0.0)
            self.assertLessEqual(served, 1.0 + 1e-12)
            self.assertGreaterEqual(request, 0.0)
            self.assertLessEqual(request, 1.0)
            self.assertGreaterEqual(float(row["cumulative_unserved"]), 0.0)

    def test_boundary_detection_lags_internal_shortfall_while_flux_rises(self):
        _receipt, report, _rows, _output = self.run_model(fixture())
        timeline = report["timeline"]
        self.assertEqual(timeline["delivered_flux_rising_at_first_underserved_time"], True)
        self.assertLess(timeline["first_underserved_time"],
                        timeline["boundary_shortfall_detection_time"])
        # Deficit is already substantial when the boundary first flags shortfall.
        self.assertGreater(timeline["cumulative_unserved_at_boundary_detection"], 0.25)
        # The absolute delivered flux keeps rising past the detection event.
        self.assertGreater(timeline["final_delivered_flux"],
                           timeline["delivered_flux_at_boundary_detection"])
        self.assertLess(timeline["final_served_fraction"], 0.95)
        self.assertGreater(timeline["final_cumulative_unserved"],
                           timeline["cumulative_unserved_at_boundary_detection"])

    def test_witness_shares_boundary_and_differs_in_tissue_receipt(self):
        _receipt, report, rows, _output = self.run_model(fixture())
        comparison = report["witness_comparison"]
        self.assertTrue(comparison["boundary_series_identical"])
        self.assertEqual(comparison["max_abs_delivered_flux_difference"], 0.0)
        self.assertEqual(comparison["max_abs_bulk_stock_difference"], 0.0)
        self.assertGreater(comparison["relative_tissue_receipt_difference"], 0.5)
        final = rows[-1]
        self.assertNotEqual(final["tissue_stock_configured"], final["tissue_stock_witness"])
        self.assertGreater(float(final["tissue_stock_configured"]),
                           float(final["tissue_stock_witness"]))

    def test_bulk_balance_residual_and_deterministic_reproduction(self):
        config = fixture()
        _receipt, report, _rows, output_one = self.run_model(config)
        self.assertLess(report["bulk_balance"]["max_abs_trapezoid_residual"], 0.05)
        _receipt_two, _report_two, _rows_two, output_two = self.run_model(config)
        for name in ("trajectory.csv", "growth_scaling_report.json", "REPORT.md"):
            self.assertEqual((output_one / name).read_bytes(), (output_two / name).read_bytes())

    def test_control_world_with_open_margin_never_accrues_deficit(self):
        config = fixture()
        config["scaling"]["capacity_coefficient"] = 5.0
        config["growth"]["surface_exponent"] = 1.0
        _receipt, report, _rows, _output = self.run_model(config)
        self.assertTrue(report["crossover"]["margin_never_closes"])
        self.assertIsNone(report["crossover"]["crossover_size"])
        self.assertIsNone(report["timeline"]["first_underserved_time"])
        self.assertIsNone(report["timeline"]["boundary_shortfall_detection_time"])
        self.assertEqual(report["timeline"]["final_cumulative_unserved"], 0.0)
        self.assertAlmostEqual(report["timeline"]["final_served_fraction"], 1.0, places=12)

    def test_rejects_malformed_configurations(self):
        for mutation, message in (
                (lambda c: c.update(schema_version=2), "schema_version"),
                (lambda c: c.update(fixture_notice="wrong"), "fixture_notice"),
                (lambda c: c["growth"].update(surface_exponent=1.2), "surface_exponent"),
                (lambda c: c["growth"].update(linear_rate=11.0), "linear_rate"),
                (lambda c: c["dimensionless_time"].update(output_step=1e-6), "output intervals"),
                (lambda c: c["exchange_world"].update(extra=1), "exchange_world"),
                (lambda c: c.pop("internal_witness"), "config"),
                (lambda c: c["internal_witness"].update(transfer_efficiency=1.5),
                 "transfer_efficiency")):
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_model(config)

    def test_bundle_metadata_and_strict_verification(self):
        _receipt, report, _rows, output = self.run_model(fixture())
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(report["fixture_notice"], NOTICE)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(NOTICE, text)
        self.assertIn("## Limits", text)


if __name__ == "__main__":
    unittest.main()
