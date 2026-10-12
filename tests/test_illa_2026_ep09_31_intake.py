import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.observations import observation_report, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/illa_2026_ep09_31_metabolic_growth_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Illa2026EP0931IntakeTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))

    def test_numeric_plot_summaries_keep_source_range_and_denominator_qualifications(self):
        validated = validate_dataset(self.dataset)
        observations = validated["observations"]
        self.assertEqual(len(observations), 14)
        self.assertEqual(len(validated["cohort_coverage"]), 3)

        values = {
            (row["assay"]["endpoint"], row["observation"]["measurement_time"]): row
            for row in observations
            if row["assay"]["endpoint"] != "Fetal growth velocity"
        }
        self.assertEqual(values[("total bilirubin", "Baseline")]["observation"]["value"], 0.45)
        self.assertEqual(values[("total bilirubin", "Days 6-7")]["observation"]["value"], 4.80)
        self.assertIn("0.30-0.70", values[("total bilirubin", "Baseline")]
                      ["observation"]["measurement_uncertainty"])
        self.assertEqual(values[("total bilirubin", "Baseline")]["observation"]
                         ["source_qualifications"][0]["status_code"], "range_type_not_reported")

        growth = {
            row["developmental_interval"]["label"]: row for row in observations
            if row["assay"]["endpoint"] == "Fetal growth velocity"
        }
        self.assertEqual(len(growth), 2)
        self.assertEqual(
            {row["observation"]["value"] for row in growth.values()}, {66.7, 35.1}
        )
        self.assertEqual(
            {row["observation"]["source_qualifications"][0]["reference_value"]
             for row in growth.values()}, {0.186}
        )
        coverage_by_id = {row["coverage_id"]: row for row in validated["cohort_coverage"]}
        self.assertEqual(coverage_by_id["ep09-31-biochemistry-assessment-denominator"]
                         ["denominator"]["value_status"], "not_reported")
        self.assertEqual(
            {coverage_by_id[key]["denominator"]["value"]
             for key in ("ep09-31-growth-under-115-days", "ep09-31-growth-at-least-115-days")},
            {5, 24},
        )

    def test_receipt_and_inventory_keep_one_pinned_source_and_no_inferred_transitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt = observation_report(DATASET, Path(temp_dir) / "intake")
            report = json.loads((Path(temp_dir) / "intake" / "observation_intake_report.json")
                                .read_text(encoding="utf-8"))
        self.assertEqual(receipt["bundle_kind"], "developmental_observation_intake")
        self.assertEqual(report["n_observation_records"], 14)
        self.assertEqual(report["n_transitions"], 0)
        self.assertEqual(report["n_cohort_coverage_records"], 3)

        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["records"]
            if row["record_id"] == "illa_2026_isuog_metabolic_growth_EP09_31"
        )
        self.assertEqual(source["visual_source_review"]["status"],
                         "completed_official_pdf_rendered_and_visually_inspected")
        self.assertEqual(source["machine_readable_candidate_intake"]["record_count"], 14)
        self.assertEqual(source["artifact_snapshot"]["sha256"], self.dataset["artifacts"][0]["sha256"])


if __name__ == "__main__":
    unittest.main()
