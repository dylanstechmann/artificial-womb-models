import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.mechanical_twin import mechanical_twin
from wombmodels.whole_path_twin import whole_path_twin


ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("living_interface", "staged", "synthetic")
FLUIDIC_COLUMNS = ("dimensionless_time", "size", "capacity_margin", "request_fraction",
                   "served_fraction", "delivered_flux", "bulk_stock", "deep_receipt_rate",
                   "cumulative_unserved", "progression", "reserve", "supplement",
                   "controller_reading")


def fixture():
    return json.loads((ROOT / "examples/mechanical_twin_fixture.json").read_text(encoding="utf-8"))


def stripped(config):
    stripped = {key: value for key, value in config.items() if key != "wall"}
    stripped["variants"] = {name: {key: value for key, value in item.items()
                                   if key != "wall_coupling"}
                            for name, item in config["variants"].items()}
    return stripped


class MechanicalTwinTests(unittest.TestCase):
    def run_twin(self, config):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = mechanical_twin(config_path, output)
        report = json.loads((output / "mechanical_twin_report.json").read_text(encoding="utf-8"))
        trajectories = {}
        for name in VARIANTS:
            with (output / f"trajectory_{name}.csv").open(newline="", encoding="utf-8") as stream:
                trajectories[name] = list(csv.DictReader(stream))
        with (output / "boundary_events.csv").open(newline="", encoding="utf-8") as stream:
            events = list(csv.DictReader(stream))
        return receipt, report, trajectories, events, output

    def test_one_way_coupling_carries_the_fluidic_twin_unchanged(self):
        config = fixture()
        _receipt, report, trajectories, _events, output = self.run_twin(config)
        self.assertTrue(report["one_way_coupling"]["fluidic_trajectories_match_uncoupled_twin"])
        self.assertFalse(report["one_way_coupling"]["wall_states_enter_fluidic_derivatives"])
        # Independent check: the uncoupled T21 twin on the same stripped
        # config produces byte-identical fluidic columns.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(stripped(config)), encoding="utf-8")
            whole_path_twin(config_path, root / "bundle")
            for name in VARIANTS:
                with (root / "bundle" / f"trajectory_{name}.csv").open(
                        newline="", encoding="utf-8") as stream:
                    uncoupled = list(csv.DictReader(stream))
                for column in FLUIDIC_COLUMNS:
                    self.assertEqual([row[column] for row in trajectories[name]],
                                     [row[column] for row in uncoupled], column)

    def test_fluidic_boundary_observables_still_never_separate(self):
        _receipt, report, _traj, _events, _output = self.run_twin(fixture())
        self.assertEqual(len(report["pairwise_separation"]), 3)
        for record in report["pairwise_separation"]:
            for observable in ("delivered_flux", "served_fraction", "bulk_stock"):
                self.assertIsNone(record["first_separated"][observable], record["pair"])
            self.assertFalse(record["fluidic_boundary_ever_separate"])

    def test_wall_strain_separates_every_pair_at_the_first_handoff(self):
        _receipt, report, _traj, _events, _output = self.run_twin(fixture())
        for record in report["pairwise_separation"]:
            self.assertEqual(record["first_separated"]["wall_strain"], 1, record["pair"])
            self.assertTrue(record["wall_strain_ever_separates"])

    def test_wall_damage_separates_every_pair_and_stays_hidden(self):
        _receipt, report, trajectories, _events, _output = self.run_twin(fixture())
        for record in report["pairwise_separation"]:
            self.assertEqual(record["first_separated"]["wall_damage"], 1, record["pair"])
            self.assertTrue(record["internal_ever_separate"])
        # The hidden channel is recorded as world truth, never as an
        # observable: the strain record is the wall's only observable column.
        self.assertIn("wall_damage", trajectories["synthetic"][0])
        self.assertIn("wall_strain", trajectories["synthetic"][0])
        self.assertTrue(all(float(row["wall_damage"]) >= 0.0
                            for row in trajectories["synthetic"]))

    def test_wall_summaries_order_strain_and_damage_by_coupling(self):
        _receipt, report, trajectories, _events, _output = self.run_twin(fixture())
        summaries = report["wall_summaries"]
        self.assertGreater(summaries["synthetic"]["final_wall_strain"],
                            summaries["staged"]["final_wall_strain"])
        self.assertGreater(summaries["staged"]["final_wall_strain"],
                            summaries["living_interface"]["final_wall_strain"])
        self.assertGreater(summaries["synthetic"]["final_wall_damage"],
                            summaries["staged"]["final_wall_damage"])
        self.assertGreater(summaries["staged"]["final_wall_damage"],
                            summaries["living_interface"]["final_wall_damage"])
        # Higher coupling crosses the strain limit earlier: synthetic in I1,
        # staged in I1, the living interface only in I2.
        self.assertLess(summaries["synthetic"]["strain_limit_crossing_time"],
                        summaries["staged"]["strain_limit_crossing_time"])
        self.assertLess(summaries["staged"]["strain_limit_crossing_time"],
                        summaries["living_interface"]["strain_limit_crossing_time"])
        self.assertLess(summaries["living_interface"]["final_wall_safety_margin"], 0.0)

    def test_outage_signature_in_the_wall_strain_channel(self):
        _receipt, _report, trajectories, _events, _output = self.run_twin(fixture())
        rows = trajectories["synthetic"]
        by_time = {round(float(row["dimensionless_time"]), 6): row for row in rows}
        before = float(by_time[8.0]["wall_strain"])
        during = [float(row["wall_strain"]) for time, row in by_time.items()
                  if 8.0 < time < 10.0]
        after = float(by_time[10.5]["wall_strain"])
        # The outage halves the delivered flux, the wall unloads, and the
        # strain falls by more than a third before reseating.
        self.assertLess(min(during), 0.7 * before)
        self.assertGreater(after, min(during))

    def test_identical_coupling_produces_no_mechanical_signature(self):
        config = fixture()
        config["variants"]["staged"]["wall_coupling"] = 0.4
        _receipt, report, _traj, _events, _output = self.run_twin(config)
        pair = next(record for record in report["pairwise_separation"]
                    if record["pair"] == ["living_interface", "staged"])
        self.assertIsNone(pair["first_separated"]["wall_strain"])
        self.assertFalse(pair["wall_strain_ever_separates"])
        # The fluidic internal channel still separates that pair: the
        # mechanical signature is exactly the interface coupling.
        self.assertEqual(pair["first_separated"]["deep_receipt_rate"], 1)
        synthetic_pairs = [record for record in report["pairwise_separation"]
                           if "synthetic" in record["pair"]]
        self.assertTrue(all(record["first_separated"]["wall_strain"] == 1
                            for record in synthetic_pairs))

    def test_deterministic_reproduction(self):
        config = fixture()
        _r1, _rep1, _t1, _e1, one = self.run_twin(config)
        _r2, _rep2, _t2, _e2, two = self.run_twin(config)
        names = [f"trajectory_{name}.csv" for name in VARIANTS]
        names += ["boundary_events.csv", "mechanical_twin_report.json", "REPORT.md"]
        for name in names:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes())

    def test_rejects_malformed_configurations(self):
        for mutation, message in (
                (lambda c: c.pop("wall"), "config"),
                (lambda c: c["wall"].pop("viscosity"), "wall"),
                (lambda c: c["wall"].update(safe_strain=0.9), "below strain_limit"),
                (lambda c: c["wall"].update(viscosity=0.0), "viscosity"),
                (lambda c: c["variants"]["staged"].pop("wall_coupling"), "wall_coupling"),
                (lambda c: c["variants"]["staged"].update(wall_coupling=0.0), "wall_coupling"),
                (lambda c: c["wall"].update(stiffness_exponent=1.5), "stiffness_exponent")):
            with self.subTest(message=message):
                config = fixture()
                mutation(config)
                with self.assertRaisesRegex(InputError, message):
                    self.run_twin(config)

    def test_bundle_metadata_and_strict_verification(self):
        receipt, report, _traj, _events, output = self.run_twin(fixture())
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(receipt["bundle_kind"], "dimensionless_mechanical_twin")
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
