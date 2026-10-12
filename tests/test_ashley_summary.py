from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.ashley_summary import derive_ashley_endpoint_summaries


class AshleySummaryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_all_six_group_summaries_and_five_label_partitions_reconcile(self):
        report = derive_ashley_endpoint_summaries(self.root)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary_groups_checked"], 6)
        self.assertEqual(report["summary_cells_checked"], 18)
        self.assertEqual(set(report["summaries"]), {
            "25d_maternal_loss", "25d_metabolized", "25d_fetal_appearance",
            "25d_placental_retention", "125d_maternal", "125d_fetal",
        })
        for group in report["summaries"].values():
            self.assertEqual(group["n"], 5)
            self.assertTrue(all(error <= 1e-12 for error in group["absolute_error"].values()))
        self.assertEqual(len(report["vitamin_d_25d_within_label_partition_check"]), 5)
        self.assertTrue(all(
            abs(item["residual"]) <= 1e-12
            for item in report["vitamin_d_25d_within_label_partition_check"].values()
        ))
        self.assertFalse(report["partition_check_is_independent_validation"])
        self.assertFalse(report["article_group_summary_reconciliation_assessed"])
        self.assertFalse(report["observation_values_added"])
        self.assertFalse(report["dimensional_transport_fit_assessed"])

    def _fixture(self, temporary: str) -> Path:
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
        return root

    def test_stale_workbook_summary_is_rejected_after_source_hashes_are_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._fixture(temporary)
            workbook_path = root / "artifacts/ashley-2022-vitamin-d-perfusion/figure1-source-data.xlsx"
            with zipfile.ZipFile(workbook_path, "r") as archive:
                members = [(item, archive.read(item.filename)) for item in archive.infolist()]
            namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
            ET.register_namespace("", namespace)
            changed = []
            changed_value = None
            for info, data in members:
                if info.filename == "xl/worksheets/sheet1.xml":
                    tree = ET.fromstring(data)
                    cell = tree.find(f".//{{{namespace}}}c[@r='G6']")
                    value = cell.find(f"{{{namespace}}}v")
                    changed_value = float(value.text) + 0.01
                    value.text = repr(changed_value)
                    data = ET.tostring(tree, encoding="utf-8", xml_declaration=True)
                changed.append((info, data))
            with zipfile.ZipFile(workbook_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for info, data in changed:
                    archive.writestr(info, data)
            workbook_hash = hashlib.sha256(workbook_path.read_bytes()).hexdigest()

            manifest_path = root / "artifacts/ashley-2022-vitamin-d-perfusion/SOURCE.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sha256"] = workbook_hash
            manifest["bytes"] = workbook_path.stat().st_size
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            candidate_path = root / "config/observations/ashley_2022_vitamin_d_perfusion_candidate.json"
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            for artifact in candidate["artifacts"]:
                if artifact.get("artifact_id") == "ashley2022-figure1-source-data":
                    artifact["sha256"] = workbook_hash
            for record in candidate["observations"]:
                record["source"]["sha256"] = workbook_hash
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

            ledger_path = root / "config/source_inventories/ashley_2022_figure1_source_cells.csv"
            rows = list(csv.DictReader(io.StringIO(ledger_path.read_text(encoding="utf-8-sig"), newline="")))
            next(row for row in rows if row["cell"] == "G6")["raw_value_json"] = json.dumps(changed_value)
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            ledger_path.write_text(stream.getvalue(), encoding="utf-8")

            with self.assertRaisesRegex(InputError, "Recomputed summary differs from workbook for 25d_maternal_loss"):
                derive_ashley_endpoint_summaries(root)


if __name__ == "__main__":
    unittest.main()
