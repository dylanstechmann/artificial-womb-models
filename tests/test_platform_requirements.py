import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.exchange import NOTICE
from wombmodels.platform_requirements import platform_requirements


ROOT = Path(__file__).resolve().parents[1]
SPEC_BUNDLE = ROOT / "artifacts" / "acquisition-spec-module-2026-10-17"
REQUIRED = ("wall_strain", "deep_receipt_rate", "progression")
FLUIDIC_BOUNDARY = ("delivered_flux", "served_fraction", "bulk_stock")
ROUTES = ("owner_led", "acquisition_or_licensing", "co_development")


def fixture():
    return json.loads((ROOT / "examples/platform_requirements_fixture.json").read_text(encoding="utf-8"))


class PlatformRequirementsTests(unittest.TestCase):
    def run_worksheet(self, config=None, spec_dir=None):
        if config is None:
            config = fixture()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        output = root / "bundle"
        receipt = platform_requirements(config_path, spec_dir or SPEC_BUNDLE, output)
        report = json.loads((output / "platform_requirements_report.json").read_text(encoding="utf-8"))
        return receipt, report, output

    def test_line_items_match_the_source_specification(self):
        _receipt, report, output = self.run_worksheet()
        spec = json.loads((output / "consumed_spec_report.json").read_text(encoding="utf-8"))
        self.assertEqual([item["channel"] for item in report["line_items"]], list(REQUIRED))
        for item in report["line_items"]:
            channel = item["channel"]
            self.assertEqual(item["resolution_floor_multiplier"],
                             spec["resolution"]["channel_floor_multiplier"][channel])
            self.assertEqual(item["binding_pair"], spec["binding_pair"][channel]["pair"])
            self.assertEqual(item["binding_margin"], spec["binding_pair"][channel]["margin"])
            self.assertEqual(item["sampling_cadence"], spec["timing"]["sampling_cadence"])
            self.assertEqual(item["discrimination_timepoints"],
                             spec["timing"]["discrimination_timepoints"])
            self.assertEqual(item["surveillance_timepoints"],
                             spec["timing"]["surveillance_timepoints"])
            self.assertEqual(item["dmp"], {"wall_strain": "W", "deep_receipt_rate": "M",
                                          "progression": "P"}[channel])

    def test_units_come_from_the_confirmed_source_sweep(self):
        _receipt, report, output = self.run_worksheet()
        spec = json.loads((output / "consumed_spec_report.json").read_text(encoding="utf-8"))
        multipliers = report["worksheet_noise_multipliers"]
        self.assertEqual(multipliers, [1.0, 4.0])
        for item in report["line_items"]:
            sweep = {row["multiplier"]: row for row
                     in spec["units_per_cohort"][item["channel"]]["sweep"]}
            for value in multipliers:
                row = sweep[value]
                self.assertEqual(item["units_per_allocation_by_multiplier"][str(value)],
                                 row["analytic_units"])
                self.assertEqual(item["confirmed_by_seeded_sweep"][str(value)],
                                 bool(row["confirmed"]) and not row["capped"])

    def test_non_requirements_are_computed_from_the_exclusions(self):
        _receipt, report, _output = self.run_worksheet()
        excluded = {row["channel"]: row for row in report["non_requirements"]}
        self.assertEqual(sorted(excluded),
                         sorted(FLUIDIC_BOUNDARY + ("cumulative_unserved", "wall_damage")))
        for channel in FLUIDIC_BOUNDARY:
            self.assertEqual(excluded[channel]["excluded_reason"], "never_separates_any_pair")
            self.assertIn("no boundary flux sensing resolution", excluded[channel]["note"])
        self.assertEqual(excluded["wall_damage"]["excluded_reason"],
                         "derived_not_directly_instrumentable")

    def test_no_invented_prices_or_totals(self):
        _receipt, report, _output = self.run_worksheet()

        def scan(value):
            if isinstance(value, dict):
                self.assertFalse(any(key.lower().startswith("total")
                                     for key in value), value)
                for item in value.values():
                    scan(item)
            elif isinstance(value, list):
                for item in value:
                    scan(item)

        scan(report)
        self.assertFalse(report["price_totals_computed"])
        for item in report["line_items"]:
            self.assertIsNone(item["price"])
            self.assertEqual(item["price_state"], "unknown_quote_needed")
            self.assertIn("quote", item["quote_need"])

    def test_route_comparison_stays_open_with_stated_unknowns(self):
        _receipt, report, _output = self.run_worksheet()
        rows = {row["route"]: row for row in report["route_comparison"]}
        self.assertEqual(sorted(rows), sorted(ROUTES))
        for route, row in rows.items():
            self.assertEqual(row["covers_channels"], list(REQUIRED))
            self.assertIn("Open", row["disposition"])
            self.assertTrue(row["critical_unknowns"])
        self.assertIn("Requirements", rows["owner_led"]["owner_retains"])
        self.assertIn("No availability", rows["acquisition_or_licensing"]["critical_unknowns"])
        self.assertIn("No partner", rows["co_development"]["critical_unknowns"])

    def test_consumed_specification_is_byte_verbatim(self):
        _receipt, report, output = self.run_worksheet()
        source = (SPEC_BUNDLE / "acquisition_spec_report.json").read_bytes()
        self.assertEqual((output / "consumed_spec_report.json").read_bytes(), source)
        from wombmodels.artifacts import sha256
        self.assertEqual(report["source_spec"]["report_sha256"], sha256(source))
        self.assertEqual(report["source_spec"]["n_variants"], 3)
        self.assertEqual(report["source_spec"]["one_way_coupling_verified"], True)

    def test_deterministic_reproduction(self):
        _r1, _rep1, one = self.run_worksheet()
        _r2, _rep2, two = self.run_worksheet()
        names = ["input_config.json", "consumed_spec_report.json", "line_items.csv",
                 "non_requirements.csv", "route_comparison.csv",
                 "platform_requirements_report.json", "REPORT.md"]
        for name in names:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes(), name)

    def test_rejects_malformed_configurations_and_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            empty = Path(temp)
            for mutation, message in (
                    (lambda c: c.update(schema_version=2), "schema_version"),
                    (lambda c: c.update(fixture_notice="wrong"), "fixture_notice"),
                    (lambda c: c.update(source_bundle_kind="other"), "source_bundle_kind"),
                    (lambda c: c.pop("degradation_multipliers"), "config"),
                    (lambda c: c.update(degradation_multipliers=[]), "1 to 12"),
                    (lambda c: c.update(degradation_multipliers=[4, 1]), "ascending"),
                    (lambda c: c.update(degradation_multipliers=[0]), "degradation multiplier"),
                    (lambda c: c.update(degradation_multipliers=[3.0]), "confirmed by the source sweep")):
                with self.subTest(message=message):
                    config = fixture()
                    mutation(config)
                    path = empty / "config.json"
                    path.write_text(json.dumps(config), encoding="utf-8")
                    with self.assertRaisesRegex(InputError, message):
                        platform_requirements(path, SPEC_BUNDLE, empty / "out")
            valid = empty / "valid.json"
            valid.write_text(json.dumps(fixture()), encoding="utf-8")
            with self.assertRaisesRegex(InputError, "missing"):
                platform_requirements(valid, empty / "no-bundle", empty / "out1")
            other_kind = empty / "other-bundle"
            other_kind.mkdir()
            (other_kind / "acquisition_spec_report.json").write_text(
                json.dumps({"result_kind": "dimensionless_whole_path_twin"}), encoding="utf-8")
            with self.assertRaisesRegex(InputError, "not the acquisition specification"):
                platform_requirements(valid, other_kind, empty / "out2")

    def test_bundle_metadata_and_strict_verification(self):
        receipt, report, output = self.run_worksheet()
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(receipt["bundle_kind"], "dimensionless_platform_requirements")
        self.assertEqual(receipt["metadata"]["n_line_items"], 3)
        self.assertEqual(receipt["metadata"]["n_non_requirements"], 5)
        self.assertEqual(receipt["metadata"]["n_routes"], 3)
        self.assertEqual(report["fixture_notice"], NOTICE)
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        text = (output / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(NOTICE, text)
        self.assertIn("## Line items", text)
        self.assertIn("## Non-requirements", text)
        self.assertIn("## Route comparison", text)
        self.assertIn("price unknown", text)
        self.assertIn("## Limits", text)
        with (output / "line_items.csv").open(newline="", encoding="utf-8") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 3)


if __name__ == "__main__":
    unittest.main()