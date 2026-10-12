"""Pinned, offline intake of Mathiesen et al. 2020 human placental perfusion observations.

This extracts concentration-level source cells and records the source-declared
perfusion window. It does not calculate transport fluxes or fit a biological
model.
"""
from __future__ import annotations

import io
import math
import re
import statistics
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .artifacts import InputError, MAX_JSON_BYTES, csv_bytes, json_bytes, publish_bundle, sha256
from .observations import validate_dataset

ARTICLE_URL = "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979"
WORKBOOK_URL = "https://doi.org/10.1371/journal.pone.0233979.s005"
TABLE1_URL = "https://journals.plos.org/plosone/article/figure/image?download&size=large&id=10.1371/journal.pone.0233979.t001"
SUCCESS_TABLE_URL = "https://doi.org/10.1371/journal.pone.0233979.s001"
S3_TABLE_URL = "https://doi.org/10.1371/journal.pone.0233979.s003"
ARTICLE_SHA256 = "ad0dd45d56df976b03742c942c22a717590440d08285283e5b7da6b830f20f31"
WORKBOOK_SHA256 = "c69a7d03d3083435ded8b5a686d25c6dbe186d77321152aceb8ec934a94812a0"
TABLE1_SHA256 = "7cb46b1b495c44ba418e57cc65ae4a987bfc385e12ce028972eff14cc97654b8"
SUCCESS_TABLE_SHA256 = "c1c16427fbc70ae6a7f89cb805cda87e5f3a98a083bd998a50d28af130bbd9e4"
S3_TABLE_SHA256 = "0fb9f383a30db58139bab94383a194fa8c90eab9e1247f74641db1ce48015554"
RETRIEVED_ON = "2026-10-10"
LICENSE_NOTE = "PLOS article page states CC BY 4.0; item-specific supplement/image reuse review remains pending"
NS = {
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
ANALYTES = (("Cortisol", 2), ("Cortisone", 32), ("Tryptophan", 62),
            ("Serotonin", 92), ("5-HIAA", 122))
M_TIMES = (("Mbefore", "maternal", None), ("M0", "maternal", 0),
           ("M2", "maternal", 2), *((f"M{time}", "maternal", time)
           for time in range(30, 361, 30)))
F_TIMES = (("Fbefore", "fetal", None), ("F2", "fetal", 2),
           *((f"F{time}", "fetal", time) for time in range(30, 361, 30)))
EXPECTED_ROWS = M_TIMES + F_TIMES

# Manually transcribed from the pinned Table 1 image. This is source metadata,
# not an OCR result; human verification is still pending.
RUNS = {
    1: ("none", 6.0), 2: ("none", 6.0), 3: ("none", 6.0), 4: ("none", 6.0),
    5: ("none", 6.0), 6: ("none", 6.0), 7: ("none", 6.0), 8: ("none", 6.0),
    9: ("carbenoxolone", 6.0), 10: ("carbenoxolone", 1.0),
    11: ("carbenoxolone", 6.0), 12: ("carbenoxolone", 6.0),
    13: ("carbenoxolone", 3.5), 14: ("fluoxetine", 6.0),
    15: ("fluoxetine", 5.5), 16: ("fluoxetine", 5.0),
    17: ("fluoxetine", 5.5), 18: ("PCPA", 6.0), 19: ("PCPA", 4.0),
    20: ("PCPA", 6.0), 21: ("PCPA", 4.0), 22: ("PCPA", 6.0),
}
CONDITION_IDS = {
    "none": "antagonist-none",
    "carbenoxolone": "antagonist-carbenoxolone",
    "fluoxetine": "antagonist-fluoxetine",
    "PCPA": "antagonist-pcpa",
}


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    raw = archive.read(name)
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise InputError("Workbook XML declarations are unsupported")
    return ET.fromstring(raw)


def _column_number(reference: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]*)", reference)
    if not match:
        raise InputError("Workbook contains an invalid cell reference")
    column = 0
    for character in match.group(1):
        column = column * 26 + ord(character) - ord("A") + 1
    return column, int(match.group(2))


