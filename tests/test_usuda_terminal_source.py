import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report
from wombmodels.usuda_source import (
    SOURCE_PATH, audit_usuda_terminal, extract_terminal,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / SOURCE_PATH


class UsudaTerminalSourceTests(unittest.TestCase):
    def test_published_morphology_retains_neutral_and_adverse_findings(self):
        cells, dataset = extract_terminal(SOURCE.read_bytes())
        self.assertEqual(len(cells), 60)
        table1 = {(row["source_endpoint_literal"], row["group"]): row
                  for row in cells if row["table_id"] == "T1"}
        expected = {
            "Body weight (necropsy) (g)": ("1,356 ± 179", "1,323 ± 116"),
            "Brain weight (g)": ("28.2 ± 2.6", "29.0 ± 1.2"),
            "Heart weight (g)": ("8.8 ± 1.9", "6.9 ± 1.5"),
            "Lung weight (g)": ("45.7 ± 6.6", "37.0 ± 4.0*"),
            "Liver weight (g)": ("75.25 ± 13.1", "53.0 ± 4.5*"),
            "Kidney weight (g)": ("12.9 ± 1.7", "9.5 ± 2.2*"),
        }
        for endpoint, literals in expected.items():
            for group, literal in zip(("control", "apt"), literals):
                self.assertEqual(table1[endpoint, group]["source_summary_literal"], literal)
        # Source bone units are retained, even if they warrant scientific review.
        self.assertEqual(table1["Humerus length gain (cm)", "apt"]["reported_unit"], "cm")
        self.assertEqual(dataset["source_revision"]["review_status"], "candidate")

    def test_group_summaries_never_create_individual_or_cross_endpoint_links(self):
        _, dataset = extract_terminal(SOURCE.read_bytes())
        self.assertEqual(dataset["transitions"], [])
        self.assertEqual(dataset["measurement_pairs"], [])
        for row in dataset["observations"]:
            self.assertIsNone(row["independent_unit"]["id"])
            self.assertEqual(row["observation"]["replicate_role"], "summary_only")
            self.assertIsNone(row["observation"]["measurement_time"])
            self.assertIsNone(row["developmental_interval"]["start"])
            self.assertIsNone(row["developmental_interval"]["end"])
        self.assertTrue(any("abstract says six" in text for text in dataset["limitations"]))

    def test_missing_control_and_mixed_uncertainty_are_preserved(self):
        _, dataset = extract_terminal(SOURCE.read_bytes())
        by_id = {row["record_id"]: row for row in dataset["observations"]}
        missing = by_id["usuda2023-t3-row19-control"]["observation"]
        self.assertIsNone(missing["value"])
        self.assertNotIn("summary_statistic", missing)
        self.assertIn("dash", missing["missingness_reason"])
        calcium = by_id["usuda2023-t3-row15-apt"]["observation"]
        self.assertEqual(calcium["value"], 8.6)
        self.assertEqual(calcium["summary_statistic"]["kind"], "median_iqr")
        self.assertEqual(calcium["summary_statistic"]["lower_quartile"], 7.7)
        igf = by_id["usuda2023-t3-row13-apt"]["observation"]
        self.assertEqual(igf["summary_statistic"]["kind"], "mean_sd")
        self.assertEqual(igf["summary_statistic"]["standard_deviation"], 7)
        self.assertEqual(igf["summary_statistic"]["reported_sample_size"], 6)

    def test_hash_failure_does_not_publish_output(self):
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "changed.xml"
            changed.write_bytes(SOURCE.read_bytes() + b"\n")
            output = Path(folder) / "output"
            with self.assertRaisesRegex(InputError, "size/hash"):
                audit_usuda_terminal(changed, output)
            self.assertFalse(output.exists())

    def test_audit_and_real_intake_verify_and_keep_all_sixty_cells(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "audit"
            audit_usuda_terminal(SOURCE, output)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
            plan = json.loads((output / "reproduction_plan.json").read_text(encoding="utf-8"))
            self.assertIn("python -m wombmodels.usuda_source", plan["command"])
            self.assertIn("external pinned JATS XML (not bundled)", plan["inputs"])
            with (output / "reported_mean_comparisons.csv").open(encoding="utf-8", newline="") as stream:
                comparisons = {row["endpoint_literal"]: row for row in csv.DictReader(stream)}
            self.assertAlmostEqual(float(comparisons["Liver weight (g)"]["apt_over_control_mean"]), 53 / 75.25)
            self.assertGreater(float(comparisons["Brain weight (g)"]["apt_over_control_mean"]), 1)
            validated = Path(folder) / "validated"
            observation_report(output / "input_dataset.json", validated, source_root=ROOT)
            self.assertTrue(verify_bundle(validated, strict=True)["bytes_verified"])
            dataset = json.loads((validated / "input_dataset.json").read_text(encoding="utf-8"))
            self.assertEqual(len(dataset["observations"]), 60)
            self.assertEqual(sum(row["observation"]["value"] is None for row in dataset["observations"]), 1)
            with self.assertRaises(InputError):
                audit_usuda_terminal(SOURCE, output)


if __name__ == "__main__":
    unittest.main()
