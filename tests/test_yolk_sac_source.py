"""Invented scalar/XML fixtures test audit boundaries, not biological readouts."""
import copy
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

from wombmodels import yolk_sac_source as source
from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.hori_source import NS


def cells_fixture():
    cells = {}
    def text(cell, value):
        cells[cell] = (value, "text", None)
    for panel, title, title_row, first, last, first_day in source.PANELS:
        for cell, value in ((f"A{title_row-1}", panel), (f"B{title_row}", title),
                            (f"B{title_row+1}", "NC"), (f"G{title_row+1}", "WEC"),
                            (f"E{title_row+1}", "mean"), (f"F{title_row+1}", "SD"),
                            (f"J{title_row+1}", "mean"), (f"K{title_row+1}", "SD")):
            text(cell, value)
        for index, row in enumerate(range(first, last+1)):
            text(f"A{row}", f"D{first_day+index}")
            value = [1, 10, 5, 4, 6, 12, 7, 6, 5, 4, 3][index]
            for col, number in zip("BCDEFGHIJK", [.25, .5, .75, .5, .25,
                                                       value-.25, value, value+.25, value, .25]):
                token = f"{number:.4f}"
                cells[f"{col}{row}"] = (token, "numeric", token)
    return cells


def workbook_fixture(cells):
    texts = sorted({token for token, kind, _ in cells.values() if kind == "text"})
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{NS["s"]}" xmlns:r="{NS["r"]}"><sheets>' + ''.join(
            f'<sheet name="{name}" r:id="r{i}"/>' for i, name in enumerate(source.SHEETS, 1)) + '</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="{NS["p"]}">' + ''.join(
            f'<Relationship Id="r{i}" Type="{NS["r"]}/worksheet" Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, 5)) + '</Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{NS["s"]}">' + ''.join(
            '<si><t>' + escape(t) + '</t></si>' for t in texts) + '</sst>')
        for i, name in enumerate(source.SHEETS, 1):
            body = ''.join(f'<c r="{cell}" t="{"s" if kind == "text" else "n"}"><v>'
                + (str(texts.index(token)) if kind == "text" else token) + '</v></c>'
                for cell, (token, kind, _) in (cells.items() if name == "Figure 5" else []))
            z.writestr(f"xl/worksheets/sheet{i}.xml", f'<worksheet xmlns="{NS["s"]}"><sheetData><row r="1">'
                       + body + '</row></sheetData></worksheet>')
    return b.getvalue()


class YolkSacSourceTests(unittest.TestCase):
    def test_pinned_audit_retains_unknown_units_timing_and_relocation(self):
        raw = workbook_fixture(cells_fixture())
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "invented.xlsx"
            path.write_bytes(raw)
            with patch.object(source, "WORKBOOK_SHA256", sha256(raw)):
                source.audit_yolk_sac_source(path, root / "audit")
                with self.assertRaises(InputError):
                    source.audit_yolk_sac_source(path, root / "audit")
            self.assertEqual(path.read_bytes(), raw)
            q = json.loads((root / "audit/qualification.json").read_text())
            self.assertEqual(q["n_source_numeric_cells"], 310)
            self.assertEqual(q["n_source_time_rows"], 31)
            self.assertEqual(q["n_summary_arithmetic_checks"], 124)
            self.assertEqual(q["n_summary_arithmetic_mismatches"], 0)
            self.assertIsNone(q["starting_cohort_denominators"])
            self.assertFalse(q["biological_fit_performed"])
            self.assertFalse(q["timing_reconciliation"]["labels_agree"])
            self.assertEqual([v["time_label"] for v in q["timing_reconciliation"]["workbook_mean_interior_maxima"]], ["D1", "D5"])
            self.assertIn("1.0000", (root / "audit/source_cells.csv").read_text())
            self.assertFalse((root / "audit/input_dataset.json").exists())
            plan = json.loads((root / "audit/reproduction_plan.json").read_text())
            self.assertIn("external pinned source workbook (not bundled)", plan["inputs"])
            self.assertIn("audit-yolk-sac-source", plan["command"])
            moved = root / "moved"
            (root / "audit").rename(moved)
            result = verify_bundle(moved, strict=True)
            self.assertTrue(result["bytes_verified"], result["errors"])
            self.assertEqual(result["scientific_review"], "not_established_by_this_tool")
            (moved / "source_cells.csv").write_text("changed\n")
            self.assertFalse(verify_bundle(moved, strict=True)["bytes_verified"])

    def test_changed_hash_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "changed.xlsx"
            path.write_bytes(b"Invented unsupported source revision")
            with self.assertRaisesRegex(InputError, "size/hash"):
                source.audit_yolk_sac_source(path, root / "audit")
            self.assertFalse((root / "audit").exists())

    def test_missing_changed_nonfinite_extra_cells_rejected(self):
        original = cells_fixture()
        changes = [("B2", ("guessed unit", "text", None)), ("A35", ("D2", "text", None)),
                   ("G35", ("NaN", "numeric", "NaN")), ("G35", ("-1", "numeric", "-1")),
                   ("G35", (None, "numeric", None)), ("G35", ("x"*129, "numeric", "x"*129)),
                   ("L45", ("1", "numeric", "1"))]
        for cell, value in changes:
            with self.subTest(cell=cell, value=value):
                cells = copy.deepcopy(original)
                cells[cell] = value
                with self.assertRaises(InputError):
                    source._extract(cells)

    def test_summary_mismatch_preserved_not_repaired(self):
        cells = cells_fixture()
        cells["J35"] = ("11.0000", "numeric", "11.0000")
        rows, checks, _ = source._extract(cells)
        self.assertEqual(sum(not row["arithmetic_matches"] for row in checks), 1)
        row = next(row for row in rows if row["cell"] == "J35")
        self.assertEqual(row["source_numeric_text"], "11.0000")
        self.assertIsNone(row["reported_concentration_unit"])
        self.assertIsNone(row["biological_unit_id"])

    def test_local_maxima_excludes_endpoints_and_plateaus(self):
        for values, expected in (([3, 2, 1], []), ([1, 2, 2, 1], []), ([1, 3, 1], ["D1"])):
            p = [{"time_label": f"D{i}", "value": value} for i, value in enumerate(values)]
            self.assertEqual([row["time_label"] for row in source._local_maxima(p)], expected)


if __name__ == "__main__":
    unittest.main()