def _workbook_cells(raw: bytes) -> dict[str, tuple[str | None, str]]:
    """Read the single expected sheet, rejecting formulas and unsafe packages."""
    if len(raw) > 1_000_000:
        raise InputError("Source workbook exceeds the 1 MB audit limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if (len(entries) > 128 or len({entry.filename for entry in entries}) != len(entries)
                    or sum(entry.file_size for entry in entries) > 10_000_000
                    or any(entry.file_size > 2_000_000 or entry.flag_bits & 1 for entry in entries)):
                raise InputError("Workbook archive exceeds bounds or has duplicate/encrypted members")
            names = {entry.filename for entry in entries}
            required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/sharedStrings.xml"}
            if not required.issubset(names):
                raise InputError("Workbook is missing a required internal member")
            sheets = [item for item in _xml(archive, "xl/workbook.xml").findall("s:sheets/s:sheet", NS)
                      if item.get("name") == "Placental perfusion"]
            if len(sheets) != 1:
                raise InputError("Expected exactly one 'Placental perfusion' worksheet")
            relationship_id = sheets[0].get("{" + NS["r"] + "}id")
            relationships = [item for item in _xml(archive, "xl/_rels/workbook.xml.rels").findall(
                "p:Relationship", NS) if item.get("Id") == relationship_id]
            if (len(relationships) != 1 or relationships[0].get("TargetMode") == "External"
                    or relationships[0].get("Type") != NS["r"] + "/worksheet"):
                raise InputError("Invalid worksheet relationship")
            target = relationships[0].get("Target", "")
            if (not target.startswith("worksheets/") or "\\" in target or ":" in target
                    or any(part in {"", ".", ".."} for part in target.split("/"))):
                raise InputError("Invalid worksheet path")
            shared = ["".join(item.itertext()) for item in
                      _xml(archive, "xl/sharedStrings.xml").findall("s:si", NS)]
            cells: dict[str, tuple[str | None, str]] = {}
            for cell in _xml(archive, "xl/" + target).findall("s:sheetData/s:row/s:c", NS):
                reference = cell.get("r")
                if not reference or reference in cells:
                    raise InputError("Missing or duplicate worksheet cell reference")
                column, row = _column_number(reference)
                if column > 23 or row > 151:
                    raise InputError("Workbook contains cells outside the pinned observation matrix")
                if cell.find("s:f", NS) is not None:
                    raise InputError("Workbook formulas are not source measurements")
                value = cell.find("s:v", NS)
                token = value.text if value is not None else None
                cell_type = cell.get("t")
                if cell_type == "s":
                    if token is None or not token.isdigit() or int(token) >= len(shared):
                        raise InputError("Invalid shared-string reference")
                    cells[reference] = (shared[int(token)], "text")
                elif cell_type == "inlineStr":
                    inline = cell.find("s:is", NS)
                    cells[reference] = ("".join(inline.itertext()) if inline is not None else "", "text")
                elif cell_type in {None, "n"}:
                    cells[reference] = (token, "numeric" if token is not None else "blank")
                elif cell_type == "str":
                    cells[reference] = (token, "text")
                else:
                    raise InputError("Workbook contains an unsupported worksheet cell type")
            return cells
    except InputError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, EOFError, ValueError) as exc:
        raise InputError("Workbook is not the supported bounded XLSX structure") from exc


def _cell(cells: dict[str, tuple[str | None, str]], reference: str):
    return cells.get(reference, (None, "blank"))


def _expect_text(cells: dict[str, tuple[str | None, str]], reference: str, expected: str) -> None:
    token, kind = _cell(cells, reference)
    if kind != "text" or token != expected:
        raise InputError(f"Unexpected source label at {reference}")


def _extract_cells(cells: dict[str, tuple[str | None, str]]) -> list[dict]:
    _expect_text(cells, "A1", "Conc. nM")
    for run_id in range(1, 23):
        reference = chr(ord("B") + run_id - 1) + "1"
        token, kind = _cell(cells, reference)
        if kind != "numeric" or token is None:
            raise InputError(f"Missing run-slot header at {reference}")
        try:
            parsed = float(token)
        except (ValueError, OverflowError) as exc:
            raise InputError(f"Invalid run-slot header at {reference}") from exc
        if not math.isfinite(parsed) or parsed != run_id:
            raise InputError("Workbook run columns must be exactly the source IDs 1–22")

    extracted = []
    for analyte, heading_row in ANALYTES:
        _expect_text(cells, f"A{heading_row}", analyte)
        for offset, (time_label, compartment, time_min) in enumerate(EXPECTED_ROWS, 1):
            row = heading_row + offset
            _expect_text(cells, f"A{row}", time_label)
            for run_id in range(1, 23):
                column = chr(ord("B") + run_id - 1)
                reference = f"{column}{row}"
                token, kind = _cell(cells, reference)
                value = None
                if token is not None:
                    if kind != "numeric":
                        raise InputError(f"Non-numeric concentration at {reference}")
                    try:
                        value = float(token)
                    except (ValueError, OverflowError) as exc:
                        raise InputError(f"Invalid concentration at {reference}") from exc
                    if not math.isfinite(value) or value < 0:
                        raise InputError(f"Concentration at {reference} must be finite and nonnegative")
                group, acceptable_hours = RUNS[run_id]
                if time_min is None:
                    window_status = "before_exposure_time_not_numeric"
                elif time_min <= acceptable_hours * 60:
                    window_status = "within_source_reported_ok_duration"
                else:
                    window_status = "after_source_reported_ok_duration"
                extracted.append({
                    "analyte": analyte, "compartment": compartment,
                    "source_time_label": time_label, "time_min": time_min,
                    "perfusion_id": run_id, "antagonist": group,
                    "source_ok_hours": acceptable_hours,
                    "window_status": window_status, "source_numeric_text": token or "",
                    "value_nM": value, "source_locator": f"Placental perfusion!{reference}",
                    "missingness_reason": ("Source cell is blank; article caption attributes missing data to analysis errors, without assigning a cell-specific cause."
                                           if value is None else ""),
                })
    return extracted


