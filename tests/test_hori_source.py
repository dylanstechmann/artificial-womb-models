"""Artificial parser fixtures, not source study measurements."""
from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.hori_source import (COMPOUNDS, GROUPS, _dataset, _extract_endpoints,
                                    _figure_cells, _summaries, audit_hori_source)
from wombmodels.observations import observation_report


def invented_cells():
    cells = {}
    for compound, labels, values in COMPOUNDS:
        cells[labels + "2"] = (compound, "text", "")
        cells[values + "3"] = ("Papp (x10-6 cm/s)", "text", "")
        for group, start, _ in GROUPS:
            for row in range(start, start + 4):
                cells[labels + str(row)] = (group, "text", "")
                cells[values + str(row)] = (str(row), "numeric", str(row))
    return cells


class HoriSourceAuditTests(unittest.TestCase):
    def test_endpoint_locators_do_not_become_unit_ids_or_pairs(self):
        rows = _extract_endpoints(invented_cells())
        self.assertEqual(len(rows), 48)
        self.assertEqual(len({row["cell"] for row in rows}), 48)
        data = _dataset(rows, "source.xlsx")
        self.assertEqual(data["source_revision"]["review_status"], "candidate")
        self.assertEqual(data["source_revision"]["reviewer"], "")
        self.assertEqual(data["transitions"], [])
        for record in data["observations"]:
            self.assertIsNone(record["independent_unit"]["id"])
            self.assertEqual(record["independent_unit"]["kind"], "not_reported")
            self.assertEqual(record["observation"]["replicate_role"], "not_reported")
            self.assertIsNone(record["observation"]["measurement_time"])
            self.assertEqual(record["assay"]["unit"], "x10-6 cm/s")
            self.assertEqual(record["evidence_status"], "author_reported_summary")
        self.assertEqual(sum(r["developmental_interval"]["start"] == 6 for r in data["observations"]), 24)
        self.assertEqual(sum(r["developmental_interval"]["start"] is None for r in data["observations"]), 24)
        summary = _summaries(rows)
        self.assertEqual(len(summary), 12)
        self.assertEqual(summary[0]["mean"], 5.5)
        self.assertTrue(all(r["n_values"] == 4 and r["n_reported_unit_ids"] == 0 for r in summary))

    def test_changed_units_labels_and_missing_or_invalid_values_fail(self):
        mutations = [{"B3": ("cm/s", "text", "")}, {"A2": ("other compound", "text", "")},
                     {"A4": ("HU", "text", "")}, {"B4": (None, "numeric", None)},
                     {"B4": ("1.0", "text", "")}, {"B4": ("nan", "numeric", "nan")},
                     {"B4": ("1e99999", "numeric", "1e99999")}, {"B4": ("-1", "numeric", "-1")}]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                cells = copy.deepcopy(invented_cells())
                cells.update(mutation)
                with self.assertRaises(InputError):
                    _extract_endpoints(cells)

    def test_wrong_source_hash_and_oversize_fail_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.xlsx"
            for content in (b"not the source", b"x" * 1_000_001):
                source.write_bytes(content)
                with self.assertRaises(InputError):
                    audit_hori_source(source, root / "out")
                self.assertFalse((root / "out").exists())

    def test_archive_reader_rejects_formulas_duplicate_cells_and_unsafe_xml(self):
        s = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        p = "http://schemas.openxmlformats.org/package/2006/relationships"
        def archive(cell_xml, *, target="worksheets/sheet9.xml", shared="<si><t>text</t></si>"):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as z:
                z.writestr("xl/workbook.xml", f'<workbook xmlns="{s}" xmlns:r="{r}"><sheets><sheet name="Fig. 5G" r:id="rId9"/></sheets></workbook>')
                z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="{p}"><Relationship Id="rId9" Type="{r}/worksheet" Target="{target}"/></Relationships>')
                z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{s}">{shared}</sst>')
                z.writestr("xl/worksheets/sheet9.xml", f'<worksheet xmlns="{s}"><sheetData><row>{cell_xml}</row></sheetData></worksheet>')
            return stream.getvalue()
        self.assertEqual(_figure_cells(archive('<c r="B4"><v>1.25</v></c>'))["B4"], ("1.25", "numeric", "1.25"))
        invalid = [archive('<c r="B4"><f>1+1</f><v>2</v></c>'),
                   archive('<c r="B4"><v>1</v></c><c r="B4"><v>2</v></c>'),
                   archive('<c r="B4" t="s"><v>99</v></c>'),
                   archive('', target="../unsafe.xml"), archive('', shared="<!ENTITY x 'bad'>"),
                   b"browser challenge instead of workbook"]
        for raw in invalid:
            with self.subTest(raw_length=len(raw)):
                with self.assertRaises(InputError):
                    _figure_cells(raw)

    def test_symlink_file_or_source_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / "real"
            real.mkdir()
            (real / "source.xlsx").write_bytes(b"invented source")
            try:
                (root / "linked").symlink_to(real, target_is_directory=True)
                (root / "file.xlsx").symlink_to(real / "source.xlsx")
            except OSError:
                self.skipTest("Platform does not permit test symlinks")
            for source in (root / "file.xlsx", root / "linked/source.xlsx"):
                with self.subTest(source=source):
                    with self.assertRaisesRegex(InputError, "nonsymlink"):
                        audit_hori_source(source, root / "out")
                    self.assertFalse((root / "out").exists())

    def test_publication_and_downstream_intake_preserve_sources_and_review(self):
        # Patch source fingerprint/reader only for these invented software inputs.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.xlsx"
            source.write_bytes(b"invented parser input; not an empirical workbook")
            raw = source.read_bytes()
            with patch("wombmodels.hori_source.WORKBOOK_SHA256", sha256(raw)), patch(
                    "wombmodels.hori_source._figure_cells", return_value=invented_cells()):
                receipt = audit_hori_source(source, root / "audit")
                with self.assertRaises(InputError):
                    audit_hori_source(source, root / "audit")
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(receipt["input_sha256"], sha256(raw))
            self.assertIn("src/wombmodels/hori_source.py", receipt["implementation_sha256"])
            self.assertTrue(verify_bundle(root / "audit", strict=True)["bytes_verified"])
            plan = json.loads((root / "audit/reproduction_plan.json").read_text())
            self.assertIn("audit-hori-source", plan["command"])
            self.assertIn("external", str(plan["inputs"]))
            self.assertFalse(any("Every value in these fixtures" in item for item in plan["limits"]))
            observation_report(root / "audit/input_dataset.json", root / "intake", source_root=root)
            report = json.loads((root / "intake/observation_intake_report.json").read_text())
            self.assertEqual(report["n_observation_records"], 48)
            self.assertEqual(report["n_exact_comparison_groups"], 12)
            self.assertEqual(report["source_file_verification"]["n_verified"], 1)
            self.assertEqual(report["source_file_verification"]["n_not_checked"], 1)
            self.assertEqual(report["source_interval_containment"]["n_contained"], 24)
            self.assertEqual(report["source_interval_containment"]["n_not_assessed"], 24)
            self.assertTrue(verify_bundle(root / "intake", strict=True)["bytes_verified"])
            (root / "audit/group_summary.csv").write_bytes(b"tampered")
            self.assertFalse(verify_bundle(root / "audit", strict=True)["bytes_verified"])
