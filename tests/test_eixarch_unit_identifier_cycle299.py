import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle299"


class EixarchUnitIdentifierCycle299Tests(unittest.TestCase):
    def test_source_records_have_no_shared_unit_key(self):
        assessment = json.loads((ART / "unit-identifier-coverage-cycle299.json").read_text(encoding="utf-8"))
        self.assertEqual(assessment["shared_unit_key"]["status"], "not found in the inspected public source surfaces")
        self.assertFalse(assessment["linkage_conclusion"]["counts_may_be_summed"])
        self.assertEqual(assessment["linkage_conclusion"]["cross_report_transitions_added"], 0)
        self.assertEqual(assessment["linkage_conclusion"]["independent_replication_status"], "not established")

    def test_poster_case_labels_are_local_not_cross_report_keys(self):
        assessment = json.loads((ART / "unit-identifier-coverage-cycle299.json").read_text(encoding="utf-8"))
        poster = assessment["sources"][2]
        self.assertIn("Animal 1–4", poster["unit_display"])
        self.assertIn("poster-local", poster["unit_key_status"].lower())
        self.assertEqual(poster["inter_report_key"], "None reported.")

    def test_2023_source_snapshot_is_exact_and_bound_to_assessment(self):
        assessment = json.loads((ART / "unit-identifier-coverage-cycle299.json").read_text(encoding="utf-8"))
        source = ART / "eixarch2023-pmc-xml-source.xml"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(digest, assessment["method"]["2023_source_sha256"])
        self.assertEqual(digest, "109cd7d7c5eba6cdc15394c65d0169991bb44c8ea71012eedbd6b9288a2f33c0")

    def test_cycle299_receipt_preserves_its_candidate_hash_snapshot(self):
        assessment = json.loads((ART / "unit-identifier-coverage-cycle299.json").read_text(encoding="utf-8"))
        receipt = json.loads((ART / "cycle299-receipt.json").read_text(encoding="utf-8"))
        self.assertFalse(assessment["candidate_records"]["changed"])
        self.assertEqual(assessment["candidate_records"]["human_review"], "pending")
        self.assertEqual(assessment["candidate_records"]["observation_counts"], {"2023": 50, "2025": 18, "2026": 20})
        self.assertEqual(
            assessment["candidate_records"]["sha256_at_screen"],
            {key: value["sha256"] for key, value in receipt["candidate_files"].items()},
        )


if __name__ == "__main__":
    unittest.main()
