import csv
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/early-exchange-transition-2026-10-11"
INVENTORY = ROOT / "config/source_inventories/early_exchange_transition_2026.json"
CROSSWALK = ROOT / "config/source_inventories/goh_2023_emtab11673_sample_crosswalk.csv"


class Goh2023F158CoronalAccessionSearchTests(unittest.TestCase):
    def test_pinned_biostudies_searches_find_no_second_human_fetal_candidate(self):
        expected = {
            "biostudies-search-all-F158.json": 16,
            "biostudies-search-all-16099.json": 39,
            "biostudies-search-all-coronal-section.json": 27,
            "biostudies-search-ArrayExpress-F158.json": 3,
            "biostudies-search-ArrayExpress-16099.json": 5,
            "biostudies-search-ArrayExpress-coronal-section.json": 9,
        }
        for filename, expected_hits in expected.items():
            snapshot = json.loads((ARTIFACTS / filename).read_text(encoding="utf-8"))
            self.assertEqual(snapshot["totalHits"], expected_hits)
            self.assertTrue(snapshot["isTotalHitsExact"])
            self.assertEqual(len(snapshot["hits"]), expected_hits)
            self.assertEqual(
                sum(hit.get("accession") == "E-MTAB-11673" for hit in snapshot["hits"]),
                1,
            )

        for filename in [
            "biostudies-search-all-F158.json",
            "biostudies-search-all-16099.json",
            "biostudies-search-all-coronal-section.json",
        ]:
            snapshot = json.loads((ARTIFACTS / filename).read_text(encoding="utf-8"))
            candidate_titles = [
                hit.get("title", "")
                for hit in snapshot["hits"]
                if any(term in hit.get("title", "").casefold() for term in ("fetal", "yolk sac"))
            ]
            self.assertEqual(
                candidate_titles,
                ["Human fetal yolk sac scRNA-seq data (sample ID: F158 for Haniffa Lab; 16099 for HDBR)"],
            )

    def test_ena_browser_records_confirm_the_existing_f158_yolk_sac_links(self):
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))

        project_root = ET.parse(ARTIFACTS / "ERP137250-ena-browser.xml").getroot()
        project = project_root.find(".//PROJECT")
        self.assertEqual(project.attrib["accession"], "PRJEB52523")
        self.assertEqual(project.attrib["alias"], "E-MTAB-11673")
        self.assertEqual(project.findtext("./IDENTIFIERS/SECONDARY_ID"), "ERP137250")

        for row in rows:
            sample_root = ET.parse(ARTIFACTS / f"{row['ena_sample']}-ena-browser.xml").getroot()
            sample = sample_root.find(".//SAMPLE")
            self.assertEqual(sample.attrib["accession"], row["biosample"])
            self.assertEqual(sample.attrib["alias"], f"E-MTAB-11673:{row['source_name']}")
            self.assertEqual(sample.findtext("./IDENTIFIERS/SECONDARY_ID"), row["ena_sample"])

            run_root = ET.parse(ARTIFACTS / f"{row['ena_run']}-ena-browser.xml").getroot()
            run = run_root.find(".//RUN")
            self.assertEqual(run.attrib["accession"], row["ena_run"])
            self.assertEqual(run.attrib["alias"], f"E-MTAB-11673:{row['source_name']}")
            self.assertEqual(run.find("./EXPERIMENT_REF").attrib["accession"], row["ena_experiment"])
            self.assertIn("F158", run.findtext("TITLE", ""))
            self.assertIn("carnegie stage 17", run.findtext("TITLE", "").casefold())
            self.assertEqual(len(run.findall("./DATA_BLOCK/FILES/FILE")), 3)

    def test_inventory_pins_search_and_direct_ena_metadata_with_scope_limit(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        review = source["coronal_section_accession_search"]
        self.assertEqual(
            review["identified_matched_coronal_accession"],
            "E-MTAB-11911 (ENA project PRJEB53919; study ERP138734)",
        )
        self.assertIn("do not infer global absence", review["ena_search_qualification"])
        for declaration in review["search_snapshots"] + review["ena_browser_snapshots"]:
            path = ROOT / declaration["path"]
            self.assertEqual(path.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])

    def test_supplement_table_and_ega_brain_candidate_are_pinned_but_unmatched(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )

        table_review = source["supplementary_table_s6_screen"]
        self.assertEqual(table_review["nonempty_dataset_rows"], 51)
        self.assertEqual(table_review["yolk_sac_rows"], 3)
        self.assertEqual(
            table_review["term_matches_in_table"],
            {"F158": 0, "16099": 0, "coronal": 0},
        )
        self.assertEqual(
            source["coronal_section_accession_search"]["identified_matched_coronal_accession"],
            "E-MTAB-11911 (ENA project PRJEB53919; study ERP138734)",
        )

        with (ROOT / table_review["csv_extract_path"]).open(encoding="utf-8", newline="") as stream:
            table_rows = list(csv.DictReader(stream))
        self.assertEqual(len(table_rows), 51)
        self.assertEqual(sum(row["Datasets"].casefold().startswith("yolk sac") for row in table_rows), 3)
        fetal_brain = next(row for row in table_rows if row["Datasets"] == "Fetal Brain")
        self.assertEqual(fetal_brain["source_data_row_number"], "20")
        self.assertEqual(fetal_brain["Biological replicates and number cells"], "n=26, k=1,665,937")
        self.assertEqual(fetal_brain["Stage/Age"], "3-6 PCW")
        self.assertEqual(fetal_brain["Notes"], "")
        self.assertEqual(fetal_brain["Reannotated"], "TRUE")
        for term in ("f158", "16099", "coronal"):
            self.assertNotIn(term, (ROOT / table_review["csv_extract_path"]).read_text(encoding="utf-8").casefold())

        ega_review = source["candidate_brain_atlas_public_metadata_screen"]
        expected_counts = {"EGAD00001006049": 379, "EGAD50000001295": 69}
        expected_subject_counts = {"EGAD00001006049": 25, "EGAD50000001295": 6}
        for declaration in table_review["snapshots"] + ega_review["snapshots"]:
            path = ROOT / declaration["path"]
            self.assertEqual(path.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])
        extract_path = ROOT / table_review["csv_extract_path"]
        self.assertEqual(extract_path.stat().st_size, table_review["csv_extract_bytes"])
        self.assertEqual(hashlib.sha256(extract_path.read_bytes()).hexdigest(), table_review["csv_extract_sha256"])

        for record in ega_review["dataset_sample_records"]:
            self.assertEqual(record["sample_record_count"], expected_counts[record["accession"]])
            self.assertEqual(record["api_head_total_count"], expected_counts[record["accession"]])
            self.assertEqual(record["unique_subject_id_values"], expected_subject_counts[record["accession"]])
            samples = json.loads((ARTIFACTS / f"ega-{record['accession'].casefold()}-samples.json").read_text(encoding="utf-8"))
            self.assertEqual(len(samples), record["sample_record_count"])
            serialized = json.dumps(samples, ensure_ascii=False).casefold()
            for term in ("f158", "16099", "coronal"):
                self.assertNotIn(term, serialized)
        self.assertEqual(ega_review["unique_subject_id_values_across_datasets"], 29)
        self.assertEqual(ega_review["exact_text_screen"]["sample_records_with_any_exact_term"], 0)
        self.assertEqual(ega_review["six_week_brain_like_metadata"]["sample_record_count"], 15)

        table_review = ega_review["sample_table_workbook_review"]
        workbook_path = ROOT / table_review["workbook_snapshot"]["path"]
        self.assertEqual(workbook_path.stat().st_size, table_review["workbook_snapshot"]["bytes"])
        self.assertEqual(
            hashlib.sha256(workbook_path.read_bytes()).hexdigest(),
            table_review["workbook_snapshot"]["sha256"],
        )
        crosswalk_path = ROOT / table_review["csv_crosswalk_path"]
        self.assertEqual(crosswalk_path.stat().st_size, table_review["csv_crosswalk_bytes"])
        self.assertEqual(
            hashlib.sha256(crosswalk_path.read_bytes()).hexdigest(),
            table_review["csv_crosswalk_sha256"],
        )
        with crosswalk_path.open(encoding="utf-8", newline="") as stream:
            brain_crosswalk = list(csv.DictReader(stream))
        self.assertEqual(len(brain_crosswalk), table_review["source_workbook_rows"])
        self.assertEqual(len({row["Sample_ID"] for row in brain_crosswalk}), table_review["distinct_sample_id_labels"])
        self.assertEqual(len({row["Specimen"] for row in brain_crosswalk}), table_review["distinct_specimen_labels"])
        duplicates = {}
        for row in brain_crosswalk:
            duplicates.setdefault(row["Sample_ID"], []).append(row)
        duplicate_groups = {sample_id: rows for sample_id, rows in duplicates.items() if len(rows) > 1}
        self.assertEqual(set(duplicate_groups), {"10X109_1", "10X109_7"})
        self.assertTrue(all(len(rows) == 2 for rows in duplicate_groups.values()))

        matched_rows = [row for row in brain_crosswalk if row["ega_sample_accession"]]
        self.assertEqual(len(matched_rows), 396)
        self.assertEqual(
            sum(bool(row["ega_sample_accession"]) and row["Specimen"] != row["ega_subject_id"] for row in brain_crosswalk),
            0,
        )
        for term in ("f158", "16099", "coronal"):
            self.assertNotIn(term, crosswalk_path.read_text(encoding="utf-8").casefold())
        b2073 = [row for row in brain_crosswalk if row["Specimen"] == "BRC2073" and row["Dissected_region"] == "Dorsal midbrain"]
        self.assertEqual(len(b2073), 2)
        self.assertEqual({row["ega_sample_accession"] for row in b2073}, {"EGAN00002408476", "EGAN00002408477"})

    def test_matched_coronal_accession_is_reciprocally_identified_and_crosswalked(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        confirmation = source["coronal_section_accession_search"]["matched_accession_confirmation"]
        self.assertEqual(confirmation["arrayexpress_submitter_alias"], "E-MTAB-11911")
        self.assertEqual(confirmation["ena_primary_accession"], "PRJEB53919")
        self.assertEqual(confirmation["ena_secondary_accession"], "ERP138734")
        for declaration in confirmation["retrieval_snapshots"]:
            snapshot = ROOT / declaration["path"]
            self.assertEqual(snapshot.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), declaration["sha256"])

        project = ET.parse(ARTIFACTS / "PRJEB53919-ena-browser.xml").getroot().find(".//PROJECT")
        self.assertEqual(project.attrib["accession"], "PRJEB53919")
        self.assertEqual(project.attrib["alias"], "E-MTAB-11911")
        self.assertEqual(project.findtext("./IDENTIFIERS/SECONDARY_ID"), "ERP138734")
        project_description = project.findtext("DESCRIPTION", "")
        self.assertIn("sample ID: F158", project.findtext("TITLE", ""))
        self.assertIn("16099 for HDBR", project.findtext("TITLE", ""))
        self.assertIn("12 coronal", project_description)
        self.assertIn("A matched accession contains the yolk sac and yolk sac stalk", project_description)

        yolk_sac_api = json.loads(
            (ROOT / "artifacts/early-exchange-transition-2026-10-09/E-MTAB-11673-biostudies-api.json")
            .read_text(encoding="utf-8")
        )
        description = next(
            attribute["value"]
            for attribute in yolk_sac_api["section"]["attributes"]
            if attribute["name"] == "Description"
        )
        self.assertIn("This accession contains the yolk sac and yolk sac stalk", description)
        self.assertIn("A matched accession contains the coronal section data", description)

        crosswalk_path = ROOT / confirmation["public_sample_metadata"]["crosswalk_path"]
        self.assertEqual(crosswalk_path.stat().st_size, confirmation["public_sample_metadata"]["crosswalk_bytes"])
        self.assertEqual(
            hashlib.sha256(crosswalk_path.read_bytes()).hexdigest(),
            confirmation["public_sample_metadata"]["crosswalk_sha256"],
        )
        with crosswalk_path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 48)
        for field in ("experiment_accession", "ena_sample_accession", "biosample_accession", "run_accession"):
            self.assertEqual(len({row[field] for row in rows}), 48)
        self.assertEqual({row["study_accession"] for row in rows}, {"ERP138734"})
        self.assertEqual({row["individual"] for row in rows}, {"F158"})
        self.assertEqual({row["sex"] for row in rows}, {"female"})
        self.assertEqual({row["embryo_stage"] for row in rows}, {"Carnegie stage 17"})
        self.assertEqual(
            Counter(row["sampling_site"] for row in rows),
            Counter({f"section {name}": 4 for name in (
                "one", "two", "three", "four", "five", "six",
                "seven", "eight", "nine", "ten", "eleven", "twelve",
            )}),
        )
        self.assertEqual(confirmation["public_sample_metadata"]["section_label_count"], 12)
        self.assertEqual(confirmation["public_sample_metadata"]["sample_run_records_per_section"], 4)

        esummary = json.loads((ARTIFACTS / "PRJEB53919-sra-esummary.json").read_text(encoding="utf-8"))
        self.assertEqual(len(esummary["result"]["uids"]), 48)
        esearch = json.loads((ARTIFACTS / "PRJEB53919-sra-esearch.json").read_text(encoding="utf-8"))
        self.assertEqual(esearch["esearchresult"]["count"], "48")
        records_by_run = {}
        for uid in esummary["result"]["uids"]:
            record = esummary["result"][uid]
            experiment_xml = ET.fromstring(f"<root>{record['expxml']}</root>")
            run_xml = ET.fromstring(f"<root>{record['runs']}</root>")
            records_by_run[run_xml.find("Run").attrib["acc"]] = (
                experiment_xml.find("Study").attrib["acc"],
                experiment_xml.find("Experiment").attrib["acc"],
                experiment_xml.find("Sample").attrib["acc"],
                experiment_xml.findtext("Biosample", "").strip(),
            )

        for row in rows:
            self.assertEqual(
                records_by_run[row["run_accession"]],
                (
                    row["study_accession"],
                    row["experiment_accession"],
                    row["ena_sample_accession"],
                    row["biosample_accession"],
                ),
            )
            sample_snapshot = ROOT / row["snapshot_path"]
            self.assertEqual(sample_snapshot.stat().st_size, int(row["snapshot_bytes"]))
            self.assertEqual(hashlib.sha256(sample_snapshot.read_bytes()).hexdigest(), row["snapshot_sha256"])
            sample = ET.parse(sample_snapshot).getroot().find(".//SAMPLE")
            self.assertEqual(sample.attrib["accession"], row["biosample_accession"])
            self.assertEqual(sample.attrib["alias"], f"E-MTAB-11911:{row['sample_title']}")
            attributes = {
                attribute.findtext("TAG", "").casefold(): attribute.findtext("VALUE", "")
                for attribute in sample.findall(".//SAMPLE_ATTRIBUTE")
            }
            self.assertEqual(attributes["individual"], row["individual"])
            self.assertEqual(attributes["sampling site"], row["sampling_site"])
            self.assertEqual(attributes["embryo stage"], row["embryo_stage"])
            self.assertEqual(attributes["sex"], row["sex"])

    def test_public_file_index_separates_fastq_manifest_from_matrix_claim(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        screen = source["coronal_section_accession_search"]["matched_accession_confirmation"]["public_file_availability_screen"]
        self.assertEqual(screen["ena_read_run_file_report"]["row_count"], 48)
        self.assertEqual(screen["ena_read_run_file_report"]["submitted_file_count"], 144)
        self.assertEqual(screen["ena_read_run_file_report"]["files_per_run"], 3)
        self.assertEqual(screen["ena_read_run_file_report"]["file_roles"], {"I1": 48, "R1": 48, "R2": 48})
        self.assertEqual(screen["ena_analysis_file_report"]["returned_analysis_rows"], 0)
        self.assertIn("does not rule out", screen["ena_analysis_file_report"]["qualification"])
        self.assertFalse(source["coronal_section_accession_search"]["raw_fastq_or_processed_expression_downloaded"])

        for declaration in screen["snapshots"]:
            snapshot = ROOT / declaration["path"]
            self.assertEqual(snapshot.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), declaration["sha256"])

        project = ET.parse(ARTIFACTS / "PRJEB53919-ena-browser.xml").getroot().find(".//PROJECT")
        description = project.findtext("DESCRIPTION", "")
        self.assertIn("F158_[features...barcodes...matrix]", description)
        self.assertIn("all the 10x lanes in this accession combined", description)
        self.assertIn("CellRanger version 6.0.1", description)

        run_report = ARTIFACTS / "PRJEB53919-read_run-file-report.tsv"
        with run_report.open(encoding="utf-8", newline="") as stream:
            run_rows = list(csv.DictReader(stream, delimiter="\t"))
        self.assertEqual(len(run_rows), 48)
        self.assertEqual(len({row["run_accession"] for row in run_rows}), 48)

        manifest_path = ROOT / screen["fastq_manifest_path"]
        self.assertEqual(manifest_path.stat().st_size, screen["fastq_manifest_bytes"])
        self.assertEqual(hashlib.sha256(manifest_path.read_bytes()).hexdigest(), screen["fastq_manifest_sha256"])
        with manifest_path.open(encoding="utf-8", newline="") as stream:
            manifest = list(csv.DictReader(stream))
        self.assertEqual(len(manifest), 144)
        self.assertEqual(len({row["ftp_path"] for row in manifest}), 144)
        self.assertEqual(Counter(row["fastq_role"] for row in manifest), {"I1": 48, "R1": 48, "R2": 48})
        self.assertEqual(Counter(row["format"] for row in manifest), {"FASTQ": 144})
        self.assertEqual(Counter(row["sampling_site"] for row in manifest), {f"section {name}": 12 for name in (
            "one", "two", "three", "four", "five", "six",
            "seven", "eight", "nine", "ten", "eleven", "twelve",
        )})

        raw_by_run = {row["run_accession"]: row for row in run_rows}
        for row in manifest:
            raw = raw_by_run[row["run_accession"]]
            files = raw["submitted_ftp"].split(";")
            checksums = raw["submitted_md5"].split(";")
            sizes = raw["submitted_bytes"].split(";")
            formats = raw["submitted_format"].split(";")
            index = files.index(row["ftp_path"])
            self.assertEqual(row["md5"], checksums[index])
            self.assertEqual(row["bytes"], sizes[index])
            self.assertEqual(row["format"], formats[index])

        analysis_report = ARTIFACTS / "PRJEB53919-analysis-file-report.tsv"
        with analysis_report.open(encoding="utf-8", newline="") as stream:
            analysis_rows = list(csv.DictReader(stream, delimiter="\t"))
        self.assertEqual(analysis_rows, [])

    def test_hdca_preprint_crosschecks_the_accession_but_not_matrix_availability(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        preprint = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]
        self.assertEqual(preprint["source_type"], "bioRxiv preprint; not treated as peer-reviewed evidence")
        self.assertEqual(preprint["doi"], "10.64898/2026.03.30.714220")
        self.assertIn("E-MTAB-11911", preprint["cross_reference_result"])
        self.assertIn("currently private", preprint["preprint_data_availability_claim"])
        self.assertIn("E-MTAB-11504", preprint["current_repository_comparison"])
        self.assertIn("45 public SRA run records", preprint["current_repository_comparison"])
        self.assertIn("144 FASTQs", preprint["current_repository_comparison"])
        self.assertIn("matrix download links", preprint["current_repository_comparison"].lower())
        self.assertFalse(preprint["sequence_or_count_matrix_files_downloaded"])
        self.assertFalse(preprint["authentication_or_access_control_bypassed"])

        article = ROOT / preprint["saved_article_snapshot"]["path"]
        self.assertEqual(article.stat().st_size, preprint["saved_article_snapshot"]["bytes"])
        self.assertEqual(
            hashlib.sha256(article.read_bytes()).hexdigest(),
            preprint["saved_article_snapshot"]["sha256"],
        )
        article_text = article.read_text(encoding="utf-8", errors="replace").casefold()
        for phrase in ("e-mtab-11504", "e-mtab-11911", "currently private", "password protected", "count matrices"):
            self.assertIn(phrase, article_text)

        portal = ROOT / preprint["portal_route_check"]["saved_snapshot"]["path"]
        self.assertEqual(portal.stat().st_size, preprint["portal_route_check"]["saved_snapshot"]["bytes"])
        self.assertEqual(
            hashlib.sha256(portal.read_bytes()).hexdigest(),
            preprint["portal_route_check"]["saved_snapshot"]["sha256"],
        )
        self.assertEqual(preprint["portal_route_check"]["http_status"], 200)
        self.assertIn("app shell only", preprint["portal_route_check"]["response"])

        archive = preprint["public_archive_crosscheck"]
        f137 = archive["f137_public_project"]
        self.assertEqual(f137["preprint_accession"], "E-MTAB-11504")
        self.assertEqual(f137["ena_primary_accession"], "PRJEB51328")
        self.assertEqual(f137["ena_secondary_accession"], "ERP135952")
        self.assertEqual(f137["ncbi_sra_search"]["search_count"], 45)
        self.assertEqual(f137["ncbi_sra_search"]["summarized_record_count"], 45)
        self.assertTrue(f137["ncbi_sra_search"]["all_run_records_public"])
        for snapshot_key in ("project_xml_snapshot",):
            snapshot = f137[snapshot_key]
            path = ROOT / snapshot["path"]
            self.assertEqual(path.stat().st_size, snapshot["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), snapshot["sha256"])
        for snapshot_key in ("esearch_snapshot", "esummary_snapshot"):
            snapshot = f137["ncbi_sra_search"][snapshot_key]
            path = ROOT / snapshot["path"]
            self.assertEqual(path.stat().st_size, snapshot["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), snapshot["sha256"])
        summary = json.loads(
            (ROOT / f137["ncbi_sra_search"]["esummary_snapshot"]["path"]).read_text(encoding="utf-8")
        )
        uids = summary["result"]["uids"]
        self.assertEqual(len(uids), 45)
        self.assertTrue(
            all(
                '<Study acc="ERP135952"' in summary["result"][uid]["expxml"]
                and 'is_public="true"' in summary["result"][uid]["runs"]
                for uid in uids
            )
        )
        self.assertEqual(
            [row["http_status"] for row in archive["other_preprint_accession_sra_screen"]],
            [200, 429, 200],
        )
        biostudies = archive["biostudies_api_check"]
        self.assertEqual(biostudies["http_status"], 403)
        self.assertIn("Study not accessible", biostudies["response_body"])
        self.assertEqual(len(biostudies["accessions_checked"]), 6)
        probe = ROOT / biostudies["anonymous_access_probe_snapshot"]["path"]
        self.assertEqual(probe.stat().st_size, biostudies["anonymous_access_probe_snapshot"]["bytes"])
        self.assertEqual(
            hashlib.sha256(probe.read_bytes()).hexdigest(),
            biostudies["anonymous_access_probe_snapshot"]["sha256"],
        )
        probe_records = json.loads(probe.read_text(encoding="utf-8"))
        self.assertFalse(probe_records["authentication_used"])
        self.assertFalse(probe_records["data_files_requested"])
        self.assertEqual(len(probe_records["records"]), 6)
        self.assertTrue(
            all(
                row["http_status"] == 403 and "Study not accessible" in row["response_body"]
                for row in probe_records["records"]
            )
        )
        self.assertFalse(archive["sequence_or_count_matrix_files_downloaded"])

    def test_cycle190_analysis_file_probe_preserves_route_failure_without_absence_claim(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        archive = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]["public_archive_crosscheck"]
        spec = archive["ena_analysis_file_route_probe_cycle190"]
        receipt_path = ROOT / spec["receipt"]["path"]
        self.assertEqual(receipt_path.stat().st_size, spec["receipt"]["bytes"])
        self.assertEqual(hashlib.sha256(receipt_path.read_bytes()).hexdigest(), spec["receipt"]["sha256"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertIn("No conclusion", receipt["matrix_availability"])
        self.assertFalse(receipt["processed_files_downloaded"])
        self.assertIn("HTTP 500 on first request", receipt["requests"][0]["outcome"])
        f158 = receipt["requests"][-1]
        self.assertEqual(f158["http_status"], 200)
        self.assertEqual(f158["analysis_rows"], 0)
        for snapshot in receipt["requests"][2:4]:
            error = snapshot["error_response_snapshot"]
            error_path = ROOT / error["path"]
            self.assertEqual(error_path.stat().st_size, error["bytes"])
            self.assertEqual(hashlib.sha256(error_path.read_bytes()).hexdigest(), error["sha256"])
        self.assertEqual(
            receipt["requests"][2]["error_response_snapshot"]["sha256"],
            receipt["requests"][3]["error_response_snapshot"]["sha256"],
        )

    def test_f137_public_sra_crosswalk_maps_all_sections_without_replication_inference(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        spec = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]["public_archive_crosscheck"]["f137_public_project"]["sample_crosswalk"]
        crosswalk_path = ROOT / spec["path"]
        self.assertEqual(crosswalk_path.stat().st_size, spec["crosswalk_bytes"])
        self.assertEqual(hashlib.sha256(crosswalk_path.read_bytes()).hexdigest(), spec["crosswalk_sha256"])
        with crosswalk_path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 45)
        self.assertEqual(len({row["ena_sample_accession"] for row in rows}), 45)
        self.assertEqual(len({row["biosample_accession"] for row in rows}), 45)
        self.assertEqual(len({row["run_accession"] for row in rows}), 45)
        self.assertTrue(all(row["run_is_public"] == "true" for row in rows))
        self.assertEqual({row["individual"] for row in rows}, {"F137"})
        self.assertEqual({row["sex"] for row in rows}, {"female"})
        self.assertEqual({row["embryo_stage"] for row in rows}, {"carnegie stage 16"})
        section_counts = Counter(row["sampling_site"] for row in rows)
        self.assertEqual(section_counts, Counter(spec["section_sample_counts"]))
        self.assertEqual(set(section_counts), {f"section {name}" for name in (
            "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve",
        )})
        excluded_lane = [row for row in rows if row["sample_title"] == "WS_wEMB10202360"]
        self.assertEqual(len(excluded_lane), 1)
        self.assertEqual(excluded_lane[0]["sampling_site"], "section seven")
        self.assertEqual(excluded_lane[0]["run_is_public"], "true")
        for row in rows:
            snapshot = ROOT / row["snapshot_path"].replace("\\", "/")
            self.assertEqual(snapshot.stat().st_size, int(row["snapshot_bytes"]))
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), row["snapshot_sha256"])

    def test_f137_runinfo_is_distinct_from_fastq_metadata_and_retains_earlier_probe(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        f137 = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]["public_archive_crosscheck"]["f137_public_project"]
        spec = f137["runinfo_manifest"]
        for snapshot_spec in (spec["snapshot"], spec["joined_manifest"]):
            path = ROOT / snapshot_spec["path"]
            self.assertEqual(path.stat().st_size, snapshot_spec["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), snapshot_spec["sha256"])
        with (ROOT / spec["joined_manifest"]["path"]).open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 45)
        self.assertEqual(len({row["run_accession"] for row in rows}), 45)
        self.assertTrue(all(row["consent"] == "public" for row in rows))
        self.assertTrue(all(row["download_path"].startswith("https://sra-download") for row in rows))
        self.assertNotIn("fastq_ftp", rows[0])
        excluded = [row for row in rows if row["run_accession"] == "ERR9034751"]
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0]["sampling_site"], "section seven")
        self.assertEqual(int(excluded[0]["spots"]), 133294)
        self.assertEqual(int(excluded[0]["bases"]), 16928338)
        self.assertEqual(spec["excluded_lane_run"]["median_spots_in_other_44_runs"], 513393835)
        self.assertEqual(spec["ena_fastq_file_report_probe"]["timeouts_seconds"], [25, 30])
        self.assertFalse(spec["ena_fastq_file_report_probe"]["fastq_manifest_created"])

    def test_f137_submitted_fastq_manifest_matches_runs_and_section_counts(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        archive = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]["public_archive_crosscheck"]
        f137 = archive["f137_public_project"]["fastq_manifest"]
        for snapshot_spec in (f137["snapshot"], f137["joined_manifest"]):
            path = ROOT / snapshot_spec["path"]
            self.assertEqual(path.stat().st_size, snapshot_spec["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), snapshot_spec["sha256"])
        self.assertEqual(f137["snapshot"]["http_status"], 200)
        self.assertEqual(f137["snapshot"]["run_rows"], 45)
        self.assertTrue(f137["joined_manifest"]["runs_match_sample_crosswalk"])

        with (ROOT / f137["joined_manifest"]["path"]).open(encoding="utf-8", newline="") as stream:
            files = list(csv.DictReader(stream))
        with (ROOT / "config/source_inventories/goh_2023_emtab11504_f137_sample_crosswalk.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            samples = {row["run_accession"]: row for row in csv.DictReader(stream)}
        self.assertEqual(len(files), 135)
        self.assertEqual(len({row["run_accession"] for row in files}), 45)
        self.assertEqual(Counter(row["fastq_role"] for row in files), Counter({"I1": 45, "R1": 45, "R2": 45}))
        for row in files:
            self.assertIn(row["run_accession"], samples)
            self.assertEqual(row["sampling_site"], samples[row["run_accession"]]["sampling_site"])
            self.assertEqual(row["biosample_accession"], samples[row["run_accession"]]["biosample_accession"])
        with (ROOT / archive["technical_run_coverage_comparison"]["section_comparison"]["path"]).open(
            encoding="utf-8", newline=""
        ) as stream:
            sections = {row["section"]: row for row in csv.DictReader(stream)}
        self.assertEqual(len(sections), 12)
        for section, summary in sections.items():
            section_files = [row for row in files if row["sampling_site"] == section]
            self.assertEqual(int(summary["f137_ena_fastq_file_rows"]), len(section_files))
            self.assertEqual(int(summary["f137_ena_fastq_bytes"]), sum(int(row["bytes"]) for row in section_files))
        self.assertFalse(f137["content_downloaded"])

    def test_f158_runinfo_zero_is_flagged_against_nonempty_ena_fastq_files(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        preprint = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]
        archive = preprint["public_archive_crosscheck"]
        spec = archive["technical_run_coverage_comparison"]
        for snapshot_spec in (spec["f158_runinfo_snapshot"], spec["f158_runinfo_manifest"], spec["section_comparison"]):
            path = ROOT / snapshot_spec["path"]
            self.assertEqual(path.stat().st_size, snapshot_spec["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), snapshot_spec["sha256"])
        with (ROOT / spec["f158_runinfo_manifest"]["path"]).open(encoding="utf-8", newline="") as stream:
            f158_runs = list(csv.DictReader(stream))
        self.assertEqual(len(f158_runs), 48)
        self.assertEqual(len({row["run_accession"] for row in f158_runs}), 48)
        self.assertTrue(all(row["consent"] == "public" for row in f158_runs))
        zero_run = [row for row in f158_runs if row["run_accession"] == "ERR9882663"]
        self.assertEqual(len(zero_run), 1)
        self.assertEqual(zero_run[0]["sampling_site"], "section one")
        self.assertEqual(int(zero_run[0]["spots"]), 0)
        self.assertEqual(int(zero_run[0]["bases"]), 0)
        self.assertEqual(zero_run[0]["download_path"], "")

        with (ROOT / "config/source_inventories/goh_2023_emtab11911_coronal_fastq_manifest.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            fastq_rows = list(csv.DictReader(stream))
        run_files = [row for row in fastq_rows if row["run_accession"] == "ERR9882663"]
        self.assertEqual(len(run_files), 3)
        self.assertEqual({row["fastq_role"] for row in run_files}, {"I1", "R1", "R2"})
        self.assertEqual(sum(int(row["bytes"]) for row in run_files), 181630756773)
        reconciliation = spec["f158_zero_runinfo_stats_with_ena_files"]
        self.assertEqual(reconciliation["ena_fastq_file_count"], 3)
        self.assertEqual(reconciliation["ena_fastq_bytes_total"], 181630756773)
        receipt_spec = reconciliation["reconciliation_snapshot"]
        receipt_path = ROOT / receipt_spec["path"]
        self.assertEqual(receipt_path.stat().st_size, receipt_spec["bytes"])
        self.assertEqual(hashlib.sha256(receipt_path.read_bytes()).hexdigest(), receipt_spec["sha256"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertTrue(receipt["cross_record_file_match"])
        self.assertEqual(receipt["run_summary_comparison"]["ncbi_runinfo"]["spots"], 0)
        self.assertEqual(receipt["run_summary_comparison"]["ena_browser_xml"]["ena_spot_count"], "0")
        self.assertEqual(len(receipt["ena_submitted_files"]), 3)
        self.assertTrue(all(row["head_status"] == 200 for row in receipt["ena_submitted_files"]))
        self.assertTrue(all(row["head_content_length_matches_declaration"] for row in receipt["ena_submitted_files"]))
        self.assertFalse(receipt["fastq_contents_downloaded"])
        self.assertFalse(receipt["checksums_recomputed"])
        for snapshot in receipt["metadata_snapshots"].values():
            path = ROOT / snapshot["snapshot_path"]
            self.assertEqual(path.stat().st_size, snapshot["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), snapshot["sha256"])
        self.assertIn("metadata level", receipt["qualification"])

        with (ROOT / spec["section_comparison"]["path"]).open(encoding="utf-8", newline="") as stream:
            sections = {row["section"]: row for row in csv.DictReader(stream)}
        self.assertEqual(len(sections), 12)
        self.assertEqual(sections["section one"]["f137_public_sra_run_records"], "1")
        self.assertEqual(sections["section one"]["f158_public_sra_run_records"], "4")
        self.assertEqual(sections["section one"]["f158_runinfo_zero_or_blank_stats_count"], "1")
        self.assertEqual(sections["section one"]["f158_ena_fastq_file_rows"], "12")
        self.assertEqual(sections["section one"]["f137_ena_fastq_file_rows"], "3")

    def test_joint_f137_f158_run_file_crosscheck_finds_only_one_zero_stat_run(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        archive = source["coronal_section_accession_search"]["contemporary_atlas_preprint_crosscheck"]["public_archive_crosscheck"]
        spec = archive["technical_run_coverage_comparison"]["run_file_crosscheck"]
        path = ROOT / spec["path"]
        self.assertEqual(path.stat().st_size, spec["bytes"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), spec["sha256"])
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 93)
        self.assertEqual(Counter(row["individual"] for row in rows), Counter({"F137": 45, "F158": 48}))
        self.assertEqual(Counter(row["ena_fastq_file_count"] for row in rows), Counter({"3": 93}))
        self.assertTrue(all(row["ena_fastq_role_set_complete"] == "true" for row in rows))
        self.assertTrue(all(row["ena_fastq_declared_nonzero_size_file_count"] == "3" for row in rows))
        self.assertTrue(all(row["ena_fastq_declared_md5_count"] == "3" for row in rows))
        zero_rows = [row for row in rows if row["runinfo_zero_or_blank_spots_or_bases"] == "true"]
        self.assertEqual([row["run_accession"] for row in zero_rows], ["ERR9882663"])
        self.assertEqual(zero_rows[0]["individual"], "F158")
        self.assertEqual(zero_rows[0]["section"], "section one")
        self.assertEqual(zero_rows[0]["ena_fastq_declared_bytes_total"], "181630756773")
        self.assertEqual(zero_rows[0]["http_head_checked_file_count"], "3")


if __name__ == "__main__":
    unittest.main()
