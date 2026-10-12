from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, sha256
from wombmodels.eliesen_source import (
    audit_eliesen_table_s3,
    derive_eliesen_antipyrine_endpoint,
    derive_eliesen_placenta_summary,
)


class EliesenSourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.manifest_path = self.root / "config/perfusion_observations/eliesen_2024_tofacitinib_dataset.json"

    def test_pinned_table_s3_values_reconcile_and_preserve_na(self):
        report = audit_eliesen_table_s3(self.root, self.manifest_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["source_table_count"], 3)
        self.assertEqual(report["source_table_index"], 3)
        self.assertEqual(report["source_rows_reconciled"], 70)
        self.assertEqual(report["observation_rows_reconciled"], 70)
        self.assertEqual(report["exact_source_lexeme_matches"], 70)
        self.assertEqual(report["numeric_values_reconciled"], 69)
        self.assertEqual(report["not_assessed_values_preserved"], 1)
        self.assertTrue(report["source_table_uses_literal_text_values"])
        self.assertFalse(report["human_source_review_complete"])
        self.assertFalse(report["dimensional_transport_fit_assessed"])

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

    def test_source_value_change_is_rejected_even_when_csv_hash_is_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, rows = self._copy_inputs(temporary)
            rows[0]["source_value_lexeme"] = "101.0"
            rows[0]["value_numeric"] = "101.0"
            manifest_path = self._write_fixture(root, manifest, rows)
            with self.assertRaisesRegex(InputError, "source_value_lexeme differs from the source"):
                audit_eliesen_table_s3(root, manifest_path)

    def test_source_na_cannot_be_replaced_by_numeric_zero(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, rows = self._copy_inputs(temporary)
            na_row = next(row for row in rows if row["source_value_lexeme"] == "N/A")
            na_row["value_numeric"] = "0"
            manifest_path = self._write_fixture(root, manifest, rows)
            with self.assertRaisesRegex(InputError, "Source N/A must remain not_assessed"):
                audit_eliesen_table_s3(root, manifest_path)

    def test_derived_placenta_summaries_flag_published_fetal_endpoint_mismatch(self):
        summaries = derive_eliesen_placenta_summary(self.root, self.manifest_path)
        self.assertEqual(len(summaries), 20)
        maternal = next(row for row in summaries
                        if row["compartment"] == "maternal reservoir" and row["measurement_time"] == "180")
        fetal = next(row for row in summaries
                     if row["compartment"] == "fetal reservoir" and row["measurement_time"] == "180")
        self.assertEqual(maternal["source_value_lexemes"], "41.9;33.5;31.5")
        self.assertEqual((maternal["arithmetic_mean"], maternal["sample_sd"]), ("35.633333", "5.518454"))
        self.assertEqual(fetal["source_value_lexemes"], "30.0;20.1;24.9")
        self.assertEqual((fetal["arithmetic_mean"], fetal["sample_sd"]), ("25.000000", "4.950758"))
        # The article reports fetal 180-minute concentration as 24.8 ± 4.7 nM.
        # Table-display rounding to 0.1 nM cannot account for a 0.2 nM mean gap.
        self.assertGreater(abs(float(fetal["arithmetic_mean"]) - 24.8), 0.05)

    def test_derived_summary_csv_matches_recomputation_from_source(self):
        output_path = self.root / (
            "config/perfusion_observations/eliesen_2024_tofacitinib_table_s3_derived_summary_cycle244.csv"
        )
        with output_path.open(encoding="utf-8", newline="") as stream:
            stored = list(csv.DictReader(stream))
        recomputed = derive_eliesen_placenta_summary(self.root, self.manifest_path)
        self.assertEqual(stored, recomputed)

    def test_antipyrine_table_s2_endpoint_reconciles_as_mapping_control(self):
        summaries = derive_eliesen_antipyrine_endpoint(self.root, self.manifest_path)
        self.assertEqual(len(summaries), 2)
        maternal, fetal = summaries
        self.assertEqual(maternal["source_value_lexemes"], "39.6;37.4;33.7")
        self.assertEqual((maternal["arithmetic_mean"], maternal["sample_sd"]), ("36.900000", "2.981610"))
        self.assertEqual(maternal["rounded_summary_matches_article"], "true")
        self.assertEqual(fetal["source_value_lexemes"], "38.0;36.8;35.4")
        self.assertEqual((fetal["arithmetic_mean"], fetal["sample_sd"]), ("36.733333", "1.301281"))
        self.assertEqual(fetal["rounded_summary_matches_article"], "true")


if __name__ == "__main__":
    unittest.main()
