import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.whole_path_twin import whole_path_twin


ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("living_interface", "staged", "synthetic")


def fixture():
    return json.loads((ROOT / "examples/whole_path_twin_fixture.json").read_text(encoding="utf-8"))


class WholePathTwinTests(unittest.TestCase):
    def run_twin(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = whole_path_twin(config_path, output)
        report = json.loads((output / "whole_path_twin_report.json").read_text(encoding="utf-8"))
        trajectories = {}
        for name in VARIANTS:
            with (output / f"trajectory_{name}.csv").open(newline="", encoding="utf-8") as stream:
                trajectories[name] = list(csv.DictReader(stream))
        with (output / "boundary_events.csv").open(newline="", encoding="utf-8") as stream:
            events = list(csv.DictReader(stream))
        with (output / "monitor_readings.csv").open(newline="", encoding="utf-8") as stream:
            monitor = list(csv.DictReader(stream))
        return receipt, report, trajectories, events, monitor, output

    def test_boundary_observables_never_separate_the_variants(self):
        _receipt, report, _traj, _events, _monitor, _output = self.run_twin(fixture())
        self.assertEqual(len(report["pairwise_separation"]), 3)
        for record in report["pairwise_separation"]:
            for observable in ("delivered_flux", "served_fraction", "bulk_stock"):
                self.assertIsNone(record["first_separated"][observable], record["pair"])
            self.assertFalse(record["boundary_observables_ever_separate"])
            self.assertTrue(record["internal_observables_ever_separate"])

    def test_internal_observables_separate_every_pair_at_first_handoff(self):
        _receipt, report, _traj, _events, _monitor, _output = self.run_twin(fixture())
        for record in report["pairwise_separation"]:
            self.assertEqual(record["first_separated"]["deep_receipt_rate"], 1)
            self.assertEqual(record["first_separated"]["progression"], 1)
            # The deficit is a boundary-world property: identical across variants.
            self.assertIsNone(record["first_separated"]["cumulative_unserved"])
        summaries = report["variant_summaries"]
        self.assertGreater(summaries["living_interface"]["final_deep_receipt_rate"],
                           summaries["staged"]["final_deep_receipt_rate"])
        self.assertGreater(summaries["staged"]["final_deep_receipt_rate"],
                           summaries["synthetic"]["final_deep_receipt_rate"])
        for name in VARIANTS:
            self.assertEqual(summaries[name]["final_cumulative_unserved"],
                             summaries["living_interface"]["final_cumulative_unserved"])

    def test_capacity_closure_arc_across_intervals(self):
        _receipt, report, trajectories, _events, _monitor, _output = self.run_twin(fixture())
        self.assertEqual(report["n_intervals"], 4)
        self.assertAlmostEqual(report["crossover"]["crossover_time"], 14.9625, places=3)
        for name in VARIANTS:
            rows = trajectories[name]
            summary = report["variant_summaries"][name]
            self.assertEqual(summary["event_dispositions"],
                             ["supported", "supported", "underserved"])
            # Full service is maintained exactly until the margin closes.
            self.assertAlmostEqual(float(rows[20]["served_fraction"]), 1.0, places=9)
            self.assertGreater(report["crossover"]["margin_at_end"], 0.75)
            self.assertLess(summary["final_served_fraction"], 0.85)
            self.assertAlmostEqual(summary["final_served_fraction"],
                                   summary["final_capacity_margin"], places=2)
            self.assertGreater(summary["final_cumulative_unserved"], 1.0)

    def test_boundary_actuation_is_idle_during_capacity_closure(self):
        _receipt, report, _traj, _events, _monitor, _output = self.run_twin(fixture())
        crossover = report["crossover"]["crossover_time"]
        for name in VARIANTS:
            summary = report["variant_summaries"][name]
            self.assertTrue(summary["supplement_ever_engaged"])
            self.assertLess(summary["supplement_last_engaged"], crossover)
            self.assertFalse(summary["boundary_actuation_during_capacity_closure"])

    def test_outage_failover_and_reserve_depletion(self):
        _receipt, report, trajectories, _events, _monitor, _output = self.run_twin(fixture())
        for name in VARIANTS:
            rows = trajectories[name]
            summary = report["variant_summaries"][name]
            self.assertAlmostEqual(summary["final_reserve"], 2.0 - 0.4 * 2.0, places=6)
            during = [row for row in rows if 8.0 <= float(row["dimensionless_time"]) < 10.0]
            self.assertLess(float(during[-1]["reserve"]), 2.0)
            for row in during:
                served = float(row["served_fraction"])
                self.assertGreater(served, 0.0)
                self.assertLess(served, 1.0)

    def test_monitor_stream_is_separate_from_the_controller(self):
        _receipt, report, _traj, _events, monitor, _output = self.run_twin(fixture())
        living = [row for row in monitor if row["variant"] == "living_interface"]
        missing = [row for row in living if row["reading"] == ""]
        self.assertTrue(missing)
        self.assertTrue(all(22.0 <= float(row["dimensionless_time"]) < 23.0 for row in missing))
        biased = [row for row in living if row["active_fault"] == "bias"]
        self.assertTrue(biased)
        for row in biased:
            self.assertGreater(float(row["reading"]), 0.0)
        # Each controller reading is the previous step's true bulk stock plus noise;
        # recorded monitor faults (bias, dropout) never reach the controller stream.
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "check"
            config_path = Path(temp) / "config.json"
            config_path.write_text(json.dumps(fixture()), encoding="utf-8")
            whole_path_twin(config_path, output)
            with (output / "trajectory_living_interface.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
        for previous, current in zip(rows, rows[1:]):
            difference = abs(float(current["controller_reading"])
                              - float(previous["bulk_stock"]))
            self.assertLess(difference, 0.1)

    def test_deterministic_reproduction(self):
        config = fixture()
        _r1, _rep1, _t1, _e1, _m1, one = self.run_twin(config)
        _r2, _rep2, _t2, _e2, _m2, two = self.run_twin(config)
        names = [f"trajectory_{name}.csv" for name in VARIANTS]
        names += ["boundary_events.csv", "monitor_readings.csv",
                  "whole_path_twin_report.json", "REPORT.md"]
        for name in names:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes())

    def test_rejects_malformed_configurations(self):
        for mutation, message in (
                (lambda c: c.update(schema_version=2), "schema_version"),
                (lambda c: c.update(fixture_notice="wrong"), "fixture_notice"),
                (lambda c: c.update(interval_boundaries=[10.3, 20, 30]), "output grid"),
                (lambda c: c.update(interval_boundaries=[20, 10, 30]), "increasing"),
                (lambda c: c.update(interval_boundaries=[10, 20, 40]), "interval boundary"),
                (lambda c: c["monitor"].update(cadence=0.7), "multiple of the output step"),
                (lambda c: c["monitor"].update(seed="x"), "integer"),
                (lambda c: c["monitor"]["faults"].__setitem__(
                    1, {"start": 22, "end": 23, "kind": "dropout", "magnitude": 0.1}),
                 "Dropout magnitude"),
                (lambda c: c["variants"]["staged"].update(extra=1), "variant staged"),
                (lambda c: c["control"].pop("rate_limit"), "control")):
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_twin(config)

    def test_bundle_metadata_and_strict_verification(self):
        receipt, report, _traj, _events, _monitor, output = self.run_twin(fixture())
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(receipt["bundle_kind"], "dimensionless_whole_path_twin")
        self.assertEqual(receipt["metadata"]["n_variants"], 3)
        self.assertEqual(receipt["metadata"]["n_intervals"], 4)
        self.assertEqual(report["fixture_notice"], NOTICE)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(NOTICE, text)
        self.assertIn("Pairwise variant separation", text)
        self.assertIn("## Limits", text)


if __name__ == "__main__":
    unittest.main()
