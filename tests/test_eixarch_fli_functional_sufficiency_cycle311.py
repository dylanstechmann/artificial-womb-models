import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle311"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchFLIFunctionalSufficiencyCycle311Tests(unittest.TestCase):
    def test_matrix_is_source_pinned_and_keeps_function_classes_separate(self):
        with (ART / "functional-claim-evidence-matrix-cycle311.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["claim_family"], "Net exchange and clearance")
        self.assertEqual(rows[2]["claim_family"], "Interface barrier")
        self.assertEqual(rows[3]["evidence_class"], "direct_biomarker_measurement")
        self.assertEqual(rows[4]["evidence_class"], "direct_biomarker_measurement")
        for row in rows:
            paths = row["candidate_path"].split("|")
            hashes = row["candidate_sha256"].split("|")
            self.assertEqual(len(paths), len(hashes))
            for path, expected in zip(paths, hashes):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_assessment_does_not_upgrade_proxies_to_function_or_pool_counts(self):
        assessment = json.loads((ART / "functional-evidence-sufficiency-cycle311.json").read_text(encoding="utf-8"))
        self.assertFalse(assessment["assessment"]["direct_exchange_flux_demonstrated"])
        self.assertFalse(assessment["assessment"]["interface_barrier_integrity_demonstrated"])
        self.assertFalse(assessment["assessment"]["same_unit_link_across_the_four_posters_established"])
        self.assertFalse(assessment["assessment"]["poster_counts_pooled"])
        self.assertEqual([g["rank"] for g in assessment["ranked_intake_gaps"]], [1, 2, 3, 4, 5])
        self.assertTrue(any("concentration" in item for item in assessment["guardrails"]))
        self.assertFalse(assessment["author_contacted"])

    def test_inventory_points_to_this_source_bounded_assessment(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = inventory["four_poster_functional_evidence_sufficiency_cycle311"]
        self.assertEqual(record["poster_codes"], ["EP09.20", "EP09.22", "EP09.31", "EP09.40"])
        self.assertFalse(record["direct_exchange_flux_demonstrated_in_this_poster_set"])
        self.assertFalse(record["same_unit_support_to_transition_link_established"])


if __name__ == "__main__":
    unittest.main()
