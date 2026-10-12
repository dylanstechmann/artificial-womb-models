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
from wombmodels.observations import FUNCTIONAL_EVIDENCE_CLASSES, observation_report, validate_dataset

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "observation_intake_fixture.json"


class ObservationIntakeTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def publish(self, data=None):
        source = self.root / "dataset.json"
        raw = json.dumps(self.data if data is None else data).encode("utf-8")
        source.write_bytes(raw)
        bundle = self.root / "intake"
        observation_report(source, bundle)
        self.assertEqual((bundle / "input_dataset.json").read_bytes(), raw)
        return bundle, json.loads((bundle / "observation_intake_report.json").read_text())

    def test_containment_report_relocates_and_verifies_without_promoting_review(self):
        bundle, report = self.publish()
        self.assertEqual(report["source_interval_containment"], {
            "n_contained": 2, "n_partially_checked": 0, "n_not_assessed": 0,
            "scientific_transcription": "not_verified"})
        self.assertEqual(report["source_review_status"], "candidate")
        self.assertEqual(report["n_continuity_not_reported"], 1)
        with (bundle / "source_scopes.csv").open(newline="") as stream:
            scope = next(csv.DictReader(stream))
        self.assertEqual(scope["source_locator"], self.data["artifacts"][0]["developmental_scope"]["source_locator"])
        moved = self.root / "moved"
        shutil.copytree(bundle, moved)
        shutil.rmtree(bundle)
        result = verify_bundle(moved, strict=True)
        self.assertTrue(result["bytes_verified"], result["errors"])
        self.assertEqual(result["scientific_review"], "not_established_by_this_tool")
        plan = json.loads((moved / "reproduction_plan.json").read_text())
        self.assertEqual(plan["inputs"], ["input_dataset.json"])
        self.assertIn("validate-observations", plan["command"])

    def test_case_to_group_summary_keeps_continuity_unreported(self):
        data = copy.deepcopy(self.data)
        case = copy.deepcopy(data["observations"][0])
        case["record_id"] = "synthetic-case-a"
        case["independent_unit"] = {
            "kind": "other", "id": "case-A", "parent_id": None,
            "hierarchy_note": "Synthetic case identifier for intake-contract validation.",
        }

        summary = copy.deepcopy(case)
        summary["record_id"] = "synthetic-terminal-group-summary"
        summary["assay"]["endpoint"] = "synthetic terminal group summary"
        summary["independent_unit"] = {
            "kind": "sample_pool", "id": "terminal-group", "parent_id": None,
            "hierarchy_note": "Synthetic aggregate; individual membership is intentionally undeclared.",
        }
        summary["observation"]["replicate_role"] = "summary_only"
        summary["source_locator"] = "Synthetic fixture only; no biological source row."

        data["observations"] = [case, summary]
        data["transitions"] = [{
            "transition_id": "synthetic-case-to-terminal-group",
            "from_record_ids": [case["record_id"]],
            "to_record_ids": [summary["record_id"]],
            "continuity_status": "not_reported",
            "note": "Synthetic contract case: no individual mapping is declared from a case to this aggregate.",
        }]

        validated = validate_dataset(copy.deepcopy(data))
        self.assertEqual(validated["transitions"][0]["continuity_status"], "not_reported")
        self.assertEqual(validated["observations"][1]["independent_unit"]["kind"], "sample_pool")

        data["transitions"][0]["continuity_status"] = "demonstrated"
        with self.assertRaisesRegex(InputError, "sample pool cannot establish"):
            validate_dataset(data)

    def test_individual_source_locator_is_validated_and_exported(self):
        self.data["observations"][0]["source_locator"] = "Workbook sheet 'Data'!G18"
        bundle, _ = self.publish()
        with (bundle / "observation_records.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["source_locator"], "Workbook sheet 'Data'!G18")
        self.assertEqual(json.loads(rows[0]["source_qualifications_json"]), [])
        for value in ("", {}, "x" * 1001):
            with self.subTest(value=str(value)[:20]):
                data = copy.deepcopy(self.data)
                data["observations"][0]["source_locator"] = value
                with self.assertRaisesRegex(InputError, "source_locator"):
                    validate_dataset(data)

    def test_independent_observation_can_preserve_anonymous_unit_without_linking_it(self):
        data = copy.deepcopy(self.data)
        first = data["observations"][0]
        first["independent_unit"].update(
            kind="pregnant_animal", id=None, parent_id=None,
            hierarchy_note="Source reports this as an independent recipient mouse but does not give its identity.",
        )
        first["observation"]["replicate_role"] = "independent"
        validate_dataset(data)
        self.assertIsNone(first["independent_unit"]["id"])

        # Anonymous units remain ineligible for demonstrated same-unit continuity.
        second = copy.deepcopy(first)
        second["record_id"] = "anonymous-later-observation"
        second["assay"]["endpoint"] = "later fixture endpoint"
        data["observations"] = [first, second]
        data["transitions"] = [{
            "transition_id": "anonymous-continuity-test",
            "from_record_ids": [first["record_id"]],
            "to_record_ids": [second["record_id"]],
            "continuity_status": "demonstrated",
            "note": "An anonymous unit cannot authenticate a same-unit link.",
        }]
        with self.assertRaisesRegex(InputError, "Demonstrated continuity needs the same reported unit"):
            validate_dataset(data)

    def test_optional_source_qualifications_are_typed_linked_and_exported(self):
        qualification = {
            "criterion_code": "reported_window",
            "status_code": "inside_window",
            "criterion_label": "Source-reported observation window",
            "source_artifact_id": "synthetic-source",
            "source_locator": "Workbook sheet 'Data'!G18",
            "reference_value": 6,
            "reference_unit": "hour",
        }
        self.data["observations"][0]["observation"]["source_qualifications"] = [qualification]
        bundle, report = self.publish()
        self.assertEqual(report["source_qualifications"], {
            "n_records_with_declarations": 1, "n_declarations": 1,
            "interpretation": "source-linked declarations; not scientific validation"})
        with (bundle / "observation_records.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(json.loads(rows[0]["source_qualifications_json"]), [qualification])
        self.assertEqual(json.loads(rows[1]["source_qualifications_json"]), [])

    def test_typed_median_iqr_summary_is_preserved_and_exported(self):
        data = copy.deepcopy(self.data)
        record = data["observations"][0]
        record["evidence_status"] = "author_reported_summary"
        record["independent_unit"].update(
            kind="other", id=None, parent_id=None,
            hierarchy_note="Aggregate statistic; contributing participant identities are not reported.",
        )
        record["observation"].update(
            value=10.0, measurement_time=None, measurement_time_unit="",
            replicate_role="summary_only",
            summary_statistic={
                "kind": "median_iqr", "lower_quartile": 8.0, "upper_quartile": 14.0,
                "reported_sample_size": 22,
                "sample_size_scope": "Source-reported stratum denominator; not endpoint-specific.",
                "sample_size_source_locator": "Table 2 header, N row, vessel column",
                "source_literal": "10 [8, 14]",
            },
        )
        data["source_revision"]["source_kind"] = "peer_reviewed_human_invivo"
        bundle, report = self.publish(data)
        self.assertEqual(report["source_kind"], "peer_reviewed_human_invivo")
        self.assertEqual(report["summary_statistics"]["n_records"], 1)
        self.assertEqual(report["summary_statistics"]["n_median_iqr"], 1)
        with (bundle / "observation_records.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(json.loads(rows[0]["summary_statistic_json"]),
                         data["observations"][0]["observation"]["summary_statistic"])
        self.assertEqual(json.loads(rows[1]["summary_statistic_json"]), None)

    def test_typed_median_iqr_rejects_bad_order_denominator_or_role(self):
        valid = {
            "kind": "median_iqr", "lower_quartile": 8.0, "upper_quartile": 14.0,
            "reported_sample_size": 22,
            "sample_size_scope": "Source-reported vessel denominator.",
            "sample_size_source_locator": "Table 2 N row, vessel column",
            "source_literal": "10 [8, 14]",
        }
        cases = [
            (dict(valid, lower_quartile=11.0), "lower <= median <= upper"),
            (dict(valid, reported_sample_size=22.0), "positive integer or null"),
            (dict(valid, sample_size_scope=" "), "sample_size_scope"),
            (dict(valid, source_literal=""), "source_literal"),
        ]
        for summary, message in cases:
            with self.subTest(summary=summary):
                data = copy.deepcopy(self.data)
                record = data["observations"][0]
                record["evidence_status"] = "author_reported_summary"
                record["independent_unit"].update(kind="other", id=None, parent_id=None)
                record["observation"].update(value=10.0, replicate_role="summary_only",
                                              summary_statistic=summary)
                with self.assertRaisesRegex(InputError, message):
                    validate_dataset(data)

        data = copy.deepcopy(self.data)
        record = data["observations"][0]
        record["observation"]["value"] = 10.0
        record["observation"]["summary_statistic"] = valid
        with self.assertRaisesRegex(InputError, "author_reported_summary with summary_only"):
            validate_dataset(data)

    def test_holm_public_aggregate_intake_exports_medians_quartiles_and_scope(self):
        dataset_path = Path(__file__).resolve().parents[1] / "config/observations/holm_2017_term_amino_acid_concentrations_candidate.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "holm-intake"
            observation_report(dataset_path, output, source_root=dataset_path.parents[2])
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_kind"], "peer_reviewed_human_invivo")
            self.assertEqual(report["n_observation_records"], 76)
            self.assertEqual(report["summary_statistics"]["n_records"], 76)
            self.assertEqual(report["summary_statistics"]["n_median_iqr"], 76)
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 76)
            alanine = next(row for row in rows if row["record_id"] == "holm2017-table2-alanine-uterine-vein")
            summary = json.loads(alanine["summary_statistic_json"])
            self.assertEqual(alanine["value"], "255.0")
            self.assertEqual(summary["lower_quartile"], 2.0)
            self.assertEqual(summary["upper_quartile"], 294.0)
            self.assertEqual(summary["source_literal"], "255 [2, 294]")
            self.assertEqual(summary["reported_sample_size"], 177)
            self.assertIn("not analyte-specific", summary["sample_size_scope"])
            self.assertEqual(alanine["independent_unit_id"], "")

    def test_holm_table3_intake_exports_p_values_and_fdr_source_markers(self):
        dataset_path = Path(__file__).resolve().parents[1] / "config/observations/holm_2017_term_amino_acid_differences_candidate.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "holm-table3-intake"
            observation_report(dataset_path, output, source_root=dataset_path.parents[2])
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_kind"], "peer_reviewed_human_invivo")
            self.assertEqual(report["n_observation_records"], 76)
            self.assertEqual(report["summary_statistics"]["n_median_iqr"], 76)
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            glutamate = next(row for row in rows if row["record_id"] == "holm2017-table3-glutamic-acid-umbilical-water-adjusted")
            qualifications = json.loads(glutamate["source_qualifications_json"])
            p_value = next(item for item in qualifications if item["criterion_code"] == "published_p_value")
            marker = next(item for item in qualifications if item["criterion_code"] == "source_bold_marker")
            self.assertIn("<0.001", p_value["criterion_label"])
            self.assertEqual(marker["status_code"], "marked_bold")
            self.assertIn("after FDR correction", marker["criterion_label"])
            self.assertEqual(glutamate["unit"], "μmol/L")
            self.assertEqual(glutamate["replicate_role"], "summary_only")

    def test_source_qualifications_reject_malformed_or_unlinked_declarations(self):
        valid = {"criterion_code": "reported_window", "status_code": "inside_window",
                 "criterion_label": "Reported observation window",
                 "source_artifact_id": "synthetic-source", "source_locator": "Table 1, row 2",
                 "reference_value": 6, "reference_unit": "hour"}
        malformed = [
            {**valid, "extra": "unknown"},
            {**valid, "criterion_code": "Uppercase"},
            {**valid, "source_artifact_id": "missing-source"},
            {**valid, "reference_value": "six"},
            {**valid, "reference_unit": ""},
            {**valid, "source_locator": " "},
        ]
        for qualification in malformed:
            with self.subTest(qualification=qualification):
                data = copy.deepcopy(self.data)
                data["observations"][0]["observation"]["source_qualifications"] = [qualification]
                with self.assertRaises(InputError):
                    validate_dataset(data)
        data = copy.deepcopy(self.data)
        data["observations"][0]["observation"]["source_qualifications"] = [valid, dict(valid)]
        with self.assertRaisesRegex(InputError, "distinct"):
            validate_dataset(data)
        data = copy.deepcopy(self.data)
        data["observations"][0]["observation"]["source_qualifications"] = [valid] * 21
        with self.assertRaisesRegex(InputError, "at most 20"):
            validate_dataset(data)

    def test_legacy_card_without_source_scope_remains_unassessed(self):
        del self.data["artifacts"][0]["developmental_scope"]
        _, report = self.publish()
        self.assertEqual(report["source_interval_containment"]["n_not_assessed"], 2)
        self.assertTrue(any("containment was not assessed" in item for item in report["warnings"]))

    def test_preprint_class_and_review_state_remain_separate(self):
        for review_state in ("candidate", "locally_reviewed_included"):
            with self.subTest(review_state=review_state):
                data = copy.deepcopy(self.data)
                revision = data["source_revision"]
                revision.update(source_kind="preprint", review_status=review_state)
                if review_state == "locally_reviewed_included":
                    revision.update(reviewer="Recorded fixture reviewer", reviewed_on="2026-10-09",
                                    review_note="Invented local review metadata; no journal review or biological eligibility established.")
                bundle, report = self.publish(data)
                self.assertEqual(report["source_kind"], "preprint")
                self.assertEqual(report["source_review_status"], review_state)
                self.assertTrue(any("does not establish journal peer review" in warning
                                    for warning in report["warnings"]))
                self.assertFalse(report["biological_assay_performed"])
                self.assertIn("requires source-specific human review", report["analysis_eligibility"])
                self.assertEqual(report["n_continuity_not_reported"], 1)
                self.assertIn("Declared source class: preprint", (bundle / "REPORT.md").read_text())
                verified = verify_bundle(bundle, strict=True)
                self.assertTrue(verified["bytes_verified"], verified["errors"])
                self.assertEqual(verified["scientific_review"], "not_established_by_this_tool")
                shutil.rmtree(bundle)

    def test_unknown_source_class_still_rejected(self):
        self.data["source_revision"]["source_kind"] = "preprint_peer_reviewed"
        with self.assertRaisesRegex(InputError, "source kind"):
            validate_dataset(self.data)

    @staticmethod
    def context(compartment="fixture compartment"):
        return {"compartment": compartment, "material": "invented tracer",
                "process": "passage", "quantity_basis": "dimensionless fixture signal",
                "assessment_context": "simulation", "source_locator": "Invented metadata only"}

    def test_functional_context_export_preserves_distinct_compartments_and_integrity(self):
        first = self.data["observations"][0]
        second = copy.deepcopy(first)
        second["record_id"] = "synthetic-other-compartment"
        first["assay"]["functional_context"] = self.context("fixture tissue")
        second["assay"]["functional_context"] = self.context("fixture receiver")
        self.data["observations"] = [first, second]
        self.data["transitions"] = []
        bundle, report = self.publish()
        self.assertEqual(report["n_exact_comparison_groups"], 2)
        self.assertEqual(report["functional_context"], {
            "n_declared": 2, "n_not_declared": 0, "scientific_transcription": "not_verified"})
        with (bundle / "functional_contexts.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["compartment"] for row in rows], ["fixture tissue", "fixture receiver"])
        self.assertTrue(all(row["source_artifact_id"] == "synthetic-source" for row in rows))
        self.assertIn("not verified mechanisms", (bundle / "REPORT.md").read_text())
        moved = self.root / "moved-context"
        shutil.copytree(bundle, moved)
        self.assertTrue(verify_bundle(moved, strict=True)["bytes_verified"])
        (moved / "functional_contexts.csv").write_text("changed context\n")
        self.assertFalse(verify_bundle(moved, strict=True)["bytes_verified"])

    def test_absent_functional_context_not_inferred_from_endpoint(self):
        self.data["observations"][0]["assay"]["endpoint"] = "Tissue uptake and secretion"
        bundle, report = self.publish()
        self.assertEqual(report["functional_context"]["n_declared"], 0)
        self.assertEqual(report["functional_context"]["n_not_declared"], 2)
        self.assertEqual(report["functional_evidence_classes"]["n_not_declared"], 2)
        with (bundle / "functional_contexts.csv").open(newline="") as stream:
            self.assertEqual(list(csv.DictReader(stream)), [])
        with (bundle / "observation_records.csv").open(newline="") as stream:
            self.assertTrue(all(row["functional_evidence_class"] == "" for row in csv.DictReader(stream)))

    def test_functional_evidence_classes_validate_export_and_remain_distinct(self):
        first = self.data["observations"][0]
        first["assay"]["functional_evidence_class"] = "direct_function_measurement"
        second = copy.deepcopy(first)
        second["record_id"] = "synthetic-response-proxy"
        second["assay"]["functional_evidence_class"] = "biological_response_proxy"
        second["assay"]["endpoint"] = "synthetic response marker"
        third = copy.deepcopy(first)
        third["record_id"] = "synthetic-developmental-outcome"
        third["assay"]["functional_evidence_class"] = "developmental_outcome"
        third["assay"]["endpoint"] = "synthetic growth outcome"
        self.data["observations"] = [first, second, third]
        self.data["transitions"] = []
        bundle, report = self.publish()
        self.assertEqual(report["functional_evidence_classes"]["counts"], {
            "biological_response_proxy": 1,
            "developmental_outcome": 1,
            "direct_function_measurement": 1,
            "other": 0,
        })
        self.assertEqual(report["functional_evidence_classes"]["n_not_declared"], 0)
        with (bundle / "observation_records.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["functional_evidence_class"] for row in rows], [
            "direct_function_measurement", "biological_response_proxy", "developmental_outcome"])
        with (bundle / "interval_groups.csv").open(newline="") as stream:
            groups = list(csv.DictReader(stream))
        self.assertEqual({row["functional_evidence_class"] for row in groups}, {
            "direct_function_measurement", "biological_response_proxy", "developmental_outcome"})
        invalid = copy.deepcopy(self.data)
        invalid["observations"][0]["assay"]["functional_evidence_class"] = "placental_replacement_proven"
        with self.assertRaisesRegex(InputError, "functional evidence class"):
            validate_dataset(invalid)

    def test_functional_evidence_class_schema_matches_runtime_vocabulary(self):
        schema_path = EXAMPLE.parents[1] / "schemas/developmental-observation.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        declared = set(schema["properties"]["assay"]["properties"]["functional_evidence_class"]["enum"])
        self.assertEqual(declared, FUNCTIONAL_EVIDENCE_CLASSES)

    def test_functional_context_rejects_partial_unknown_and_unbounded_metadata(self):
        bad = [None, {}, {**self.context(), "extra": "unknown"},
               {**self.context(), "compartment": " "},
               {**self.context(), "material": "x" * 301},
               {**self.context(), "quantity_basis": 1},
               {**self.context(), "source_locator": "x" * 1001},
               {**self.context(), "process": "adequate_delivery"},
               {**self.context(), "assessment_context": "clinical_ready"}]
        for context in bad:
            with self.subTest(context=context):
                data = copy.deepcopy(self.data)
                data["observations"][0]["assay"]["functional_context"] = context
                with self.assertRaises(InputError):
                    validate_dataset(data)

    def test_material_handoff_candidate_keeps_context_selection_and_missingness(self):
        path = EXAMPLE.parents[1] / "config/observations/koike_2023_material_handoff_candidate.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        _, report = self.publish(data)
        self.assertEqual(report["source_kind"], "peer_reviewed_animal")
        self.assertEqual(report["source_review_status"], "candidate")
        self.assertEqual(report["n_observation_records"], 14)
        self.assertEqual(report["functional_context"]["n_declared"], 14)
        self.assertEqual(report["n_continuity_not_reported"], 2)
        self.assertTrue(all(row["independent_unit"]["id"] is None for row in data["observations"]))
        rows = {row["record_id"]: row for row in data["observations"]}
        self.assertEqual(rows["koike-vegf-fluid"]["assay"]["functional_context"]["assessment_context"], "in_utero")
        self.assertEqual(rows["koike-vegf-release"]["assay"]["functional_context"]["assessment_context"], "isolated_tissue")
        self.assertEqual(rows["koike-other-branch-arrest"]["assay"]["measurement_role"], "adverse_effect")
        self.assertEqual(rows["koike-embryonic-use-gap"]["evidence_status"], "planned")
        self.assertIsNone(rows["koike-embryonic-use-gap"]["observation"]["value"])
        data["transitions"][0]["continuity_status"] = "demonstrated"
        with self.assertRaisesRegex(InputError, "same reported unit"):
            validate_dataset(data)

    def test_yolk_sac_candidate_does_not_promote_proxies_or_infer_embryo_age(self):
        path = EXAMPLE.parents[1] / "config/observations/jin_2026_yolk_sac_candidate.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        _, report = self.publish(data)
        self.assertEqual(report["source_review_status"], "candidate")
        self.assertEqual(report["n_observation_records"], 13)
        self.assertEqual(report["n_continuity_not_reported"], 1)
        self.assertEqual(report["source_interval_containment"]["n_contained"], 0)
        rows = {row["record_id"]: row for row in data["observations"]}
        for key in ("jin-lysosomal-proxy", "jin-barrier-transcripts", "jin-coagulation-transcripts"):
            self.assertEqual(rows[key]["assay"]["measurement_role"], "molecular_identity")
        self.assertEqual(rows["jin-embryo-arrest"]["assay"]["measurement_role"], "adverse_effect")
        self.assertEqual(rows["jin-paired-recipient-gap"]["evidence_status"], "planned")
        self.assertTrue(all(row["observation"]["value"] is None or isinstance(row["observation"]["value"], str)
                            for row in data["observations"]))
        self.assertTrue(all(row["independent_unit"]["id"] is None for row in data["observations"]))
        data["transitions"][0]["continuity_status"] = "demonstrated"
        with self.assertRaisesRegex(InputError, "same reported unit"):
            validate_dataset(data)

    def test_terminal_candidate_retains_missing_source_identity_and_unknown_continuity(self):
        path = EXAMPLE.parents[1] / "config/observations/lokshtanov_2026_terminal_candidate.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        _, report = self.publish(data)
        self.assertEqual(report["source_kind"], "preprint")
        self.assertEqual(report["source_review_status"], "candidate")
        self.assertEqual(report["n_observation_records"], 12)
        self.assertEqual(report["n_continuity_not_reported"], 2)
        self.assertEqual(report["source_interval_containment"]["n_contained"], 0)
        self.assertTrue(all(item["sha256"] for item in data["artifacts"]))
        self.assertEqual(report["source_file_verification"]["status"], "not_requested")
        self.assertTrue(all(row["independent_unit"]["id"] is None for row in data["observations"]))
        missing = [row for row in data["observations"] if row["observation"]["value"] is None]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["evidence_status"], "planned")
        self.assertEqual(missing[0]["assay"]["measurement_role"], "durability")
        data["transitions"][0]["continuity_status"] = "demonstrated"
        with self.assertRaisesRegex(InputError, "same reported unit"):
            validate_dataset(data)

    def test_textual_and_missing_bounds_are_not_inferred_from_prose(self):
        for bounds in (("early", "later"), (None, None), (0, None)):
            with self.subTest(bounds=bounds):
                data = copy.deepcopy(self.data)
                interval = data["observations"][0]["developmental_interval"]
                interval["start"], interval["end"] = bounds
                bundle, report = self.publish(data)
                self.assertEqual(report["source_interval_containment"]["n_contained"], 1)
                self.assertEqual(report["source_interval_containment"]["n_not_assessed"], 1)
                with (bundle / "source_interval_checks.csv").open(newline="") as stream:
                    expected = "partially_checked" if bounds == (0, None) else "not_numeric"
                    self.assertEqual(next(csv.DictReader(stream))["status"], expected)
                self.assertEqual(report["source_interval_containment"]["n_partially_checked"],
                                 int(bounds == (0, None)))
                shutil.rmtree(bundle)

    def test_one_sided_source_scope_preserves_unknown_bound_without_full_containment(self):
        for bounds in ((0, None), (None, 4), (None, None)):
            with self.subTest(bounds=bounds):
                data = copy.deepcopy(self.data)
                scope = data["artifacts"][0]["developmental_scope"]
                scope["start"], scope["end"] = bounds
                bundle, report = self.publish(data)
                self.assertEqual(report["source_interval_containment"]["n_contained"], 0)
                self.assertEqual(report["source_interval_containment"]["n_not_assessed"], 2)
                self.assertEqual(report["source_interval_containment"]["n_partially_checked"],
                                 0 if bounds == (None, None) else 2)
                with (bundle / "source_scopes.csv").open(newline="") as stream:
                    exported = next(csv.DictReader(stream))
                for field, bound in zip(("start", "end"), bounds):
                    self.assertEqual(exported[field], "" if bound is None else str(bound))
                with (bundle / "source_interval_checks.csv").open(newline="") as stream:
                    statuses = {row["status"] for row in csv.DictReader(stream)}
                self.assertEqual(statuses, {"source_bounds_unknown" if bounds == (None, None)
                                            else "partially_checked"})
                self.assertTrue(verify_bundle(bundle, strict=True)["bytes_verified"])
                shutil.rmtree(bundle)

    def test_partial_intervals_still_reject_any_numeric_bound_outside_known_scope(self):
        cases = [((0, None), (-0.01, None)), ((0, None), (None, -0.01)),
                 ((None, 4), (4.01, None)), ((None, 4), (None, 4.01)),
                 ((0, 4), (-0.01, None)), ((0, 4), (None, 4.01))]
        for source_bounds, record_bounds in cases:
            with self.subTest(source=source_bounds, record=record_bounds):
                data = copy.deepcopy(self.data)
                scope = data["artifacts"][0]["developmental_scope"]
                scope["start"], scope["end"] = source_bounds
                interval = data["observations"][0]["developmental_interval"]
                interval["start"], interval["end"] = record_bounds
                with self.assertRaisesRegex(InputError, "outside.*bounds"):
                    self.publish(data)
                self.assertFalse((self.root / "intake").exists())

    def test_missing_source_bounds_do_not_bypass_species_stage_or_unit_checks(self):
        for field, value in (("species", "human"), ("stage_track", "partial_fetal_support"),
                             ("time_unit", "days")):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["artifacts"][0]["developmental_scope"].update(start=None, end=None)
                record = data["observations"][0]
                target = record["developmental_interval"] if field == "time_unit" else record
                target[field] = value
                with self.assertRaisesRegex(InputError, "source.*scope"):
                    validate_dataset(data)

    def test_rejects_widened_source_intervals_and_preserves_destination(self):
        for start, end in ((-0.01, 2), (0, 4.01)):
            with self.subTest(start=start, end=end):
                data = copy.deepcopy(self.data)
                data["observations"][0]["developmental_interval"].update(start=start, end=end)
                with self.assertRaisesRegex(InputError, "outside.*bounds"):
                    self.publish(data)
                self.assertFalse((self.root / "intake").exists())

    def test_rejects_species_stage_and_unit_mismatch(self):
        for field, value in (("species", "human"), ("stage_track", "partial_fetal_support"),
                             ("time_unit", "days"), ("time_unit", "dimensionless_fixture_time ")):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                record = data["observations"][0]
                target = record["developmental_interval"] if field == "time_unit" else record
                target[field] = value
                with self.assertRaisesRegex(InputError, "source.*scope"):
                    validate_dataset(data)

    def test_rejects_malformed_scope(self):
        changes = [{"start": True}, {"end": float("inf")}, {"end": float("nan")},
                   {"start": 10 ** 400},
                   {"start": "0"}, {"end": -1}, {"source_locator": " "},
                   {"species": "unknown"}, {"stage_tracks": []},
                   {"stage_tracks": ["unspecified", "unspecified"]}, {"stage_tracks": [{}]},
                   {"extra": "unknown"}]
        for change in changes:
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                data["artifacts"][0]["developmental_scope"].update(change)
                with self.assertRaises(InputError):
                    validate_dataset(data)

    def test_scope_binding_uses_stage_source_instead_of_measurement_source(self):
        other = copy.deepcopy(self.data["artifacts"][0])
        other["artifact_id"] = "separate-stage-source"
        other["developmental_scope"]["end"] = 1
        self.data["artifacts"].append(other)
        self.data["observations"][0]["developmental_interval"]["stage_source_artifact_id"] = other["artifact_id"]
        with self.assertRaisesRegex(InputError, "outside.*bounds"):
            validate_dataset(self.data)

    def test_declared_scope_does_not_replace_other_intake_checks(self):
        changes = [lambda row: row["source"].update(sha256="a" * 64),
                   lambda row: row["observation"].update(value=None),
                   lambda row: row["assay"].update(calibration_artifact_id="unknown")]
        for change in changes:
            data = copy.deepcopy(self.data)
            change(data["observations"][0])
            with self.assertRaises(InputError):
                validate_dataset(data)
        self.data["observations"][0]["observation"]["replicate_role"] = "independent"
        with self.assertRaisesRegex(InputError, "Repeated rows"):
            self.publish()

    def test_changed_scope_bytes_fail_bundle_verification(self):
        bundle, _ = self.publish()
        (bundle / "source_scopes.csv").write_text("changed scope\n")
        self.assertFalse(verify_bundle(bundle, strict=True)["bytes_verified"])

    @staticmethod
    def coverage_record(coverage_id, *, label="Exp 1", endpoint="fixture endpoint",
                        counted_entity_kind="embryo", denominator=5, declarations=None,
                        cohort_window_status="source_labels_only", completeness="partial",
                        mutually_exclusive="unknown", exhaustive="unknown"):
        if declarations is None:
            declarations = [
                ("retained", "within_denominator", 3),
                ("assay_withdrawn", "outside_denominator", 1),
            ]
        return {
            "coverage_id": coverage_id,
            "source_artifact_id": "synthetic-source",
            "reported_group_label": label,
            "group_label_status": "reported",
            "counted_entity_kind": counted_entity_kind,
            "counted_entity_label": f"invented {counted_entity_kind} units",
            "endpoint_label": endpoint,
            "population_frame": "Invented, dimensionless software fixture population",
            "measurement_window": "fixture window A",
            "selection_definition": "Invented selection rule; no biological units or measurements.",
            "selection_definition_source_locator": "Fixture metadata / selection",
            "denominator": {
                "value": denominator,
                "value_status": "reported",
                "reported_label": f"invented denominator {denominator}",
                "source_locator": "Fixture metadata / denominator",
            },
            "declarations": [
                {
                    "category": category,
                    "scope": scope,
                    "reported_label": f"invented {category} value {value}",
                    "quantity_kind": "count",
                    "value": value,
                    "value_status": "reported" if value is not None else "not_reported",
                    "source_locator": f"Fixture metadata / {category}",
                    "note": "Artificial acceptance fixture only.",
                }
                for category, scope, value in declarations
            ],
            "selection_statements": [{
                "text": "Invented fixture statement: one unit was withdrawn from later assessment.",
                "source_locator": "Fixture metadata / selection statement",
            }],
            "cohort_window_status": cohort_window_status,
            "disposition_completeness": completeness,
            "categories_mutually_exclusive": mutually_exclusive,
            "categories_exhaustive": exhaustive,
        }

    def test_fetus_is_a_first_class_independent_and_counted_entity(self):
        data = copy.deepcopy(self.data)
        data["observations"][0]["independent_unit"] = {
            "kind": "fetus", "id": "source-case-a", "parent_id": None,
            "hierarchy_note": "Synthetic schema fixture only; no biological source data.",
        }
        data["cohort_coverage"] = [self.coverage_record(
            "synthetic-fetus-cohort", counted_entity_kind="fetus")]

        validated = validate_dataset(data)
        self.assertEqual(validated["observations"][0]["independent_unit"]["kind"], "fetus")
        self.assertEqual(validated["cohort_coverage"][0]["counted_entity_kind"], "fetus")

    def test_aggregate_coverage_preserves_withdrawals_partiality_and_label_collisions(self):
        data = copy.deepcopy(self.data)
        data["cohort_coverage"] = [
            self.coverage_record("fixture-coverage-a", label="Exp 1"),
            self.coverage_record("fixture-coverage-b", label="Exp 1", endpoint="other fixture endpoint",
                                 counted_entity_kind="tissue_fragment", denominator=4),
        ]
        bundle, report = self.publish(data)

        self.assertEqual(report["n_observation_records"], len(data["observations"]))
        self.assertEqual(report["n_cohort_coverage_records"], 2)
        self.assertEqual(report["n_continuity_not_reported"], 1)
        self.assertTrue(all(check["status"] == "not_assessed"
                            for check in report["cohort_coverage_checks"]))
        with (bundle / "observation_records.csv").open(newline="") as stream:
            observation_rows = list(csv.DictReader(stream))
        self.assertEqual({row["record_id"] for row in observation_rows},
                         {row["record_id"] for row in data["observations"]})
        self.assertEqual({row["independent_unit_id"] for row in observation_rows},
                         {row["independent_unit"]["id"] for row in data["observations"]})
        with (bundle / "cohort_coverage.csv").open(newline="") as stream:
            coverage_rows = list(csv.DictReader(stream))
        self.assertEqual([row["coverage_id"] for row in coverage_rows],
                         ["fixture-coverage-a", "fixture-coverage-b"])
        self.assertEqual([row["reported_group_label"] for row in coverage_rows], ["Exp 1", "Exp 1"])
        self.assertEqual([row["counted_entity_kind"] for row in coverage_rows], ["embryo", "tissue_fragment"])
        with (bundle / "cohort_dispositions.csv").open(newline="", encoding="utf-8") as stream:
            declaration_rows = list(csv.DictReader(stream))
        withdrawal = next(row for row in declaration_rows
                          if row["coverage_id"] == "fixture-coverage-a"
                          and row["category"] == "assay_withdrawn")
        self.assertEqual(withdrawal["scope"], "outside_denominator")
        self.assertEqual(withdrawal["value"], "1")
        self.assertIn("Fixture metadata / assay_withdrawn", withdrawal["source_locator"])
        self.assertTrue(verify_bundle(bundle, strict=True)["bytes_verified"])

        before = {path.name: path.read_bytes() for path in bundle.iterdir() if path.is_file()}
        source = self.root / "dataset.json"
        with self.assertRaisesRegex(InputError, "Output already exists"):
            observation_report(source, bundle)
        self.assertEqual(before, {path.name: path.read_bytes() for path in bundle.iterdir() if path.is_file()})

    def test_coverage_closure_requires_a_source_declared_partition(self):
        data = copy.deepcopy(self.data)
        data["cohort_coverage"] = [
            self.coverage_record("fixture-partial", denominator=5,
                                 declarations=[("retained", "within_denominator", 3),
                                               ("shed", "within_denominator", 1)],
                                 completeness="partial"),
            self.coverage_record("fixture-unresolved-membership", denominator=5,
                                 declarations=[("retained", "unresolved", 3),
                                               ("shed", "within_denominator", 2)],
                                 cohort_window_status="source_reported_common", completeness="complete",
                                 mutually_exclusive="source_reported_yes", exhaustive="source_reported_yes"),
            self.coverage_record("fixture-complete-match", denominator=5,
                                 declarations=[("retained", "within_denominator", 3),
                                               ("shed", "within_denominator", 2)],
                                 cohort_window_status="source_reported_common", completeness="complete",
                                 mutually_exclusive="source_reported_yes", exhaustive="source_reported_yes"),
            self.coverage_record("fixture-complete-mismatch", denominator=5,
                                 declarations=[("retained", "within_denominator", 3),
                                               ("shed", "within_denominator", 1)],
                                 cohort_window_status="source_reported_common", completeness="complete",
                                 mutually_exclusive="source_reported_yes", exhaustive="source_reported_yes"),
            self.coverage_record("fixture-overlapping-category", denominator=5,
                                 declarations=[("retained", "within_denominator", 3),
                                               ("retained", "within_denominator", 2)],
                                 cohort_window_status="source_reported_common", completeness="complete",
                                 mutually_exclusive="source_reported_yes", exhaustive="source_reported_yes"),
        ]

        _, report = self.publish(data)
        checks = {item["coverage_id"]: item for item in report["cohort_coverage_checks"]}
        self.assertEqual(checks["fixture-partial"]["status"], "not_assessed")
        self.assertEqual(checks["fixture-unresolved-membership"]["status"], "not_assessed")
        self.assertEqual(checks["fixture-complete-match"]["status"], "matches")
        self.assertEqual(checks["fixture-complete-mismatch"]["status"], "mismatch")
        self.assertEqual(checks["fixture-complete-mismatch"]["disposition_sum"], 4)
        self.assertEqual(checks["fixture-complete-mismatch"]["difference"], -1)
        self.assertEqual(checks["fixture-overlapping-category"]["status"], "not_assessed")
        self.assertIn("not distinct", checks["fixture-overlapping-category"]["reason"])

    def test_hiraoka_candidate_coverage_stays_aggregate_and_unassessed(self):
        path = EXAMPLE.parents[1] / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        bundle, report = self.publish(data)

        self.assertEqual(report["source_review_status"], "candidate")
        self.assertEqual(report["n_cohort_coverage_records"], 119)
        self.assertTrue(all(check["status"] == "not_assessed"
                            for check in report["cohort_coverage_checks"]))
        self.assertFalse(any(check["status"] == "mismatch" for check in report["cohort_coverage_checks"]))
        with (bundle / "cohort_dispositions.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        attachment = [row for row in rows if row["coverage_id"] == "hiraoka-attachment24-coverage"]
        self.assertEqual({(row["category"], row["value"], row["source_locator"]) for row in attachment}, {
            ("attached", "343", "Supplementary Fig. 5, physical PDF p8, 24h attachment row"),
            ("other", "94.2%", "Supplementary Fig. 5, physical PDF p8, 24h attachment row"),
        })
        withdrawals = [row for row in rows if row["category"] == "assay_withdrawn"]
        self.assertTrue(withdrawals)
        self.assertTrue(all(row["value_status"] == "not_reported" for row in withdrawals))
        self.assertEqual(report["n_observation_records"], len(data["observations"]))
        with (bundle / "cohort_coverage.csv").open(newline="", encoding="utf-8") as stream:
            coverage_rows = list(csv.DictReader(stream))
        pdms_free = [row for row in coverage_rows
                     if row["coverage_id"] == "hiraoka-pdms-free-attachment24-coverage"]
        self.assertEqual(len(pdms_free), 1)
        self.assertEqual(pdms_free[0]["counted_entity_kind"], "recipient_animal")
        self.assertEqual(pdms_free[0]["denominator_value"], "4")
        self.assertIn("not an embryo count denominator", pdms_free[0]["denominator_label"])
        with (bundle / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
            observation_rows = list(csv.DictReader(stream))
        pdms_observation = [row for row in observation_rows
                            if row["record_id"] == "hiraoka-pdms-free-attachment24-review-context"]
        self.assertEqual(len(pdms_observation), 1)
        self.assertEqual(pdms_observation[0]["value"], "~35%")
        self.assertEqual(pdms_observation[0]["replicate_role"], "summary_only")
        fixed_pdms = [row for row in coverage_rows
                      if row["coverage_id"] == "hiraoka-pdms-long-fixed-72h-coverage"]
        self.assertEqual(len(fixed_pdms), 1)
        self.assertEqual(fixed_pdms[0]["denominator_value"], "")
        self.assertEqual(fixed_pdms[0]["denominator_value_status"], "not_reported")
        self.assertEqual(fixed_pdms[0]["counted_entity_kind"], "embryo")
        fixed_observation = [row for row in observation_rows
                             if row["record_id"] == "hiraoka-pdms-long-fixed-72h-morphology"]
        self.assertEqual(len(fixed_observation), 1)
        self.assertIn("appeared dead", fixed_observation[0]["value"])
        self.assertIn("n unstated", fixed_observation[0]["value"])
        for thickness, value in [("750", "95.8%"), ("1500", "94.8%")]:
            row_id = f"hiraoka-attachment-{thickness}um-24h-coverage"
            group = next(row for row in coverage_rows if row["coverage_id"] == row_id)
            self.assertEqual(group["denominator_value"], "3")
            self.assertIn("not an embryo count denominator", group["denominator_label"])
            observation = next(
                row for row in observation_rows
                if row["record_id"] == f"hiraoka-attachment-{thickness}um-ceiling-24h"
            )
            self.assertEqual(observation["value"], value)
            self.assertEqual(observation["replicate_role"], "summary_only")


if __name__ == "__main__":
    unittest.main()
