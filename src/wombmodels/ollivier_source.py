"""Bounded source reconciliation for Ollivier et al. 2026 perfusion intake.

The audits preserve literal source cells and reported summaries. Derived ratios
are arithmetic diagnostics only: they do not supply missing volumes, estimate
flux, resolve source discrepancies, or establish biological model validity.
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

from .artifacts import InputError, decode_json, sha256
from .observations import _coverage_closure, validate_dataset

MAX_DOCX_BYTES = 1_000_000
MAX_XML_BYTES = 1_000_000
MAX_CSV_BYTES = 1_000_000
MAX_JSON_BYTES = 1_000_000
MAX_ARTIFACT_BYTES = 2_000_000
MAX_ARCHIVE_ENTRIES = 128
MAX_UNCOMPRESSED_BYTES = 10_000_000
MAX_MEMBER_BYTES = 5_000_000
MAX_DOCUMENT_XML_BYTES = 5_000_000

ARTIFACT_DIRECTORY = str(PurePosixPath("artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12"))
CARD_PATH = str(PurePosixPath("config/observations/ollivier_2026_aciclovir_antipyrine_perfusion_candidate.json"))
INVENTORY_PATH = str(PurePosixPath("config/source_inventories/ollivier_2026_aciclovir_perfusion.json"))
TIME_UNIT = "min of ex-vivo perfusion; reported as 3 hours; not gestational time"
METHODS_118_DA_SENTENCE_SHA256 = "1bf3fd9557fad56386d0c11957425c4e6b6897b2bf720b13d8300150b80a1d0f"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MATH_NS = "http://www.w3.org/1998/Math/MathML"
NS = {"w": WORD_NS}
MATH = {"m": MATH_NS}
HEADERS = [
    "Maternal Concentration at 3 hours of Antipyrine(µg/mL)",
    "Fetal Concentration at 3 hours of Antipyrine (µg/mL)",
    "Fetal Transfer Rate of Antipyrine (%)",
    "Fetal concentration / Maternal concentration rate of Antipyrine (%)",
]
ROW_LABELS = [f"Placenta {index}" for index in range(1, 10)] + ["Mean", "Standard Deviation"]
SPECS = [
    {"compartment": "maternal reservoir", "endpoint_kind": "concentration", "unit": "µg/mL",
     "endpoint": "Maternal antipyrine concentration at 3 hours"},
    {"compartment": "fetal reservoir", "endpoint_kind": "concentration", "unit": "µg/mL",
     "endpoint": "Fetal antipyrine concentration at 3 hours"},
    {"compartment": "fetal and maternal reservoirs", "endpoint_kind": "fetal_transfer_rate", "unit": "%",
     "endpoint": "Fetal transfer rate of antipyrine at 3 hours"},
    {"compartment": "fetal-to-maternal concentration ratio", "endpoint_kind": "concentration_ratio", "unit": "%",
     "endpoint": "Fetal/maternal antipyrine concentration ratio at 3 hours"},
]
CSV_COLUMNS = [
    "record_id", "source_artifact_id", "source_table", "row_index", "column_index",
    "row_label", "row_role", "analyte", "compartment", "endpoint_kind",
    "measurement_time", "measurement_time_unit", "source_column_header",
    "source_value_lexeme", "value_numeric", "unit", "measurement_status", "source_locator",
]
SUMMARY_EXPECTED = {
    "ollivier2026-results-aciclovir-maternal-3h": (7.55, 2.46, "mg/L", 180, "7.55 mg/L (SD: 2.46 mg/L)"),
    "ollivier2026-results-aciclovir-fetal-3h": (1.85, 0.60, "mg/L", 180, "1.85 mg/L (SD: 0.60 mg/L)"),
    "ollivier2026-results-aciclovir-ftr-3h": (17.4, 7.8, "%", 180, "17.4% at 3 h (SD: 7.8%)"),
    "ollivier2026-results-fetal-volume-3h": (201, 57, "mL", 180, "201 mL (SD: 57 mL)"),
    "ollivier2026-results-maternal-volume-3h": (247, 53, "mL", 180, "247 mL (SD: 53 mL)"),
    "ollivier2026-results-fetal-ph": (7.2, 0.1, "pH units", None, "7.2 (SD: 0.1)"),
    "ollivier2026-results-maternal-ph": (7.4, 0.1, "pH units", None, "7.4 (SD: 0.1)"),
    "ollivier2026-results-fetal-temperature": (37.4, 0.7, "degC", None, "37.4°C (SD: 0.7°C)"),
    "ollivier2026-results-maternal-temperature": (37.3, 0.5, "degC", None, "37.3°C (SD: 0.5°C)"),
    "ollivier2026-results-fetal-arterial-pressure": (67.5, 30.9, "mmHg", None, "67.5 mmHg (SD: 30.9 mmHg)"),
    "ollivier2026-table1-umbilical-artery-ph": (7.28, 1.60, "pH units", None, "7.28 (SD: 1.60)"),
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


def _json_object(raw: bytes, *, label: str) -> dict:
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a JSON object")
    return value


def _load_manifest(repository_root: Path, manifest_path: Path) -> tuple[Path, bytes, dict]:
    root = Path(repository_root).resolve()
    raw = _read_file(Path(manifest_path), label="Dataset manifest", limit=MAX_JSON_BYTES)
    return root, raw, _json_object(raw, label="Dataset manifest")


def _verify_pin(metadata: object, raw: bytes, *, label: str) -> None:
    if not isinstance(metadata, dict):
        raise InputError(f"{label} pin must be an object")
    if sha256(raw) != metadata.get("sha256"):
        raise InputError(f"{label} hash differs from the pinned SHA-256")
    if len(raw) != metadata.get("size_bytes") or type(metadata.get("size_bytes")) is not int:
        raise InputError(f"{label} byte size differs from the pinned size")


def _decimal(value: object, *, label: str) -> Decimal:
    if isinstance(value, bool):
        raise InputError(f"{label} must be a finite decimal value")
    try:
        parsed = Decimal(str(value))
        if not parsed.is_finite():
            raise InvalidOperation
        return parsed
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{label} must be a finite decimal value") from exc


def _docx_table(raw: bytes) -> tuple[list[list[str]], int, int]:
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
    if len(tables) != 1:
        raise InputError("Expected exactly one table in the pinned Table S1 DOCX")
    target = tables[0]
    if target.findall(".//w:instrText", NS) or target.findall(".//w:fldSimple", NS):
        raise InputError("Table S1 contains a field instead of literal source text")
    if target.findall(".//w:del", NS) or target.findall(".//w:ins", NS):
        raise InputError("Table S1 contains tracked-change text instead of one literal cell reading")

    table: list[list[str]] = []
    paragraph_count = run_count = 0
    for row in target.findall("./w:tr", NS):
        cells = []
        for cell in row.findall("./w:tc", NS):
            paragraphs = cell.findall("./w:p", NS)
            if not paragraphs:
                raise InputError("Table S1 cell has no literal paragraph")
            paragraph_count += len(paragraphs)
            paragraph_texts = []
            for paragraph in paragraphs:
                runs = paragraph.findall(".//w:r", NS)
                if not runs:
                    raise InputError("Table S1 paragraph has no literal text run")
                run_count += len(runs)
                paragraph_texts.append("".join(
                    text.text or "" for run in runs for text in run.findall(".//w:t", NS)))
            # Do not insert spaces or newlines between source paragraphs/runs:
            # the pinned first header stores its unit in a second paragraph.
            cells.append("".join(paragraph_texts))
        table.append(cells)
    if len(table) != 12 or any(len(row) != 5 for row in table):
        raise InputError("Table S1 must have exactly 12 rows by five columns")
    if table[0] != ["\u00a0"] + HEADERS or [row[0] for row in table[1:]] != ROW_LABELS:
        raise InputError("Table S1 headers or placenta/summary row labels differ from the source")
    lexemes = [value for row in table[1:] for value in row[1:]]
    if len(lexemes) != 44 or any(re.fullmatch(r"[0-9]+,[0-9]{2}", value) is None for value in lexemes):
        raise InputError("Table S1 must contain 44 two-decimal decimal-comma numeric cells")
    return table, paragraph_count, run_count


def _expected_source_rows(table: list[list[str]]) -> list[dict[str, str]]:
    expected = []
    for row_index in range(1, 12):
        label = table[row_index][0]
        for column_index in range(1, 5):
            spec = SPECS[column_index - 1]
            lexeme = table[row_index][column_index]
            locator = (f"Table S1; DOCX table 1; zero-based row {row_index} ({label}); "
                       f"zero-based column {column_index}; header={HEADERS[column_index - 1]}")
            expected.append({
                "record_id": f"ollivier2026-table-s1-r{row_index:02d}-c{column_index:02d}",
                "source_artifact_id": "ollivier2026-table-s1-docx",
                "source_table": "Table S1", "row_index": str(row_index),
                "column_index": str(column_index), "row_label": label,
                "row_role": "placenta_perfusion" if row_index <= 9 else "source_reported_summary",
                "analyte": "antipyrine", "compartment": spec["compartment"],
                "endpoint_kind": spec["endpoint_kind"], "measurement_time": "180",
                "measurement_time_unit": TIME_UNIT, "source_column_header": HEADERS[column_index - 1],
                "source_value_lexeme": lexeme, "value_numeric": lexeme.replace(",", "."),
                "unit": spec["unit"],
                "measurement_status": "reported_numeric" if row_index <= 9 else "source_reported_summary",
                "source_locator": locator,
            })
    return expected


def _csv_records(raw: bytes) -> list[dict[str, str]]:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise InputError("Observation CSV must be UTF-8 without BOM and use LF line endings")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
        if reader.fieldnames != CSV_COLUMNS:
            raise InputError("Observation CSV columns differ from the audited schema")
        records = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("Observation CSV is not valid bounded UTF-8 CSV") from exc
    if any(None in row or any(value is None for value in row.values()) for row in records):
        raise InputError("Observation CSV contains a malformed row")
    if len(records) != 44:
        raise InputError("Observation CSV must contain exactly 44 Table S1 numeric cells")
    return records


def _table_inputs(repository_root: Path, manifest_path: Path):
    root, manifest_raw, manifest = _load_manifest(repository_root, manifest_path)
    source = manifest.get("source_artifact")
    observation = manifest.get("observation_file")
    if not isinstance(source, dict) or not isinstance(observation, dict):
        raise InputError("Dataset manifest is missing source-artifact or observation metadata")
    if source.get("artifact_id") != "ollivier2026-table-s1-docx" or source.get("table") and source.get("table") != "Table S1":
        raise InputError("Dataset manifest does not identify the Ollivier Table S1 DOCX")
    _, docx_raw = _load_relative(root, source.get("local_path"), label="Source DOCX", limit=MAX_DOCX_BYTES)
    _, csv_raw = _load_relative(root, observation.get("path"), label="Observation CSV", limit=MAX_CSV_BYTES)
    _verify_pin(source, docx_raw, label="Source DOCX")
    _verify_pin(observation, csv_raw, label="Observation CSV")
    if observation.get("rows") != 44 or observation.get("placenta_perfusion_rows") != 36 or observation.get("source_reported_summary_rows") != 8:
        raise InputError("Manifest Table S1 row-role counts differ from the pinned 36 + 8 layout")
    return root, manifest_raw, manifest, docx_raw, csv_raw


def audit_ollivier_table_s1(repository_root: Path, manifest_path: Path) -> dict:
    """Reconcile all 44 literal Table S1 cells and their CSV representation."""
    _, _, manifest, docx_raw, csv_raw = _table_inputs(repository_root, manifest_path)
    table, paragraph_count, run_count = _docx_table(docx_raw)
    expected = _expected_source_rows(table)
    records = _csv_records(csv_raw)
    for index, (source_row, actual) in enumerate(zip(expected, records), 1):
        if actual["record_id"] != source_row["record_id"]:
            raise InputError(f"Observation record_id differs from the pinned Table S1 layout at CSV row {index}")
        for field in CSV_COLUMNS:
            if actual[field] != source_row[field]:
                raise InputError(f"Observation {field} differs from the source at {source_row['source_locator']}")
        if _decimal(actual["source_value_lexeme"].replace(",", "."), label="Source table value") != _decimal(actual["value_numeric"], label="Observation numeric value"):
            raise InputError(f"Numeric value differs from the source at {source_row['source_locator']}")
    reconciliation = manifest.get("source_reconciliation", {})
    for field, expected_value in (("numeric_cells_reconciled", 44), ("individual_cells", 36),
                                  ("source_summary_cells", 8), ("source_table_count", 1),
                                  ("source_rows", 12), ("source_columns", 5),
                                  ("human_source_review_complete", False)):
        if reconciliation.get(field) != expected_value:
            raise InputError(f"Manifest source-reconciliation field {field} differs from the audit")
    return {
        "status": "pass",
        "scope": "literal DOCX paragraph/run text, all 44 source cells, CSV schema, values, roles, units and pins only",
        "source_docx_sha256": sha256(docx_raw), "source_docx_size_bytes": len(docx_raw),
        "observation_csv_sha256": sha256(csv_raw), "observation_csv_size_bytes": len(csv_raw),
        "source_table": "Table S1", "source_table_index": 1, "source_table_count": 1,
        "source_table_rows": 12, "source_table_columns": 5,
        "source_paragraphs_reconciled": paragraph_count, "source_runs_reconciled": run_count,
        "source_cells_reconciled": 44, "observation_rows_reconciled": 44,
        "placenta_perfusion_rows": 36, "source_reported_summary_rows": 8,
        "exact_decimal_comma_lexeme_matches": 44, "numeric_values_reconciled": 44,
        "source_table_uses_literal_paragraph_run_text": True,
        "dimensional_transport_fit_assessed": False, "human_source_review_complete": False,
    }


def _mean_sample_sd(values: list[Decimal]) -> tuple[Decimal, Decimal]:
    if len(values) != 9:
        raise InputError("Each Ollivier source summary must contain exactly nine placenta values")
    with localcontext() as context:
        context.prec = 50
        mean = sum(values, Decimal(0)) / Decimal(9)
        variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / Decimal(8)
        return mean, variance.sqrt()


def _six(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001")), "f")


def derive_ollivier_antipyrine_summary_and_volume_ratios(repository_root: Path, manifest_path: Path) -> dict:
    """Recompute Table S1 summaries, F/M ratios and algebraic Vf/Vm diagnostics."""
    root = Path(repository_root).resolve()
    audit_ollivier_table_s1(root, manifest_path)
    _, _, manifest, _, csv_raw = _table_inputs(root, manifest_path)
    records = _csv_records(csv_raw)
    individuals = [row for row in records if row["row_role"] == "placenta_perfusion"]
    printed = [row for row in records if row["row_role"] == "source_reported_summary"]
    by_cell = {(row["row_label"], row["column_index"]): row for row in records}
    if len(individuals) != 36 or len(printed) != 8:
        raise InputError("Table S1 row roles do not form 36 individual and eight summary cells")

    summaries = []
    for column_index in range(1, 5):
        column = str(column_index)
        rows = [by_cell[(f"Placenta {index}", column)] for index in range(1, 10)]
        values = [_decimal(row["value_numeric"], label="Table S1 placenta value") for row in rows]
        mean, sample_sd = _mean_sample_sd(values)
        rounded_mean = mean.quantize(Decimal("0.01"))
        rounded_sd = sample_sd.quantize(Decimal("0.01"))
        mean_row = by_cell[("Mean", column)]
        sd_row = by_cell[("Standard Deviation", column)]
        printed_mean = _decimal(mean_row["value_numeric"], label="Printed Table S1 mean")
        printed_sd = _decimal(sd_row["value_numeric"], label="Printed Table S1 SD")
        if rounded_mean != printed_mean:
            raise InputError(f"Printed Mean differs from the recomputed nine-placenta mean in Table S1 column {column_index}")
        if rounded_sd != printed_sd:
            raise InputError(f"Printed Standard Deviation differs from the recomputed sample SD in Table S1 column {column_index}")
        summaries.append({
            "column_index": column, "source_column_header": HEADERS[column_index - 1],
            "analyte": "antipyrine", "compartment": rows[0]["compartment"],
            "endpoint_kind": rows[0]["endpoint_kind"], "unit": rows[0]["unit"],
            "source_value_lexemes": [row["source_value_lexeme"] for row in rows],
            "arithmetic_mean": _six(mean), "sample_sd": _six(sample_sd),
            "rounded_mean": format(rounded_mean, "f"), "printed_mean_lexeme": mean_row["source_value_lexeme"],
            "rounded_sample_sd": format(rounded_sd, "f"), "printed_sd_lexeme": sd_row["source_value_lexeme"],
            "rounded_summary_matches_printed": True,
        })

    ratio_rows = []
    for index in range(1, 10):
        label = f"Placenta {index}"
        cm = _decimal(by_cell[(label, "1")]["value_numeric"], label="Maternal concentration")
        cf = _decimal(by_cell[(label, "2")]["value_numeric"], label="Fetal concentration")
        ftr = _decimal(by_cell[(label, "3")]["value_numeric"], label="Fetal transfer rate")
        printed_ratio = _decimal(by_cell[(label, "4")]["value_numeric"], label="Printed F/M ratio")
        if not Decimal(0) < ftr < Decimal(100) or cm <= 0 or cf <= 0:
            raise InputError("Table S1 ratio inputs must be positive and FTR must lie between 0 and 100")
        with localcontext() as context:
            context.prec = 50
            recomputed_ratio = (Decimal(100) * cf / cm).quantize(Decimal("0.01"))
            if recomputed_ratio != printed_ratio:
                raise InputError(f"Printed fetal/maternal ratio differs from round(100 * Cf / Cm, 2) at {label}")
            implied_ratio = (ftr / (Decimal(100) - ftr)) * (cm / cf)
            predicted_common = Decimal(100) * cf * Decimal(201) / (cf * Decimal(201) + cm * Decimal(247))
        ratio_rows.append({
            "placenta_label": label,
            "recomputed_fetal_maternal_ratio_percent": format(recomputed_ratio, "f"),
            "printed_fetal_maternal_ratio_lexeme": by_cell[(label, "4")]["source_value_lexeme"],
            "rounded_ratio_matches_printed": True,
            "implied_vf_over_vm": _six(implied_ratio),
            "implied_vf_over_vm_twelve_decimals": format(implied_ratio.quantize(Decimal("0.000000000001")), "f"),
            "common_volume_predicted_ftr_percent": _six(predicted_common),
            "printed_ftr_percent": format(ftr, "f"),
            "common_volume_predicted_minus_printed_ftr_percentage_points": _six(predicted_common - ftr),
        })

    implied = [_decimal(row["implied_vf_over_vm"], label="Rounded implied volume ratio") for row in ratio_rows]
    differences = [_decimal(row["common_volume_predicted_minus_printed_ftr_percentage_points"], label="Common-volume FTR difference") for row in ratio_rows]
    with localcontext() as context:
        context.prec = 50
        mae = sum((abs(value) for value in differences), Decimal(0)) / Decimal(9)
        bias = sum(differences, Decimal(0)) / Decimal(9)
        rmse = (sum((value * value for value in differences), Decimal(0)) / Decimal(9)).sqrt()
        predicted_values = [_decimal(row["common_volume_predicted_ftr_percent"], label="Common-volume FTR") for row in ratio_rows]
        mean_predicted = sum(predicted_values, Decimal(0)) / Decimal(9)
        printed_mean_ftr = sum((_decimal(by_cell[(f"Placenta {index}", "3")]["value_numeric"], label="Printed FTR") for index in range(1, 10)), Decimal(0)) / Decimal(9)
    minimum = min(implied); maximum = max(implied)
    max_difference = max(differences, key=lambda value: abs(value))
    max_index = differences.index(max_difference)
    common = {
        "assumed_vf_ml": 201, "assumed_vm_ml": 247,
        "assumption_status": "counterfactual common-volume substitution; not observed per-placenta volumes",
        "mean_predicted_ftr_percent": _six(mean_predicted),
        "printed_mean_ftr_percent": _six(printed_mean_ftr),
        "mean_predicted_minus_printed_percentage_points": _six(bias),
        "mean_absolute_per_placenta_difference_percentage_points": _six(mae),
        "rmse_per_placenta_difference_percentage_points": _six(rmse),
        "maximum_absolute_difference_percentage_points": _six(abs(max_difference)),
        "maximum_absolute_difference_placenta": max_index + 1,
    }
    diagnostic = manifest.get("summary_and_volume_ratio_diagnostic", {})
    expected_range = diagnostic.get("implied_vf_over_vm_range_six_decimals")
    if expected_range != [format(minimum, "f"), format(maximum, "f")]:
        raise InputError("Manifest implied Vf/Vm range differs from source recomputation")
    if expected_range != ["0.328392", "1.333187"]:
        raise InputError("Pinned implied Vf/Vm range differs from the audited 0.328392 to 1.333187 span")
    if diagnostic.get("implied_vf_over_vm_min_placenta") != implied.index(minimum) + 1 or diagnostic.get("implied_vf_over_vm_max_placenta") != implied.index(maximum) + 1:
        raise InputError("Manifest implied Vf/Vm extrema labels differ from source recomputation")
    expected_common = diagnostic.get("common_mean_volume_sensitivity", {})
    common_matches = {
        "mean_predicted_ftr_percent": "mean_predicted_ftr_percent",
        "printed_mean_ftr_percent": "printed_mean_ftr_percent",
        "mean_predicted_minus_printed_percentage_points": "mean_predicted_minus_printed_percentage_points",
        "mean_absolute_per_placenta_difference_percentage_points": "mean_absolute_per_placenta_difference_percentage_points",
        "rmse_per_placenta_difference_percentage_points": "rmse_per_placenta_difference_percentage_points",
        "maximum_absolute_difference_percentage_points": "maximum_absolute_difference_percentage_points",
        "maximum_absolute_difference_placenta": "maximum_absolute_difference_placenta",
    }
    for manifest_field, computed_field in common_matches.items():
        if _decimal(expected_common.get(manifest_field), label=f"Manifest {manifest_field}") != _decimal(common[computed_field], label=f"Computed {computed_field}"):
            raise InputError(f"Manifest common-volume diagnostic {manifest_field} differs from recomputation")
    return {
        "status": "pass", "scope": "Decimal arithmetic diagnostics on displayed Table S1 values; no volume imputation or transport fit",
        "source_csv_sha256": sha256(csv_raw), "column_summaries": summaries,
        "printed_mean_sd_columns_matched_after_two_decimal_rounding": 4,
        "placenta_diagnostics": ratio_rows, "printed_fetal_maternal_ratios_matched": 9,
        "implied_volume_ratio_formula": "Vf/Vm = (FTR / (100 - FTR)) * (Cm / Cf)",
        "implied_vf_over_vm_range": [format(minimum, "f"), format(maximum, "f")],
        "implied_vf_over_vm_min_placenta": implied.index(minimum) + 1,
        "implied_vf_over_vm_max_placenta": implied.index(maximum) + 1,
        "common_mean_volume_sensitivity": common,
        "per_placenta_volume_records_reported": False,
        "dimensional_transport_fit_assessed": False, "human_source_review_complete": False,
    }


def _normalized(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def _require_snippet(paragraphs: list[str], snippet: str, *, label: str) -> None:
    if sum(snippet in paragraph for paragraph in paragraphs) != 1:
        raise InputError(f"Pinned JATS {label} differs from the audited sentence")


def _candidate_and_inventory(root: Path, manifest_raw: bytes, manifest: dict):
    card_meta = manifest.get("observation_card")
    if not isinstance(card_meta, dict) or card_meta.get("path") != CARD_PATH:
        raise InputError("Dataset manifest does not point to the canonical Ollivier observation card")
    _, card_raw = _load_relative(root, CARD_PATH, label="Observation card", limit=MAX_JSON_BYTES)
    _verify_pin(card_meta, card_raw, label="Observation card")
    card = _json_object(card_raw, label="Observation card")
    inventory_meta = manifest.get("source_inventory")
    if not isinstance(inventory_meta, dict) or inventory_meta.get("path") != INVENTORY_PATH:
        raise InputError("Dataset manifest does not point to the canonical Ollivier source inventory")
    inventory_raw = _read_file(root / INVENTORY_PATH, label="Source inventory", limit=MAX_JSON_BYTES)
    inventory = _json_object(inventory_raw, label="Source inventory")
    manifest_pin = inventory.get("perfusion_manifest")
    if not isinstance(manifest_pin, dict) or manifest_pin.get("path") != "config/perfusion_observations/ollivier_2026_aciclovir_antipyrine_dataset.json":
        raise InputError("Source inventory does not point to the canonical perfusion manifest")
    _verify_pin(manifest_pin, manifest_raw, label="Perfusion manifest")
    if inventory.get("observation_file") != manifest.get("observation_file") or inventory.get("observation_card") != card_meta:
        raise InputError("Source inventory tracked-input pins differ from the perfusion manifest")
    if inventory.get("source_artifacts") != manifest.get("source_artifacts"):
        raise InputError("Source inventory artifact declarations differ from the perfusion manifest")
    artifact_declarations = inventory.get("source_artifacts")
    if (not isinstance(artifact_declarations, list) or len(artifact_declarations) != 5
            or any(not isinstance(artifact, dict) for artifact in artifact_declarations)):
        raise InputError("Source inventory must declare exactly five local primary artifact objects")
    artifact_checks = []
    for artifact in artifact_declarations:
        _, raw = _load_relative(root, artifact.get("local_path"), label=f"Local artifact {artifact.get('artifact_id')}", limit=MAX_ARTIFACT_BYTES)
        _verify_pin(artifact, raw, label=f"Local artifact {artifact.get('artifact_id')}")
        artifact_checks.append({"artifact_id": artifact["artifact_id"], "local_path": artifact["local_path"],
                                "sha256": sha256(raw), "size_bytes": len(raw), "status": "verified"})
    if len(artifact_checks) != 5:
        raise InputError("Source inventory must pin and verify all five local primary artifacts")
    return card, card_raw, inventory, artifact_checks


def audit_ollivier_jats_and_observation_card(repository_root: Path, manifest_path: Path) -> dict:
    """Cross-check pinned JATS text, the 47-record card, pairs, coverage and inventory."""
    root, manifest_raw, manifest = _load_manifest(repository_root, manifest_path)
    audit_ollivier_table_s1(root, manifest_path)
    jats_meta = manifest.get("jats_artifact")
    if not isinstance(jats_meta, dict) or jats_meta.get("artifact_id") != "ollivier2026-jats-xml":
        raise InputError("Dataset manifest does not identify the pinned Ollivier JATS artifact")
    _, jats_raw = _load_relative(root, jats_meta.get("local_path"), label="Source JATS XML", limit=MAX_XML_BYTES)
    _verify_pin(jats_meta, jats_raw, label="Source JATS XML")
    card, card_raw, inventory, artifact_checks = _candidate_and_inventory(root, manifest_raw, manifest)
    validate_dataset(card)
    if card.get("dataset_id") != "ollivier2026-aciclovir-antipyrine-perfusion-candidate":
        raise InputError("Observation card dataset_id differs from the canonical Ollivier candidate")
    artifacts = {item["artifact_id"]: item for item in card.get("artifacts", [])}
    if set(artifacts) != {"ollivier2026-jats-xml", "ollivier2026-table-s1-docx"}:
        raise InputError("Observation card must contain exactly the pinned JATS and Table S1 artifacts")
    if (artifacts["ollivier2026-jats-xml"].get("sha256") != jats_meta.get("sha256")
            or artifacts["ollivier2026-jats-xml"].get("local_path") != jats_meta.get("local_path")
            or artifacts["ollivier2026-table-s1-docx"].get("sha256") != manifest["source_artifact"].get("sha256")
            or artifacts["ollivier2026-table-s1-docx"].get("local_path") != manifest["source_artifact"].get("local_path")):
        raise InputError("Observation card artifact pins differ from the perfusion manifest")

    if b"<!ENTITY" in jats_raw.upper():
        raise InputError("Source JATS entity declarations are unsupported")
    try:
        jats = ET.fromstring(jats_raw)
    except ET.ParseError as exc:
        raise InputError("Source JATS XML is invalid") from exc
    identifiers = {node.get("pub-id-type"): (node.text or "") for node in jats.findall(".//article-meta/article-id")}
    if (identifiers.get("doi") != "10.1111/1471-0528.70168" or identifiers.get("pmid") != "41621825"
            or identifiers.get("pmcid") != "PMC13040426"):
        raise InputError("Pinned JATS bibliographic identifiers differ from Ollivier et al. 2026")
    license_refs = [node.text or "" for node in jats.findall(".//article-meta/permissions/license/*")
                    if node.tag.rsplit("}", 1)[-1] == "license_ref"]
    if not any("creativecommons.org/licenses/by/4.0/" in value for value in license_refs):
        raise InputError("Pinned JATS does not carry the expected CC BY 4.0 license reference")
    table1 = jats.find(".//table-wrap[@id='bjo70168-tbl-0001']")
    if table1 is None:
        raise InputError("Pinned JATS Table 1 is missing")
    table1_rows = [[_normalized(cell) for cell in row] for row in table1.findall(".//tr")]
    if ["Umbilical artery pH", "7.28 (SD: 1.60)"] not in table1_rows:
        raise InputError("Pinned JATS Table 1 umbilical-artery pH 7.28 (SD: 1.60) row differs")
    methods = jats.find(".//sec[@id='bjo70168-sec-0009']")
    results = jats.find(".//sec[@id='bjo70168-sec-0016']")
    if methods is None or results is None:
        raise InputError("Pinned JATS Methods or Results section is missing")
    methods_paragraphs = [_normalized(node) for node in methods.findall(".//p")]
    results_paragraphs = [_normalized(node) for node in results.findall(".//p")]
    method_118_sentences = [sentence for paragraph in methods_paragraphs
                            for sentence in re.split(r"(?<=[.!?])\s+", paragraph) if "118 Da" in sentence]
    if (len(method_118_sentences) != 1
            or sha256(method_118_sentences[0].encode("utf-8")) != METHODS_118_DA_SENTENCE_SHA256):
        raise InputError("Pinned JATS Methods 118 Da sentence differs from the exact audited sentence")
    _require_snippet(methods_paragraphs, "every 10 min for 30 min, then every 20 min for a period of 3 h for 2 placentas, and every 30 min for a period of 3 h for 7 placentas", label="2/7 sampling-cadence sentence")
    _require_snippet(methods_paragraphs, "continued for a period of 5 h for one placenta", label="one-placenta five-hour extension sentence")
    _require_snippet(results_paragraphs, "The mean fetal transfer rate of antipyrine at 3 h was 81% (SD: 6.9%), and the maternal‐to‐fetal concentration ratio of antipyrine at 3 h was 39% (SD: 12.2%) (Table S1).", label="antipyrine metric-swap sentence")
    _require_snippet(results_paragraphs, "At 3 h, the average maternal concentration is 7.55 mg/L (SD: 2.46 mg/L), and the average fetal concentration is 1.85 mg/L (SD: 0.60 mg/L).", label="aciclovir 3-hour concentration sentence")
    _require_snippet(results_paragraphs, "The average fetal transfer rate of aciclovir between the maternal and fetal compartments was 17.4% at 3 h (SD: 7.8%).", label="aciclovir 17.4% FTR sentence")
    _require_snippet(results_paragraphs, "the average volume of the fetal solution at 3 h was 201 mL (SD: 57 mL) and that of the maternal solution was 247 mL (SD: 53 mL)", label="3-hour compartment-volume sentence")
    _require_snippet(results_paragraphs, "The average pH was at the target value of 7.2 (SD: 0.1) in the fetal solution and 7.4 (SD: 0.1) in the maternal solution.", label="perfusion pH summary sentence")
    _require_snippet(results_paragraphs, "The average temperature of the fetal solution was 37.4°C (SD: 0.7°C), and that of the maternal solution was 37.3°C (SD: 0.5°C)", label="perfusion temperature summary sentence")
    _require_snippet(results_paragraphs, "the average fetal pressure was 67.5 mmHg (SD: 30.9 mmHg)", label="fetal arterial pressure summary sentence")
    _require_snippet(results_paragraphs, "Throughout the study, 9 placentas validated the criteria for transplacental transfer of antipyrine.", label="nine-perfusion cohort sentence")
    formula = jats.find(".//disp-formula[@id='bjo70168-disp-0001']")
    if formula is None:
        raise InputError("Pinned JATS FTR formula is missing")
    fraction = formula.find(".//m:mfrac", MATH)
    if fraction is None or len(fraction) != 2:
        raise InputError("Pinned JATS FTR MathML fraction structure differs")
    numerator = "".join(fraction[0].itertext())
    denominator = "".join(fraction[1].itertext())
    if numerator != "100×FC×FV" or denominator != "FC×FV+MC×MV":
        raise InputError("Pinned JATS FTR MathML tokens differ from 100 × FC × FV / FC × FV + MC × MV")

    _, csv_raw = _load_relative(root, manifest["observation_file"]["path"], label="Observation CSV", limit=MAX_CSV_BYTES)
    csv_rows = _csv_records(csv_raw)
    source_by_id = {row["record_id"]: row for row in csv_rows[:36]}
    observations = card.get("observations", [])
    if len(observations) != 47:
        raise InputError("Observation card must contain exactly 47 observations")
    by_id = {row["record_id"]: row for row in observations}
    measured = [row for row in observations if row.get("evidence_status") == "measured"]
    summaries = [row for row in observations if row.get("evidence_status") == "author_reported_summary"]
    if len(measured) != 36 or len(summaries) != 11 or set(by_id) != set(source_by_id) | set(SUMMARY_EXPECTED):
        raise InputError("Observation card must contain 36 measured Table S1 and 11 author-reported summary records")
    for record_id, source_row in source_by_id.items():
        record = by_id[record_id]
        observation = record["observation"]
        column = int(source_row["column_index"])
        if (record["source"]["artifact_id"] != "ollivier2026-table-s1-docx"
                or record["source_locator"] != source_row["source_locator"]
                or record["assay"]["endpoint"] != SPECS[column - 1]["endpoint"]
                or record["assay"]["unit"] != source_row["unit"]
                or _decimal(observation["value"], label=f"{record_id} value") != _decimal(source_row["value_numeric"], label="CSV value")):
            raise InputError(f"Observation value differs from Table S1 or its mapped endpoint at {record_id}")
        if (observation["measurement_time"] != 180 or observation["measurement_time_unit"] != TIME_UNIT
                or observation["replicate_role"] != "independent"
                or record["independent_unit"]["id"] != f"placenta-{source_row['row_index']}"):
            raise InputError(f"Observation time/unit mapping differs from Table S1 at {record_id}")
        qualifications = observation["source_qualifications"]
        decimal_qualifiers = [item for item in qualifications if item["criterion_code"] == "source_decimal_lexeme"]
        if len(decimal_qualifiers) != 1 or source_row["source_value_lexeme"] not in decimal_qualifiers[0]["criterion_label"]:
            raise InputError(f"Observation decimal-comma qualification differs from Table S1 at {record_id}")
        codes = {item["criterion_code"] for item in qualifications}
        if column in (3, 4) and not {"results_table_metric_swap", "per_placenta_volume_records"}.issubset(codes):
            raise InputError(f"FTR/F/M observation must retain metric-swap and missing-volume qualifications at {record_id}")
    for record_id, (mean, sd, unit, measurement_time, literal) in SUMMARY_EXPECTED.items():
        record = by_id[record_id]
        observation = record["observation"]
        statistic = observation.get("summary_statistic", {})
        if (record["source"]["artifact_id"] != "ollivier2026-jats-xml" or observation["replicate_role"] != "summary_only"
                or observation["value"] != mean or observation["measurement_time"] != measurement_time
                or record["assay"]["unit"] != unit or statistic.get("kind") != "mean_sd"
                or statistic.get("mean") != mean or statistic.get("standard_deviation") != sd
                or statistic.get("reported_sample_size") != 9 or statistic.get("source_literal") != literal):
            raise InputError(f"Author-reported summary differs from pinned JATS metadata at {record_id}")
    baseline_codes = {item["criterion_code"] for item in by_id["ollivier2026-table1-umbilical-artery-ph"]["observation"]["source_qualifications"]}
    if "printed_summary_anomaly" not in baseline_codes:
        raise InputError("Table 1 umbilical-artery pH summary must retain its printed-SD anomaly qualification")

    pairs = card.get("measurement_pairs", [])
    if len(pairs) != 9:
        raise InputError("Observation card must contain exactly nine maternal/fetal concentration pairs")
    for index, pair in enumerate(pairs, 1):
        if (pair["pair_id"] != f"ollivier2026-placenta-{index}-antipyrine-concentration-pair"
                or pair["pair_type"] != "same_unit_same_time" or pair["linkage_basis"] != "source_explicit"
                or [member["record_id"] for member in pair["members"]] != [f"ollivier2026-table-s1-r{index:02d}-c01", f"ollivier2026-table-s1-r{index:02d}-c02"]):
            raise InputError(f"Measurement pair mapping differs from Table S1 at Placenta {index}")
    coverage = {row["coverage_id"]: row for row in card.get("cohort_coverage", [])}
    expected_coverage = {"ollivier2026-validated-perfusion-coverage", "ollivier2026-sampling-cadence-coverage", "ollivier2026-five-hour-extension-coverage"}
    if set(coverage) != expected_coverage:
        raise InputError("Observation card cohort-coverage IDs differ from the three required source frames")
    coverage_checks = {coverage_id: _coverage_closure(row) for coverage_id, row in coverage.items()}
    expected_status = {"ollivier2026-validated-perfusion-coverage": "not_assessed", "ollivier2026-sampling-cadence-coverage": "matches", "ollivier2026-five-hour-extension-coverage": "not_assessed"}
    if {key: value["status"] for key, value in coverage_checks.items()} != expected_status:
        raise InputError("Observation card cohort count-closure statuses differ from the declared source coverage")
    cadence = coverage["ollivier2026-sampling-cadence-coverage"]
    if [item["value"] for item in cadence["declarations"]] != [2, 7] or cadence["denominator"]["value"] != 9:
        raise InputError("Sampling-cadence coverage must preserve the 2/7 partition within nine perfusions")
    extension = coverage["ollivier2026-five-hour-extension-coverage"]
    if extension["declarations"][0]["value"] != 1 or extension["denominator"]["value"] != 9:
        raise InputError("Five-hour coverage must preserve one extended perfusion within the nine-placenta cohort")
    return {
        "status": "pass", "scope": "pinned JATS source text, MathML, observation card, pairs, cohort coverage and local artifact/inventory pins",
        "source_jats_sha256": sha256(jats_raw), "source_jats_size_bytes": len(jats_raw),
        "observation_card_sha256": sha256(card_raw), "observation_card_size_bytes": len(card_raw),
        "observation_records_reconciled": 47, "measured_antipyrine_records": 36,
        "author_reported_summary_records": 11, "mean_sd_reported_sample_size": 9,
        "measurement_pairs_reconciled": 9, "cohort_coverage_records": 3,
        "cohort_coverage_checks": coverage_checks,
        "table1_umbilical_artery_ph_literal": "7.28 (SD: 1.60)",
        "methods_antipyrine_molecular_weight_da": 118,
        "ftr_mathml_numerator_tokens": "100 × FC × FV", "ftr_mathml_denominator_tokens": "FC × FV + MC × MV",
        "results_table_s1_metric_swap_preserved": True, "printed_table1_sd_anomaly_preserved": True,
        "local_artifacts": artifact_checks, "local_artifacts_verified": len(artifact_checks),
        "inventory": INVENTORY_PATH, "figure_digitized": False,
        "dimensional_transport_fit_assessed": False, "human_source_review_complete": False,
    }
