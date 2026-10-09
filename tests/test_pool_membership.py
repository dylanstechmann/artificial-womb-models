from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from wombmodels.artifacts import InputError
from wombmodels.bundle_verification import verify_bundle
from wombmodels.observations import observation_report, validate_dataset

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/observation_intake_fixture.json"


class PoolMembershipTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EXAMPLE.read_text())
        self.data["transitions"] = []
        for index, record in enumerate(self.data["observations"]):
            record["independent_unit"] = {"kind": "sample_pool", "id": f"invented-pool-{index}",
                "parent_id": None, "members": [{"kind": "other", "id": "invented-shared-member"},
                                               {"kind": "other", "id": f"invented-member-{index}"}]}
            record["observation"]["replicate_role"] = "summary_only"
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_overlapping_pools_are_preserved_and_audited_without_independent_n(self):
        source = self.root / "input.json"
        raw = json.dumps(self.data).encode()
        source.write_bytes(raw)
        output = self.root / "intake"
        observation_report(source, output)
        self.assertEqual((output / "input_dataset.json").read_bytes(), raw)
        report = json.loads((output / "observation_intake_report.json").read_text())
        self.assertEqual(report["declared_unit_membership"]["n_pool_records"], 2)
        self.assertEqual(report["declared_unit_membership"]["n_shared_identifier_keys"], 1)
        with (output / "shared_unit_membership.csv").open(newline="") as stream:
            shared = list(csv.DictReader(stream))
        self.assertEqual(shared[0]["unit_id"], "invented-shared-member")
        self.assertEqual(shared[0]["n_records"], "2")
        with (output / "unit_members.csv").open(newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 4)
        self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])

    def test_overlapping_independence_rejected_for_pool_pool_or_pool_direct_unit(self):
        for direct in (False, True):
            data = copy.deepcopy(self.data)
            data["observations"][0]["observation"]["replicate_role"] = "independent"
            if direct:
                data["observations"][1]["independent_unit"] = {
                    "kind": "other", "id": " invented-shared-member ", "parent_id": None}
            with self.subTest(direct=direct):
                with self.assertRaisesRegex(InputError, "overlapping.*independent"):
                    validate_dataset(data)

    def test_member_namespace_retains_parent_and_source_boundaries(self):
        data = copy.deepcopy(self.data)
        data["observations"][0]["observation"]["replicate_role"] = "independent"
        data["observations"][1]["independent_unit"]["members"][0]["parent_id"] = "invented-other-parent"
        validate_dataset(data)
        data = copy.deepcopy(self.data)
        artifact = copy.deepcopy(data["artifacts"][0])
        artifact["artifact_id"] = "invented-other-source"
        data["artifacts"].append(artifact)
        data["observations"][0]["observation"]["replicate_role"] = "independent"
        data["observations"][1]["source"]["artifact_id"] = "invented-other-source"
        validate_dataset(data)

    def test_missing_members_remain_unknown_and_do_not_prevent_legacy_intake(self):
        data = copy.deepcopy(self.data)
        del data["observations"][0]["independent_unit"]["members"]
        validate_dataset(data)
        self.assertEqual(data["observations"][0]["independent_unit"]["members"], [])
        validate_dataset(json.loads(EXAMPLE.read_text()))

    def test_malformed_members_fail(self):
        invalid = [None, [{"kind": "not_reported", "id": "x"}],
                   [{"kind": "sample_pool", "id": "x"}], [{"kind": "other", "id": None}],
                   [{"kind": "other", "id": " "}], [{"kind": "other", "id": "x", "extra": True}],
                   [{"kind": "other", "id": "x"}, {"kind": "other", "id": " x "}],
                   [{"kind": "other", "id": str(i)} for i in range(101)]]
        for members in invalid:
            data = copy.deepcopy(self.data)
            data["observations"][0]["independent_unit"]["members"] = members
            with self.subTest(members=members):
                with self.assertRaises(InputError):
                    validate_dataset(data)
        data = copy.deepcopy(self.data)
        data["observations"][0]["independent_unit"]["kind"] = "other"
        with self.assertRaisesRegex(InputError, "sample_pool"):
            validate_dataset(data)

    def test_same_pool_label_cannot_establish_individual_developmental_continuity(self):
        data = copy.deepcopy(self.data)
        data["observations"][1]["independent_unit"] = copy.deepcopy(data["observations"][0]["independent_unit"])
        data["transitions"] = [{"transition_id": "invented-pool-transition",
            "from_record_ids": [data["observations"][0]["record_id"]],
            "to_record_ids": [data["observations"][1]["record_id"]],
            "continuity_status": "demonstrated", "note": "Invented pool labels cannot prove individual development."}]
        with self.assertRaisesRegex(InputError, "individual developmental continuity"):
            validate_dataset(data)
        data["transitions"][0]["continuity_status"] = "not_reported"
        validate_dataset(data)
