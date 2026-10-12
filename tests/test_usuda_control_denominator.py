import json
import hashlib
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"
JATS = ROOT / "artifacts/usuda-2023-case-linkage-2026-10-10/PMC10484719.fullTextXML.xml"


class UsudaControlDenominatorTests(unittest.TestCase):
    def test_source_specific_counts_and_unresolved_pairing_are_preserved(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(
            item for item in inventory["records"]
            if item["record_id"] == "usuda_2023_growth_and_disposition"
        )

        self.assertEqual(record["cohort_size"]["apt"], 6)
        self.assertEqual(record["cohort_size"]["in_utero_controls_abstract"], 6)
        self.assertEqual(record["cohort_size"]["in_utero_controls_methods"], 8)
        self.assertEqual(record["cohort_size"]["in_utero_controls_table_1"], 8)
        self.assertEqual(record["cohort_size"]["in_utero_controls_tables_3_and_6"], 8)

        qualification = record["control_denominator_qualification"]
        self.assertEqual(qualification["status"], "source_discrepancy_unresolved")
        self.assertEqual(
            qualification["sex_count_text"],
            {"female": 4, "male": 3, "sex_not_recorded": 1,
             "source_locator": "Results > Physiological variables"},
        )
        self.assertIn("no public individual-ID pairing map", qualification["pairing_qualification"])
        self.assertEqual(
            [(item["n"], item["source_locator"])
             for item in qualification["reported_counts"]],
            [
                (6, "Abstract > Methods"),
                (8, "Material and methods > Experimental protocol > Intrauterine control group"),
                (8, "Table 1; Tables 3 and 6 captions"),
            ],
        )

    def test_case_level_and_terminal_outcome_coverage_are_distinguished(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(
            item for item in inventory["records"]
            if item["record_id"] == "usuda_2023_growth_and_disposition"
        )
        linkage = record["outcome_linkage"]

        self.assertEqual(linkage["shared_case_labels"], list("ABCDEF"))
        self.assertEqual(
            [item["table"] for item in linkage["case_level_source_tables"]], [4, 5]
        )
        self.assertEqual(
            [item["table"] for item in linkage["group_summary_only_tables"]], [1, 3, 6]
        )
        self.assertTrue(linkage["post_support_follow_up"].startswith("Not reported"))
        self.assertIn("no individual terminal growth", linkage["interpretation_limit"])

    def test_supplementary_screen_is_bounded_to_inspected_article_surfaces(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(
            item for item in inventory["records"]
            if item["record_id"] == "usuda_2023_growth_and_disposition"
        )
        screen = record["data_availability"]["supplementary_material_screen"]

        self.assertEqual(screen["status"], "not_identified_in_inspected_article_surfaces")
        self.assertEqual(screen["jats_supplementary_material_node_count"], 0)
        self.assertIn("does not establish", screen["scope_limit"])
        self.assertFalse(record["data_availability"]["public_repository_located"])
        snapshot = screen["jats_snapshot"]
        self.assertEqual(hashlib.sha256(JATS.read_bytes()).hexdigest(), snapshot["sha256"])
        root = ET.parse(JATS).getroot()
        supplementary_nodes = [node for node in root.iter()
                               if node.tag.split("}")[-1] == "supplementary-material"]
        self.assertEqual(len(supplementary_nodes), 0)


if __name__ == "__main__":
    unittest.main()
