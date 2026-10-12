import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle300"


class EixarchPosterSubsetCycle300Tests(unittest.TestCase):
    def test_case_values_fit_reported_duration_and_gestational_frames_conditionally(self):
        d = json.loads((ART / "poster-cohort-compatibility-cycle300.json").read_text(encoding="utf-8"))
        c = d["conditional_compatibility"]
        self.assertTrue(c["all_ep09_22_gas_fit_ge_115_stratum_if_same_cohort"])
        self.assertTrue(c["all_ep09_22_durations_meet_ep09_31_ge_6_day_criterion_if_same_duration_definition"])
        self.assertTrue(c["even_if_unverified_24_to_14_hypothesis_used_still_meets_criterion"])
        self.assertEqual(c["ep09_31_ga_strata"]["sum"], c["ep09_31_study_model_count"])

    def test_eligibility_compatibility_does_not_create_a_join_or_rate(self):
        d = json.loads((ART / "poster-cohort-compatibility-cycle300.json").read_text(encoding="utf-8"))
        a = d["linkage_assessment"]
        self.assertEqual(a["shared_animal_or_experiment_key"], "not reported")
        self.assertFalse(a["identity_established"])
        self.assertFalse(a["transition_rate_calculable"])
        self.assertFalse(a["counts_may_be_summed"])
        self.assertEqual(a["candidate_changes"]["transitions_added"], 0)

    def test_source_pdf_hashes_match_pinned_records(self):
        d = json.loads((ART / "poster-cohort-compatibility-cycle300.json").read_text(encoding="utf-8"))
        for item in d["source_surfaces"]:
            p = ROOT / item["pdf_path"]
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), item["pdf_sha256"])

    def test_cycle300_receipt_preserves_its_candidate_hash_snapshot(self):
        d = json.loads((ART / "poster-cohort-compatibility-cycle300.json").read_text(encoding="utf-8"))
        receipt = json.loads((ART / "cycle300-receipt.json").read_text(encoding="utf-8"))
        self.assertFalse(d["candidate_records"]["changed"])
        self.assertEqual(
            d["candidate_records"]["sha256"],
            {key: value["sha256"] for key, value in receipt["candidate_files"].items()},
        )
        self.assertEqual(d["candidate_records"]["observation_counts"], {"ep09_22": 20, "ep09_31": 14})


if __name__ == "__main__":
    unittest.main()
