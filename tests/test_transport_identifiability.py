from __future__ import annotations

import copy
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.developmental_models import simulate_transport
from wombmodels.numerical_verification import _exact_transport_state
from wombmodels.transport_identifiability import core_coefficients, transport_identifiability

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/transport_identifiability_fixture.json"


class TransportObservationAmbiguityTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EXAMPLE.read_text())
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def publish(self, data=None):
        raw = json.dumps(self.data if data is None else data).encode()
        source = self.root / "fixture.json"
        source.write_bytes(raw)
        output = self.root / "diagnostic"
        receipt = transport_identifiability(source, output)
        self.assertEqual((output / "input_config.json").read_bytes(), raw)
        return output, json.loads((output / "transport_identifiability_report.json").read_text()), receipt

    def test_distinct_rates_preserve_core_but_not_interface_and_no_biology_is_fitted(self):
        output, report, receipt = self.publish()
        self.assertEqual(report["core_only"]["configured_witness_status"], "distinct_equivalent_core_traces")
        self.assertLess(report["core_only"]["max_absolute_core_difference"], 1e-12)
        self.assertGreater(report["core_only"]["max_absolute_interface_difference"], 0.1)
        self.assertEqual(report["swapped_rates"], {
            "boundary_exchange": 0.3, "intercompartment_transport": 0.4, "loss": 0.08})
        # Independently expanded expected scalar equation for the invented case.
        expected = {"a1": 1.26, "a0": 0.2144, "gain": 0.12}
        for key, value in expected.items():
            self.assertAlmostEqual(report["core_only"]["baseline_coefficients"][key], value)
            self.assertAlmostEqual(report["core_only"]["swapped_coefficients"][key], value)
        self.assertTrue(report["paired_transient"]["configured_swap_has_different_interface"])
        for key in ("biological_measurements", "physiologically_calibrated", "human_gestation_prediction", "parameter_fitting_performed"):
            self.assertFalse(report[key])
        self.assertIn("src/wombmodels/transport_identifiability.py", receipt["implementation_sha256"])
        with (output / "observation_contrasts.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 401)
        self.assertEqual(float(rows[0]["baseline_core"]), 0)
        self.assertEqual(float(rows[-1]["dimensionless_time"]), 8)

    def test_rate_swap_identity_across_unequal_and_lossless_regimes(self):
        for e, d, loss in ((0.8, 0.15, 0.08), (0.2, 0.9, 0), (12, 0.03, 0.5), (0.003, 1.7, 0.01)):
            for key, value in core_coefficients(e, d, loss).items():
                self.assertAlmostEqual(value, core_coefficients(2*d, e/2, loss)[key])
            for time in (0, 0.01, 0.3, 1, 8):
                one = _exact_transport_state(0, 0, time, exchange=e, transport=d, loss=loss, boundary=1)
                two = _exact_transport_state(0, 0, time, exchange=2*d, transport=e/2, loss=loss, boundary=1)
                self.assertAlmostEqual(one[1], two[1], places=11)

    def test_two_stationary_traces_cannot_distinguish_doubled_rate_scale(self):
        output, report, _ = self.publish()
        self.assertLess(report["steady_state_only"]["max_absolute_equilibrium_difference"], 1e-14)
        states = []
        for name in ("stationary", "doubled_stationary"):
            fixture = output / f"{name}_config.json"
            bundle = self.root / name
            simulate_transport(fixture, bundle)
            initial = json.loads(fixture.read_text())["initial"]
            with (bundle / "transport_trajectory.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                self.assertAlmostEqual(float(row["interface_state"]), initial["interface"], places=12)
                self.assertAlmostEqual(float(row["core_state"]), initial["core"], places=12)
            states.append(initial)
        self.assertEqual(states[0], states[1])

    def test_coincident_swap_is_explicit_and_zero_excitation_has_no_information(self):
        data = copy.deepcopy(self.data)
        data["rates"]["intercompartment_transport"] = 0.4
        _, report, _ = self.publish(data)
        self.assertFalse(report["core_only"]["distinct_rate_allocations"])
        self.assertEqual(report["core_only"]["configured_witness_status"], "coincident_swap_at_e_equals_2d")
        self.assertFalse(report["paired_transient"]["configured_swap_has_different_interface"])
        for e, d, loss in ((0.8, 0.15, 0.08), (0.3, 0.4, 0.08)):
            for time in (0, 1, 8):
                self.assertEqual(_exact_transport_state(0, 0, time, exchange=e, transport=d, loss=loss, boundary=0), (0, 0))

    def test_wrong_assumptions_and_unsupported_bounds_fail_before_publication(self):
        cases = []
        for field, value in (("initial", {"interface": 0.1, "core": 0}),
                             ("boundary_concentration", 0),
                             ("dimensionless_time", {"duration": 8, "step": 0.0002})):
            data = copy.deepcopy(self.data)
            data[field] = value
            cases.append(data)
        for field, value in (("boundary_exchange", 0), ("intercompartment_transport", 0), ("loss", -0.1), ("loss", float("nan"))):
            data = copy.deepcopy(self.data)
            data["rates"][field] = value
            cases.append(data)
        large = copy.deepcopy(self.data)
        large["dimensionless_time"]["step"] = 0.001
        large["rates"]["boundary_exchange"] = 600
        cases.append(large)
        malformed = copy.deepcopy(self.data)
        malformed["rates"]["physical_rate"] = 1
        cases.append(malformed)
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(InputError):
                    self.publish(data)
                self.assertFalse((self.root / "diagnostic").exists())

    def test_exclusive_publication_and_relocated_verification(self):
        output, _, _ = self.publish()
        with self.assertRaises(InputError):
            self.publish()
        moved = self.root / "moved"
        shutil.copytree(output, moved)
        shutil.rmtree(output)
        (self.root / "fixture.json").unlink()
        result = verify_bundle(moved, strict=True)
        self.assertTrue(result["bytes_verified"], result["errors"])
        self.assertEqual(result["scientific_review"], "not_established_by_this_tool")
        self.assertEqual(result["reproduction"], "not_attempted")
        plan = json.loads((moved / "reproduction_plan.json").read_text())
        self.assertEqual(plan["inputs"], ["input_config.json"])
        self.assertIn("transport-identifiability", plan["command"])

    def test_fractional_grid_ends_at_declared_duration(self):
        for duration in (0.9, 0.95):
            data = copy.deepcopy(self.data)
            data["dimensionless_time"] = {"duration": duration, "step": 0.3}
            output, _, _ = self.publish(data)
            with (output / "observation_contrasts.csv").open(newline="") as stream:
                times = [float(row["dimensionless_time"]) for row in csv.DictReader(stream)]
            self.assertEqual(times[-1], duration)
            self.assertTrue(all(b > a for a, b in zip(times, times[1:])))
            shutil.rmtree(output)
