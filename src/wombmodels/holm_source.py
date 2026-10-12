"""Reconcile a candidate Holm et al. 2017 aggregate Table 2 intake."""
from __future__ import annotations

import csv
import io
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath

from .artifacts import InputError, sha256

MAX_INPUT_BYTES = 5_000_000
EXPECTED_ROWS = 76
VESSEL_SLUGS = {
    "Radial artery": "radial-artery",
    "Uterine vein": "uterine-vein",
    "Umbilical vein": "umbilical-vein",
    "Umbilical artery": "umbilical-artery",
}
REQUIRED_SOURCE_COLUMNS = {
    "source_doi", "source_table", "source_table_row_index", "source_table_cell_locator",
    "amino_acid_class", "amino_acid", "vessel", "vessel_N_as_reported",
    "vessel_N_scope", "concentration_unit", "median_as_published", "q1_as_published",
    "q3_as_published", "summary_cell_literal", "review_flag",
}
REQUIRED_TABLE3_COLUMNS = {
    "source_doi", "source_table", "source_table_row_index", "summary_cell_locator",
    "p_value_cell_locator", "amino_acid_class", "amino_acid", "circulation_side",
    "summary_type", "sample_N_as_reported", "sample_N_scope", "difference_unit",
    "positive_difference_interpretation", "median_difference_as_published", "q1_as_published",
    "q3_as_published", "summary_cell_literal", "p_value_as_published",
    "summary_cell_marked_bold", "bolding_note",
}
TABLE3_CIRCULATION_SLUGS = {"Uteroplacental": "uteroplacental", "Umbilical": "umbilical"}
TABLE3_SUMMARY_SLUGS = {
    "Crude": "crude",
    "Adjusted for transfer of water across the placenta": "water-adjusted",
}


def _read_relative(root: Path, relative: object, *, label: str) -> tuple[Path, bytes]:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise InputError(f"{label} path must be repository-relative POSIX text")
    posix = PurePosixPath(relative)
    if posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
        raise InputError(f"{label} path must not be absolute or traverse directories")
    base = Path(root).resolve()
    path = base.joinpath(*posix.parts)
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != base.parent):
        raise InputError(f"{label} must not traverse a symbolic link")
    try:
        path.resolve().relative_to(base)
    except ValueError as exc:
        raise InputError(f"{label} must remain inside the repository root") from exc
    if not path.is_file():
        raise InputError(f"{label} is missing or is not a regular file")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise InputError(f"{label} exceeds its {MAX_INPUT_BYTES} byte audit limit")
    raw = path.read_bytes()
    return path, raw


def _json_object(raw: bytes, *, label: str) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"{label} must be valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a JSON object")
    return value


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise InputError("An amino-acid label cannot form a record identifier")
    return slug


