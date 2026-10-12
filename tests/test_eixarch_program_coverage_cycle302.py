import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle302"
class EixarchProgramCoverageCycle302Tests(unittest.TestCase):
 def test_source_counts_remain_distinct_and_unpooled(self):
  d=json.loads((ART/"program-coverage-cycle302.json").read_text(encoding="utf-8")); by={x["record_id"]:x for x in d["sources"]}
  self.assertIn("28 transfers",by["eixarch_2023_entry_learning_curve"]["count"])
  self.assertIn("12 experiments",by["eixarch_2025_fetalife_conference_abstract"]["count"])
  self.assertIn("29 selected",by["illa_2026_isuog_metabolic_growth_EP09_31"]["count"])
  self.assertIn("4 displayed",by["eixarch_2026_isuog_neonatal_transition_EP09_22"]["count"])
  self.assertFalse(d["continuity_boundary"]["counts_may_be_summed"])
  self.assertFalse(d["continuity_boundary"]["continuous_gestation_or_life_history_demonstrated"])
 def test_only_ep09_22_supplies_post_support_transition_coverage(self):
  d=json.loads((ART/"program-coverage-cycle302.json").read_text(encoding="utf-8"))
  rows=[x["record_id"] for x in d["sources"] if x["transition_to_neonatal"] != "not reported"]
  self.assertEqual(rows,["eixarch_2026_isuog_neonatal_transition_EP09_22"])
  self.assertEqual(d["phase_coverage"][3]["coverage_in_these_sources"],"2026 EP09.22 only; four selected cases")
 def test_long_term_claim_is_one_case_and_not_comprehensive(self):
  d=json.loads((ART/"program-coverage-cycle302.json").read_text(encoding="utf-8"))
  self.assertIn("one EP09.22 case to 13 months",d["phase_coverage"][4]["coverage_in_these_sources"])
  self.assertIn("do not establish a broad healthy developmental outcome",d["phase_coverage"][4]["qualification"])
 def test_matrix_does_not_claim_embryo_to_birth_continuity(self):
  d=json.loads((ART/"program-coverage-cycle302.json").read_text(encoding="utf-8"))
  self.assertFalse(d["continuity_boundary"]["human_embryo_or_human_birth_outcomes_included"])
  self.assertEqual(d["phase_coverage"][0]["coverage_in_these_sources"],"none")
  self.assertFalse(d["data_changes"]["candidate_numeric_values_changed"])
  self.assertEqual(d["data_changes"]["transitions_added"],0)
if __name__=="__main__":unittest.main()
