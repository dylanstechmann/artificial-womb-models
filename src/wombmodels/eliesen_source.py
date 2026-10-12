"""Source-cell reconciliation for Eliesen et al. 2024 Supplementary Table S3.

This bounded audit compares the pinned DOCX table's literal text with the
existing concentration-observation CSV. It does not estimate amount, flux,
recovery, transfer parameters, or biological outcomes.
"""
from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation, localcontext
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

from .artifacts import InputError, decode_json, sha256

MAX_DOCX_BYTES = 1_000_000
MAX_CSV_BYTES = 1_000_000
MAX_MANIFEST_BYTES = 1_000_000
MAX_ARCHIVE_ENTRIES = 128
MAX_UNCOMPRESSED_BYTES = 10_000_000
MAX_MEMBER_BYTES = 5_000_000
MAX_DOCUMENT_XML_BYTES = 5_000_000

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}
TABLE_HEADER_GROUPS = [
    "Tofacitinib control (nM)",
    "Tofacitinib maternal (nM)",
    "Tofacitinib fetal (nM)",
]
TABLE_COLUMNS = [
    "Time (min)",
    "No placenta in system",
    "Placenta 1", "Placenta 2", "Placenta 3",
    "Placenta 1", "Placenta 2", "Placenta 3",
]
CSV_COLUMNS = [
    "record_id", "source_artifact_id", "source_table", "perfusion_label",
    "unit_role", "analyte", "compartment", "measurement_time",
    "measurement_time_unit", "source_value_lexeme", "value_numeric",
    "concentration_unit", "measurement_status", "missingness_reason",
    "source_locator",
]
MISSINGNESS_REASON = "Source table marks N/A; not assessed; not zero."


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
        raise InputError(f"{label} path must be a nonempty repository-relative path")
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


