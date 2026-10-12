"""Bounded source-cell reconciliation for Faure Bardon et al. 2020 S1 Data.

This module verifies the existing source-cell CSV against its pinned XLSX
without calculating transport, amount, flux, or biological model parameters.
"""
from __future__ import annotations

import csv
import io
import json
import posixpath
import re
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET

from .artifacts import InputError, sha256

MAX_WORKBOOK_BYTES = 5_000_000
MAX_CSV_BYTES = 5_000_000
MAX_MANIFEST_BYTES = 1_000_000
MAX_ARCHIVE_ENTRIES = 128
MAX_UNCOMPRESSED_BYTES = 10_000_000
MAX_MEMBER_BYTES = 2_000_000
RATIO_ABSOLUTE_TOLERANCE = Decimal("0.00001")
NS = {
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}
REQUIRED_COLUMNS = {
    "record_id", "study_drug", "source_placenta_label", "analyte_group",
    "measurement_field", "reported_cell_value_lexeme", "value_status",
    "source_formula_text", "source_formula_type", "source_formula_shared_index",
    "source_formula_shared_ref", "source_formula_master_cell",
    "formula_cached_value_lexeme", "source_worksheet", "source_cell", "source_row",
    "time_value_lexeme", "source_table_section",
}


def _read_file(path: Path, *, label: str, limit: int) -> bytes:
    path = Path(path)
    if any(parent.is_symlink() for parent in (path, *path.parents)) or not path.is_file():
        raise InputError(f"{label} must be a regular nonsymlink file")
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError as exc:
        raise InputError(f"Could not read {label}") from exc
    if len(raw) > limit:
        raise InputError(f"{label} exceeds its {limit} byte audit limit")
    return raw


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    raw = archive.read(name)
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise InputError("Workbook XML declarations are unsupported")
    return ET.fromstring(raw)


