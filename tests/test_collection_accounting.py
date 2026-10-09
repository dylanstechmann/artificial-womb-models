"""Artificial, dimensionless accounting observations; never biological assays."""
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
from wombmodels.collection_accounting import collection_accounting, validate_accounting

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/collection_accounting_fixture.json"


class CollectionAccountingTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(EXAMPLE.read_text())
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def publish(self):
        raw = json.dumps(self.config).encode()
        path = self.root / "input.json"
        path.write_bytes(raw)
        bundle = self.root / "bundle"
        collection_accounting(path, bundle)
        self.assertEqual((bundle / "input_config.json").read_bytes(), raw)
        with (bundle / "observations.csv").open(newline="") as stream:
            observations = {r["case_id"]: r for r in csv.DictReader(stream)}
        with (bundle / "allocation_witnesses.csv").open(newline="") as stream:
            witnesses = list(csv.DictReader(stream))
        return bundle, json.loads((bundle / "accounting_report.json").read_text()), observations, witnesses

    def test_collection_omission_is_not_tissue_accumulation(self):
        _, report, rows, _ = self.publish()
        case = rows["collection_explains_disappearance"]
        self.assertEqual(float(case["collection_corrected_residual"]), 0)
        self.assertEqual(float(case["residual_if_collection_omitted"]), 5)
        self.assertEqual(case["relative_change_status"], "unavailable_zero_receiver_baseline")
        self.assertEqual(case["receiver_concentration_change_percent"], "")
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["parameter_fitting_performed"])
        self.assertFalse(report["human_gestation_prediction"])

    def test_receiver_concentration_can_increase_without_inventory_increase(self):
        _, report, rows, _ = self.publish()
        case = rows["concentration_rises_without_amount_rise"]
        self.assertEqual(float(case["receiver_concentration_change_percent"]), 100)
        self.assertEqual(float(case["receiver_inventory_change"]), 0)
        result = next(c for c in report["cases"] if c["case_id"] == case["case_id"])
        self.assertTrue(result["receiver_concentration_increased_without_receiver_inventory_increase"])

    def test_distinct_partitions_preserve_same_observations_and_tissue_measurement(self):
        _, report, rows, witnesses = self.publish()
        unconstrained = [w for w in witnesses if w["case_id"] == "unresolved_residual_partition"]
        self.assertEqual(len(unconstrained), 3)
        allocations = {(float(w["tissue_inventory_change"]), float(w["conversion"]), float(w["unrecovered"])) for w in unconstrained}
        self.assertEqual(allocations, {(4, 0, 0), (0, 4, 0), (0, 0, 4)})
        constrained = [w for w in witnesses if w["case_id"] == "tissue_observation_leaves_two_sinks"]
        self.assertEqual(len(constrained), 2)
        self.assertTrue(all(float(w["tissue_inventory_change"]) == 1.5 for w in constrained))
        for witness in unconstrained + constrained:
            self.assertEqual(float(witness["sum_allocated"]), float(rows[witness["case_id"]]["collection_corrected_residual"]))
        linear = report["linear_constraints"]
        for matrix, basis in ((linear["fluid_only_matrix"], linear["fluid_only_nullspace_basis"]),
                              (linear["with_tissue_matrix"], linear["with_tissue_nullspace_basis"])):
            for vector in basis:
                self.assertTrue(any(vector))
                for row in matrix:
                    self.assertEqual(sum(a*b for a,b in zip(row, vector)), 0)

    def test_known_zero_tissue_is_distinct_from_missing_and_boundary_is_not_general_identification(self):
        self.config["cases"][2]["observed_tissue_change"] = 0
        self.config["cases"][3]["observed_tissue_change"] = 4
        _, report, _, witnesses = self.publish()
        known_zero = [w for w in witnesses if w["case_id"] == "unresolved_residual_partition"]
        self.assertEqual(len(known_zero), 2)
        boundary = next(c for c in report["cases"] if c["case_id"] == "tissue_observation_leaves_two_sinks")
        self.assertEqual(boundary["n_distinct_witnesses"], 1)
        self.assertEqual(boundary["allocation_status"], "single_partition_at_nonnegative_boundary")
        self.assertEqual(boundary["unknown_partition_dimension_before_nonnegative_constraints"], 1)

    def test_negative_balance_and_tissue_exceeding_balance_are_not_clamped_or_diagnosed(self):
        self.config["cases"][0]["collected_amount"] = 6
        self.config["cases"][3]["observed_tissue_change"] = 5
        _, report, rows, witnesses = self.publish()
        self.assertEqual(float(rows["collection_explains_disappearance"]["collection_corrected_residual"]), -1)
        for cid in ("collection_explains_disappearance", "tissue_observation_leaves_two_sinks"):
            case = next(c for c in report["cases"] if c["case_id"] == cid)
            self.assertEqual(case["allocation_status"], "no_nonnegative_partition_under_declared_assumptions")
            self.assertFalse(any(w["case_id"] == cid for w in witnesses))

    def test_small_inventory_change_survives_large_common_inventory_cancellation(self):
        case = self.config["cases"][0]
        case["initial"] = {"donor_concentration": 1e6, "donor_volume": 1e6,
                           "receiver_concentration": 1e-12, "receiver_volume": 1e-12}
        case["final"] = {**case["initial"], "receiver_concentration": 2e-12}
        case["collected_amount"] = 0
        self.config["cases"] = [case]
        _, _, rows, _ = self.publish()
        actual = rows[case["case_id"]]
        self.assertGreater(float(actual["receiver_inventory_change"]), 0)
        self.assertLess(float(actual["collection_corrected_residual"]), 0)
        self.assertAlmostEqual(float(actual["collection_corrected_residual"]) / 1e-24, -1)

    def test_malformed_nonfinite_and_out_of_domain_inputs_fail_without_publication(self):
        invalid = [None, "1", True, float("nan"), float("inf"), -1, 10**1000, 1e-20]
        for field in ("donor_concentration", "donor_volume"):
            for value in invalid + [1e6 + 1]:
                data = copy.deepcopy(self.config)
                data["cases"][0]["initial"][field] = value
                with self.subTest(field=field, value=str(value)[:30]):
                    with self.assertRaises(InputError):
                        validate_accounting(data)
        for value in invalid + [1e12 + 1]:
            data = copy.deepcopy(self.config)
            data["cases"][0]["supplied_amount"] = value
            with self.assertRaises(InputError):
                validate_accounting(data)
        self.config["cases"][0]["initial"]["donor_volume"] = 0
        with self.assertRaises(InputError):
            self.publish()
        self.assertFalse((self.root / "bundle").exists())

    def test_notice_fields_and_case_budgets_cannot_be_bypassed(self):
        mutations = [lambda c:c.update(schema_version=True), lambda c:c.update(fixture_notice="biological observations"),
            lambda c:c.update(unit="mg"), lambda c:c.update(cases=[]),
            lambda c:c["cases"].append(copy.deepcopy(c["cases"][0])),
            lambda c:c["cases"][0].update(case_id=" padded "),
            lambda c:c["cases"][0]["initial"].update(unmeasured_loss=0),
            lambda c:c.update(cases=[copy.deepcopy(c["cases"][0]) for _ in range(51)])]
        for change in mutations:
            data = copy.deepcopy(self.config)
            change(data)
            with self.assertRaises(InputError):
                validate_accounting(data)

    def test_exclusive_receipt_and_relocation_preserve_integrity_and_review_separation(self):
        bundle, _, _, _ = self.publish()
        with self.assertRaises(InputError):
            collection_accounting(self.root / "input.json", bundle)
        moved = self.root / "moved"
        shutil.copytree(bundle, moved)
        shutil.rmtree(bundle)
        result = verify_bundle(moved, strict=True)
        self.assertTrue(result["bytes_verified"])
        self.assertEqual(result["scientific_review"], "not_established_by_this_tool")
        plan = json.loads((moved / "reproduction_plan.json").read_text())
        self.assertEqual(plan["inputs"], ["input_config.json"])
        self.assertIn("collection-accounting", plan["command"])
