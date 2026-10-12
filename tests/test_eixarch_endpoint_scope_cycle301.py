import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle301"
DATA = ROOT / "config/observations/eixarch_2026_neonatal_transition_candidate.json"


class EixarchEndpointScopeCycle301Tests(unittest.TestCase):
    def test_extubation_count_is_bounded_to_four_listed_cases(self):
        d = json.loads((ART / "endpoint-scope-assessment-cycle301.json").read_text(encoding="utf-8"))
        c = d["case_table_reconciliation"]
        self.assertEqual((c["successful_extubation_yes"], c["successful_extubation_no"]), (2, 2))
        self.assertEqual(c["successful_extubation_fraction_in_listed_cases"]["denominator"], 4)
        self.assertIn("not an all-FLI-start rate", c["successful_extubation_fraction_in_listed_cases"]["interpretation"])
        self.assertIn("not necessarily a direct contradiction", c["narrative_table_relationship"].lower())

    def test_long_follow_up_is_one_case_and_one_qualitative_domain(self):
        d = json.loads((ART / "endpoint-scope-assessment-cycle301.json").read_text(encoding="utf-8"))
        f = d["developmental_follow_up"]
        self.assertEqual(f["cases_with_reported_13_month_survival"], 1)
        self.assertEqual(f["maze_assessed_cases"], 1)
        self.assertEqual(f["age_at_maze_months"], 3)
        self.assertEqual(f["control_group_n"], "not reported")
        self.assertIn("Comprehensive normal development", f["not_supported"])

    def test_candidate_keeps_source_values_but_narrows_limitation(self):
        d = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(len(d["observations"]), 20)
        self.assertTrue(any("do not equate satisfactory monitored parameters with extubation" in x for x in d["limitations"]))
        self.assertFalse(any("conflicts with the table’s no-successful-extubation" in x for x in d["limitations"]))
        self.assertEqual(hashlib.sha256((ROOT / "artifacts/fetal-ovine-transition-2026-10-10/ep09-22-poster.pdf").read_bytes()).hexdigest(), d["artifacts"][0]["sha256"])
        before = json.loads((ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle298/validate-2026/input_dataset.json").read_text(encoding="utf-8"))
        self.assertEqual(d["observations"], before["observations"])


if __name__ == "__main__":
    unittest.main()
