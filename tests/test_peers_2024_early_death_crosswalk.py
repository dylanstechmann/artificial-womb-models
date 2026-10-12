import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Peers2024EarlyDeathCrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.record = next(
            row for row in self.inventory["records"]
            if row["record_id"] == "peers_2024_extend_outcomes"
        )

    def test_results_narrative_duration_cause_pairs_are_preserved(self):
        deaths = self.record["reported_premature_deaths"]
        crosswalk = deaths["duration_reason_crosswalk"]
        self.assertEqual(
            [(event["support_days_before_death"], event["reported_reason"])
             for event in crosswalk["events_as_reported"]],
            [
                (3, "iatrogenic fluid overload"),
                (6, "sudden cardiac arrest"),
                (7, "sudden and irreversible venous spasm"),
                (8, "sudden and irreversible venous spasm"),
            ],
        )
        self.assertIn("suspected", crosswalk["events_as_reported"][1]["qualification"])
        self.assertIn("likely trigger", crosswalk["events_as_reported"][2]["qualification"])

    def test_event_tuples_do_not_manufacture_animal_ids_or_join_analyzed_rows(self):
        deaths = self.record["reported_premature_deaths"]
        crosswalk = deaths["duration_reason_crosswalk"]
        self.assertEqual(crosswalk["status"],
                         "duration_and_reason_linked_in_results; persistent_animal_ids_not_reported")
        self.assertIn("not specimen identifiers", crosswalk["animal_identity_boundary"])
        self.assertTrue(all("animal_id" not in event and "case_id" not in event
                            for event in crosswalk["events_as_reported"]))
        self.assertEqual(self.record["cohort_size"]["analyzed"], 10)
        self.assertEqual(deaths["n"], 4)


if __name__ == "__main__":
    unittest.main()