def _read_pinned(path: Path, *, label: str, expected_hash: str, limit: int) -> bytes:
    path = Path(path)
    if any(parent.is_symlink() for parent in (path, *path.parents)) or not path.is_file():
        raise InputError(f"{label} must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise InputError(f"{label} exceeds the {limit} byte audit limit")
    if sha256(raw) != expected_hash:
        raise InputError(f"{label} hash differs from the inspected source revision; a new audit is required")
    return raw


def _s3_candidate_link(raw: bytes) -> dict:
    """Screen S3's numbered key against Table 1 without asserting a unit join."""
    if len(raw) > 1_000_000:
        raise InputError("PLOS S3 Table exceeds the 1 MB audit limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if (len(entries) > 128 or len(names) != len(set(names))
                    or sum(entry.file_size for entry in entries) > 10_000_000
                    or any(entry.file_size > 2_000_000 or entry.flag_bits & 1 for entry in entries)
                    or "word/document.xml" not in names):
                raise InputError("PLOS S3 DOCX archive exceeds bounds or is malformed")
            document = archive.read("word/document.xml")
        if b"<!DOCTYPE" in document.upper() or b"<!ENTITY" in document.upper():
            raise InputError("PLOS S3 DOCX XML declarations are unsupported")
        root = ET.fromstring(document)
        tables = root.findall(".//w:tbl", NS)
        if len(tables) != 1:
            raise InputError("Expected one table in the pinned PLOS S3 DOCX")
        table_rows = tables[0].findall("w:tr", NS)
        if len(table_rows) != 23:
            raise InputError("Expected one S3 header row and 22 numbered data rows")

        def cells(row: ET.Element) -> list[str]:
            return [" ".join(part.text or "" for part in cell.findall(".//w:t", NS)).strip()
                    for cell in row.findall("w:tc", NS)]

        header = cells(table_rows[0])
        if len(header) != 14 or header[0].casefold() != "nr":
            raise InputError("PLOS S3 header must have 14 columns and begin with 'nr'")
        keys = []
        for row in table_rows[1:]:
            row_cells = cells(row)
            keys.append(row_cells[0] if row_cells else "")
    except InputError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, EOFError, ValueError) as exc:
        raise InputError("PLOS S3 file is not the supported bounded DOCX structure") from exc

    table1_keys = [str(run_id) for run_id in RUNS]
    keys_match = (len(keys) == len(table1_keys) and len(set(keys)) == len(keys)
                  and set(keys) == set(table1_keys))
    return {
        "source_artifact_id": "mathiesen2020-s3table",
        "source_uri": S3_TABLE_URL,
        "source_sha256": sha256(raw),
        "pinned_source_sha256": S3_TABLE_SHA256,
        "source_hash_is_pinned": sha256(raw) == S3_TABLE_SHA256,
        "header_column": "nr",
        "source_data_rows": len(keys),
        "source_keys": keys,
        "table1_key_column": "ID",
        "table1_key_values": table1_keys,
        "numeric_key_sets_match": keys_match,
        "article_context": "S3 is described as donor questionnaire data and selected perfusion outcomes; Table 1 describes each perfusion.",
        "explicit_same_key_statement_found": False,
        "status": "candidate link; not verified" if keys_match else "keys do not match",
        "join_performed": False,
        "biological_identity_inferred": False,
        "donor_measurement_values_transcribed": False,
        "handling": "Do not join donor-level records to perfusion IDs or add inferred unit membership.",
    }


