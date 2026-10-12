import csv
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle315"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
SCHEMA = ROOT / "schemas/developmental-observation.schema.json"


class Eixarch2023FunctionalClassificationCycle315Tests(unittest.TestCase):
    def test_overlay_covers_source_records_and_pins_candidate_and_primary_pdf(self):
        assessment = json.loads((ART / "functional-evidence-assessment-cycle315.json").read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        with (ART / "eixarch2023-row-functional-classification-overlay-cycle315.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 50)
        self.assertEqual({row["record_id"] for row in rows}, {row["record_id"] for row in candidate["observations"]})
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), assessment["candidate_sha256"])
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), rows[0]["candidate_sha256"])
        pdf = next(item for item in candidate["artifacts"] if item["artifact_id"] == "eixarch2023-publisher-pdf")
        pdf_path = ROOT / pdf["local_path"]
        self.assertEqual(hashlib.sha256(pdf_path.read_bytes()).hexdigest(), assessment["primary_pdf_sha256"])
        self.assertTrue(all(row["source_locator"] for row in rows))
        self.assertTrue(all("functional_evidence_class" not in item["assay"] for item in candidate["observations"]))

    def test_classes_preserve_flow_vs_response_vs_outcome_and_context(self):
        with (ART / "eixarch2023-row-functional-classification-overlay-cycle315.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        counts = Counter(row["functional_evidence_class"] for row in rows)
        self.assertEqual(counts, {
            "direct_function_measurement": 6,
            "biological_response_proxy": 18,
            "developmental_outcome": 11,
            "other": 15,
        })
        direct = [row for row in rows if row["functional_evidence_class"] == "direct_function_measurement"]
        self.assertEqual(len(direct), 6)
        self.assertTrue(all("Circuit flow" in row["endpoint"] for row in direct))
        self.assertTrue(all(row["reported_unit"] == "mL/kg/min" for row in direct))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        allowed = set(schema["properties"]["assay"]["properties"]["functional_evidence_class"]["enum"])
        self.assertTrue(all(row["functional_evidence_class"] in allowed for row in rows))
        rationale = " ".join(row["classification_rationale"] for row in direct)
        self.assertIn("not net exchange", rationale)
        self.assertIn("oxygen", rationale)

    def test_goal_band_denominators_remain_distinct_and_not_endpoint_n(self):
        assessment = json.loads((ART / "functional-evidence-assessment-cycle315.json").read_text(encoding="utf-8"))
        self.assertEqual([row["denominator"] for row in assessment["cohort_coverage_groups"]], [8, 10, 10])
        self.assertTrue(all(row["endpoint_specific_n"] == "not assigned from goal-band cohort n"
                            for row in assessment["cohort_coverage_groups"]))
        self.assertFalse(assessment["cohort_counts_pooled"])
        self.assertFalse(assessment["candidate_records_modified"])
        self.assertFalse(assessment["candidate_classes_applied"])
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(inventory["eixarch_2023_functional_classification_overlay_cycle315"]["rows"], 50)


if __name__ == "__main__":
    unittest.main()
