from __future__ import annotations

import json
import csv
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, sha256
from wombmodels.faure_bardon_source import audit_faure_bardon_source_cells


class FaureBardonSourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.manifest = self.root / "config/perfusion_observations/faure_bardon_2020_lmv_mbv_dataset.json"

    def test_pinned_source_cells_and_ftr_pairs_reconcile(self):
        report = audit_faure_bardon_source_cells(self.root, self.manifest)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_cell_rows"], 912)
        self.assertEqual(report["matched_values_formulas_and_caches"], 912)
        self.assertEqual(report["source_cell_mismatches"], 0)
        self.assertEqual(report["formula_cells_checked"], 304)
        self.assertEqual(report["ordinary_formula_cells"], 23)
        self.assertEqual(report["shared_formula_cells"], 281)
        self.assertEqual(report["shared_formula_followers_without_local_expression_text"], 259)
        self.assertEqual(report["blank_source_rows"], 16)
        self.assertEqual(report["paired_ftr_rows_recomputed"], 288)
        self.assertFalse(report["dimensional_transport_fit_assessed"])

    def test_modified_csv_is_rejected_even_when_manifest_hash_is_updated(self):
        original = json.loads(self.manifest.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workbook_rel = original["source_artifact"]["local_path"]
            csv_rel = original["observation_file"]["path"]
            workbook = root / workbook_rel
            csv_path = root / csv_rel
            workbook.parent.mkdir(parents=True)
            csv_path.parent.mkdir(parents=True)
            shutil.copyfile(self.root / workbook_rel, workbook)
            raw_csv = (self.root / csv_rel).read_bytes()
            rows = list(csv.DictReader(io.StringIO(raw_csv.decode("utf-8-sig"), newline="")))
            changed = [row for row in rows if row["source_cell"] == "C4"]
            self.assertEqual(len(changed), 1)
            changed[0]["reported_cell_value_lexeme"] = "9.8000000000000007"
            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=rows[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            changed_csv = buffer.getvalue().encode("utf-8")
            csv_path.write_bytes(changed_csv)
            original["observation_file"]["sha256"] = sha256(changed_csv)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(InputError, "Source value differs at C4"):
                audit_faure_bardon_source_cells(root, manifest_path)

    def test_inconsistent_nested_formula_count_is_rejected(self):
        original = json.loads(self.manifest.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workbook_rel = original["source_artifact"]["local_path"]
            csv_rel = original["observation_file"]["path"]
            workbook = root / workbook_rel
            csv_path = root / csv_rel
            workbook.parent.mkdir(parents=True)
            csv_path.parent.mkdir(parents=True)
            shutil.copyfile(self.root / workbook_rel, workbook)
            shutil.copyfile(self.root / csv_rel, csv_path)
            original["formula_and_cache_provenance"]["unit_level_formula_cells_with_cached_results"] = 45
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(InputError, "Formula/cache provenance count differs"):
                audit_faure_bardon_source_cells(root, manifest_path)


if __name__ == "__main__":
    unittest.main()
