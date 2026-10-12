import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle312"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class EixarchFLIFunctionalSchemaCycle312Tests(unittest.TestCase):
    def test_review_aid_pins_candidates_and_does_not_rewrite_them(self):
        assessment = json.loads((ART / "functional-evidence-classification-intake-cycle312.json").read_text(encoding="utf-8"))
        self.assertEqual(len(assessment["poster_review_aid"]), 5)
        for item in assessment["poster_review_aid"]:
            digest = hashlib.sha256((ROOT / item["candidate"]).read_bytes()).hexdigest()
            self.assertEqual(digest, item["candidate_sha256"])
        self.assertFalse(assessment["candidate_observations_changed"])
        self.assertFalse(assessment["author_contacted"])

    def test_schema_field_is_optional_and_inventory_marks_no_inference(self):
        schema = json.loads((ROOT / "schemas/developmental-observation.schema.json").read_text(encoding="utf-8"))
        assay = schema["properties"]["assay"]
        self.assertNotIn("functional_evidence_class", assay["required"])
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        item = inventory["functional_evidence_class_intake_cycle312"]
        self.assertTrue(item["optional"])
        self.assertFalse(item["omission_inferred"])
        self.assertFalse(item["candidate_observations_changed"])


if __name__ == "__main__":
    unittest.main()
