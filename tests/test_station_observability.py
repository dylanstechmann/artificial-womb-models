"""Tests for the delay-matched shared-station observability counterexample (T32)."""
import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.station_observability import station_observability

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "examples" / "station_observability_fixture.json"
EXPECTED_DEMANDS = {"living_interface": 12.5, "staged": 17.5, "synthetic": 32.0}
EXPECTED_OVERSHOOTS = {
    "living_interface": 0.07621185758956822,
    "staged": 0.053517864711518426,
    "synthetic": 0.024255711822430026,
}


def fixture():
    return json.loads(FIXTURE_PATH.read_bytes())


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))


def write_config(directory, config):
    path = Path(directory) / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


class StationObservabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.output = cls.root / "bundle"
        cls.receipt = station_observability(FIXTURE_PATH, cls.output)
        cls.report = json.loads((cls.output / "station_observability_report.json").read_bytes())
        cls.events = read_csv(cls.output / "station_observability_events.csv")
        cls.station_rows = read_csv(cls.output / "station_observations.csv")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def variant_report(self, name):
        return next(item for item in self.report["variants"] if item["variant"] == name)

    def event(self, variant, world, unit="B"):
        return next(row for row in self.events if row["variant"] == variant
                    and row["world"] == world and row["unit"] == unit)

    def test_hand_calculated_b_schedules(self):
        for name, demand in EXPECTED_DEMANDS.items():
            with self.subTest(variant=name):
                item = self.variant_report(name)
                self.assertEqual(item["demand_time"], demand)
                self.assertEqual(item["wait_duration"], 3.0)
                self.assertEqual(item["service_start"], demand + 3.0)
                self.assertEqual(item["service_end"], demand + 6.0)
                self.assertTrue(item["schedule_matches_hand_calculation"])

    def test_outage_a_offset_is_nonnegative_and_ends_at_d(self):
        expected_offsets = {"living_interface": 9.5, "staged": 14.5, "synthetic": 29.0}
        for name, demand in EXPECTED_DEMANDS.items():
            with self.subTest(variant=name):
                offset = self.variant_report(name)["outage_only_unit_a_demand_time"]
                self.assertEqual(offset, expected_offsets[name])
                self.assertGreaterEqual(offset, 0.0)
                event = self.event(name, "outage_only", "A")
                self.assertEqual(float(event["demand_time"]), demand - 3.0)
                self.assertEqual(float(event["service_start"]), demand - 3.0)
                self.assertEqual(float(event["service_end"]), demand)
                self.assertEqual(float(event["wait_duration"]), 0.0)

    def test_b_wait_service_and_overshoot_are_exactly_identical(self):
        fields = ("demand_time", "wait_duration", "service_start", "service_end",
                  "stage_overshoot")
        for name in EXPECTED_DEMANDS:
            with self.subTest(variant=name):
                queue = self.event(name, "queue_only")
                outage = self.event(name, "outage_only")
                self.assertEqual({key: queue[key] for key in fields},
                                 {key: outage[key] for key in fields})
                self.assertNotEqual(queue["ground_truth_delay_cause"],
                                    outage["ground_truth_delay_cause"])

    def test_stage_overshoot_values_and_direct_progression_difference(self):
        for name, expected in EXPECTED_OVERSHOOTS.items():
            with self.subTest(variant=name):
                item = self.variant_report(name)
                self.assertEqual(item["stage_overshoot"], expected)
                rows = read_csv(self.output / f"unit_b_local_queue_only_{name}.csv")
                by_time = {float(row["dimensionless_time"]): float(row["progression"])
                           for row in rows}
                demand = item["demand_time"]
                direct = by_time[demand + 3.0] - by_time[demand]
                self.assertAlmostEqual(direct, expected, places=15)

    def test_b_local_series_are_bitwise_identical(self):
        for name in EXPECTED_DEMANDS:
            with self.subTest(variant=name):
                queue = (self.output / f"unit_b_local_queue_only_{name}.csv").read_bytes()
                outage = (self.output / f"unit_b_local_outage_only_{name}.csv").read_bytes()
                self.assertEqual(queue, outage)
                self.assertEqual(sha256(queue), self.variant_report(name)["unit_b_local_sha256"])

    def test_local_series_include_boundary_wall_and_internal_channels(self):
        required = {"delivered_flux", "served_fraction", "bulk_stock", "wall_strain",
                    "wall_damage", "deep_receipt_rate", "cumulative_unserved", "progression",
                    "reserve", "supplement", "controller_reading"}
        header = (self.output / "unit_b_local_queue_only_living_interface.csv").read_text().splitlines()[0]
        self.assertTrue(required <= set(header.split(",")))

    def test_unit_local_channels_cannot_attribute_delay_cause(self):
        self.assertFalse(self.report["unit_local_separates"])
        for item in self.report["variants"]:
            self.assertFalse(item["unit_local_separates"])
            self.assertTrue(item["unit_b_local_bitwise_identical"])
            self.assertTrue(item["unit_b_wait_and_overshoot_identical"])
            self.assertEqual(item["queue_only_ground_truth_delay_cause"], "queue")
            self.assertEqual(item["outage_only_ground_truth_delay_cause"], "station_outage")

    def test_station_operational_state_separates_at_delay_window(self):
        self.assertTrue(self.report["station_operational_state_separates"])
        for name, demand in EXPECTED_DEMANDS.items():
            rows = [row for row in self.station_rows if row["variant"] == name
                    and float(row["dimensionless_time"]) == demand]
            states = {row["world"]: row["station_operational_state"] for row in rows}
            self.assertEqual(states, {"queue_only": "available", "outage_only": "outage"})

    def test_station_active_occupancy_separates_at_delay_window(self):
        self.assertTrue(self.report["station_active_unit_separates"])
        for name, demand in EXPECTED_DEMANDS.items():
            rows = [row for row in self.station_rows if row["variant"] == name
                    and float(row["dimensionless_time"]) == demand]
            active = {row["world"]: row["station_active_unit"] for row in rows}
            self.assertEqual(active, {"queue_only": "serving_unit_A",
                                      "outage_only": "idle_during_outage"})

    def test_lumped_unavailable_flag_never_separates(self):
        self.assertFalse(self.report["lumped_unavailable_separates"])
        for name in EXPECTED_DEMANDS:
            rows = [row for row in self.station_rows if row["variant"] == name]
            queue = {row["dimensionless_time"]: row["station_unavailable_flag"]
                     for row in rows if row["world"] == "queue_only"}
            outage = {row["dimensionless_time"]: row["station_unavailable_flag"]
                      for row in rows if row["world"] == "outage_only"}
            self.assertEqual(queue, outage)
            self.assertTrue(all(value == "True" for key, value in queue.items()
                                if float(key) < self.variant_report(name)["service_end"]))

    def test_channels_reconverge_during_b_service(self):
        for name in EXPECTED_DEMANDS:
            item = self.variant_report(name)
            rows = [row for row in self.station_rows if row["variant"] == name
                    and float(row["dimensionless_time"]) == item["service_start"]]
            self.assertEqual({row["station_operational_state"] for row in rows}, {"available"})
            self.assertEqual({row["station_active_unit"] for row in rows}, {"serving_unit_B"})

    def test_t31_canonical_source_and_fixture_hashes_are_unchanged(self):
        register = json.loads((ROOT / "config/program/roadmap.json").read_bytes())
        task = next(item for item in register["tasks"] if item["id"] == "T31")
        pinned = {entry["path"]: entry["sha256"] for entry in task["evidence"]}
        for path in ("src/wombmodels/transition_demand.py", "examples/transition_demand_fixture.json"):
            self.assertEqual(sha256((ROOT / path).read_bytes()), pinned[path])

    def test_t31_dedicated_control_behavior_is_unchanged(self):
        from wombmodels.transition_demand import transition_demand
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "t31"
            transition_demand(ROOT / "examples" / "transition_demand_fixture.json", output)
            report = json.loads((output / "transition_demand_report.json").read_bytes())
            self.assertTrue(report["dedicated_matches_twin"])
            self.assertTrue(report["simultaneous_second_wait_equals_service_time"])
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_t31_readiness_and_canonical_fluidics_are_reused(self):
        self.assertTrue(self.report["t31_canonical_unchanged"])
        self.assertEqual(self.report["transition_contract"]["readiness_threshold"], 0.25)
        self.assertEqual(self.report["transition_contract"]["fifo_tiebreak"], "unit_A_first")
        self.assertEqual({item["variant"]: item["demand_time"] for item in self.report["variants"]},
                         EXPECTED_DEMANDS)

    def test_measurement_addendum_is_bounded_nonmutating_and_unpriced(self):
        addendum = self.report["measurement_addendum"]
        self.assertFalse(addendum["mutates_t24_t25_architecture_discrimination_spec"])
        self.assertTrue(addendum["calibration_required"])
        self.assertFalse(addendum["procurement_authorized"])
        self.assertFalse(addendum["hardware_reliability_claim"])
        self.assertIsNone(addendum["total_price"])
        self.assertEqual(len(addendum["channels"]), 3)
        for channel in addendum["channels"]:
            self.assertIsNone(channel["price"])
        insufficient = next(channel for channel in addendum["channels"]
                            if channel["channel"] == "station_unavailable_flag")
        self.assertEqual(insufficient["requirement"], "insufficient")
        self.assertFalse(insufficient["separates_counterexample"])

    def test_malformed_inputs_publish_nothing(self):
        cases = [
            ("missing wall", lambda c: c.pop("wall")),
            ("boolean service time", lambda c: c["transition_experiment"].__setitem__("service_time", True)),
            ("negative service time", lambda c: c["transition_experiment"].__setitem__("service_time", -1.0)),
            ("boolean schema", lambda c: c.__setitem__("schema_version", True)),
            ("out-of-range wall coupling", lambda c: c["variants"]["staged"].__setitem__("wall_coupling", 0.0)),
            ("off-grid service time", lambda c: c["transition_experiment"].__setitem__("service_time", 2.6)),
            ("window exceeds duration", lambda c: c["dimensionless_time"].__setitem__("duration", 34.0)),
        ]
        for label, mutate in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                config = fixture()
                mutate(config)
                output = Path(tmp) / "out"
                with self.assertRaises(InputError):
                    station_observability(write_config(tmp, config), output)
                self.assertFalse(output.exists())

    def test_duplicate_boolean_nonfinite_and_out_of_range_json_rejected(self):
        raw_cases = [
            b'{"schema_version": 1, "schema_version": 1}',
            FIXTURE_PATH.read_bytes().replace(b'"service_time": 3.0', b'"service_time": NaN'),
            FIXTURE_PATH.read_bytes().replace(b'"readiness_threshold": 0.25',
                                              b'"readiness_threshold": true'),
            FIXTURE_PATH.read_bytes().replace(b'"readiness_threshold": 0.25',
                                              b'"readiness_threshold": 25.0'),
        ]
        for raw in raw_cases:
            with self.subTest(raw=raw[:60]), tempfile.TemporaryDirectory() as tmp:
                config = Path(tmp) / "config.json"
                config.write_bytes(raw)
                output = Path(tmp) / "out"
                with self.assertRaises(InputError):
                    station_observability(config, output)
                self.assertFalse(output.exists())

    def test_work_budget_exhaustion_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "wombmodels.station_observability.MAX_TOTAL_SUBSTEPS", 1):
            output = Path(tmp) / "out"
            with self.assertRaisesRegex(InputError, "substep budget"):
                station_observability(FIXTURE_PATH, output)
            self.assertFalse(output.exists())

    def test_output_destination_is_exclusive(self):
        original = (self.output / "receipt.json").read_bytes()
        with self.assertRaisesRegex(InputError, "already exists"):
            station_observability(FIXTURE_PATH, self.output)
        self.assertEqual((self.output / "receipt.json").read_bytes(), original)

    def test_deterministic_publication(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            out1, out2 = Path(first) / "out", Path(second) / "out"
            station_observability(FIXTURE_PATH, out1)
            station_observability(FIXTURE_PATH, out2)
            names1 = sorted(path.name for path in out1.iterdir())
            names2 = sorted(path.name for path in out2.iterdir())
            self.assertEqual(names1, names2)
            for name in names1:
                self.assertEqual((out1 / name).read_bytes(), (out2 / name).read_bytes(), name)

    def test_cli_round_trip_and_strict_verification(self):
        from wombmodels.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "cli"
            result = main(["station-observability-model", "--config", str(FIXTURE_PATH),
                           "--out", str(output)])
            self.assertEqual(result, 0)
            checked = verify_bundle(output, strict=True)
            self.assertTrue(checked["bytes_verified"], checked["errors"])
            self.assertIn("station-observability-model", checked["rerun_command"])

    def test_strict_relocation_and_relocatable_reproduction_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "original"
            moved = Path(tmp) / "relocated" / "renamed"
            shutil.copytree(self.output, original)
            moved.parent.mkdir()
            shutil.copytree(original, moved)
            shutil.rmtree(original)
            checked = verify_bundle(moved, strict=True)
            self.assertTrue(checked["bytes_verified"], checked["errors"])
            self.assertEqual(checked["bundle"], "renamed")
            plan_text = (moved / "reproduction_plan.json").read_text()
            self.assertNotIn(str(self.root), plan_text)
            self.assertNotIn(str(FIXTURE_PATH), plan_text)

    def test_tamper_and_undeclared_files_fail_strict_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            moved = Path(tmp) / "bundle"
            shutil.copytree(self.output, moved)
            target = moved / "unit_b_local_queue_only_staged.csv"
            target.write_bytes(target.read_bytes() + b"\n")
            self.assertFalse(verify_bundle(moved, strict=True)["bytes_verified"])
            target.write_bytes((self.output / target.name).read_bytes())
            (moved / "notes.txt").write_text("undeclared\n")
            self.assertFalse(verify_bundle(moved, strict=True)["bytes_verified"])

    def test_receipt_pins_exact_input_source_and_output_bytes(self):
        self.assertEqual(self.receipt["bundle_kind"], "dimensionless_station_observability")
        self.assertEqual(self.receipt["input_sha256"], sha256(FIXTURE_PATH.read_bytes()))
        self.assertIn("src/wombmodels/station_observability.py",
                      self.receipt["implementation_sha256"])
        for name, entry in self.receipt["outputs"].items():
            raw = (self.output / name).read_bytes()
            self.assertEqual(entry["sha256"], sha256(raw), name)
            self.assertEqual(entry["size_bytes"], len(raw), name)

    def test_report_status_and_explicit_nonclaims(self):
        self.assertEqual(self.report["qualification_status"],
                         "dimensionless_software_checks_passed")
        self.assertTrue(self.report["counterexample_verified"])
        self.assertFalse(self.report["biological_measurements"])
        self.assertFalse(self.report["physiologically_calibrated"])
        self.assertFalse(self.report["human_gestation_prediction"])
        text = (self.output / "REPORT.md").read_text()
        self.assertIn("Artificial dimensionless software fixture", text)
        self.assertIn("No biological, neonatal, clinical", text)
        self.assertIn("All prices remain null", text)


if __name__ == "__main__":
    unittest.main()
