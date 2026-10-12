import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/eixarch_2026_neonatal_transition_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2026TransitionCandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))

    def test_four_poster_case_summaries_include_visual_duration_rows_with_source_conflict(self):
        validated = validate_dataset(self.dataset)
        observations = validated["observations"]
        self.assertEqual(len(observations), 20)
        self.assertEqual(
            {row["independent_unit"]["id"] for row in observations},
            {f"Animal {number}" for number in range(1, 5)},
        )
        self.assertEqual(sum(row["observation"]["measurement_time"] is None for row in observations), 10)
        support_days = {
            row["independent_unit"]["id"]: row["observation"]["value"]
            for row in observations
            if row["assay"]["endpoint"] == "Days on fetal liquid incubator support"
        }
        self.assertEqual(support_days, {
            "Animal 1": 9, "Animal 2": 24, "Animal 3": 8, "Animal 4": 7,
        })
        animal_2_duration = next(
            row for row in observations
            if row["record_id"] == "ep09-22-animal-2-fli-support-duration"
        )
        qualification = animal_2_duration["observation"]["source_qualifications"][0]
        self.assertEqual(qualification["status_code"],
                         "table_cell_conflicts_with_stage_delta_and_summary")
        self.assertEqual(qualification["reference_value"], 14)
        by_case_endpoint = {
            (row["independent_unit"]["id"], row["assay"]["endpoint"]): row
            for row in observations
        }
        self.assertEqual(by_case_endpoint[("Animal 1", "Successful extubation")]
                         ["observation"]["measurement_time"], None)
        self.assertEqual(by_case_endpoint[("Animal 2", "Successful extubation")]
                         ["observation"]["measurement_time"], None)
        self.assertEqual(by_case_endpoint[("Animal 3", "Successful extubation")]
                         ["observation"]["measurement_time_unit"], "hours after neonatal transition")
        self.assertEqual(by_case_endpoint[("Animal 4", "Maze-test comparison statement")]
                         ["observation"]["measurement_time_unit"], "months of age")
        self.assertTrue(any("24" in item and "Animal 2 gestational ages imply 14 days" in item
                            for item in validated["limitations"]))
        self.assertTrue(all(row["source"]["sha256"] == self.dataset["artifacts"][0]["sha256"]
                            for row in observations))
        self.assertEqual(validated["cohort_coverage"][0]["denominator"]["value"], 4)
        self.assertIn("number entering", validated["cohort_coverage"][0]["selection_definition"])

    def test_intake_export_keeps_typed_rows_and_does_not_invent_transitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "intake"
            receipt = observation_report(DATASET, output)
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(receipt["bundle_kind"], "developmental_observation_intake")
        self.assertEqual(report["n_observation_records"], 20)
        self.assertEqual(report["n_transitions"], 0)
        self.assertEqual({row["independent_unit_id"] for row in rows},
                         {f"Animal {number}" for number in range(1, 5)})
        self.assertEqual(sum(row["measurement_time"] == "" for row in rows), 10)

    def test_inventory_crosswalk_preserves_summary_conflict_and_subset_denominator(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(
            row for row in inventory["records"]
            if row["record_id"] == "eixarch_2026_isuog_neonatal_transition_EP09_22"
        )
        intake = source_record["machine_readable_candidate_intake"]
        self.assertEqual(intake["path"], "config/observations/eixarch_2026_neonatal_transition_candidate.json")
        self.assertEqual(intake["record_count"], len(self.dataset["observations"]))
        self.assertEqual(source_record["visual_source_review"]["status"],
                         "completed_official_pdf_rendered_and_visually_inspected")
        self.assertEqual(source_record["artifact_snapshot"]["sha256"],
                         self.dataset["artifacts"][0]["sha256"])

        extubation = {
            row["independent_unit"]["id"]: row["observation"]["value"]
            for row in self.dataset["observations"]
            if row["assay"]["endpoint"] == "Successful extubation"
        }
        self.assertEqual(set(extubation), {f"Animal {number}" for number in range(1, 5)})
        self.assertTrue(extubation["Animal 1"].startswith("No"))
        self.assertTrue(extubation["Animal 2"].startswith("No"))
        self.assertEqual(extubation["Animal 3"], "Yes")
        self.assertEqual(extubation["Animal 4"], "Yes")
        summary_note = source_record["summary_to_table_note"].lower()
        self.assertIn("satisfactory respiratory parameters", summary_note)
        self.assertIn("no successful extubation", summary_note)

        coverage = self.dataset["cohort_coverage"][0]
        self.assertEqual(coverage["denominator"]["value"], 4)
        self.assertIn("not reported", coverage["selection_definition"].lower())


if __name__ == "__main__":
    unittest.main()

