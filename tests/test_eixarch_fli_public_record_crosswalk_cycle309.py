import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle309"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchFLIPublicRecordCrosswalkCycle309Tests(unittest.TestCase):
    def test_ep09_20_crossref_and_exact_queries_are_pinned(self):
        assessment = json.loads((ART / "public-record-screen-cycle309.json").read_text(encoding="utf-8"))
        message = json.loads((ART / "crossref-response.json").read_text(encoding="utf-8"))["message"]
        self.assertEqual(message["DOI"], "10.1002/uog.70305_729")
        self.assertEqual(message["page"], "256-256")
        self.assertEqual(message["relation"], {})
        self.assertEqual(hashlib.sha256((ART / "crossref-response.json").read_bytes()).hexdigest(), assessment["searches"]["crossref"]["sha256"])
        for key in ("pubmed_exact_doi", "pubmed_exact_title", "europepmc_exact_doi", "datacite_exact_doi", "zenodo_exact_doi", "figshare_exact_doi", "osf_title"):
            self.assertEqual(assessment["searches"][key]["count"], 0)

    def test_four_poster_crosswalk_preserves_candidate_hashes_and_scope(self):
        with (ART / "fli-poster-public-record-crosswalk-cycle309.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r["poster"] for r in rows], ["EP09.20", "EP09.22", "EP09.31", "EP09.40"])
        for row in rows:
            self.assertEqual(row["crossref_relations"], "empty")
            self.assertEqual(row["wiley_http_status"], "403")
            actual = hashlib.sha256((ROOT / row["candidate_path"]).read_bytes()).hexdigest()
            self.assertEqual(actual, row["candidate_sha256"])
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        summary = inventory["isuog2026_public_record_route_screen_summary_cycle309"]
        self.assertTrue(summary["crossref_relation_empty_for_all"])
        self.assertIn("no global absence claim", summary["limit"])

    def test_no_candidate_or_transition_changes(self):
        assessment = json.loads((ART / "public-record-screen-cycle309.json").read_text(encoding="utf-8"))
        self.assertFalse(assessment["candidate"]["changed"])
        self.assertEqual(assessment["candidate_changes"]["observations_added"], 0)
        self.assertEqual(assessment["candidate_changes"]["transitions_added"], 0)
        self.assertFalse(assessment["author_contacted"])


if __name__ == "__main__":
    unittest.main()
