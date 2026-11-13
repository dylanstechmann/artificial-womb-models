"""Tests for the multi-unit shared-service contention experiment (T30)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
FIXTURE_PATH = EXAMPLES / "multi_unit_contention_fixture.json"


def fixture():
    with open(FIXTURE_PATH, "rb") as fh:
        return json.loads(fh.read())


_TEMP_DIRS = []


def run_model(config, cli_args=None):
    from wombmodels.multi_unit_contention import _run_experiment
    from wombmodels.bundle_verification import verify_bundle
    import json as _json
    tmp_obj = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(tmp_obj)
    tmp = tmp_obj.name
    config_path = Path(tmp) / "config.json"
    config_path.write_text(_json.dumps(config))
    output = Path(tmp) / "output"
    receipt = _run_experiment(config_path, output)
    report_path = output / "multi_unit_contention_report.json"
    report = _json.loads(report_path.read_bytes())
    verified = verify_bundle(output, strict=True)
    return receipt, report, output, verified


class MultiUnitContentionTests(unittest.TestCase):
    def tearDown(self):
        while _TEMP_DIRS:
            _TEMP_DIRS.pop().cleanup()
    def test_isolated_mode_produces_both_units(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        # Check that isolated trajectories exist for both units
        for name in config["variants"]:
            self.assertTrue((output / f"trajectory_isolated_{name}_A.csv").exists())
            self.assertTrue((output / f"trajectory_isolated_{name}_B.csv").exists())

    def test_shared_mode_produces_fault_trajectories(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        # Check shared trajectories exist for sensor_bias and actuator_offset faults
        for name in config["variants"]:
            for fault_kind in ("sensor_bias", "actuator_offset"):
                self.assertTrue(
                    (output / f"trajectory_shared_{name}_{fault_kind}_A.csv").exists(),
                    f"Missing trajectory_shared_{name}_{fault_kind}_A.csv")
                self.assertTrue(
                    (output / f"trajectory_shared_{name}_{fault_kind}_B.csv").exists(),
                    f"Missing trajectory_shared_{name}_{fault_kind}_B.csv")

    def test_observations_report_cross_unit_propagation(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        # Read observations CSV
        import csv, io
        obs_path = output / "contention_observations.csv"
        reader = csv.DictReader(io.StringIO(obs_path.read_text()))
        rows = list(reader)
        self.assertGreater(len(rows), 0)
        # Check that cross_unit_propagation is recorded
        propagated = [r for r in rows if r.get("cross_unit_propagation") == "True"]
        # Sensor bias should cause propagation
        self.assertGreater(len(propagated), 0, "Expected cross-unit propagation from sensor bias")

    def test_cross_unit_propagation_from_sensor_bias(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        comparisons = report.get("comparisons", [])
        sensor_bias_comps = [c for c in comparisons if c["fault_kind"] == "sensor_bias"]
        self.assertGreater(len(sensor_bias_comps), 0)
        for comp in sensor_bias_comps:
            self.assertTrue(comp["cross_unit_propagation_detected"],
                           f"Expected cross-unit propagation for {comp['variant']} sensor_bias")

    def test_cross_unit_propagation_from_actuator_offset(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        comparisons = report.get("comparisons", [])
        actuator_comps = [c for c in comparisons if c["fault_kind"] == "actuator_offset"]
        self.assertGreater(len(actuator_comps), 0)
        for comp in actuator_comps:
            self.assertTrue(comp["cross_unit_propagation_detected"],
                           f"Expected cross-unit propagation for {comp['variant']} actuator_offset")

    def test_hidden_contention_boundary_blindness(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        hidden = report.get("hidden_contention_check", {})
        self.assertTrue(hidden.get("contention_boundary_blind"),
                       "Unit B's boundary channels should be blind to internal differences")
        self.assertTrue(hidden.get("unit_b_boundary_identical"),
                       "Unit B boundary channels should be identical")
        self.assertTrue(hidden.get("unit_b_internal_differs"),
                       "Unit B internal channels should differ")

    def test_isolated_mode_matches_twin(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        self.assertTrue(report.get("no_fault_isolated_matches_twin"),
                       "Isolated mode should match independent whole_path_twin runs")

    def test_deterministic_publication(self):
        config = fixture()
        import json as _json
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            from wombmodels.multi_unit_contention import _run_experiment
            config_path1 = Path(tmp1) / "config.json"
            config_path1.write_text(_json.dumps(config))
            config_path2 = Path(tmp2) / "config.json"
            config_path2.write_text(_json.dumps(config))
            out1 = Path(tmp1) / "out"
            out2 = Path(tmp2) / "out"
            _run_experiment(config_path1, out1)
            _run_experiment(config_path2, out2)
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
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        self.assertIn("comparisons", report)
        self.assertIn("hidden_contention_check", report)
        self.assertIn("interpretation", report)
        self.assertIn("limits", report)
        # Check REPORT.md exists
        report_md = output / "REPORT.md"
        self.assertTrue(report_md.exists())
        content = report_md.read_text()
        self.assertIn("multi-unit", content.lower())

    def test_malformed_inputs(self):
        config = fixture()
        import json as _json
        from wombmodels.artifacts import InputError
        from wombmodels.multi_unit_contention import _run_experiment

        cases = [
            ("missing contention_experiment", lambda c: c.pop("contention_experiment"),
             "contention_experiment"),
            ("missing shared_reservoir", lambda c: c["contention_experiment"].pop("shared_reservoir"),
             "shared_reservoir"),
            ("missing modes", lambda c: c["contention_experiment"].pop("modes"),
             "modes"),
            ("invalid mode", lambda c: c["contention_experiment"]["modes"].append("invalid"),
             "modes"),
            ("negative reservoir initial", lambda c: c["contention_experiment"]["shared_reservoir"].__setitem__("initial", -1.0),
             "shared_reservoir"),
            ("negative replenishment", lambda c: c["contention_experiment"]["shared_reservoir"].__setitem__("replenishment_rate", -1.0),
             "shared_reservoir"),
            ("invalid fault kind", lambda c: c["contention_experiment"]["unit_a_faults"][0].__setitem__("kind", "invalid_kind"),
             "kind"),
            ("overlapping faults", lambda c: (
                c["contention_experiment"]["unit_a_faults"].append(
                    {"kind": "sensor_bias", "start": 16, "end": 20, "magnitude": 0.5})),
             "nonoverlapping"),
            ("off-grid fault", lambda c: c["contention_experiment"]["unit_a_faults"][1].__setitem__("start", 15.3),
             "output grid"),
            ("boolean as seed", lambda c: c["contention_experiment"].update({"seed": True}),
             "seed"),
        ]
        for label, mutate, expected in cases:
            with self.subTest(label=label):
                mutated = _json.loads(_json.dumps(config))
                mutate(mutated)
                with tempfile.TemporaryDirectory() as tmp:
                    config_path = Path(tmp) / "config.json"
                    config_path.write_text(_json.dumps(mutated))
                    with self.assertRaises((InputError, KeyError, TypeError, ValueError),
                                          msg=f"Expected rejection for {label}"):
                        _run_experiment(config_path, Path(tmp) / "out")

    def test_work_budget_exhaustion_rejected(self):
        config = fixture()
        import json as _json
        from wombmodels.artifacts import InputError
        from wombmodels.multi_unit_contention import _run_experiment
        with patch("wombmodels.multi_unit_contention.MAX_TOTAL_SUBSTEPS", 1):
            with tempfile.TemporaryDirectory() as tmp:
                config_path = Path(tmp) / "config.json"
                config_path.write_text(_json.dumps(config))
                with self.assertRaises(InputError):
                    _run_experiment(config_path, Path(tmp) / "out")
                # Verify no output directory was created
                self.assertFalse((Path(tmp) / "out").exists(),
                                "Output directory should not exist after budget exhaustion")

    def test_cli_entry(self):
        import json as _json
        from wombmodels.cli import main
        from wombmodels.bundle_verification import verify_bundle
        config = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(_json.dumps(config))
            output = Path(tmp) / "output"
            result = main(["multi-unit-contention-model", "--config", str(config_path),
                          "--out", str(output)])
            self.assertEqual(result, 0)
            verified = verify_bundle(output, strict=True)
            self.assertTrue(verified["bytes_verified"],
                           f"CLI strict verification failed: {verified.get('errors', [])}")

    def test_report_md_contains_notice(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        report_md = output / "REPORT.md"
        content = report_md.read_text()
        self.assertIn("Artificial dimensionless software fixture", content)

    def test_isolated_units_produce_identical_trajectories(self):
        config = fixture()
        _, report, output, verified = run_model(config)
        self.assertTrue(verified["bytes_verified"])
        import csv, io
        for name in config["variants"]:
            rows_a = list(csv.DictReader(io.StringIO((output / f"trajectory_isolated_{name}_A.csv").read_text())))
            rows_b = list(csv.DictReader(io.StringIO((output / f"trajectory_isolated_{name}_B.csv").read_text())))
            self.assertEqual(len(rows_a), len(rows_b))
            for ra, rb in zip(rows_a, rows_b):
                for key in ra:
                    if key != "unit":
                        self.assertEqual(ra[key], rb[key])

    def test_fixture_notice_in_config(self):
        config = fixture()
        self.assertIn("fixture_notice", config)
        self.assertIn("Artificial dimensionless software fixture", config["fixture_notice"])


if __name__ == "__main__":
    unittest.main()
