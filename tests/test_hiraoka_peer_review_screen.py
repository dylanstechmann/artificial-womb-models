import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaPeerReviewScreenTests(unittest.TestCase):
    def setUp(self):
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.screen = self.inventory["source_mapping_audit"]["peer_review_file"]["repeat_text_screen"]

    def test_repeat_screen_is_bound_to_the_preserved_26_page_source(self):
        peer_review = self.inventory["source_mapping_audit"]["peer_review_file"]
        self.assertEqual(peer_review["bytes"], 675055)
        self.assertEqual(
            peer_review["sha256"],
            "9dcfe7381b85d99e93c0930b2df80e2df24e9313f7a618decd37cb43b14a2d48",
        )
        self.assertEqual(peer_review["pages"], 26)
        self.assertEqual(self.screen["verified_on"], "2026-10-10")
        self.assertIn("SHA-256", self.screen["local_integrity"])

    def test_review_context_keeps_authorship_denominators_and_limits(self):
        declarations = self.screen["context_declarations"]
        by_locator = {item["source_locator"]: item for item in declarations}

        pdms = by_locator["Physical PDF pp. 6-7"]
        self.assertIn("35%", pdms["declaration"])
        self.assertIn("initial 24 hours", pdms["declaration"])
        self.assertIn("denominator", pdms["qualification"])
        self.assertIn("n=4 biologically independent recipient-mouse samples", pdms["qualification"])
        self.assertIn("not an embryo denominator", pdms["qualification"])

        duration = by_locator["Physical PDF p. 14"]
        self.assertIn("E5.5", duration["declaration"])
        self.assertIn("96 hours", duration["declaration"])
        self.assertIn("chronological conversion", duration["qualification"])

        self.assertTrue(all(item["attribution"] for item in declarations))
        self.assertTrue(all(item["qualification"] for item in declarations))

    def test_peer_review_does_not_close_the_cohort_or_withdrawal_map(self):
        unresolved = " ".join(self.screen["unresolved_mapping_questions"])
        self.assertIn("No individual embryo or recipient identity map", unresolved)
        self.assertIn("No numeric assay-withdrawal count", unresolved)
        self.assertIn("343/362, 235/279 or 55/96", unresolved)
        self.assertIn("No author contact was performed", self.screen["interpretation_limit"])
        fixed = self.inventory["source_mapping_audit"]["pdms_long_fixed_condition"]
        self.assertEqual(fixed["denominator_status"], "not_reported")
        self.assertIn("n=3", fixed["figure_n_scope"])
        self.assertIn("not for the PDMS-long-fixed", fixed["figure_n_scope"])
        thickness = self.inventory["source_mapping_audit"]["pdms_ceiling_thickness_comparison"]
        self.assertEqual(thickness["comparison"], "Article reports similar efficiencies and no statistically significant difference.")
        self.assertEqual([group["recipient_mouse_n"] for group in thickness["groups"]], [3, 3])

    def test_candidate_intake_keeps_pdms_free_group_separate_and_unit_safe(self):
        candidate = json.loads(
            (ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json")
            .read_text(encoding="utf-8")
        )
        observation = next(
            item for item in candidate["observations"]
            if item["record_id"] == "hiraoka-pdms-free-attachment24-review-context"
        )
        coverage = next(
            item for item in candidate["cohort_coverage"]
            if item["coverage_id"] == "hiraoka-pdms-free-attachment24-coverage"
        )
        self.assertEqual(observation["observation"]["value"], "~35%")
        self.assertEqual(observation["observation"]["replicate_role"], "summary_only")
        self.assertEqual(observation["independent_unit"]["kind"], "pregnant_animal")
        self.assertIsNone(observation["independent_unit"]["id"])
        self.assertEqual(coverage["denominator"]["value"], 4)
        self.assertIn("not an embryo count denominator", coverage["denominator"]["reported_label"])
        self.assertEqual(coverage["declarations"][0]["value"], "~35%")
        self.assertEqual(coverage["declarations"][0]["scope"], "unresolved")
        self.assertIn(
            "separate from the 343/362",
            coverage["selection_definition"],
        )

        fixed = next(
            item for item in candidate["observations"]
            if item["record_id"] == "hiraoka-pdms-long-fixed-72h-morphology"
        )
        fixed_coverage = next(
            item for item in candidate["cohort_coverage"]
            if item["coverage_id"] == "hiraoka-pdms-long-fixed-72h-coverage"
        )
        self.assertIn("all embryos lost morphology", fixed["observation"]["value"])
        self.assertIn("appeared dead", fixed["observation"]["value"])
        self.assertEqual(fixed["observation"]["replicate_role"], "summary_only")
        self.assertIsNone(fixed_coverage["denominator"]["value"])
        self.assertEqual(fixed_coverage["denominator"]["value_status"], "not_reported")
        self.assertIn("representative image", fixed_coverage["population_frame"])

        thickness_observations = {
            item["record_id"]: item for item in candidate["observations"]
            if item["record_id"] in {
                "hiraoka-attachment-750um-ceiling-24h",
                "hiraoka-attachment-1500um-ceiling-24h",
            }
        }
        self.assertEqual(thickness_observations["hiraoka-attachment-750um-ceiling-24h"]["observation"]["value"], "95.8%")
        self.assertEqual(thickness_observations["hiraoka-attachment-1500um-ceiling-24h"]["observation"]["value"], "94.8%")
        self.assertTrue(all(item["observation"]["measurement_uncertainty"] is None
                            for item in thickness_observations.values()))


if __name__ == "__main__":
    unittest.main()
