import csv
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/source_inventories/early_exchange_transition_2026.json"
SDRF = ROOT / "artifacts/early-exchange-transition-2026-10-09/E-MTAB-10552.sdrf.txt"
CROSSWALK = ROOT / "config/source_inventories/goh_2023_emtab10552_sdrf_crosswalk.csv"


class Goh2023EMTAB10552MetadataTests(unittest.TestCase):
    def test_sdrf_crosswalk_preserves_stage_and_three_individual_labels(self):
        with SDRF.open(encoding="utf-8-sig", newline="") as stream:
            source_rows = list(csv.DictReader(stream, delimiter="\t"))
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            crosswalk_rows = list(csv.DictReader(stream))

        self.assertEqual(len(source_rows), 22)
        self.assertEqual(len(crosswalk_rows), 22)
        self.assertEqual(
            [row["Comment[ENA_SAMPLE]"] for row in source_rows],
            [row["Comment[ENA_SAMPLE]"] for row in crosswalk_rows],
        )
        self.assertEqual(len({row["Comment[ENA_SAMPLE]"] for row in crosswalk_rows}), 22)
        self.assertEqual(len({row["Comment[BioSD_SAMPLE]"] for row in crosswalk_rows}), 22)
        self.assertEqual(len({row["Comment[ENA_RUN]"] for row in crosswalk_rows}), 22)
        self.assertEqual(
            Counter(row["Characteristics[individual]"] for row in crosswalk_rows),
            Counter({"F61": 10, "F79": 7, "F80": 5}),
        )
        self.assertEqual(
            Counter(row["Characteristics[embryo stage]"] for row in crosswalk_rows),
            Counter({"carnegie stage 18": 22}),
        )
        self.assertEqual(
            Counter(row["Characteristics[organism part]"] for row in crosswalk_rows),
            Counter({"yolk sac": 18, "liver": 4}),
        )

    def test_inventory_hashes_and_file_counts_match_public_snapshots(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(row for row in inventory["sources"]
                      if row["source_id"] == "goh-2023-yolk-sac-reference")
        intake = source["repository_intake"]
        self.assertEqual(intake["sample_metadata_rows"], 22)
        self.assertEqual(intake["file_inventory"], {
            "total_files": 75,
            "raw_data_files": 66,
            "processed_data_files": 7,
            "mage_tab_files": 2,
            "downloaded_for_this_intake": [
                "API study metadata JSON", "API info JSON", "SDRF metadata text"
            ],
            "raw_sequence_or_processed_expression_files_downloaded": False,
        })
        snapshots = [
            ROOT / row["path"] for row in intake["retrieval_snapshots"]
        ]
        for snapshot, declaration in zip(snapshots, intake["retrieval_snapshots"]):
            self.assertEqual(snapshot.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                             declaration["sha256"])
        crosswalk = ROOT / intake["local_crosswalk"]["path"]
        self.assertEqual(crosswalk.stat().st_size, intake["local_crosswalk"]["bytes"])
        self.assertEqual(hashlib.sha256(crosswalk.read_bytes()).hexdigest(),
                         intake["local_crosswalk"]["sha256"])


if __name__ == "__main__":
    unittest.main()
