from __future__ import annotations

import copy
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.phenotype_intake import phenotype_report, validate_phenotype_intake

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/phenotype_intake_fixture.json"


class PhenotypeIntakeTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def publish(self, data=None, source_root=None):
        raw = json.dumps(self.data if data is None else data).encode()
        path = self.root / "input.json"
        path.write_bytes(raw)
        bundle = self.root / "bundle"
        phenotype_report(path, bundle, source_root=source_root)
        self.assertEqual((bundle / "input_phenotypes.json").read_bytes(), raw)
        return bundle, json.loads((bundle / "phenotype_report.json").read_text())

    def csv(self, bundle, name):
        with (bundle / name).open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def reject(self, change, pattern=None):
        data = copy.deepcopy(self.data)
        change(data)
        if pattern:
            with self.assertRaisesRegex(InputError, pattern):
                validate_phenotype_intake(data)
        else:
            with self.assertRaises(InputError):
                validate_phenotype_intake(data)

    def test_roster_denominators_exclusions_missingness_and_hierarchy_are_preserved(self):
        bundle, report = self.publish()
        self.assertEqual(report["n_outcomes"], 16)
        rows = self.csv(bundle, "phenotype_outcomes.csv")
        excluded = next(row for row in rows if row["status"] == "excluded")
        self.assertEqual(float(excluded["value"]), 999)
        self.assertTrue(excluded["value_source_locator"])
        groups = self.csv(bundle, "endpoint_groups.csv")
        self.assertEqual(len(groups), 8)
        self.assertTrue(all(row["species"] == "unspecified" and row["interval_time_unit"] == "dimensionless_fixture_time" for row in groups))
        self.assertEqual(sum(int(row["n_declared_specimens"]) for row in groups), 16)
        self.assertEqual(sum(int(row["n_excluded"]) for row in groups), 1)
        self.assertEqual(sum(int(row["n_missing"]) for row in groups), 1)
        self.assertEqual(sum(int(row["n_not_assessed"]) for row in groups), 1)
        self.assertLess(max(float(row["observed_max"]) for row in groups), 1)
        hierarchy = report["hierarchy"][0]
        self.assertEqual(hierarchy["n_declared_specimens"], 8)
        self.assertEqual(hierarchy["n_experiment_labels"], 2)
        self.assertEqual(hierarchy["n_endometrial_source_labels"], 2)
        self.assertEqual(report["effect_estimation"], "not_performed")
        self.assertEqual(report["paired_identity_function_linkage"], "not_assessed")
        self.assertEqual(report["qualification_status"], "unresolved")
        self.assertTrue(any("dimensionless" in text for text in report["analysis_blockers"]))

    def test_absent_duplicate_and_reused_outcomes_cannot_hide_denominators(self):
        self.reject(lambda d: d["cohorts"][0]["outcomes"].pop(), "Every roster")
        self.reject(lambda d: d["cohorts"][0]["outcomes"].append(copy.deepcopy(d["cohorts"][0]["outcomes"][0])), "duplicate")
        self.reject(lambda d: d["cohorts"][0]["outcomes"][1].update(record_id=d["cohorts"][0]["outcomes"][0]["record_id"]), "reused")
        self.reject(lambda d: d["cohorts"][0]["specimens"].pop(), "Unknown")
        self.reject(lambda d: d["cohorts"][0]["endpoints"].append(copy.deepcopy(d["cohorts"][0]["endpoints"][0])), "Duplicate")
        def duplicate_endpoint(d):
            ep = copy.deepcopy(d["cohorts"][0]["endpoints"][0])
            ep["endpoint_id"] = "alias-endpoint"
            d["cohorts"][0]["endpoints"].append(ep)
        self.reject(duplicate_endpoint, "Duplicate endpoint definitions")

    def test_values_status_and_reasons_cannot_conflict(self):
        self.reject(lambda d: d["cohorts"][0]["outcomes"][1].update(status="observed"), "numeric value")
        self.reject(lambda d: d["cohorts"][0]["outcomes"][0].update(status="missing", reason="Invented reason"), "cannot carry numeric")
        self.reject(lambda d: d["cohorts"][0]["outcomes"][2].update(reason=" "))
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["observation"].update(value="0.1"), "finite numeric")
        for value in (float("nan"), float("inf"), True):
            self.reject(lambda d: d["observation_dataset"]["observations"][0]["observation"].update(value=value))

    def test_exact_units_times_source_and_specimen_identity_are_required(self):
        self.reject(lambda d: d["cohorts"][0]["endpoints"][0].update(unit="invented-converted-unit"), "match exactly")
        self.reject(lambda d: d["cohorts"][0]["endpoints"][0].update(measurement_time=3), "ascertainment")
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["independent_unit"].update(id="different-specimen"), "matching individual")
        self.reject(lambda d: d["cohorts"][0]["outcomes"][0]["source"].update(artifact_id="unknown-source"), "unknown source")
        self.reject(lambda d: d["cohorts"][0]["specimens"][0].update(specimen_id=" padded "), "whitespace")
        def outside(d):
            d["cohorts"][0]["endpoints"][0]["measurement_time"] = 5
            for r in d["observation_dataset"]["observations"][::2]:
                r["observation"]["measurement_time"] = 5
        self.reject(outside, "outside")

    def test_pool_summary_and_molecular_identity_cannot_become_individual_phenotypes(self):
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["independent_unit"].update(kind="sample_pool"), "pools")
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["observation"].update(replicate_role="summary_only"), "Summary")
        self.reject(lambda d: d["observation_dataset"]["observations"][0].update(evidence_status="author_reported_summary"), "measurements")
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["assay"].update(measurement_role="molecular_identity"), "Molecular")
        self.reject(lambda d: d["cohorts"][0].update(population="human_embryo"), "separate")
        def relabel_simulation(d):
            d["cohorts"][0]["population"] = "other"
            for record in d["observation_dataset"]["observations"]:
                record["evidence_status"] = "measured"
        self.reject(relabel_simulation, "Simulation")

    def test_different_intervals_and_model_contexts_are_separate(self):
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["developmental_interval"].update(end=3), "separate phenotype cohorts")
        self.reject(lambda d: d["observation_dataset"]["observations"][0]["model_system"].update(label="Invented different model"), "separate phenotype cohorts")
        # Preparation batch labels may differ without pretending they are different model types.
        self.data["observation_dataset"]["observations"][0]["model_system"]["batch_id"] = "invented-batch"
        validate_phenotype_intake(self.data)

    def test_missing_hierarchy_metadata_and_partial_roster_stay_unresolved(self):
        cohort = self.data["cohorts"][0]
        cohort["selection_frame"] = "partial"
        cohort["specimens"][0]["experiment_id"] = None
        cohort["specimens"][1]["endometrial_source_id"] = None
        cohort["conditions"][0]["assignment_note"] = None
        cohort["endpoints"][0]["calibration_note"] = None
        _, report = self.publish()
        self.assertEqual(report["hierarchy"][0]["n_specimens_with_incomplete_hierarchy"], 2)
        self.assertIn("calibration_note", report["measurement_metadata_gaps"][0]["missing_fields"])
        self.assertTrue(any("starting selection" in b for b in report["analysis_blockers"]))
        self.assertTrue(any("assignment" in b for b in report["analysis_blockers"]))

    def test_recorded_review_and_source_hashes_do_not_authenticate_biological_eligibility(self):
        # Invented metadata exercises the non-synthetic branch; it is not evidence or a real review.
        dataset = self.data["observation_dataset"]
        self.data["cohorts"][0]["population"] = "other"
        for record in dataset["observations"]:
            record["evidence_status"] = "measured"
            record["model_system"]["kind"] = "other"
        dataset["source_revision"].update(review_status="locally_reviewed_included", reviewer="Invented reviewer for branch coverage",
            reviewed_on="2026-10-09", review_note="Invented test review assertion; no biological source review.")
        raw = b"Invented source bytes; not a biological study or observation."
        (self.root / "invented.txt").write_bytes(raw)
        dataset["artifacts"][0].update(local_path="invented.txt", sha256=sha256(raw))
        for record in dataset["observations"]:
            record["source"]["sha256"] = sha256(raw)
        _, report = self.publish(source_root=self.root)
        self.assertEqual(report["source_file_verification"]["status"], "complete")
        self.assertEqual(report["qualification_status"], "recorded_requirements_present_for_human_review")
        self.assertFalse(report["human_review_authenticated"])
        self.assertEqual(report["effect_estimation"], "not_performed")

    def test_finite_extreme_values_have_finite_descriptive_median(self):
        records = self.data["observation_dataset"]["observations"]
        records[4]["observation"]["value"] = 1e308
        records[6]["observation"]["value"] = 1e308
        bundle, _ = self.publish()
        rows = self.csv(bundle, "endpoint_groups.csv")
        selected = next(row for row in rows if row["experiment_id"] == "invented-experiment-1" and row["condition_id"] == "group-b" and row["endpoint_id"] == "abstract-area")
        self.assertEqual(float(selected["observed_median"]), 1e308)

    def test_subnormal_values_do_not_vanish_from_descriptive_median(self):
        records = self.data["observation_dataset"]["observations"]
        records[4]["observation"]["value"] = 5e-324
        records[6]["observation"]["value"] = 5e-324
        bundle, _ = self.publish()
        selected = next(row for row in self.csv(bundle, "endpoint_groups.csv") if row["experiment_id"] == "invented-experiment-1" and row["condition_id"] == "group-b" and row["endpoint_id"] == "abstract-area")
        self.assertEqual(float(selected["observed_median"]), 5e-324)

    def test_empty_observed_groups_remain_blank_and_unresolved(self):
        cohort = self.data["cohorts"][0]
        for outcome in cohort["outcomes"]:
            if outcome["endpoint_id"] == "abstract-area" and int(outcome["specimen_id"].rsplit("-", 1)[-1]) % 4 in (3, 0):
                outcome.update(status="excluded", reason="Invented exclusion for empty-group coverage.")
        bundle, report = self.publish()
        empty = [row for row in self.csv(bundle, "endpoint_groups.csv") if row["endpoint_id"] == "abstract-area" and row["condition_id"] == "group-b"]
        self.assertEqual(len(empty), 2)
        self.assertTrue(all(row["observed_median"] == "" and int(row["n_observed"]) == 0 for row in empty))
        self.assertTrue(any("no observed values" in b for b in report["analysis_blockers"]))

    def test_source_mismatch_is_preserved_as_unresolved(self):
        dataset = self.data["observation_dataset"]
        (self.root / "invented.txt").write_bytes(b"Changed artificial file bytes.")
        dataset["artifacts"][0].update(local_path="invented.txt", sha256="0" * 64)
        for record in dataset["observations"]:
            record["source"]["sha256"] = "0" * 64
        _, report = self.publish(source_root=self.root)
        self.assertEqual(report["source_file_verification"]["status"], "mismatch")
        self.assertEqual(report["qualification_status"], "unresolved")
        self.assertTrue(any("source bytes" in b for b in report["analysis_blockers"]))

    def test_exclusive_publication_relocation_and_strict_integrity(self):
        bundle, _ = self.publish()
        with self.assertRaises(InputError):
            phenotype_report(self.root / "input.json", bundle)
        moved = self.root / "moved"
        shutil.copytree(bundle, moved)
        shutil.rmtree(bundle)
        verification = verify_bundle(moved, strict=True)
        self.assertTrue(verification["bytes_verified"])
        self.assertEqual(verification["scientific_review"], "not_established_by_this_tool")
        plan = json.loads((moved / "reproduction_plan.json").read_text())
        self.assertIn("input_phenotypes.json", plan["inputs"])
        self.assertIn("validate-phenotypes", plan["command"])

    def test_bounds_unknown_fields_and_nonfinite_times_fail_before_publication(self):
        self.reject(lambda d: d.update(unexpected=True))
        self.reject(lambda d: d["cohorts"][0]["specimens"].extend(copy.deepcopy(d["cohorts"][0]["specimens"])))
        self.reject(lambda d: d["cohorts"][0]["endpoints"][0].update(measurement_time=float("inf")))
        self.reject(lambda d: d["cohorts"][0]["endpoints"][0].update(measurement_time=10**1000))
        self.reject(lambda d: d["cohorts"].extend([copy.deepcopy(d["cohorts"][0])] * 20))
        self.data["cohorts"][0]["outcomes"].pop()
        with self.assertRaises(InputError):
            self.publish()
        self.assertFalse((self.root / "bundle").exists())
