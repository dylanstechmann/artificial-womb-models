"""Bounded source-cell reconciliation for the Ashley et al. 2022 intake.

This audit checks the selected 30 endpoint values and the complete nonempty
cell ledger against the pinned Figure 1 workbook. It does not recalculate rates,
infer vitamin sufficiency, or treat related endpoints as independent evidence.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from pathlib import Path, PurePosixPath

from .artifacts import InputError, sha256
from .faure_bardon_source import _workbook_cells

MAX_SOURCE_BYTES = 5_000_000
MAX_JSON_BYTES = 5_000_000
MAX_CSV_BYTES = 5_000_000
EXPECTED_SAMPLE_LABELS = ("252", "254", "275", "343", "402")
EXPECTED_SELECTED_ROWS = 30
EXPECTED_LEDGER_ROWS = 207

GROUPS = {
    "ashley2022-25d-maternal-loss-p": {
        "cells": {label: f"{chr(ord('B') + index)}6" for index, label in enumerate(EXPECTED_SAMPLE_LABELS)},
        "unit": "pmol/min/g",
        "qualifier": "maternal_row6",
    },
    "ashley2022-25d-metabolized-p": {
        "cells": {label: f"{chr(ord('B') + index)}7" for index, label in enumerate(EXPECTED_SAMPLE_LABELS)},
        "unit": "pmol/min/g",
        "qualifier": None,
    },
    "ashley2022-25d-fetal-transfer-p": {
        "cells": {label: f"{chr(ord('M') + index)}6" for index, label in enumerate(EXPECTED_SAMPLE_LABELS)},
        "unit": "pmol/min/g",
        "qualifier": "fetal_row6",
    },
    "ashley2022-25d-placental-storage-p": {
        "cells": {label: f"{chr(ord('M') + index)}7" for index, label in enumerate(EXPECTED_SAMPLE_LABELS)},
        "unit": "pmol/min/g",
        "qualifier": None,
    },
    "ashley2022-125d-maternal-p": {
        "cells": {label: f"F{22 + index}" for index, label in enumerate(EXPECTED_SAMPLE_LABELS)},
        "unit": "fmol/min/g",
        "qualifier": None,
    },
    "ashley2022-125d-fetal-p": {
        "cells": {label: f"F{30 + index}" for index, label in enumerate(EXPECTED_SAMPLE_LABELS)},
        "unit": "fmol/min/g",
        "qualifier": None,
    },
}
LEDGER_COLUMNS = {
    "worksheet", "cell", "raw_value_json", "row_header_cell_A",
    "column_header_row3", "disposition",
}


def _load_relative(root: Path, value: object, *, label: str, limit: int) -> tuple[Path, bytes]:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InputError(f"{label} path must be repository-relative POSIX text")
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
    if not path.is_file():
        raise InputError(f"{label} is missing or is not a regular file")
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError as exc:
        raise InputError(f"Could not read {label}") from exc
    if len(raw) > limit:
        raise InputError(f"{label} exceeds its {limit} byte audit limit")
    return path, raw


def _json(raw: bytes, *, label: str) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"{label} must be valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a JSON object")
    return value


def _record_group(record_id: str) -> tuple[str, str]:
    for prefix in GROUPS:
        if record_id.startswith(prefix):
            label = record_id[len(prefix):]
            if label in EXPECTED_SAMPLE_LABELS:
                return prefix, label
    raise InputError(f"Unexpected Ashley candidate record identifier: {record_id}")


def _numeric(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise InputError(f"{label} must be finite")
    return result


def audit_ashley_source_cells(
    repository_root: Path,
    *,
    source_manifest_path: str = "artifacts/ashley-2022-vitamin-d-perfusion/SOURCE.json",
    candidate_path: str = "config/observations/ashley_2022_vitamin_d_perfusion_candidate.json",
    source_cell_ledger_path: str = "config/source_inventories/ashley_2022_figure1_source_cells.csv",
) -> dict:
    """Match the candidate observations and all nonempty ledger cells to the pinned XLSX."""
    root = Path(repository_root)
    _, manifest_raw = _load_relative(root, source_manifest_path, label="Source manifest", limit=MAX_JSON_BYTES)
    _, candidate_raw = _load_relative(root, candidate_path, label="Candidate dataset", limit=MAX_JSON_BYTES)
    _, ledger_raw = _load_relative(root, source_cell_ledger_path, label="Source-cell ledger", limit=MAX_CSV_BYTES)
    manifest = _json(manifest_raw, label="Source manifest")
    candidate = _json(candidate_raw, label="Candidate dataset")

    source_relative = manifest.get("local_path")
    _, workbook_raw = _load_relative(root, source_relative, label="Source workbook", limit=MAX_SOURCE_BYTES)
    workbook_hash = sha256(workbook_raw)
    if workbook_hash != manifest.get("sha256"):
        raise InputError("Source workbook hash differs from SOURCE.json")
    artifact_id = manifest.get("artifact_id")
    artifact_matches = [item for item in candidate.get("artifacts", [])
                        if isinstance(item, dict) and item.get("artifact_id") == artifact_id]
    if len(artifact_matches) != 1 or artifact_matches[0].get("sha256") != workbook_hash:
        raise InputError("Candidate dataset does not pin the source workbook hash")

    workbook_info = manifest.get("workbook")
    sheet_name = workbook_info.get("sheet") if isinstance(workbook_info, dict) else None
    if (sheet_name != "Sheet1" or workbook_info.get("dimensions") != "A1:T34"
            or workbook_info.get("formula_cells") != []):
        raise InputError("Unexpected source worksheet declaration")
    cells = _workbook_cells(workbook_raw, expected_sheet=sheet_name)
    formulas = [reference for reference, cell in cells.items() if cell["formula_text"] is not None]
    if formulas:
        raise InputError("Pinned source workbook unexpectedly contains formulas")
    nonempty_cells = {reference: cell for reference, cell in cells.items() if cell["value"] is not None}

    try:
        reader = csv.DictReader(io.StringIO(ledger_raw.decode("utf-8-sig"), newline=""))
        if not LEDGER_COLUMNS.issubset(reader.fieldnames or []):
            raise InputError("Source-cell ledger is missing required columns")
        ledger_rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Source-cell ledger is not valid bounded UTF-8 CSV") from exc
    if len(ledger_rows) != EXPECTED_LEDGER_ROWS or len(nonempty_cells) != EXPECTED_LEDGER_ROWS:
        raise InputError("Workbook and source-cell ledger must each contain 207 nonempty cells")
    ledger_by_cell: dict[str, dict[str, str]] = {}
    for row in ledger_rows:
        if row["worksheet"] != sheet_name or not row["cell"] or row["cell"] in ledger_by_cell:
            raise InputError("Source-cell ledger contains a wrong-sheet or duplicate cell")
        ledger_by_cell[row["cell"]] = row
    if set(ledger_by_cell) != set(nonempty_cells):
        raise InputError("Source-cell ledger does not cover the workbook's nonempty cells exactly")
    for reference, row in ledger_by_cell.items():
        try:
            ledger_value = json.loads(row["raw_value_json"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise InputError(f"Invalid raw_value_json for {reference}") from exc
        workbook_value = nonempty_cells[reference]["value"]
        if isinstance(ledger_value, (int, float)) and not isinstance(ledger_value, bool):
            try:
                matches = float(workbook_value) == float(ledger_value)
            except (TypeError, ValueError, OverflowError):
                matches = False
        else:
            matches = workbook_value == ledger_value
        if not matches:
            raise InputError(f"Source-cell ledger value differs from workbook at {reference}")

    observations = candidate.get("observations")
    if not isinstance(observations, list) or len(observations) != EXPECTED_SELECTED_ROWS:
        raise InputError("Candidate dataset must contain exactly 30 selected observations")
    seen_ids: set[str] = set()
    seen_cells: set[str] = set()
    group_counts = {prefix: 0 for prefix in GROUPS}
    labels_by_group = {prefix: set() for prefix in GROUPS}
    for record in observations:
        if not isinstance(record, dict):
            raise InputError("Candidate observation must be an object")
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or record_id in seen_ids:
            raise InputError("Candidate record IDs must be unique text")
        seen_ids.add(record_id)
        prefix, sample_label = _record_group(record_id)
        spec = GROUPS[prefix]
        expected_cell = spec["cells"][sample_label]
        locator = record.get("source_locator", "")
        match = re.fullmatch(rf"{re.escape(sheet_name)}!([A-Z]+[1-9][0-9]*);.*", locator)
        if not match or match.group(1) != expected_cell:
            raise InputError(f"Source locator differs from expected cell {expected_cell}")
        if expected_cell in seen_cells:
            raise InputError(f"Candidate observations reuse source cell {expected_cell}")
        seen_cells.add(expected_cell)
        if expected_cell not in nonempty_cells:
            raise InputError(f"Candidate source cell {expected_cell} is absent from workbook")
        if prefix.startswith("ashley2022-25d-"):
            label_cell = f"{expected_cell.rstrip('0123456789')}3"
            source_label = str(nonempty_cells.get(label_cell, {}).get("value", "")).strip()
            label_matches = source_label == sample_label
        else:
            source_row = int(expected_cell.lstrip("F"))
            label_cell = f"A{source_row}"
            compartment_prefix = "M" if "-maternal-p" in prefix else "F"
            source_label = str(nonempty_cells.get(label_cell, {}).get("value", "")).strip()
            label_matches = source_label == f"{compartment_prefix} {sample_label}"
        if not label_matches:
            raise InputError(f"Placenta label in workbook differs at {label_cell}")
        source_value = nonempty_cells[expected_cell]["value"]
        candidate_value = _numeric(record.get("observation", {}).get("value"), label=f"{record_id} value")
        try:
            source_numeric = float(source_value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise InputError(f"Candidate source cell {expected_cell} is not numeric") from exc
        if candidate_value != source_numeric:
            raise InputError(f"Candidate value differs from workbook at {expected_cell}")
        if ledger_by_cell[expected_cell]["disposition"] != "candidate_observation":
            raise InputError(f"Source-cell ledger does not designate {expected_cell} as selected")

        independent = record.get("independent_unit", {})
        if independent.get("id") != f"placenta-{sample_label}":
            raise InputError(f"Placenta label differs from workbook at {expected_cell}")
        if record.get("assay", {}).get("unit") != spec["unit"]:
            raise InputError(f"Candidate unit differs from the declared unit for {record_id}")
        if record.get("observation", {}).get("measurement_time") != 300:
            raise InputError(f"Candidate time differs from 300 min for {record_id}")
        if record.get("source", {}).get("artifact_id") != artifact_id:
            raise InputError(f"Candidate source artifact differs for {record_id}")
        if record.get("source", {}).get("sha256") != workbook_hash:
            raise InputError(f"Candidate source hash differs for {record_id}")

        # Row 6 workbook headers omit “/min”; the article's Figure 1b supplies
        # the rate unit, and the intake must preserve that source qualification.
        qualifier_kind = spec["qualifier"]
        qualifications = record.get("observation", {}).get("source_qualifications", [])
        if qualifier_kind:
            expected_header = "A6" if qualifier_kind == "maternal_row6" else "L6"
            expected_locator = f"{sheet_name}!{expected_header} and {expected_cell}"
            source_unit_literal = nonempty_cells[expected_header]["value"]
            expected_reference_unit = f"worksheet: {source_unit_literal}; article: pmol/min/g"
            if not any(isinstance(item, dict)
                       and item.get("criterion_code") == "workbook_unit_label"
                       and item.get("status_code") == "article_rate_unit_used"
                       and item.get("source_locator") == expected_locator
                       and item.get("reference_unit") == expected_reference_unit
                       and "Worksheet literal omits /min" in item.get("criterion_label", "")
                       for item in qualifications):
                raise InputError(f"Missing row-6 workbook-unit qualification for {record_id}")
        group_counts[prefix] += 1
        labels_by_group[prefix].add(sample_label)

    for prefix in GROUPS:
        if group_counts[prefix] != len(EXPECTED_SAMPLE_LABELS) or labels_by_group[prefix] != set(EXPECTED_SAMPLE_LABELS):
            raise InputError(f"Candidate group does not cover all five source labels: {prefix}")
    return {
        "status": "pass",
        "source_manifest_sha256": sha256(manifest_raw),
        "source_workbook_sha256": workbook_hash,
        "candidate_dataset_sha256": sha256(candidate_raw),
        "source_cell_ledger_sha256": sha256(ledger_raw),
        "worksheet": sheet_name,
        "worksheet_nonempty_cells": len(nonempty_cells),
        "worksheet_formula_cells": len(formulas),
        "source_cell_ledger_rows_checked": len(ledger_rows),
        "candidate_observations_checked": len(observations),
        "selected_value_matches": len(seen_cells),
        "selected_source_cells_designated_in_ledger": len(seen_cells),
        "unique_placenta_labels": len(EXPECTED_SAMPLE_LABELS),
        "selected_endpoint_groups": len(GROUPS),
        "excluded_24_25_rows_imported": sum("24,25" in item.get("record_id", "") for item in observations),
        "row6_unit_qualifications_preserved": sum(
            1 for prefix, count in group_counts.items() if GROUPS[prefix]["qualifier"] for _ in range(count)
        ),
        "formula_recalculated": False,
        "source_transcription_or_scientific_review_complete": False,
        "dimensional_transport_fit_assessed": False,
    }
