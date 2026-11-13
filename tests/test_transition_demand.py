"""Tests for the concurrent transition demand experiment (T31)."""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
FIXTURE_PATH = EXAMPLES / "transition_demand_fixture.json"


def fixture():
    with open(FIXTURE_PATH, "rb") as fh:
        return json.loads(fh.read())


def twin_rows(config):
    """Reconstruct the canonical whole-path twin trajectories from a config."""
    from wombmodels.whole_path_twin import _validate, _variant_run
    base = {key: value for key, value in config.items() if key != "transition_experiment"}
    parsed = _validate(base)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, variants, analysis) = parsed
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)
    return {name: _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
            for name in sorted(variants)}


_TEMP_DIRS = []


def run_model(config):
    from wombmodels.transition_demand import transition_demand
    from wombmodels.bundle_verification import verify_bundle
    tmp_obj = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(tmp_obj)
    tmp = tmp_obj.name
    config_path = Path(tmp) / "config.json"
    config_path.write_text(json.dumps(config))
    output = Path(tmp) / "output"
    receipt = transition_demand(config_path, output)
    report_path = output / "transition_demand_report.json"
    report = json.loads(report_path.read_bytes())
    verified = verify_bundle(output, strict=True)
    return receipt, report, output, verified


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text())))


class TransitionDemandTests(unittest.TestCase):
    def tearDown(self):
        while _TEMP_DIRS:
            _TEMP_DIRS.pop().cleanup()

    def test_dedicated_produces_both_units(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        for name in config["variants"]:
            self.assertTrue((output / f"trajectory_dedicated_{name}_A.csv").exists())
            self.assertTrue((output / f"trajectory_dedicated_{name}_B.csv").exists())

    def test_dedicated_matches_twin_and_waits_zero(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        self.assertTrue(report["dedicated_matches_twin"])
        twins = twin_rows(config)
        nonunit = [c for c in ("dimensionless_time", "size", "capacity_margin",
                               "request_fraction", "served_fraction", "delivered_flux",
                               "bulk_stock", "deep_receipt_rate", "cumulative_unserved",
                               "progression", "reserve", "supplement")]
        for name in config["variants"]:
            for unit in ("A", "B"):
                rows = read_csv(output / f"trajectory_dedicated_{name}_{unit}.csv")
                self.assertEqual(len(rows), len(twins[name]))
                for actual, expected in zip(rows, twins[name]):
                    for column in nonunit:
                        self.assertEqual(float(actual[column]), expected[column],
                                         f"{name}/{unit} {column}")
        events = read_csv(output / "transition_demand_events.csv")
        for event in events:
            if event["mode"] == "dedicated":
                self.assertEqual(float(event["wait_time"]), 0.0)

    def test_simultaneous_second_wait_equals_service_time(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        self.assertTrue(report["simultaneous_second_wait_equals_service_time"])
        events = read_csv(output / "transition_demand_events.csv")
        staged_b = [e for e in events
                    if e["mode"] == "shared_serial" and e["variant"] == "staged"
                    and e["unit"] == "B"][0]
        self.assertEqual(float(staged_b["wait_time"]), config["transition_experiment"]["service_time"])
        self.assertEqual(staged_b["cause"], "queue")

    def test_closed_form_offset_sweep(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        sweep = report["closed_form_offset_sweep"]
        self.assertTrue(sweep["overall"])
        service_time = config["transition_experiment"]["service_time"]
        for variant in sweep["variants"]:
            if not variant["ready"]:
                continue
            for entry in variant["offsets"]:
                self.assertTrue(entry["confirmed"])
                self.assertAlmostEqual(entry["expected"],
                                       max(0.0, service_time - entry["offset"]))

    def test_outage_increases_waits(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        outage = report["outage_correlates_delays"]
        self.assertTrue(outage["overall"])
        for variant in outage["variants"]:
            if variant["correlates"]:
                self.assertGreater(variant["outage_waits"]["A"],
                                   variant["no_outage_waits"]["A"])
                self.assertGreater(variant["outage_waits"]["B"],
                                   variant["no_outage_waits"]["B"])

    def test_stage_overshoot_delayed_positive_dedicated_zero(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        events = read_csv(output / "transition_demand_events.csv")
        for event in events:
            if event["mode"] == "dedicated":
                self.assertEqual(float(event["stage_overshoot"]), 0.0)
            elif event["mode"] == "shared_serial" and event["unit"] == "B":
                self.assertGreater(float(event["stage_overshoot"]), 0.0)

    def test_not_ready_units_preserved_with_nulls(self):
        config = fixture()
        config["transition_experiment"]["readiness_threshold"] = 9.0
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        events = read_csv(output / "transition_demand_events.csv")
        self.assertGreater(len(events), 0)
        for event in events:
            self.assertEqual(event["ready"], "False")
            self.assertEqual(event["demand_time"], "")
            self.assertEqual(event["service_start"], "")
            self.assertEqual(event["service_end"], "")
            self.assertEqual(event["wait_time"], "")
            self.assertEqual(event["stage_overshoot"], "")
            self.assertEqual(event["transition_completed"], "False")

    def test_local_blindness_check(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        blindness = report["local_blindness_check"]
        self.assertTrue(blindness["b_local_columns_identical_to_twin"])
        self.assertFalse(blindness["cause_attributable_from_local_channels"])
        self.assertGreater(len(blindness["distinct_causes_across_scenarios"]), 1)
        # Direct check: B's local columns up to service_start equal the free twin.
        twins = twin_rows(config)
        nonunit = [c for c in ("dimensionless_time", "size", "capacity_margin",
                               "request_fraction", "served_fraction", "delivered_flux",
                               "bulk_stock", "deep_receipt_rate", "cumulative_unserved",
                               "progression", "reserve", "supplement")]
        events = read_csv(output / "transition_demand_events.csv")
        for name in config["variants"]:
            b_event = [e for e in events
                       if e["mode"] == "shared_serial" and e["variant"] == name
                       and e["unit"] == "B"][0]
            b_start = float(b_event["service_start"])
            rows = read_csv(output / f"trajectory_shared_serial_{name}_B.csv")
            twin = twins[name]
            for actual, expected in zip(rows, twin):
                if float(actual["dimensionless_time"]) > b_start + 1e-9:
                    break
                for column in nonunit:
                    self.assertEqual(float(actual[column]), expected[column],
                                     f"{name}/{column}")

    def test_deterministic_publication(self):
        config = fixture()
        from wombmodels.transition_demand import transition_demand
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            config_path1 = Path(tmp1) / "config.json"
            config_path1.write_text(json.dumps(config))
            config_path2 = Path(tmp2) / "config.json"
            config_path2.write_text(json.dumps(config))
            out1 = Path(tmp1) / "out"
            out2 = Path(tmp2) / "out"
            transition_demand(config_path1, out1)
            transition_demand(config_path2, out2)
            files1 = sorted(p.name for p in out1.rglob("*") if p.is_file() and p.name != "receipt.json")
            files2 = sorted(p.name for p in out2.rglob("*") if p.is_file() and p.name != "receipt.json")
            self.assertEqual(files1, files2)
            for name in files1:
                self.assertEqual((out1 / name).read_bytes(), (out2 / name).read_bytes(),
                                 f"File {name} differs between runs")

    def test_strict_bundle_verification(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"],
                        f"Strict verification failed: {verified.get('errors', [])}")

    def test_report_has_required_sections(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["result_kind"], "dimensionless_transition_demand")
        self.assertEqual(report["model_family"], "dimensionless_transition_demand_experiment")
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        self.assertIn("dedicated_matches_twin", report)
        self.assertIn("simultaneous_second_wait_equals_service_time", report)
        self.assertIn("closed_form_offset_sweep", report)
        self.assertIn("outage_correlates_delays", report)
        self.assertIn("local_blindness_check", report)
        self.assertIn("interpretation", report)
        self.assertIn("limits", report)
        self.assertEqual(report["qualification_status"],
                         "dimensionless_software_checks_passed")
        report_md = output / "REPORT.md"
        self.assertTrue(report_md.exists())
        content = report_md.read_text()
        self.assertIn("Artificial dimensionless software fixture", content)
        self.assertIn("transition", content.lower())

    def test_malformed_inputs(self):
        config = fixture()
        from wombmodels.artifacts import InputError
        from wombmodels.transition_demand import transition_demand

        def many_outages(c):
            c["transition_experiment"]["station_outages"] = [
                {"start": float(i), "end": float(i) + 0.5} for i in range(9)
            ]
            return c

        cases = [
            ("missing transition_experiment",
             lambda c: c.pop("transition_experiment"), "transition_experiment"),
            ("missing service_time",
             lambda c: c["transition_experiment"].pop("service_time"), "service_time"),
            ("invalid mode",
             lambda c: c["transition_experiment"]["modes"].append("invalid"), "modes"),
            ("negative service_time",
             lambda c: c["transition_experiment"].__setitem__("service_time", -1.0), "service_time"),
            ("off-grid outage",
             lambda c: c["transition_experiment"]["station_outages"][0].__setitem__("start", 12.3),
             "output grid"),
            ("overlapping outages",
             lambda c: c["transition_experiment"]["station_outages"].append(
                 {"start": 14.0, "end": 16.0}), "nonoverlapping"),
            ("threshold out of range",
             lambda c: c["transition_experiment"].__setitem__("readiness_threshold", 11.0),
             "readiness_threshold"),
            ("boolean as number",
             lambda c: c["transition_experiment"].__setitem__("service_time", True), "service_time"),
            ("excess outages",
             many_outages, "at most 8"),
        ]
        for label, mutate, expected in cases:
            with self.subTest(label=label):
                mutated = json.loads(json.dumps(config))
                mutate(mutated)
                with tempfile.TemporaryDirectory() as tmp:
                    config_path = Path(tmp) / "config.json"
                    config_path.write_text(json.dumps(mutated))
                    with self.assertRaises((InputError, KeyError, TypeError, ValueError),
                                           msg=f"Expected rejection for {label}"):
                        transition_demand(config_path, Path(tmp) / "out")

    def test_work_budget_exhaustion_rejected(self):
        config = fixture()
        from wombmodels.artifacts import InputError
        from wombmodels.transition_demand import transition_demand
        with patch("wombmodels.transition_demand.MAX_TOTAL_SUBSTEPS", 1):
            with tempfile.TemporaryDirectory() as tmp:
                config_path = Path(tmp) / "config.json"
                config_path.write_text(json.dumps(config))
                with self.assertRaises(InputError):
                    transition_demand(config_path, Path(tmp) / "out")
                self.assertFalse((Path(tmp) / "out").exists(),
                                 "Output directory should not exist after budget exhaustion")

    def test_cli_entry(self):
        from wombmodels.cli import main
        from wombmodels.bundle_verification import verify_bundle
        config = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(json.dumps(config))
            output = Path(tmp) / "output"
            result = main(["transition-demand-model", "--config", str(config_path),
                           "--out", str(output)])
            self.assertEqual(result, 0)
            verified = verify_bundle(output, strict=True)
            self.assertTrue(verified["bytes_verified"],
                            f"CLI strict verification failed: {verified.get('errors', [])}")


if __name__ == "__main__":
    unittest.main()
