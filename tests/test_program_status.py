import copy
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError, json_bytes, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.program_status import assess_register, publish_status


ROOT = Path(__file__).resolve().parents[1]


class ProgramStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.register = json.loads((ROOT / "config/program/roadmap.json").read_text(encoding="utf-8"))
        # Synthetic local planning evidence exercises integrity, never biological validity.
        raw = b"An accepted planning artifact for this isolated test.\n"
        (self.root / "planning.md").write_bytes(raw)
        self.ref = {"path": "planning.md", "sha256": sha256(raw)}
        for item in self.register["achievements"] + self.register["milestones"] + self.register["tasks"]:
            if item["status"] == "complete":
                item["evidence"] = [copy.deepcopy(self.ref)]
            elif item.get("evidence"):
                # Held or waiting items may cite real repository files; repoint them at
                # the synthetic artifact so integrity checks stay isolated from the tree.
                item["evidence"] = [copy.deepcopy(self.ref) for _ in item["evidence"]]

    def test_dependencies_do_not_advance_biological_gates(self):
        report = assess_register(self.register, self.root)
        available = {t["id"] for t in report["tasks"] if t["eligible_to_start"]}
        # The eligible set derives from the register's own declared statuses, so this
        # test tracks planning progress instead of rotting whenever a task completes.
        # Update the pinned structural spot-checks below in the same change as any
        # config/program/roadmap.json status or dependency edit.
        valid = report["completion_dependencies_valid"]
        expected = {item["id"] for item in self.register["tasks"]
                    if item["status"] == "ready"
                    and all(valid.get(dep, False) for dep in item["depends_on"])}
        self.assertEqual(available, expected)
        # Derived equality alone is near-tautological, so pin the substance too.
        self.assertEqual({item["id"] for item in self.register["tasks"]
                          if item["status"] == "ready"}, {"T15"})
        self.assertEqual(sorted(next(item for item in self.register["tasks"]
                                     if item["id"] == "T15")["depends_on"]), ["M01", "T12"])
        self.assertTrue(valid["M01"], "T15 depends on the verified baseline milestone")
        self.assertTrue(valid["T12"])
        for row in report["tasks"]:
            if row["eligible_to_start"]:
                self.assertEqual(row["declared_status"], "ready")
                self.assertTrue(row["dependencies_satisfied"])
                self.assertEqual(row["unmet_dependencies"], "")
        self.assertEqual(report["gate_statuses"], self.register["gates"])
        self.assertEqual(report["biological_gate_updates"], 0)
        self.assertEqual(report["scientific_review"], "not_established_by_this_tool")
        self.assertTrue(report["evidence_integrity_matches"])

    def test_stale_or_missing_completion_evidence_blocks_downstream_start(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                path = self.root / "planning.md"
                if missing:
                    path.unlink()
                else:
                    path.write_bytes(b"Changed after acceptance.\n")
                report = assess_register(self.register, self.root)
                self.assertFalse(report["evidence_integrity_matches"])
                self.assertFalse(any(t["eligible_to_start"] for t in report["tasks"]))
                self.assertEqual(report["biological_gate_updates"], 0)
                self.assertEqual(report["evidence_checks"][0]["status"],
                                 "missing" if missing else "changed_since_assessment")

    def test_completion_requires_pinned_evidence_and_explicit_release(self):
        task = self.register["tasks"][0]
        # Set both fields explicitly so the rule fires whatever the register already
        # declares; a completed item without pinned evidence is always rejected.
        task["status"] = "complete"
        task["evidence"] = []
        with self.assertRaisesRegex(InputError, "completed item"):
            assess_register(self.register, self.root)
        task["evidence"] = [copy.deepcopy(self.ref)]
        downstream = self.register["tasks"][1]
        downstream_id = downstream["id"]
        downstream["status"] = "waiting_dependency"
        report = assess_register(self.register, self.root)
        next_task = next(t for t in report["tasks"] if t["id"] == downstream_id)
        self.assertTrue(next_task["dependencies_satisfied"])
        self.assertFalse(next_task["eligible_to_start"])
        downstream["status"] = "ready"
        report = assess_register(self.register, self.root)
        self.assertTrue(next(t for t in report["tasks"]
                             if t["id"] == downstream_id)["eligible_to_start"])

    def test_dependency_cycle_and_malformed_ids_are_rejected(self):
        self.register["tasks"][0]["depends_on"] = ["T02"]
        with self.assertRaisesRegex(InputError, "cycle"):
            assess_register(self.register, self.root)
        self.register["tasks"][0]["depends_on"] = [{}]
        with self.assertRaisesRegex(InputError, "strings"):
            assess_register(self.register, self.root)

    def test_completed_descendant_cannot_bypass_unresolved_ancestor(self):
        ancestor, descendant, next_task = self.register["tasks"][0], self.register["tasks"][1], self.register["tasks"][3]
        descendant["status"] = "complete"
        descendant["evidence"] = [copy.deepcopy(self.ref)]
        next_task["status"] = "ready"
        for state in ("incomplete", "missing", "changed"):
            with self.subTest(state=state):
                ancestor["status"] = "ready" if state == "incomplete" else "complete"
                ancestor["evidence"] = [] if state == "incomplete" else [{
                    "path": "missing.md" if state == "missing" else "planning.md", "sha256": "0" * 64}]
                report = assess_register(self.register, self.root)
                self.assertTrue(report["completion_evidence_matches"]["T02"])
                self.assertFalse(report["completion_dependencies_valid"]["T02"])
                self.assertFalse(next(t for t in report["tasks"] if t["id"] == "T04")["eligible_to_start"])

    def test_nonfinite_or_boolean_effort_cannot_complete_a_timebox(self):
        for cap in (float("nan"), float("inf"), True, 0, 49):
            with self.subTest(cap=cap):
                self.register["tasks"][0]["agent_hour_cap"] = cap
                with self.assertRaisesRegex(InputError, "cap"):
                    assess_register(self.register, self.root)

    def test_evidence_cannot_escape_project_root(self):
        for path in ("../outside.md", "/outside.md", "C:/outside.md", "dir\\outside.md"):
            with self.subTest(path=path):
                self.register["milestones"][0]["evidence"][0]["path"] = path
                with self.assertRaisesRegex(InputError, "root"):
                    assess_register(self.register, self.root)

    def test_status_bundle_verifies_without_claiming_rerun_or_science(self):
        self.register["objective"] = "Owned ten-unit test system; no biology asserted by these synthetic files."
        register_path = self.root / "register.json"
        register_path.write_bytes(json_bytes(self.register))
        output = self.root / "status"
        receipt = publish_status(register_path, self.root, output)
        checked = verify_bundle(output, strict=True)
        self.assertTrue(checked["bytes_verified"], checked["errors"])
        self.assertEqual(checked["errors"], [])
        self.assertEqual(checked["reproduction"], "not_attempted")
        self.assertEqual(receipt["metadata"]["biological_gate_updates"], 0)
        self.assertEqual((output / "input_register.json").read_bytes(), register_path.read_bytes())
        view = (output / "PROGRAM_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("not_established", view)
        self.assertIn("Pinned evidence matches", view)
        self.assertIn(self.register["objective"], view)
        self.assertNotIn("Eventual access for ten or more children", view)
        with self.assertRaisesRegex(InputError, "already exists"):
            publish_status(register_path, self.root, output)


if __name__ == "__main__":
    unittest.main()
