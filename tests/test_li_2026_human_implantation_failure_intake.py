import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/li_2026_human_implantation_failure.json"
RECEIPT = ROOT / "artifacts/implantation-failure-model-2026-10-11/li-implantation-failure-route-and-supplement-screen-cycle194.json"


class LiHumanImplantationFailureIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_article_identity_and_review_depth_are_explicit(self):
        article = self.inventory["article"]
        self.assertEqual(article["doi"], "10.1016/j.cell.2025.10.026")
        self.assertEqual(article["pmid"], "41443192")
        self.assertEqual(article["source_review_depth"], "PubMed abstract and publisher-hosted supplemental workbook only; full article not reviewed")
        self.assertEqual(self.inventory["human_review"], "pending")

    def test_supplement_group_headers_are_not_assay_denominators(self):
        supplement = self.inventory["supplement_review"]
        self.assertEqual(supplement["declared_group_headers"], {"Ctrl": 18, "RIF": 40})
        self.assertEqual(supplement["sequence_labeled_columns"], 58)
        self.assertIn("not treated as implantation-assay sample sizes", supplement["qualification"])
        self.assertFalse(self.receipt["publisher_supplement"]["participant_level_values_transcribed"])

    def test_public_route_results_are_bounded_and_no_data_claim_is_overstated(self):
        routes = self.inventory["data_routes"]
        self.assertEqual(routes["biostudies_exact_title_and_doi_hits"], 0)
        self.assertEqual(routes["geo_exact_title_and_pmid_hits"], 0)
        self.assertIn("do not prove", routes["search_scope_qualification"])
        self.assertTrue(routes["publisher_supplement_directly_retrievable"])

    def test_no_observations_or_clinical_inference_are_promoted(self):
        self.assertEqual(self.inventory["observation_intake"]["observation_records_promoted"], 0)
        self.assertFalse(self.receipt["intake_decision"]["clinical_inference_made"])
        self.assertFalse(self.receipt["intake_decision"]["complete_gestation_or_birth_evidence"])
        self.assertFalse(self.inventory["feasibility_boundary"]["authors_contacted"])


if __name__ == "__main__":
    unittest.main()
