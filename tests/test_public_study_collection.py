"""Check published metadata, nested sampling units and provenance in the public study collection."""
import csv
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "studies" / "public-evidence"

def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))

class PublicStudyCollectionTests(unittest.TestCase):
    def test_receipts_and_local_paths(self):
        def digest(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        snapshot = DIRECTORY / "bibliography"
        search = json.loads((snapshot / "receipt.json").read_bytes())
        bibliography = rows(snapshot / "records.tsv")
        self.assertEqual(len(bibliography), len({(r["source"], r["id"]) for r in bibliography}))
        self.assertEqual(len(bibliography), search["unique_source_id_pairs"])
        for label, entry in search["searches"].items():
            self.assertEqual(entry["hits"], sum(label in r["searches"].split(",") for r in bibliography))
        self.assertEqual(digest(snapshot / "records.tsv"), search["records_sha256"])
        self.assertEqual(digest(DIRECTORY / "discover.py"), search["script_sha256"])
        audit = DIRECTORY / "audit"
        receipt = json.loads((audit / "receipt.json").read_bytes())
        self.assertEqual(digest(DIRECTORY / "audit.py"), receipt["implementation_sha256"])
        self.assertEqual(digest(DIRECTORY / "inputs.json"), receipt["input_manifest_sha256"])
        for name, checksum in receipt["outputs_sha256"].items():
            self.assertEqual(digest(audit / name), checksum, name)
        for row in rows(DIRECTORY / "studies.tsv"):
            data = row["data_or_local_record"]
            if data and not data.startswith("https://"):
                self.assertTrue((DIRECTORY / data).is_file(), data)
        index = subprocess.check_output([sys.executable, str(DIRECTORY / "local_index.py")], text=True)
        self.assertEqual(index, (DIRECTORY / "local-index.tsv").read_text(encoding="utf-8"))

    def test_individuals_and_reference_material(self):
        audit = DIRECTORY / "audit"
        samples = rows(audit / "samples.tsv")
        self.assertEqual((len(samples), len({s["sheep"] for s in samples})), (36, 9))
        self.assertEqual([s["gsm"] for s in samples if s["paper_qc"] == "excluded_low_counts"], ["GSM8473189"])
        animals = rows(audit / "ovine_animals.tsv")
        self.assertEqual(len(animals), 5)
        self.assertEqual(sum(float(r["mean_distance_late"]) < float(r["mean_distance_early"]) for r in animals), 4)
        traces = rows(audit / "human_traces.tsv")
        self.assertEqual(len(traces), 8)
        self.assertTrue(all(r["cases"] == "7" for r in traces))
        self.assertEqual(sum(int(r["time_velocity_pairs"]) for r in traces), 10210)
