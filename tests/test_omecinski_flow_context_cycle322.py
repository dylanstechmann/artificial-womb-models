from __future__ import annotations

import json
import unittest
from pathlib import Path

from wombmodels.observations import validate_dataset


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "config" / "observations" / "omecinski_2023_invitro_gas_exchange_candidate.json"


class OmecinskiFlowContextCycle322Tests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    def test_source_reported_flow_summary_retains_value_uncertainty_and_scope(self):
        dataset = validate_dataset(self.data)
        record = next(item for item in dataset["observations"]
                      if item["record_id"] == "omecinski2023-preemieox-blood-flow-context")
        summary = record["observation"]["summary_statistic"]
        self.assertEqual((summary["estimate"], summary["plus_minus"], summary["plus_minus_type"],
                          summary["reported_sample_size"]),
                         (163, 2, "not_reported", 9))
        self.assertEqual(record["assay"]["measurement_role"], "environmental_condition")
        self.assertIn("individually identified", summary["sample_size_scope"])

    def test_flow_context_is_not_joined_to_aggregate_gas_removal(self):
        dataset = validate_dataset(self.data)
        self.assertEqual(dataset["measurement_pairs"], [])
        flow = next(item for item in dataset["observations"]
                    if item["record_id"] == "omecinski2023-preemieox-blood-flow-context")
        vco2 = next(item for item in dataset["observations"]
                    if item["record_id"] == "omecinski2023-preemieox-vco2-aggregate")
        self.assertNotEqual(flow["record_id"], vco2["record_id"])
        self.assertIsNone(flow["independent_unit"]["id"])
        self.assertIsNone(vco2["independent_unit"]["id"])

    def test_all_summaries_remain_aggregate_and_unpaired(self):
        self.assertEqual(len(self.data["observations"]), 5)
        self.assertTrue(all(item["observation"]["replicate_role"] == "summary_only"
                            for item in self.data["observations"][:4]))
        self.assertEqual(self.data["observations"][4]["observation"]["replicate_role"], "not_reported")
        self.assertEqual(self.data.get("measurement_pairs", []), [])


if __name__ == "__main__":
    unittest.main()
