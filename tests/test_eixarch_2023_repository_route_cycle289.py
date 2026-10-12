import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle289"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2023RepositoryRouteCycle289Tests(unittest.TestCase):
    def test_public_route_screen_is_bounded_and_candidate_values_are_unchanged(self):
        summary = json.loads((ART / "repository-route-summary-cycle289.json").read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(summary["query_count"], 11)
        self.assertFalse(summary["assessment"]["target_dataset_or_supplement_identified"])
        self.assertFalse(summary["assessment"]["candidate_observation_values_changed"])
        self.assertEqual(len(candidate["observations"]), 50)
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertTrue(any("Cycle 289 queried public" in item for item in candidate["limitations"]))

        zenodo = next(item for item in summary["query_results"]
                      if item["query"] == "Zenodo exact DOI")
        self.assertEqual(zenodo["http_status"], 500)
        self.assertIsNone(zenodo["results_returned"])
        self.assertEqual(zenodo["result_count_status"], "unavailable_http_error")
        self.assertIn("unavailable", zenodo["query_limit"].lower())

        figshare = next(item for item in summary["query_results"]
                        if item["query"] == "Figshare artificial placenta sheep")
        self.assertEqual(figshare["results_returned"], 3)
        with (ART / "repository-route-crosswalk-cycle289.csv").open(
                encoding="utf-8", newline="") as stream:
            crosswalk = list(csv.DictReader(stream))
        related = [row for row in crosswalk
                   if row["query"] == "Figshare artificial placenta sheep"
                   and row["manual_disposition"].startswith("Topically related")]
        self.assertEqual(len(related), 2)
        self.assertTrue(all(row["target_record_match"] == "False" for row in related))

    def test_crosswalk_raw_response_hashes_and_inventory_binding(self):
        summary = json.loads((ART / "repository-route-summary-cycle289.json").read_text(encoding="utf-8"))
        routes = json.loads((ART / "route-results-cycle289.json").read_text(encoding="utf-8"))
        route_by_file = {item["file"]: item for item in routes["queries"]}
        with (ART / "repository-route-crosswalk-cycle289.csv").open(
                encoding="utf-8", newline="") as stream:
            crosswalk = list(csv.DictReader(stream))
        self.assertEqual(len(crosswalk), 59)
        for row in crosswalk:
            route = route_by_file[row["raw_response_file"]]
            raw = ART / route["file"]
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()
            self.assertEqual(row["raw_response_sha256"], digest)
            self.assertEqual(route["sha256"], digest)

        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(item for item in inventory["records"]
                      if item["record_id"] == "eixarch_2023_entry_learning_curve")
        screen = record["public_repository_route_check_cycle289"]
        self.assertEqual(screen["returned_target_records"], 0)
        self.assertEqual(screen["zenodo_exact_doi_status"],
                         "HTTP 500; unavailable, not a zero-result query")
        self.assertIn("global data absence", screen["bounded_interpretation"])


if __name__ == "__main__":
    unittest.main()

