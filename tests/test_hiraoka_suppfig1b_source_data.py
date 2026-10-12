import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


class HiraokaSupplementaryFig1BSourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.observations = {
            item["record_id"]: item for item in self.dataset["observations"]
            if item["record_id"].startswith("hiraoka-suppfig1b-")
        }
        self.audit = self.inventory["source_mapping_audit"]["fig1b_source_data"]

    def test_publisher_workbook_is_hash_pinned_and_curated_scope_is_bounded(self):
        source = next(item for item in self.dataset["artifacts"]
                      if item["artifact_id"] == "hiraoka2025-suppfig1-source-data")
        snapshot = next(item for item in self.inventory["snapshots"]
                        if item["path"].endswith("source-data-suppfig1.xlsx"))
        self.assertEqual(source["sha256"], "f34b1385968afa5039fb14a35face0da30ec71ef79754a1aeeaa517b3fbff097")
        self.assertEqual(snapshot["sha256"], source["sha256"])
        self.assertEqual(snapshot["bytes"], 17937)
        self.assertEqual(self.audit["curated_sheets"], ["1B", "1C", "1D", "1E", "1F", "1G"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])

    def test_all_30_recipient_level_formula_rows_preserve_counts_and_anonymous_identity(self):
        expected_counts = {
            "open": 4, "ceiling-50um": 4, "ceiling-250um": 3, "ceiling-750um": 3,
            "bottom-750um-inverted": 5, "ceiling-1500um": 3,
            "bottom-750um-upright": 5, "glass": 3,
        }
        self.assertEqual(len(self.observations), 30)
        source_id = "hiraoka2025-suppfig1-source-data"
        by_group = {group: [] for group in expected_counts}
        for record_id, item in self.observations.items():
            match = re.fullmatch(r"hiraoka-suppfig1b-(.+)-exp\d+", record_id)
            self.assertIsNotNone(match)
            slug = match.group(1)
            by_group[slug].append(item)
            self.assertEqual(item["source"]["artifact_id"], source_id)
            self.assertEqual(item["independent_unit"]["kind"], "pregnant_animal")
            self.assertIsNone(item["independent_unit"]["id"])
            self.assertEqual(item["observation"]["replicate_role"], "independent")
            basis = item["assay"]["functional_context"]["quantity_basis"]
            formula = re.search(r"formula (=\d+/\d+)", basis)
            self.assertIsNotNone(formula)
            numerator, denominator = map(int, formula.group(1)[1:].split("/"))
            self.assertGreater(denominator, 0)
            self.assertAlmostEqual(item["observation"]["value"], numerator / denominator, places=12)
            locator = item["assay"]["functional_context"]["source_locator"]
            self.assertRegex(locator, r"sheet 1B cell [B-I][2-6];")
            self.assertIn("not an animal ID", basis)

        self.assertEqual({key: len(value) for key, value in by_group.items()}, expected_counts)
        self.assertEqual(self.audit["source_observation_rows"], 30)

    def test_unweighted_recipient_means_reconcile_article_text_without_pooling_embryos(self):
        summaries = {item["condition_slug"]: item for item in self.audit["group_summaries"]}
        for slug, records in self._records_by_group().items():
            values = [record["observation"]["value"] for record in records]
            summary = summaries[slug]
            self.assertEqual(summary["recipient_mouse_n"], len(values))
            calculated_mean = sum(values) / len(values) * 100
            self.assertAlmostEqual(calculated_mean, summary["mean_of_recipient_fractions_percent"], places=6)
        comparison = self.inventory["source_mapping_audit"]["pdms_ceiling_thickness_comparison"]["source_data_reconciliation"]
        self.assertEqual(comparison["per_recipient_source_formulas"]["750_um"], ["2/2", "5/5", "7/8"])
        self.assertEqual(comparison["per_recipient_source_formulas"]["1500_um"], ["12/12", "17/18", "18/20"])
        self.assertAlmostEqual(comparison["unweighted_mean_percent_recomputed"]["750_um"], 95.8, places=1)
        self.assertAlmostEqual(comparison["unweighted_mean_percent_recomputed"]["1500_um"], 94.8, places=1)
        self.assertNotEqual(comparison["unweighted_mean_percent_recomputed"]["750_um"],
                            comparison["embryo_weighted_ratio_percent_diagnostic_only"]["750_um"])
        self.assertIn("No p-value", comparison["interpretation"])
        self.assertIn("No cross-condition pairing", comparison["identity_limit"])

    def test_suppfig1c_keeps_four_anonymous_recipient_rates_per_group(self):
        audit = self.inventory["source_mapping_audit"]["fig1c_source_data"]
        self.assertEqual(audit["source_observation_rows"], 8)
        self.assertEqual(audit["reported_comparison"]["figure_annotation"], "P=0.8532 (ns)")
        self.assertIn("not an equivalence test", audit["interpretation_limit"])
        expected = {
            "autologous": ("Autologous", ["=3/4", "=2/2", "=1/1", "=8/8"], 93.75, 6.25),
            "allogenic": ("Allogenic", ["=2/2", "=8/8", "=4/5", "=8/9"], 92.222222, 4.843221),
        }
        for slug, (label, formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-suppfig1c-{slug}-")]
            self.assertEqual(len(records), 4)
            self.assertTrue(all(item["independent_unit"]["id"] is None for item in records))
            self.assertTrue(all(item["observation"]["replicate_role"] == "independent" for item in records))
            source_formulas = [
                re.search(r"formula (=\d+/\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(source_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            summary = next(item for item in audit["groups"] if item["condition"] == label)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)

        coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}
        self.assertIn("hiraoka-suppfig1c-autologous-coverage", coverage_ids)
        self.assertIn("hiraoka-suppfig1c-allogenic-coverage", coverage_ids)

    def test_suppfig1d_preserves_twelve_anonymous_rates_and_source_test_annotations(self):
        audit = self.inventory["source_mapping_audit"]["fig1d_source_data"]
        self.assertEqual(audit["source_observation_rows"], 12)
        self.assertEqual(audit["reported_comparisons"]["caption_test"],
                         "Ordinary one-way ANOVA with post hoc Tukey multiple-comparisons test")
        self.assertEqual(
            [item["annotation"] for item in audit["reported_comparisons"]["figure_annotations"]],
            ["P=0.9157 (ns)", "P=0.0038", "P=0.0017"],
        )
        expected = {
            "3pg": (["=4/4", "=11/12", "=11/12"], 94.444444, 2.777778),
            "30pg": (["=17/18", "=10/12", "=13/15"], 88.148148, 3.291924),
            "300pg": (["=6/15", "=6/17", "=10/18"], 43.616558, 6.122121),
            "3ng": (["=2/4", "=7/15", "=2/15"], 36.666667, 11.706282),
        }
        for slug, (formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-suppfig1d-estrogen-{slug}-")]
            self.assertEqual(len(records), 3)
            self.assertTrue(all(item["independent_unit"]["id"] is None for item in records))
            observed_formulas = [
                re.search(r"formula (=?\d+/\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            summary = next(item for item in audit["groups"] if item["condition_slug"] == slug)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)
        coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}
        self.assertIn("hiraoka-suppfig1d-estrogen-3pg-coverage", coverage_ids)
        self.assertIn("hiraoka-suppfig1d-estrogen-3ng-coverage", coverage_ids)

    def test_suppfig1e_preserves_workbook_spelling_and_recipient_level_rates(self):
        audit = self.inventory["source_mapping_audit"]["fig1e_source_data"]
        self.assertEqual(audit["source_observation_rows"], 10)
        self.assertEqual(audit["reported_comparison"]["figure_annotation"], "P=0.0157")
        self.assertIn("Two-tailed unpaired Student t-test", audit["reported_comparison"]["caption_test"])
        self.assertIn("workbook group header is PMGS", audit["label_qualification"])
        expected = {
            "natural": ("Natural", ["=4/5", "=7/8", "=8/8"], 89.166667, 5.833333),
            "pmsg": ("PMGS", ["=8/10", "=2/3", "=4/15", "=3/5", "=1/5", "=3/7", "=2/5"],
                     48.027211, 8.231761),
        }
        for slug, (label, formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-suppfig1e-endometrium-{slug}-")]
            self.assertEqual(len(records), len(formulas))
            self.assertTrue(all(item["independent_unit"]["id"] is None for item in records))
            observed_formulas = [
                re.search(r"formula (=?\d+/\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            summary = next(item for item in audit["groups"] if item["condition_slug"] == slug)
            self.assertEqual(summary["condition"], label)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)
        pmsg_records = [item for item in self.dataset["observations"]
                        if item["record_id"].startswith("hiraoka-suppfig1e-endometrium-pmsg-")]
        self.assertTrue(all("Workbook header PMGS; figure/caption PMSG" in item["assay"]["functional_context"]["quantity_basis"]
                            for item in pmsg_records))
        coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}
        self.assertIn("hiraoka-suppfig1e-endometrium-natural-coverage", coverage_ids)
        self.assertIn("hiraoka-suppfig1e-endometrium-pmsg-coverage", coverage_ids)

    def test_suppfig1f_preserves_workbook_spelling_and_unpaired_test_annotation(self):
        audit = self.inventory["source_mapping_audit"]["fig1f_source_data"]
        self.assertEqual(audit["source_observation_rows"], 6)
        self.assertEqual(audit["reported_comparison"]["figure_annotation"], "P=0.8835 (ns)")
        self.assertIn("Two-tailed unpaired Student t-test", audit["reported_comparison"]["caption_test"])
        self.assertIn("workbook group header is PMGS", audit["label_qualification"])
        expected = {
            "natural": ("Natural", ["=8/8", "=3/3", "=3/4"], 91.666667, 8.333333),
            "pmsg": ("PMGS", ["=4/5", "=4/4", "=2/2"], 93.333333, 6.666667),
        }
        for slug, (label, formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-suppfig1f-embryo-{slug}-")]
            self.assertEqual(len(records), 3)
            self.assertTrue(all(item["independent_unit"]["id"] is None for item in records))
            observed_formulas = [
                re.search(r"formula (=?\d+/\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            summary = next(item for item in audit["groups"] if item["condition_slug"] == slug)
            self.assertEqual(summary["condition"], label)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)
        coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}
        self.assertIn("hiraoka-suppfig1f-embryo-natural-coverage", coverage_ids)
        self.assertIn("hiraoka-suppfig1f-embryo-pmsg-coverage", coverage_ids)

    def test_suppfig1g_preserves_six_rates_per_hatch_condition(self):
        audit = self.inventory["source_mapping_audit"]["fig1g_source_data"]
        self.assertEqual(audit["source_observation_rows"], 12)
        self.assertEqual(audit["reported_comparison"]["figure_annotation"], "P=0.3560 (ns)")
        self.assertIn("Two-tailed unpaired Student t-test", audit["reported_comparison"]["caption_test"])
        expected = {
            "naturally-hatched": (
                ["=5/5", "=12/13", "=26/26", "=7/7", "=3/3", "=19/20"],
                97.884615, 1.382299,
            ),
            "at-hatched": (
                ["=9/9", "=13/15", "=24/26", "=3/3", "=2/2", "=13/14"],
                95.30525, 2.278345,
            ),
        }
        for slug, (formulas, mean_percent, sem_pp) in expected.items():
            records = [item for item in self.dataset["observations"]
                       if item["record_id"].startswith(f"hiraoka-suppfig1g-hatching-{slug}-")]
            self.assertEqual(len(records), 6)
            self.assertTrue(all(item["independent_unit"]["id"] is None for item in records))
            observed_formulas = [
                re.search(r"formula (=?\d+/\d+)", item["assay"]["functional_context"]["quantity_basis"]).group(1)
                for item in records
            ]
            self.assertEqual(observed_formulas, formulas)
            values = [item["observation"]["value"] for item in records]
            self.assertAlmostEqual(sum(values) / len(values) * 100, mean_percent, places=5)
            summary = next(item for item in audit["groups"] if item["condition_slug"] == slug)
            self.assertAlmostEqual(summary["mean_of_recipient_fractions_percent"], mean_percent, places=5)
            self.assertAlmostEqual(summary["sample_sem_percentage_points"], sem_pp, places=5)
        coverage_ids = {item["coverage_id"] for item in self.dataset["cohort_coverage"]}
        self.assertIn("hiraoka-suppfig1g-hatching-naturally-hatched-coverage", coverage_ids)
        self.assertIn("hiraoka-suppfig1g-hatching-at-hatched-coverage", coverage_ids)

    def _records_by_group(self):
        groups = {}
        for record_id, item in self.observations.items():
            slug = re.fullmatch(r"hiraoka-suppfig1b-(.+)-exp\d+", record_id).group(1)
            groups.setdefault(slug, []).append(item)
        return groups


if __name__ == "__main__":
    unittest.main()
