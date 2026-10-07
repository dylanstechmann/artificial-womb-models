import csv
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
            for key in ("claims", "sources", "stages", "requirements", "transitions"):
                self.assertEqual(report[key], original[key])
            self.assertFalse(report["complete_human_gestation_demonstrated"])
            stage_map = (output / "stage_map.csv").read_text(encoding="utf-8")
            self.assertIn("mouse postimplantation embryo", stage_map)
            self.assertIn("ovine fetal lamb", stage_map)
            self.assertIn("human", stage_map)
            self.assertNotIn("readiness", stage_map)
            transitions_csv = (output / "transitions.csv").read_text(encoding="utf-8")
            self.assertIn("preimplantation-to-interface", transitions_csv)
            self.assertIn("not_reported", transitions_csv)
            self.assertIn("unit_ids", transitions_csv)
            self.assertNotIn("readiness", transitions_csv)
            with (output / "claims.csv").open(encoding="utf-8", newline="") as handle:
                claims_csv = list(csv.DictReader(handle))
            lamb_claim = next(row for row in claims_csv if row["claim_id"] == "lamb-partial-support")
            self.assertEqual(json.loads(lamb_claim["interval_components"])[0]["maximum"], 28)

    def test_claim_intervals_cannot_exceed_or_relabel_source_axes(self):
        data = ledger()
        validate_ledger(data)

        data = ledger()
        data["claims"][0]["interval_components"][0]["maximum"] = 29
        with self.assertRaisesRegex(InputError, "extends or changes source"):
            validate_ledger(data)

        data = ledger()
        data["claims"][1]["interval_components"][0]["unit"] = "day"
        with self.assertRaisesRegex(InputError, "extends or changes source"):
            validate_ledger(data)

        data = ledger()
        data["claims"][0].pop("interval_components")
        with self.assertRaisesRegex(InputError, "omits structured intervals"):
            validate_ledger(data)

    def test_malformed_structured_interval_components_are_rejected(self):
        malformed = (
            {"axis": "support_duration", "unit": "day", "minimum": True, "maximum": 28},
            {"axis": "support_duration", "unit": "day", "minimum": 0, "maximum": float("nan")},
            {"axis": "support_duration", "unit": "day", "minimum": 30, "maximum": 28},
        )
        for component in malformed:
            with self.subTest(component=component):
                data = ledger()
                data["claims"][0]["interval_components"] = [component]
                with self.assertRaises(InputError):
                    validate_ledger(data)

        data = ledger()
        data["sources"][0]["interval_components"].append(
            data["sources"][0]["interval_components"][0].copy())
        with self.assertRaisesRegex(InputError, "unique stable identifiers"):
            validate_ledger(data)

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

    def test_transition_edges_require_known_distinct_stages_and_explicit_states(self):
        data = ledger()
        data["transitions"][0]["to_stage_id"] = "missing-stage"
        with self.assertRaisesRegex(InputError, "two distinct known stage IDs"):
            validate_ledger(data)

        data = ledger()
        data["transitions"][0]["to_stage_id"] = data["transitions"][0]["from_stage_id"]
        with self.assertRaisesRegex(InputError, "two distinct known stage IDs"):
            validate_ledger(data)

        data = ledger()
        data["transitions"][0]["continuity_state"] = "likely"
        with self.assertRaisesRegex(InputError, "continuity_state"):
            validate_ledger(data)

    def test_transition_evidence_must_cover_both_stages_and_keep_source_class(self):
        data = ledger()
        transition = data["transitions"][2]
        transition.update({
            "species": "mouse postimplantation embryo",
            "source_ids": ["aguilera2021"],
            "claim_ids": ["mouse-embryonic-interval"],
            "unit_ids": ["embryo-1"],
            "source_locations": [{"source_id": "aguilera2021", "locator": "test locator"}],
            "continuity_state": "demonstrated",
        })
        data["claims"][1]["unit_ids"] = ["embryo-1"]
        with self.assertRaisesRegex(InputError, "extends its claim stage coverage"):
            validate_ledger(data)

        data = ledger()
        transition = data["transitions"][3]
        transition.update({
            "species": "ovine fetal lamb",
            "source_ids": ["fetalife2026"],
            "claim_ids": ["fetalife-announced-support"],
            "unit_ids": ["lamb-1"],
            "source_locations": [{"source_id": "fetalife2026", "locator": "test locator"}],
            "continuity_state": "demonstrated",
        })
        data["claims"][4]["unit_ids"] = ["lamb-1"]
        with self.assertRaisesRegex(InputError, "cannot establish transition continuity"):
            validate_ledger(data)

    def test_reported_transition_units_must_be_explicitly_linked(self):
        data = ledger()
        transition = data["transitions"][0]
        transition["continuity_state"] = "demonstrated"
        transition["unit_ids"] = ["human-model-1"]
        with self.assertRaisesRegex(InputError, "unit IDs need linked claims"):
            validate_ledger(data)

        data = ledger()
        data["transitions"][0]["unit_ids"] = ["invented-unit"]
        with self.assertRaisesRegex(InputError, "cannot name unit IDs"):
            validate_ledger(data)

    def test_transition_sources_require_exact_one_to_one_locators(self):
        data = ledger()
        transition = data["transitions"][0]
        transition["source_locations"] = [{"source_id": "partridge2017", "locator": "test locator"}]
        with self.assertRaisesRegex(InputError, "exactly one source locator"):
            validate_ledger(data)


if __name__ == "__main__":
    unittest.main()
