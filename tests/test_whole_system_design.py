import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.schematics import load_layout, publish_schematic, render_html, render_svg


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "schematics" / "early_exchange_system_v2.json"
RESEARCH_OBS = {"d_probe", "m_readout", "p_staging", "unit_registry"}


class WholeSystemDesignTests(unittest.TestCase):
    def setUp(self):
        self.layout, self.raw = load_layout(CONFIG)

    def test_all_three_architecture_variants_are_drawn(self):
        ids = {c["id"] for c in self.layout["components"]}
        # The three retained allocations from the T01 comparison are all
        # instantiated on one skeleton rather than described in prose.
        self.assertIn("living_interface", ids)
        self.assertIn("synthetic_exchange", ids)
        self.assertIn("stage_boundary", ids)
        # Each variant reaches the one continuous habitat with unit identity.
        targets = {conn["to"] for conn in self.layout["connections"]}
        for variant in ("living_interface", "synthetic_exchange", "stage_boundary"):
            self.assertTrue(any(conn["from"] == variant and conn["to"] == "early_habitat"
                                for conn in self.layout["connections"]),
                            f"{variant} does not support the habitat")

    def test_dmp_observation_is_same_unit_and_control_independent(self):
        conn = {(c["from"], c["to"]) for c in self.layout["connections"]}
        # D, M and P are all sampled from the same living unit.
        for readout in ("d_probe", "m_readout", "p_staging"):
            self.assertIn(("early_habitat", readout), conn)
        # Delivery observation pairs interface and core states; without the
        # pairing, exchange and transport rates are structurally ambiguous.
        self.assertIn(("living_interface", "d_probe"), conn)
        self.assertIn(("early_habitat", "d_probe"), conn)
        # The research observation lane never feeds closed-loop control: no
        # connection from a research component to the controller exists, and
        # the registry reaches only human oversight as a review record.
        for source in RESEARCH_OBS:
            self.assertNotIn((source, "controller"), conn)
        self.assertIn(("unit_registry", "human_override"), conn)
        kinds = {(c["from"], c["to"]): c["kind"] for c in self.layout["connections"]}
        self.assertEqual(kinds[("unit_registry", "human_override")], "signal")
        # Every unit ends in the disposition registry with losses recorded.
        for readout in ("d_probe", "m_readout", "p_staging"):
            self.assertIn((readout, "unit_registry"), conn)

    def test_render_is_deterministic_wellformed_and_selfcontained(self):
        first = render_svg(self.layout)
        self.assertEqual(first, render_svg(self.layout))
        ET.fromstring(first)
        page = render_html(self.layout["title"], first)
        for artifact in (first, page):
            self.assertNotIn("http://", artifact.replace("http://www.w3.org/2000/svg", ""))
            self.assertNotIn("https://", artifact)
            self.assertNotIn("<script", artifact)

    def test_publish_bundle_is_receipt_complete_and_exclusive(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            publish_schematic(CONFIG, out)
            names = {p.name for p in out.iterdir()}
            self.assertEqual(names, {"schematic.svg", "index.html",
                                     "layout_snapshot.json", "reproduction_plan.json",
                                     "receipt.json"})
            receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
            self.assertFalse(receipt["metadata"]["asserts_biological_capability"])
            with self.assertRaisesRegex(InputError, "already exists"):
                publish_schematic(CONFIG, out)


if __name__ == "__main__":
    unittest.main()
