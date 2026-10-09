"""Invented parser metadata, never biological study observations."""
from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import InputError, sha256
from wombmodels.bundle_verification import verify_bundle
from wombmodels.crest_linkage import (CODE_MEMBER, METADATA_MEMBER, SDRF_FIELDS,
                                      _archive_summary, _pools, audit_crest_linkage)
from wombmodels.observations import observation_report


def invented_sdrf():
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    # Repeated unselected protocol columns are legal SDRF structure.
    writer.writerow([*SDRF_FIELDS, "Protocol REF", "Protocol REF"])
    for sample, members in (("Sample 1", "Em1+Em2"), ("Sample 3", "Em2+Em3")):
        for repeat in range(2):
            writer.writerow([sample, "Homo sapiens", "Embryo day 14", "invented metadata model",
                members, "invented cell label", "invented stage label", "invented stromal label",
                "invented group", f"invented-assay-{repeat}", "", ""])
    return stream.getvalue().encode()


def invented_archive(*, metadata="Batch,Inferred ID\nC1,ClassA\nC1,ClassB\nC3,ClassA\n",
                       code='D1$ID3 <- "C1"\nD3$ID3 <- "C3"\nD3B$ID3 <- "C4"\nstop("never execute this text")\n'):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(METADATA_MEMBER, metadata)
        archive.writestr(CODE_MEMBER, code)
        archive.writestr("Files/Genotypes/not-to-be-read.tsv", "invented forbidden-to-read test member")
    return stream.getvalue()


class CrestLinkageAuditTests(unittest.TestCase):
    def test_source_rows_are_grouped_as_preparations_and_declared_members(self):
        pools = _pools(invented_sdrf())
        self.assertEqual(len(pools), 2)
        self.assertEqual(pools[0]["members"], ["Em1", "Em2"])
        self.assertEqual(pools[0]["n_sdrf_rows"], 2)
        self.assertEqual(pools[0]["n_assay_labels"], 2)
        self.assertEqual(pools[0]["source_lines"], [2, 3])

    def test_archive_reads_only_selected_metadata_and_literal_code_labels(self):
        called = []
        original = zipfile.ZipFile.read
        def tracked(archive, name, *args, **kwargs):
            called.append(name)
            return original(archive, name, *args, **kwargs)
        with patch.object(zipfile.ZipFile, "read", tracked):
            labels, report = _archive_summary(invented_archive())
        self.assertEqual(called, [METADATA_MEMBER, CODE_MEMBER])
        self.assertEqual(report["n_cell_rows"], 3)
        self.assertEqual(report["n_class_labels"], 2)
        self.assertFalse(report["author_code_executed"])
        self.assertFalse(report["genomic_variant_contents_read"])
        self.assertEqual(labels[-1]["status"], "no_rows_in_supplied_annotation_csv")

    def test_conflicting_or_malformed_sdrf_and_annotation_are_rejected(self):
        raw = invented_sdrf()
        wrong = [raw.replace(b"Homo sapiens", b"other species", 1),
                 raw.replace(b"Em1+Em2", b"Em1+Em1", 1),
                 raw.replace(b"Embryo day 14", b"Embryo day 15"),
                 raw.replace(b"Em1+Em2", b"Em1+Em4", 1), b"not an SDRF", b"\xff"]
        for value in wrong:
            with self.subTest(length=len(value)):
                with self.assertRaises(InputError):
                    _pools(value)
        bad_archives = [invented_archive(metadata="Batch,Inferred ID\nUnknown,ClassA\n"),
                        invented_archive(metadata="Batch,Batch,Inferred ID\nC1,C1,ClassA\n"),
                        invented_archive(code='D1$ID3 <- "C1"\nD3$ID3 <- "C1"\n'),
                        invented_archive(code='D1$ID3 <- "C1"\nD1$ID3 <- "C3"\n'), b"not a ZIP"]
        for value in bad_archives:
            with self.subTest(length=len(value)):
                with self.assertRaises(InputError):
                    _archive_summary(value)

    def test_pinned_publication_and_intake_preserve_unknown_phenotype_linkage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sdrf, archive = invented_sdrf(), invented_archive()
            sp, ap = root / "source.sdrf.txt", root / "code.zip"
            sp.write_bytes(sdrf)
            ap.write_bytes(archive)
            output = root / "audit"
            with patch("wombmodels.crest_linkage.SDRF_SHA256", sha256(sdrf)), patch(
                    "wombmodels.crest_linkage.ARCHIVE_SHA256", sha256(archive)):
                receipt = audit_crest_linkage(sp, ap, output)
                with self.assertRaises(InputError):
                    audit_crest_linkage(sp, ap, output)
            self.assertEqual(sp.read_bytes(), sdrf)
            self.assertEqual(ap.read_bytes(), archive)
            self.assertEqual(receipt["input_sha256"], sha256((output / "input_source_manifest.json").read_bytes()))
            self.assertTrue(verify_bundle(output, strict=True)["bytes_verified"])
            report = json.loads((output / "linkage_report.json").read_text())
            self.assertEqual(report["n_source_named_preparations"], 2)
            self.assertEqual(report["n_shared_declared_member_labels"], 1)
            self.assertEqual(report["phenotype_linkage"], "not_established_in_inspected_inputs")
            self.assertEqual(report["review_status"], "candidate")
            data = json.loads((output / "input_dataset.json").read_text())
            self.assertEqual(data["transitions"], [])
            self.assertTrue(all(r["observation"]["replicate_role"] == "summary_only" for r in data["observations"]))
            intake = root / "intake"
            observation_report(output / "input_dataset.json", intake, source_root=root)
            summary = json.loads((intake / "observation_intake_report.json").read_text())
            self.assertEqual(summary["source_file_verification"]["n_verified"], 1)
            self.assertEqual(summary["declared_unit_membership"]["n_shared_identifier_keys"], 1)
            self.assertTrue(verify_bundle(intake, strict=True)["bytes_verified"])

    def test_wrong_source_hash_and_bound_fail_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.sdrf.txt"
            archive = root / "code.zip"
            archive.write_bytes(invented_archive())
            for raw in (b"wrong revision", b"x" * 128_001):
                source.write_bytes(raw)
                with self.assertRaises(InputError):
                    audit_crest_linkage(source, archive, root / "out")
                self.assertFalse((root / "out").exists())
