from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.ashley_source import audit_ashley_source_cells


class AshleySourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_selected_values_and_complete_cell_ledger_reconcile(self):
        report = audit_ashley_source_cells(self.root)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["worksheet_nonempty_cells"], 207)
        self.assertEqual(report["worksheet_formula_cells"], 0)
        self.assertEqual(report["source_cell_ledger_rows_checked"], 207)
        self.assertEqual(report["candidate_observations_checked"], 30)
        self.assertEqual(report["selected_value_matches"], 30)
        self.assertEqual(report["selected_source_cells_designated_in_ledger"], 30)
        self.assertEqual(report["unique_placenta_labels"], 5)
        self.assertEqual(report["selected_endpoint_groups"], 6)
        self.assertEqual(report["excluded_24_25_rows_imported"], 0)
        self.assertEqual(report["row6_unit_qualifications_preserved"], 10)
        self.assertFalse(report["formula_recalculated"])
        self.assertFalse(report["source_transcription_or_scientific_review_complete"])
        self.assertFalse(report["dimensional_transport_fit_assessed"])

    def _fixture(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary)
        relative_paths = [
            "artifacts/ashley-2022-vitamin-d-perfusion/SOURCE.json",
            "artifacts/ashley-2022-vitamin-d-perfusion/figure1-source-data.xlsx",
            "config/observations/ashley_2022_vitamin_d_perfusion_candidate.json",
            "config/source_inventories/ashley_2022_figure1_source_cells.csv",
        ]
        for relative in relative_paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)
        candidate = root / relative_paths[2]
        return root, candidate

    def test_candidate_value_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate_path = self._fixture(temporary)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["observations"][0]["observation"]["value"] += 0.1
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            with self.assertRaisesRegex(InputError, "Candidate value differs from workbook"):
                audit_ashley_source_cells(root)

    def test_row6_rate_unit_without_source_qualification_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate_path = self._fixture(temporary)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["observations"][0]["observation"]["source_qualifications"] = []
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            with self.assertRaisesRegex(InputError, "Missing row-6 workbook-unit qualification"):
                audit_ashley_source_cells(root)


if __name__ == "__main__":
    unittest.main()
