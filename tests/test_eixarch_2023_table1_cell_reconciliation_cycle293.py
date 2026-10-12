import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle293"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2023Table1CellReconciliationCycle293Tests(unittest.TestCase):
    def test_all_table_cells_keep_value_missingness_and_linkage_states(self):
        assessment = json.loads((ART / "table1-cell-reconciliation-cycle293.json").read_text(encoding="utf-8"))
        with (ART / "table1-cell-crosswalk-cycle293.csv").open(encoding="utf-8-sig", newline="") as stream:
            cells = list(csv.DictReader(stream))
        self.assertEqual(len(cells), 60)
        self.assertEqual(sum(c["cell_status"] == "reported" for c in cells), 51)
        self.assertEqual(sum(c["cell_status"] == "dash" for c in cells), 7)
        self.assertEqual(sum(c["cell_status"] == "not_applicable" for c in cells), 2)
        self.assertEqual(sum(c["candidate_match"] == "True" and bool(c["coverage_declaration"])
                             for c in cells), 42)
        self.assertEqual(sum(bool(c["candidate_record_id"]) for c in cells), 46)
        self.assertEqual(sum(c["mapping_note"].startswith("Source-inventory cell only") for c in cells), 5)
        self.assertEqual(sum(c["source_cell_lexeme"] == "0" and c["cell_status"] == "reported"
                             for c in cells), 5)
        self.assertTrue(all(not c["candidate_record_id"] for c in cells
                            if c["cell_status"] in {"dash", "not_applicable"}))
        self.assertFalse(assessment["candidate_observation_values_changed"])
        self.assertEqual(assessment["unresolved_cells"], [
            "Bubbles in the circuit, 4-24 h: 1 (14.3%)",
            "Vasospasm, 4-24 h: 4 (57.1%)",
        ])

    def test_direct_observations_match_cell_lexemes_and_pinned_source(self):
        assessment = json.loads((ART / "table1-cell-reconciliation-cycle293.json").read_text(encoding="utf-8"))
        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        records = {r["record_id"]: r for r in candidate["observations"]}
        with (ART / "table1-cell-crosswalk-cycle293.csv").open(encoding="utf-8-sig", newline="") as stream:
            cells = list(csv.DictReader(stream))
        direct = [c for c in cells if c["candidate_match"] == "True"
                  and c["coverage_declaration"]]
        self.assertEqual(len(direct), 42)
        for cell in direct:
            record = records[cell["candidate_record_id"]]
            literal = cell["source_cell_lexeme"].replace("*", "").strip()
            if "±" in literal:
                mean, uncertainty = literal.split("±")
                self.assertEqual(float(record["observation"]["value"]), float(mean.strip()))
                self.assertEqual(float(record["observation"]["measurement_uncertainty"]),
                                 float(uncertainty.strip()))
            else:
                self.assertEqual(int(record["observation"]["value"]), int(literal.split(" ", 1)[0]))
        pdf = ROOT / assessment["source_pdf_path"]
        self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), assessment["source_pdf_sha256"])
        self.assertEqual(len(candidate["observations"]), 50)
        self.assertEqual(candidate["source_revision"]["review_status"], "candidate")

    def test_source_inventory_retains_specific_complication_cells(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = next(x for x in inventory["records"]
                      if x["record_id"] == "eixarch_2023_entry_learning_curve")
        check = record["table1_cell_reconciliation_cycle293"]
        self.assertEqual(check["specific_complication_cells_source_inventory_only"], 5)
        self.assertFalse(check["candidate_observations_changed"])
        self.assertIn("denominator", check["denominator_status"])


if __name__ == "__main__":
    unittest.main()

