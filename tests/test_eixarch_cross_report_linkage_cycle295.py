import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle295/phase-linkage-assessment-cycle295.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
CANDIDATE_2023 = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
CANDIDATE_2025 = ROOT / "config/observations/eixarch_2025_fetalife_abstract_candidate.json"


class EixarchCrossReportLinkageCycle295Tests(unittest.TestCase):
    def test_shared_stage_and_project_phase_do_not_create_a_cohort_join(self):
        assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        overlap = assessment["observed_overlap"]
        self.assertEqual(overlap["species"], "ovine in both")
        self.assertIn("within both", overlap["gestational_stage"])
        linkage = assessment["linkage_assessment"]
        self.assertEqual(linkage["record_level_linkage"], "not reported")
        self.assertEqual(linkage["cohort_overlap_status"], "unresolved; source phase labels suggest a later project phase but do not establish independent animal membership")
        self.assertFalse(linkage["source_count_changed"])
        self.assertFalse(linkage["transition_added"])

    def test_inventory_keeps_28_animals_and_12_experiments_as_different_units(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        rows = [r for r in inventory["records"] if r["record_id"] in {"eixarch_2023_entry_learning_curve", "eixarch_2025_fetalife_conference_abstract"}]
        self.assertEqual(len(rows), 2)
        for row in rows:
            relation = row["cross_report_cohort_linkage_cycle295"]
            self.assertEqual(relation["cohort_overlap_status"], "unresolved; do not claim samples are disjoint or identical")
            self.assertFalse(relation["counts_may_be_summed"])
            self.assertEqual(relation["transitions_added"], 0)
        old = next(r for r in rows if r["record_id"] == "eixarch_2023_entry_learning_curve")
        new = next(r for r in rows if r["record_id"] == "eixarch_2025_fetalife_conference_abstract")
        self.assertEqual(old["cohort_size"], {"value":28,"basis":"reported transfers into the AP system"})
        self.assertEqual(new["cohort_size"], {"value":12,"basis":"reported experiments"})

    def test_candidate_datasets_remain_unjoined_and_unchanged_in_count(self):
        old = json.loads(CANDIDATE_2023.read_text(encoding="utf-8"))
        new = json.loads(CANDIDATE_2025.read_text(encoding="utf-8"))
        self.assertEqual(len(old["observations"]), 50)
        self.assertEqual(len(new["observations"]), 18)
        self.assertEqual(old.get("transitions", []), [])
        self.assertEqual(new.get("transitions", []), [])
        self.assertEqual(old["source_revision"]["review_status"], "candidate")
        self.assertEqual(new["source_revision"]["review_status"], "candidate")


if __name__ == "__main__":
    unittest.main()
