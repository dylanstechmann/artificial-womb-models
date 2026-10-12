import csv
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/early-exchange-transition-2026-10-11"
SDRF = ARTIFACTS / "E-MTAB-10888.sdrf.txt"
CROSSWALK = ROOT / "config/source_inventories/goh_2023_emtab10888_sample_crosswalk.csv"
INVENTORY = ROOT / "config/source_inventories/early_exchange_transition_2026.json"


class Goh2023EMTAB10888MetadataTests(unittest.TestCase):
    def test_paired_end_file_rows_collapse_to_142_sample_run_records(self):
        with SDRF.open(encoding="utf-8-sig", newline="") as stream:
            source_rows = list(csv.DictReader(stream, delimiter="\t"))
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            crosswalk_rows = list(csv.DictReader(stream))

        grouped = defaultdict(list)
        for row in source_rows:
            grouped[row["Comment[ENA_SAMPLE]"]].append(row)

        self.assertEqual(len(source_rows), 284)
        self.assertEqual(len(grouped), 142)
        self.assertEqual(len(crosswalk_rows), 142)
        self.assertEqual(Counter(map(len, grouped.values())), Counter({2: 142}))
        self.assertEqual(
            Counter(
                (row["Characteristics[individual]"], row["Characteristics[embryo stage]"])
                for row in grouped.values()
                for row in [row[0]]
            ),
            Counter({("F79", "Carnegie stage 18"): 71, ("F80", "Carnegie stage 15"): 71}),
        )
        self.assertEqual({row["Characteristics[sex]"] for row in source_rows}, {"male"})
        self.assertEqual({row["Characteristics[organism part]"] for row in source_rows}, {"yolk sac"})
        self.assertEqual(
            {row["Comment[LIBRARY_SOURCE]"] for row in source_rows},
            {"TRANSCRIPTOMIC SINGLE CELL"},
        )

        crosswalk_by_sample = {row["ena_sample"]: row for row in crosswalk_rows}
        for sample_id, rows in grouped.items():
            self.assertEqual(len({row["Comment[ENA_RUN]"] for row in rows}), 1)
            self.assertEqual(len({row["Comment[BioSD_SAMPLE]"] for row in rows}), 1)
            self.assertEqual(
                {row["Comment[SUBMITTED_FILE_NAME]"].rsplit("_", 1)[-1] for row in rows},
                {"R1.fastq.gz", "R2.fastq.gz"},
            )
            crosswalk = crosswalk_by_sample[sample_id]
            self.assertEqual(crosswalk["sdrf_file_row_count"], "2")
            self.assertEqual(crosswalk["ena_run"], rows[0]["Comment[ENA_RUN]"])
            self.assertEqual(
                crosswalk["submitted_file_names"].split(" | "),
                [row["Comment[SUBMITTED_FILE_NAME]"] for row in sorted(rows, key=lambda r: r["Comment[SUBMITTED_FILE_NAME]"])],
            )

    def test_accession_comparison_preserves_distinct_ids_and_f80_stage_conflict(self):
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            current = list(csv.DictReader(stream))
        prior_paths = {
            "E-MTAB-10552": ROOT / "config/source_inventories/goh_2023_emtab10552_sdrf_crosswalk.csv",
            "E-MTAB-11673": ROOT / "config/source_inventories/goh_2023_emtab11673_sample_crosswalk.csv",
        }
        prior = {}
        for accession, path in prior_paths.items():
            with path.open(encoding="utf-8", newline="") as stream:
                prior[accession] = list(csv.DictReader(stream))

        self.assertEqual(
            {row["individual_source_label"] for row in current}, {"F79", "F80"}
        )
        self.assertEqual(
            {row["Characteristics[individual]"] for row in prior["E-MTAB-10552"]},
            {"F61", "F79", "F80"},
        )
        current_f80_stages = {
            row["embryo_stage"] for row in current if row["individual_source_label"] == "F80"
        }
        prior_f80_stages = {
            row["Characteristics[embryo stage]"]
            for row in prior["E-MTAB-10552"]
            if row["Characteristics[individual]"] == "F80"
        }
        self.assertEqual(current_f80_stages, {"Carnegie stage 15"})
        self.assertEqual(prior_f80_stages, {"carnegie stage 18"})

        for accession, rows in prior.items():
            sample_key = "Comment[ENA_SAMPLE]" if accession == "E-MTAB-10552" else "ena_sample"
            biosample_key = "Comment[BioSD_SAMPLE]" if accession == "E-MTAB-10552" else "biosample"
            run_key = "Comment[ENA_RUN]" if accession == "E-MTAB-10552" else "ena_run"
            self.assertTrue({row["ena_sample"] for row in current}.isdisjoint(row[sample_key] for row in rows))
            self.assertTrue({row["biosample"] for row in current}.isdisjoint(row[biosample_key] for row in rows))
            self.assertTrue({row["ena_run"] for row in current}.isdisjoint(row[run_key] for row in rows))

    def test_inventory_snapshots_and_crosswalk_hashes(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        intake = next(
            row for row in source["additional_accession_intakes"]
            if row["accession"] == "E-MTAB-10888"
        )
        self.assertEqual(intake["sdrf_file_rows"], 284)
        self.assertEqual(intake["unique_sample_records"], 142)
        self.assertEqual(intake["individual_labels"], {"F79": 71, "F80": 71})
        self.assertEqual(intake["embryo_stage_by_individual"], {
            "F79": {"Carnegie stage 18": 71},
            "F80": {"Carnegie stage 15": 71},
        })
        self.assertEqual(intake["file_inventory"]["total_files"], 5)
        self.assertFalse(intake["file_inventory"]["linked_ena_raw_data_access_inspected"])

        for declaration in intake["retrieval_snapshots"]:
            path = ROOT / declaration["path"]
            self.assertEqual(path.stat().st_size, declaration["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])
        declaration = intake["local_crosswalk"]
        path = ROOT / declaration["path"]
        self.assertEqual(path.stat().st_size, declaration["bytes"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])


if __name__ == "__main__":
    unittest.main()
