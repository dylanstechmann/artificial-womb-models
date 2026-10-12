import csv
import json
import math
import statistics
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/peers_2024_extend_table2_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
SUMMARY = ROOT / "config/source_inventories/peers_2024_table2_summary_reconstruction.csv"


class Peers2024Table2CandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.validated = validate_dataset(self.dataset)

    def test_ten_animal_rows_keep_run_values_and_reproduce_table2_mean(self):
        by_animal = defaultdict(dict)
        for row in self.validated["observations"]:
            unit = row["independent_unit"]["id"]
            by_animal[unit][row["assay"]["endpoint"]] = row["observation"]["value"]

        self.assertEqual(len(by_animal), 10)
        self.assertTrue(all(len(rows) == 17 for rows in by_animal.values()))
        run = [by_animal[f"Animal {n}"]["Length of the run on EXTEND"] for n in range(1, 11)]
        self.assertEqual(run, [11, 21, 14, 14, 16, 14, 10, 13, 12, 10])
        self.assertEqual(sum(run) / len(run), 13.5)

    def test_supplement_screen_records_metadata_without_claiming_content_review(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(row for row in inventory["records"]
                             if row["record_id"] == "peers_2024_extend_outcomes")
        screen = source_record["supplementary_file_screen"]
        self.assertEqual(screen["file_name"], "41390_2024_3287_MOESM1_ESM.pdf")
        self.assertEqual(screen["size_reported"], "82.7 MB")
        self.assertEqual(screen["status"], "metadata_only_file_not_inspected")
        self.assertFalse(screen.get("content_inspected", False))
        self.assertIn("does not establish whether any plots show animal-specific traces", screen["boundary"])

    def test_duration_correction_screen_is_bounded_and_does_not_repair_table_value(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(row for row in inventory["records"]
                             if row["record_id"] == "peers_2024_extend_outcomes")
        screen = source_record["publication_correction_screen"]
        self.assertEqual(screen["status"], "no_correction_identified_in_bounded_public_record_search")
        self.assertIn("not proof that no correction exists", screen["boundary"])
        discrepancy = source_record["support_duration_days"]["table2_run_duration_discrepancy"]
        self.assertTrue(discrepancy["do_not_repair"])
        animal5 = next(row for row in self.validated["observations"]
                       if row["independent_unit"]["id"] == "Animal 5"
                       and row["assay"]["endpoint"] == "Length of the run on EXTEND")
        self.assertEqual(animal5["observation"]["value"], 16)

    def test_transfusion_counts_reconcile_to_group_summary_as_care_exposure(self):
        by_animal = defaultdict(dict)
        for row in self.validated["observations"]:
            by_animal[row["independent_unit"]["id"]][row["assay"]["endpoint"]] = row["observation"]["value"]
        counts = [by_animal[f"Animal {n}"]["Number of transfusions during EXTEND support"] for n in range(1, 11)]
        self.assertEqual(counts, [0, 0, 1, 2, 1, 0, 0, 1, 1, 4])
        self.assertEqual(sum(value > 0 for value in counts), 6)
        self.assertEqual(statistics.mean(counts), 1)
        self.assertAlmostEqual(statistics.stdev(counts) / math.sqrt(len(counts)), 0.394405, places=6)
        self.assertTrue(all("not identify indication" in row["limitations"][0]
                            for row in self.validated["observations"]
                            if row["assay"]["endpoint"] == "Number of transfusions during EXTEND support"))

    def test_run_duration_matches_row_ages_while_animal5_text_conflict_stays_open(self):
        by_animal = defaultdict(dict)
        for row in self.validated["observations"]:
            by_animal[row["independent_unit"]["id"]][row["assay"]["endpoint"]] = row["observation"]["value"]

        for number, rows in ((n, by_animal[f"Animal {n}"]) for n in range(1, 11)):
            self.assertEqual(rows["Age at necropsy"] - rows["Age at cannulation"],
                             rows["Length of the run on EXTEND"], msg=f"Animal {number}")
        animal5 = by_animal["Animal 5"]["Length of the run on EXTEND"]
        self.assertEqual(animal5, 16)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(row for row in inventory["records"]
                             if row["record_id"] == "peers_2024_extend_outcomes")
        discrepancy = source_record["support_duration_days"]["table2_run_duration_discrepancy"]
        self.assertEqual(discrepancy["status"], "unresolved_within_primary_article")
        self.assertTrue(discrepancy["do_not_repair"])
        self.assertIn("16 days", discrepancy["details"])

    def test_blank_brain_weight_and_group_only_brain_analysis_are_separate(self):
        brain_rows = [row for row in self.validated["observations"]
                      if row["assay"]["endpoint"] == "Brain weight at necropsy"]
        self.assertEqual(len(brain_rows), 10)
        missing = [row for row in brain_rows if row["observation"]["value"] is None]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["independent_unit"]["id"], "Animal 3")
        self.assertIn("Table 2 cell is blank", missing[0]["observation"]["missingness_reason"])
        self.assertEqual(len(self.validated["cohort_coverage"]), 6)
        brain_coverage = self.validated["cohort_coverage"][1]
        self.assertEqual(brain_coverage["denominator"]["value"], 10)
        self.assertEqual([item["value"] for item in brain_coverage["declarations"]
                          if item["category"] == "assessed"], [6, 6])
        self.assertTrue(all(not any(f"Animal {n}" in item["reported_label"] for n in range(1, 11))
                            for item in brain_coverage["declarations"]
                            if item["category"] == "assessed"))
        self.assertTrue(any("does not identify all six analyzed animals" in item["text"]
                            for item in brain_coverage["selection_statements"]))

    def test_export_has_170_rows_and_preserves_missing_brain_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "intake"
            observation_report(DATASET, output)
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(len(rows), 170)
        brain_missing = [row for row in rows
                         if row["endpoint"] == "Brain weight at necropsy"
                         and row["value"] == ""]
        self.assertEqual(len(brain_missing), 1)
        self.assertIn("Animal 3", brain_missing[0]["independent_unit_id"])

    def test_summary_reconstruction_is_calculated_from_candidate_rows_and_keeps_sem_limits(self):
        with SUMMARY.open(newline="", encoding="utf-8") as stream:
            checks = list(csv.DictReader(stream))
        self.assertEqual(len(checks), 14)
        endpoint_by_table_row = {
            "Age at cannulation (days)": "Age at cannulation",
            "Weight at cannulation (kg)": "Weight at cannulation",
            "Age at necropsy (days)": "Age at necropsy",
            "Weight at necropsy (kg)": "Weight at necropsy",
            "Length of the run (days)": "Length of the run on EXTEND",
            "Brain weight at necropsy (g)": "Brain weight at necropsy",
            "Number of transfusions": "Number of transfusions during EXTEND support",
            "Growth rate(g/kg/J)": "Growth rate(g/kg/J)",
            "Brain to body weight": "Brain to body weight",
            "Brain to liver weight": "Brain to liver weight",
            "Heart weight at necropsy (g)": "Heart weight at necropsy",
            "Lung weight at necropsy (g)": "Lung weight at necropsy",
            "Liver weight at necropsy (g)": "Liver weight at necropsy",
            "Right kidney weight at necropsy (g)": "Right kidney weight at necropsy",
        }
        for check in checks:
            values = [row["observation"]["value"] for row in self.validated["observations"]
                      if row["assay"]["endpoint"] == endpoint_by_table_row[check["source_table_row"]]
                      and row["observation"]["value"] is not None
                      and not (check["source_table_row"] == "Brain to liver weight"
                               and row["independent_unit"]["id"] == "Animal 5")]
            self.assertEqual(len(values), int(check["n"]))
            reconstructed_mean = statistics.mean(values)
            reconstructed_sem = statistics.stdev(values) / math.sqrt(len(values))
            self.assertAlmostEqual(reconstructed_mean,
                                   float(check["reconstructed_mean_from_displayed_rows"]), delta=0.000001)
            self.assertAlmostEqual(reconstructed_sem,
                                   float(check["reconstructed_sem_from_displayed_rows"]), delta=0.000001)

        unresolved = [row["source_table_row"] for row in checks
                      if row["sem_check_status"] == "not_reproduced_from_displayed_values"]
        self.assertEqual(unresolved, ["Age at cannulation (days)", "Weight at cannulation (kg)"])
        self.assertEqual([row["source_table_row"] for row in checks
                          if row["mean_check_status"] == "not_reproduced_from_displayed_values"],
                         ["Brain to liver weight"])
        self.assertTrue(all("do not infer an article error" in row["interpretation"]
                            for row in checks if row["sem_check_status"] == "not_reproduced_from_displayed_values"))

    def test_comparator_group_coverage_stays_separate_from_numbered_extremely_preterm_animals(self):
        coverage = {item["coverage_id"]: item for item in self.validated["cohort_coverage"]}
        expected = {
            "peers2024-extremely-preterm-control-coverage": (5, 0, 0),
            "peers2024-late-gestation-extend-coverage": (10, 0, 0),
            "peers2024-late-gestation-control-coverage": (4, 3, 3),
            "peers2024-iugr-extend-pilot-coverage": (3, 0, 0),
        }
        for coverage_id, (denominator, mri_n, histology_n) in expected.items():
            item = coverage[coverage_id]
            self.assertEqual(item["denominator"]["value"], denominator)
            self.assertEqual([d["value"] for d in item["declarations"]
                              if d["reported_label"] == "Animals included in brain MRI analysis"], [mri_n])
            self.assertEqual([d["value"] for d in item["declarations"]
                              if d["reported_label"] == "Animals included in brain histology analysis"], [histology_n])
        self.assertIn("historic", coverage["peers2024-late-gestation-extend-coverage"]["selection_statements"][0]["text"])
        self.assertIn("excluded from statistical comparisons", coverage["peers2024-iugr-extend-pilot-coverage"]["selection_statements"][0]["text"])
        self.assertEqual({row["independent_unit"]["id"] for row in self.validated["observations"]},
                         {f"Animal {n}" for n in range(1, 11)})

    def test_full_table2_per_animal_fields_and_footnote_conflicts_are_preserved(self):
        by_animal = defaultdict(dict)
        for row in self.validated["observations"]:
            by_animal[row["independent_unit"]["id"]][row["assay"]["endpoint"]] = row["observation"]
        self.assertEqual(by_animal["Animal 1"]["Sex (F/M)"]["value"], "F")
        self.assertEqual(by_animal["Animal 10"]["Sex (F/M)"]["value"], "F")
        self.assertEqual(by_animal["Animal 1"]["Size of arterial cannulas (Fr)"]["value"], "10/10")
        self.assertEqual(by_animal["Animal 10"]["Size of venous cannula (Fr)"]["value"], 14)
        self.assertEqual(by_animal["Animal 1"]["Growth rate(g/kg/J)"]["value"], 70.6)
        self.assertEqual(by_animal["Animal 3"]["Brain to body weight"]["value"], None)
        self.assertEqual(by_animal["Animal 3"]["Brain to liver weight"]["value"], None)
        self.assertEqual(by_animal["Animal 5"]["Brain to liver weight"]["value"], 1.5)
        self.assertEqual(by_animal["Animal 5"]["Heart weight at necropsy"]["value"], 10.5)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(row for row in inventory["records"]
                             if row["record_id"] == "peers_2024_extend_outcomes")
        self.assertEqual(source_record["machine_readable_candidate_intake"]["record_count"], 170)
        self.assertIn("including Lamb 1", source_record["table2_summary_reconstruction"]["result"])
        comparator_groups = source_record["table2_comparator_coverage"]["groups"]
        self.assertEqual([item["n"] for item in comparator_groups], [5, 10, 4, 3])
        self.assertIn("Do not infer animal IDs", source_record["table2_comparator_coverage"]["boundary"])
        limitation = " ".join(self.dataset["limitations"])
        self.assertIn("excluding Lamb 1 gives 36.947", limitation)
        self.assertIn("brain-to-liver weight", limitation)


if __name__ == "__main__":
    unittest.main()
