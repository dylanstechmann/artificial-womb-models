"""Bounded source-cell reconciliation for Mandelbrot et al. 2019 S1 Table.

The source XLSX contains cached values and both ordinary and shared formulas,
some of which reference an unbundled external workbook. This audit compares
the published cached cell contents and formula metadata with the candidate
CSV; it never evaluates a formula or estimates transport quantities.
"""
from __future__ import annotations

import csv
import io
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath

from .artifacts import InputError, decode_json, sha256
from .faure_bardon_source import _workbook_cells

MAX_WORKBOOK_BYTES = 5_000_000
MAX_CSV_BYTES = 5_000_000
MAX_MANIFEST_BYTES = 1_000_000

SOURCE_FIELDS = {
    "dtg_fetal_ng_ml": "C",
    "dtg_maternal_ng_ml": "D",
    "dtg_fetal_to_maternal_ratio_pct": "E",
    "antipyrine_fetal_mg_l": "G",
    "antipyrine_maternal_mg_l": "H",
    "antipyrine_fetal_to_maternal_ratio_pct": "I",
    "clearance_index": "K",
}
PREFIX_COLUMNS = [
    "record_id", "source_artifact_id", "source_table", "source_sheet", "source_row",
    "perfusion_label", "label_source_cell", "label_source_lexeme",
    "measurement_time_min_cell", "measurement_time_min_lexeme", "measurement_time_min_numeric",
]
SUFFIX_COLUMNS = ["time_unit", "source_locator"]
FIELD_COLUMNS = [
    column
    for field in SOURCE_FIELDS
    for column in (
        f"{field}_cell", f"{field}_source_value_lexeme", f"{field}_value_numeric",
        f"{field}_source_formula", f"{field}_source_formula_type",
        f"{field}_source_formula_shared_index", f"{field}_source_formula_shared_ref",
        f"{field}_source_formula_master_cell", f"{field}_measurement_status",
    )
]
CSV_COLUMNS = PREFIX_COLUMNS + FIELD_COLUMNS + SUFFIX_COLUMNS


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


def _load_relative(root: Path, value: object, *, label: str, limit: int) -> tuple[Path, bytes]:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InputError(f"{label} path must be a nonempty repository-relative POSIX path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise InputError(f"{label} path must not be absolute or traverse directories")
    base = Path(root).resolve()
    path = base.joinpath(*relative.parts)
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != base.parent):
        raise InputError(f"{label} must not traverse a symbolic link")
    try:
        path.resolve().relative_to(base)
    except ValueError as exc:
        raise InputError(f"{label} must remain inside the repository root") from exc
    return path, _read_file(path, label=label, limit=limit)


def _decimal(value: str, *, label: str) -> Decimal:
    try:
        parsed = Decimal(value)
        if not parsed.is_finite():
            raise InvalidOperation
        return parsed
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{label} must be a finite decimal value") from exc


def _column(reference: str) -> str:
    match = re.fullmatch(r"([A-Z]{1,3})[1-9][0-9]*", reference)
    if match is None:
        raise InputError("Observation CSV contains an invalid XLSX cell reference")
    return match.group(1)


