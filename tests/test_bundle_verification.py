from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.exchange import simulate
from wombmodels.identifiability import analyze

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class BundleVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.simulation = self.root / "sim"
        simulate(EXAMPLES / "exchange_fixture.json", self.simulation)
        self.bundle = self.root / "ident"
        analyze(EXAMPLES / "exchange_fixture.json", self.simulation / "trajectory.csv", self.bundle)

    def receipt(self, bundle: Path) -> dict:
        return json.loads((bundle / "receipt.json").read_text(encoding="utf-8"))

    def test_published_bundle_verifies_and_separates_statuses(self):
        report = verify_bundle(self.bundle, strict=True)
        self.assertTrue(report["bytes_verified"], report["errors"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(report["ancestry_resolved"], "resolved")
        self.assertEqual(report["scientific_review"], "not_established_by_this_tool")
        self.assertEqual(report["reproduction"], "not_attempted")
        self.assertEqual(report["inventory"]["declared_outputs"], report["inventory"]["verified_outputs"])
        self.assertEqual(report["declared_dependencies"], ["python>=3.10 standard library only"])
        self.assertIn("identifiability-report", report["rerun_command"])

    def test_every_bundle_carries_a_reproduction_plan_without_absolute_paths(self):
        for bundle in (self.simulation, self.bundle):
            with self.subTest(bundle=bundle.name):
                plan = json.loads((bundle / "reproduction_plan.json").read_text(encoding="utf-8"))
                self.assertEqual(plan["schema_version"], 1)
                self.assertEqual(plan["declared_dependencies"], ["python>=3.10 standard library only"])
                self.assertIn("wombmodels", plan["command"])
                self.assertIn("reproduction_plan.json", plan["expected_outputs"])
                self.assertTrue(plan["limits"])
                encoded = json.dumps(plan)
                self.assertNotIn(str(self.root), encoded)
                self.assertNotIn(str(EXAMPLES), encoded)
                entry = self.receipt(bundle)["outputs"]["reproduction_plan.json"]
                raw = (bundle / "reproduction_plan.json").read_bytes()
                self.assertEqual(entry["sha256"], sha256(raw))
                self.assertEqual(entry["size_bytes"], len(raw))

    def test_parent_receipt_travels_with_the_bundle_and_resolves_ancestry(self):
        parent = json.loads((self.bundle / "source_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(parent["bundle_kind"], "synthetic_exchange_software_fixture")
        metadata = self.receipt(self.bundle)["metadata"]
        self.assertEqual(metadata["parent_receipt_file"], "source_receipt.json")
        self.assertEqual(metadata["parent_receipt_sha256"],
                         sha256((self.bundle / "source_receipt.json").read_bytes()))
        self.assertEqual(metadata["parent_receipt_sha256"],
                         sha256((self.simulation / "receipt.json").read_bytes()))

    def test_relocated_bundle_verifies_after_the_source_directory_is_gone(self):
        moved = self.root / "relocated" / "renamed-bundle"
        moved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.bundle, moved)
        shutil.rmtree(self.simulation)
        shutil.rmtree(self.bundle)
        report = verify_bundle(moved, strict=True)
        self.assertTrue(report["bytes_verified"], report["errors"])
        self.assertEqual(report["ancestry_resolved"], "resolved")
        self.assertEqual(report["bundle"], "renamed-bundle")

    def test_changed_output_bytes_fail_with_the_offending_name(self):
        target = self.bundle / "observability_report.json"
        target.write_bytes(target.read_bytes() + b"\n")
        report = verify_bundle(self.bundle)
        self.assertFalse(report["bytes_verified"])
        self.assertTrue(any("observability_report.json" in error and "receipt hash" in error
                            for error in report["errors"]), report["errors"])

    def test_missing_declared_output_is_reported(self):
        (self.bundle / "interval_design.csv").unlink()
        report = verify_bundle(self.bundle)
        self.assertFalse(report["bytes_verified"])
        self.assertIn("declared output is missing from the bundle: interval_design.csv", report["errors"])

    def test_removed_parent_receipt_leaves_ancestry_unresolved(self):
        (self.bundle / "source_receipt.json").unlink()
        report = verify_bundle(self.bundle)
        self.assertFalse(report["bytes_verified"])
        self.assertEqual(report["ancestry_resolved"], "unresolved")

    def test_swapped_parent_receipt_is_detected(self):
        other = self.root / "sim-two"
        simulate(EXAMPLES / "exchange_fixture.json", other)
        (self.bundle / "source_receipt.json").write_bytes(
            (other / "receipt.json").read_bytes() + b"\n")
        report = verify_bundle(self.bundle)
        self.assertFalse(report["bytes_verified"])
        self.assertEqual(report["ancestry_resolved"], "unresolved")
        self.assertTrue(any("parent receipt" in error for error in report["errors"]), report["errors"])

    def test_bundle_without_a_declared_parent_reports_no_parent(self):
        report = verify_bundle(self.simulation, strict=True)
        self.assertTrue(report["bytes_verified"], report["errors"])
        self.assertEqual(report["ancestry_resolved"], "no_parent_declared")

    def test_undeclared_file_is_a_warning_and_a_strict_failure(self):
        (self.bundle / "notes.txt").write_text("a reviewer left this behind\n", encoding="utf-8")
        lenient = verify_bundle(self.bundle)
        self.assertTrue(lenient["bytes_verified"], lenient["errors"])
        self.assertEqual(lenient["inventory"]["undeclared_files"], ["notes.txt"])
        self.assertTrue(any("does not declare" in warning for warning in lenient["warnings"]))
        self.assertFalse(verify_bundle(self.bundle, strict=True)["bytes_verified"])

    def test_symlinked_output_is_rejected(self):
        target = self.bundle / "observability_report.json"
        payload = target.read_bytes()
        decoy = self.root / "outside.json"
        decoy.write_bytes(payload)
        target.unlink()
        try:
            target.symlink_to(decoy)
        except (OSError, NotImplementedError):
            self.skipTest("this platform does not permit creating test symlinks")
        report = verify_bundle(self.bundle)
        self.assertFalse(report["bytes_verified"])
        self.assertTrue(any("symlink" in error for error in report["errors"]), report["errors"])

    def test_corrupt_and_absent_receipts_raise_actionable_errors(self):
        with self.assertRaisesRegex(InputError, "does not exist"):
            verify_bundle(self.root / "not-a-bundle")
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaisesRegex(InputError, "no receipt.json"):
            verify_bundle(empty)
        (self.bundle / "receipt.json").write_bytes(b"{not json")
        with self.assertRaisesRegex(InputError, "not readable bounded JSON"):
            verify_bundle(self.bundle)

    def test_receipt_structure_is_checked_without_a_schema_library(self):
        receipt = self.receipt(self.bundle)
        receipt["outputs"]["observability_report.json"]["sha256"] = "short"
        del receipt["implementation_sha256"]
        (self.bundle / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        report = verify_bundle(self.bundle)
        self.assertFalse(report["bytes_verified"])
        self.assertIn("receipt implementation_sha256 must record the publishing implementation", report["errors"])
        self.assertTrue(any("64-character sha256" in error for error in report["errors"]))

    def test_unknown_bundle_kind_warns_and_fails_strictly(self):
        receipt = self.receipt(self.bundle)
        receipt["bundle_kind"] = "speculative_human_gestation_prediction"
        (self.bundle / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        lenient = verify_bundle(self.bundle)
        self.assertTrue(any("does not publish" in warning for warning in lenient["warnings"]))
        self.assertFalse(verify_bundle(self.bundle, strict=True)["bytes_verified"])

    def test_cli_reports_exit_status_for_pass_and_fail(self):
        self.assertEqual(main(["verify-bundle", "--bundle", str(self.bundle), "--strict"]), 0)
        (self.bundle / "REPORT.md").write_text("edited after publication\n", encoding="utf-8")
        self.assertEqual(main(["verify-bundle", "--bundle", str(self.bundle)]), 1)


if __name__ == "__main__":
    unittest.main()
