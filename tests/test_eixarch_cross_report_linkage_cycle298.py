import hashlib
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle298"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
D2025 = ROOT / "config/observations/eixarch_2025_fetalife_abstract_candidate.json"
D2026 = ROOT / "config/observations/eixarch_2026_neonatal_transition_candidate.json"


def mean_sd(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
    return mean, sd


class EixarchCrossReportLinkageCycle298Tests(unittest.TestCase):
    def test_2025_2026_linkage_stays_possible_but_unverified(self):
        assessment = json.loads((ART / "cross-report-linkage-assessment-cycle298.json").read_text(encoding="utf-8"))
        relation = assessment["identity_boundary"]
        self.assertTrue(relation["possible_partial_overlap_or_follow_up"])
        self.assertEqual(relation["record_level_linkage"], "not reported")
        self.assertEqual(relation["independent_replication_status"], "not established")
        self.assertEqual(relation["cohort_overlap_status"], "unresolved; source similarities make overlap plausible, while source conflicts prevent a verified mapping")
        self.assertEqual(assessment["candidate_changes"]["transitions_added"], 0)
        self.assertFalse(relation["counts_may_be_summed"])

    def test_close_group_means_have_different_reported_frames(self):
        assessment = json.loads((ART / "cross-report-linkage-assessment-cycle298.json").read_text(encoding="utf-8"))
        source25, source26 = assessment["sources"]
        self.assertEqual((source25["survival_mean_days"], source25["survival_sd_days"]), (9.5, 3.3))
        self.assertEqual((source26["poster_group_support_mean_days"], source26["poster_group_support_sd_days"]), (9.6, 3.1))
        self.assertEqual(source25["reported_experiments"], 12)
        self.assertEqual(source26["transition_cases"], 4)
        self.assertEqual(source26["FLI_start_denominator"], "not reported")

    def test_poster_table_and_summary_discrepancies_are_preserved(self):
        assessment = json.loads((ART / "cross-report-linkage-assessment-cycle298.json").read_text(encoding="utf-8"))
        arith = assessment["poster_internal_arithmetic"]
        self.assertEqual(mean_sd([9, 24, 8, 7]), (12.0, arith["table_support_duration_summary"]["sample_sd"]))
        self.assertAlmostEqual(arith["table_support_duration_summary"]["sample_sd"], 8.0415587212, places=8)
        self.assertEqual(mean_sd([123, 125, 126, 129]), (125.75, 2.5))
        self.assertEqual(mean_sd([9, 14, 8, 7]), (9.5, arith["conditional_animal2_24_to_14_substitution"]["summary"]["sample_sd"]))
        self.assertEqual(arith["conditional_animal2_24_to_14_substitution"]["status"], "unverified hypothesis only; do not replace source value")

    def test_source_pdf_and_candidates_remain_source_pinned_and_unjoined(self):
        assessment = json.loads((ART / "cross-report-linkage-assessment-cycle298.json").read_text(encoding="utf-8"))
        pdf = ROOT / "artifacts/fetal-ovine-transition-2026-10-10/ep09-22-poster.pdf"
        self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), assessment["poster_visual_check"]["source_pdf_sha256"])
        self.assertEqual(assessment["poster_visual_check"]["source_pdf_sha256"], "b12a66778648322b6f937d190cfc7d59ecadfc782339d78aeb9bf986c60526f2")
        d25 = json.loads(D2025.read_text(encoding="utf-8"))
        d26 = json.loads(D2026.read_text(encoding="utf-8"))
        self.assertEqual(len(d25["observations"]), 18)
        self.assertEqual(len(d26["observations"]), 20)
        self.assertEqual(d25.get("transitions", []), [])
        self.assertEqual(d26.get("transitions", []), [])
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        paired = [r for r in inventory["records"] if r["record_id"] in {"eixarch_2025_fetalife_conference_abstract", "eixarch_2026_isuog_neonatal_transition_EP09_22"}]
        self.assertEqual(len(paired), 2)
        self.assertTrue(all(r["cross_report_cohort_linkage_cycle298"]["transitions_added"] == 0 for r in paired))


if __name__ == "__main__":
    unittest.main()
