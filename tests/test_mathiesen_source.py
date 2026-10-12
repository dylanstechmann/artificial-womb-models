"""Artificial XLSX fixtures for the offline Mathiesen source audit; no study values."""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.mathiesen_source import (ANALYTES, EXPECTED_ROWS, RUNS, _extract_cells,
    _missingness_summary, _observation_dataset, _s3_candidate_link, _summary, _workbook_cells,
    audit_mathiesen_source)
from wombmodels.observations import observation_report, validate_dataset


def invented_xlsx(*, formula_at: str | None = None, duplicate_cell: str | None = None,
                   unsafe_target: str | None = None) -> bytes:
    """Build a complete parser fixture with artificial values and explicit labels."""
    strings = ["Conc. nM"]
    cells: list[tuple[str, str, str]] = [("A1", "s", "Conc. nM")]
    for run_id in range(1, 23):
        cells.append((f"{chr(ord('B') + run_id - 1)}1", "n", str(run_id)))
    row_number = 2
    for analyte, heading_row in ANALYTES:
        row_number = heading_row
        cells.append((f"A{row_number}", "s", analyte))
        row_number += 1
        for time_label, compartment, time_min in EXPECTED_ROWS:
            cells.append((f"A{row_number}", "s", time_label))
            for run_id in range(1, 23):
                column = chr(ord("B") + run_id - 1)
                cell_ref = f"{column}{row_number}"
                if cell_ref == "D3":  # one artificial missing cell
                    continue
                value = 1000.0
                if analyte == "Tryptophan" and time_label == "F360":
                    value = 700.0
                cells.append((cell_ref, "n", str(value)))
            row_number += 1
    shared_values = list(dict.fromkeys(value for _, kind, value in cells if kind == "s"))
    shared_index = {value: index for index, value in enumerate(shared_values)}
    shared_xml = "".join(f"<si><t>{escape(value)}</t></si>" for value in shared_values)
    row_cells: dict[int, list[str]] = {}
    for reference, kind, value in cells:
        row = int("".join(character for character in reference if character.isdigit()))
        if kind == "s":
            cell_xml = f'<c r="{reference}" t="s"><v>{shared_index[value]}</v></c>'
        elif formula_at == reference:
            cell_xml = f'<c r="{reference}"><f>1+1</f><v>{escape(value)}</v></c>'
        else:
            cell_xml = f'<c r="{reference}"><v>{escape(value)}</v></c>'
        row_cells.setdefault(row, []).append(cell_xml)
        if duplicate_cell == reference:
            row_cells[row].append(f'<c r="{reference}"><v>999</v></c>')
    target = unsafe_target or "worksheets/sheet1.xml"
    buffer = __import__("io").BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Placental perfusion" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="{escape(target)}"/></Relationships>')
        archive.writestr("xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            + shared_xml + '</sst>')
        archive.writestr("xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            + "".join(f'<row r="{row}">' + "".join(items) + "</row>"
                      for row, items in sorted(row_cells.items()))
            + '</sheetData></worksheet>')
    return buffer.getvalue()


def invented_s3_docx(keys: tuple[int, ...] = tuple(range(1, 23))) -> bytes:
    """Build a structural fixture with artificial table keys and no human data."""
    header = ["nr"] + [f"Header {index}" for index in range(2, 15)]
    table_rows = [header] + [[str(key)] + ["invented"] * 13 for key in keys]
    xml_rows = []
    for row in table_rows:
        cells = "".join(
            f"<w:tc><w:p><w:r><w:t>{escape(value)}</w:t></w:r></w:p></w:tc>"
            for value in row)
        xml_rows.append(f"<w:tr>{cells}</w:tr>")
    document = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:tbl>" + "".join(xml_rows) + "</w:tbl></w:body></w:document>")
    buffer = __import__("io").BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document)
    return buffer.getvalue()


