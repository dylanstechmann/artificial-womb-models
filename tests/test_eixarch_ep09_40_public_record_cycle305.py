import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle305"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
DATA = ROOT / "config/observations/eixarch_2026_ep09_40_hpa_candidate.json"


class EixarchEP0940PublicRecordCycle305Tests(unittest.TestCase):
    def test_scoped_exact_search_results_and_publisher_route_are_preserved(self):
        assessment = json.loads((ART / "public-record-screen-cycle305.json").read_text(encoding="utf-8"))
        searches = assessment["searches"]
        self.assertEqual(searches["pubmed_exact_doi"]["count"], 0)
        self.assertEqual(searches["pubmed_exact_title"]["count"], 0)
        self.assertEqual(searches["europe_pmc_exact_doi"]["hit_count"], 0)
        self.assertEqual(searches["datacite_exact_doi"]["total"], 0)
        self.assertEqual(searches["zenodo_exact_doi"]["total"], 0)
        self.assertEqual(searches["figshare_exact_doi"]["match_count"], 0)
        self.assertEqual(searches["osf_title"]["result_count"], 0)
        self.assertEqual(searches["wiley_publisher_page"]["http_status"], 403)

    def test_screen_is_bounded_not_a_global_absence_claim(self):
        assessment = json.loads((ART / "public-record-screen-cycle305.json").read_text(encoding="utf-8"))
        self.assertIn("cannot establish", assessment["interpretation_limit"])
        self.assertIn("poster PDF remains", assessment["result"])
        self.assertEqual(assessment["crossref"]["relation"], {})

    def test_no_candidate_or_transition_changes_and_inventory_records_screen(self):
        assessment = json.loads((ART / "public-record-screen-cycle305.json").read_text(encoding="utf-8"))
        cycle304 = json.loads((ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle304/hpa-intake-and-linkage-cycle304.json").read_text(encoding="utf-8"))
        current_hash = hashlib.sha256(DATA.read_bytes()).hexdigest()
        self.assertEqual(current_hash, cycle304["candidate_intake"]["sha256"])
        self.assertEqual(assessment["candidate_changes"]["observations_added"], 0)
        self.assertEqual(assessment["candidate_changes"]["transitions_added"], 0)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(r for r in inventory["records"] if r["record_id"] == "eixarch_2026_isuog_hpa_dynamics_EP09_40")
        self.assertEqual(record["public_record_screen_cycle305"]["wiley_doi_page_http_status"], 403)
        self.assertIn("no global absence", record["public_record_screen_cycle305"]["interpretation"])
        self.assertFalse(assessment["author_contacted"])


if __name__ == "__main__":
    unittest.main()
