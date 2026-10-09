"""Invented archives test byte recovery and rejection; no biological assays."""
from __future__ import annotations

import io
import json
import shutil
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError, read_json, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels import roelofsen_source as source
from wombmodels.observations import observation_report
from wombmodels.roelofsen_intake import candidate_intake


def guid(number):
    return f"{number:08X}-0000-0000-0000-000000000000"


def native_archive(index, *, bad_token=False, bad_shape=False, axis_title="Time (min)", label_format="text"):
    """Native test tables reproduce shape only; every number is invented."""
    buffer = io.BytesIO()
    csvs = {}
    with zipfile.ZipFile(buffer, "w") as archive:
        titles = ["THAL % of ID", "AM % of ID", "VA % of ID", "AP % of ID"] if index == 5 else ["Data 9"]
        for number, title in enumerate(titles, 1):
            identifier = guid(number)
            sets = [guid(100 + number*10 + k) for k in range(2 if index == 5 else 4)]
            axis_id = guid(500 + number)
            axis = {"format":"y_single", "title":axis_title, "attributes":["DS_ATTR_X"]} if index == 5 else {"format":label_format}
            archive.writestr(f"data/sets/{axis_id}.json", json.dumps(axis))
            axis_reference = {"xDataSet":axis_id, "xDataSetFormat":"y_single"} if index == 5 else {"rowTitlesDataSet":axis_id}
            sheet = {"title": {"string": title}, "table": {"uid": identifier, **axis_reference,
                "format": "xy" if index == 5 else "grouped", "replicatesCount": 4 if index == 5 else 6,
                "dataSets": sets}}
            archive.writestr(f"data/sheets/{identifier}/sheet.json", json.dumps(sheet))
            for set_id in sets:
                archive.writestr(f"data/sets/{set_id}.json", json.dumps({"format": "y_replicates", "title": "Invented source slot"}))
            rows = [[str(row) if index == 5 else f"Placenta {row+1}"] + ["1.2500"]*(8 if index == 5 else 24)
                    for row in range(11 if index == 5 else 4)]
            if bad_token:
                rows[0][1] = "NaN"
            if bad_shape:
                rows[0].pop()
            raw = ("\r\n".join(",".join(row) for row in rows)+"\r\n").encode()
            member = f"data/tables/{identifier}/data.csv"
            csvs[member] = raw
            archive.writestr(member, raw)
        archive.writestr("ignored-saved-analysis.json", "This is never evaluated")
        archive.writestr("padding.bin", b"x"*4096)
    return buffer.getvalue(), csvs