class MathiesenSourceAuditTests(unittest.TestCase):
    def test_s3_candidate_key_screen_never_joins_matching_or_mismatching_keys(self):
        matching = _s3_candidate_link(invented_s3_docx())
        self.assertTrue(matching["numeric_key_sets_match"])
        self.assertEqual(matching["status"], "candidate link; not verified")
        self.assertFalse(matching["join_performed"])
        self.assertFalse(matching["biological_identity_inferred"])
        self.assertFalse(matching["donor_measurement_values_transcribed"])
        self.assertFalse(matching["source_hash_is_pinned"])

        mismatched = _s3_candidate_link(invented_s3_docx(tuple(range(2, 24))))
        self.assertFalse(mismatched["numeric_key_sets_match"])
        self.assertEqual(mismatched["status"], "keys do not match")
        self.assertFalse(mismatched["join_performed"])

        with self.assertRaises(InputError):
            _s3_candidate_link(b"not a DOCX")

    def test_run_mapping_and_raw_cells_preserve_units_missingness_and_validity(self):
        cells = _workbook_cells(invented_xlsx())
        rows = _extract_cells(cells)
        self.assertEqual(len(rows), 3190)
        self.assertEqual(sum(row["value_nM"] is not None for row in rows), 3189)
        self.assertEqual(sum(row["value_nM"] is None for row in rows), 1)
        self.assertEqual(len(RUNS), 22)
        self.assertEqual(sum(group == "none" for group, _hours in RUNS.values()), 8)
        self.assertEqual(RUNS[10], ("carbenoxolone", 1.0))
        self.assertEqual(RUNS[13], ("carbenoxolone", 3.5))
        index = {(row["analyte"], row["source_time_label"], row["perfusion_id"]): row
                 for row in rows}
        self.assertEqual(index[("Tryptophan", "M0", 1)]["source_locator"], "Placental perfusion!B64")
        self.assertEqual(index[("Tryptophan", "M0", 1)]["value_nM"], 1000.0)
        self.assertEqual(index[("Cortisol", "Mbefore", 3)]["value_nM"], None)
        self.assertTrue(index[("Cortisol", "Mbefore", 3)]["missingness_reason"])
        self.assertEqual(index[("Cortisol", "F60", 10)]["window_status"],
                         "within_source_reported_ok_duration")
        self.assertEqual(index[("Cortisol", "F90", 10)]["window_status"],
                         "after_source_reported_ok_duration")
        self.assertEqual(_summary(rows)["mean_percent"], 70.0)
        missingness = _missingness_summary(rows)
        self.assertEqual(missingness["n_expected"], 3190)
        self.assertEqual(missingness["n_blank"], 1)
        self.assertEqual(missingness["n_after_source_ok_window"], 270)
        self.assertEqual(missingness["n_numeric_after_source_ok_window"], 270)
        cortisol_maternal = next(item for item in missingness["breakdown"]
                                 if item["dimension"] == "analyte_compartment"
                                 and item["category"] == "Cortisol"
                                 and item["compartment"] == "maternal")
        self.assertEqual(cortisol_maternal["n_blank"], 1)

    def test_observation_dataset_keeps_term_stage_and_exact_source_locators(self):
        rows = _extract_cells(_workbook_cells(invented_xlsx()))
        artifacts = [
            {"artifact_id": "mathiesen2020-article", "uri": "https://example.org/article",
             "license": "fixture license", "sha256": "a" * 64, "retrieved_on": "2026-10-10",
             "local_path": None},
            {"artifact_id": "mathiesen2020-s1data", "uri": "https://example.org/data",
             "license": "fixture license", "sha256": "b" * 64, "retrieved_on": "2026-10-10",
             "local_path": None},
            {"artifact_id": "mathiesen2020-table1", "uri": "https://example.org/table1",
             "license": "fixture license", "sha256": "c" * 64, "retrieved_on": "2026-10-10",
             "local_path": None},
        ]
        data = _observation_dataset(rows, artifacts)
        validate_dataset(data)
        self.assertEqual(len(data["observations"]), 3190)
        by_locator = {record["source_locator"]: record for record in data["observations"]}
        self.assertEqual(by_locator["Placental perfusion!B64"]["independent_unit"]["id"], "perfusion-01")
        self.assertEqual(by_locator["Placental perfusion!B64"]["observation"]["value"], 1000.0)
        self.assertEqual(by_locator["Placental perfusion!D3"]["observation"]["value"], None)
        self.assertIn("analysis errors", by_locator["Placental perfusion!D3"]["observation"]["missingness_reason"])
        qualification_counts = {}
        for record in data["observations"]:
            declarations = record["observation"]["source_qualifications"]
            self.assertEqual(len(declarations), 1)
            qualification = declarations[0]
            self.assertEqual(qualification["source_artifact_id"], "mathiesen2020-table1")
            self.assertEqual(qualification["reference_unit"], "hour")
            self.assertEqual(qualification["source_locator"],
                             f"PLOS Table 1, row ID {int(record['independent_unit']['id'][-2:])}")
            qualification_counts[qualification["status_code"]] = (
                qualification_counts.get(qualification["status_code"], 0) + 1)
        self.assertEqual(qualification_counts, {
            "before_exposure_time_not_numeric": 220,
            "within_source_reported_ok_duration": 2700,
            "after_source_reported_ok_duration": 270,
        })
        self.assertEqual(data["source_revision"]["review_status"], "candidate")
        self.assertEqual(data["transitions"], [])
        self.assertEqual(data["observations"][0]["stage_track"], "organoid_or_tissue_model")

    def test_xlsx_reader_rejects_formula_duplicate_unsafe_path_and_changed_labels(self):
        for raw in (invented_xlsx(formula_at="B3"), invented_xlsx(duplicate_cell="B3"),
                    invented_xlsx(unsafe_target="../sheet1.xml"), b"not an XLSX"):
            with self.subTest(length=len(raw)):
                with self.assertRaises(InputError):
                    _workbook_cells(raw)

    def test_pinned_source_audit_publishes_reproducible_candidate_without_modifying_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = {
                "article.html": b"invented pinned article bytes",
                "observations.xlsx": invented_xlsx(),
                "table1.png": b"invented table image bytes",
                "success.docx": b"invented success table bytes",
                "s3.docx": invented_s3_docx(),
            }
            for filename, raw in inputs.items():
                (root / filename).write_bytes(raw)
            from wombmodels import mathiesen_source as source
            with patch.object(source, "ARTICLE_SHA256", sha256(inputs["article.html"])), \
                 patch.object(source, "WORKBOOK_SHA256", sha256(inputs["observations.xlsx"])), \
                 patch.object(source, "TABLE1_SHA256", sha256(inputs["table1.png"])), \
                 patch.object(source, "SUCCESS_TABLE_SHA256", sha256(inputs["success.docx"])), \
                 patch.object(source, "S3_TABLE_SHA256", sha256(inputs["s3.docx"])):
                receipt = audit_mathiesen_source(root / "article.html", root / "observations.xlsx",
                    root / "table1.png", root / "success.docx", root / "s3.docx", root / "audit")
            self.assertEqual(receipt["metadata"]["n_source_cells"], 3190)
            self.assertFalse(receipt["metadata"]["model_fit"])
            self.assertTrue(verify_bundle(root / "audit", strict=True)["bytes_verified"])
            with (root / "audit/missingness_summary.csv").open(newline="") as stream:
                missingness_rows = list(csv.DictReader(stream))
            self.assertEqual(len(missingness_rows), 19)
            linkage = json.loads((root / "audit/candidate_unit_linkage.json").read_text())
            self.assertTrue(linkage["numeric_key_sets_match"])
            self.assertFalse(linkage["join_performed"])
            self.assertEqual(linkage["status"], "candidate link; not verified")
            self.assertTrue(linkage["source_hash_is_pinned"])
            audit_dataset = json.loads((root / "audit/input_dataset.json").read_text())
            self.assertEqual(len(audit_dataset["observations"]), 3190)
            source_intake = observation_report(root / "audit/input_dataset.json", root / "intake")
            self.assertEqual(source_intake["metadata"]["source_review_status"], "candidate")
            with (root / "intake/observation_records.csv").open(newline="") as stream:
                exported = next(csv.DictReader(stream))
            self.assertEqual(exported["source_locator"], "Placental perfusion!B3")
            exported_qualification = json.loads(exported["source_qualifications_json"])
            self.assertEqual(len(exported_qualification), 1)
            self.assertEqual(exported_qualification[0]["source_locator"], "PLOS Table 1, row ID 1")
            self.assertTrue(verify_bundle(root / "intake", strict=True)["bytes_verified"])
            for filename, raw in inputs.items():
                self.assertEqual((root / filename).read_bytes(), raw)

    def test_audit_rejects_changed_source_bytes_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = []
            for filename, raw in (("article", b"changed article"), ("data", invented_xlsx()),
                                  ("table", b"table"), ("success", b"success"),
                                  ("s3", invented_s3_docx())):
                path = root / filename
                path.write_bytes(raw)
                paths.append(path)
            with self.assertRaisesRegex(InputError, "hash differs"):
                audit_mathiesen_source(*paths, root / "out")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
