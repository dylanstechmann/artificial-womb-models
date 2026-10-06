import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, read_json
from wombmodels.evidence import evidence_report, validate_ledger

ROOT = Path(__file__).resolve().parents[1]


def ledger():
    return json.loads((ROOT / "config/evidence.json").read_text(encoding="utf-8"))


class EvidenceTests(unittest.TestCase):
    def test_species_intervals_statuses_and_stages_preserved_in_report(self):
        original = ledger()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report"
            evidence_report(ROOT / "config/evidence.json", output)
            report = json.loads((output / "evidence_report.json").read_text(encoding="utf-8"))
            for key in ("claims", "sources", "stages", "requirements"):
                self.assertEqual(report[key], original[key])
            self.assertFalse(report["complete_human_gestation_demonstrated"])
            stage_map = (output / "stage_map.csv").read_text(encoding="utf-8")
            self.assertIn("mouse postimplantation embryo", stage_map)
            self.assertIn("ovine fetal lamb", stage_map)
            self.assertIn("human", stage_map)
            self.assertNotIn("readiness", stage_map)

    def test_species_and_stage_extrapolation_rejected(self):
        data = ledger()
        data["claims"][0]["species"] = "human"
        with self.assertRaises(InputError):
            validate_ledger(data)
        data = ledger()
        data["claims"][0]["stage_ids"].append("complete-gestation")
        with self.assertRaises(InputError):
            validate_ledger(data)

    def test_announcements_and_regulator_discussion_cannot_be_trial_results(self):
        for index in (3, 4):
            data = ledger()
            data["claims"][index]["status"] = "source_reported"
            with self.assertRaises(InputError):
                validate_ledger(data)

    def test_proposed_human_benefits_and_complete_gestation_must_remain_gaps(self):
        for index in (5, 6, 7):
            data = ledger()
            data["claims"][index]["status"] = "announced"
            data["claims"][index]["source_ids"] = ["fetalife2026"]
            with self.assertRaises(InputError):
                validate_ledger(data)
        data = ledger()
        data["claims"] = data["claims"][:-1]
        with self.assertRaises(InputError):
            validate_ledger(data)

    def test_unknown_duplicate_and_missing_references_rejected(self):
        data = ledger()
        data["claims"][0]["source_ids"] = ["imaginary-source"]
        with self.assertRaises(InputError):
            validate_ledger(data)
        data = ledger()
        data["sources"].append(data["sources"][0])
        with self.assertRaises(InputError):
            validate_ledger(data)
        data = ledger()
        data["claims"][0]["source_ids"] = []
        with self.assertRaises(InputError):
            validate_ledger(data)

    def test_ledger_report_does_not_overwrite_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            protected = output / "keep.txt"
            protected.write_text("preserve")
            with self.assertRaises(InputError):
                evidence_report(ROOT / "config/evidence.json", output)
            self.assertEqual(protected.read_text(), "preserve")

    def test_json_duplicate_nonfinite_and_wrong_root_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for value in ('{"value": NaN}', '{"id": 1, "id": 2}', '[1, 2]', '{broken'):
                path.write_text(value)
                with self.assertRaises(InputError):
                    read_json(path)

    def test_malformed_status_types_and_dates_have_controlled_errors(self):
        for field in ("source", "claim", "requirement"):
            data = ledger()
            if field == "source":
                data["sources"][0]["kind"] = []
            else:
                data[field + "s"][0]["status"] = []
            with self.assertRaises(InputError):
                validate_ledger(data)
        data = ledger()
        data["reviewed_on"] = "20261006"
        with self.assertRaises(InputError):
            validate_ledger(data)


if __name__ == "__main__":
    unittest.main()