def _decimal(value: object, *, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{label} must be a finite decimal") from exc


def expected_record_id(row: dict[str, str]) -> str:
    vessel = row.get("vessel")
    if vessel not in VESSEL_SLUGS:
        raise InputError(f"Unknown vessel label: {vessel}")
    return f"holm2017-table2-{_slug(row.get('amino_acid', ''))}-{VESSEL_SLUGS[vessel]}"


def expected_table3_record_id(row: dict[str, str]) -> str:
    circulation = row.get("circulation_side")
    summary_type = row.get("summary_type")
    if circulation not in TABLE3_CIRCULATION_SLUGS:
        raise InputError(f"Unknown Table 3 circulation label: {circulation}")
    if summary_type not in TABLE3_SUMMARY_SLUGS:
        raise InputError(f"Unknown Table 3 summary type: {summary_type}")
    return (f"holm2017-table3-{_slug(row.get('amino_acid', ''))}-"
            f"{TABLE3_CIRCULATION_SLUGS[circulation]}-{TABLE3_SUMMARY_SLUGS[summary_type]}")


def audit_holm_table2_candidate(
    repository_root: Path,
    *,
    source_inventory_path: str = "config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json",
    candidate_path: str = "config/observations/holm_2017_term_amino_acid_concentrations_candidate.json",
) -> dict:
    """Check all typed summary records against the hash-pinned aggregate cell ledger."""
    root = Path(repository_root)
    _, inventory_raw = _read_relative(root, source_inventory_path, label="Source inventory")
    _, candidate_raw = _read_relative(root, candidate_path, label="Candidate dataset")
    inventory = _json_object(inventory_raw, label="Source inventory")
    candidate = _json_object(candidate_raw, label="Candidate dataset")
    candidate_pointer = inventory.get("candidate_observation_intake")
    if not isinstance(candidate_pointer, dict):
        raise InputError("Source inventory is missing its candidate-intake pointer")
    if (candidate_pointer.get("path") != candidate_path
            or candidate_pointer.get("sha256") != sha256(candidate_raw)
            or candidate_pointer.get("record_count") != EXPECTED_ROWS):
        raise InputError("Candidate dataset differs from its pinned inventory pointer")
    intake = inventory.get("aggregate_table_intake")
    if not isinstance(intake, dict):
        raise InputError("Source inventory is missing its aggregate Table 2 intake")
    ledger_path, ledger_raw = _read_relative(root, intake.get("path"), label="Table 2 source-cell ledger")
    ledger_hash = sha256(ledger_raw)
    if ledger_hash != intake.get("sha256"):
        raise InputError("Table 2 ledger hash differs from the source inventory")
    try:
        reader = csv.DictReader(io.StringIO(ledger_raw.decode("utf-8-sig"), newline=""))
        if not REQUIRED_SOURCE_COLUMNS.issubset(reader.fieldnames or []):
            raise InputError("Table 2 ledger is missing required columns")
        source_rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Table 2 ledger is not valid bounded UTF-8 CSV") from exc
    if len(source_rows) != EXPECTED_ROWS or intake.get("row_count") != EXPECTED_ROWS:
        raise InputError("Table 2 ledger must contain exactly 76 aggregate cells")

    artifacts = candidate.get("artifacts")
    if not isinstance(artifacts, list):
        raise InputError("Candidate dataset must list source artifacts")
    ledger_artifacts = [item for item in artifacts if isinstance(item, dict)
                        and item.get("artifact_id") == "holm2017-table2-aggregate-extract"]
    if len(ledger_artifacts) != 1:
        raise InputError("Candidate must declare the local Table 2 source-cell extract once")
    ledger_artifact = ledger_artifacts[0]
    if (ledger_artifact.get("local_path") != intake.get("path")
            or ledger_artifact.get("sha256") != ledger_hash):
        raise InputError("Candidate artifact does not pin the Table 2 source-cell ledger")

    records = candidate.get("observations")
    if not isinstance(records, list) or len(records) != EXPECTED_ROWS:
        raise InputError("Candidate dataset must contain exactly 76 summary records")
    record_by_id = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("record_id"), str):
            raise InputError("Candidate observation needs a record ID")
        if record["record_id"] in record_by_id:
            raise InputError("Candidate record IDs must be unique")
        record_by_id[record["record_id"]] = record

    selected_ids = set()
    flagged = []
    vessel_denominators: dict[str, set[int]] = {vessel: set() for vessel in VESSEL_SLUGS}
    for row in source_rows:
        record_id = expected_record_id(row)
        if record_id in selected_ids or record_id not in record_by_id:
            raise InputError(f"Missing or duplicate candidate for source cell {row['source_table_cell_locator']}")
        selected_ids.add(record_id)
        record = record_by_id[record_id]
        if record.get("evidence_status") != "author_reported_summary":
            raise InputError(f"Summary status differs for {record_id}")
        if record.get("source_locator") != row["source_table_cell_locator"]:
            raise InputError(f"Source table-cell locator differs for {record_id}")
        if record.get("assay", {}).get("endpoint") != f"{row['amino_acid']} concentration in {row['vessel']}":
            raise InputError(f"Analyte/vessel endpoint differs for {record_id}")
        if record.get("assay", {}).get("unit") != row["concentration_unit"]:
            raise InputError(f"Concentration unit differs for {record_id}")
        if record.get("source", {}).get("sha256") != ledger_hash:
            raise InputError(f"Source-file hash differs for {record_id}")
        if record.get("source", {}).get("artifact_id") != "holm2017-table2-aggregate-extract":
            raise InputError(f"Source artifact differs for {record_id}")
        if (record.get("source", {}).get("uri") != ledger_artifact.get("uri")
                or record.get("source", {}).get("license") != ledger_artifact.get("license")):
            raise InputError(f"Source URI or license differs for {record_id}")
        value = _decimal(record.get("observation", {}).get("value"), label=f"{record_id} median")
        if value != _decimal(row["median_as_published"], label="source median"):
            raise InputError(f"Median differs from source literal for {record_id}")
        summary = record.get("observation", {}).get("summary_statistic")
        if not isinstance(summary, dict) or summary.get("kind") != "median_iqr":
            raise InputError(f"Typed median/IQR summary is missing for {record_id}")
        if summary.get("source_literal") != row["summary_cell_literal"]:
            raise InputError(f"Source summary literal differs for {record_id}")
        if _decimal(summary.get("lower_quartile"), label="candidate Q1") != _decimal(row["q1_as_published"], label="source Q1"):
            raise InputError(f"Q1 differs from source literal for {record_id}")
        if _decimal(summary.get("upper_quartile"), label="candidate Q3") != _decimal(row["q3_as_published"], label="source Q3"):
            raise InputError(f"Q3 differs from source literal for {record_id}")
        if summary.get("reported_sample_size") != int(row["vessel_N_as_reported"]):
            raise InputError(f"Vessel N differs from source table header for {record_id}")
        if summary.get("sample_size_scope") != row["vessel_N_scope"]:
            raise InputError(f"Sample-size scope differs for {record_id}")
        expected_n_locator = f"Table 2 header N row, column {row['vessel']}"
        if summary.get("sample_size_source_locator") != expected_n_locator:
            raise InputError(f"Sample-size source locator differs for {record_id}")
        if record.get("independent_unit", {}).get("id") is not None:
            raise InputError(f"Aggregate record must not invent a participant identity for {record_id}")
        if record.get("observation", {}).get("replicate_role") != "summary_only":
            raise InputError(f"Aggregate record must use summary_only replicate role for {record_id}")
        vessel_denominators[row["vessel"]].add(int(row["vessel_N_as_reported"]))
        if row["review_flag"]:
            flagged.append({"record_id": record_id, "locator": row["source_table_cell_locator"],
                            "literal": row["summary_cell_literal"], "flag": row["review_flag"]})

    if set(record_by_id) != selected_ids:
        raise InputError("Candidate dataset contains rows not present in the Table 2 source ledger")
    expected_flag = [{"record_id": "holm2017-table2-alanine-uterine-vein",
                      "locator": "Table 2 tr[14] td[3]", "literal": "255 [2, 294]",
                      "flag": "source XML reports Q1 literal 2; preserved without correction"}]
    if flagged != expected_flag:
        raise InputError("The unusual alanine/uterine-vein source literal must remain explicitly flagged")
    if any(len(values) != 1 for values in vessel_denominators.values()):
        raise InputError("Reported vessel denominators are inconsistent within Table 2")

    return {
        "status": "pass",
        "source_inventory_sha256": sha256(inventory_raw),
        "source_cell_ledger_sha256": ledger_hash,
        "candidate_dataset_sha256": sha256(candidate_raw),
        "source_rows_checked": len(source_rows),
        "candidate_summary_records_checked": len(records),
        "exact_source_cell_matches": len(selected_ids),
        "typed_median_iqr_records": sum(record["observation"]["summary_statistic"]["kind"] == "median_iqr"
                                         for record in records),
        "participant_level_records": 0,
        "all_values_are_concentrations": True,
        "blood_flow_or_flux_inferred": False,
        "unusual_literal_retained": flagged[0],
        "vessel_denominators": {vessel: next(iter(values)) for vessel, values in vessel_denominators.items()},
        "author_contacted": False,
    }


