"""Invented label/number fixtures test linkage logic, not biological effects."""
import copy
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from wombmodels import boundary_source as source
from wombmodels.artifacts import InputError, csv_bytes, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.cli import main


def native_fixture():
    rows = {
        "cell-counts.csv": [["E1", "123456", "0", "WT"], ["E1", "234567", "3", "het"]],
        "lengths.csv": [["E1", "123456", "4.000", "WT"], ["E1", "234567", "5", "het"],
                        ["E2", "234567", "6", "del"]],
        "displacement.csv": [["123456", "Downward", "EPI", "1", "1", "1", "-1.200"],
                             ["123456", "Downward", "TE_inner", "1", "1", "1.0", "-0.500"],
                             ["123456", "Downward", "EPI", "1", "1", "2", "-2"]],
        "tracks.csv": [["0", "0", "0", "0", "0", "0", "0", "0"],
                       ["1", "0", "0", "10", "-1", "2", "1", "1"]],
    }
    return {name: csv_bytes(source.HEADERS[name], [dict(zip(source.HEADERS[name], row)) for row in data])
            for name, data in rows.items()}


def archive_fixture(native=None, extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
        for name, raw in (native or native_fixture()).items():
            z.writestr(source.MEMBERS[name], raw)
        if extra:
            z.writestr(*extra)
    return stream.getvalue()


class BoundarySourceTests(unittest.TestCase):
    def test_compound_labels_pair_candidates_without_boundary_join(self):
        _, tables = source._recover(archive_fixture())
        endpoints, pairs, groups, q = source._link(tables)
        self.assertEqual(q["endpoint_linkage_counts"], {"key_match_candidate": 2, "length_only": 1})
        self.assertEqual(q["endpoint_embryo_labels_reused_across_datasets"], ["E1"])
        self.assertEqual(q["shared_dataset_labels_with_endpoints"], ["123456"])
        self.assertEqual(q["n_qualified_boundary_outcome_joins"], 0)
        self.assertEqual(q["zero_cell_counts_retained"], 1)
        self.assertEqual(endpoints[0]["cell_number_text"], "0")
        self.assertEqual(endpoints[0]["length_um_text"], "4.000")
        self.assertFalse(endpoints[0]["biological_identity_verified"])
        self.assertEqual(pairs[0]["EPI_source_row"], 2)
        self.assertEqual(pairs[0]["TE_inner_time_text"], "1.0")
        self.assertEqual(pairs[1]["linkage_status"], "tissue_counterpart_missing")
        self.assertIsNone(pairs[0]["embryo_id"])
        self.assertEqual(len(groups), 1)
        self.assertEqual(q["cell_tracks"]["n_original_track_labels"], 1)
        self.assertEqual(q["cell_tracks"]["n_individual_track_labels"], 2)

    def test_duplicate_endpoint_displacement_and_track_keys_rejected(self):
        _, original = source._recover(archive_fixture())
        for name in source.MEMBERS:
            with self.subTest(name=name):
                tables = copy.deepcopy(original)
                tables[name].append(copy.deepcopy(tables[name][0]))
                with self.assertRaisesRegex(InputError, "Duplicate source observation key"):
                    source._link(tables)

    def test_genotype_conflict_is_preserved_separately(self):
        _, tables = source._recover(archive_fixture())
        tables["lengths.csv"][0]["Genotype"] = "del"
        endpoints, _, _, q = source._link(tables)
        self.assertEqual(q["endpoint_linkage_counts"]["key_match_genotype_conflict"], 1)
        self.assertEqual(endpoints[0]["cell_genotype"], "WT")
        self.assertEqual(endpoints[0]["length_genotype"], "del")

    def test_malformed_nonfinite_missing_and_changed_headers_rejected(self):
        raw = native_fixture()["lengths.csv"]
        for value in (b"NaN", b"Infinity", b"-1", b"1e99999999", b"", b"1e" ):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    source._table(raw.replace(b"4.000", value), "lengths.csv")
        with self.assertRaises(InputError):
            source._table(raw.replace(b"Length (um)", b"Length (unknown)"), "lengths.csv")
        bad = native_fixture()["tracks.csv"].replace(b"0,10,", b"0,60,")
        with self.assertRaises(InputError):
            source._table(bad, "tracks.csv")
        with self.assertRaises(InputError):
            source._table(b"x" * 256_001, "lengths.csv")

    def test_archive_missing_duplicate_and_unsafe_members_rejected(self):
        native = native_fixture()
        del native["lengths.csv"]
        with self.assertRaises(InputError):
            source._recover(archive_fixture(native))
        for extra in (("../outside.txt", b"x"), (source.MEMBERS["lengths.csv"], b"x")):
            with self.subTest(extra=extra[0]):
                with self.assertRaises(InputError):
                    source._recover(archive_fixture(extra=extra))

    def test_hash_rejection_has_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "invented.zip"
            p.write_bytes(archive_fixture())
            with self.assertRaisesRegex(InputError, "size/hash"):
                source.audit_boundary_source(p, root / "audit")
            self.assertFalse((root / "audit").exists())

    def test_cli_native_bytes_receipt_exclusivity_relocation_and_tamper(self):
        native = native_fixture()
        raw = archive_fixture(native)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "invented.zip"
            p.write_bytes(raw)
            out = root / "audit"
            with patch.object(source, "ARCHIVE_SHA256", sha256(raw)):
                self.assertEqual(main(["audit-boundary-source", "--archive", str(p), "--out", str(out)]), 0)
                with self.assertRaises(InputError):
                    source.audit_boundary_source(p, out)
            self.assertEqual(p.read_bytes(), raw)
            for name, data in native.items():
                self.assertEqual((out / name).read_bytes(), data)
            q = json.loads((out / "qualification.json").read_bytes())
            self.assertFalse(q["biological_fit_performed"])
            plan = json.loads((out / "reproduction_plan.json").read_bytes())
            self.assertIn("external pinned source archive (not bundled)", plan["inputs"])
            self.assertIn("audit-boundary-source", plan["command"])
            moved = root / "moved"
            out.rename(moved)
            result = verify_bundle(moved, strict=True)
            self.assertTrue(result["bytes_verified"], result["errors"])
            self.assertEqual(result["scientific_review"], "not_established_by_this_tool")
            (moved / "lengths.csv").write_bytes(b"changed")
            self.assertFalse(verify_bundle(moved, strict=True)["bytes_verified"])


if __name__ == "__main__":
    unittest.main()
