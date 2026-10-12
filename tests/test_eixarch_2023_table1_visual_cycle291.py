import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle291"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2023Table1VisualCycle291Tests(unittest.TestCase):
    def test_publisher_table_cells_and_footnote_scope_are_preserved(self):
        assessment = json.loads((ART / "table1-visual-assessment-cycle291.json").read_text(encoding="utf-8"))
        text = (ART / "publisher-page5-text-cycle291.txt").read_text(encoding="utf-8")
        flat = re.sub(r"\s+", " ", text)
        self.assertIn("1 (14.3%)", flat)
        self.assertIn("4 (57.1%)", flat)
        self.assertIn("Complications after 24 h survival #", flat)
        self.assertIn("Only in fetuses with >24 h survival.", flat)
        self.assertEqual(assessment["visual_findings"]["bubbles_middle_group_printed_cell"], "1 (14.3%)")
        self.assertEqual(assessment["visual_findings"]["vasospasm_middle_group_printed_cell"], "4 (57.1%)")
        self.assertFalse(assessment["visual_findings"]["specific_footnote_marker_on_these_cells"])
        self.assertEqual(assessment["denominator_resolution"], "unresolved")
        self.assertFalse(assessment["candidate_observation_values_changed"])

    def test_pdf_render_hash_and_inventory_are_bound(self):
        assessment = json.loads((ART / "table1-visual-assessment-cycle291.json").read_text(encoding="utf-8"))
        image = ROOT / assessment["render_path"]
        self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), assessment["render_sha256"])
        pdf = ROOT / assessment["source_pdf_path"]
        self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), assessment["source_pdf_sha256"])
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        self.assertEqual(len(candidate["observations"]), 50)
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(x for x in inventory["records"]
                      if x["record_id"] == "eixarch_2023_entry_learning_curve")
        self.assertEqual(record["table1_visual_denominator_check_cycle291"]["render_sha256"],
                         assessment["render_sha256"])


if __name__ == "__main__":
    unittest.main()

