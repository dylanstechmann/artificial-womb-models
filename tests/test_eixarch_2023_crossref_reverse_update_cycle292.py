import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle292"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2023CrossrefReverseUpdateCycle292Tests(unittest.TestCase):
    def test_zero_reverse_links_are_bounded_and_candidate_is_unchanged(self):
        audit = json.loads((ART / "correction-reverse-link-screen-cycle292.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["query"]["status"], 200)
        self.assertEqual(audit["query"]["results_returned"], 0)
        self.assertIn("member-deposited", audit["interpretation_limit"])
        self.assertIn("does not establish", audit["interpretation_limit"])
        self.assertFalse(audit["candidate_observation_values_changed"])

        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(len(candidate["observations"]), 50)
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertTrue(any("Cycle 292 used Crossref" in item for item in candidate["limitations"]))

        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(x for x in inventory["records"]
                      if x["record_id"] == "eixarch_2023_entry_learning_curve")
        self.assertEqual(record["crossref_reverse_update_screen_cycle292"]["crossref_updates_filter_results"], 0)

    def test_crossref_response_is_pinned_and_query_matches_audit(self):
        audit = json.loads((ART / "correction-reverse-link-screen-cycle292.json").read_text(encoding="utf-8"))
        raw_path = ART / audit["query"]["raw_response_file"]
        self.assertEqual(hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                         audit["query"]["raw_response_sha256"])
        response = json.loads(raw_path.read_text(encoding="utf-8"))
        self.assertEqual(response["message"]["total-results"], 0)
        self.assertEqual(response["message"]["items"], [])
        self.assertIn("updates%3A10.3390%2Fbiomedicines11030702", audit["query"]["url"])
        self.assertEqual(audit["query"]["filter_semantics_url"],
                         "https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/")


if __name__ == "__main__":
    unittest.main()

