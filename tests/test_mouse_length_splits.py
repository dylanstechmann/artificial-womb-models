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
from wombmodels.mouse_length_splits import audit_mouse_length_splits


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
        self.assertEqual(Counter(fold["time_coverage"] for fold in summary["holdouts"]), {
            "insufficient_training_times": 2, "interpolation": 2, "extrapolation": 4,
        })

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
                bracketed.add((group["condition"], group["source_time"], tuple(fold["training_times"])))
        self.assertEqual(bracketed, {("in utero", 10.5, (9.5, 11)), ("ex utero", 3, (2, 4))})

    def test_changed_candidate_is_rejected_before_publishing(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "modified.json"
            path.write_bytes(DATASET.read_bytes() + b"\n")
            output = Path(directory) / "bundle"
            with self.assertRaisesRegex(InputError, "differs from the pinned data card"):
                audit_mouse_length_splits(path, output)
            self.assertFalse(output.exists())
