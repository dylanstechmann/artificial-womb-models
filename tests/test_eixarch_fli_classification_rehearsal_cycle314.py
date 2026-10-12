import csv
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report, validate_dataset

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle313"
ASSESSMENT = ART / "functional-classification-overlay-cycle313.json"
OVERLAY = ART / "poster-row-functional-classification-overlay-cycle313.csv"


class EixarchFLIClassificationRehearsalCycle314Tests(unittest.TestCase):
    def test_machine_readable_receipt_separates_validation_from_scientific_review(self):
        result = json.loads((ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle314/functional-classification-rehearsal-cycle314.json").read_text(encoding="utf-8"))
        self.assertEqual(result["totals"]["validated_and_exported_observation_rows"], 51)
        self.assertEqual(result["totals"]["source_artifacts_byte_verified"], 4)
        self.assertEqual(result["totals"]["output_bundles_strictly_verified"], 4)
        self.assertTrue(result["candidate_files_byte_for_byte_unchanged"])
        self.assertFalse(result["classification_scientifically_validated"])

    def test_temporary_tagged_copies_validate_export_and_verify_sources(self):
        assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        with OVERLAY.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        by_candidate = {}
        for row in rows:
            by_candidate.setdefault(row["candidate_path"], []).append(row)

        with tempfile.TemporaryDirectory() as temporary:
            temp_root = Path(temporary)
            seen = 0
            for source in assessment["candidate_sources"]:
                candidate_path = ROOT / source["candidate_path"]
                original_bytes = candidate_path.read_bytes()
                self.assertEqual(hashlib.sha256(original_bytes).hexdigest(), source["candidate_sha256"])
                data = json.loads(original_bytes.decode("utf-8"))
                overlay_rows = by_candidate[source["candidate_path"]]
                tagged = {row["record_id"]: row["functional_evidence_class"] for row in overlay_rows}
                self.assertEqual(set(tagged), {item["record_id"] for item in data["observations"]})
                for item in data["observations"]:
                    item["assay"]["functional_evidence_class"] = tagged[item["record_id"]]
                validate_dataset(data)

                dataset_path = temp_root / f"{source['poster'].replace('.', '-')}.json"
                dataset_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                bundle = temp_root / f"bundle-{source['poster'].replace('.', '-') }"
                observation_report(dataset_path, bundle, source_root=ROOT)
                report = json.loads((bundle / "observation_intake_report.json").read_text(encoding="utf-8"))
                self.assertEqual(report["functional_evidence_classes"]["n_not_declared"], 0)
                self.assertEqual(report["source_file_verification"]["status"], "complete")
                self.assertTrue(verify_bundle(bundle, strict=True)["bytes_verified"])
                with (bundle / "observation_records.csv").open(encoding="utf-8", newline="") as stream:
                    output_rows = list(csv.DictReader(stream))
                self.assertEqual({item["record_id"]: item["functional_evidence_class"] for item in output_rows}, tagged)
                seen += len(output_rows)
                self.assertEqual(candidate_path.read_bytes(), original_bytes)
            self.assertEqual(seen, 51)

    def test_temporary_projection_counts_agree_with_overlay(self):
        with OVERLAY.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        counts = Counter(row["functional_evidence_class"] for row in rows)
        self.assertEqual(counts, {
            "biological_response_proxy": 29,
            "developmental_outcome": 18,
            "other": 4,
        })


if __name__ == "__main__":
    unittest.main()
