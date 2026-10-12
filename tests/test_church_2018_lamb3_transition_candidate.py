import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/church_2018_lamb3_transition_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
ARTIFACTS = ROOT / "artifacts/fetal-ovine-transition-2026-10-11-cycle285"


class Church2018TransitionTableCandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.validated = validate_dataset(self.dataset)
        self.by_id = {row["record_id"]: row for row in self.validated["observations"]}

    def test_five_table_rows_and_lamb3_outcome_keep_timing_limits(self):
        self.assertEqual(len(self.validated["observations"]), 35)
        self.assertEqual(len(self.dataset["cohort_coverage"]), 1)
        self.assertEqual(len(self.dataset["transitions"]), 9)
        self.assertEqual(self.by_id["church2018-ap-lamb3-mv-alone-duration"]["observation"]["value"], 26)
        outcome = self.by_id["church2018-ap-lamb3-outcome"]
        self.assertEqual(outcome["observation"]["value"],
                         "Mucus plugging in ETT → acute respiratory failure")
        self.assertIsNone(outcome["observation"]["measurement_time"])
        self.assertTrue(any("exact event timestamps" in item for item in outcome["limitations"]))

    def test_duration_aggregation_mismatch_is_preserved_not_reconciled(self):
        rows = [self.by_id[f"church2018-ap-lamb{i}-ap-mv-duration"]["observation"]["value"]
                for i in range(1, 6)]
        self.assertEqual(rows, [91, 17, 25, 15, 115])
        receipt = json.loads((ARTIFACTS / "duration-aggregation-check-cycle285.json").read_text(encoding="utf-8"))
        check = receipt["arithmetic_check_using_mean_and_sample_SD"]
        self.assertEqual(check["AP + MV concurrent"]["mean_hours"], 52.6)
        self.assertEqual(check["AP + MV concurrent first four rows"]["mean_hours"], 37)
        self.assertEqual(check["AP + MV concurrent first four rows"]["sample_sd_hours"], 36.2583)
        self.assertIn("does not state which rows", receipt["interpretation"])

    def test_phase_links_use_derived_elapsed_hours_and_not_event_times(self):
        raw_by_id = {row["record_id"]: row for row in self.dataset["observations"]}
        ap = raw_by_id["church2018-ap-lamb3-ap-duration"]["developmental_interval"]
        ap_mv = raw_by_id["church2018-ap-lamb3-ap-mv-duration"]["developmental_interval"]
        mv = raw_by_id["church2018-ap-lamb3-mv-alone-duration"]["developmental_interval"]
        self.assertEqual((ap["start"], ap["end"]), (0, 240))
        self.assertEqual((ap_mv["start"], ap_mv["end"]), (240, 265))
        self.assertEqual((mv["start"], mv["end"]), (265, 291))
        self.assertTrue(all("(derived)" in row["time_unit"] for row in (ap, ap_mv, mv)))
        self.assertTrue(all(edge["continuity_status"] == "demonstrated"
                            for edge in self.dataset["transitions"]))

    def test_source_snapshot_hash_and_inventory_match(self):
        artifact = self.dataset["artifacts"][0]
        source_path = ROOT / artifact["local_path"]
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        self.assertEqual(digest, artifact["sha256"])
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(row for row in inventory["records"]
                             if row["record_id"] == "church_2018_ap_to_ventilation")
        intake = source_record["machine_readable_candidate_intake"]
        self.assertEqual(intake["record_count"], 35)
        self.assertEqual(intake["source_snapshot_sha256"], digest)
        self.assertEqual(source_record["post_support_observation"]["longest_ventilation_only_case_id"],
                         "AP Lamb 3")
        self.assertIsNone(source_record["post_support_observation"]["case_outcome_time"])
        self.assertEqual(source_record["data_availability"]["status"],
                         "article_case_table_no_longitudinal_file_located")

    def test_export_keeps_duration_numeric_and_outcome_as_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "intake"
            observation_report(DATASET, output)
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(len(rows), 35)
        by_id = {row["record_id"]: row for row in rows}
        self.assertEqual(by_id["church2018-ap-lamb3-mv-alone-duration"]["value"], "26")
        self.assertEqual(by_id["church2018-ap-lamb3-mv-alone-duration"]["measurement_time"], "")
        self.assertEqual(by_id["church2018-ap-lamb3-outcome"]["value"],
                         "Mucus plugging in ETT → acute respiratory failure")
        self.assertEqual(by_id["church2018-ap-lamb3-outcome"]["measurement_time"], "")


if __name__ == "__main__":
    unittest.main()
