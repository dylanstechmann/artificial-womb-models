import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/gse263528-maternal-interface-2026-10-11"
INVENTORY = ROOT / "config/source_inventories/gse263528_human_embryo_endometrial_assembloid.json"


class GSE263528MetadataIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.receipt = json.loads((ARTIFACTS / "gse263528-metadata-screen-cycle196.json").read_text(encoding="utf-8"))
        cls.metadata = json.loads((ARTIFACTS / "GSE263528_sample_metadata.json").read_text(encoding="utf-8"))
        with (ARTIFACTS / "GSE263528_sample_crosswalk.csv").open(encoding="utf-8", newline="") as handle:
            cls.crosswalk = list(csv.DictReader(handle))

    def test_sample_accessions_and_sra_experiments_are_unique_repository_records(self):
        samples = self.metadata["samples"]
        self.assertEqual(len(samples), 11)
        self.assertEqual(len({row["sample_accession"] for row in samples}), 11)
        self.assertEqual(len({row["linked_sra_experiment"] for row in samples}), 11)
        self.assertEqual(len(self.crosswalk), 11)
        self.assertEqual(self.inventory["repository_sample_map"]["submission_date_counts"], {"2024-04-09": 3, "2026-05-14": 8})
        self.assertIn("count is not an embryo", self.inventory["repository_sample_map"]["unit_qualification"])

    def test_day_labels_are_not_recast_as_developmental_age(self):
        labels = " ".join(row["title"] for row in self.metadata["samples"])
        self.assertIn("day2", labels)
        self.assertIn("day4", labels)
        self.assertIn("preserved as submitted", self.inventory["repository_sample_map"]["day_labels_qualification"])

    def test_song_author_initial_collision_is_resolved_without_data_join(self):
        linkage = self.inventory["publication_linkage"]["song_2026_crosscheck"]
        self.assertEqual(linkage["geo_contributor_with_initial_collision"], "Xinbao Zhang")
        self.assertEqual(linkage["song_pubmed_author"], "Xinwen Zhang")
        self.assertFalse(linkage["exact_full_name_match"])
        self.assertFalse(linkage["direct_sample_to_article_crosswalk_found"])
        self.assertFalse(self.inventory["publication_linkage"]["pubmed_relation_in_geo_series"])

    def test_screen_does_not_promote_expression_or_developmental_observations(self):
        review = self.inventory["data_review"]
        self.assertFalse(review["expression_matrices_downloaded"])
        self.assertFalse(review["sequencing_reads_downloaded"])
        self.assertEqual(review["observation_records_promoted"], 0)
        self.assertIn("complete gestation", self.inventory["feasibility_boundary"]["does_not_establish"])

    def test_sra_suppression_is_recorded_as_route_status_not_data_absence(self):
        with (ARTIFACTS / "GSE263528_sra_experiment_status.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 11)
        self.assertEqual({row["sra_status"] for row in rows}, {"suppressed"})
        self.assertTrue(all(row["run_list_length"] == "0" for row in rows))
        qualification = self.inventory["repository_sample_map"]["sra_status_qualification"]
        self.assertIn("does not establish that sequence data do not exist", qualification)
        self.assertFalse(self.inventory["data_review"]["sequencing_reads_downloaded"])

    def test_geo_matrix_routes_are_head_reachable_without_content_review(self):
        with (ARTIFACTS / "GSE263528_geo_matrix_head_status.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        receipt = json.loads((ARTIFACTS / "gse263528-geo-matrix-head-screen-cycle199.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 11)
        self.assertEqual({row["head_status"] for row in rows}, {"200"})
        self.assertTrue(all(int(row["content_length"]) > 0 for row in rows))
        self.assertFalse(receipt["interpretation"]["matrix_contents_reviewed"])
        self.assertFalse(receipt["interpretation"]["matrix_checksums_verified"])
        self.assertEqual(receipt["interpretation"]["observation_records_promoted"], 0)

    def test_geo_sidecars_have_integrity_receipt_without_biological_promotion(self):
        with (ARTIFACTS / "GSE263528_geo_sidecar_integrity_cycle200.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        receipt = json.loads((ARTIFACTS / "gse263528-geo-sidecar-integrity-screen-cycle200.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(len(rows), 22)
        self.assertEqual({row["gsm"] for row in rows}, {row["sample_accession"] for row in self.metadata["samples"]})
        self.assertEqual({row["kind"] for row in rows}, {"barcodes", "features"})
        self.assertTrue(all(row["http_status"] == "200" for row in rows))
        self.assertTrue(all(row["gzip_read_to_eof"] == "true" for row in rows))
        self.assertTrue(all(row["compressed_bytes"] == row["declared_content_length"] for row in rows))
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
        self.assertEqual(receipt["sidecars_checked"], 22)
        self.assertTrue(receipt["all_checks_passed"])
        self.assertFalse(receipt["raw_sidecars_retained_in_repository"])
        self.assertEqual(receipt["umi_matrix_bodies_downloaded"], 0)
        self.assertFalse(receipt["biological_outcomes_transcribed"])

    def test_geo_sidecar_keys_match_pinned_hashes_and_matrix_dimensions(self):
        with (ARTIFACTS / "GSE263528_geo_sidecar_key_validation_cycle264.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        with (ARTIFACTS / "GSE263528_geo_sidecar_integrity_cycle200.csv").open(encoding="utf-8-sig", newline="") as handle:
            original = {(row["gsm"], row["kind"]): row for row in csv.DictReader(handle)}
        with (ARTIFACTS / "GSE263528_geo_matrix_prefix_dimensions_cycle201.csv").open(encoding="utf-8-sig", newline="") as handle:
            dimensions = {row["gsm"]: row for row in csv.DictReader(handle)}
        receipt = json.loads((ARTIFACTS / "gse263528-geo-sidecar-key-validation-cycle264.json").read_text(encoding="utf-8"))

        self.assertEqual(len(rows), 22)
        self.assertEqual({row["kind"] for row in rows}, {"barcodes", "features"})
        self.assertEqual({row["gsm"] for row in rows}, set(dimensions))
        for row in rows:
            pinned = original[(row["gsm"], row["kind"])]
            expected_dimension = dimensions[row["gsm"]]["matrix_columns" if row["kind"] == "barcodes" else "matrix_rows"]
            self.assertEqual(row["http_status"], "200")
            self.assertEqual(row["compressed_bytes_read"], row["declared_compressed_bytes"])
            self.assertEqual(row["compressed_bytes_read"], pinned["declared_content_length"])
            self.assertEqual(row["compressed_sha256"], pinned["sha256"])
            self.assertEqual(row["sha256_matches_cycle200"].lower(), "true")
            self.assertEqual(row["gzip_crc_and_eof_valid"].lower(), "true")
            self.assertEqual(row["line_count"], pinned["line_count"])
            self.assertEqual(row["line_count"], expected_dimension)
            self.assertEqual(row["line_count_matches_matrix_dimension"].lower(), "true")
            expected_fields = "1" if row["kind"] == "barcodes" else "3"
            self.assertEqual(json.loads(row["field_count_histogram"]), {expected_fields: int(row["line_count"])})
            self.assertEqual(row["blank_rows"], "0")
            self.assertEqual(row["wrong_field_count_rows"], "0")
            self.assertEqual(row["empty_key_rows"], "0")
            self.assertEqual(row["empty_nonkey_field_rows"], "0")
            self.assertEqual(row["duplicate_key_rows"], "0")
            self.assertEqual(row["unique_key_count"], row["line_count"])
            self.assertEqual(row["all_checks_pass"].lower(), "true")
            self.assertEqual(row["identifiers_retained"].lower(), "false")

        self.assertEqual(receipt["sidecars_checked"], 22)
        self.assertEqual(receipt["total_rows_checked"], 2663026)
        self.assertEqual(receipt["duplicate_key_rows"], 0)
        self.assertTrue(receipt["all_checks_pass"])
        self.assertFalse(receipt["identifiers_retained"])
        self.assertFalse(receipt["raw_sidecars_retained"])
        counts = self.inventory["repository_sample_map"]["geo_sidecar_key_validation_counts_at_2026-10-11"]
        self.assertEqual(counts["sidecars_checked"], 22)
        self.assertEqual(counts["duplicate_key_rows"], 0)
        self.assertFalse(counts["raw_identifiers_retained"])

    def test_geo_matrix_range_prefix_dimensions_match_sidecars_with_strict_byte_cap(self):
        with (ARTIFACTS / "GSE263528_geo_matrix_prefix_dimensions_cycle201.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        receipt = json.loads((ARTIFACTS / "gse263528-geo-matrix-prefix-screen-cycle201.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(row["response_status"] == "206" for row in rows))
        self.assertTrue(all(int(row["prefix_bytes_read"]) <= 65536 for row in rows))
        self.assertTrue(all(row["matrix_market_header_valid"] == "True" for row in rows))
        self.assertTrue(all(row["sidecar_shape_match"] == "True" for row in rows))
        self.assertTrue(all(row["header_total_matches_head"] == "True" for row in rows))
        self.assertTrue(all(len(row["prefix_sha256"]) == 64 for row in rows))
        self.assertEqual(receipt["range_bytes_per_matrix_max"], 65536)
        self.assertEqual(receipt["http_206_with_bounded_prefix"], 11)
        self.assertEqual(receipt["matrix_headers_parsed"], 11)
        self.assertEqual(receipt["sidecar_shape_matches"], 11)
        self.assertEqual(receipt["expression_matrix_bodies_downloaded"], 0)
        self.assertEqual(receipt["matrix_expression_values_read"], 0)
        self.assertFalse(receipt["raw_prefixes_retained"])
        self.assertEqual(receipt["observation_records_promoted"], 0)

    def test_geo_matrix_full_stream_integrity_matches_head_and_prefix_crosswalks(self):
        with (ARTIFACTS / "GSE263528_geo_matrix_full_integrity_cycle260.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        with (ARTIFACTS / "GSE263528_geo_matrix_head_status.csv").open(encoding="utf-8-sig", newline="") as handle:
            heads = {row["geo_sample_accession"]: row for row in csv.DictReader(handle)}
        with (ARTIFACTS / "GSE263528_geo_matrix_prefix_dimensions_cycle201.csv").open(encoding="utf-8-sig", newline="") as handle:
            prefixes = {row["gsm"]: row for row in csv.DictReader(handle)}
        receipt = json.loads((ARTIFACTS / "gse263528-geo-matrix-full-integrity-screen-cycle260.json").read_text(encoding="utf-8"))

        self.assertEqual(len(rows), 11)
        self.assertEqual({row["geo_sample_accession"] for row in rows}, set(heads))
        self.assertEqual({row["geo_sample_accession"] for row in rows}, set(prefixes))
        for row in rows:
            gsm = row["geo_sample_accession"]
            self.assertEqual(row["http_status"], "200")
            self.assertEqual(row["listed_matrix_uri"], heads[gsm]["listed_matrix_uri"])
            self.assertEqual(row["head_content_length"], heads[gsm]["content_length"])
            self.assertEqual(row["compressed_bytes_read"], heads[gsm]["content_length"])
            self.assertEqual(row["gzip_crc_and_eof_valid"].lower(), "true")
            self.assertEqual(row["matrix_rows"], prefixes[gsm]["matrix_rows"])
            self.assertEqual(row["matrix_columns"], prefixes[gsm]["matrix_columns"])
            self.assertEqual(row["header_nonzero_entries"], prefixes[gsm]["matrix_nonzero_entries"])
            self.assertEqual(row["actual_body_lines"], row["header_nonzero_entries"])
            self.assertEqual(row["nonzero_count_matches"].lower(), "true")
            self.assertEqual(row["dimensions_match_prefix"].lower(), "true")
            self.assertEqual(row["first_and_last_coordinates_in_bounds"].lower(), "true")
            self.assertEqual(row["expression_values_retained"].lower(), "false")
            self.assertEqual(len(row["compressed_sha256"]), 64)

        self.assertEqual(receipt["matrix_routes_requested"], 11)
        self.assertEqual(receipt["compressed_bytes_streamed"], 1171938176)
        self.assertEqual(receipt["decompressed_bytes_streamed"], 4135469512)
        self.assertEqual(receipt["nonzero_entry_lines_counted"], 314202222)
        self.assertEqual(receipt["coordinate_records_exhaustively_parsed"], 0)
        self.assertFalse(receipt["expression_values_analyzed"])
        self.assertFalse(receipt["expression_values_retained"])
        self.assertEqual(receipt["observation_records_promoted"], 0)
        self.assertEqual(self.inventory["data_review"]["matrix_bodies_streamed"], 11)
        self.assertEqual(self.inventory["data_review"]["matrix_files_retained"], 0)

    def test_geo_matrix_triplet_syntax_checks_all_records_without_value_summaries(self):
        with (ARTIFACTS / "GSE263528_geo_matrix_triplet_syntax_cycle262.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        with (ARTIFACTS / "GSE263528_geo_matrix_full_integrity_cycle260.csv").open(encoding="utf-8", newline="") as handle:
            full_integrity = {row["geo_sample_accession"]: row for row in csv.DictReader(handle)}
        receipt = json.loads((ARTIFACTS / "gse263528-geo-matrix-triplet-syntax-screen-cycle262.json").read_text(encoding="utf-8"))
        pilot = json.loads((ARTIFACTS / "gse263528-geo-matrix-triplet-syntax-pilot-cycle261.json").read_text(encoding="utf-8"))

        self.assertEqual(len(rows), 11)
        self.assertEqual({row["geo_sample_accession"] for row in rows}, set(full_integrity))
        for row in rows:
            gsm = row["geo_sample_accession"]
            expected = full_integrity[gsm]
            self.assertEqual(row["compressed_sha256"], expected["compressed_sha256"])
            self.assertEqual(row["compressed_sha256_matches_cycle260"].lower(), "true")
            self.assertEqual(row["gzip_crc_and_eof_valid"].lower(), "true")
            self.assertEqual(row["matrix_market_header"], "%%MatrixMarket matrix coordinate integer general")
            self.assertEqual(row["matrix_rows"], row["expected_rows"])
            self.assertEqual(row["matrix_columns"], row["expected_columns"])
            self.assertEqual(row["header_nonzero_entries"], row["expected_nonzero_entries"])
            for field in ("nonblank_body_lines", "triplets_with_three_fields", "integer_triplets", "coordinates_in_bounds", "positive_integer_values"):
                self.assertEqual(row[field], row["expected_nonzero_entries"], f"{gsm}: {field}")
            self.assertEqual(row["invalid_lines"], "0")
            self.assertEqual(row["all_triplet_syntax_and_domain_checks_pass"].lower(), "true")
            self.assertEqual(row["expression_values_retained"].lower(), "false")
            self.assertEqual(row["expression_value_summaries_computed"].lower(), "false")

        self.assertEqual(sum(int(row["integer_triplets"]) for row in rows), 314202222)
        self.assertEqual(receipt["triplets_checked"], 314202222)
        self.assertEqual(receipt["invalid_records"], 0)
        self.assertTrue(receipt["all_matrix_checks_pass"])
        self.assertFalse(receipt["count_values_retained"])
        self.assertFalse(receipt["expression_value_summaries_computed"])
        self.assertTrue(pilot["all_checks_pass"])
        self.assertEqual(pilot["triplets_checked"], 16843623)
        self.assertFalse(pilot["count_values_retained"])
        review = self.inventory["data_review"]
        self.assertEqual(review["matrix_triplet_records_syntax_checked"], 314202222)
        self.assertEqual(review["matrix_triplet_invalid_records"], 0)
        self.assertFalse(review["matrix_expression_value_summaries_computed"])

    def test_europepmc_publication_check_stays_within_indexed_metadata(self):
        receipt = json.loads((ARTIFACTS / "europepmc-publication-linkage-screen-cycle202.json").read_text(encoding="utf-8"))
        queries = {query["label"]: query for query in receipt["queries"]}
        self.assertEqual(set(queries), {"gse_accession", "gse_exact_title", "song_doi", "song_pmid"})
        self.assertEqual(queries["gse_accession"]["hit_count"], 0)
        self.assertEqual(queries["gse_exact_title"]["hit_count"], 0)
        self.assertEqual(queries["song_doi"]["hit_count"], 1)
        song = queries["song_doi"]["records"][0]
        self.assertEqual(song["pmid"], "41443195")
        self.assertIsNone(song["pmcid"])
        self.assertEqual(song["inEPMC"], "N")
        self.assertEqual(song["inPMC"], "N")
        self.assertEqual(song["hasSuppl"], "N")
        self.assertFalse(receipt["interpretation"]["article_data_availability_statement_reviewed"])
        self.assertFalse(receipt["interpretation"]["gse_to_song_linkage_established"])
        self.assertEqual(receipt["interpretation"]["observations_promoted"], 0)

    def test_source_manifest_hashes_match_metadata_artifacts(self):
        source = json.loads((ARTIFACTS / "SOURCE.json").read_text(encoding="utf-8"))
        for entry in source["files"]:
            path = ROOT / entry["path"]
            content = path.read_bytes()
            self.assertEqual(len(content), entry["bytes"], entry["path"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), entry["sha256"], entry["path"])


if __name__ == "__main__":
    unittest.main()
