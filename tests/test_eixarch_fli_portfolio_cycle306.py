import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle306"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchFLIPortfolioCycle306Tests(unittest.TestCase):
    def test_official_author_listing_covers_four_existing_fli_candidates(self):
        assessment = json.loads((ART / "fli-portfolio-screen-cycle306.json").read_text(encoding="utf-8"))
        posters = {p["code"]: p for p in assessment["fli_specific_posters"]}
        self.assertEqual(set(posters), {"EP09.20", "EP09.22", "EP09.31", "EP09.40"})
        self.assertEqual(assessment["listing_sources"]["author_page"]["displayed_result_count"], 5)
        self.assertEqual(assessment["listing_sources"]["affiliation_page"]["displayed_result_count"], 6)
        for poster in posters.values():
            self.assertTrue((ROOT / poster["candidate"]).is_file())

    def test_affiliation_filter_omission_and_adjacent_non_fli_items_are_explicit(self):
        assessment = json.loads((ART / "fli-portfolio-screen-cycle306.json").read_text(encoding="utf-8"))
        affiliation = assessment["listing_sources"]["affiliation_page"]["poster_nodes"]
        self.assertNotIn("543", affiliation)
        self.assertIn("543", assessment["listing_sources"]["author_page"]["poster_nodes"])
        adjacent = {p["code"] for p in assessment["adjacent_not_fli_specific"]}
        self.assertEqual(adjacent, {"EP09.39", "EP15.29"})
        self.assertIn("not a complete publication registry", assessment["interpretation_limit"])

    def test_listing_snapshots_and_inventory_screen_hashes_match(self):
        assessment = json.loads((ART / "fli-portfolio-screen-cycle306.json").read_text(encoding="utf-8"))
        for name, digest in assessment["page_snapshot_hashes"].items():
            self.assertEqual(hashlib.sha256((ART / name).read_bytes()).hexdigest(), digest)
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        screen = inventory["isuog2026_fli_portfolio_screen_cycle306"]
        self.assertEqual(screen["official_fli_poster_codes"], ["EP09.20", "EP09.22", "EP09.31", "EP09.40"])
        self.assertEqual(screen["new_fli_poster_candidates"], 0)
        self.assertFalse(assessment["candidate_changes"]["candidate_values_changed"])


if __name__ == "__main__":
    unittest.main()
