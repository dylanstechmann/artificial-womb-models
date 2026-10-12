import csv
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/early-exchange-transition-2026-10-11"
INVENTORY = ROOT / "config/source_inventories/early_exchange_transition_2026.json"
CROSSWALK = ROOT / "config/source_inventories/goh_2023_remaining_citeseq_sample_crosswalk.csv"
ACCESSIONS = ("E-MTAB-11549", "E-MTAB-11618", "E-MTAB-11613")


def read_sdrf(accession):
    path = ARTIFACTS / f"{accession}.sdrf.txt"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


class Goh2023RemainingAccessionScreenTests(unittest.TestCase):
    def test_sample_crosswalk_separates_samples_runs_and_read_files(self):
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            crosswalk = list(csv.DictReader(stream))
        self.assertEqual(len(crosswalk), 11)
        by_accession = defaultdict(list)
        for row in crosswalk:
            by_accession[row["accession"]].append(row)

        self.assertEqual(
            {accession: len(by_accession[accession]) for accession in ACCESSIONS},
            {"E-MTAB-11549": 2, "E-MTAB-11618": 3, "E-MTAB-11613": 6},
        )
        expected_rows = {"E-MTAB-11549": 288, "E-MTAB-11618": 430, "E-MTAB-11613": 864}
        expected_runs = {"E-MTAB-11549": 96, "E-MTAB-11618": 144, "E-MTAB-11613": 288}
        expected_claims = {
            "E-MTAB-11549": "two biological replicates",
            "E-MTAB-11618": "three biological replicates",
            "E-MTAB-11613": "six biological replicates",
        }

        for accession in ACCESSIONS:
            source_rows = read_sdrf(accession)
            self.assertEqual(len(source_rows), expected_rows[accession])
            grouped = defaultdict(list)
            for row in source_rows:
                grouped[row["Comment[ENA_SAMPLE]"]].append(row)
            cross_by_sample = {row["ena_sample"]: row for row in by_accession[accession]}
            self.assertEqual(set(grouped), set(cross_by_sample))
            self.assertEqual(
                sum(int(row["unique_ena_runs"]) for row in by_accession[accession]),
                expected_runs[accession],
            )
            self.assertEqual(
                {row["description_replicate_claim"] for row in by_accession[accession]},
                {expected_claims[accession]},
            )
            for sample_id, sample_rows in grouped.items():
                cross = cross_by_sample[sample_id]
                run_ids = sorted({row["Comment[ENA_RUN]"] for row in sample_rows})
                experiment_ids = sorted({row["Comment[ENA_EXPERIMENT]"] for row in sample_rows})
                read_indexes = Counter(row["Comment[READ_INDEX]"] for row in sample_rows)
                self.assertEqual(len(run_ids), 48)
                self.assertEqual(int(cross["unique_ena_runs"]), 48)
                self.assertEqual(cross["ena_run_ids"].split(" | "), run_ids)
                self.assertEqual(cross["ena_experiment_ids"].split(" | "), experiment_ids)
                self.assertEqual(int(cross["unique_ena_experiments"]), 2)
                self.assertEqual(int(cross["sdrf_file_row_count"]), len(sample_rows))
                self.assertEqual(json.loads(cross["read_index_counts"]), dict(read_indexes))

        self.assertEqual(
            Counter(int(row["sdrf_file_row_count"]) for row in by_accession["E-MTAB-11618"]),
            Counter({144: 2, 142: 1}),
        )
        irregular = next(
            row for row in by_accession["E-MTAB-11618"] if row["ena_sample"] == "ERS11465100"
        )
        self.assertEqual(
            json.loads(irregular["read_index_counts"]),
            {"index1": 46, "read1": 48, "read2": 48},
        )

    def test_remaining_accessions_do_not_identify_the_f158_coronal_record(self):
        with CROSSWALK.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for accession in ACCESSIONS:
            api_path = ARTIFACTS / f"{accession}-biostudies-api.json"
            sdrf_path = ARTIFACTS / f"{accession}.sdrf.txt"
            searchable = api_path.read_text(encoding="utf-8").casefold() + sdrf_path.read_text(encoding="utf-8").casefold()
            self.assertNotIn("f158", searchable)
            self.assertNotIn("coronal", searchable)
        self.assertEqual(
            {row["organism_part"] for row in rows if row["accession"] == "E-MTAB-11549"},
            {"yolk sac"},
        )
        self.assertEqual(
            {row["organism_part"] for row in rows if row["accession"] in {"E-MTAB-11618", "E-MTAB-11613"}},
            {"liver"},
        )
        self.assertEqual(
            {row["library_strategy_values"] for row in rows if row["accession"] == "E-MTAB-11549"},
            {"OTHER"},
        )
        self.assertEqual(
            {row["library_strategy_values"] for row in rows if row["accession"] != "E-MTAB-11549"},
            {"OTHER | RNA-Seq"},
        )

        previous = {
            "E-MTAB-10552": ("goh_2023_emtab10552_sdrf_crosswalk.csv", "Comment[ENA_SAMPLE]", "Comment[BioSD_SAMPLE]", "Comment[ENA_RUN]"),
            "E-MTAB-11673": ("goh_2023_emtab11673_sample_crosswalk.csv", "ena_sample", "biosample", "ena_run"),
            "E-MTAB-10888": ("goh_2023_emtab10888_sample_crosswalk.csv", "ena_sample", "biosample", "ena_run"),
        }
        for filename, sample_col, biosample_col, run_col in previous.values():
            with (ROOT / "config/source_inventories" / filename).open(encoding="utf-8", newline="") as stream:
                old_rows = list(csv.DictReader(stream))
            for new_col, old_col in [("ena_sample", sample_col), ("biosample", biosample_col), ("ena_run_ids", run_col)]:
                old_ids = {value for row in old_rows for value in row[old_col].split(" | ")}
                new_ids = {value for row in rows for value in row[new_col].split(" | ")}
                self.assertTrue(old_ids.isdisjoint(new_ids))

    def test_inventory_pins_all_snapshots_and_preserves_source_claims(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source = next(
            row for row in inventory["sources"]
            if row["source_id"] == "goh-2023-yolk-sac-reference"
        )
        screens = {row["accession"]: row for row in source["remaining_accession_intakes"]}
        self.assertEqual(set(screens), set(ACCESSIONS))
        self.assertEqual(source["remaining_accession_screen"]["aggregate_counts"], {
            "unique_ena_sample_records": 11,
            "unique_ena_runs": 528,
            "sdrf_file_rows": 1582,
        })
        self.assertIn("did not find the matched coronal accession within those three accessions", source["remaining_accession_screen"]["result"])
        self.assertIn("later identified E-MTAB-11911", source["remaining_accession_screen"]["result"])

        for accession, intake in screens.items():
            self.assertIn("biological replicates", intake["description_replicate_claim"])
            self.assertFalse(intake["f158_text_in_api_or_sdrf"])
            self.assertFalse(intake["coronal_text_in_api_or_sdrf"])
            for declaration in intake["retrieval_snapshots"]:
                path = ROOT / declaration["path"]
                self.assertEqual(path.stat().st_size, declaration["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])

        declaration = source["remaining_accession_screen"]["local_crosswalk"]
        path = ROOT / declaration["path"]
        self.assertEqual(path.stat().st_size, declaration["bytes"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), declaration["sha256"])


if __name__ == "__main__":
    unittest.main()
