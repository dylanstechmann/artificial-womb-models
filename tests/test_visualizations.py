import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.reciprocal_twin import reciprocal_twin
from wombmodels.visualizations import (
    _extent, _project, load_twin_bundle, publish_visualization, render_html, render_svg)
from wombmodels.whole_path_twin import whole_path_twin

ROOT = Path(__file__).resolve().parents[1]


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        whole_path_twin(ROOT / "examples/whole_path_twin_fixture.json", self.source)

    def test_projection_is_finite_and_changes_with_view(self):
        source = load_twin_bundle(self.source)
        extents = [_extent(source["series"], axis)
                   for axis in ("dimensionless_time", "bulk_stock", "progression")]
        point = [0.5, 0.5, 0.5]
        first = _project(point, extents)
        rotated = _project(point, extents, yaw=0.4)
        self.assertTrue(all(value > 0 for value in first))
        self.assertNotEqual(first, rotated)
        self.assertNotEqual(first, _project(point, extents, pitch=-0.4))

    def test_html_is_offline_and_embeds_all_variants_and_axes(self):
        source = load_twin_bundle(self.source)
        page = render_html(source)
        self.assertIn('type="application/json"', page)
        self.assertIn("Drag to rotate", page)
        self.assertIn("Scroll to zoom", page)
        self.assertIn("Download SVG", page)
        for item in source["series"]:
            self.assertIn(item["name"], page)
        for axis in source["axes"]:
            self.assertIn(axis, page)
        self.assertNotIn("https://", page)
        self.assertNotIn("http://", page.replace("http://www.w3.org/2000/svg", ""))
        self.assertNotIn("fetch(", page)
        self.assertNotIn("XMLHttpRequest", page)
        self.assertNotIn("src=\"http", page)

    def test_static_svg_is_wellformed_and_deterministic(self):
        source = load_twin_bundle(self.source)
        svg = render_svg(source["series"])
        self.assertEqual(svg, render_svg(source["series"]))
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("Dimensionless twin trajectories", svg)
        self.assertNotIn("<script", svg)

    def test_publication_verifies_and_relocates_with_parent_receipt(self):
        output = self.root / "view"
        receipt = publish_visualization(self.source, output)
        self.assertEqual(receipt["bundle_kind"], "dimensionless_twin_3d_visualization")
        self.assertEqual(receipt["metadata"]["n_variants"], 3)
        self.assertFalse(receipt["metadata"]["biological_measurements"])
        self.assertEqual({path.name for path in output.iterdir()}, {
            "index.html", "trajectory.svg", "source_receipt.json",
            "visualization_report.json", "reproduction_plan.json", "receipt.json"})
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["ancestry_resolved"], "resolved")
        moved = self.root / "relocated"
        shutil.copytree(output, moved)
        shutil.rmtree(self.source)
        self.assertTrue(verify_bundle(moved, strict=True)["bytes_verified"])

    def test_reciprocal_bundle_exposes_mechanical_axes(self):
        source = self.root / "reciprocal"
        reciprocal_twin(ROOT / "examples/reciprocal_twin_fixture.json", source)
        loaded = load_twin_bundle(source)
        self.assertIn("wall_strain", loaded["axes"])
        self.assertIn("wall_damage", loaded["axes"])
        output = self.root / "reciprocal-view"
        publish_visualization(source, output)
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_changed_source_or_wrong_kind_is_rejected_before_publication(self):
        trajectory = self.source / "trajectory_staged.csv"
        trajectory.write_bytes(trajectory.read_bytes() + b"\n")
        output = self.root / "view"
        with self.assertRaisesRegex(InputError, "strict verification"):
            publish_visualization(self.source, output)
        self.assertFalse(output.exists())
        from wombmodels.exchange import simulate
        other = self.root / "exchange"
        simulate(ROOT / "examples/exchange_fixture.json", other)
        with self.assertRaisesRegex(InputError, "requires a whole-path"):
            publish_visualization(other, self.root / "other")

    def test_cli_publishes_and_rejects_an_existing_destination(self):
        output = self.root / "cli-view"
        self.assertEqual(main(["visualize-twin", "--bundle", str(self.source),
                               "--out", str(output)]), 0)
        self.assertTrue((output / "index.html").is_file())
        with self.assertRaises(SystemExit) as raised:
            main(["visualize-twin", "--bundle", str(self.source), "--out", str(output)])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
