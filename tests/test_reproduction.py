from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wombmodels.artifacts import InputError, implementation_hashes, json_bytes, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.exchange import simulate
from wombmodels.identifiability import analyze
from wombmodels.reproduction import (
    MAX_CAPTURED_STREAM_BYTES,
    REPRODUCTION_BUNDLE_KIND,
    RERUN_ENTRY_POINTS,
    RERUN_TIMEOUT_SECONDS,
    _compare_output_bytes,
    _execute_entry_point,
    _load_rerun_source,
    rerun_bundle,
)


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.simulation = self.root / "simulation"
        simulate(EXAMPLES / "exchange_fixture.json", self.simulation)
        self.identifiability = self.root / "identifiability"
        analyze(EXAMPLES / "exchange_fixture.json", self.simulation / "trajectory.csv",
                self.identifiability)

    def receipt(self, bundle: Path) -> dict:
        return json.loads((bundle / "receipt.json").read_text(encoding="utf-8"))

    def report(self, bundle: Path) -> dict:
        return json.loads((bundle / "reproduction_report.json").read_text(encoding="utf-8"))

    def replace_declared(self, bundle: Path, name: str, raw: bytes):
        (bundle / name).write_bytes(raw)
        receipt = self.receipt(bundle)
        receipt["outputs"][name] = {"sha256": sha256(raw), "size_bytes": len(raw)}
        (bundle / "receipt.json").write_bytes(json_bytes(receipt))

    def rewrite_identifiability_parent(self, bundle: Path, parent: dict):
        parent_raw = json_bytes(parent)
        parent_hash = sha256(parent_raw)
        (bundle / "source_receipt.json").write_bytes(parent_raw)
        manifest = json.loads((bundle / "source_manifest.json").read_text(encoding="utf-8"))
        manifest["simulation_receipt_sha256"] = parent_hash
        manifest_raw = json_bytes(manifest)
        (bundle / "source_manifest.json").write_bytes(manifest_raw)
        receipt = self.receipt(bundle)
        receipt["metadata"]["parent_receipt_sha256"] = parent_hash
        receipt["input_sha256"] = sha256(manifest_raw)
        for name, raw in (("source_receipt.json", parent_raw), ("source_manifest.json", manifest_raw)):
            receipt["outputs"][name] = {"sha256": sha256(raw), "size_bytes": len(raw)}
        (bundle / "receipt.json").write_bytes(json_bytes(receipt))

    def assert_rerun_rejected_without_child(self, source: Path, output: Path):
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            with self.assertRaises(InputError):
                rerun_bundle(source, output)
        execute.assert_not_called()
        self.assertFalse(output.exists(), "invalid preflight metadata must not publish a report")

    def assert_subprocess_cli_input_error(self, source: Path, output: Path, marker: Path):
        script = (
            'import sys\n'
            'from pathlib import Path\n'
            'from unittest import mock\n'
            'from wombmodels.cli import main\n'
            'def unexpected_child(*args, **kwargs):\n'
            '    Path(sys.argv[3]).write_text("child executed", encoding="utf-8")\n'
            '    raise AssertionError("unexpected child execution")\n'
            'with mock.patch("wombmodels.reproduction._execute_entry_point", side_effect=unexpected_child):\n'
            '    main(["rerun-bundle", "--bundle", sys.argv[1], "--out", sys.argv[2]])\n'
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(EXAMPLES.parent / "src") + os.pathsep + environment.get("PYTHONPATH", "")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-B", "-c", script, str(source), str(output), str(marker)],
            capture_output=True, text=True, timeout=30, env=environment, check=False,
        )
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stdout + completed.stderr)
        self.assertIn("error:", completed.stderr)
        self.assertFalse(output.exists(), "malformed input must not publish a destination or report")
        self.assertFalse(marker.exists(), "malformed input must not execute the trusted child")

    def test_constants_and_corrected_reproduction_plans(self):
        self.assertEqual(RERUN_ENTRY_POINTS, {
            "synthetic_exchange_software_fixture": "simulate/1",
            "synthetic_exchange_observability_diagnostic": "identifiability/1",
        })
        self.assertEqual(REPRODUCTION_BUNDLE_KIND, "synthetic_bundle_reproduction_check")
        self.assertEqual(RERUN_TIMEOUT_SECONDS, 120)
        expected = {
            self.simulation: (["input_config.json"], {"input_config.json": "config.json"}),
            self.identifiability: (
                ["source_manifest.json", "source_config.json", "source_trajectory.csv", "source_receipt.json"],
                {"source_config.json": "config.json", "source_trajectory.csv": "simulation/trajectory.csv",
                 "source_receipt.json": "simulation/receipt.json"},
            ),
        }
        for bundle, (inputs, mapping) in expected.items():
            with self.subTest(bundle=bundle.name):
                plan = json.loads((bundle / "reproduction_plan.json").read_text(encoding="utf-8"))
                self.assertEqual(plan["entry_point"], RERUN_ENTRY_POINTS[plan["bundle_kind"]])
                self.assertEqual(plan["inputs"], inputs)
                self.assertEqual(plan["input_mapping"], mapping)
                self.assertEqual(plan["report_kind"], REPRODUCTION_BUNDLE_KIND)
                self.assertTrue(plan["command"].startswith("python -I -B "), plan["command"])
                self.assertNotIn("shell", plan["command"].lower())

    def test_fresh_simulation_rerun_is_exact_and_strictly_verifiable(self):
        output = self.root / "simulation-reproduction"
        returned = rerun_bundle(self.simulation, output)
        report = self.report(output)
        self.assertEqual(returned, report)
        self.assertEqual(report["reproduction_status"], "reproduced_exact")
        self.assertEqual(report["source_bundle_kind"], "synthetic_exchange_software_fixture")
        self.assertEqual(report["entry_point"], "simulate/1")
        self.assertTrue(report["bytes_verified"])
        self.assertEqual(report["ancestry_resolved"], "no_parent_declared")
        self.assertTrue(report["implementation_match"])
        self.assertTrue(report["comparison"]["exact_match"])
        self.assertTrue(report["payload_diagnostic"]["exact_match"])
        self.assertEqual(report["comparison"]["expected_inventory"],
                         report["comparison"]["actual_inventory"])
        self.assertEqual(report["scientific_review"], "not_established_by_this_tool")
        self.assertFalse(report["biological_measurements"])
        self.assertFalse(report["physiologically_calibrated"])
        self.assertFalse(report["human_gestation_prediction"])
        verified = verify_bundle(output, strict=True)
        self.assertTrue(verified["bytes_verified"], verified["errors"])
        self.assertEqual(verified["bundle_kind"], REPRODUCTION_BUNDLE_KIND)
        self.assertEqual(verified["reproduction"], "not_attempted")
        required = {"source_bundle_receipt.json", "source_reproduction_plan.json",
                    "rerun_input_manifest.json", "input_config.json", "reproduction_report.json",
                    "REPORT.md", "reproduction_plan.json", "receipt.json"}
        self.assertTrue(required <= {path.name for path in output.iterdir()})

    def test_relocated_identifiability_runs_after_both_originals_are_unavailable(self):
        moved = self.root / "relocated" / "renamed-identifiability"
        moved.parent.mkdir()
        shutil.copytree(self.identifiability, moved)
        shutil.rmtree(self.simulation)
        shutil.rmtree(self.identifiability)
        output = self.root / "identifiability-reproduction"
        report = rerun_bundle(moved, output)
        self.assertEqual(report["reproduction_status"], "reproduced_exact")
        self.assertEqual(report["ancestry_resolved"], "resolved")
        self.assertTrue(report["comparison"]["exact_match"])
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
        manifest = json.loads((output / "rerun_input_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([item["source"] for item in manifest["inputs"]],
                         ["source_config.json", "source_receipt.json", "source_trajectory.csv"])
        self.assertEqual({item["staged"] for item in manifest["inputs"]},
                         {"config.json", "simulation/receipt.json", "simulation/trajectory.csv"})
        for source in ("source_manifest.json", "source_config.json", "source_trajectory.csv", "source_receipt.json"):
            self.assertEqual((output / source).read_bytes(), (moved / source).read_bytes())

    def test_relocated_simulation_runs_after_original_is_unavailable(self):
        moved = self.root / "relocated" / "renamed-simulation"
        moved.parent.mkdir()
        shutil.copytree(self.simulation, moved)
        shutil.rmtree(self.simulation)
        output = self.root / "simulation-reproduction"
        report = rerun_bundle(moved, output)
        self.assertEqual(report["reproduction_status"], "reproduced_exact")
        self.assertEqual(report["ancestry_resolved"], "no_parent_declared")
        self.assertTrue(report["comparison"]["exact_match"])
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_cli_strict_verification_rejects_one_byte_mutation_before_rerun(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(EXAMPLES.parent / "src") + os.pathsep + environment.get("PYTHONPATH", "")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        for source, target_name in (
                (self.simulation, "trajectory.csv"),
                (self.identifiability, "observability_report.json")):
            with self.subTest(kind=source.name):
                mutated = self.root / f"mutated-{source.name}"
                shutil.copytree(source, mutated)
                target = mutated / target_name
                target.write_bytes(target.read_bytes() + b"\n")
                checked = subprocess.run(
                    [sys.executable, "-B", "-m", "wombmodels", "verify-bundle",
                     "--bundle", str(mutated), "--strict"],
                    capture_output=True, text=True, timeout=30, env=environment, check=False)
                self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
                report = json.loads(checked.stdout)
                self.assertFalse(report["bytes_verified"])
                self.assertTrue(any(target_name in error and "receipt hash" in error
                                    for error in report["errors"]), report["errors"])
                output = self.root / f"mutated-{source.name}-report"
                rerun = subprocess.run(
                    [sys.executable, "-B", "-m", "wombmodels", "rerun-bundle",
                     "--bundle", str(mutated), "--out", str(output)],
                    capture_output=True, text=True, timeout=30, env=environment, check=False)
                self.assertEqual(rerun.returncode, 2, rerun.stdout + rerun.stderr)
                self.assertIn("Source bundle failed strict verification", rerun.stderr)
                self.assertNotIn("Traceback", rerun.stdout + rerun.stderr)
                self.assertFalse(output.exists())

    def test_repeated_report_bundles_are_byte_deterministic(self):
        first = self.root / "reproduction-one"
        second = self.root / "reproduction-two"
        rerun_bundle(self.simulation, first)
        rerun_bundle(self.simulation, second)
        self.assertEqual({path.name for path in first.iterdir()}, {path.name for path in second.iterdir()})
        for path in first.iterdir():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())

    def test_destination_collision_and_nested_destination_do_not_execute_or_mutate_source(self):
        before = {path.name: path.read_bytes() for path in self.simulation.iterdir()}
        (self.root / "occupied").mkdir()
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            with self.assertRaises(InputError):
                rerun_bundle(self.simulation, self.root / "occupied")
            with self.assertRaises(InputError):
                rerun_bundle(self.simulation, self.simulation / "nested-output")
        execute.assert_not_called()
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.simulation.iterdir()})

    def test_source_tamper_and_unsupported_kind_do_not_execute(self):
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            target = self.simulation / "trajectory.csv"
            original = target.read_bytes()
            target.write_bytes(original + b"\n")
            with self.assertRaises(InputError):
                rerun_bundle(self.simulation, self.root / "tamper-report")
            target.write_bytes(original)
            receipt = self.receipt(self.simulation)
            receipt["bundle_kind"] = "synthetic_exchange_design_sweep"
            (self.simulation / "receipt.json").write_bytes(json_bytes(receipt))
            with self.assertRaisesRegex(InputError, "not supported"):
                rerun_bundle(self.simulation, self.root / "unsupported-report")
        execute.assert_not_called()

    def test_missing_parent_does_not_execute(self):
        (self.identifiability / "source_receipt.json").unlink()
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            with self.assertRaises(InputError):
                rerun_bundle(self.identifiability, self.root / "missing-parent-report")
        execute.assert_not_called()

    def test_recomputed_receipt_plan_substitutions_never_execute(self):
        cases = ("command_substitution", "absolute_path", "wrong_mapping_type",
                 "wrong_inputs_type", "wrong_version_type", "unsafe_version_syntax")
        for original in (self.simulation, self.identifiability):
            for case in cases:
                with self.subTest(kind=original.name, case=case):
                    source = self.root / f"plan-{original.name}-{case}"
                    shutil.copytree(original, source)
                    plan = json.loads((source / "reproduction_plan.json").read_text(encoding="utf-8"))
                    if case == "command_substitution":
                        plan["command"] = "sh -c arbitrary-bundle-selected-command"
                    elif case == "absolute_path":
                        first_input = next(iter(plan["input_mapping"]))
                        plan["input_mapping"][first_input] = str(self.root / "absolute-config.json")
                    elif case == "wrong_mapping_type":
                        plan["input_mapping"] = []
                    elif case == "wrong_inputs_type":
                        plan["inputs"] = "input_config.json"
                    elif case == "wrong_version_type":
                        plan["package_version"] = []
                    else:
                        plan["python_version"] = "../3.12"
                    self.replace_declared(source, "reproduction_plan.json", json_bytes(plan))
                    self.assertTrue(verify_bundle(source, strict=True)["bytes_verified"])
                    output = self.root / f"report-{original.name}-{case}"
                    with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
                        with self.assertRaisesRegex(InputError, "plan"):
                            rerun_bundle(source, output)
                    execute.assert_not_called()
                    self.assertFalse(output.exists())

    def test_receipt_plan_version_disagreement_never_executes(self):
        for original in (self.simulation, self.identifiability):
            for field, value in (("package_version", "0.0.0"), ("python_version", "3.0.0")):
                with self.subTest(kind=original.name, field=field):
                    source = self.root / f"disagreement-{original.name}-{field}"
                    shutil.copytree(original, source)
                    receipt = self.receipt(source)
                    receipt[field] = value
                    (source / "receipt.json").write_bytes(json_bytes(receipt))
                    self.assertTrue(verify_bundle(source, strict=True)["bytes_verified"])
                    output = self.root / f"disagreement-report-{original.name}-{field}"
                    with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
                        with self.assertRaisesRegex(InputError, "plan"):
                            rerun_bundle(source, output)
                    execute.assert_not_called()
                    self.assertFalse(output.exists())

    def test_subprocess_cli_rejects_hash_valid_malformed_metadata_without_child(self):
        for original in (self.simulation, self.identifiability):
            for index, malformed in enumerate((None, [], "malformed")):
                with self.subTest(kind=original.name, malformed=malformed):
                    source = self.root / f"metadata-{original.name}-{index}"
                    shutil.copytree(original, source)
                    receipt = self.receipt(source)
                    receipt["metadata"] = malformed
                    (source / "receipt.json").write_bytes(json_bytes(receipt))
                    verification = verify_bundle(source, strict=True)
                    self.assertTrue(verification["bytes_verified"], verification["errors"])
                    self.assert_subprocess_cli_input_error(
                        source, self.root / f"metadata-report-{original.name}-{index}",
                        self.root / f"metadata-child-{original.name}-{index}")

    def test_hash_valid_malformed_parent_structures_are_input_errors_without_child(self):
        cases = [(location, value) for location in
                 ("parent_outputs", "parent_metadata", "output_entry", "output_sha256", "output_size")
                 for value in (None, [], "malformed")]
        for index, (location, malformed) in enumerate(cases):
            with self.subTest(location=location, malformed=malformed):
                source = self.root / f"parent-structure-{index}"
                shutil.copytree(self.identifiability, source)
                parent = json.loads((source / "source_receipt.json").read_text(encoding="utf-8"))
                if location == "parent_outputs":
                    parent["outputs"] = malformed
                elif location == "parent_metadata":
                    parent["metadata"] = malformed
                elif location == "output_entry":
                    parent["outputs"]["trajectory.csv"] = malformed
                elif location == "output_sha256":
                    parent["outputs"]["trajectory.csv"]["sha256"] = malformed
                else:
                    parent["outputs"]["trajectory.csv"]["size_bytes"] = malformed
                self.rewrite_identifiability_parent(source, parent)
                verification = verify_bundle(source, strict=True)
                self.assertTrue(verification["bytes_verified"], verification["errors"])
                self.assertEqual(verification["ancestry_resolved"], "resolved")
                output = self.root / f"parent-structure-report-{index}"
                with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
                    with self.assertRaises(InputError):
                        rerun_bundle(source, output)
                execute.assert_not_called()
                self.assertFalse(output.exists())

    def test_source_limitations_require_literal_false_without_child_or_output(self):
        fields = {
            self.simulation: ("physiologically_calibrated", "biological_assay_performed",
                              "human_gestation_prediction"),
            self.identifiability: ("biological_measurements", "physiologically_calibrated",
                                   "human_gestation_prediction"),
        }
        cases = (("true", True), ("integer", 1), ("string", "false"), ("none", None),
                 ("missing", ...))
        for original, names in fields.items():
            for field in names:
                for label, value in cases:
                    with self.subTest(kind=original.name, field=field, case=label):
                        source = self.root / f"limitations-{original.name}-{field}-{label}"
                        shutil.copytree(original, source)
                        receipt = self.receipt(source)
                        if value is ...:
                            receipt["metadata"].pop(field)
                        else:
                            receipt["metadata"][field] = value
                        (source / "receipt.json").write_bytes(json_bytes(receipt))
                        verification = verify_bundle(source, strict=True)
                        self.assertTrue(verification["bytes_verified"], verification["errors"])
                        self.assert_rerun_rejected_without_child(
                            source, self.root / f"limitations-report-{original.name}-{field}-{label}")

    def test_parent_limitations_require_literal_false_without_child_or_output(self):
        cases = (("true", True), ("integer", 1), ("string", "false"), ("none", None),
                 ("missing", ...))
        for field in ("physiologically_calibrated", "biological_assay_performed",
                      "human_gestation_prediction"):
            for label, value in cases:
                with self.subTest(field=field, case=label):
                    source = self.root / f"parent-limitations-{field}-{label}"
                    shutil.copytree(self.identifiability, source)
                    parent = json.loads((source / "source_receipt.json").read_text(encoding="utf-8"))
                    if value is ...:
                        parent["metadata"].pop(field)
                    else:
                        parent["metadata"][field] = value
                    self.rewrite_identifiability_parent(source, parent)
                    verification = verify_bundle(source, strict=True)
                    self.assertTrue(verification["bytes_verified"], verification["errors"])
                    self.assertEqual(verification["ancestry_resolved"], "resolved")
                    self.assert_rerun_rejected_without_child(
                        source, self.root / f"parent-limitations-report-{field}-{label}")

    def test_hash_valid_parent_metadata_closure_failures_never_execute_or_publish(self):
        cases = (
            "package_type", "package_syntax", "package_disagreement",
            "python_type", "python_syntax", "python_disagreement",
            "implementation_type", "implementation_missing", "implementation_extra",
            "implementation_name", "implementation_uppercase", "implementation_short",
            "implementation_value_type", "publication_type", "publication_disagreement",
            "output_missing", "output_extra", "config_hash", "config_size", "parent_input_hash",
        )
        for case in cases:
            with self.subTest(case=case):
                source = self.root / f"parent-closure-{case}"
                shutil.copytree(self.identifiability, source)
                parent = json.loads((source / "source_receipt.json").read_text(encoding="utf-8"))
                if case == "package_type":
                    parent["package_version"] = None
                elif case == "package_syntax":
                    parent["package_version"] = "../0.5.0"
                elif case == "package_disagreement":
                    parent["package_version"] = "0.0.0"
                elif case == "python_type":
                    parent["python_version"] = []
                elif case == "python_syntax":
                    parent["python_version"] = "../3.12.16"
                elif case == "python_disagreement":
                    parent["python_version"] = "3.0.0"
                elif case == "implementation_type":
                    parent["implementation_sha256"] = []
                elif case == "implementation_missing":
                    parent.pop("implementation_sha256")
                elif case == "implementation_extra":
                    parent["implementation_sha256"]["unexpected.py"] = "0" * 64
                elif case == "implementation_name":
                    name = sorted(parent["implementation_sha256"])[0]
                    parent["implementation_sha256"]["src/wombmodels/not-current.py"] = (
                        parent["implementation_sha256"].pop(name))
                elif case in {"implementation_uppercase", "implementation_short",
                              "implementation_value_type"}:
                    name = sorted(parent["implementation_sha256"])[0]
                    value = {"implementation_uppercase": "A" * 64,
                             "implementation_short": "0" * 63,
                             "implementation_value_type": True}[case]
                    parent["implementation_sha256"][name] = value
                elif case == "publication_type":
                    parent["publication_contract"] = None
                elif case == "publication_disagreement":
                    parent["publication_contract"] = "any directory; any order"
                elif case == "output_missing":
                    parent["outputs"].pop("REPORT.md")
                elif case == "output_extra":
                    parent["outputs"]["extra.json"] = {"sha256": "0" * 64, "size_bytes": 0}
                elif case == "config_hash":
                    parent["outputs"]["input_config.json"]["sha256"] = "0" * 64
                elif case == "config_size":
                    parent["outputs"]["input_config.json"]["size_bytes"] += 1
                else:
                    parent["input_sha256"] = "0" * 64
                self.rewrite_identifiability_parent(source, parent)
                verification = verify_bundle(source, strict=True)
                self.assertTrue(verification["bytes_verified"], verification["errors"])
                self.assertEqual(verification["ancestry_resolved"], "resolved")
                self.assert_rerun_rejected_without_child(
                    source, self.root / f"parent-closure-report-{case}")

    def test_parent_implementation_hash_values_need_not_equal_current_hashes(self):
        source = self.root / "parent-archived-implementation"
        shutil.copytree(self.identifiability, source)
        parent = json.loads((source / "source_receipt.json").read_text(encoding="utf-8"))
        for name in parent["implementation_sha256"]:
            parent["implementation_sha256"][name] = "0" * 64
        self.rewrite_identifiability_parent(source, parent)
        loaded = _load_rerun_source(source)
        archived = loaded["inputs"]["source_receipt.json"]
        archived_parent = json.loads(archived)
        self.assertEqual(set(archived_parent["implementation_sha256"]), set(implementation_hashes()))
        self.assertTrue(all(value == "0" * 64
                            for value in archived_parent["implementation_sha256"].values()))

    def test_subprocess_cli_rejects_limitations_and_parent_closure_without_child(self):
        simulation = self.root / "cli-literal-limitation"
        shutil.copytree(self.simulation, simulation)
        receipt = self.receipt(simulation)
        receipt["metadata"]["physiologically_calibrated"] = 1
        (simulation / "receipt.json").write_bytes(json_bytes(receipt))
        self.assert_subprocess_cli_input_error(
            simulation, self.root / "cli-literal-limitation-report",
            self.root / "cli-literal-limitation-child")

        identifiability = self.root / "cli-parent-closure"
        shutil.copytree(self.identifiability, identifiability)
        parent = json.loads((identifiability / "source_receipt.json").read_text(encoding="utf-8"))
        parent["publication_contract"] = "unbounded publication"
        self.rewrite_identifiability_parent(identifiability, parent)
        self.assert_subprocess_cli_input_error(
            identifiability, self.root / "cli-parent-closure-report",
            self.root / "cli-parent-closure-child")

    def test_implementation_and_package_mismatches_publish_could_not_run_without_execution(self):
        for field, value in (("implementation_sha256", None), ("package_version", "0.0.0")):
            with self.subTest(field=field):
                source = self.root / f"source-{field}"
                shutil.copytree(self.simulation, source)
                receipt = self.receipt(source)
                if field == "implementation_sha256":
                    key = sorted(implementation_hashes())[0]
                    receipt[field][key] = "0" * 64
                    receipt[field]["DO_NOT_COPY_THIS_SECRET_NAME"] = "f" * 64
                else:
                    receipt[field] = value
                (source / "receipt.json").write_bytes(json_bytes(receipt))
                if field == "package_version":
                    plan = json.loads((source / "reproduction_plan.json").read_text(encoding="utf-8"))
                    plan[field] = value
                    self.replace_declared(source, "reproduction_plan.json", json_bytes(plan))
                output = self.root / f"report-{field}"
                with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
                    report = rerun_bundle(source, output)
                execute.assert_not_called()
                self.assertEqual(report["reproduction_status"], "could_not_run")
                self.assertFalse(report["implementation_match"])
                self.assertEqual(report["comparison"]["actual_inventory"]["count"], 0)
                self.assertNotIn("DO_NOT_COPY_THIS_SECRET_NAME", json.dumps(report))
                self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_valid_but_different_child_output_is_not_reproduced(self):
        def different_output(entry_point, staged, output, *, timeout):
            config_path = staged / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["monitor"]["seed"] += 1
            config_path.write_bytes(json_bytes(config))
            simulate(config_path, output)
            return {"outcome": "completed", "returncode": 0}

        output = self.root / "different-report"
        with mock.patch("wombmodels.reproduction._execute_entry_point", side_effect=different_output):
            report = rerun_bundle(self.simulation, output)
        self.assertEqual(report["reproduction_status"], "not_reproduced")
        self.assertFalse(report["comparison"]["exact_match"])
        self.assertIn("trajectory.csv", report["comparison"]["changed"])
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_full_inventory_comparison_distinguishes_missing_extra_and_changed(self):
        expected = {"input_config.json": b"input", "trajectory.csv": b"payload",
                    "REPORT.md": b"report", "receipt.json": b"old receipt"}
        actual = {"input_config.json": b"input", "trajectory.csv": b"payload",
                  "extra.txt": b"extra", "receipt.json": b"new receipt"}
        comparison = _compare_output_bytes(expected, actual, {"input_config.json"})
        self.assertFalse(comparison["exact_match"])
        self.assertEqual(comparison["missing"], ["REPORT.md"])
        self.assertEqual(comparison["extra"], ["extra.txt"])
        self.assertEqual(comparison["changed"], ["receipt.json"])
        self.assertEqual(comparison["expected_inventory"]["count"], 4)
        self.assertEqual(comparison["actual_inventory"]["count"], 4)
        self.assertFalse(comparison["payload_diagnostic"]["exact_match"])

    def test_payload_only_match_cannot_override_a_changed_receipt(self):
        expected = {"input_config.json": b"input", "trajectory.csv": b"payload", "receipt.json": b"old"}
        actual = {"input_config.json": b"input", "trajectory.csv": b"payload", "receipt.json": b"new"}
        comparison = _compare_output_bytes(expected, actual, {"input_config.json"})
        self.assertFalse(comparison["exact_match"])
        self.assertTrue(comparison["payload_diagnostic"]["exact_match"])
        self.assertIn("cannot override", comparison["payload_diagnostic"]["interpretation"])

    def test_traversal_and_undeclared_symlink_sources_never_execute(self):
        traversal = self.root / "traversal-source"
        shutil.copytree(self.simulation, traversal)
        receipt = self.receipt(traversal)
        receipt["outputs"]["../escape"] = {"sha256": "0" * 64, "size_bytes": 0}
        (traversal / "receipt.json").write_bytes(json_bytes(receipt))
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            with self.assertRaises(InputError):
                rerun_bundle(traversal, self.root / "traversal-report")
        execute.assert_not_called()

        linked = self.root / "undeclared-symlink-source"
        shutil.copytree(self.simulation, linked)
        outside = self.root / "outside-notes"
        outside.write_text("not declared\n", encoding="utf-8")
        try:
            (linked / "notes-link").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("this platform does not permit creating test symlinks")
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            with self.assertRaises(InputError):
                rerun_bundle(linked, self.root / "undeclared-symlink-report")
        execute.assert_not_called()

    def test_mismatch_lists_and_details_are_bounded(self):
        expected = {f"output-{index:03d}.bin": bytes([index % 256]) for index in range(100)}
        comparison = _compare_output_bytes(expected, {}, set())
        self.assertEqual(comparison["mismatch_count"], 100)
        self.assertEqual(len(comparison["missing"]), 32)
        self.assertEqual(len(comparison["mismatch_details"]), 32)
        self.assertEqual(comparison["mismatch_details_omitted"], 68)
        self.assertEqual(comparison["actual_inventory"], {"count": 0, "files": {}})

    def test_executor_uses_isolated_fixed_command_and_scrubbed_environment(self):
        staged = self.root / "direct-staging"
        staged.mkdir()
        shutil.copyfile(EXAMPLES / "exchange_fixture.json", staged / "config.json")
        captured = {}
        real_popen = subprocess.Popen

        def observing_popen(command, **kwargs):
            captured["command"] = command
            captured.update(kwargs)
            return real_popen(command, **kwargs)

        with mock.patch.dict(os.environ, {"A_SECRET_THAT_MUST_NOT_PROPAGATE": "secret"}), \
                mock.patch("wombmodels.reproduction.subprocess.Popen", side_effect=observing_popen):
            result = _execute_entry_point("simulate/1", staged, self.root / "direct-output", timeout=10)
        self.assertEqual(result["outcome"], "completed", result)
        self.assertEqual(captured["command"][:3], [sys.executable, "-I", "-B"])
        self.assertIsInstance(captured["command"], list)
        self.assertNotIn("shell", captured)
        self.assertNotIn("A_SECRET_THAT_MUST_NOT_PROPAGATE", captured["env"])
        self.assertEqual(captured["cwd"], str(staged))
        self.assertTrue(verify_bundle(self.root / "direct-output", strict=True)["bytes_verified"])

    def test_nonzero_child_exit_is_could_not_run(self):
        staged = self.root / "bad-staging"
        staged.mkdir()
        (staged / "config.json").write_bytes(b"{}")
        result = _execute_entry_point("simulate/1", staged, self.root / "bad-output", timeout=10)
        self.assertEqual(result["outcome"], "nonzero_exit")
        self.assertNotEqual(result["returncode"], 0)
        self.assertNotIn("stderr_text", result)

    def test_timeout_kills_the_child_and_is_bounded(self):
        class HangingProcess:
            def __init__(self):
                self.stdout = io.BytesIO(b"")
                self.stderr = io.BytesIO(b"")
                self.killed = False

            def wait(self, timeout=None):
                if self.killed:
                    return -9
                raise subprocess.TimeoutExpired("trusted-runner", timeout)

            def kill(self):
                self.killed = True

        process = HangingProcess()
        staged = self.root / "timeout-staging"
        staged.mkdir()
        with mock.patch("wombmodels.reproduction.subprocess.Popen", return_value=process):
            result = _execute_entry_point("simulate/1", staged, self.root / "timeout-output", timeout=0.01)
        self.assertEqual(result["outcome"], "timeout")
        self.assertTrue(process.killed)

    def test_output_capture_is_bounded_and_reports_no_stream_contents(self):
        class NoisyProcess:
            def __init__(self):
                self.stdout = io.BytesIO(b"x" * (MAX_CAPTURED_STREAM_BYTES + 1000))
                self.stderr = io.BytesIO(b"")
                self.killed = False

            def wait(self, timeout=None):
                return -9 if self.killed else 0

            def kill(self):
                self.killed = True

        staged = self.root / "noisy-staging"
        staged.mkdir()
        with mock.patch("wombmodels.reproduction.subprocess.Popen", return_value=NoisyProcess()):
            result = _execute_entry_point("simulate/1", staged, self.root / "noisy-output", timeout=10)
        self.assertEqual(result["outcome"], "output_limit")
        self.assertEqual(result["stdout"]["captured_size_bytes"], MAX_CAPTURED_STREAM_BYTES)
        self.assertTrue(result["stdout"]["truncated"])
        self.assertNotIn("xxx", json.dumps(result))

    def test_execution_failure_status_has_no_absolute_paths_or_stream_text(self):
        output = self.root / "failed-report"
        failure = {"outcome": "timeout", "returncode": None,
                   "stdout": {"captured_sha256": sha256(str(self.root).encode()),
                              "captured_size_bytes": 123, "truncated": False}}
        with mock.patch("wombmodels.reproduction._execute_entry_point", return_value=failure):
            report = rerun_bundle(self.simulation, output)
        self.assertEqual(report["reproduction_status"], "could_not_run")
        encoded = json.dumps(report)
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn("timestamp", encoded)
        self.assertNotIn("stdout_text", encoded)

    def test_symlink_destination_is_rejected_without_execution(self):
        target = self.root / "symlink-target"
        target.mkdir()
        link = self.root / "symlink-output"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("this platform does not permit creating test symlinks")
        with mock.patch("wombmodels.reproduction._execute_entry_point") as execute:
            with self.assertRaises(InputError):
                rerun_bundle(self.simulation, link)
        execute.assert_not_called()

    def test_cli_exit_zero_one_and_two(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["rerun-bundle", "--bundle", str(self.simulation),
                                   "--out", str(self.root / "cli-success")]), 0)
            receipt = self.receipt(self.simulation)
            receipt["package_version"] = "0.0.0"
            (self.simulation / "receipt.json").write_bytes(json_bytes(receipt))
            plan = json.loads((self.simulation / "reproduction_plan.json").read_text(encoding="utf-8"))
            plan["package_version"] = "0.0.0"
            self.replace_declared(self.simulation, "reproduction_plan.json", json_bytes(plan))
            self.assertEqual(main(["rerun-bundle", "--bundle", str(self.simulation),
                                   "--out", str(self.root / "cli-mismatch")]), 1)
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            main(["rerun-bundle", "--bundle", str(self.root / "missing"), "--out", str(self.root / "cli-error")])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