def _workbook_cells(raw: bytes, *, expected_sheet: str) -> dict[str, dict[str, str | None]]:
    """Return cell reference -> (formula text, raw/cached value lexeme)."""
    if len(raw) > MAX_WORKBOOK_BYTES:
        raise InputError("Source workbook exceeds its audit limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = [item.filename for item in entries]
            if (len(entries) > MAX_ARCHIVE_ENTRIES or len(names) != len(set(names))
                    or sum(item.file_size for item in entries) > MAX_UNCOMPRESSED_BYTES
                    or any(item.file_size > MAX_MEMBER_BYTES or item.flag_bits & 1 for item in entries)):
                raise InputError("Workbook archive exceeds bounds or has duplicate/encrypted members")
            if not {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}.issubset(names):
                raise InputError("Workbook is missing a required internal member")

            workbook = _xml(archive, "xl/workbook.xml")
            sheets = [item for item in workbook.findall("s:sheets/s:sheet", NS)
                      if item.get("name") == expected_sheet]
            if len(sheets) != 1:
                raise InputError(f"Expected exactly one {expected_sheet!r} worksheet")
            relation_id = sheets[0].get("{" + NS["r"] + "}id")
            relationships = [item for item in _xml(archive, "xl/_rels/workbook.xml.rels").findall(
                "p:Relationship", NS) if item.get("Id") == relation_id]
            if (len(relationships) != 1 or relationships[0].get("TargetMode") == "External"
                    or relationships[0].get("Type") != NS["r"] + "/worksheet"):
                raise InputError("Invalid worksheet relationship")
            target = relationships[0].get("Target", "")
            if target.startswith("/"):
                sheet_path = target.lstrip("/")
            else:
                sheet_path = posixpath.normpath(posixpath.join("xl", target))
            if (not sheet_path.startswith("xl/worksheets/") or "\\" in sheet_path
                    or ":" in sheet_path or any(part in {"", ".", ".."}
                                                for part in sheet_path.split("/"))
                    or sheet_path not in names):
                raise InputError("Invalid worksheet path")

            shared: list[str] = []
            if "xl/sharedStrings.xml" in names:
                shared_root = _xml(archive, "xl/sharedStrings.xml")
                shared = ["".join(node.itertext()) for node in shared_root.findall("s:si", NS)]
            sheet = _xml(archive, sheet_path)
            cells: dict[str, dict[str, str | None]] = {}
            for cell in sheet.findall("s:sheetData/s:row/s:c", NS):
                reference = cell.get("r")
                if not reference or not re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]*", reference):
                    raise InputError("Workbook contains an invalid cell reference")
                if reference in cells:
                    raise InputError("Workbook contains a duplicate cell reference")
                formula_node = cell.find("s:f", NS)
                value_node = cell.find("s:v", NS)
                formula = formula_node.text or "" if formula_node is not None else None
                value = value_node.text if value_node is not None else None
                cell_type = cell.get("t")
                if cell_type == "s":
                    if value is None or not value.isdigit() or int(value) >= len(shared):
                        raise InputError("Workbook contains an invalid shared-string reference")
                    value = shared[int(value)]
                elif cell_type == "inlineStr":
                    inline = cell.find("s:is", NS)
                    value = "".join(inline.itertext()) if inline is not None else ""
                elif cell_type not in {None, "n", "str", "b", "e"}:
                    raise InputError("Workbook contains an unsupported cell type")
                formula_type = None
                shared_index = shared_ref = master_cell = None
                if formula_node is not None:
                    formula_type = "shared" if formula_node.get("t") == "shared" else "ordinary"
                    if formula_type == "shared":
                        shared_index = formula_node.get("si")
                        shared_ref = formula_node.get("ref")
                        master_cell = reference if formula else None
                cells[reference] = {
                    "formula_text": formula,
                    "formula_type": formula_type,
                    "shared_index": shared_index,
                    "shared_ref": shared_ref,
                    "master_cell": master_cell,
                    "value": value,
                }

            shared_masters: dict[str, tuple[str, str]] = {}
            for reference, cell in cells.items():
                if cell["formula_type"] != "shared":
                    continue
                index = cell["shared_index"]
                if not index:
                    raise InputError("Shared formula is missing its group index")
                if cell["formula_text"]:
                    if not cell["shared_ref"] or index in shared_masters:
                        raise InputError("Shared formula has a missing or duplicate master")
                    shared_masters[index] = (cell["shared_ref"], reference)
            for cell in cells.values():
                if cell["formula_type"] == "shared":
                    master = shared_masters.get(cell["shared_index"])
                    if master is None:
                        raise InputError("Shared formula follower has no master")
                    cell["shared_ref"], cell["master_cell"] = master
            return cells
    except InputError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, EOFError, ValueError) as exc:
        raise InputError("Workbook is not the supported bounded XLSX structure") from exc


