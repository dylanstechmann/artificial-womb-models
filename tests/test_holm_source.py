from __future__ import annotations

import json
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.holm_source import audit_holm_table2_candidate, audit_holm_table3_candidate


class HolmTable2IntakeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_all_typed_table2_summaries_match_the_source_cell_ledger(self):
        report = audit_holm_table2_candidate(self.root)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_rows_checked"], 76)
        self.assertEqual(report["candidate_summary_records_checked"], 76)
        self.assertEqual(report["exact_source_cell_matches"], 76)
        self.assertEqual(report["typed_median_iqr_records"], 76)
        self.assertEqual(report["participant_level_records"], 0)
        self.assertTrue(report["all_values_are_concentrations"])
        self.assertFalse(report["blood_flow_or_flux_inferred"])
        self.assertEqual(report["vessel_denominators"], {
            "Radial artery": 168, "Uterine vein": 177,
            "Umbilical vein": 177, "Umbilical artery": 162,
        })
        self.assertEqual(report["unusual_literal_retained"]["literal"], "255 [2, 294]")

    def _fixture(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary)
        relative_paths = [
            "config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json",
            "config/source_inventories/holm_2017_table2_aggregate_source_cells.csv",
            "config/observations/holm_2017_term_amino_acid_concentrations_candidate.json",
        ]
        for relative in relative_paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)
        return root, root / relative_paths[2]

    @staticmethod
    def _write_candidate(root: Path, candidate_path: Path, candidate: dict) -> None:
        raw = json.dumps(candidate).encode("utf-8")
        candidate_path.write_bytes(raw)
        inventory_path = root / "config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["candidate_observation_intake"]["sha256"] = hashlib.sha256(raw).hexdigest()
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    def test_quartile_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate_path = self._fixture(temporary)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["observations"][0]["observation"]["summary_statistic"]["lower_quartile"] += 0.1
            self._write_candidate(root, candidate_path, candidate)
            with self.assertRaisesRegex(InputError, "Q1 differs from source literal"):
                audit_holm_table2_candidate(root)

    def test_unusual_alanine_literal_cannot_be_silently_corrected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate_path = self._fixture(temporary)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            record = next(item for item in candidate["observations"]
                          if item["record_id"] == "holm2017-table2-alanine-uterine-vein")
            record["observation"]["summary_statistic"]["source_literal"] = "255 [202, 294]"
            self._write_candidate(root, candidate_path, candidate)
            with self.assertRaisesRegex(InputError, "Source summary literal differs"):
                audit_holm_table2_candidate(root)

    def test_all_table3_paired_summaries_p_values_and_source_markers_reconcile(self):
        report = audit_holm_table3_candidate(self.root)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_rows_checked"], 76)
        self.assertEqual(report["candidate_summary_records_checked"], 76)
        self.assertEqual(report["exact_source_cell_matches"], 76)
        self.assertEqual(report["printed_p_values_preserved"], 76)
        self.assertEqual(report["source_bold_markers_preserved"], 76)
        self.assertEqual(report["vessel_circulation_denominators"], {
            "Uteroplacental": 166, "Umbilical": 160,
        })
        self.assertEqual(report["water_adjusted_umbilical_descriptive_check"], {
            "analyte_count": 19, "positive_median_count": 17, "negative_median_count": 2,
            "source_bolded_fdr_significant_positive_count": 14,
            "source_bolded_fdr_significant_negative_count": 1,
            "negative_bolded_analyte": "Glutamic acid",
        })
        self.assertFalse(report["p_values_recalculated"])
        self.assertFalse(report["fdr_significance_recalculated"])
        self.assertFalse(report["blood_flow_or_flux_inferred"])

    def _fixture_table3(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary)
        relative_paths = [
            "config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json",
            "config/source_inventories/holm_2017_table3_paired_difference_summaries.csv",
            "config/observations/holm_2017_term_amino_acid_differences_candidate.json",
        ]
        for relative in relative_paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)
        return root, root / relative_paths[2]

    @staticmethod
    def _write_table3_candidate(root: Path, candidate_path: Path, candidate: dict) -> None:
        raw = json.dumps(candidate).encode("utf-8")
        candidate_path.write_bytes(raw)
        inventory_path = root / "config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["candidate_paired_difference_intake"]["sha256"] = hashlib.sha256(raw).hexdigest()
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    def test_table3_printed_p_value_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate_path = self._fixture_table3(temporary)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            qualification = next(item for item in candidate["observations"][0]["observation"]["source_qualifications"]
                                 if item["criterion_code"] == "published_p_value")
            qualification["criterion_label"] = "Table 3 printed p-value literal: 0.99; no p-value was recalculated."
            self._write_table3_candidate(root, candidate_path, candidate)
            with self.assertRaisesRegex(InputError, "source qualification differs.*published_p_value"):
                audit_holm_table3_candidate(root)

    def test_table3_fdr_bold_marker_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate_path = self._fixture_table3(temporary)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            qualification = next(item for item in candidate["observations"][0]["observation"]["source_qualifications"]
                                 if item["criterion_code"] == "source_bold_marker")
            qualification["status_code"] = "marked_bold" if qualification["status_code"] == "not_bold" else "not_bold"
            self._write_table3_candidate(root, candidate_path, candidate)
            with self.assertRaisesRegex(InputError, "source qualification differs.*source_bold_marker"):
                audit_holm_table3_candidate(root)


if __name__ == "__main__":
    unittest.main()
