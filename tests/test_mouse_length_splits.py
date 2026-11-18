from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main
from wombmodels.mouse_length_splits import _group_holdouts, _match_panel_cells, audit_mouse_length_splits
from tests.local_evidence import ARTIFACTS, requires_local_evidence


DATASET = (Path(__file__).resolve().parents[1] / "config" / "observations"
           / "aguilera_castrejon_2021_length_source_candidate.json")


class MouseLengthSplitsTests(unittest.TestCase):
    def test_cli_preserves_axis_clock_and_group_membership(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["audit-mouse-length-splits", "--dataset", str(DATASET),
                                       "--out", str(output)]), 0)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
            summary = json.loads((output / "splits.json").read_bytes())

        groups = {group["group_id"]: group for group in summary["groups"]}
        record_ids = [record_id for group in groups.values() for record_id in group["observation_ids"]]
        source = json.loads(DATASET.read_bytes())
        self.assertEqual(len(groups), 8)
        self.assertEqual(len(record_ids), 216)
        self.assertCountEqual(record_ids, [record["record_id"] for record in source["observations"]])
        self.assertEqual(summary["records_with_reported_embryo_id"], 0)
        self.assertEqual(summary["source_review_status"], "candidate")
        self.assertEqual(summary["split_specimen_independence"], "unresolved")
        self.assertEqual(summary["workbook_verification"], {"status": "not_supplied"})
        self.assertEqual(Counter(fold["time_coverage"] for fold in summary["holdouts"]), {
            "insufficient_training_times": 2, "interpolation": 2, "extrapolation": 4,
        })

        expected = {
            "in utero": (10.5, (9.5, 11), 4895.383333333333, -168.325333333333),
            "ex utero": (3, (2, 4), 4315.956471544715, 129.180621478540),
        }
        bracketed = set()
        for fold in summary["holdouts"]:
            group = groups[fold["held_out_group_id"]]
            if group["measurement_axis"] == "antero-posterior":
                self.assertEqual(fold["training_group_ids"], [])
            for training_id in fold["training_group_ids"]:
                training = groups[training_id]
                for key in ("condition", "measurement_axis", "source_time_unit", "length_unit"):
                    self.assertEqual(group[key], training[key])
                self.assertNotEqual(group["source_time"], training["source_time"])
            if fold["time_coverage"] == "interpolation":
                condition = group["condition"]
                time, training_times, reference, difference = expected[condition]
                self.assertEqual(group["source_time"], time)
                self.assertEqual(tuple(fold["training_times"]), training_times)
                comparison = fold["group_mean_comparison"]
                self.assertAlmostEqual(comparison["interpolated_mean_length"], reference)
                self.assertAlmostEqual(comparison["observed_minus_interpolated"], difference)
                self.assertAlmostEqual(group["mean_length"], reference + difference)
                bracketed.add(condition)
            else:
                self.assertIsNone(fold["group_mean_comparison"])
        self.assertEqual(bracketed, set(expected))

    def test_held_out_lengths_cannot_change_their_reference(self):
        records = json.loads(DATASET.read_bytes())["observations"]
        group_id = "ex utero/crown-rump/3"
        groups, original = _group_holdouts(records)
        held_out = next(group for group in groups if group["group_id"] == group_id)
        ids = set(held_out["observation_ids"])
        for record in records:
            if record["record_id"] in ids:
                record["observation"]["value"] += 100
        _, changed = _group_holdouts(records)
        original_fold = next(fold for fold in original if fold["held_out_group_id"] == group_id)
        changed_fold = next(fold for fold in changed if fold["held_out_group_id"] == group_id)
        before = original_fold["group_mean_comparison"]
        after = changed_fold["group_mean_comparison"]
        self.assertEqual(before["interpolated_mean_length"], after["interpolated_mean_length"])
        self.assertAlmostEqual(after["observed_minus_interpolated"],
                               before["observed_minus_interpolated"] + 100)

    def test_panel_cells_require_one_matching_value_row_and_column(self):
        record = {"source_locator": "Panel e!B3; row label 'row 1'",
                  "model_system": {"label": "Fixture; source group A"}, "observation": {"value": 1.5}}
        cells = {"A3": ("row 1", "text", None), "B2": ("A", "text", None), "B3": ("1.50", "numeric", "1.50")}
        self.assertEqual(_match_panel_cells(cells, [record]), 1)
        for address, replacement in [
            ("A3", ("row 2", "text", None)), ("B2", ("B", "text", None)),
            ("B3", ("1.51", "numeric", "1.51")), ("B3", (None, "numeric", None)),
            ("B3", ("invalid", "numeric", "invalid")), ("B4", ("2.0", "numeric", "2.0")),
        ]:
            with self.subTest(address=address, replacement=replacement), self.assertRaises(InputError):
                _match_panel_cells({**cells, address: replacement}, [record])
        with self.assertRaisesRegex(InputError, "repeated numeric source cell"):
            _match_panel_cells(cells, [record, record])

    @requires_local_evidence("aguilera-castrejon-source-data-2026-10-11")
    def test_publisher_workbook_and_rerun_instructions(self):
        workbook = ARTIFACTS / "aguilera-castrejon-source-data-2026-10-11" / "41586_2021_3416_MOESM11_ESM.xlsx"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["audit-mouse-length-splits", "--dataset", str(DATASET),
                                       "--workbook", str(workbook), "--out", str(output)]), 0)
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
            summary = json.loads((output / "splits.json").read_bytes())
            plan = json.loads((output / "reproduction_plan.json").read_bytes())
        check = summary["workbook_verification"]
        self.assertEqual((check["status"], check["matched_cells"], check["size_bytes"]), ("matched", 216, 15884))
        self.assertEqual(check["sha256"], json.loads(DATASET.read_bytes())["artifacts"][0]["sha256"])
        self.assertIn("--workbook", plan["command"])
        self.assertEqual(len(plan["inputs"]), 2)

    def test_changed_workbook_is_rejected_before_publishing(self):
        with TemporaryDirectory() as directory:
            workbook = Path(directory) / "modified.xlsx"
            workbook.write_bytes(b"different workbook")
            output = Path(directory) / "bundle"
            with self.assertRaisesRegex(InputError, "hash differs"):
                audit_mouse_length_splits(DATASET, output, workbook_path=workbook)
            self.assertFalse(output.exists())

    def test_changed_candidate_is_rejected_before_publishing(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "modified.json"
            path.write_bytes(DATASET.read_bytes() + b"\n")
            output = Path(directory) / "bundle"
            with self.assertRaisesRegex(InputError, "differs from the pinned data card"):
                audit_mouse_length_splits(path, output)
            self.assertFalse(output.exists())