def _docx_table(
    raw: bytes, *, table_index: int = 2, table_label: str = "Supplementary Table S3"
) -> tuple[list[list[str]], int]:
    if len(raw) > MAX_DOCX_BYTES:
        raise InputError("Source DOCX exceeds its audit limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = [item.filename for item in entries]
            if (len(entries) > MAX_ARCHIVE_ENTRIES or len(names) != len(set(names))
                    or sum(item.file_size for item in entries) > MAX_UNCOMPRESSED_BYTES
                    or any(item.file_size > MAX_MEMBER_BYTES or item.flag_bits & 1 for item in entries)):
                raise InputError("Source DOCX archive exceeds bounds or has duplicate/encrypted members")
            for name in names:
                member = PurePosixPath(name)
                if (member.is_absolute() or "\\" in name
                        or any(part in {"", ".", ".."} for part in member.parts)):
                    raise InputError("Source DOCX archive contains an unsafe member path")
            if "word/document.xml" not in names:
                raise InputError("Source DOCX is missing word/document.xml")
            if archive.getinfo("word/document.xml").file_size > MAX_DOCUMENT_XML_BYTES:
                raise InputError("Source DOCX document XML exceeds its audit limit")
            document_raw = archive.read("word/document.xml")
    except InputError:
        raise
    except (zipfile.BadZipFile, KeyError, RuntimeError, EOFError, OSError, ValueError) as exc:
        raise InputError("Source DOCX is not a valid bounded Office document") from exc

    if b"<!DOCTYPE" in document_raw.upper() or b"<!ENTITY" in document_raw.upper():
        raise InputError("Source DOCX XML declarations are unsupported")
    try:
        document = ET.fromstring(document_raw)
    except ET.ParseError as exc:
        raise InputError("Source DOCX document XML is invalid") from exc
    tables = document.findall(".//w:tbl", NS)
    if len(tables) != 3:
        raise InputError("Expected exactly three tables in the pinned supplement")
    if not isinstance(table_index, int) or not 0 <= table_index < len(tables):
        raise InputError("Requested table index is outside the pinned supplement")
    target = tables[table_index]
    if target.findall(".//w:instrText", NS) or target.findall(".//w:fldSimple", NS):
        raise InputError(f"{table_label} contains a field instead of literal source text")

    rows: list[list[str]] = []
    for row in target.findall("./w:tr", NS):
        cells = []
        for cell in row.findall("./w:tc", NS):
            # Concatenate text runs exactly as stored; adding spaces can alter
            # decimal lexemes split across runs.
            cells.append("".join(node.text or "" for node in cell.findall(".//w:t", NS)))
        rows.append(cells)
    return rows, len(tables)


def _decimal(value: str, *, label: str) -> Decimal:
    try:
        parsed = Decimal(value)
        if not parsed.is_finite():
            raise InvalidOperation
        return parsed
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{label} must be a finite decimal value") from exc


def audit_eliesen_table_s3(repository_root: Path, manifest_path: Path) -> dict:
    """Reconcile every Table S3 value lexeme and observation row to the DOCX."""
    root = Path(repository_root).resolve()
    manifest_raw = _read_file(Path(manifest_path), label="Dataset manifest", limit=MAX_MANIFEST_BYTES)
    manifest = decode_json(manifest_raw)
    if not isinstance(manifest, dict):
        raise InputError("Dataset manifest must be a JSON object")
    source = manifest.get("source_artifact")
    observation = manifest.get("observation_file")
    if not isinstance(source, dict) or not isinstance(observation, dict):
        raise InputError("Dataset manifest is missing source-artifact or observation metadata")

    _, docx_raw = _load_relative(root, source.get("local_path"), label="Source DOCX", limit=MAX_DOCX_BYTES)
    _, csv_raw = _load_relative(root, observation.get("path"), label="Observation CSV", limit=MAX_CSV_BYTES)
    docx_hash = sha256(docx_raw)
    csv_hash = sha256(csv_raw)
    if docx_hash != source.get("sha256"):
        raise InputError("Source DOCX hash differs from the pinned manifest")
    if csv_hash != observation.get("sha256"):
        raise InputError("Observation CSV hash differs from the pinned manifest")
    if source.get("table") != "Supplementary Table S3":
        raise InputError("Manifest does not identify Supplementary Table S3")

    table, table_count = _docx_table(docx_raw)
    if len(table) != 12 or table[0][1:] != TABLE_HEADER_GROUPS or table[1] != TABLE_COLUMNS:
        raise InputError("Supplementary Table S3 headers or 10-timepoint layout differ from the audited source")
    quantity = manifest.get("observed_quantity")
    if not isinstance(quantity, dict):
        raise InputError("Manifest is missing observed-quantity metadata")
    expected_times = quantity.get("reported_timepoints")
    if (not isinstance(expected_times, list) or len(expected_times) != 10
            or [row[0] for row in table[2:]] != [str(value) for value in expected_times]):
        raise InputError("Manifest timepoints do not match the source table rows")

    try:
        reader = csv.DictReader(io.StringIO(csv_raw.decode("utf-8-sig"), newline=""))
        if reader.fieldnames != CSV_COLUMNS:
            raise InputError("Observation CSV columns differ from the audited schema")
        records = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Observation CSV is not valid bounded UTF-8 CSV") from exc
    if any(None in row or any(value is None for value in row.values()) for row in records):
        raise InputError("Observation CSV contains a malformed row")
    if len(records) != observation.get("rows") or len(records) != 70:
        raise InputError("Observation row count differs from the pinned source layout")

    source_units = manifest.get("source_units")
    if not isinstance(source_units, dict):
        raise InputError("Manifest is missing source-unit metadata")
    placenta_labels = source_units.get("experimental_perfusion_labels")
    if placenta_labels != ["Placenta 1", "Placenta 2", "Placenta 3"]:
        raise InputError("Manifest placenta labels differ from Supplementary Table S3")
    if (quantity.get("analyte") != "tofacitinib" or quantity.get("concentration_unit") != "nM"
            or quantity.get("time_unit") != "min"):
        raise InputError("Manifest analyte or units differ from Supplementary Table S3")

    expected: dict[tuple[str, str, str], dict[str, str]] = {}
    for table_row in table[2:]:
        time = table_row[0]
        # Source column index, label, role and compartment are explicit so the
        # system-control column cannot be mistaken for a fourth placenta.
        columns = [(1, "No placenta in system", "no_placenta_system_control",
                    "system control; compartment not specified", "Tofacitinib control (nM)")]
        columns.extend((index, f"Placenta {index - 1}", "placenta_perfusion", "maternal reservoir",
                        "Tofacitinib maternal (nM)") for index in range(2, 5))
        columns.extend((index, f"Placenta {index - 4}", "placenta_perfusion", "fetal reservoir",
                        "Tofacitinib fetal (nM)") for index in range(5, 8))
        for index, label, role, compartment, column_header in columns:
            lexeme = table_row[index]
            source_locator = f"Table S3; row time={time} min; column={column_header}, {label}"
            key = (time, label, compartment)
            if key in expected:
                raise InputError("Source table contains duplicate time/unit observations")
            expected[key] = {
                "source_value_lexeme": lexeme,
                "perfusion_label": label,
                "unit_role": role,
                "analyte": "tofacitinib",
                "compartment": compartment,
                "measurement_time": time,
                "measurement_time_unit": "min",
                "concentration_unit": "nM",
                "source_locator": source_locator,
            }

    indexed: dict[tuple[str, str, str], dict[str, str]] = {}
    record_ids: set[str] = set()
    numeric_count = not_assessed_count = 0
    for row in records:
        record_id = row["record_id"]
        key = (row["measurement_time"], row["perfusion_label"], row["compartment"])
        if not record_id or record_id in record_ids:
            raise InputError("Observation CSV contains a blank or duplicate record_id")
        if key in indexed:
            raise InputError("Observation CSV contains a duplicate source-unit/time row")
        if key not in expected:
            raise InputError("Observation CSV contains a row absent from Supplementary Table S3")
        source_row = expected[key]
        for field, expected_value in source_row.items():
            actual = row[field]
            if actual != expected_value:
                raise InputError(f"Observation {field} differs from the source at {source_row['source_locator']}")
        if row["source_artifact_id"] != source.get("artifact_id") or row["source_table"] != "Table S3":
            raise InputError("Observation row names a different source artifact or table")

        if source_row["source_value_lexeme"] == "N/A":
            if (row["value_numeric"] or row["measurement_status"] != "not_assessed"
                    or row["missingness_reason"] != MISSINGNESS_REASON):
                raise InputError("Source N/A must remain not_assessed with no numeric value")
            not_assessed_count += 1
        else:
            if row["measurement_status"] != "reported_numeric" or row["missingness_reason"]:
                raise InputError("Numeric source value has inconsistent status or missingness metadata")
            source_number = _decimal(source_row["source_value_lexeme"], label="Source table value")
            csv_number = _decimal(row["value_numeric"], label="Observation numeric value")
            if source_number != csv_number:
                raise InputError(f"Numeric value differs from the source at {source_row['source_locator']}")
            numeric_count += 1
        record_ids.add(record_id)
        indexed[key] = row

    if set(indexed) != set(expected):
        raise InputError("Observation CSV key set differs from the source time/unit cells")
    if (numeric_count != observation.get("reported_numeric_rows")
            or not_assessed_count != observation.get("not_assessed_rows")
            or numeric_count != 69 or not_assessed_count != 1):
        raise InputError("Numeric and not-assessed counts differ from the pinned manifest")

    return {
        "status": "pass",
        "scope": "source text, observation keys, values, units, and missingness reconciliation only",
        "source_docx_sha256": docx_hash,
        "observation_csv_sha256": csv_hash,
        "source_table": "Supplementary Table S3",
        "source_table_index": 3,
        "source_table_count": table_count,
        "source_rows_reconciled": len(expected),
        "observation_rows_reconciled": len(records),
        "unique_record_ids": len(record_ids),
        "exact_source_lexeme_matches": len(expected),
        "numeric_values_reconciled": numeric_count,
        "not_assessed_values_preserved": not_assessed_count,
        "source_table_uses_literal_text_values": True,
        "dimensional_transport_fit_assessed": False,
        "human_source_review_complete": False,
    }


def derive_eliesen_placenta_summary(repository_root: Path, manifest_path: Path) -> list[dict[str, str]]:
    """Derive arithmetic mean and sample SD for the three placenta labels.

    The system-control series is deliberately excluded because its replicate
    count is not reported. The source-cell audit runs first; summaries use the
    table's displayed numeric lexemes, with no interpolation or fitting.
    """
    root = Path(repository_root).resolve()
    audit_eliesen_table_s3(root, manifest_path)
    manifest = decode_json(_read_file(Path(manifest_path), label="Dataset manifest", limit=MAX_MANIFEST_BYTES))
    observation = manifest["observation_file"]
    _, csv_raw = _load_relative(root, observation["path"], label="Observation CSV", limit=MAX_CSV_BYTES)
    csv_hash = sha256(csv_raw)
    try:
        records = list(csv.DictReader(io.StringIO(csv_raw.decode("utf-8-sig"), newline="")))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Observation CSV is not valid bounded UTF-8 CSV") from exc

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in records:
        if row["unit_role"] != "placenta_perfusion":
            continue
        grouped.setdefault((row["compartment"], row["measurement_time"]), []).append(row)

    labels = ["Placenta 1", "Placenta 2", "Placenta 3"]
    times = [str(value) for value in manifest["observed_quantity"]["reported_timepoints"]]
    expected_groups = {(compartment, time) for compartment in ("maternal reservoir", "fetal reservoir")
                       for time in times}
    if set(grouped) != expected_groups:
        raise InputError("Placenta concentration rows do not form both reported ten-timepoint series")

    summaries = []
    for compartment in ("maternal reservoir", "fetal reservoir"):
        for time in times:
            rows = sorted(grouped[(compartment, time)], key=lambda row: labels.index(row["perfusion_label"]))
            if [row["perfusion_label"] for row in rows] != labels:
                raise InputError("Each summary point must contain exactly Placenta 1, 2, and 3")
            values = [_decimal(row["value_numeric"], label="Placenta concentration") for row in rows]
            mean = sum(values, Decimal(0)) / Decimal(3)
            with localcontext() as context:
                context.prec = 40
                variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / Decimal(2)
                sample_sd = variance.sqrt()
            summaries.append({
                "source_artifact_id": manifest["source_artifact"]["artifact_id"],
                "source_table": "Table S3",
                "source_docx_sha256": manifest["source_artifact"]["sha256"],
                "source_csv_sha256": csv_hash,
                "compartment": compartment,
                "measurement_time": time,
                "measurement_time_unit": "min",
                "concentration_unit": "nM",
                "placenta_labels": ";".join(labels),
                "n_placenta_perfusion_labels": "3",
                "source_value_lexemes": ";".join(row["source_value_lexeme"] for row in rows),
                "arithmetic_mean": format(mean.quantize(Decimal("0.000001")), "f"),
                "sample_sd": format(sample_sd.quantize(Decimal("0.000001")), "f"),
                "summary_method": "arithmetic mean and sample SD of displayed Table S3 values; no fit",
            })
    return summaries


def derive_eliesen_antipyrine_endpoint(repository_root: Path, manifest_path: Path) -> list[dict[str, str]]:
    """Recompute the S2 antipyrine 180-minute summary as a table-mapping control."""
    root = Path(repository_root).resolve()
    audit_eliesen_table_s3(root, manifest_path)
    manifest = decode_json(_read_file(Path(manifest_path), label="Dataset manifest", limit=MAX_MANIFEST_BYTES))
    source = manifest["source_artifact"]
    _, docx_raw = _load_relative(root, source["local_path"], label="Source DOCX", limit=MAX_DOCX_BYTES)
    table, _ = _docx_table(docx_raw, table_index=1, table_label="Supplementary Table S2")
    expected_header0 = ["", "Antipyrine maternal (µg/ml)", "Antipyrine fetal (µg/ml)"]
    expected_header1 = ["Time (min)", "Placenta 1", "Placenta 2", "Placenta 3",
                        "Placenta 1", "Placenta 2", "Placenta 3"]
    if (len(table) != 12 or table[0] != expected_header0 or table[1] != expected_header1
            or table[-1][0] != "180" or len(table[-1]) != 7):
        raise InputError("Supplementary Table S2 headers or 180-minute row differ from the audited source")

    summaries = []
    for compartment, start, published_mean, published_sd in (
            ("maternal reservoir", 1, Decimal("36.9"), Decimal("3.0")),
            ("fetal reservoir", 4, Decimal("36.7"), Decimal("1.3"))):
        lexemes = table[-1][start:start + 3]
        values = [_decimal(value, label="Antipyrine Table S2 value") for value in lexemes]
        mean = sum(values, Decimal(0)) / Decimal(3)
        with localcontext() as context:
            context.prec = 40
            variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / Decimal(2)
            sample_sd = variance.sqrt()
        rounded_mean = mean.quantize(Decimal("0.1"))
        rounded_sd = sample_sd.quantize(Decimal("0.1"))
        summaries.append({
            "source_artifact_id": source["artifact_id"],
            "source_table": "Table S2",
            "source_docx_sha256": source["sha256"],
            "analyte": "antipyrine",
            "compartment": compartment,
            "measurement_time": "180",
            "measurement_time_unit": "min",
            "concentration_unit": "µg/ml",
            "placenta_labels": "Placenta 1;Placenta 2;Placenta 3",
            "source_value_lexemes": ";".join(lexemes),
            "arithmetic_mean": format(mean.quantize(Decimal("0.000001")), "f"),
            "sample_sd": format(sample_sd.quantize(Decimal("0.000001")), "f"),
            "article_reported_mean": format(published_mean, "f"),
            "article_reported_sd": format(published_sd, "f"),
            "rounded_summary_matches_article": str(
                (rounded_mean, rounded_sd) == (published_mean, published_sd)
            ).lower(),
        })
    return summaries