def _read_manifest(raw: bytes) -> dict:
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("Dataset manifest must be valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict):
        raise InputError("Dataset manifest must be an object")
    for section in ("source_artifact", "observation_file"):
        if not isinstance(manifest.get(section), dict):
            raise InputError(f"Dataset manifest is missing {section}")
    return manifest


def _load_relative(root: Path, relative: str, *, label: str, limit: int) -> tuple[Path, bytes]:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise InputError(f"{label} path must be a repository-relative POSIX path")
    base = root.resolve()
    path = root / relative
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise InputError(f"{label} must not traverse a symbolic link")
    try:
        path.resolve().relative_to(base)
    except ValueError as exc:
        raise InputError(f"{label} must remain inside the repository root") from exc
    return path, _read_file(path, label=label, limit=limit)


def audit_faure_bardon_source_cells(repository_root: Path, manifest_path: Path) -> dict:
    """Reconcile the manifest's source-cell CSV to its pinned XLSX and FTR pairs."""
    root = Path(repository_root)
    manifest_raw = _read_file(Path(manifest_path), label="Dataset manifest", limit=MAX_MANIFEST_BYTES)
    manifest = _read_manifest(manifest_raw)
    source = manifest["source_artifact"]
    observation = manifest["observation_file"]

    workbook_path, workbook_raw = _load_relative(
        root, source.get("local_path"), label="Source workbook", limit=MAX_WORKBOOK_BYTES)
    csv_path, csv_raw = _load_relative(
        root, observation.get("path"), label="Observation CSV", limit=MAX_CSV_BYTES)
    workbook_hash = sha256(workbook_raw)
    csv_hash = sha256(csv_raw)
    if workbook_hash != source.get("sha256"):
        raise InputError("Source workbook hash differs from the pinned manifest")
    if csv_hash != observation.get("sha256"):
        raise InputError("Observation CSV hash differs from the pinned manifest")

    sheet_name = source.get("worksheet")
    if not isinstance(sheet_name, str) or not sheet_name:
        raise InputError("Manifest is missing the source worksheet name")
    cells = _workbook_cells(workbook_raw, expected_sheet=sheet_name)
    try:
        decoded = csv_raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded, newline=""))
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)) or not REQUIRED_COLUMNS.issubset(columns):
            raise InputError("Observation CSV has duplicate or missing required columns")
        records = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Observation CSV is not valid bounded UTF-8 CSV") from exc

    if len(records) != observation.get("rows"):
        raise InputError("Observation row count differs from the pinned manifest")
    record_ids: set[str] = set()
    source_cells: set[str] = set()
    formula_count = 0
    blank_count = 0
    reported_count = 0
    indexed: dict[tuple[str, str, str, str, str, str], dict[str, str]] = {}
    for row in records:
        if None in row or any(value is None for value in row.values()):
            raise InputError("Observation CSV contains a malformed row")
        record_id = row["record_id"]
        reference = row["source_cell"]
        if not record_id or record_id in record_ids:
            raise InputError("Observation CSV contains a blank or duplicate record_id")
        if not reference or reference in source_cells:
            raise InputError("Observation CSV contains a blank or duplicate source_cell")
        if row["source_worksheet"] != sheet_name:
            raise InputError("Observation row names a different source worksheet")
        record_ids.add(record_id)
        source_cells.add(reference)
        cell = cells.get(reference, {
            "formula_text": None, "formula_type": None, "shared_index": None,
            "shared_ref": None, "master_cell": None, "value": None,
        })
        formula = cell["formula_text"]
        value = cell["value"]
        expected_formula = row["source_formula_text"]
        expected_value = row["reported_cell_value_lexeme"]
        expected_cache = row["formula_cached_value_lexeme"]
        if formula is not None:
            formula_count += 1
            if (cell["formula_type"] != row["source_formula_type"]
                    or formula != expected_formula or value != expected_cache or value != expected_value
                    or cell["shared_index"] != (row["source_formula_shared_index"] or None)
                    or cell["shared_ref"] != (row["source_formula_shared_ref"] or None)
                    or cell["master_cell"] != (row["source_formula_master_cell"] or None)):
                raise InputError(f"Source formula or cache differs at {reference}")
        else:
            if (expected_formula or expected_cache or row["source_formula_type"]
                    or row["source_formula_shared_index"] or row["source_formula_shared_ref"]
                    or row["source_formula_master_cell"]):
                raise InputError(f"CSV assigns formula provenance to a nonformula cell at {reference}")
            if value != (expected_value or None):
                raise InputError(f"Source value differs at {reference}")
        if row["value_status"] == "source_blank":
            blank_count += 1
            if expected_value or value is not None:
                raise InputError(f"Source blank is not blank at {reference}")
        else:
            reported_count += 1

        key = (row["study_drug"], row["source_placenta_label"], row["analyte_group"],
               row["time_value_lexeme"], row["source_table_section"], row["measurement_field"])
        if key in indexed:
            raise InputError("Observation CSV has duplicate analyte/series/time/field records")
        indexed[key] = row

    if len(record_ids) != observation.get("unique_record_ids"):
        raise InputError("Unique record count differs from the pinned manifest")
    if formula_count != observation.get("unit_level_formula_cells_with_cached_results"):
        raise InputError("Formula-cell count differs from the pinned manifest")
    formula_provenance = manifest.get("formula_and_cache_provenance")
    if (not isinstance(formula_provenance, dict)
            or formula_provenance.get("unit_level_formula_cells_with_cached_results") != formula_count):
        raise InputError("Formula/cache provenance count differs from the pinned manifest")
    formula_counts = manifest.get("formula_provenance_counts")
    if not isinstance(formula_counts, dict):
        raise InputError("Manifest is missing formula provenance counts")
    actual_formula_counts = {
        "mapped_formula_cells_with_cached_values": sum(bool(row["source_formula_type"]) for row in records),
        "ordinary_formula_cells": sum(row["source_formula_type"] == "ordinary" for row in records),
        "shared_formula_cells": sum(row["source_formula_type"] == "shared" for row in records),
        "shared_formula_followers_without_local_expression_text": sum(
            row["source_formula_type"] == "shared" and not row["source_formula_text"] for row in records),
    }
    if actual_formula_counts != formula_counts:
        raise InputError("Formula type counts differ from the pinned manifest")
    if blank_count != observation.get("source_blank_rows"):
        raise InputError("Source-blank count differs from the pinned manifest")
    if reported_count != observation.get("reported_value_rows"):
        raise InputError("Reported-value count differs from the pinned manifest")

    ratio_pairs = 0
    for key, ratio in indexed.items():
        if key[-1] != "fetal_to_maternal_ratio":
            continue
        prefix = key[:-1]
        fetal = indexed.get((*prefix, "fetal_concentration"))
        maternal = indexed.get((*prefix, "maternal_concentration"))
        if fetal is None or maternal is None:
            raise InputError("FTR row lacks a paired FC or MC source row")
        fetal_value = fetal["reported_cell_value_lexeme"]
        maternal_value = maternal["reported_cell_value_lexeme"]
        ratio_value = ratio["reported_cell_value_lexeme"]
        if not fetal_value or not maternal_value:
            continue
        try:
            fetal_decimal = Decimal(fetal_value)
            maternal_decimal = Decimal(maternal_value)
            ratio_decimal = Decimal(ratio_value)
            if not all(value.is_finite() for value in (fetal_decimal, maternal_decimal, ratio_decimal)):
                raise InvalidOperation
            if maternal_decimal == 0:
                raise InvalidOperation
            recomputed = fetal_decimal / maternal_decimal
        except (InvalidOperation, ZeroDivisionError) as exc:
            raise InputError("Invalid numeric FC/MC/FTR source values") from exc
        if abs(recomputed - ratio_decimal) > RATIO_ABSOLUTE_TOLERANCE:
            raise InputError(f"Source FTR differs from FC/MC at {ratio['source_cell']}")
        ratio_pairs += 1

    return {
        "status": "pass",
        "scope": "raw source-cell and source-ratio reconciliation only",
        "workbook_sha256": workbook_hash,
        "csv_sha256": csv_hash,
        "worksheet": sheet_name,
        "source_cell_rows": len(records),
        "unique_record_ids": len(record_ids),
        "matched_values_formulas_and_caches": len(records),
        "source_cell_mismatches": 0,
        "formula_cells_checked": formula_count,
        "ordinary_formula_cells": actual_formula_counts["ordinary_formula_cells"],
        "shared_formula_cells": actual_formula_counts["shared_formula_cells"],
        "shared_formula_followers_without_local_expression_text": actual_formula_counts[
            "shared_formula_followers_without_local_expression_text"],
        "blank_source_rows": blank_count,
        "paired_ftr_rows_recomputed": ratio_pairs,
        "ftr_absolute_tolerance": str(RATIO_ABSOLUTE_TOLERANCE),
        "dimensional_transport_fit_assessed": False,
    }