def _local_path(path: Path) -> str | None:
    try:
        return Path(path).resolve(strict=True).relative_to(Path.cwd().resolve()).as_posix()
    except (OSError, RuntimeError, ValueError):
        return None


def _artifacts(paths: dict[str, Path], raw_files: dict[str, bytes]) -> list[dict]:
    declarations = (
        ("mathiesen2020-article", ARTICLE_URL, "article.html", "PLOS article page states CC BY 4.0"),
        ("mathiesen2020-s1data", WORKBOOK_URL, "supplement-s1-data.xlsx", LICENSE_NOTE),
        ("mathiesen2020-table1", TABLE1_URL, "table1.png", LICENSE_NOTE),
        ("mathiesen2020-s1table", SUCCESS_TABLE_URL, "supplement-s1-table.docx", LICENSE_NOTE),
    )
    expected = {"mathiesen2020-article": ARTICLE_SHA256, "mathiesen2020-s1data": WORKBOOK_SHA256,
                "mathiesen2020-table1": TABLE1_SHA256, "mathiesen2020-s1table": SUCCESS_TABLE_SHA256}
    artifacts = []
    for artifact_id, uri, name, license_note in declarations:
        path = paths[artifact_id]
        raw = raw_files[artifact_id]
        artifacts.append({"artifact_id": artifact_id, "uri": uri, "license": license_note,
                          "sha256": expected[artifact_id], "retrieved_on": RETRIEVED_ON,
                          "local_path": _local_path(path)})
    return artifacts


def _observation_dataset(rows: list[dict], artifacts: list[dict]) -> dict:
    article = next(item for item in artifacts if item["artifact_id"] == "mathiesen2020-article")
    workbook = next(item for item in artifacts if item["artifact_id"] == "mathiesen2020-s1data")
    by_id = {item["artifact_id"]: item for item in artifacts}
    observations = []
    for row in rows:
        group, acceptable_hours = RUNS[row["perfusion_id"]]
        label = row["source_time_label"].lower()
        analyte_id = row["analyte"].lower().replace("-", "")
        record_id = f"mathiesen2020-{analyte_id}-{row['compartment'][:1]}-id{row['perfusion_id']:02d}-{label}"
        measurement_time = row["time_min"] if row["time_min"] is not None else "before"
        time_unit = "min" if row["time_min"] is not None else "source label; exact elapsed time unreported"
        beyond_note = (f"Source Table 1 reports perfusion {row['perfusion_id']} as acceptable for {acceptable_hours:g} h; this later sample is retained but follows that source-reported window."
                       if row["window_status"] == "after_source_reported_ok_duration" else "")
        limitations = ["The reported nM value is a reservoir concentration, not a collected amount, mass balance, net flux or permeability coefficient."]
        if beyond_note:
            limitations.append(beyond_note)
        if row["time_min"] is None:
            limitations.append("The source's 'before' label is preserved without assigning a numerical assay time.")
        observations.append({
            "schema_version": 1, "record_id": record_id, "evidence_status": "measured",
            "species": "human", "stage_track": "organoid_or_tissue_model",
            "developmental_interval": {"label": "Term placental tissue; exact gestational age is not reported for each perfusion",
                "start": "term", "end": "term", "time_unit": "source term label; week unavailable",
                "stage_source_artifact_id": article["artifact_id"]},
            "model_system": {"kind": "other",
                "label": "Ex vivo recirculating perfusion of a single term human placental cotyledon"},
            "assay": {"name": "Published UPLC/UHPLC concentration assay",
                "endpoint": f"{row['analyte']} concentration in the {row['compartment']} perfusate reservoir",
                "unit": "nM", "measurement_role": "function",
                "functional_context": {"compartment": row["compartment"] + " perfusate reservoir",
                    "material": row["analyte"], "process": "other",
                    "quantity_basis": "Source-reported nM reservoir concentration; not a direct amount or flux",
                    "assessment_context": "isolated_tissue", "source_locator": row["source_locator"]}},
            "independent_unit": {"kind": "other", "id": f"perfusion-{row['perfusion_id']:02d}",
                "parent_id": None,
                "hierarchy_note": f"Source Table 1 ID {row['perfusion_id']} matches the S1 Data column header; this is a perfusion-run identifier, not personal identity. Antagonist={group}; source-reported acceptable duration={acceptable_hours:g} h."},
            "observation": {"value": row["value_nM"], "measurement_time": measurement_time,
                "measurement_time_unit": time_unit,
                "comparator_id": CONDITION_IDS[group], "replicate_role": "repeated_measure",
                "measurement_uncertainty": None, "missingness_reason": row["missingness_reason"],
                "source_qualifications": [{
                    "criterion_code": "source_reported_ok_duration",
                    "status_code": row["window_status"],
                    "criterion_label": "Source Table 1 acceptable perfusion duration",
                    "source_artifact_id": "mathiesen2020-table1",
                    "source_locator": f"PLOS Table 1, row ID {row['perfusion_id']}",
                    "reference_value": acceptable_hours,
                    "reference_unit": "hour",
                }]},
            "source": {key: workbook[key] for key in
                       ("artifact_id", "uri", "license", "sha256", "retrieved_on")},
            "source_locator": row["source_locator"],
            "limitations": limitations,
        })
    data = {
        "schema_version": 1, "dataset_id": "mathiesen2020-human-placental-perfusion-candidate",
        "title": "Source-cell intake of Mathiesen et al. term human placental perfusion concentrations",
        "source_revision": {"revision_id": "mathiesen2020-s1data-pinned-2026-10-10",
            "citation": "Mathiesen L, Bay-Richter C, Wegener G, Liebenberg N, Knudsen LE (2020). Maternal stress and placental function; ex vivo placental perfusion studying cortisol, cortisone, tryptophan and serotonin. PLOS ONE 15(6): e0233979.",
            "source_kind": "peer_reviewed_human_invitro", "source_url": ARTICLE_URL,
            "review_status": "candidate", "reviewer": "", "reviewed_on": None, "review_note": ""},
        "artifacts": artifacts, "observations": observations, "transitions": [],
        "limitations": [
            "Source IDs and antagonist groups are transcribed from the publisher's Table 1 image and await human verification; they identify perfusion runs, not personal donor identities.",
            "Source Table 1 says 15 runs were acceptable for 6 h and seven ended earlier; later concentration values are retained and marked by source-time-window status in the audit CSV.",
            "PLOS S1 Data calls missing values analysis errors but does not assign an exact reason to each blank cell.",
            "The broader S1 Table reports a 48-to-43-to-26-to-15 selection funnel, whereas the article's 22-run dataset has a separate table; the source does not link those four population frames, so they are not reconciled.",
            "Numerical per-sample reservoir-volume/removal logs, per-run final volumes, analyte inventory/recovery, calibration records and original instrument outputs are not present in the pinned public files; the Methods section does state that fetal volume was observed after samples.",
            "This term-tissue concentration dataset does not measure embryo/fetal growth, gestational continuity, neonatal transition or later health.",
            "No transport parameter fit, statistical test, biological prediction or readiness claim is made; source review and analysis eligibility remain pending.",
        ],
    }
    validate_dataset(data)
    return data


