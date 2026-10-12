from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, sha256
from wombmodels.mandelbrot_source import audit_mandelbrot_source_cells


class MandelbrotSourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.manifest_path = self.root / "config/perfusion_observations/mandelbrot_2019_dolutegravir_dataset.json"

    def test_pinned_values_and_formula_groups_reconcile(self):
        report = audit_mandelbrot_source_cells(self.root, self.manifest_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["observation_rows"], 94)
        self.assertEqual(report["unique_record_ids"], 94)
        self.assertEqual(report["selected_field_cells_checked"], 658)
        self.assertEqual(report["cached_value_lexeme_mismatches"], 0)
        self.assertEqual(report["worksheet_formula_cells"], 483)
        self.assertEqual(report["mapped_formula_cells"], 465)
        self.assertEqual(report["local_formula_expression_text_cells"], 397)
        self.assertEqual(report["shared_formula_cells"], 73)
        self.assertEqual(report["shared_formula_followers_without_local_expression_text"], 68)
        self.assertFalse(report["formula_recalculated"])
        self.assertFalse(report["external_workbook_retrieved"])
        self.assertFalse(report["dimensional_transport_fit_assessed"])
        self.assertFalse(report["human_source_review_complete"])

    def _copy_inputs(self, temporary: str) -> tuple[Path, dict, list[dict[str, str]]]:
        root = Path(temporary)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        for relative in (manifest["source_artifact"]["local_path"], manifest["observation_file"]["path"]):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)
        csv_path = root / manifest["observation_file"]["path"]
        rows = list(csv.DictReader(io.StringIO(csv_path.read_text(encoding="utf-8-sig"), newline="")))
        return root, manifest, rows

    @staticmethod
    def _write_fixture(root: Path, manifest: dict, rows: list[dict[str, str]]) -> Path:
        csv_path = root / manifest["observation_file"]["path"]
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        raw = stream.getvalue().encode("utf-8")
        csv_path.write_bytes(raw)
        manifest["observation_file"]["sha256"] = sha256(raw)
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def test_shared_formula_group_tamper_is_rejected_even_when_hash_is_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, rows = self._copy_inputs(temporary)
            follower = next(row for row in rows if row["antipyrine_fetal_to_maternal_ratio_pct_cell"] == "I8")
            follower["antipyrine_fetal_to_maternal_ratio_pct_source_formula_shared_index"] = "99"
            manifest_path = self._write_fixture(root, manifest, rows)
            with self.assertRaisesRegex(InputError, "Formula/cache provenance differs at I8"):
                audit_mandelbrot_source_cells(root, manifest_path)

    def test_cached_value_tamper_is_rejected_even_when_hash_is_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, rows = self._copy_inputs(temporary)
            row = next(row for row in rows if row["dtg_fetal_ng_ml_cell"] == "C7")
            row["dtg_fetal_ng_ml_source_value_lexeme"] = "4.1"
            row["dtg_fetal_ng_ml_value_numeric"] = "4.1"
            manifest_path = self._write_fixture(root, manifest, rows)
            with self.assertRaisesRegex(InputError, "Source value lexeme differs at C7"):
                audit_mandelbrot_source_cells(root, manifest_path)

    def test_formula_cell_count_must_include_shared_followers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, _ = self._copy_inputs(temporary)
            ratio = next(item for item in manifest["measured_fields"]
                         if item["name"] == "antipyrine_fetal_to_maternal_ratio_pct")
            ratio["source_formula_cell_count"] = 22
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            message = "Manifest formula counts differ for antipyrine_fetal_to_maternal_ratio_pct"
            with self.assertRaisesRegex(InputError, message):
                audit_mandelbrot_source_cells(root, manifest_path)


if __name__ == "__main__":
    unittest.main()