def audit_mandelbrot_source_cells(repository_root: Path, manifest_path: Path) -> dict:
    """Match all candidate timepoint rows and formula/cache provenance to S1."""
    root = Path(repository_root).resolve()
    manifest_raw = _read_file(Path(manifest_path), label="Dataset manifest", limit=MAX_MANIFEST_BYTES)
    manifest = decode_json(manifest_raw)
    if not isinstance(manifest, dict):
        raise InputError("Dataset manifest must be a JSON object")
    source = manifest.get("source_artifact")
    observation = manifest.get("observation_file")
    if not isinstance(source, dict) or not isinstance(observation, dict):
        raise InputError("Dataset manifest is missing source-artifact or observation metadata")

    _, workbook_raw = _load_relative(root, source.get("local_path"), label="Source workbook",
                                     limit=MAX_WORKBOOK_BYTES)
    _, csv_raw = _load_relative(root, observation.get("path"), label="Observation CSV", limit=MAX_CSV_BYTES)
    workbook_hash = sha256(workbook_raw)
    csv_hash = sha256(csv_raw)
    if workbook_hash != source.get("sha256"):
        raise InputError("Source workbook hash differs from the pinned manifest")
    if csv_hash != observation.get("sha256"):
        raise InputError("Observation CSV hash differs from the pinned manifest")
    if source.get("worksheet") != "Feuil1" or source.get("table") != "S1 Table":
        raise InputError("Manifest does not identify the inspected S1 worksheet")

    cells = _workbook_cells(workbook_raw, expected_sheet=source["worksheet"])
    workbook_formula_count = sum(cell["formula_type"] is not None for cell in cells.values())
    try:
        reader = csv.DictReader(io.StringIO(csv_raw.decode("utf-8-sig"), newline=""))
        if reader.fieldnames != CSV_COLUMNS:
            raise InputError("Observation CSV columns differ from the audited formula-provenance schema")
        records = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Observation CSV is not valid bounded UTF-8 CSV") from exc
    if any(None in row or any(value is None for value in row.values()) for row in records):
        raise InputError("Observation CSV contains a malformed row")
    if len(records) != observation.get("rows") or len(records) != 94:
        raise InputError("Observation row count differs from the pinned manifest")

    fields = manifest.get("measured_fields")
    if not isinstance(fields, list) or len(fields) != len(SOURCE_FIELDS):
        raise InputError("Manifest measured-field list is malformed")
    field_meta = {item.get("name"): item for item in fields if isinstance(item, dict)}
    if set(field_meta) != set(SOURCE_FIELDS):
        raise InputError("Manifest measured fields differ from the source CSV")
    observation_frame = manifest.get("observation_frame")
    if not isinstance(observation_frame, dict):
        raise InputError("Manifest is missing the observation frame")
    labels = observation_frame.get("source_labels")
    if not isinstance(labels, list) or len(labels) != 5 or len(set(labels)) != 5:
        raise InputError("Manifest source labels must list the five table labels")
    times = manifest.get("reported_timepoints_min")
    if not isinstance(times, list) or not times or len(set(times)) != len(times):
        raise InputError("Manifest reported-time list is invalid")

    formula_cells_by_field = {field: 0 for field in SOURCE_FIELDS}
    formula_text_by_field = {field: 0 for field in SOURCE_FIELDS}
    shared_cells_by_field = {field: 0 for field in SOURCE_FIELDS}
    shared_followers_by_field = {field: 0 for field in SOURCE_FIELDS}
    statuses = {field: {} for field in SOURCE_FIELDS}
    record_ids: set[str] = set()
    label_times: set[tuple[str, str]] = set()
    rows_by_label: dict[str, int] = {}
    selected_cells: set[str] = set()

    for row in records:
        record_id = row["record_id"]
        if not record_id or record_id in record_ids:
            raise InputError("Observation CSV contains a blank or duplicate record_id")
        record_ids.add(record_id)
        if row["source_artifact_id"] != source.get("artifact_id") or row["source_table"] != "S1 Table":
            raise InputError("Observation row names a different source artifact or table")
        if row["source_sheet"] != source["worksheet"]:
            raise InputError("Observation row names a different source worksheet")
        try:
            source_row = int(row["source_row"])
        except (TypeError, ValueError) as exc:
            raise InputError("Observation row has an invalid source row number") from exc
        if str(source_row) != row["source_row"]:
            raise InputError("Observation source row number is not canonical")

        label_ref = row["label_source_cell"]
        time_ref = row["measurement_time_min_cell"]
        label_cell = cells.get(label_ref)
        time_cell = cells.get(time_ref)
        if (label_cell is None or label_cell["value"] != row["label_source_lexeme"]
                or row["perfusion_label"] != row["label_source_lexeme"]):
            raise InputError(f"Source perfusion label differs at {label_ref}")
        if (time_cell is None or time_cell["value"] != row["measurement_time_min_lexeme"]
                or time_cell["formula_type"] is not None):
            raise InputError(f"Source measurement time differs at {time_ref}")
        if _column(label_ref) != "A" or _column(time_ref) != "B" or int(time_ref[1:]) != source_row:
            raise InputError("Observation label/time cells do not match the declared source row")
        if row["time_unit"] != "min":
            raise InputError("Observation time unit differs from S1 Table")
        if not row["measurement_time_min_numeric"] or _decimal(
                row["measurement_time_min_numeric"], label="Observation time") != _decimal(
                    row["measurement_time_min_lexeme"], label="Source time"):
            raise InputError(f"Numeric time differs from its source lexeme at {time_ref}")
        if int(row["measurement_time_min_numeric"]) not in times:
            raise InputError(f"Observation time is absent from the manifest at {time_ref}")
        key = (row["perfusion_label"], row["measurement_time_min_numeric"])
        if key in label_times:
            raise InputError("Observation CSV contains a duplicate label/time key")
        label_times.add(key)
        rows_by_label[row["perfusion_label"]] = rows_by_label.get(row["perfusion_label"], 0) + 1

        locator_fields = "; ".join(f"{field}={row[f'{field}_cell']}" for field in SOURCE_FIELDS)
        expected_locator = (
            f"S1 Table; {source['worksheet']} row {source_row}; perfusion label {row['perfusion_label']} "
            f"from {label_ref}; time {row['measurement_time_min_lexeme']} min from {time_ref}; "
            f"{locator_fields}"
        )
        if row["source_locator"] != expected_locator:
            raise InputError(f"Observation source locator differs at source row {source_row}")

        for field, source_column in SOURCE_FIELDS.items():
            meta = field_meta[field]
            if meta.get("source_column") != source_column:
                raise InputError(f"Manifest source column differs for {field}")
            reference = row[f"{field}_cell"]
            if not reference or _column(reference) != source_column or int(reference[1:]) != source_row:
                raise InputError(f"Observation cell locator differs for {field} at row {source_row}")
            cell = cells.get(reference)
            if cell is None:
                raise InputError(f"Workbook is missing observed source cell {reference}")
            selected_cells.add(reference)
            source_value = cell["value"]
            lexeme = row[f"{field}_source_value_lexeme"]
            if (source_value or "") != lexeme:
                raise InputError(f"Source value lexeme differs at {reference}")

            formula_text = cell["formula_text"] or ""
            formula_type = cell["formula_type"] or ""
            shared_index = cell["shared_index"] or ""
            shared_ref = cell["shared_ref"] or ""
            master_cell = cell["master_cell"] or ""
            if (row[f"{field}_source_formula"] != formula_text
                    or row[f"{field}_source_formula_type"] != formula_type
                    or row[f"{field}_source_formula_shared_index"] != shared_index
                    or row[f"{field}_source_formula_shared_ref"] != shared_ref
                    or row[f"{field}_source_formula_master_cell"] != master_cell):
                raise InputError(f"Formula/cache provenance differs at {reference}")

            status = row[f"{field}_measurement_status"]
            numeric = row[f"{field}_value_numeric"]
            if source_value is None:
                expected_status = "source_blank"
                if lexeme or numeric:
                    raise InputError(f"Blank source cell was converted at {reference}")
            else:
                try:
                    source_number = Decimal(source_value)
                    if not source_number.is_finite():
                        raise InvalidOperation
                    numeric_source = True
                except (InvalidOperation, ValueError):
                    numeric_source = False
                expected_status = "reported_numeric" if numeric_source else "reported_text"
                if numeric_source:
                    if not numeric or _decimal(numeric, label=f"Numeric value at {reference}") != source_number:
                        raise InputError(f"Numeric value differs from its source cache at {reference}")
                elif numeric:
                    raise InputError(f"Text source cell has a numeric value at {reference}")
            if status != expected_status:
                raise InputError(f"Observation status differs from source cell at {reference}")
            statuses[field][status] = statuses[field].get(status, 0) + 1

            if formula_type:
                formula_cells_by_field[field] += 1
                if formula_text:
                    formula_text_by_field[field] += 1
                if formula_type == "shared":
                    shared_cells_by_field[field] += 1
                    if not formula_text:
                        shared_followers_by_field[field] += 1
                elif formula_type != "ordinary":
                    raise InputError(f"Unsupported formula type at {reference}")
                if formula_type == "shared" and not (shared_index and shared_ref and master_cell):
                    raise InputError(f"Shared-formula group metadata is incomplete at {reference}")
                if formula_type == "ordinary" and (shared_index or shared_ref or master_cell):
                    raise InputError(f"Ordinary formula has shared-group metadata at {reference}")
            elif formula_text or shared_index or shared_ref or master_cell:
                raise InputError(f"Nonformula cell has formula provenance at {reference}")

    if len(record_ids) != observation.get("unique_record_ids") or len(label_times) != len(records):
        raise InputError("Observation record or label/time counts differ from the manifest")
    if rows_by_label != manifest.get("observation_counts", {}).get("rows_by_source_label"):
        raise InputError("Observation rows by source label differ from the manifest")
    gaps = manifest.get("source_gaps")
    if not isinstance(gaps, list):
        raise InputError("Manifest source_gaps must be a list")
    declared_gaps = set()
    for gap in gaps:
        if not isinstance(gap, dict):
            raise InputError("Manifest contains a malformed source-gap record")
        declared_gaps.add((gap.get("perfusion_label"), str(gap.get("expected_time_min"))))
    expected_keys = {(label, str(time)) for label in labels for time in times} - declared_gaps
    if label_times != expected_keys:
        raise InputError("Observation label/time keys differ from the declared source frame and gaps")
    if len(selected_cells) != len(records) * len(SOURCE_FIELDS):
        raise InputError("Selected source-cell count differs from the observation layout")
    counts = manifest.get("formula_provenance_counts")
    if not isinstance(counts, dict):
        raise InputError("Manifest is missing formula-provenance counts")
    expected_count_fields = {
        "worksheet_formula_cells": workbook_formula_count,
        "observation_mapped_formula_cells": sum(formula_cells_by_field.values()),
        "observation_local_formula_expression_text_cells": sum(formula_text_by_field.values()),
        "observation_shared_formula_cells": sum(shared_cells_by_field.values()),
        "observation_shared_formula_followers_without_local_expression_text": sum(shared_followers_by_field.values()),
    }
    if counts != expected_count_fields:
        raise InputError("Formula-provenance summary counts differ from workbook cells")

    for field, meta in field_meta.items():
        expected_meta = {
            "source_formula_cell_count": formula_cells_by_field[field],
            "source_formula_expression_text_count": formula_text_by_field[field],
            "source_shared_formula_cell_count": shared_cells_by_field[field],
            "source_shared_formula_follower_count": shared_followers_by_field[field],
        }
        if any(meta.get(key) != value for key, value in expected_meta.items()):
            raise InputError(f"Manifest formula counts differ for {field}")
        if statuses[field] != manifest.get("observation_counts", {}).get("field_status_counts", {}).get(field):
            raise InputError(f"Observation status counts differ for {field}")

    return {
        "status": "pass",
        "scope": "source-cell values, formula metadata, caches, row keys, and missingness only",
        "source_workbook_sha256": workbook_hash,
        "observation_csv_sha256": csv_hash,
        "worksheet": source["worksheet"],
        "worksheet_cells": len(cells),
        "worksheet_formula_cells": workbook_formula_count,
        "observation_rows": len(records),
        "unique_record_ids": len(record_ids),
        "unique_label_time_keys": len(label_times),
        "selected_field_cells_checked": len(selected_cells),
        "cached_value_lexeme_mismatches": 0,
        "mapped_formula_cells": sum(formula_cells_by_field.values()),
        "local_formula_expression_text_cells": sum(formula_text_by_field.values()),
        "shared_formula_cells": sum(shared_cells_by_field.values()),
        "shared_formula_followers_without_local_expression_text": sum(shared_followers_by_field.values()),
        "formula_provenance_mismatches": 0,
        "formula_recalculated": False,
        "external_workbook_retrieved": False,
        "dimensional_transport_fit_assessed": False,
        "human_source_review_complete": False,
    }