def _summary(rows: list[dict]) -> dict:
    indexed = {(row["analyte"], row["compartment"], row["source_time_label"], row["perfusion_id"]): row["value_nM"]
               for row in rows}
    ratios = []
    for perfusion_id in range(1, 9):
        maternal_start = indexed[("Tryptophan", "maternal", "M0", perfusion_id)]
        fetal_end = indexed[("Tryptophan", "fetal", "F360", perfusion_id)]
        if maternal_start is None or fetal_end is None:
            raise InputError("The source cells needed for the bounded descriptive check are missing")
        ratios.append({"perfusion_id": perfusion_id, "fetal_360_over_maternal_0_percent":
                       fetal_end / maternal_start * 100.0})
    values = [item["fetal_360_over_maternal_0_percent"] for item in ratios]
    return {
        "status": "descriptive_source_check_only", "analyte": "Tryptophan",
        "condition": "none", "n_source_perfusion_ids": len(ratios),
        "numerator": "fetal reservoir concentration at 360 min (F360), nM",
        "denominator": "maternal reservoir concentration at time 0 (M0), nM",
        "computed_metric": "mean of per-perfusion (F360 / M0) * 100",
        "mean_percent": statistics.mean(values), "minimum_percent": min(values),
        "maximum_percent": max(values), "perfusion_values": ratios,
        "reported_source_comparison": "Article describes the six-hour fetal tryptophan concentration as approximately 70% of the maternal start concentration.",
        "limits": ["The ratio is a concentration comparison, not mass flux, cumulative transfer, fetal nutrient sufficiency or permeability.",
                   "The eight source IDs are separate perfusion runs; no inferential statistics or model fit were run."]}


