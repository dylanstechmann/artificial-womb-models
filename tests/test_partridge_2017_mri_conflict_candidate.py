import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/partridge_2017_mri_time_conflict_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Partridge2017MriConflictCandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))

    def test_case_summary_keeps_both_reported_ages_without_selecting_one(self):
        validated = validate_dataset(self.dataset)
        self.assertEqual(len(validated["observations"]), 1)
        row = validated["observations"][0]
        self.assertEqual(row["independent_unit"]["id"], "Semi-closed CA/JV Animal 4")
        self.assertIsNone(row["observation"]["measurement_time"])
        self.assertIn("1 year", row["observation"]["measurement_time_unit"])
        self.assertIn("6 months", row["observation"]["measurement_time_unit"])
        self.assertTrue(any("does not select one" in item for item in validated["limitations"]))
        self.assertTrue(any("not a comprehensive developmental assessment" in item
                            for item in validated["limitations"]))

    def test_inventory_crosswalk_preserves_primary_source_conflict(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(
            row for row in inventory["records"]
            if row["record_id"] == "partridge_2017_semiclosed_cajv"
        )
        intake = source_record["machine_readable_candidate_intake"]
        self.assertEqual(intake["path"], "config/observations/partridge_2017_mri_time_conflict_candidate.json")
        self.assertEqual(intake["record_count"], 1)
        self.assertEqual(source_record["follow_up_time_discrepancy"]["status"],
                         "unresolved_within_primary_article")
        self.assertEqual(source_record["follow_up_time_discrepancy"]["details_months"], [6, 12])

    def test_export_leaves_the_disputed_measurement_time_blank(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "intake"
            observation_report(DATASET, output)
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["measurement_time"], "")
        self.assertIn("1 year", rows[0]["measurement_time_unit"])
        self.assertIn("6 months", rows[0]["measurement_time_unit"])


if __name__ == "__main__":
    unittest.main()
