from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from local_evidence import requires_local_evidence
from wombmodels.artifacts import InputError, json_bytes, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report, validate_dataset
from wombmodels.ollivier_source import (
    ARTIFACT_DIRECTORY,
    CARD_PATH,
    INVENTORY_PATH,
    TIME_UNIT,
    audit_ollivier_jats_and_observation_card,
    audit_ollivier_table_s1,
    derive_ollivier_antipyrine_summary_and_volume_ratios,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = "config/perfusion_observations/ollivier_2026_aciclovir_antipyrine_dataset.json"
CSV_REL = "config/perfusion_observations/ollivier_2026_table_s1_source_cells.csv"
EXPECTED_ARTIFACTS = {
    "ollivier2026-jats-xml": ("pmc13040426.xml", 86739, "4e4e7e52d4eaabdf334d3b1a3aa4072aea2bed000e61c93a94b09232249b529d"),
    "ollivier2026-supplementary-zip": ("PMC13040426_supplementaryFiles.zip", 321806, "70f3ebcb844b79dccf690395301beab4eca2f237ad2cf834511d7d6a0774585e"),
    "ollivier2026-table-s1-docx": ("BJO-133-1241-s003.docx", 15690, "442a3272ef5230bf5a649d02432bc6438db09373a1356fd6786802499b99bf84"),
    "ollivier2026-figure-s2-png": ("BJO-133-1241-s001.png", 113156, "abe907575a4dc43dbb72c8577f4ac77fb2657e28e99440dd0d5f345c2d7ae3c5"),
    "ollivier2026-figure-s1-png": ("BJO-133-1241-s002.png", 78450, "c65634aad1767eb8544ca17cc4551e4aed370ade201d631e13a5ad699c4ecd18"),
}


def _json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _write_json(path: Path, value: dict) -> None:
    path.write_bytes(json_bytes(value))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n", quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(stream.getvalue().encode("utf-8"))


class OllivierCleanCloneTests(unittest.TestCase):
    """These checks use tracked inputs only and never inspect artifacts/."""

    def test_tracked_card_schema_counts_pairs_and_coverage(self):
        card = _json(ROOT / CARD_PATH)
        validate_dataset(card)
        self.assertEqual(len(card["artifacts"]), 2)
        self.assertEqual(len(card["observations"]), 47)
        measured = [row for row in card["observations"] if row["evidence_status"] == "measured"]
        summaries = [row for row in card["observations"] if row["evidence_status"] == "author_reported_summary"]
        self.assertEqual((len(measured), len(summaries)), (36, 11))
        self.assertTrue(all(row["observation"]["measurement_time"] == 180 for row in measured))
        self.assertTrue(all(row["observation"]["measurement_time_unit"] == TIME_UNIT for row in measured))
        self.assertTrue(all(row["observation"]["summary_statistic"]["kind"] == "mean_sd" for row in summaries))
        self.assertTrue(all(row["observation"]["summary_statistic"]["reported_sample_size"] == 9 for row in summaries))
        for row in measured:
            codes = {item["criterion_code"] for item in row["observation"]["source_qualifications"]}
            self.assertIn("source_decimal_lexeme", codes)
            if row["record_id"].endswith(("c03", "c04")):
                self.assertTrue({"results_table_metric_swap", "per_placenta_volume_records"}.issubset(codes))
        baseline = next(row for row in summaries if row["record_id"] == "ollivier2026-table1-umbilical-artery-ph")
        self.assertEqual(baseline["observation"]["summary_statistic"]["standard_deviation"], 1.60)
        self.assertEqual(baseline["observation"]["source_qualifications"][0]["criterion_code"], "printed_summary_anomaly")
        self.assertEqual(len(card["measurement_pairs"]), 9)
        for index, pair in enumerate(card["measurement_pairs"], 1):
            self.assertEqual(pair["pair_type"], "same_unit_same_time")
            self.assertEqual(pair["linkage_basis"], "source_explicit")
            self.assertEqual([member["record_id"] for member in pair["members"]],
                             [f"ollivier2026-table-s1-r{index:02d}-c01", f"ollivier2026-table-s1-r{index:02d}-c02"])
        self.assertEqual(len(card["cohort_coverage"]), 3)
        self.assertEqual(card["transitions"], [])

    def test_clean_clone_observation_bundle_and_count_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "validated"
            observation_report(ROOT / CARD_PATH, output)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
            report = _json(output / "observation_intake_report.json")
            self.assertEqual(report["n_observation_records"], 47)
            self.assertEqual(report["source_file_verification"]["status"], "not_requested")
            self.assertEqual(report["measurement_pairing"]["n_pairs"], 9)
            statuses = {row["coverage_id"]: row["status"] for row in report["cohort_coverage_checks"]}
            self.assertEqual(statuses, {
                "ollivier2026-validated-perfusion-coverage": "not_assessed",
                "ollivier2026-sampling-cadence-coverage": "matches",
                "ollivier2026-five-hour-extension-coverage": "not_assessed",
            })

    def test_tracked_csv_and_inventory_pointers_are_byte_exact(self):
        manifest = _json(ROOT / MANIFEST_REL)
        inventory = _json(ROOT / INVENTORY_PATH)
        for section in (manifest["observation_file"], manifest["observation_card"], inventory["perfusion_manifest"]):
            raw = (ROOT / section["path"]).read_bytes()
            self.assertEqual(len(raw), section["size_bytes"])
            self.assertEqual(sha256(raw), section["sha256"])
            self.assertNotIn(b"\r", raw)
        self.assertEqual(inventory["observation_file"], manifest["observation_file"])
        self.assertEqual(inventory["observation_card"], manifest["observation_card"])
        rows = _csv_rows(ROOT / CSV_REL)
        self.assertEqual(len(rows), 44)
        self.assertEqual(sum(row["row_role"] == "placenta_perfusion" for row in rows), 36)
        self.assertEqual(sum(row["row_role"] == "source_reported_summary" for row in rows), 8)
        self.assertEqual(rows[0]["source_value_lexeme"], "8,09")
        self.assertEqual(rows[0]["value_numeric"], "8.09")
        self.assertEqual(rows[1]["source_value_lexeme"], "7,07")
        self.assertEqual(rows[2]["source_value_lexeme"], "36,81")
        self.assertEqual(rows[3]["source_value_lexeme"], "87,39")
        self.assertTrue(all("," in row["source_value_lexeme"] for row in rows))
        artifacts = {row["artifact_id"]: row for row in inventory["source_artifacts"]}
        self.assertEqual(set(artifacts), set(EXPECTED_ARTIFACTS))
        for artifact_id, (filename, size, digest) in EXPECTED_ARTIFACTS.items():
            row = artifacts[artifact_id]
            self.assertEqual(row["local_path"], f"{ARTIFACT_DIRECTORY}/{filename}")
            self.assertEqual((row["size_bytes"], row["sha256"]), (size, digest))
            self.assertEqual(row["license"], "CC BY 4.0")
        self.assertEqual(inventory["eligibility"]["figure_digitized"], False)
        self.assertFalse(inventory["author_contacted"])

    def test_perfusion_crosswalk_and_dataset_manifests_preserve_volume_identifiability_boundary(self):
        crosswalk_relative = "config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json"
        crosswalk_raw = (ROOT / crosswalk_relative).read_bytes()
        self.assertNotIn(b"\r", crosswalk_raw)
        crosswalk = json.loads(crosswalk_raw.decode("utf-8"))
        screens = {
            row["source_id"]: row
            for row in crosswalk["related_public_source_candidate_screens"]
            if "source_id" in row
        }
        ashley_id = "ashley_2022_elife_vitamin_d_placental_perfusion"
        ollivier_id = "ollivier_2026_bjog_aciclovir_antipyrine_placental_perfusion"
        self.assertIn(ashley_id, screens)
        self.assertIn(ollivier_id, screens)
        expected_ollivier_artifacts = {
            "perfusion_manifest": MANIFEST_REL,
            "table_s1_source_cells": CSV_REL,
            "candidate_observation_card": CARD_PATH,
            "source_inventory": INVENTORY_PATH,
        }
        artifacts = screens[ollivier_id]["accessible_artifacts"]
        for key, relative in expected_ollivier_artifacts.items():
            self.assertEqual(artifacts[key], relative)
            self.assertTrue((ROOT / relative).is_file(), relative)

        manifest_names = (
            "eliesen_2024_tofacitinib_dataset.json",
            "faure_bardon_2020_lmv_mbv_dataset.json",
            "mandelbrot_2019_dolutegravir_dataset.json",
            "ollivier_2026_aciclovir_antipyrine_dataset.json",
        )
        for name in manifest_names:
            with self.subTest(manifest=name):
                manifest = _json(ROOT / "config/perfusion_observations" / name)
                self.assertEqual(manifest["intake_status"], "candidate")
                self.assertIs(manifest["author_contacted"], False)
                pointer = manifest["observation_file"]
                observation_path = ROOT / pointer["path"]
                self.assertTrue(observation_path.is_file(), pointer["path"])
                observation_raw = observation_path.read_bytes()
                self.assertEqual(pointer["sha256"], sha256(observation_raw))
                if "size_bytes" in pointer:
                    self.assertEqual(pointer["size_bytes"], len(observation_raw))
                not_eligible = manifest["eligibility"]["not_eligible_for"]
                self.assertTrue(any("dimensional transfer-parameter fitting" in item.lower()
                                    for item in not_eligible))
                self.assertTrue(any("mass-balance" in item.lower() for item in not_eligible))
                volume_boundary = json.dumps({
                    "missing_records": manifest["eligibility"].get("missing_records", []),
                    "article_context": manifest.get("article_context", ""),
                }, ensure_ascii=False).lower()
                self.assertIn("volume", volume_boundary)
                self.assertRegex(volume_boundary, r"sample.*removal")


@requires_local_evidence("ollivier-2026-aciclovir-perfusion-2026-11-12")
class OllivierLocalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT
        self.manifest_path = self.root / MANIFEST_REL

    def test_docx_audit_reconciles_every_literal_cell(self):
        report = audit_ollivier_table_s1(self.root, self.manifest_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_table_count"], 1)
        self.assertEqual((report["source_table_rows"], report["source_table_columns"]), (12, 5))
        self.assertEqual(report["source_cells_reconciled"], 44)
        self.assertEqual(report["placenta_perfusion_rows"], 36)
        self.assertEqual(report["source_reported_summary_rows"], 8)
        self.assertEqual(report["exact_decimal_comma_lexeme_matches"], 44)
        self.assertTrue(report["source_table_uses_literal_paragraph_run_text"])
        self.assertFalse(report["human_source_review_complete"])

    def test_decimal_summaries_ratios_and_volume_identifiability(self):
        report = derive_ollivier_antipyrine_summary_and_volume_ratios(self.root, self.manifest_path)
        self.assertEqual(report["printed_mean_sd_columns_matched_after_two_decimal_rounding"], 4)
        self.assertEqual(report["printed_fetal_maternal_ratios_matched"], 9)
        self.assertEqual(report["implied_vf_over_vm_range"], ["0.328392", "1.333187"])
        self.assertEqual(report["implied_vf_over_vm_min_placenta"], 5)
        self.assertEqual(report["implied_vf_over_vm_max_placenta"], 9)
        self.assertEqual(report["common_mean_volume_sensitivity"]["mean_absolute_per_placenta_difference_percentage_points"], "9.154696")
        self.assertEqual(report["common_mean_volume_sensitivity"]["maximum_absolute_difference_percentage_points"], "18.290812")
        self.assertFalse(report["per_placenta_volume_records_reported"])

    def test_jats_card_inventory_and_source_root_bundle(self):
        report = audit_ollivier_jats_and_observation_card(self.root, self.manifest_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["observation_records_reconciled"], 47)
        self.assertEqual(report["author_reported_summary_records"], 11)
        self.assertEqual(report["measurement_pairs_reconciled"], 9)
        self.assertEqual(report["local_artifacts_verified"], 5)
        self.assertEqual(report["table1_umbilical_artery_ph_literal"], "7.28 (SD: 1.60)")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "validated"
            observation_report(self.root / CARD_PATH, output, source_root=self.root)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
            intake = _json(output / "observation_intake_report.json")
            self.assertEqual(intake["source_file_verification"]["status"], "complete")
            self.assertEqual(intake["source_file_verification"]["n_verified"], 2)

    def _copy_table_fixture(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary)
        manifest = _json(self.manifest_path)
        for relative in (manifest["source_artifact"]["local_path"], CSV_REL, MANIFEST_REL):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)
        return root, root / MANIFEST_REL

    def _copy_full_fixture(self, temporary: str) -> Path:
        root = Path(temporary)
        manifest = _json(self.manifest_path)
        relative_paths = [row["local_path"] for row in manifest["source_artifacts"]]
        relative_paths += [CSV_REL, CARD_PATH, MANIFEST_REL, INVENTORY_PATH]
        for relative in relative_paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)
        return root

    @staticmethod
    def _refresh_full_pins(root: Path) -> None:
        manifest_path = root / MANIFEST_REL
        manifest = _json(manifest_path)
        csv_raw = (root / CSV_REL).read_bytes()
        manifest["observation_file"].update(sha256=sha256(csv_raw), size_bytes=len(csv_raw))
        card_raw = (root / CARD_PATH).read_bytes()
        manifest["observation_card"].update(sha256=sha256(card_raw), size_bytes=len(card_raw))
        for singular, artifact_id in (("source_artifact", "ollivier2026-table-s1-docx"),
                                      ("jats_artifact", "ollivier2026-jats-xml")):
            raw = (root / manifest[singular]["local_path"]).read_bytes()
            manifest[singular].update(sha256=sha256(raw), size_bytes=len(raw))
            for artifact in manifest["source_artifacts"]:
                if artifact["artifact_id"] == artifact_id:
                    artifact.update(sha256=sha256(raw), size_bytes=len(raw))
        _write_json(manifest_path, manifest)
        inventory_path = root / INVENTORY_PATH
        inventory = _json(inventory_path)
        inventory["source_artifacts"] = manifest["source_artifacts"]
        inventory["observation_file"] = manifest["observation_file"]
        inventory["observation_card"] = manifest["observation_card"]
        manifest_raw = manifest_path.read_bytes()
        inventory["perfusion_manifest"].update(sha256=sha256(manifest_raw), size_bytes=len(manifest_raw))
        _write_json(inventory_path, inventory)

    def test_cell_value_tamper_is_rejected_even_when_csv_hash_is_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest_path = self._copy_table_fixture(temporary)
            rows = _csv_rows(root / CSV_REL)
            rows[0]["source_value_lexeme"] = "8,10"
            rows[0]["value_numeric"] = "8.10"
            _write_csv(root / CSV_REL, rows)
            manifest = _json(manifest_path)
            raw = (root / CSV_REL).read_bytes()
            manifest["observation_file"].update(sha256=sha256(raw), size_bytes=len(raw))
            _write_json(manifest_path, manifest)
            with self.assertRaisesRegex(InputError, "source_value_lexeme differs from the source"):
                audit_ollivier_table_s1(root, manifest_path)

    def test_printed_summary_tamper_is_rejected_by_decimal_recomputation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest_path = self._copy_table_fixture(temporary)
            rows = _csv_rows(root / CSV_REL)
            mean_row = next(row for row in rows if row["record_id"] == "ollivier2026-table-s1-r10-c01")
            mean_row["source_value_lexeme"] = "9,75"
            mean_row["value_numeric"] = "9.75"
            _write_csv(root / CSV_REL, rows)
            docx_path = root / _json(manifest_path)["source_artifact"]["local_path"]
            replacement = docx_path.with_suffix(".changed.docx")
            with zipfile.ZipFile(docx_path) as source, zipfile.ZipFile(replacement, "w") as target:
                for item in source.infolist():
                    raw = source.read(item.filename)
                    if item.filename == "word/document.xml":
                        self.assertEqual(raw.count(b"9,74"), 1)
                        raw = raw.replace(b"9,74", b"9,75", 1)
                    target.writestr(item, raw)
            replacement.replace(docx_path)
            manifest = _json(manifest_path)
            for relative, section in ((CSV_REL, manifest["observation_file"]),
                                      (manifest["source_artifact"]["local_path"], manifest["source_artifact"])):
                raw = (root / relative).read_bytes()
                section.update(sha256=sha256(raw), size_bytes=len(raw))
            _write_json(manifest_path, manifest)
            with self.assertRaisesRegex(InputError, "Printed Mean differs from the recomputed"):
                derive_ollivier_antipyrine_summary_and_volume_ratios(root, manifest_path)

    def test_jats_metric_swap_tamper_is_rejected_with_refreshed_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_full_fixture(temporary)
            manifest = _json(root / MANIFEST_REL)
            xml_path = root / manifest["jats_artifact"]["local_path"]
            raw = xml_path.read_bytes()
            self.assertEqual(raw.count("was 81% (SD: 6.9%)".encode()), 1)
            xml_path.write_bytes(raw.replace("was 81% (SD: 6.9%)".encode(), "was 82% (SD: 6.9%)".encode(), 1))
            card_path = root / CARD_PATH
            card = _json(card_path)
            digest = sha256(xml_path.read_bytes())
            for artifact in card["artifacts"]:
                if artifact["artifact_id"] == "ollivier2026-jats-xml":
                    artifact["sha256"] = digest
            for record in card["observations"]:
                if record["source"]["artifact_id"] == "ollivier2026-jats-xml":
                    record["source"]["sha256"] = digest
            _write_json(card_path, card)
            self._refresh_full_pins(root)
            with self.assertRaisesRegex(InputError, "antipyrine metric-swap sentence"):
                audit_ollivier_jats_and_observation_card(root, root / MANIFEST_REL)

    def test_observation_card_value_tamper_is_rejected_with_refreshed_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_full_fixture(temporary)
            card_path = root / CARD_PATH
            card = _json(card_path)
            card["observations"][0]["observation"]["value"] = 8.10
            _write_json(card_path, card)
            self._refresh_full_pins(root)
            with self.assertRaisesRegex(InputError, "Observation value differs from Table S1"):
                audit_ollivier_jats_and_observation_card(root, root / MANIFEST_REL)


if __name__ == "__main__":
    unittest.main()
