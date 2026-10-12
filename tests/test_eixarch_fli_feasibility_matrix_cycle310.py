import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle310"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchFLIFeasibilityMatrixCycle310Tests(unittest.TestCase):
    def test_four_sources_keep_distinct_denominators_and_candidate_hashes(self):
        with (ART / "four-poster-feasibility-coverage-cycle310.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r["poster"] for r in rows], ["EP09.20", "EP09.31", "EP09.40", "EP09.22"])
        self.assertIn("n=20", rows[0]["cohort_frame"])
        self.assertIn("biochemical endpoint", rows[1]["denominator_limit"])
        self.assertIn("n=16", rows[2]["cohort_frame"])
        self.assertIn("Four selected", rows[3]["cohort_frame"])
        for row in rows:
            self.assertEqual(hashlib.sha256((ROOT / row["candidate_path"]).read_bytes()).hexdigest(), row["candidate_sha256"])

    def test_matrix_retains_transition_and_time_summary_limits(self):
        with (ART / "four-poster-feasibility-coverage-cycle310.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        ep0922 = next(r for r in rows if r["poster"] == "EP09.22")
        ep0940 = next(r for r in rows if r["poster"] == "EP09.40")
        self.assertIn("2 Yes/2 No", ep0922["domains"])
        self.assertIn("9/24/8/7", ep0922["denominator_limit"])
        self.assertIn("PRE (0 h)", ep0940["intake"])
        self.assertIn("No per-timepoint n", ep0940["denominator_limit"])

    def test_ranked_gaps_and_no_pooling_gate_are_explicit(self):
        assessment = json.loads((ART / "integrated-evidence-gap-assessment-cycle310.json").read_text(encoding="utf-8"))
        with (ART / "data-gap-priority-cycle310.csv").open(encoding="utf-8", newline="") as f:
            gaps = list(csv.DictReader(f))
        self.assertEqual([int(r["rank"]) for r in gaps], [1, 2, 3, 4, 5, 6])
        self.assertFalse(assessment["same_unit_transition_link_established"])
        self.assertFalse(assessment["count_pooling_allowed"])
        self.assertIn("do not pool", " ".join(assessment["cross_poster_rules"]))
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertFalse(inventory["four_poster_feasibility_coverage_cycle310"]["count_pooling_allowed"])


if __name__ == "__main__":
    unittest.main()
