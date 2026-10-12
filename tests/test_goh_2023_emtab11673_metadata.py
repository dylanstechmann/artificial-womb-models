import csv
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/early_exchange_transition_2026.json"
SDRF = ROOT / "artifacts/early-exchange-transition-2026-10-09/E-MTAB-11673.sdrf.txt"
CROSSWALK = ROOT / "config/source_inventories/goh_2023_emtab11673_sample_crosswalk.csv"
PREVIOUS_CROSSWALK = ROOT / "config/source_inventories/goh_2023_emtab10552_sdrf_crosswalk.csv"


class Goh2023EMTAB11673MetadataTests(unittest.TestCase):
    def test_file_rows_collapse_to_six_stage_and_tissue_labeled_samples(self):
        with SDRF.open(encoding="utf-8-sig", newline="") as stream:
            source_rows = list(csv.DictReader(stream, delimiter="\t"))
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            crosswalk_rows = list(csv.DictReader(stream))
        grouped = defaultdict(list)
        for row in source_rows:
            grouped[row["Comment[ENA_SAMPLE]"]].append(row)

        self.assertEqual(len(source_rows), 18)
        self.assertEqual(len(grouped), 6)
        self.assertEqual(len(crosswalk_rows), 6)
        self.assertEqual(Counter(map(len, grouped.values())), Counter({3: 6}))
        self.assertEqual(
            {row["sampling_site"] for row in crosswalk_rows},
            {"yolk sac", "yolk sac stalk"},
        )
        self.assertEqual(
            Counter(row["sampling_site"] for row in crosswalk_rows),
            Counter({"yolk sac": 4, "yolk sac stalk": 2}),
        )
        self.assertEqual({row["individual_source_label"] for row in crosswalk_rows}, {"F158"})
        self.assertEqual({row["embryo_stage"] for row in crosswalk_rows}, {"Carnegie stage 17"})
        self.assertEqual({row["sex"] for row in crosswalk_rows}, {"female"})

        crosswalk_by_sample = {row["ena_sample"]: row for row in crosswalk_rows}
        for sample_id, rows in grouped.items():
            self.assertEqual(len({row["Comment[ENA_RUN]"] for row in rows}), 1)
            self.assertEqual(len({row["Characteristics[sampling site]"] for row in rows}), 1)
            crosswalk = crosswalk_by_sample[sample_id]
            self.assertEqual(crosswalk["sdrf_file_row_count"], "3")
            self.assertEqual(crosswalk["ena_run"], rows[0]["Comment[ENA_RUN]"])
            self.assertEqual(
                crosswalk["submitted_file_names"].split(" | "),
                [row["Comment[SUBMITTED_FILE_NAME]"] for row in rows],
            )
        excluded = crosswalk_by_sample["ERS11881168"]
        self.assertEqual(excluded["source_name"], "WS_wEMB12142156")
        self.assertIn("excluded from downstream analysis", excluded["source_described_analysis_note"])

        with PREVIOUS_CROSSWALK.open(encoding="utf-8", newline="") as stream:
            previous_ids = {row["Comment[ENA_SAMPLE]"] for row in csv.DictReader(stream)}
        self.assertTrue(previous_ids.isdisjoint(crosswalk_by_sample))

    def test_inventory_records_distinct_stage_and_source_hashes(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(row for row in inventory["sources"]
                      if row["source_id"] == "goh-2023-yolk-sac-reference")
        intake = source["additional_accession_intakes"][0]
        self.assertEqual(intake["accession"], "E-MTAB-11673")
        self.assertEqual(intake["unique_sample_records"], 6)
        self.assertEqual(intake["sdrf_file_rows"], 18)
        self.assertEqual(intake["file_inventory"]["total_files"], 9)
        self.assertFalse(intake["file_inventory"]["linked_ena_raw_data_access_inspected"])
        for declaration in intake["retrieval_snapshots"]:
            path = ROOT / declaration["path"]
            self.assertEqual(path.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])
        crosswalk = ROOT / intake["local_crosswalk"]["path"]
        self.assertEqual(crosswalk.stat().st_size, intake["local_crosswalk"]["bytes"])
        self.assertEqual(hashlib.sha256(crosswalk.read_bytes()).hexdigest(),
                         intake["local_crosswalk"]["sha256"])


if __name__ == "__main__":
    unittest.main()
