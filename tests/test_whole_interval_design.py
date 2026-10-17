import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.schematics import load_layout, publish_schematic, render_html, render_svg


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "schematics" / "whole_interval_system_v3.json"
RESEARCH_OBS = {"boundary_probe", "internal_delivery", "maturation_endpoints",
                "destructive_branch", "transition_readiness", "unit_registry"}


class WholeIntervalDesignTests(unittest.TestCase):
    def setUp(self):
        self.layout, self.raw = load_layout(CONFIG)

    def test_intervals_connect_by_same_unit_handoff(self):
        conn = {(c["from"], c["to"]) for c in self.layout["connections"]}
        # The v3 layout begins where the v2 early-interval layout ends, with
        # the same unit identity carried across the handoff.
        self.assertIn(("inbound_early", "growth_chamber"), conn)
        # The sustained-exchange surface and the transition station both
        # receive from and support the one continuous growth habitat.
        self.assertIn(("sustained_exchange", "growth_chamber"), conn)
        self.assertIn(("growth_chamber", "transition_station"), conn)

    def test_every_boundary_is_a_measured_continuity_event(self):
        conn = {(c["from"], c["to"]) for c in self.layout["connections"]}
        # Pre/post-boundary paired D/M/P sampling exists and lands in the
        # same-unit disposition registry; continuity is measured, not assumed.
        self.assertIn(("growth_chamber", "boundary_probe"), conn)
        self.assertIn(("boundary_probe", "unit_registry"), conn)
        # Internal delivery is spatially resolved in the growing unit; bulk
        # supply accounting alone cannot establish it.
        self.assertIn(("growth_chamber", "internal_delivery"), conn)
        self.assertIn(("internal_delivery", "unit_registry"), conn)

    def test_destructive_branch_is_separate_from_surviving_followup(self):
        conn = {(c["from"], c["to"]) for c in self.layout["connections"]}
        # Destructive endpoint sampling is its own branch: it records into the
        # registry and never feeds transition readiness or any control path.
        self.assertIn(("growth_chamber", "destructive_branch"), conn)
        self.assertIn(("destructive_branch", "unit_registry"), conn)
        self.assertNotIn(("destructive_branch", "transition_readiness"), conn)
        self.assertNotIn(("destructive_branch", "transition_station"), conn)

    def test_transition_readiness_keeps_uncertainty_and_independence(self):
        conn = {(c["from"], c["to"]) for c in self.layout["connections"]}
        self.assertIn(("transition_station", "transition_readiness"), conn)
        self.assertIn(("transition_readiness", "unit_registry"), conn)
        # The research observation lane never feeds closed-loop control.
        for source in RESEARCH_OBS:
            self.assertNotIn((source, "controller"), conn)
        kinds = {(c["from"], c["to"]): c["kind"] for c in self.layout["connections"]}
        self.assertEqual(kinds[("unit_registry", "human_override")], "signal")

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
