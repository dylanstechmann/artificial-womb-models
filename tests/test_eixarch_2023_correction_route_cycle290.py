import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle290"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2023CorrectionRouteCycle290Tests(unittest.TestCase):
    def test_pubmed_and_crossref_findings_keep_publisher_gap_explicit(self):
        audit = json.loads((ART / "correction-notice-route-screen-cycle290.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["findings"]["pubmed_record_type"], ["Journal Article"])
        self.assertEqual(audit["findings"]["pubmed_comments_corrections_entries"], 0)
        self.assertEqual(audit["findings"]["pubmed_exact_doi_correction_query_count"], "0")
        self.assertEqual(audit["findings"]["pubmed_exact_title_correction_query_count"], "0")
        self.assertEqual(audit["findings"]["crossref_relation"], {})
        self.assertEqual(audit["findings"]["crossref_update_to"], [])
        self.assertEqual(audit["findings"]["mdpi_notes_http_status"], 403)
        self.assertFalse(audit["findings"]["correction_resolution_identified"])
        self.assertIn("publisher has no correction notice", audit["interpretation_limit"])

        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(len(candidate["observations"]), 50)
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        self.assertTrue(any("Cycle 290 checked the PubMed record" in item
                            for item in candidate["limitations"]))

        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(item for item in inventory["records"]
                      if item["record_id"] == "eixarch_2023_entry_learning_curve")
        self.assertEqual(record["correction_notice_route_check_cycle290"]["mdpi_notes_http_status"], 403)

    def test_pinned_response_hashes_and_query_counts_match_receipt(self):
        receipt = json.loads((ART / "route-responses-cycle290.json").read_text(encoding="utf-8"))
        self.assertEqual(len(receipt["responses"]), 5)
        for response in receipt["responses"]:
            data = (ART / response["file"]).read_bytes()
            self.assertEqual(len(data), response["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), response["sha256"])
        for filename, count in (("03-pubmed-correction-search.xml", "0"),
                                ("05-pubmed-correction-title-search.xml", "0")):
            xml = ET.parse(ART / filename).getroot()
            self.assertEqual(xml.findtext("Count"), count)


if __name__ == "__main__":
    unittest.main()

