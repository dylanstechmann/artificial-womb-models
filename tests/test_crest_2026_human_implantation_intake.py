import csv
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/early-interface-model-2026-10-11"
INVENTORY = ROOT / "config/source_inventories/crest_2026_human_implantation.json"
CROSSWALK = ROOT / "config/source_inventories/crest_2026_emtab13629_sample_crosswalk.csv"


def read_tsv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class CrestHumanImplantationIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.sdrf = read_tsv(ARTIFACTS / "E-MTAB-13629.sdrf.txt")
        cls.ena = read_tsv(ARTIFACTS / "ERP156726-read-run.tsv")
        cls.crosswalk = read_csv(CROSSWALK)
        cls.fastq_manifest = read_csv(
            ARTIFACTS / "emtab13629_fastq_manifest_head_checked_cycle191.csv"
        )

    def test_sample_and_run_crosswalk_keeps_units_distinct(self):
        self.assertEqual(len(self.crosswalk), 7)
        self.assertEqual(
            Counter(row["scaffold_group_source_label"] for row in self.crosswalk),
            {"EEC1": 3, "EEC5+EEC4": 4},
        )
        self.assertEqual(sum(int(row["ena_run_count"]) for row in self.crosswalk), 15)
        self.assertEqual(sum(int(row["sdrf_file_rows"]) for row in self.crosswalk), 60)
        self.assertEqual(
            sum(int(row["head_200_fastq_count"]) for row in self.crosswalk), 60
        )
        self.assertTrue(
            all(
                row["independent_embryo_unit_resolution"].startswith("unresolved")
                for row in self.crosswalk
            )
        )

    def test_sdrf_fastq_manifest_is_metadata_only_and_complete(self):
        self.assertEqual(len(self.sdrf), 60)
        self.assertEqual(len({row["Comment[ENA_SAMPLE]"] for row in self.sdrf}), 7)
        self.assertEqual(len({row["Comment[ENA_RUN]"] for row in self.sdrf}), 15)
        self.assertEqual(len(self.fastq_manifest), 60)
        self.assertEqual(
            {row["fastq_uri"] for row in self.fastq_manifest},
            {row["Comment[FASTQ_URI]"] for row in self.sdrf},
        )
        self.assertTrue(all(row["status_code"] == "200" for row in self.fastq_manifest))
        self.assertTrue(
            all(int(row["content_length"]) > 0 for row in self.fastq_manifest)
        )
        self.assertTrue(
            all(row["file_content_downloaded"] == "false" for row in self.fastq_manifest)
        )
        self.assertTrue(
            all(row["file_checksum_recomputed"] == "false" for row in self.fastq_manifest)
        )
        per_run = defaultdict(Counter)
        for row in self.sdrf:
            per_run[row["Comment[ENA_RUN]"]][row["Comment[READ_INDEX]"]] += 1
        self.assertEqual(len(per_run), 15)
        self.assertTrue(
            all(
                counts == Counter({"index1": 1, "index2": 1, "read1": 1, "read2": 1})
                for counts in per_run.values()
            )
        )

    def test_blank_ena_file_fields_do_not_override_sdrf_routes(self):
        self.assertEqual(len(self.ena), 15)
        self.assertEqual(
            {row["run_accession"] for row in self.ena},
            {row["Comment[ENA_RUN]"] for row in self.sdrf},
        )
        for field in ("fastq_ftp", "fastq_md5", "fastq_bytes"):
            self.assertTrue(all(not row[field] for row in self.ena))
        self.assertEqual(
            self.inventory["sample_intake"]["ena_read_run_report"]["fastq_ftp_nonblank_rows"],
            0,
        )
        self.assertEqual(
            self.inventory["sample_intake"]["metadata_only_fastq_head_probe"]["status"],
            "60 of 60 returned HTTP 200",
        )

    def test_correct_zenodo_records_and_licenses_are_pinned(self):
        processed = json.loads(
            (ARTIFACTS / "zenodo-processed-zenodo.json").read_text(encoding="utf-8")
        )
        code = json.loads(
            (ARTIFACTS / "zenodo-code-zenodo.json").read_text(encoding="utf-8")
        )
        self.assertEqual(processed["doi"], "10.5281/zenodo.17930156")
        self.assertEqual(processed["metadata"]["license"]["id"], "mit-license")
        self.assertEqual(len(processed["files"]), 4)
        self.assertEqual(code["doi"], "10.5281/zenodo.17955321")
        self.assertEqual(code["metadata"]["license"]["id"], "cc-by-4.0")
        self.assertEqual(code["metadata"]["version"], "v1.0")

    def test_inventory_preserves_scRNA_site_mapping_gap_and_no_promotion(self):
        intake = self.inventory
        self.assertEqual(intake["reported_scope"]["whole_paper_human_embryo_count"], 248)
        self.assertEqual(intake["reported_scope"]["reported_scRNA_site_count"], 17)
        self.assertEqual(intake["sample_intake"]["ena_sample_group_count"], 7)
        self.assertIn(
            "mapping is not present",
            intake["reported_scope"]["scRNA_site_count_qualification"],
        )
        self.assertEqual(intake["observation_intake"]["observation_records_promoted"], 0)
        self.assertFalse(intake["feasibility_boundary"]["authors_contacted"])

    def test_pinned_source_artifacts_match_manifest_hashes(self):
        source = json.loads((ARTIFACTS / "SOURCE.json").read_text(encoding="utf-8"))
        for entry in source["files"]:
            path = ROOT / entry["path"]
            content = path.read_bytes()
            self.assertEqual(len(content), entry["bytes"], entry["path"])
            self.assertEqual(
                hashlib.sha256(content).hexdigest(), entry["sha256"], entry["path"]
            )

    def test_retained_biostudies_extract_omits_protocol_payloads(self):
        summary_path = ARTIFACTS / "E-MTAB-13629-biostudies-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertIn("protocol text", summary["record_type"])
        self.assertNotIn('"Protocols"', summary_path.read_text(encoding="utf-8"))
        self.assertFalse((ARTIFACTS / "E-MTAB-13629-biostudies-api.json").exists())
        self.assertFalse((ARTIFACTS / "E-MTAB-13629.idf.txt").exists())
        self.assertFalse((ARTIFACTS / "Modeling-human-embryo-implantation.pdf").exists())
        source = json.loads((ARTIFACTS / "SOURCE.json").read_text(encoding="utf-8"))
        self.assertFalse(source["reviewed_source_pdf"]["retained_in_repository_artifacts"])

    def test_static_code_review_preserves_cell_level_and_unit_linkage_limits(self):
        receipt_path = ARTIFACTS / "crest-code-release-analysis-cycle192.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        review = self.inventory["code_release_static_review"]
        self.assertEqual(receipt["inspected_release_files"]["cell_metadata_csv"]["row_count"], 15673)
        self.assertEqual(review["distinct_source_batch_labels"], 6)
        self.assertFalse(review["explicit_ena_sample_or_implantation_site_id_in_cell_csv"])
        self.assertEqual(
            receipt["inspected_release_files"]["cell_metadata_csv"]["selected_column_summaries"]["nCount_RNA"]["constant_value"],
            "SeuratProject",
        )
        self.assertFalse(self.inventory["processed_data"]["downloaded"])
        self.assertFalse(self.inventory["code_release"]["scripts_executed"])
        self.assertTrue(self.inventory["code_release"]["archive_retrieved_in_memory"])
        self.assertFalse(self.inventory["code_release"]["archive_persisted_locally"])
        self.assertIn("no per-sample", review["figureS5G_test"])

    def test_publisher_supplement_negative_mapping_screen_is_pinned(self):
        receipt_path = ARTIFACTS / "crest-supplement-screen-cycle193.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        screen = self.inventory["supplement_screen"]
        self.assertEqual(receipt["source"]["pages"], 2)
        self.assertEqual(
            receipt["source"]["publisher_asset_uri"],
            "https://ars.els-cdn.com/content/image/1-s2.0-S0092867425012322-mmc1.pdf",
        )
        self.assertFalse(receipt["result"]["site_to_sample_mapping_found"])
        self.assertFalse(receipt["result"]["sample_or_donor_level_values_transcribed"])
        self.assertFalse(receipt["result"]["protocol_detail_persisted"])
        self.assertEqual(receipt["result"]["biological_observations_promoted"], 0)
        self.assertFalse(screen["site_to_sample_mapping_found"])
        self.assertEqual(screen["observation_promotion"], 0)
        self.assertTrue(
            (ROOT / receipt["source"]["local_review_copy"]).is_file()
        )


if __name__ == "__main__":
    unittest.main()