def cfb(native):
    contents = struct.pack("<I", len(native)+4) + native
    n_contents = (len(contents)+511)//512
    if n_contents > 120:
        raise AssertionError("Test helper needs one FAT sector")
    header = bytearray(512)
    header[:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<4H", header, 26, 3, 0xFFFE, 9, 6)
    for offset, value in {44:1, 48:1, 56:4096, 60:source.END, 68:source.END}.items():
        struct.pack_into("<I", header, offset, value)
    struct.pack_into("<109I", header, 76, 0, *([source.FREE]*108))
    fat = [source.FREE]*128
    fat[0], fat[1] = 0xFFFFFFFD, source.END
    for sector in range(2, 2+n_contents):
        fat[sector] = sector+1 if sector < 1+n_contents else source.END
    directory = bytearray(512)
    name = "CONTENTS\0".encode("utf-16-le")
    directory[:len(name)] = name
    struct.pack_into("<H", directory, 64, len(name))
    directory[66] = 2
    struct.pack_into("<I", directory, 116, 2)
    struct.pack_into("<Q", directory, 120, len(contents))
    return bytes(header) + struct.pack("<128I", *fat) + bytes(directory) + contents.ljust(n_contents*512, b"\0")


def supplement(*, bad_token=False):
    buffer = io.BytesIO()
    expected_csvs = []
    with zipfile.ZipFile(buffer, "w") as archive:
        for index in (5, 6):
            native, csvs = native_archive(index, bad_token=bad_token)
            archive.writestr(f"word/embeddings/oleObject{index}.bin", cfb(native))
            expected_csvs.extend(csvs.values())
    return buffer.getvalue(), expected_csvs


class NativeSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_cfb_recovers_exact_native_bytes_and_leaves_saved_analysis_unexecuted(self):
        native, csvs = native_archive(5)
        self.assertEqual(source._regular_contents(cfb(native)), native)
        tables = source._tables(native, 5)
        self.assertEqual(len(tables), 4)
        for table in tables:
            self.assertEqual(table["csv_raw"], csvs[table["csv_member"]])
            self.assertEqual(table["csv_sha256"], sha256(table["csv_raw"]))
        self.assertEqual(sum(t["n_y_values"] for t in tables), 352)

    def test_cfb_rejects_cycles_reserved_overlaps_and_out_of_range_chains(self):
        native, _ = native_archive(5)
        original = cfb(native)
        for offset, value in ((512+2*4, 2), (1024+116, 0), (1024+116, 1),
                              (1024+116, 1000), (48, 0)):
            raw = bytearray(original)
            struct.pack_into("<I", raw, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(InputError):
                source._regular_contents(bytes(raw))

    def test_cfb_rejects_unsupported_layout_size_prefix_and_duplicate_names(self):
        native, _ = native_archive(5)
        original = cfb(native)
        mutations = [(68, 2), (72, 1), (44, 0), (1024+120, 100), (1536, 123)]
        for offset, value in mutations:
            raw = bytearray(original)
            struct.pack_into("<I", raw, offset, value)
            with self.subTest(offset=offset), self.assertRaises(InputError):
                source._regular_contents(bytes(raw))
        raw = bytearray(original)
        raw[1024+128:1024+256] = raw[1024:1024+128]
        with self.assertRaises(InputError):
            source._regular_contents(bytes(raw))

    def test_native_csv_shape_nonfinite_and_duplicate_archive_members_fail(self):
        for kwargs in ({"bad_token":True}, {"bad_shape":True}):
            native, _ = native_archive(5, **kwargs)
            with self.assertRaises(InputError):
                source._tables(native, 5)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("duplicate", "a")
            with self.assertWarns(UserWarning):
                archive.writestr("duplicate", "b")
        with self.assertRaises(InputError):
            source._tables(buffer.getvalue(), 5)

    def test_axis_unit_requires_referenced_metadata_and_tissue_labels_require_text(self):
        for title in ("Time", "Time (h)", "Time (min) guessed"):
            native, _ = native_archive(5, axis_title=title)
            with self.subTest(title=title), self.assertRaises(InputError):
                source._tables(native, 5)
        native, _ = native_archive(6, label_format="y_single")
        with self.assertRaises(InputError):
            source._tables(native, 6)

    def test_cell_mapping_retains_lexemes_and_never_promotes_slots_to_independent_units(self):
        tables = []
        for index in (5,6):
            native, _ = native_archive(index)
            tables.extend(source._tables(native, index))
        cells, dataset, qualification = candidate_intake(tables, "invented.docx", "a"*64)
        self.assertEqual(len(cells), 448)
        self.assertEqual(len({r["record_id"] for r in cells}), 448)
        records = {r["record_id"]:r for r in dataset["observations"]}
        for cell in cells:
            self.assertEqual(cell["numeric_text"], "1.2500")
            record = records[cell["record_id"]]
            self.assertEqual(record["observation"]["value"], 1.25)
            self.assertEqual(record["source"]["sha256"], "a"*64)
            self.assertIsNone(record["independent_unit"]["id"])
            self.assertEqual(record["observation"]["replicate_role"], "not_reported")
            self.assertIsNone(record["developmental_interval"]["start"])
            self.assertEqual(record["observation"]["measurement_time_unit"], "min" if cell["object_index"] == 5 else "minutes")
            self.assertEqual(record["observation"]["measurement_time"], float(cell["measurement_time_numeric_text"]))
            self.assertIn(cell["source_locator"], record["limitations"][0])
        self.assertEqual(dataset["transitions"], [])
        self.assertIsNone(qualification["cohort"]["starting_attempts"])
        self.assertIsNone(qualification["cohort"]["failed_or_excluded_attempts"])
        self.assertEqual(qualification["cohort"]["success_fraction"], "not_estimable_from_inspected_tables")
        self.assertFalse(qualification["model_fit_performed"])

    def test_pinned_publication_keeps_original_csv_and_review_distinct_from_integrity(self):
        raw, csvs = supplement()
        path, bundle = self.root/"invented.docx", self.root/"bundle"
        path.write_bytes(raw)
        with patch.object(source, "SUPPLEMENT_SHA256", sha256(raw)):
            receipt = source.audit_roelofsen_source(path, bundle)
            with self.assertRaises(InputError):
                source.audit_roelofsen_source(path, bundle)
        self.assertEqual(receipt["input_sha256"], sha256(raw))
        self.assertCountEqual([(bundle/f"source-table-{n}.csv").read_bytes() for n in range(1,6)], csvs)
        report = json.loads((bundle/"native_table_report.json").read_text())
        self.assertEqual(report["n_published_y_values"], 448)
        self.assertEqual(report["human_review"], "pending")
        self.assertEqual(report["tables"][-1]["source_row_labels"], [f"Placenta {n}" for n in range(1,5)])
        self.assertIn("not authenticated", report["replicate_identity"])
        manifest = json.loads((bundle/"input_source_manifest.json").read_text())
        self.assertFalse(manifest["saved_analyses_executed"])
        dataset, _ = read_json(bundle/"input_dataset.json")
        self.assertEqual(len(dataset["observations"]), 448)
        self.assertEqual(dataset["artifacts"][0]["sha256"], sha256(raw))
        moved = self.root/"relocated"
        shutil.copytree(bundle, moved)
        verification = verify_bundle(moved, strict=True)
        self.assertTrue(verification["bytes_verified"])
        self.assertEqual(verification["scientific_review"], "not_established_by_this_tool")
        plan = json.loads((moved/"reproduction_plan.json").read_text())
        self.assertIn("audit-roelofsen-source", plan["command"])
        self.assertIn("external pinned source supplement (not bundled)", plan["inputs"])
        self.assertFalse(any("Every value" in limit for limit in plan["limits"]))

    def test_generated_candidate_intake_verifies_source_bytes_without_establishing_review(self):
        raw, _ = supplement()
        path, bundle, intake = self.root/"invented.docx", self.root/"bundle", self.root/"intake"
        path.write_bytes(raw)
        with patch.object(source, "SUPPLEMENT_SHA256", sha256(raw)):
            source.audit_roelofsen_source(path, bundle)
        observation_report(bundle/"input_dataset.json", intake, source_root=self.root)
        self.assertTrue(verify_bundle(intake, strict=True)["bytes_verified"])
        report = json.loads((intake/"observation_intake_report.json").read_text())
        self.assertEqual(report["source_review_status"], "candidate")
        self.assertIn("requires source-specific human review", report["analysis_eligibility"])

    def test_wrong_source_hash_and_bad_numeric_source_publish_nothing(self):
        path = self.root/"invented.docx"
        raw, _ = supplement(bad_token=True)
        path.write_bytes(raw)
        with self.assertRaises(InputError):
            source.audit_roelofsen_source(path, self.root/"wrong-hash")
        with patch.object(source, "SUPPLEMENT_SHA256", sha256(raw)), self.assertRaises(InputError):
            source.audit_roelofsen_source(path, self.root/"bad-numeric")
        self.assertFalse((self.root/"wrong-hash").exists())
        self.assertFalse((self.root/"bad-numeric").exists())

    def test_archive_budgets_and_oversized_source_are_rejected(self):
        native, _ = native_archive(5)
        for bounds in ((1, 2_000_000, 500_000), (200, 1, 500_000), (200, 2_000_000, 1)):
            with self.assertRaises(InputError):
                source._bounded_zip(native, *bounds)
        path = self.root/"oversized.docx"
        path.write_bytes(b"x"*1_000_001)
        with self.assertRaises(InputError):
            source.audit_roelofsen_source(path, self.root/"bundle")
        self.assertFalse((self.root/"bundle").exists())