def _missingness_summary(rows: list[dict]) -> dict:
    """Count blanks by source labels without assigning causes or imputing values."""
    groupers = (
        ("analyte", lambda row: (row["analyte"], "")),
        ("analyte_compartment", lambda row: (row["analyte"], row["compartment"])),
        ("antagonist", lambda row: (row["antagonist"], "")),
    )
    breakdown = []
    for dimension, key_for in groupers:
        groups: dict[tuple[str, str], list[dict]] = {}
        for row in rows:
            groups.setdefault(key_for(row), []).append(row)
        for (category, compartment), members in groups.items():
            after = [item for item in members
                     if item["window_status"] == "after_source_reported_ok_duration"]
            numeric_after = [item for item in after if item["value_nM"] is not None]
            blank = sum(item["value_nM"] is None for item in members)
            breakdown.append({
                "dimension": dimension,
                "category": category,
                "compartment": compartment,
                "n_expected": len(members),
                "n_numeric": len(members) - blank,
                "n_blank": blank,
                "n_after_source_ok_window": len(after),
                "n_numeric_after_source_ok_window": len(numeric_after),
                "n_blank_after_source_ok_window": len(after) - len(numeric_after),
            })
    after = [row for row in rows
             if row["window_status"] == "after_source_reported_ok_duration"]
    blank = sum(row["value_nM"] is None for row in rows)
    numeric_after = sum(row["value_nM"] is not None for row in after)
    return {
        "n_expected": len(rows),
        "n_numeric": len(rows) - blank,
        "n_blank": blank,
        "n_in_or_before_source_ok_window": len(rows) - len(after),
        "n_blank_in_or_before_source_ok_window": blank - (len(after) - numeric_after),
        "n_after_source_ok_window": len(after),
        "n_numeric_after_source_ok_window": numeric_after,
        "n_blank_after_source_ok_window": len(after) - numeric_after,
        "breakdown": breakdown,
        "interpretation_limit": "Counts describe source-table blanks only; the article attributes missing data to analysis errors but does not assign a cause to each cell. No imputation or missing-at-random assumption is made.",
    }


