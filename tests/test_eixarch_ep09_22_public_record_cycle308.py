import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle308"
DATA = ROOT / "config/observations/eixarch_2026_neonatal_transition_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchEP0922PublicRecordCycle308Tests(unittest.TestCase):
    def test_crossref_identifies_poster_entry_and_empty_relations(self):
        assessment = json.loads((ART / "public-record-screen-cycle308.json").read_text(encoding="utf-8"))
        snapshot = json.loads((ART / "crossref-response.json").read_text(encoding="utf-8"))["message"]
        self.assertEqual(snapshot["DOI"], "10.1002/uog.70305_731")
        self.assertEqual(snapshot["page"], "257-257")
        self.assertEqual(snapshot["relation"], {})
        self.assertEqual(hashlib.sha256((ART / "crossref-response.json").read_bytes()).hexdigest(), assessment["searches"]["crossref"]["sha256"])

    def test_public_record_searches_are_scoped_and_access_limit_is_explicit(self):
        assessment = json.loads((ART / "public-record-screen-cycle308.json").read_text(encoding="utf-8"))
        for key in ("pubmed_exact_doi", "pubmed_exact_title", "europepmc_exact_doi", "datacite_exact_doi", "zenodo_exact_doi", "figshare_exact_doi", "osf_title"):
            self.assertEqual(assessment["searches"][key]["count"], 0)
        self.assertEqual(assessment["searches"]["wiley_doi_route"]["http_status"], 403)
        self.assertIn("do not establish the absence", assessment["interpretation_limit"])

    def test_four_case_candidate_is_unchanged_and_not_expanded(self):
        assessment = json.loads((ART / "public-record-screen-cycle308.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(DATA.read_bytes()).hexdigest(), assessment["candidate"]["sha256"])
        self.assertFalse(assessment["candidate"]["changed"])
        self.assertEqual(assessment["candidate_changes"]["observations_added"], 0)
        self.assertEqual(assessment["candidate_changes"]["transitions_added"], 0)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        rec = next(r for r in inventory["records"] if r["record_id"] == "eixarch_2026_isuog_neonatal_transition_EP09_22")
        self.assertEqual(rec["public_record_screen_cycle308"]["wiley_doi_page_http_status"], 403)


if __name__ == "__main__":
    unittest.main()
