import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/artificial-placenta-gas-pairability-2026-10-11-cycle319"
ASSESSMENT = ART / "gas-exchange-pairability-cycle319.json"
TABLE = ART / "gas-exchange-pairability-cycle319.csv"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/artificial_placenta_gas_pairability_2026.json"


class ArtificialPlacentaGasPairabilityCycle319Tests(unittest.TestCase):
    def test_two_public_sources_keep_sampling_route_distinct_from_pairable_results(self):
        assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        with TABLE.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual({row["source_id"] for row in rows}, {"reoma_2009", "omecinski_2023"})
        self.assertTrue(all(row["reported_measurement_route"] for row in rows))
        self.assertIn("PMC", next(row for row in rows if row["source_id"] == "reoma_2009")["reported_measurement_route"])
        self.assertTrue(all(row["pairable_numeric_records_in_inspected_route"] == "no" for row in rows))
        self.assertEqual(assessment["conclusion"]["eligible_measurement_pair_sets_identified"], 0)
        self.assertTrue(assessment["conclusion"]["methods_sampling_is_not_a_result"])
        self.assertTrue(assessment["conclusion"]["no_values_digitized"])

    def test_screen_is_bounded_and_does_not_contact_authors_or_change_candidate(self):
        assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        self.assertTrue(all(not source["author_contacted"] for source in assessment["sources"]))
        self.assertTrue(assessment["conclusion"]["bounded_absence_claim"].startswith("The inspected public routes"))
        expected = "4174517e06e55ac6ab9c27e2ecbd8346510552c2184e52022fa476717e948159"
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), expected)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(inventory["eligible_pair_sets_identified"], 0)
        self.assertFalse(inventory["candidate_values_changed"])
        self.assertFalse(inventory["author_contacted"])

    def test_report_links_the_primary_public_sources(self):
        report = (ART / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("https://pmc.ncbi.nlm.nih.gov/articles/PMC11660002/", report)
        self.assertIn("https://pmc.ncbi.nlm.nih.gov/articles/PMC9897463/", report)
        self.assertIn("do not establish", report)


if __name__ == "__main__":
    unittest.main()
