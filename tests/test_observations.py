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
from wombmodels.observations import observation_report, validate_dataset

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
            "n_contained": 2, "n_not_assessed": 0, "scientific_transcription": "not_verified"})
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
        with (bundle / "functional_contexts.csv").open(newline="") as stream:
            self.assertEqual(list(csv.DictReader(stream)), [])

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
        self.assertEqual(report["n_observation_records"], 10)
        self.assertEqual(report["n_continuity_not_reported"], 2)
        self.assertEqual(report["source_interval_containment"]["n_contained"], 0)
        self.assertTrue(any("no SHA-256" in warning for warning in report["warnings"]))
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
                    self.assertEqual(next(csv.DictReader(stream))["status"], "not_numeric")
                shutil.rmtree(bundle)

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
        changes = [{"start": True}, {"end": float("inf")}, {"start": 10 ** 400},
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


if __name__ == "__main__":
    unittest.main()