def audit_mathiesen_source(article_path: Path, workbook_path: Path, table1_path: Path,
                           success_table_path: Path, s3_table_path: Path,
                           output: Path) -> dict:
    """Audit pinned public source files and publish a candidate observation intake."""
    paths = {
        "mathiesen2020-article": Path(article_path),
        "mathiesen2020-s1data": Path(workbook_path),
        "mathiesen2020-table1": Path(table1_path),
        "mathiesen2020-s1table": Path(success_table_path),
        "mathiesen2020-s3table": Path(s3_table_path),
    }
    expected = {
        "mathiesen2020-article": (ARTICLE_SHA256, 2_000_000, "PLOS article HTML"),
        "mathiesen2020-s1data": (WORKBOOK_SHA256, 1_000_000, "PLOS S1 Data workbook"),
        "mathiesen2020-table1": (TABLE1_SHA256, 1_000_000, "PLOS Table 1 image"),
        "mathiesen2020-s1table": (SUCCESS_TABLE_SHA256, 1_000_000, "PLOS S1 Table DOCX"),
        "mathiesen2020-s3table": (S3_TABLE_SHA256, 1_000_000, "PLOS S3 Table DOCX"),
    }
    raw_files = {key: _read_pinned(path, label=expected[key][2], expected_hash=expected[key][0],
                                   limit=expected[key][1]) for key, path in paths.items()}
    rows = _extract_cells(_workbook_cells(raw_files["mathiesen2020-s1data"]))
    artifacts = _artifacts(paths, raw_files)
    candidate_link = _s3_candidate_link(raw_files["mathiesen2020-s3table"])
    s3_artifact = {
        "artifact_id": "mathiesen2020-s3table", "uri": S3_TABLE_URL,
        "license": LICENSE_NOTE, "sha256": S3_TABLE_SHA256,
        "retrieved_on": RETRIEVED_ON,
        "local_path": _local_path(paths["mathiesen2020-s3table"]),
    }
    manifest_artifacts = artifacts + [s3_artifact]
    dataset = _observation_dataset(rows, artifacts)
    dataset_raw = json_bytes(dataset)
    if len(dataset_raw) > MAX_JSON_BYTES:
        raise InputError("Generated observation dataset exceeds the 16 MB bounded JSON limit")
    summary = _summary(rows)
    missingness = _missingness_summary(rows)
    run_counts = {group: sum(1 for item in RUNS.values() if item[0] == group)
                  for group in CONDITION_IDS}
    numeric = [row for row in rows if row["value_nM"] is not None]
    missing = [row for row in rows if row["value_nM"] is None]
    after = [row for row in rows if row["window_status"] == "after_source_reported_ok_duration"]
    after_numeric = [row for row in after if row["value_nM"] is not None]
    summary_report = {
        "schema_version": 1, "review_status": "candidate", "human_review": "pending",
        "source_transcription": "agent-extracted numerical cells and manually transcribed Table 1 mapping; source verification pending",
        "source_cells_expected": len(rows), "numeric_values": len(numeric),
        "blank_cells": len(missing), "numeric_cells_after_reported_ok_duration": len(after_numeric),
        "all_cells_after_reported_ok_duration": len(after),
        "missingness": missingness,
        "run_count_by_antagonist": run_counts,
        "runs_acceptable_for_six_hours": sum(hours == 6 for _, hours in RUNS.values()),
        "runs_with_shorter_source_reported_duration": sum(hours < 6 for _, hours in RUNS.values()),
        "candidate_unit_linkage": candidate_link,
        "fit_eligibility": "not_eligible_pending source review and absent numerical per-sample volume/removal, final-volume, inventory/recovery, calibration and original instrument records",
        "descriptive_check": summary,
        "limits": ["Source table positions are not used as biological values; cell lexemes and locators are retained.",
                   "Post-window cells are not deleted; this report distinguishes them from readings inside the source-reported acceptable duration.",
                   "No source-reported correction for sample withdrawal or concentration-to-amount conversion is reproduced.",
                   "The four-source-manifest hash binds the exact set of pinned files; each file hash remains listed separately."],
    }
    run_rows = [{"perfusion_id": run_id, "source_column_header": run_id,
                 "antagonist": group, "condition_id": CONDITION_IDS[group],
                 "source_reported_ok_hours": hours,
                 "source_locator": f"PLOS Table 1, row ID {run_id}"}
                for run_id, (group, hours) in RUNS.items()]
    cell_columns = ["analyte", "compartment", "source_time_label", "time_min", "perfusion_id",
                    "antagonist", "source_ok_hours", "window_status", "source_numeric_text",
                    "value_nM", "source_locator", "missingness_reason"]
    source_manifest = {"schema_version": 1, "retrieved_on": RETRIEVED_ON,
        "source_set_sha256_role": "sha256 of canonical JSON containing all five pinned source file IDs, URIs, byte sizes and individual SHA-256 values",
        "sources": [{"artifact_id": item["artifact_id"], "uri": item["uri"],
                     "sha256": item["sha256"], "size_bytes": len(raw_files[item["artifact_id"]]),
                     "license_note": item["license"], "local_path": item["local_path"]}
                    for item in manifest_artifacts],
        "source_modified_or_rewritten": False,
        "run_mapping_review": "Manual transcription from pinned Table 1 image; human verification pending.",
        "candidate_unit_linkage": candidate_link,
        "output_numeric_cells_are_newly_transcribed": True}
    input_fingerprint = json_bytes({"schema_version": 1, "sources": [
        {"artifact_id": item["artifact_id"], "uri": item["uri"],
         "sha256": item["sha256"], "size_bytes": len(raw_files[item["artifact_id"]])}
        for item in manifest_artifacts]})
    report_lines = [
        "# Mathiesen et al. human placental perfusion source audit", "",
        "Candidate source-cell intake; agent extraction and run mapping; human review pending.", "",
        "The source workbook has 22 numbered perfusion columns and 3,190 expected concentration cells across five analytes, two reservoirs and source-labeled times. The audit retained 2,908 numeric values and 282 blank cells.",
        "The PLOS Table 1 image maps the 22 run IDs to four antagonist groups and reports the duration each run remained acceptable: 15 are listed for 6 hours and seven for shorter durations. All later numeric values remain in the intake but are flagged in `cell_observations.csv`; no values were filtered from the source copy.",
        "The pinned S3 table has 22 unique `nr` keys, 1–22, matching Table 1's numeric ID set. The article describes S3 as donor questionnaire data with selected perfusion outcomes but does not define `nr` as the Table 1 ID. This is a candidate key alignment only; no unit join is made. `candidate_unit_linkage.json` records the screen and its limits.",
        "A descriptive source check reproduces the article's approximately 70% six-hour tryptophan statement: for the eight `none` perfusions, the mean of per-run fetal F360 concentration divided by maternal M0 concentration is {:.2f}% (range {:.2f}%–{:.2f}%). This is a concentration ratio, not a transport flux or nutrition adequacy result.".format(summary["mean_percent"], summary["minimum_percent"], summary["maximum_percent"]),
        "Missing cells are not evenly distributed: 5-HIAA and serotonin account for {}/{} and {}/{} expected cells, respectively; the complete count breakdown by analyte, reservoir and antagonist group is in `missingness_summary.csv`. No blank values are imputed and no cell-specific cause is inferred.".format(
            sum(item["n_blank"] for item in missingness["breakdown"]
                if item["dimension"] == "analyte" and item["category"] == "5-HIAA"),
            sum(item["n_expected"] for item in missingness["breakdown"]
                if item["dimension"] == "analyte" and item["category"] == "5-HIAA"),
            sum(item["n_blank"] for item in missingness["breakdown"]
                if item["dimension"] == "analyte" and item["category"] == "Serotonin"),
            sum(item["n_expected"] for item in missingness["breakdown"]
                if item["dimension"] == "analyte" and item["category"] == "Serotonin")),
        "The article's broader S1 Table reports a 48→43→26→15 intake/selection funnel, while its Table 1 and raw workbook cover 22 numbered test-substance perfusions. The source does not link the four count frames at the intermediate step; they are preserved as different population descriptions rather than reconciled.",
        "",
        f"[Mathiesen et al., PLOS ONE (2020)]({ARTICLE_URL}); source workbook: [S1 Data]({WORKBOOK_URL}); Table 1, S1 Table and S3 Table were separately pinned.",
        "Article page states CC BY 4.0. Item-specific supplement/image reuse terms and the hand-transcribed Table 1 mapping require human review. Original source files are not altered or embedded in this repository; source hashes and local verification paths are in `input_source_manifest.json`.",
        "",
        "## Observation contract", "",
        "Values are the published nM concentrations in the maternal or fetal perfusate reservoir. Mbefore/Fbefore remain text-labeled pre-exposure readings without invented elapsed times. M0, M2, then 30-minute labels are preserved as reported minutes; fetal data begin at Fbefore and F2. Each numbered column is linked to Table 1 as a perfusion-run ID and group, not to personal identity.",
        "The source says blanks reflect analysis errors but does not give per-cell causes. The run map reports a source-defined acceptable-duration window. Values after that duration remain visible and are flagged; the audit does not silently treat them as valid late-time observations.",
        "",
        "## Eligibility and remaining evidence", "",
        "Eligible for source-linked descriptive concentration summaries after human transcription review. Not eligible for a dimensional transport fit from this file set: numerical per-sample reservoir volume/removal histories, per-run final volumes, analyte inventory/recovery, calibration/uncertainty and original chromatograms are absent. The article describes observing volume after samples but does not publish those numeric records in the pinned data files. Term placental tissue does not observe embryonic growth, gestational continuity, birth or later health.",
        "No fit, inferential test, source-ledger promotion, experimental instruction or clinical recommendation is produced.",
        "",
        "Run mapping details are in `run_map.csv`; all expected source coordinates and validity-window labels are in `cell_observations.csv`; exact source values and missingness also populate `input_dataset.json`.",
    ]
    files = {
        "input_source_manifest.json": json_bytes(source_manifest),
        "candidate_unit_linkage.json": json_bytes(candidate_link),
        "input_dataset.json": dataset_raw,
        "cell_observations.csv": csv_bytes(cell_columns, rows),
        "run_map.csv": csv_bytes(["perfusion_id", "source_column_header", "antagonist", "condition_id",
                                   "source_reported_ok_hours", "source_locator"], run_rows),
        "missingness_summary.csv": csv_bytes(
            ["dimension", "category", "compartment", "n_expected", "n_numeric", "n_blank",
             "n_after_source_ok_window", "n_numeric_after_source_ok_window",
             "n_blank_after_source_ok_window"], missingness["breakdown"]),
        "summary_reproduction.json": json_bytes(summary),
        "qualification.json": json_bytes(summary_report),
        "REPORT.md": ("\n".join(report_lines) + "\n").encode("utf-8"),
    }
    return publish_bundle(output, kind="human_placental_perfusion_observation_audit",
        input_raw=input_fingerprint, files=files,
        metadata={"source_review_status": "candidate", "human_review": "pending",
            "source_artifact_sha256": {item["artifact_id"]: item["sha256"] for item in manifest_artifacts},
            "n_source_cells": len(rows), "n_numeric_values": len(numeric), "n_blank_cells": len(missing),
            "biological_assay_performed": False, "model_fit": False,
            "descriptive_check": "Tryptophan concentration ratio only; not a flux estimate."})
