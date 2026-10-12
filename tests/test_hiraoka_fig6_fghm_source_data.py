import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/hiraoka_2025_maternal_interface_candidate.json"
INVENTORY = ROOT / "config/source_inventories/hiraoka_maternal_interface_2025.json"


EXPECTED = {
    "6f": {
        "dmso": [0.9181055880638681, 1.4470436221947, 0.6236623099422208, 1.0111884797992108],
        "celecoxib": [0.18680162508686757, 0.3377963575347662, 0.37566051834516173],
    },
    "6g": {
        "dmso": [0.859019, 1.244936, 0.798355, 1.097691],
        "celecoxib": [0.523485, 0.901387, 0.580831],
    },
    "6h": {
        "dmso": [1.086850772357901, 1.1819922148026596, 0.7943893279128957, 0.936767684926543],
        "celecoxib": [0.3628744396633889, 0.38108653803386233, 0.6576970142955942],
    },
}

EXPECTED_RAW = {
    "6f": {
        "dmso": [178.96998596191406, 282.07798767089844, 121.57298278808594, 197.11500549316406],
        "celecoxib": [36.41398620605469, 65.84799194335938, 73.22900390625],
    },
    "6g": {
        "dmso": [155.08399963378906, 224.75599670410156, 144.13198852539062, 198.17300415039062],
        "celecoxib": [94.50799560546875, 162.73300170898438, 104.86099243164062],
    },
    "6h": {
        "dmso": [1.1540196692407256, 1.2550409858129974, 0.8434836987395713, 0.9946612372267231],
        "celecoxib": [0.38530058724415034, 0.4046382187499707, 0.6983436090783551],
    },
}

EXPECTED_6M = {
    "dmso": [7.88279, 8.77392, 6.32079, 9.86653, 15.5704, 8.63682],
    "mk2206-10um": [1.34369, 1.02173, 1.00562, 0.5235330078125, 0.71615296875, 2.10294, 0.973856015625],
}


class HiraokaFigure6FGHMSourceDataTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.audit = self.inventory["source_mapping_audit"]["fig6_ijk_source_data"]
        self.observations = self.dataset["observations"]
        self.coverage = self.dataset["cohort_coverage"]

    def test_normalized_molecular_values_and_raw_pairs_are_preserved_once(self):
        panels = {panel["panel"].lower(): panel for panel in self.audit["direct_measurement_panels"]}
        for panel, groups in EXPECTED.items():
            panel_audit = panels[panel]
            for slug, expected_values in groups.items():
                group = next(item for item in panel_audit["groups"] if item["condition_slug"] == slug)
                records = [item for item in self.observations
                           if item["record_id"].startswith(f"hiraoka-fig6-{panel[1:]}-{slug}-")]
                records.sort(key=lambda item: int(item["record_id"].rsplit("embryo", 1)[1]))
                self.assertEqual([item["observation"]["value"] for item in records], expected_values)
                self.assertEqual(group["normalized_source_values"], expected_values)
                self.assertEqual(group["raw_source_values"], EXPECTED_RAW[panel][slug])
                self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                    and item["independent_unit"]["id"] is None
                                    and item["independent_unit"]["parent_id"] is None
                                    for item in records))
                self.assertEqual(len(records), group["caption_biologically_independent_n"])
                self.assertEqual(len(group["paired_values"]), len(records))
                coverage_id = f"hiraoka-fig6-{panel[1:]}-{slug}-coverage"
                coverage = next(item for item in self.coverage if item["coverage_id"] == coverage_id)
                self.assertEqual(coverage["denominator"]["value"], len(records))

                raw = EXPECTED_RAW[panel][slug]
                if panel in ("6f", "6g"):
                    reference_raw_mean = sum(EXPECTED_RAW[panel]["dmso"]) / len(EXPECTED_RAW[panel]["dmso"])
                    for normalized, raw_value in zip(expected_values, raw):
                        self.assertAlmostEqual(raw_value / reference_raw_mean, normalized, delta=1.1e-6)
                else:
                    reference_raw_mean = sum(EXPECTED_RAW[panel]["dmso"]) / len(EXPECTED_RAW[panel]["dmso"])
                    for normalized, raw_value in zip(expected_values, raw):
                        self.assertAlmostEqual(raw_value / reference_raw_mean, normalized, delta=1.1e-12)

        self.assertEqual(self.audit["source_observation_rows_added"], 34)
        self.assertIn("no p-values recalculated", self.audit["statistical_annotations_added"]["6M"].lower())

    def test_6m_values_unit_and_n_a_are_kept_as_separate_source_states(self):
        audit = self.audit["invasion_volume_panel_6M"]
        self.assertEqual(audit["source_unit"], "1E+05μm^3")
        for slug, values in EXPECTED_6M.items():
            records = [item for item in self.observations
                       if item["record_id"].startswith(f"hiraoka-fig6-m-{slug}-")]
            records.sort(key=lambda item: int(item["record_id"].rsplit("embryo", 1)[1]))
            self.assertEqual([item["observation"]["value"] for item in records], values)
            self.assertTrue(all(item["assay"]["unit"] == audit["source_unit"] for item in records))
            self.assertTrue(all(item["independent_unit"]["kind"] == "embryo"
                                and item["independent_unit"]["id"] is None for item in records))

        self.assertEqual(sum(len(values) for values in EXPECTED_6M.values()), 13)
        self.assertEqual(audit["nonnumeric_source_cells"], [{
            "cell": "D2", "row_label": "Embryo 1", "group": "MK-2206 (100 μM)",
            "source_value": "N/A", "numeric_observation_created": False,
        }])
        unavailable = next(item for item in self.coverage
                           if item["coverage_id"] == "hiraoka-fig6-m-mk2206-100um-unavailable-coverage")
        self.assertIsNone(unavailable["denominator"]["value"])
        self.assertEqual(unavailable["denominator"]["value_status"], "not_reported")
        self.assertFalse(any(item["record_id"].startswith("hiraoka-fig6-m-mk2206-100um-")
                             for item in self.observations))
        self.assertIn("report a sample-size n", audit["narrative_qualification"])

    def test_panel_caption_counts_test_annotations_and_no_linkage_are_recorded(self):
        self.assertEqual(self.audit["curated_sheets"], ["6F", "6G", "6H", "6I", "6J", "6K", "6M"])
        self.assertEqual(self.audit["unreviewed_sheets"], [])
        self.assertEqual(len([item for item in self.observations
                              if item["record_id"].startswith(("hiraoka-fig6-f-", "hiraoka-fig6-g-",
                                                                "hiraoka-fig6-h-", "hiraoka-fig6-m-"))]), 34)
        self.assertIn("two-tailed unpaired student t-test",
                      self.audit["statistical_annotations_added"]["6F-6H"].lower())
        self.assertIn("same-numbered", self.audit["cross_panel_limit"].lower())
        self.assertIn("no p-values recalculated", self.audit["statistical_annotations_added"]["6M"].lower())


if __name__ == "__main__":
    unittest.main()
