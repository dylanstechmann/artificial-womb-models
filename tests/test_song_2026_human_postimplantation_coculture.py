import hashlib
import json
import unittest
import csv
import tempfile
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/song_2026_human_postimplantation_coculture.json"
RECEIPT = ROOT / "artifacts/postimplantation-coculture-2026-10-11/song-postimplantation-source-route-screen-cycle195.json"


class SongPostimplantationCocultureIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_reported_stage_endpoint_is_capped_at_day_14(self):
        scope = self.inventory["reported_scope"]
        self.assertEqual(scope["reported_embryo_endpoint"], "up to day 14 post-fertilization")
        self.assertFalse(scope["later_developmental_interval_reported"])
        self.assertIn("complete gestation", self.inventory["feasibility_boundary"]["does_not_establish"])

    def test_supplement_is_aggregate_proportions_not_embryo_rows(self):
        supplement = self.receipt["publisher_supplement"]
        self.assertEqual(supplement["workbook_structure"]["populated_sheet_dimensions"], "35 rows by 7 columns")
        self.assertIn("not a row-per-embryo", supplement["qualification"])
        self.assertFalse(supplement["row_level_values_transcribed"])
        self.assertIn("four populated blocks", self.inventory["data_routes"]["workbook_structure"])

    def test_cycle203_extract_corrects_structure_and_preserves_percentage_conflicts(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        audit = json.loads((base / "song-mmc2-cell-audit-cycle203.json").read_text(encoding="utf-8"))
        with (base / "song-mmc2-source-cell-extract-cycle203.csv").open(encoding="utf-8-sig", newline="") as handle:
            cells = list(csv.DictReader(handle))
        self.assertEqual(audit["source_workbook"]["sha256"], self.receipt["publisher_supplement"]["source_data_workbook_sha256"])
        self.assertEqual(audit["source_cell_extract"]["cell_values"], 106)
        self.assertEqual(len(cells), 106)
        self.assertEqual(audit["integrity_checks"]["cluster_proportion_values_checked"], 35)
        self.assertEqual(audit["integrity_checks"]["proportions_matching_count_over_derived_group_total"], 35)
        self.assertEqual(audit["integrity_checks"]["stage_percent_cells_matching_recomputed_ratio"], 27)
        self.assertEqual(audit["integrity_checks"]["stage_percent_mismatches"], [{"cell": "E23", "printed_value": "5(0.01%)", "percent_from_counts_rounded_2dp": "0.10"}])
        self.assertTrue(all(not row["matches_all_cluster_basis"] and row["matches_embryo_only_basis"] for row in audit["integrity_checks"]["bottom_summary_stage_percentage_basis_matches"] if row["row_label"] == "Epi"))
        self.assertTrue(all(row["matches_all_cluster_basis"] and not row["matches_embryo_only_basis"] for row in audit["integrity_checks"]["bottom_summary_stage_percentage_basis_matches"] if row["row_label"] == "TE"))
        self.assertEqual(audit["observation_intake"]["biological_observation_records_promoted"], 0)

    def test_similar_geo_candidate_is_not_misattributed(self):
        routes = self.receipt["repository_route_checks"]
        candidate = routes["geo_title_query"]
        self.assertEqual(candidate["candidate_accession"], "GSE263528")
        self.assertEqual(candidate["match_status"], "not linked to this article")
        self.assertIn("Xinbao Zhang", candidate["reason"])
        self.assertIn("Xinwen Zhang", candidate["reason"])
        self.assertIn("no exact full-name match", candidate["reason"])
        self.assertFalse(self.inventory["data_routes"]["geo_title_candidate_linked_to_article"])

    def test_no_observation_promotion_or_later_outcome_claim(self):
        self.assertEqual(self.inventory["observation_intake"]["observation_records_promoted"], 0)
        self.assertFalse(self.receipt["intake_decision"]["complete_gestation_or_birth_evidence"])
        self.assertTrue(self.inventory["data_routes"]["publisher_supplement_pdf"]["downloaded_or_reviewed"])

    def test_cycle204_caption_sample_sizes_are_not_promoted_as_outcomes(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        path = base / "song-mmc1-caption-outcome-screen-cycle204.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        s1b = next(item for item in receipt["caption_level_sample_and_outcome_details"] if item["locator"] == "p. 2, Figure S1B")
        self.assertEqual(s1b["caption_sample_sizes"], {"co_cultured_embryos": 20, "sole_embryos": 16})
        self.assertEqual(s1b["reported_interval"], "d.p.f. 6 to d.p.f. 14")
        self.assertFalse(s1b["operational_survival_criterion_in_caption"])
        self.assertFalse(receipt["observation_intake"]["graph_values_digitized"])
        self.assertFalse(receipt["observation_intake"]["individual_embryo_outcomes_transcribed"])
        self.assertEqual(receipt["observation_intake"]["biological_observation_records_promoted"], 0)
        pdf = self.inventory["data_routes"]["publisher_supplement_pdf"]
        self.assertEqual(pdf["sha256"], receipt["publisher_supplement"]["sha256"])
        self.assertFalse(pdf["source_pdf_persisted_under_artifacts"])
        self.assertEqual(pdf["review_receipt"], "artifacts/postimplantation-coculture-2026-10-11/song-mmc1-caption-outcome-screen-cycle204.json")

    def test_cycle205_article_screen_preserves_survival_and_repository_access_conflicts(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-article-data-access-and-survival-cycle205.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["survival_endpoint"]["co_culture"], {
            "reported_group_label": "co-cultured human embryos", "survivors": 15, "denominator": 20, "printed_rate": "75%"
        })
        self.assertEqual(receipt["survival_endpoint"]["sole_embryo_control"]["survivors"], 6)
        self.assertEqual(receipt["survival_endpoint"]["sole_embryo_control"]["denominator"], 16)
        self.assertFalse(receipt["survival_endpoint"]["per_embryo_fates_transcribed"])
        self.assertFalse(receipt["article_copy"]["publisher_byte_equivalence_verified"])
        self.assertEqual(receipt["repository_route_checks"]["gsa_human"]["current_access_label"], "Controlled access")
        self.assertEqual(receipt["repository_route_checks"]["pride"]["status"], 404)
        self.assertFalse(receipt["intake_decision"]["authors_contacted"])
        self.assertTrue(self.inventory["data_routes"]["publisher_data_availability_section_reviewed"])
        self.assertEqual(self.inventory["data_routes"]["article_declared_data_accessions"]["single_cell_rna_seq"], "GSA-Human HRA006892")
        self.assertFalse(self.inventory["data_routes"]["geo_title_candidate_linked_to_article"])

    def test_cycle205_group_survival_candidate_validates_without_individual_units(self):
        path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        dataset = validate_dataset(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(dataset["source_revision"]["review_status"], "candidate")
        self.assertEqual(len(dataset["observations"]), 2)
        self.assertEqual([item["observation"]["value"] for item in dataset["observations"]], [75, 37.5])
        self.assertTrue(all(item["independent_unit"]["kind"] == "not_reported" for item in dataset["observations"]))
        self.assertEqual([item["denominator"]["value"] for item in dataset["cohort_coverage"]], [20, 16])
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "intake"
            observation_report(path, bundle)
            report = json.loads((bundle / "observation_intake_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["n_observation_records"], 2)
        self.assertEqual(report["n_cohort_coverage_records"], 2)
        self.assertTrue(all(item["status"] == "not_assessed" for item in report["cohort_coverage_checks"]))
        self.assertFalse(report["biological_assay_performed"])

    def test_cycle206_proteomecentral_status_is_not_mistaken_for_data_absence(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-proteomecentral-release-status-cycle206.json").read_text(encoding="utf-8"))
        target = receipt["official_route_checks"]["proteomecentral_target"]
        control = receipt["official_route_checks"]["proteomecentral_known_project_control"]
        self.assertEqual(target["status"], 404)
        self.assertEqual(target["response_bytes"], 4121)
        self.assertEqual(target["response_sha256"], "4778bab5c19c96c41a58afca2166677926ede6f983c3f48f7d2db7f97a409366")
        self.assertIn("not yet publicly released and announced", target["reported_state"])
        self.assertEqual(control["status"], 200)
        self.assertEqual(receipt["interpretation"]["current_route_status"], "reserved_deposited_not_publicly_released_or_announced")
        self.assertFalse(receipt["scope_and_actions"]["project_files_accessed_or_downloaded"])
        self.assertFalse(receipt["scope_and_actions"]["reviewer_credentials_used"])
        self.assertFalse(receipt["scope_and_actions"]["release_or_access_request_made"])
        self.assertIn("that the deposited data are absent", receipt["interpretation"]["does_not_establish"])
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertIn("not yet publicly released or announced", " ".join(candidate["limitations"]))

    def test_cycle207_gsa_public_partial_metadata_is_not_a_survival_cohort(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-gsa-human-public-metadata-screen-cycle207.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["official_record"]["access_label"], "Controlled access")
        self.assertIn("authorized users", receipt["official_record"]["displayed_metadata_notice"])
        individual = receipt["public_partial_metadata_endpoints"]["individual_and_sample_table"]
        runs = receipt["public_partial_metadata_endpoints"]["run_table"]
        self.assertEqual(individual["reported_rows"], 5)
        self.assertEqual(individual["unique_repository_individual_accessions"], 5)
        self.assertEqual(individual["unique_sample_accessions"], 5)
        self.assertEqual(runs["reported_rows"], 10)
        self.assertEqual(runs["unique_experiment_accessions"], 5)
        self.assertFalse(individual["row_level_metadata_retained"])
        self.assertFalse(runs["row_level_metadata_retained"])
        self.assertIn("no crosswalk", receipt["interpretation"]["unit_boundary"])
        self.assertFalse(receipt["scope_and_actions"]["detailed_metadata_export_downloaded"])
        self.assertFalse(receipt["scope_and_actions"]["data_files_accessed_or_downloaded"])
        self.assertFalse(receipt["scope_and_actions"]["access_request_made"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertIn("no crosswalk links", " ".join(candidate["limitations"]))

    def test_cycle208_bioproject_label_counts_remain_unjoined_metadata(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-bioproject-crosslink-screen-cycle208.json").read_text(encoding="utf-8"))
        project = receipt["official_project_page"]
        self.assertTrue(project["title_matches_hra006892"])
        self.assertEqual(project["listed_biosample_count"], 5)
        self.assertEqual(sum(project["listed_biosample_label_counts"].values()), 5)
        self.assertFalse(project["sample_or_biosample_accessions_retained"])
        queries = receipt["external_index_queries"]
        self.assertEqual(queries["ncbi_bioproject_accession"]["result_count"], 0)
        self.assertEqual(queries["ncbi_sra_accession"]["result_count"], 0)
        self.assertEqual(queries["ena_read_run_title"]["result_count"], 0)
        self.assertIn("not verified embryos", receipt["interpretation"]["unit_boundary"])
        self.assertFalse(receipt["scope_and_actions"]["controlled_access_requested"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")

    def test_cycle209_scrna_n_labels_are_not_embryo_or_survival_denominators(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-scrna-assay-n-and-repository-reconciliation-cycle209.json").read_text(encoding="utf-8"))
        labels = receipt["article_single_cell_claims"]["stage_associated_n_labels"]
        self.assertEqual([(item["stage_label"], item["reported_n"]) for item in labels], [("d.p.f. 9", 25), ("d.p.f. 12", 16), ("d.p.f. 14", 33)])
        self.assertEqual(receipt["article_single_cell_claims"]["arithmetic_sum_of_reported_n_labels"], 74)
        self.assertEqual(receipt["article_single_cell_claims"]["counted_unit_status"], "not_independently_defined_in_caption")
        self.assertFalse(receipt["repository_metadata_comparison"]["sample_to_article_n_crosswalk"])
        self.assertFalse(receipt["repository_metadata_comparison"]["sample_to_survival_group_crosswalk"])
        self.assertEqual(receipt["intake_decision"]["biological_observation_records_promoted"], 0)
        self.assertFalse(receipt["intake_decision"]["individual_embryo_records_created"])
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertEqual(len(candidate["observations"]), 2)

    def test_cycle210_public_sample_run_join_stays_aggregate_and_modality_unresolved(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-gsa-sample-run-aggregate-join-cycle210.json").read_text(encoding="utf-8"))
        join = receipt["route_and_join"]
        by_label = {item["label"]: item["run_rows"] for item in join["aggregate_runs_by_public_sample_label"]}
        self.assertEqual(by_label, {"d.p.f.9": 2, "d.p.f.12": 2, "d.p.f.14": 4, "D14WE": 2})
        self.assertEqual(sum(by_label.values()), 10)
        self.assertEqual(join["aggregate_strategy_counts"], {"RNA-Seq": 10})
        self.assertEqual(join["aggregate_platform_counts"], {"Illumina NovaSeq 6000": 10})
        self.assertFalse(receipt["article_modality_comparison"]["gsa_public_strategy_and_platform_distinguish_article_modalities"])
        self.assertFalse(receipt["article_modality_comparison"]["article_library_modality_to_repository_run_crosswalk"])
        self.assertFalse(receipt["outcome_linkage"]["run_to_survival_group_crosswalk"])
        self.assertFalse(receipt["scope_and_actions"]["sample_accessions_or_individual_identifiers_retained"])
        self.assertFalse(receipt["scope_and_actions"]["files_accessed_or_downloaded"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertEqual(len(candidate["observations"]), 2)

    def test_cycle211_no_title_token_hit_is_bounded_not_data_absence(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-gsa-title-modality-token-screen-cycle211.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_route"]["rows_screened"], 10)
        self.assertEqual(len(receipt["results"]), 6)
        self.assertTrue(all(item["matching_run_rows"] == 0 and item["matching_experiments"] == 0 for item in receipt["results"]))
        self.assertFalse(receipt["interpretation"]["modality_crosswalk_resolved"])
        self.assertIn("does not show", receipt["interpretation"]["meaning"])
        self.assertFalse(receipt["scope_and_actions"]["title_values_retained"])
        self.assertFalse(receipt["scope_and_actions"]["project_files_accessed_or_downloaded"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")

    def test_cycle212_experiment_detail_pages_do_not_resolve_assay_modality(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-gsa-experiment-detail-field-screen-cycle212.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["page_selection"]["unique_experiment_pages_checked"], 5)
        self.assertEqual(receipt["detail_page_results"]["http_status_counts"], {"200": 5})
        field_keys = [key for key in receipt["detail_page_results"] if key.endswith("_pages")]
        self.assertTrue(field_keys)
        self.assertTrue(all(receipt["detail_page_results"][key] == 0 for key in field_keys))
        self.assertFalse(receipt["interpretation"]["assay_modality_crosswalk_resolved"])
        self.assertFalse(receipt["scope_and_actions"]["files_accessed_or_downloaded"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")

    def test_cycle213_distinguishes_run_rows_from_unique_runs_and_keeps_index_checks_bounded(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-gsa-accession-mirror-check-cycle213.json").read_text(encoding="utf-8"))
        table = receipt["gsa_public_table"]
        self.assertEqual(table["table_rows"], 10)
        self.assertEqual(table["unique_run_accessions"], 5)
        self.assertEqual(table["unique_experiment_accessions"], 5)
        self.assertEqual(table["table_rows_per_run_accession"], {"2": 5})
        self.assertFalse(table["file_pair_semantics_inferred"])
        external = receipt["external_index_checks"]
        self.assertEqual(external["ncbi_sra_combined_run_and_experiment_accession_search"]["result_count"], 0)
        self.assertEqual(external["ena_read_run_accession_query"]["result_count"], 0)
        self.assertEqual(external["ena_read_experiment_accession_query"]["result_count"], 0)
        self.assertFalse(receipt["scope_and_actions"]["sample_or_run_identifiers_retained"])
        self.assertFalse(receipt["scope_and_actions"]["data_files_accessed_or_downloaded"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")

    def test_cycle214_biosample_index_no_hits_do_not_mean_data_absence(self):
        base = ROOT / "artifacts/postimplantation-coculture-2026-10-11"
        receipt = json.loads((base / "song-gsa-biosample-mirror-check-cycle214.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["gsa_public_sample_source"]["distinct_biosample_accessions_queried"], 5)
        self.assertFalse(receipt["gsa_public_sample_source"]["accession_strings_retained"])
        self.assertEqual(receipt["external_index_checks"]["ncbi_biosample"]["result_count"], 0)
        self.assertEqual(receipt["external_index_checks"]["ena_sample"]["result_count"], 0)
        self.assertFalse(receipt["interpretation"]["sample_mirror_found"])
        self.assertIn("that the NGDC BioSample records or data are absent", receipt["interpretation"]["does_not_establish"])
        self.assertFalse(receipt["scope_and_actions"]["biosample_or_sequence_files_accessed_or_downloaded"])
        self.assertFalse(receipt["scope_and_actions"]["controlled_access_requested"])
        self.assertEqual(receipt["scope_and_actions"]["biological_observation_records_promoted"], 0)
        candidate_path = ROOT / "config/observations/song_2026_postimplantation_survival_candidate.json"
        candidate = validate_dataset(json.loads(candidate_path.read_text(encoding="utf-8")))
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")

    def test_review_receipt_matches_source_manifest(self):
        source_path = ROOT / "artifacts/postimplantation-coculture-2026-10-11/SOURCE.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        for entry in source["files"]:
            content = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(len(content), entry["bytes"], entry["path"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), entry["sha256"], entry["path"])
        self.assertIn("publisher_supplement_caption_outcome_screen", [entry["role"] for entry in source["files"]])
        self.assertIn("article_data_access_and_survival_source_screen", [entry["role"] for entry in source["files"]])
        self.assertIn("proteomecentral_release_status_review", [entry["role"] for entry in source["files"]])
        self.assertIn("gsa_human_public_metadata_screen", [entry["role"] for entry in source["files"]])
        self.assertIn("ngdc_bioproject_crosslink_screen", [entry["role"] for entry in source["files"]])
        self.assertIn("scrna_assay_repository_reconciliation", [entry["role"] for entry in source["files"]])
        self.assertIn("gsa_sample_run_aggregate_join", [entry["role"] for entry in source["files"]])
        self.assertIn("gsa_title_modality_token_screen", [entry["role"] for entry in source["files"]])
        self.assertIn("gsa_experiment_detail_field_screen", [entry["role"] for entry in source["files"]])
        self.assertIn("gsa_accession_mirror_check", [entry["role"] for entry in source["files"]])
        self.assertIn("gsa_biosample_mirror_check", [entry["role"] for entry in source["files"]])
        self.assertFalse(source["reviewed_source_workbook"]["persisted_under_artifacts"])

    def test_article_linkage_follow_up_is_bounded(self):
        linkage_path = ROOT / "artifacts/postimplantation-coculture-2026-10-11/song-article-to-repository-linkage-cycle197.json"
        linkage = json.loads(linkage_path.read_text(encoding="utf-8"))
        self.assertEqual(linkage["official_ncbi_crosslinks"]["pubmed_to_geo"]["linked_geo_records"], [])
        self.assertEqual(linkage["official_ncbi_crosslinks"]["pubmed_to_sra"]["linked_sra_records"], [])
        self.assertFalse(linkage["publisher_full_text_access"]["data_availability_section_reviewed"])
        self.assertIn("alternate publication link", linkage["gse263528_assessment"]["decision"])


if __name__ == "__main__":
    unittest.main()
