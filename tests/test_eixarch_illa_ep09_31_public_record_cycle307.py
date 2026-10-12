import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle307"
DATA = ROOT / "config/observations/illa_2026_ep09_31_metabolic_growth_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class IllaEP0931PublicRecordCycle307Tests(unittest.TestCase):
    def test_crossref_metadata_and_relations_are_pinned(self):
        assessment = json.loads((ART / "public-record-screen-cycle307.json").read_text(encoding="utf-8"))
        snapshot = json.loads((ART / "crossref-response.json").read_text(encoding="utf-8"))["message"]
        self.assertEqual(snapshot["DOI"], "10.1002/uog.70305_739")
        self.assertEqual(snapshot["page"], "259-259")
        self.assertEqual(snapshot["relation"], {})
        self.assertEqual(hashlib.sha256((ART / "crossref-response.json").read_bytes()).hexdigest(), assessment["crossref_record"]["sha256"])

    def test_exact_index_and_repository_searches_are_bounded(self):
        assessment = json.loads((ART / "public-record-screen-cycle307.json").read_text(encoding="utf-8"))
        searches = assessment["searches"]
        for key in ("pubmed_exact_doi", "pubmed_exact_title", "europepmc_exact_doi", "datacite_exact_doi", "zenodo_exact_doi", "figshare_exact_doi", "osf_title"):
            self.assertEqual(searches[key]["count"], 0)
        self.assertEqual(searches["wiley_doi_route"]["http_status"], 403)
        self.assertIn("cannot prove absence", assessment["interpretation_limit"])

    def test_candidate_and_inventory_remain_source_specific(self):
        assessment = json.loads((ART / "public-record-screen-cycle307.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(DATA.read_bytes()).hexdigest(), assessment["candidate"]["sha256"])
        self.assertFalse(assessment["candidate"]["changed"])
        self.assertEqual(assessment["candidate_changes"]["observations_added"], 0)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(r for r in inventory["records"] if r["record_id"] == "illa_2026_isuog_metabolic_growth_EP09_31")
        self.assertEqual(record["public_record_screen_cycle307"]["wiley_doi_page_http_status"], 403)
        self.assertEqual(record["cohort_size"]["value"], 29)


if __name__ == "__main__":
    unittest.main()
