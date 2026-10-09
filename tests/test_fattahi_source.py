"""Invented scalar parser values; no source measurement or physiological fixture."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.fattahi_source import PANELS, _dataset, _extract_panels, audit_fattahi_source
from wombmodels.observations import observation_report


def invented_sheets():
    sheets = {panel[0]: {} for panel in PANELS}
    for sheet, header, header_cell, condition_row, first_row, columns, _, _ in PANELS:
        cells = sheets[sheet]
        cells[header_cell] = (header, "text", "")
        cells[f"B{condition_row-1}"] = ("Cadmium concentration (µM)", "text", "")
        conditions = ("0", "0.1", "1") if sheet == "Figure 2k" else ("0", "0.5", "1", "5", "10")
        for column, condition in zip(columns, conditions):
            cells[f"{column}{condition_row}"] = (condition, "numeric", condition)
            for row in range(first_row, first_row + 4):
                cells[f"A{row}"] = (f"Sample {row-first_row+1}", "text", "")
                cells[f"{column}{row}"] = (str(row), "numeric", str(row))
    return sheets


class FattahiSourceTests(unittest.TestCase):
    def test_readouts_preserve_lexemes_units_locators_and_unknown_pairing(self):
        rows = _extract_panels(invented_sheets())
        self.assertEqual(len(rows), 92)
        self.assertEqual(len({(r["sheet"], r["cell"]) for r in rows}), 92)
        self.assertEqual(len({r["source_metric_header"] for r in rows}), 5)
        self.assertTrue(all(r["paired_unit_identity"] == "not_established" for r in rows))
        glucose = [r for r in rows if r["sheet"] == "Figure 2k"]
        self.assertEqual(len(glucose), 12)
        self.assertTrue(all(r["reported_unit"] == "%" and r["functional_quantity"] == "receiver_concentration_change" for r in glucose))
        self.assertEqual(glucose[0]["source_numeric_text"], "6")
        hormone = [r for r in rows if r["sheet"] == "Figure 2i"]
        self.assertTrue(all(r["functional_quantity"] == "hormone_concentration" and r["reported_unit"] == "mIU/ml" for r in hormone))
        sheets = invented_sheets()
        sheets["Figure 2k"]["B6"] = ("0", "numeric", "0")
        zero = next(row for row in _extract_panels(sheets) if row["sheet"] == "Figure 2k" and row["cell"] == "B6")
        self.assertEqual(zero["value"], 0)
        self.assertEqual(zero["source_numeric_text"], "0")

    def test_no_identity_or_gestational_time_is_inferred_from_sample_labels(self):
        data = _dataset(_extract_panels(invented_sheets()), "source.xlsx")
        self.assertEqual(data["source_revision"]["review_status"], "candidate")
        self.assertEqual(data["transitions"], [])
        for record in data["observations"]:
            self.assertEqual(record["evidence_status"], "author_reported_summary")
            self.assertEqual(record["independent_unit"]["kind"], "not_reported")
            self.assertIsNone(record["independent_unit"]["id"])
            self.assertIsNone(record["developmental_interval"]["start"])
            self.assertIsNone(record["observation"]["measurement_time"])

    def test_changed_headers_conditions_labels_and_invalid_values_fail(self):
        bad = [("Figure 2h", "A2", ("Different unit", "text", "")),
            ("Figure 2k", "B4", ("Different exposure unit", "text", "")),
            ("Figure 2k", "B5", ("2", "numeric", "2")),
            ("Figure 2k", "A6", ("Different Sample", "text", ""))]
        for token in (None, "nan", "inf", "1e999", "-1", "nonnumeric"):
            bad += [("Figure 2k", "B6", (token, "numeric", token)),
                    ("Figure 2k", "B5", (token, "numeric", token))]
        bad.append(("Figure 2k", "B6", ("6", "text", "6")))
        for sheet, cell, value in bad:
            with self.subTest(sheet=sheet, cell=cell, value=value):
                sheets = invented_sheets()
                sheets[sheet][cell] = value
                with self.assertRaises(InputError):
                    _extract_panels(sheets)

    def test_pinned_publication_and_intake_are_exclusive_and_leave_source_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.xlsx"
            raw = b"Invented parser fixture, not a biological workbook."
            source.write_bytes(raw)
            with patch("wombmodels.fattahi_source.WORKBOOK_SHA256", sha256(raw)), patch(
                    "wombmodels.fattahi_source._figure_cells", side_effect=lambda raw, name: invented_sheets()[name]):
                audit_fattahi_source(source, root / "audit")
                with self.assertRaises(InputError):
                    audit_fattahi_source(source, root / "audit")
            self.assertEqual(source.read_bytes(), raw)
            self.assertTrue(verify_bundle(root / "audit", strict=True)["bytes_verified"])
            qualification = json.loads((root / "audit/qualification.json").read_text())
            self.assertEqual(qualification["n_published_values"], 92)
            self.assertEqual(qualification["cross_assay_pairing"], "not_established")
            self.assertEqual(qualification["model_fit"], "not_performed")
            plan = json.loads((root / "audit/reproduction_plan.json").read_text())
            self.assertIn("audit-fattahi-source", plan["command"])
            observation_report(root / "audit/input_dataset.json", root / "intake", source_root=root)
            report = json.loads((root / "intake/observation_intake_report.json").read_text())
            self.assertEqual(report["source_file_verification"]["n_verified"], 1)
            self.assertTrue(verify_bundle(root / "intake", strict=True)["bytes_verified"])

    def test_changed_source_revision_and_oversize_fail_without_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.xlsx"
            for raw in (b"Different bytes", b"x" * 1_000_001):
                source.write_bytes(raw)
                with self.assertRaises(InputError):
                    audit_fattahi_source(source, root / "audit")
                self.assertFalse((root / "audit").exists())
