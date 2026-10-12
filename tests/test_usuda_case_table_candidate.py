import csv
import hashlib
import json
import statistics
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/usuda_2023_case_table_candidate.json"


class UsudaCaseTableCandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))

    def test_case_table_values_remain_attached_to_source_case_labels(self):
        validated = validate_dataset(self.dataset)
        observations = validated["observations"]
        self.assertEqual(len(observations), 36)
        self.assertTrue(all(row["independent_unit"]["kind"] == "fetus" for row in observations))

        expected = {
            "A": (705, 1460, 296, "-", "(240H-) +",
                 "Euthanized at 296 h after progressive circuit-flow deterioration; the case narrative reports no overt bleeding."),
            "B": (630, 1230, 306, "Bladder+ (290H-)", "(216H-) +",
                 "Euthanized at 306 h after gross hematuria; necropsy reported bladder-wall perforation."),
            "C": (605, 1290, 213, "retroperitoneum+ (24H)", "-",
                 "Euthanized at 213 h after circuit-flow deterioration; earlier retroperitoneal bleeding at 24 h is reported."),
            "D": (625, 1250, 174, "Bladder + (172H-)", "-",
                 "Euthanized at 174 h after gross hematuria; necropsy reported bladder and colon perforation."),
            "E": (672, 1230, 173, "Bladder + (170H-)", "-",
                 "Euthanized at 173 h after gross hematuria; necropsy reported bladder perforation."),
            "F": (698, 1480, 336, "-", "(240H-) +",
                 "Survival time was 336 h; the Results report one of six fetuses reached the pre-determined duration."),
        }
        by_case = {}
        for row in observations:
            case = row["independent_unit"]["id"][-1]
            by_case.setdefault(case, {})[row["assay"]["endpoint"]] = row["observation"]["value"]
        self.assertEqual(set(by_case), set(expected))
        for case, (start_weight, end_weight, duration, bleeding, edema, disposition) in expected.items():
            with self.subTest(case=case):
                self.assertEqual(by_case[case], {
                    "Body weight at induction of APT": start_weight,
                    "Body weight at conclusion of APT": end_weight,
                    "Support survival duration": duration,
                    "Bleeding status (source-coded)": bleeding,
                    "Edema status (source-coded)": edema,
                    "Case-specific experiment disposition summary": disposition,
                })

        event_rows = [row for row in observations
                      if row["assay"]["endpoint"] in {
                          "Bleeding status (source-coded)", "Edema status (source-coded)"}]
        self.assertTrue(all(row["observation"]["measurement_time"] is None for row in event_rows))
        self.assertTrue(all("unparsed" in row["observation"]["measurement_time_unit"]
                            for row in event_rows))

        by_record_id = {row["record_id"]: row for row in observations}
        for case in "abcdef":
            start = by_record_id[f"usuda-case-{case}-body-weight-at-induction"]
            end = by_record_id[f"usuda-case-{case}-body-weight-at-conclusion"]
            duration = by_record_id[f"usuda-case-{case}-support-survival-duration"]
            self.assertEqual(start["observation"]["measurement_time"], 0)
            self.assertEqual(end["observation"]["measurement_time"], duration["observation"]["value"])
            self.assertEqual(start["developmental_interval"]["end"], duration["observation"]["value"])

    def test_candidate_source_bytes_and_denominator_are_preserved(self):
        artifact = self.dataset["artifacts"][0]
        source_path = ROOT / artifact["local_path"]
        self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), artifact["sha256"])
        self.assertEqual(self.dataset["source_revision"]["review_status"], "candidate")
        coverage = self.dataset["cohort_coverage"][0]
        self.assertEqual(coverage["counted_entity_kind"], "fetus")
        self.assertEqual(coverage["denominator"]["value"], 6)
        self.assertEqual(coverage["cohort_window_status"], "source_labels_only")
        self.assertEqual(self.dataset["transitions"], [])
        self.assertTrue(any("no per-case join" in item for item in self.dataset["limitations"]))

    def test_table4_case_rows_reconstruct_table1_group_summaries(self):
        expected = {
            "Body weight at induction of APT": (656, 42),
            "Body weight at conclusion of APT": (1323, 116),
            "Support survival duration": (250, 72),
        }
        for endpoint, reported_mean_sd in expected.items():
            values = [row["observation"]["value"] for row in self.dataset["observations"]
                      if row["assay"]["endpoint"] == endpoint]
            with self.subTest(endpoint=endpoint):
                self.assertEqual(len(values), 6)
                self.assertEqual(
                    (round(statistics.mean(values)), round(statistics.stdev(values))),
                    reported_mean_sd,
                )

        inventory_path = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        source_record = next(
            item for item in inventory["records"]
            if item["record_id"] == "usuda_2023_growth_and_disposition"
        )
        check = source_record["machine_readable_candidate_intake"]["transcription_check"]
        self.assertEqual(check["status"], "case_rows_reconcile_to_table_1_after_rounding")
        self.assertEqual(
            {item["endpoint"]: item["table_4_reconstructed_mean_sd"]
             for item in check["comparisons"]},
            {
                "Body weight at induction of APT": "656 ± 42 g",
                "Body weight at conclusion of APT": "1323 ± 116 g",
                "Support survival duration": "250 ± 72 h",
            },
        )

    def test_intake_export_keeps_fetus_labels_events_and_no_inferred_transition(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "intake"
            receipt = observation_report(DATASET, output, source_root=ROOT)
            report = json.loads((output / "observation_intake_report.json").read_text(encoding="utf-8"))

            self.assertEqual(receipt["bundle_kind"], "developmental_observation_intake")
            self.assertEqual(report["n_observation_records"], 36)
            self.assertEqual(report["n_transitions"], 0)
            self.assertEqual(report["source_file_verification"]["status"], "complete")
            with (output / "observation_records.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 36)
            self.assertEqual({row["independent_unit_kind"] for row in rows}, {"fetus"})
            self.assertEqual({row["independent_unit_id"] for row in rows},
                             {f"Case {case}" for case in "ABCDEF"})
            event_rows = [row for row in rows if row["endpoint"].endswith("status (source-coded)")]
            self.assertEqual(len(event_rows), 12)
            self.assertEqual({row["value"] for row in event_rows}, {
                "-", "(240H-) +", "Bladder+ (290H-)", "(216H-) +",
                "retroperitoneum+ (24H)", "Bladder + (172H-)", "Bladder + (170H-)",
            })
            disposition_rows = [row for row in rows if row["endpoint"] == "Case-specific experiment disposition summary"]
            self.assertEqual(len(disposition_rows), 6)
            self.assertTrue(all("vasoconstriction" not in row["value"].lower()
                                for row in disposition_rows))
            with (output / "transitions.csv").open(newline="", encoding="utf-8") as stream:
                self.assertEqual(list(csv.reader(stream)), [[
                    "transition_id", "from_record_ids", "to_record_ids", "continuity_status", "note"
                ]])


if __name__ == "__main__":
    unittest.main()
