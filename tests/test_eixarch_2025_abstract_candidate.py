import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "config/observations/eixarch_2025_fetalife_abstract_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2025AbstractCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.records = {r["record_id"]: r for r in cls.dataset["observations"]}

    def test_only_abstract_aggregate_values_are_intaken(self):
        self.assertEqual(len(self.records), 18)
        self.assertEqual(len(self.dataset["cohort_coverage"]), 3)
        self.assertEqual(self.dataset["transitions"], [])
        self.assertTrue(all(r["evidence_status"] == "author_reported_summary" for r in self.records.values()))
        self.assertTrue(all(r["observation"]["replicate_role"] == "summary_only" for r in self.records.values()))
        self.assertTrue(all(r["independent_unit"]["id"] is None for r in self.records.values()))
        self.assertEqual(self.dataset["source_revision"]["review_status"], "candidate")

    def test_reported_summary_literals_and_pH_dispersion_are_preserved(self):
        expected = {
            "eixarch2025-mean-survival": (9.5, 3.3),
            "eixarch2025-flow-0-7": (171.7, 44.5),
            "eixarch2025-flow-7-10": (135.07, 60.9),
            "eixarch2025-flow-10-14": (105.7, 54.4),
            "eixarch2025-ph-0-7": (7.36, 0.49),
            "eixarch2025-ph-7-10": (7.39, 0.07),
            "eixarch2025-ph-10-14": (7.38, 0.09),
            "eixarch2025-lactate-0-7": (2.7, 3.3),
            "eixarch2025-lactate-7-10": (1.4, 2.0),
            "eixarch2025-lactate-10-14": (2.4, 3.2),
        }
        for rid, (mean, sd) in expected.items():
            self.assertEqual(self.records[rid]["observation"]["value"], mean)
            self.assertEqual(self.records[rid]["observation"]["measurement_uncertainty"], sd)
        self.assertIn("publisher typography", " ".join(self.records["eixarch2025-ph-0-7"]["limitations"]))

    def test_methods_experiments_are_not_used_as_animal_outcome_denominators(self):
        coverages = {c["coverage_id"]: c for c in self.dataset["cohort_coverage"]}
        methods = coverages["eixarch2025-methods-experiment-count"]
        self.assertEqual(methods["denominator"]["value"], 12)
        self.assertEqual(methods["counted_entity_label"], "experiment (Methods wording; not equated to one animal)")
        for cid in ("eixarch2025-survival-threshold-denominators", "eixarch2025-discontinuation-cause-denominators"):
            self.assertIsNone(coverages[cid]["denominator"]["value"])
            self.assertEqual(coverages[cid]["denominator"]["value_status"], "not_reported")
        record = next(x for x in self.inventory["records"] if x["record_id"] == "eixarch_2025_fetalife_conference_abstract")
        reconciliation = record["percentage_count_reconciliation"]
        self.assertEqual(reconciliation["methods_reported_experiment_count"], 12)
        self.assertIsNone(reconciliation["outcome_denominator"])

    def test_official_source_byte_hash_is_unclaimed(self):
        self.assertIsNone(self.dataset["artifacts"][0]["sha256"])
        self.assertTrue(all(r["source"]["sha256"] is None for r in self.records.values()))
        self.assertIn("direct local publisher", " ".join(self.dataset["limitations"]).lower())

    def test_cycle297_percentages_do_not_uniquely_identify_outcome_denominators(self):
        path = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle297/percent-denominator-ambiguity-cycle297.json"
        audit = json.loads(path.read_text(encoding="utf-8"))
        examples = audit["survival_thresholds"]["common_arithmetic_denominator_examples"]
        self.assertEqual([x["denominator"] for x in examples], [12, 24])
        self.assertEqual([x["rounded_percentages"] for x in examples], [[75, 50, 17], [75, 50, 17]])
        causes = audit["discontinuation_causes"]["arithmetic_examples_not_joined_to_survival_denominator"]
        self.assertEqual([x["rounded_percentages"] for x in causes], [[58, 25], [58, 25]])
        coverage = {c["coverage_id"]: c for c in self.dataset["cohort_coverage"]}
        self.assertIsNone(coverage["eixarch2025-survival-threshold-denominators"]["denominator"]["value"])
        self.assertIsNone(coverage["eixarch2025-discontinuation-cause-denominators"]["denominator"]["value"])
        self.assertFalse(audit["candidate_dataset_changed"])

    def test_cycle296_pdf_route_errors_are_not_treated_as_source_bytes(self):
        route_file = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle296/publisher-pdf-route-probes-cycle296.json"
        routes = json.loads(route_file.read_text(encoding="utf-8"))["routes"]
        self.assertEqual(len(routes), 4)
        self.assertTrue(all(route["http_status"] == 403 and not route["pdf_magic"] for route in routes))
        self.assertTrue(all(route["saved_as"].endswith(".html") for route in routes))
        self.assertIsNone(self.dataset["artifacts"][0]["sha256"])

    def test_2023_cohort_candidate_remains_separate_and_unmodified_in_count(self):
        old = json.loads((ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json").read_text(encoding="utf-8"))
        self.assertEqual(len(old["observations"]), 50)
        self.assertEqual(old["source_revision"]["review_status"], "candidate")


if __name__ == "__main__":
    unittest.main()

