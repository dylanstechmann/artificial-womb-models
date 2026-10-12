"""Artificial XLSX tests for exact transcription and qualification boundaries."""
import csv
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
    panel_j = {"A1":("40-MG","s"),"B1":("40-MGT","s"),"C1":("40-MGN","s")}
    for col in ("A","B","C"):
        for row in range(2,5):
            panel_j[col+str(row)] = ("25.0000","n")
    groups.append(("Sup10J",panel_j))
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
            f'<Relationship Id="r{n}" Type="{ns["r"]}/worksheet" Target="worksheets/sheet{n}.xml"/>' for n in range(1,8))+'</Relationships>')
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

    def test_exact_mechanical_lexeme_overlap_does_not_infer_pairing(self):
        endpoints = [
            {"sheet":"Fig4A", "source_condition":"40-MG", "numeric_text":"5.833", "cell":"A2"},
            {"sheet":"Fig4A", "source_condition":"40-MG", "numeric_text":"5.833", "cell":"A3"},
            {"sheet":"Fig4D", "source_condition":"40-MG", "numeric_text":"5.833", "cell":"A2"},
            {"sheet":"Fig4D", "source_condition":"40-MG", "numeric_text":"7.000", "cell":"A3"},
        ]
        overlaps = source._mechanical_value_overlaps(endpoints)
        self.assertEqual(len(overlaps),1)
        self.assertEqual(overlaps[0]["n_matching_lexemes"],1)
        self.assertEqual(overlaps[0]["n_left_source_cells"],2)
        self.assertEqual(overlaps[0]["n_right_source_cells"],1)
        self.assertEqual(overlaps[0]["matches"],[{
            "numeric_text":"5.833", "left_cells":["A2","A3"], "right_cells":["A2"]}])
        self.assertIn("do not infer pairing",overlaps[0]["interpretation_limit"])

    def test_40mg_cross_panel_scale_check_is_descriptive_and_keeps_method_boundary(self):
        endpoints = [
            {"sheet":sheet,"source_condition":"40-MG","value":float(value)}
            for sheet,values in (("Fig4A",range(1,10)),("Fig4D",range(1,6)))
            for value in values
        ]
        panel_j = [{"source_condition":"40-MG","value":30.0} for _ in range(3)]
        check = source._summarize_40mg_cross_panel_scale(endpoints,panel_j)
        self.assertEqual(check["comparability_status"],"unresolved_protocol_and_run_hierarchy")
        self.assertEqual(check["descriptive_summaries"]["Figure 4A"]["n_source_values"],9)
        self.assertEqual(check["descriptive_summaries"]["Figure 4D"]["method_status"],
                         "figure caption identifies nanoindentation")
        self.assertEqual(check["descriptive_summaries"]["Supplementary Fig. 10J"]["method_status"],
                         "figure caption identifies rheometer")
        self.assertEqual(check["supplementary_10j_mean_to_figure_4_mean_ratios"]["vs_figure_4a"],6.0)
        self.assertEqual(check["supplementary_10j_mean_to_figure_4_mean_ratios"]["vs_figure_4d"],10.0)
        self.assertEqual(check["supplementary_10j_range_overlap_with_figure_4"],
                         {"with_figure_4a":False,"with_figure_4d":False})
        self.assertFalse(check["values_enter_observation_intake"])
        self.assertFalse(check["values_enter_mechanical_fit"])

    def test_profile_half_response_check_preserves_raw_crossing_brackets(self):
        curves = [
            {"cell":"A2","column_role":"source_time_coordinate","value":5.0},
            {"cell":"A3","column_role":"source_time_coordinate","value":10.0},
            {"cell":"A4","column_role":"source_time_coordinate","value":15.0},
            {"cell":"A5","column_role":"source_time_coordinate","value":20.0},
            {"cell":"B2","column_role":"source_response_profile","source_condition":"40-MG","value":0.8},
            {"cell":"B3","column_role":"source_response_profile","source_condition":"40-MG","value":0.6},
            {"cell":"B4","column_role":"source_response_profile","source_condition":"40-MG","value":0.4},
            {"cell":"B5","column_role":"source_response_profile","source_condition":"40-MG","value":0.7},
        ]
        panel_j = [
            {"source_condition":"40-MG","value":value}
            for value in (11.0,12.0,13.0)
        ]
        check = source._profile_half_response_crossing_check(curves,panel_j)
        result = check["condition_checks"]["40-MG"]
        self.assertEqual(result["n_observed_downward_crossings"],1)
        self.assertEqual(result["n_observed_upward_crossings"],1)
        self.assertEqual(result["first_downward_crossing_bracket"]["time_interval_seconds"],[10.0,15.0])
        self.assertEqual(result["sup10j_mean_seconds"],12.0)
        self.assertEqual(result["sup10j_mean_position_vs_first_bracket"],"within_observed_bracket")
        self.assertEqual(result["gap_from_sup10j_mean_to_first_bracket_seconds"],0.0)
        self.assertFalse(check["values_enter_mechanical_fit"])

    def test_transcription_retains_lexemes_and_mechanical_values_stay_out_of_intake(self):
        raw = fixture()
        _,bundle = self.publish(raw)
        report = json.loads((bundle/"qualification.json").read_text(encoding="utf-8"))
        self.assertEqual((report["n_endpoint_cells"],report["n_developmental_percentage_cells"],report["n_profile_cells"]),(96,32,800))
        axis_context = {item["panel"]:item for item in report["mechanical_panel_axis_qualification"]}
        self.assertIn("names no assay",axis_context["Fig4A"]["method_mapping_status"])
        self.assertIn("nanoindentation",axis_context["Fig4D"]["method_mapping_status"])
        self.assertIsNone(report["starting_cohort_denominators"])
        n_qualification = report["developmental_outcome_n_qualification"]
        self.assertEqual(n_qualification["caption_n_statement"],f"n {chr(0x2265)} 4")
        self.assertEqual(n_qualification["minimum_n_stated"],4)
        self.assertIsNone(n_qualification["exact_n_by_condition"])
        self.assertEqual(n_qualification["populated_percentage_cell_counts_by_condition"],{
            "Fig4E":{"40-MG":7,"40-MGT":4,"40-MGN":5},
            "Fig4F":{"40-MG":7,"40-MGT":4,"40-MGN":5}})
        self.assertIn("not verified biological n",n_qualification["cell_count_semantics"])
        axes = {item["panel"]:item for item in report["mechanical_panel_axis_qualification"]}
        self.assertEqual((axes["Fig4A"]["unit"],axes["Fig4A"]["axis_scale"]),("s","linear"))
        self.assertIn("independent experiments",axes["Fig4A"]["caption_n"])
        self.assertEqual((axes["Fig4C"]["unit"],axes["Fig4C"]["axis_scale"]),
                         ("Pa","logarithmic (10^1 and 10^2 ticks)"))
        self.assertEqual(axes["Fig4D"]["unit"],"s")
        self.assertIn("remain unqualified",report["mechanical_units_loading_normalization"])
        self.assertEqual(report["stiffness_equivalence"],"not_established_by_nonsignificant_difference")
        endpoints = list(csv.DictReader(io.StringIO((bundle/"endpoint_cells.csv").read_text(encoding="utf-8"))))
        mechanical = {item["sheet"]:item for item in endpoints if item["sheet"] in ("Fig4A","Fig4C","Fig4D")}
        self.assertEqual((mechanical["Fig4A"]["reported_unit"],mechanical["Fig4A"]["unit_status"]),
                         ("s","axis_reported"))
        self.assertEqual((mechanical["Fig4C"]["reported_unit"],mechanical["Fig4C"]["reported_axis_scale"]),
                         ("Pa","logarithmic (10^1 and 10^2 ticks)"))
        methods = report["mechanical_measurement_context"]
        self.assertEqual(methods["rheometer_relaxation"]["loading_mode"],"fixed strain, 1%")
        self.assertEqual(methods["rheometer_relaxation"]["response_normalization"],
                         "stress normalized to initial maximum stress")
        self.assertIn("three-element generalized Maxwell",methods["rheometer_relaxation"]["fit_model"])
        self.assertEqual(methods["nanoindentation_relaxation"]["loading_history"],
                         "4 s loading to 15,000 nm indentation depth, 40 s hold, then 4 s unloading")
        self.assertIn("three experiments per tested sample",
                      methods["nanoindentation_relaxation"]["repeat_statement"])
        self.assertEqual(methods["young_modulus_method_mapping"]["mapping_status"],
                         "not_explicitly_established_for_figure_4c")
        profile_context = report["supplementary_profile_qualification"]
        self.assertEqual((profile_context["workbook_sheet"],profile_context["x_unit"],
                          profile_context["response_axis_label"],profile_context["assay"]),
                         ("Sup 10 I","s","σ/σ₀","rheometer"))
        self.assertEqual(profile_context["source_time_coordinate_count"],200)
        self.assertEqual(profile_context["n_source_response_columns"],3)
        self.assertFalse(profile_context["profiles_enter_observation_intake"])
        self.assertIn("n=3 independent experiments",profile_context["adjacent_panel_j_scope"])
        profile_grid = profile_context["profile_grid_qualification"]
        self.assertEqual(profile_grid["n_time_coordinates"],200)
        self.assertTrue(profile_grid["time_grid_unique"])
        self.assertTrue(profile_grid["time_grid_strictly_increasing"])
        self.assertEqual(profile_grid["time_range_seconds"],[2.0,201.0])
        self.assertFalse(profile_grid["zero_second_coordinate_present"])
        self.assertEqual(profile_grid["condition_profiles"]["40-MG"]["n_adjacent_increases"],0)
        profile_cells = list(csv.DictReader(io.StringIO((bundle/"profile_cells.csv").read_text(encoding="utf-8"))))
        profile_by_cell = {item["cell"]:item for item in profile_cells}
        self.assertEqual((profile_by_cell["A2"]["reported_unit"],profile_by_cell["A2"]["reported_axis_label"],
                          profile_by_cell["A2"]["unit_status"]),
                         ("s","Time (s)","axis_reported"))
        self.assertEqual((profile_by_cell["B2"]["reported_unit"],profile_by_cell["B2"]["reported_axis_label"],
                          profile_by_cell["B2"]["unit_status"]),
                         ("dimensionless","σ/σ₀","axis_and_caption_reported"))
        panel_j = report["supplementary_panel_j_qualification"]
        self.assertEqual(panel_j["n_source_cells"],9)
        self.assertEqual(panel_j["n_source_values_by_condition"],{
            "40-MG":3,"40-MGT":3,"40-MGN":3})
        self.assertEqual(panel_j["caption_n"],"n=3 independent experiments per condition")
        self.assertEqual(panel_j["assay"],"rheometer")
        self.assertFalse(panel_j["values_enter_observation_intake"])
        self.assertEqual(panel_j["derived_summary_reconstruction"]["40-MG"]["mean_from_source_cells"],25.0)
        self.assertEqual(panel_j["derived_summary_reconstruction"]["40-MG"]["sample_sd_from_source_cells"],0.0)
        summary_cells = list(csv.DictReader(io.StringIO(
            (bundle/"supplementary_panel_j_cells.csv").read_text(encoding="utf-8"))))
        self.assertEqual(len(summary_cells),9)
        self.assertEqual((summary_cells[0]["source_panel"],summary_cells[0]["reported_unit"],
                          summary_cells[0]["caption_n"]),
                         ("Supplementary Fig. 10J","s","n=3 independent experiments per condition"))
        cross_panel = report["mechanical_40mg_cross_panel_scale_check"]
        self.assertEqual(cross_panel["supplementary_10j_mean_to_figure_4_mean_ratios"]["vs_figure_4a"],1.0)
        self.assertEqual(cross_panel["supplementary_10j_range_overlap_with_figure_4"],
                         {"with_figure_4a":True,"with_figure_4d":True})
        self.assertFalse(cross_panel["values_enter_observation_intake"])
        self.assertIn("no strong scale-separation flag",(bundle/"REPORT.md").read_text(encoding="utf-8"))
        profile_crossings = report["supplementary_profile_half_response_crossing_check"]["condition_checks"]
        self.assertIsNone(profile_crossings["40-MG"]["first_downward_crossing_bracket"])
        self.assertFalse(report["mechanical_fit_performed"])
        self.assertIn("25.0000",(bundle/"endpoint_cells.csv").read_text())
        data = json.loads((bundle/"input_dataset.json").read_text(encoding="utf-8"))
        self.assertEqual(data["artifacts"][0]["sha256"],sha256(raw))
        for record in data["observations"]:
            self.assertEqual(record["assay"]["unit"],"%")
            self.assertIn(record["observation"]["measurement_time"],(3,4))
            self.assertIsNone(record["independent_unit"]["id"])
            self.assertIsNone(record["developmental_interval"]["end"])
            self.assertEqual(record["observation"]["replicate_role"],"not_reported")
            self.assertTrue(any("n ≥ 4" in item for item in record["limitations"]))
        self.assertEqual(data["transitions"],[])
        self.assertTrue(verify_bundle(bundle,strict=True)["bytes_verified"])

    def test_linked_supplement_snapshot_is_hash_checked_when_present(self):
        raw = fixture()
        workbook = self.root/"guo-source-data.xlsx"
        workbook.write_bytes(raw)
        supplement = self.root/"guo-supplementary-information.pdf"
        supplement_bytes = b"pinned supplemental PDF fixture"
        supplement.write_bytes(supplement_bytes)
        output = self.root/"audit"
        with patch.object(source,"WORKBOOK_SHA256",sha256(raw)), \
             patch.object(source,"SUPPLEMENTARY_INFO_SHA256",sha256(supplement_bytes)), \
             patch.object(source,"SUPPLEMENTARY_INFO_SIZE_BYTES",len(supplement_bytes)):
            source.audit_guo_source(workbook,output)
        manifest = json.loads((output/"input_source_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["linked_context_source"]["local_snapshot_hash_verified_during_audit"])

    def test_linked_article_snapshot_is_hash_checked_when_present(self):
        raw = fixture()
        workbook = self.root/"guo-source-data.xlsx"
        workbook.write_bytes(raw)
        article = self.root/"guo-niche.html"
        article_bytes = b"pinned Guo article text fixture"
        article.write_bytes(article_bytes)
        output = self.root/"audit"
        with patch.object(source,"WORKBOOK_SHA256",sha256(raw)), \
             patch.object(source,"ARTICLE_HTML_SHA256",sha256(article_bytes)), \
             patch.object(source,"ARTICLE_HTML_SIZE_BYTES",len(article_bytes)):
            source.audit_guo_source(workbook,output)
        manifest = json.loads((output/"input_source_manifest.json").read_text(encoding="utf-8"))
        context = manifest["linked_article_context_source"]
        self.assertTrue(context["local_snapshot_hash_verified_during_audit"])
        self.assertIn("Figure 4 caption, panels A and D",context["reviewed_locators"])

    def test_candidate_intake_hashes_external_source_without_establishing_review(self):
        path,bundle = self.publish(fixture())
        output = self.root/"intake"
        observation_report(bundle/"input_dataset.json",output,source_root=self.root)
        report = json.loads((output/"observation_intake_report.json").read_text(encoding="utf-8"))
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
