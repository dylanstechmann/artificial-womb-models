import csv
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle313"
SCHEMA = ROOT / "schemas/developmental-observation.schema.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchFLIFunctionalOverlayCycle313Tests(unittest.TestCase):
    def test_overlay_covers_every_candidate_row_and_pins_each_source(self):
        assessment = json.loads((ART / "functional-classification-overlay-cycle313.json").read_text(encoding="utf-8"))
        with (ART / "poster-row-functional-classification-overlay-cycle313.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 51)
        self.assertEqual(len({row["record_id"] for row in rows}), 51)
        for source in assessment["candidate_sources"]:
            candidate_path = ROOT / source["candidate_path"]
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            self.assertEqual(hashlib.sha256(candidate_path.read_bytes()).hexdigest(), source["candidate_sha256"])
            overlay_rows = [row for row in rows if row["poster_code"] == source["poster"]]
            self.assertEqual({row["record_id"] for row in overlay_rows},
                             {item["record_id"] for item in candidate["observations"]})
            self.assertTrue(all(row["candidate_sha256"] == source["candidate_sha256"] for row in overlay_rows))
            self.assertTrue(all(row["source_locator"] for row in overlay_rows))
            self.assertTrue(all("functional_evidence_class" not in item["assay"]
                                for item in candidate["observations"]))

    def test_classes_match_schema_and_distinguish_response_from_outcome(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        allowed = set(schema["properties"]["assay"]["properties"]["functional_evidence_class"]["enum"])
        with (ART / "poster-row-functional-classification-overlay-cycle313.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertTrue(all(row["functional_evidence_class"] in allowed for row in rows))
        counts = Counter(row["functional_evidence_class"] for row in rows)
        self.assertEqual(counts, {
            "biological_response_proxy": 29,
            "developmental_outcome": 18,
            "other": 4,
        })
        self.assertTrue(all(row["functional_evidence_class"] != "direct_function_measurement" for row in rows))
        durations = [row for row in rows if "fli-support-duration" in row["record_id"]]
        self.assertEqual(len(durations), 4)
        self.assertTrue(all(row["functional_evidence_class"] == "other" for row in durations))

    def test_inventory_and_assessment_keep_overlay_provisional(self):
        assessment = json.loads((ART / "functional-classification-overlay-cycle313.json").read_text(encoding="utf-8"))
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        entry = inventory["fli_poster_row_classification_overlay_cycle313"]
        self.assertEqual(assessment["overlay_rows"], entry["row_count"])
        self.assertFalse(assessment["candidate_records_modified"])
        self.assertFalse(assessment["candidate_classifications_applied"])
        self.assertFalse(entry["unit_counts_pooled"])
        self.assertEqual(assessment["human_review"], "pending")
        self.assertFalse(assessment["author_contacted"])


if __name__ == "__main__":
    unittest.main()
