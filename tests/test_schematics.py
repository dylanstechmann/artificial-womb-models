import copy
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.schematics import (
    KIND_COLORS, load_layout, publish_schematic, render_html, render_svg,
    validate_layout)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "schematics" / "ectogenesis_platform_v1.json"


class SchematicTests(unittest.TestCase):
    def setUp(self):
        self.layout, self.raw = load_layout(CONFIG)

    def test_real_config_covers_lanes_kinds_and_automation(self):
        used_lanes = {c["lane"] for c in self.layout["components"]}
        declared = {lane["id"] for lane in self.layout["lanes"]}
        self.assertEqual(used_lanes, declared)
        used_kinds = {c["kind"] for c in self.layout["components"]}
        self.assertLessEqual(used_kinds, set(KIND_COLORS))
        # Automation-first intent: robotic servicing and human override both exist.
        ids = {c["id"] for c in self.layout["components"]}
        self.assertIn("robot_service", ids)
        self.assertIn("human_override", ids)
        self.assertGreaterEqual(len(self.layout["components"]), 12)

    def test_render_is_deterministic_and_wellformed(self):
        first = render_svg(self.layout)
        self.assertEqual(first, render_svg(self.layout))
        ET.fromstring(first)  # raises if the SVG is not well-formed XML
        for comp in self.layout["components"]:
            self.assertIn(f'id="{comp["id"]}"', first)
        for conn in self.layout["connections"]:
            if conn.get("label"):
                self.assertIn(conn["label"], first)

    def test_render_has_no_external_references(self):
        svg = render_svg(self.layout)
        page = render_html(self.layout["title"], svg)
        for artifact in (svg, page):
            self.assertNotIn("http://", artifact.replace("http://www.w3.org/2000/svg", ""))
            self.assertNotIn("https://", artifact)
            self.assertNotIn("<script", artifact)

    def test_unknown_connection_endpoint_rejected(self):
        mutated = copy.deepcopy(self.layout)
        mutated["connections"][0]["to"] = "ghost"
        with self.assertRaisesRegex(InputError, "unknown component"):
            validate_layout(mutated)

    def test_component_outside_canvas_rejected(self):
        mutated = copy.deepcopy(self.layout)
        width = mutated["canvas"]["width"]
        mutated["components"][0]["x"] = width  # box extends past the right edge
        with self.assertRaisesRegex(InputError, "canvas"):
            validate_layout(mutated)

    def test_publish_bundle_is_receipt_complete_and_exclusive(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            publish_schematic(CONFIG, out)
            names = {p.name for p in out.iterdir()}
            self.assertEqual(names, {"schematic.svg", "index.html",
                                     "layout_snapshot.json", "reproduction_plan.json",
                                     "receipt.json"})
            receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["bundle_kind"], "machine_schematic")
            self.assertFalse(receipt["metadata"]["asserts_biological_capability"])
            ET.fromstring((out / "schematic.svg").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(InputError, "already exists"):
                publish_schematic(CONFIG, out)


if __name__ == "__main__":
    unittest.main()
