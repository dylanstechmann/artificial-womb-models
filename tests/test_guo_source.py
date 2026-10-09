"""Artificial XLSX tests for exact transcription and qualification boundaries."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

from wombmodels import guo_source as source
from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report
from wombmodels.hori_source import NS


def fixture(*, bad_header=False, bad_numeric=False, extra=False, formula=False):
    groups = []
    for name, _, headers, counts, _ in source.PANELS:
        cells = {chr(65+col)+"1":(header,"s") for col,header in enumerate(headers)}
        for col,count in enumerate(counts):
            for row in range(2,2+count):
                cells[chr(65+col)+str(row)] = ("25.0000","n")
        groups.append((name,cells))
    profiles = {"B1":("40-MG","s"),"D1":("40-MGN","s"),"F1":("40-MGT","s")}
    for row in range(2,202):
        for col in ("A","B","D","F"):
            profiles[col+str(row)] = (str(row) if col == "A" else "0.5000","n")
    groups.append(("Sup 10 I",profiles))
    if bad_header:
        groups[3][1]["A1"] = ("guessed condition","s")
    if bad_numeric:
        groups[3][1]["A2"] = ("NaN","n")
    if extra:
        groups[3][1]["D2"] = ("0","n")
    texts = []
    for _,cells in groups:
        for text,kind in cells.values():
            if kind == "s" and text not in texts:
                texts.append(text)
    ns = NS
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,"w") as archive:
        archive.writestr("xl/workbook.xml",'<workbook xmlns="'+ns["s"]+'" xmlns:r="'+ns["r"]+'"><sheets>'+''.join(
            f'<sheet name="{name}" sheetId="{n}" r:id="r{n}"/>' for n,(name,_) in enumerate(groups,1))+'</sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="'+ns["p"]+'">'+''.join(
            f'<Relationship Id="r{n}" Type="{ns["r"]}/worksheet" Target="worksheets/sheet{n}.xml"/>' for n in range(1,7))+'</Relationships>')
        archive.writestr("xl/sharedStrings.xml",'<sst xmlns="'+ns["s"]+'">'+''.join('<si><t>'+escape(t)+'</t></si>' for t in texts)+'</sst>')
        for n,(_,cells) in enumerate(groups,1):
            rows = {}
            for locator,(text,kind) in cells.items():
                row = int(locator[1:])
                token = str(texts.index(text)) if kind == "s" else text
                xml = f'<c r="{locator}" t="{kind}"><v>{token}</v>'
                if formula and n == 4 and locator == "A2":
                    xml += '<f>1+1</f>'
                rows.setdefault(row,[]).append(xml+'</c>')
            archive.writestr(f"xl/worksheets/sheet{n}.xml",'<worksheet xmlns="'+ns["s"]+'"><sheetData>'+''.join(
                f'<row r="{row}">'+''.join(values)+'</row>' for row,values in rows.items())+'</sheetData></worksheet>')
    return buffer.getvalue()


class GuoAuditTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def publish(self,raw):
        path = self.root/"artificial.xlsx"
        path.write_bytes(raw)
        with patch.object(source,"WORKBOOK_SHA256",sha256(raw)):
            source.audit_guo_source(path,self.root/"audit")
        return path,self.root/"audit"

    def test_transcription_retains_lexemes_and_mechanical_values_stay_out_of_intake(self):
        raw = fixture()
        _,bundle = self.publish(raw)
        report = json.loads((bundle/"qualification.json").read_text())
        self.assertEqual((report["n_endpoint_cells"],report["n_developmental_percentage_cells"],report["n_profile_cells"]),(96,32,800))
        self.assertIsNone(report["starting_cohort_denominators"])
        self.assertEqual(report["stiffness_equivalence"],"not_established_by_nonsignificant_difference")
        self.assertFalse(report["mechanical_fit_performed"])
        self.assertIn("25.0000",(bundle/"endpoint_cells.csv").read_text())
        data = json.loads((bundle/"input_dataset.json").read_text())
        self.assertEqual(data["artifacts"][0]["sha256"],sha256(raw))
        for record in data["observations"]:
            self.assertEqual(record["assay"]["unit"],"%")
            self.assertIn(record["observation"]["measurement_time"],(3,4))
            self.assertIsNone(record["independent_unit"]["id"])
            self.assertIsNone(record["developmental_interval"]["end"])
            self.assertEqual(record["observation"]["replicate_role"],"not_reported")
        self.assertEqual(data["transitions"],[])
        self.assertTrue(verify_bundle(bundle,strict=True)["bytes_verified"])

    def test_candidate_intake_hashes_external_source_without_establishing_review(self):
        path,bundle = self.publish(fixture())
        output = self.root/"intake"
        observation_report(bundle/"input_dataset.json",output,source_root=self.root)
        report = json.loads((output/"observation_intake_report.json").read_text())
        self.assertEqual(report["source_review_status"],"candidate")
        self.assertEqual(report["source_file_verification"]["n_verified"],1)
        self.assertTrue(verify_bundle(output,strict=True)["bytes_verified"])
        self.assertEqual(verify_bundle(output)["scientific_review"],"not_established_by_this_tool")

    def test_changed_headers_extra_cells_nonfinite_and_formulas_fail_before_publication(self):
        for mutation in ("bad_header","bad_numeric","extra","formula"):
            raw = fixture(**{mutation:True})
            with self.subTest(mutation=mutation),self.assertRaises(InputError):
                self.publish(raw)
            self.assertFalse((self.root/"audit").exists())

    def test_wrong_hash_and_exclusive_output_are_enforced(self):
        path = self.root/"artificial.xlsx"
        raw = fixture()
        path.write_bytes(raw)
        with self.assertRaises(InputError):
            source.audit_guo_source(path,self.root/"wrong")
        self.assertFalse((self.root/"wrong").exists())
        _,bundle = self.publish(raw)
        with patch.object(source,"WORKBOOK_SHA256",sha256(raw)),self.assertRaises(InputError):
            source.audit_guo_source(path,bundle)