def audit_holm_table3_candidate(
    repository_root: Path,
    *,
    source_inventory_path: str = "config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json",
    candidate_path: str = "config/observations/holm_2017_term_amino_acid_differences_candidate.json",
) -> dict:
    """Check Table 3 medians, quartiles, printed p-values and bold markers."""
    root = Path(repository_root)
    _, inventory_raw = _read_relative(root, source_inventory_path, label="Source inventory")
    _, candidate_raw = _read_relative(root, candidate_path, label="Candidate dataset")
    inventory = _json_object(inventory_raw, label="Source inventory")
    candidate = _json_object(candidate_raw, label="Candidate dataset")
    candidate_pointer = inventory.get("candidate_paired_difference_intake")
    if not isinstance(candidate_pointer, dict):
        raise InputError("Source inventory is missing its paired-difference candidate pointer")
    if (candidate_pointer.get("path") != candidate_path
            or candidate_pointer.get("sha256") != sha256(candidate_raw)
            or candidate_pointer.get("record_count") != EXPECTED_ROWS):
        raise InputError("Table 3 candidate differs from its pinned inventory pointer")
    table = inventory.get("paired_difference_table_intake")
    if not isinstance(table, dict):
        raise InputError("Source inventory is missing its Table 3 intake")
    _, ledger_raw = _read_relative(root, table.get("path"), label="Table 3 source-cell ledger")
    ledger_hash = sha256(ledger_raw)
    if ledger_hash != table.get("sha256"):
        raise InputError("Table 3 ledger hash differs from the source inventory")
    try:
        reader = csv.DictReader(io.StringIO(ledger_raw.decode("utf-8-sig"), newline=""))
        if not REQUIRED_TABLE3_COLUMNS.issubset(reader.fieldnames or []):
            raise InputError("Table 3 ledger is missing required columns")
        source_rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Table 3 ledger is not valid bounded UTF-8 CSV") from exc
    if len(source_rows) != EXPECTED_ROWS or table.get("row_count") != EXPECTED_ROWS:
        raise InputError("Table 3 ledger must contain exactly 76 aggregate cells")

    ledger_artifacts = [item for item in candidate.get("artifacts", [])
                        if isinstance(item, dict)
                        and item.get("artifact_id") == "holm2017-table3-paired-difference-extract"]
    if len(ledger_artifacts) != 1:
        raise InputError("Candidate must declare the Table 3 source-cell extract once")
    ledger_artifact = ledger_artifacts[0]
    if (ledger_artifact.get("local_path") != table.get("path")
            or ledger_artifact.get("sha256") != ledger_hash):
        raise InputError("Candidate artifact does not pin the Table 3 source-cell ledger")

    records = candidate.get("observations")
    if not isinstance(records, list) or len(records) != EXPECTED_ROWS:
        raise InputError("Table 3 candidate must contain exactly 76 summary records")
    record_by_id = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("record_id"), str):
            raise InputError("Table 3 candidate observation needs a record ID")
        if record["record_id"] in record_by_id:
            raise InputError("Table 3 candidate record IDs must be unique")
        record_by_id[record["record_id"]] = record

    matched: set[str] = set()
    denominators: dict[str, set[int]] = {side: set() for side in TABLE3_CIRCULATION_SLUGS}
    direction_counts = {"positive": 0, "negative": 0, "zero": 0,
                        "positive_bold": 0, "negative_bold": 0,
                        "positive_nonbold": 0, "negative_nonbold": 0}
    adjusted_umbilical = []
    for row in source_rows:
        record_id = expected_table3_record_id(row)
        if record_id in matched or record_id not in record_by_id:
            raise InputError(f"Missing or duplicate candidate for {row['summary_cell_locator']}")
        matched.add(record_id)
        record = record_by_id[record_id]
        if record.get("evidence_status") != "author_reported_summary":
            raise InputError(f"Table 3 status differs for {record_id}")
        if record.get("observation", {}).get("replicate_role") != "summary_only":
            raise InputError(f"Table 3 aggregate must use summary_only role for {record_id}")
        if record.get("source_locator") != row["summary_cell_locator"]:
            raise InputError(f"Table 3 summary-cell locator differs for {record_id}")
        if record.get("assay", {}).get("endpoint") != f"{row['amino_acid']} {row['summary_type'].lower()} concentration difference ({row['circulation_side']})":
            raise InputError(f"Table 3 endpoint differs for {record_id}")
        if record.get("assay", {}).get("unit") != row["difference_unit"]:
            raise InputError(f"Table 3 unit differs for {record_id}")
        if (record.get("source", {}).get("artifact_id") != "holm2017-table3-paired-difference-extract"
                or record.get("source", {}).get("sha256") != ledger_hash
                or record.get("source", {}).get("uri") != ledger_artifact.get("uri")
                or record.get("source", {}).get("license") != ledger_artifact.get("license")):
            raise InputError(f"Table 3 source binding differs for {record_id}")
        observation = record.get("observation", {})
        if _decimal(observation.get("value"), label="candidate median") != _decimal(
                row["median_difference_as_published"], label="source median difference"):
            raise InputError(f"Table 3 median differs for {record_id}")
        summary = observation.get("summary_statistic")
        if not isinstance(summary, dict) or summary.get("kind") != "median_iqr":
            raise InputError(f"Table 3 typed median/IQR summary is missing for {record_id}")
        if summary.get("source_literal") != row["summary_cell_literal"]:
            raise InputError(f"Table 3 source summary literal differs for {record_id}")
        if _decimal(summary.get("lower_quartile"), label="candidate Q1") != _decimal(row["q1_as_published"], label="source Q1"):
            raise InputError(f"Table 3 Q1 differs for {record_id}")
        if _decimal(summary.get("upper_quartile"), label="candidate Q3") != _decimal(row["q3_as_published"], label="source Q3"):
            raise InputError(f"Table 3 Q3 differs for {record_id}")
        if summary.get("reported_sample_size") != int(row["sample_N_as_reported"]):
            raise InputError(f"Table 3 N differs for {record_id}")
        if summary.get("sample_size_scope") != row["sample_N_scope"]:
            raise InputError(f"Table 3 N scope differs for {record_id}")
        expected_n_locator = f"Table 3 N row, circulation {row['circulation_side']}"
        if summary.get("sample_size_source_locator") != expected_n_locator:
            raise InputError(f"Table 3 N locator differs for {record_id}")
        if record.get("independent_unit", {}).get("id") is not None:
            raise InputError(f"Table 3 summary cannot invent a participant identity for {record_id}")

        qualifications = observation.get("source_qualifications", [])
        expected_bold = row["summary_cell_marked_bold"] == "True"
        expected_qualifications = {
            "published_p_value": ("as_published", row["p_value_cell_locator"],
                                   f"Table 3 printed p-value literal: {row['p_value_as_published']}; no p-value was recalculated."),
            "source_bold_marker": ("marked_bold" if expected_bold else "not_bold",
                                   row["summary_cell_locator"],
                                   "Table 3 footnote defines bold differences as significant after FDR correction; this source cell is " + ("marked bold." if expected_bold else "not marked bold.")),
            "difference_sign_convention": ("source_reported", "Table 3 footnote",
                                           row["positive_difference_interpretation"]),
        }
        for criterion, (status, locator, label) in expected_qualifications.items():
            if not any(isinstance(item, dict) and item.get("criterion_code") == criterion
                       and item.get("status_code") == status and item.get("source_locator") == locator
                       and item.get("criterion_label") == label
                       for item in qualifications):
                raise InputError(f"Table 3 source qualification differs for {record_id}: {criterion}")

        median = _decimal(row["median_difference_as_published"], label="source median difference")
        bold = expected_bold
        if median > 0:
            direction_counts["positive"] += 1
            direction_counts["positive_bold" if bold else "positive_nonbold"] += 1
        elif median < 0:
            direction_counts["negative"] += 1
            direction_counts["negative_bold" if bold else "negative_nonbold"] += 1
        else:
            direction_counts["zero"] += 1
        if row["circulation_side"] == "Umbilical" and row["summary_type"] == "Adjusted for transfer of water across the placenta":
            adjusted_umbilical.append((row["amino_acid"], median, bold))
        denominators[row["circulation_side"]].add(int(row["sample_N_as_reported"]))

    if set(record_by_id) != matched:
        raise InputError("Table 3 candidate contains rows absent from the paired-difference source ledger")
    if any(len(values) != 1 for values in denominators.values()):
        raise InputError("Table 3 reports inconsistent N values within a circulation")
    adjusted_counts = {
        "analyte_count": len(adjusted_umbilical),
        "positive_median_count": sum(value > 0 for _, value, _ in adjusted_umbilical),
        "negative_median_count": sum(value < 0 for _, value, _ in adjusted_umbilical),
        "source_bolded_fdr_significant_positive_count": sum(value > 0 and bold for _, value, bold in adjusted_umbilical),
        "source_bolded_fdr_significant_negative_count": sum(value < 0 and bold for _, value, bold in adjusted_umbilical),
        "negative_bolded_analyte": next((name for name, value, bold in adjusted_umbilical if value < 0 and bold), None),
    }
    declared_counts = inventory.get("descriptive_consistency_audit", {})
    for key, value in adjusted_counts.items():
        if declared_counts.get(key) != value:
            raise InputError(f"Table 3 descriptive check differs from source inventory: {key}")
    return {
        "status": "pass",
        "source_inventory_sha256": sha256(inventory_raw),
        "source_cell_ledger_sha256": ledger_hash,
        "candidate_dataset_sha256": sha256(candidate_raw),
        "source_rows_checked": len(source_rows),
        "candidate_summary_records_checked": len(records),
        "exact_source_cell_matches": len(matched),
        "typed_median_iqr_records": len(records),
        "participant_level_records": 0,
        "printed_p_values_preserved": len(records),
        "source_bold_markers_preserved": len(records),
        "direction_conventions_preserved": len(records),
        "p_values_recalculated": False,
        "fdr_significance_recalculated": False,
        "blood_flow_or_flux_inferred": False,
        "vessel_circulation_denominators": {side: next(iter(values)) for side, values in denominators.items()},
        "direction_counts_all_table3_cells": direction_counts,
        "water_adjusted_umbilical_descriptive_check": adjusted_counts,
        "author_contacted": False,
    }
