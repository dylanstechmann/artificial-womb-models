import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle316"
XML = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle286/eixarch2023-pmc10044909-efetch.xml"
PDF = ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle287/eixarch2023-publisher-version.pdf"
CANDIDATE = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


def node_text(node):
    return " ".join("".join(node.itertext()).split())


def section_text(root, prefix):
    for section in root.findall(".//sec"):
        title = section.find("title")
        if title is not None and node_text(title).startswith(prefix):
            return " ".join(node_text(p) for p in section.findall("./p"))
    raise AssertionError(f"Missing section starting with {prefix}")


class Eixarch2023GasTransferScreenCycle316Tests(unittest.TestCase):
    def test_method_route_exists_but_results_candidate_do_not_contain_transfer_values(self):
        root = ET.parse(XML).getroot()
        circuit = section_text(root, "2.2.2.")
        support = section_text(root, "2.2.5.")
        results = section_text(root, "3.")
        self.assertIn("oxygenator", circuit.lower())
        self.assertIn("PaO2", circuit)
        self.assertIn("PaCO2", circuit)
        self.assertIn("pre- and post-membrane blood samples", support.lower())
        self.assertIn("blood gas", support.lower())
        self.assertIn("pH", results)
        self.assertIn("lactate", results.lower())
        self.assertNotIn("PaO2", results)
        self.assertNotIn("PaCO2", results)

        candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
        endpoints = " ".join(row["assay"]["endpoint"] for row in candidate["observations"])
        self.assertNotIn("PaO2", endpoints)
        self.assertNotIn("PaCO2", endpoints)
        self.assertIn("circuit flow", endpoints.lower())

    def test_source_hashes_and_data_availability_statement_are_pinned(self):
        assessment = json.loads((ART / "oxygen-transfer-evidence-screen-cycle316.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(XML.read_bytes()).hexdigest(), assessment["source_files"][0]["sha256"])
        self.assertEqual(hashlib.sha256(PDF.read_bytes()).hexdigest(), assessment["source_files"][1]["sha256"])
        self.assertEqual(hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), assessment["source_files"][2]["sha256"])
        root = ET.parse(XML).getroot()
        data_note = root.find(".//notes[@notes-type='data-availability']")
        self.assertIsNotNone(data_note)
        self.assertEqual(node_text(data_note.find("p")), "Not applicable.")
        self.assertFalse(assessment["candidate_records_modified"])
        self.assertFalse(assessment["author_contacted"])
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(inventory["eixarch_2023_gas_transfer_screen_cycle316"]["assessment_path"],
                         "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle316/oxygen-transfer-evidence-screen-cycle316.json")


if __name__ == "__main__":
    unittest.main()
