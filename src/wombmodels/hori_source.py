"""Offline, pinned-file audit of Hori 2024 Figure 5G; no model calibration."""
from __future__ import annotations

import io
import math
import statistics
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256
from .observations import validate_dataset

WORKBOOK_SHA256 = "a2b741034f322e2ffc2f23adf09ed5a00aaa1b11a4c239b0feec283a81075e9b"
ARTICLE_URL = "https://www.nature.com/articles/s41467-024-45279-y"
WORKBOOK_URL = ("https://static-content.springer.com/esm/"
                "art%3A10.1038%2Fs41467-024-45279-y/MediaObjects/41467_2024_45279_MOESM7_ESM.xlsx")
LICENSE_NOTE = "Article CC BY 4.0; workbook-specific/third-party terms need human confirmation"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
REPORTED_UNIT = "x10-6 cm/s"
COMPOUNDS = (("Antipyrine", "A", "B"), ("Caffeine", "D", "E"), ("Glyphosate", "G", "H"))
GROUPS = (("Cont", 4, "acellular collagen membrane control"),
          ("HU", 8, "HUVEC"), ("ST", 12, "ST"), ("ST/HU", 16, "ST/HUVEC"))


def _figure_cells(raw: bytes) -> dict:
    """Read one known sheet's scalar cells without evaluating workbook code."""
    if len(raw) > 1_000_000:
        raise InputError("Workbook exceeds the 1 MB audit limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if (len(members) > 128 or len({i.filename for i in members}) != len(members)
                    or sum(i.file_size for i in members) > 10_000_000
                    or any(i.file_size > 2_000_000 or i.flag_bits & 1 for i in members)):
                raise InputError("Workbook archive exceeds bounds or has duplicate/encrypted members")

            def xml(name):
                content = archive.read(name)
                if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
                    raise InputError("Workbook XML declarations are unsupported")
                return ET.fromstring(content)

            sheets = [item for item in xml("xl/workbook.xml").findall("s:sheets/s:sheet", NS)
                      if item.get("name") == "Fig. 5G"]
            if len(sheets) != 1:
                raise InputError("Expected exactly one Fig. 5G sheet")
            rid = sheets[0].get("{" + NS["r"] + "}id")
            links = [item for item in xml("xl/_rels/workbook.xml.rels").findall("p:Relationship", NS)
                     if item.get("Id") == rid]
            if (len(links) != 1 or links[0].get("TargetMode") == "External"
                    or links[0].get("Type") != NS["r"] + "/worksheet"):
                raise InputError("Invalid Fig. 5G worksheet relationship")
            target = links[0].get("Target", "")
            if (not target.startswith("worksheets/") or "\\" in target or ":" in target
                    or any(part in {"", ".", ".."} for part in target.split("/"))):
                raise InputError("Invalid worksheet path")
            shared = ["".join(item.itertext()) for item in
                      xml("xl/sharedStrings.xml").findall("s:si", NS)]
            cells = {}
            for cell in xml("xl/" + target).findall("s:sheetData/s:row/s:c", NS):
                locator = cell.get("r")
                if not locator or locator in cells:
                    raise InputError("Missing or duplicate worksheet cell locator")
                if cell.find("s:f", NS) is not None:
                    raise InputError("Fig. 5G formulas are unsupported; cached results are not measurements")
                value = cell.find("s:v", NS)
                token = value.text if value is not None else None
                if cell.get("t") == "s":
                    if token is None or not token.isdigit() or int(token) >= len(shared):
                        raise InputError("Invalid shared string reference")
                    cells[locator] = (shared[int(token)], "text", token)
                elif cell.get("t") in {None, "n"}:
                    cells[locator] = (token, "numeric", token)
                else:
                    raise InputError("Unsupported Fig. 5G cell type")
            return cells
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, EOFError, ValueError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("Workbook is not the supported bounded XLSX structure") from exc


def _extract_endpoints(cells: dict) -> list[dict]:
    rows = []
    for compound, label_column, value_column in COMPOUNDS:
        if cells.get(label_column + "2", (None,))[0] != compound:
            raise InputError(f"Unexpected compound header at {label_column}2")
        if cells.get(value_column + "3", (None,))[0] != "Papp (x10-6 cm/s)":
            raise InputError(f"Unexpected reported unit at {value_column}3")
        for group, first_row, _ in GROUPS:
            for row in range(first_row, first_row + 4):
                cell = value_column + str(row)
                if cells.get(label_column + str(row), (None,))[0] != group:
                    raise InputError(f"Unexpected group label for {cell}")
                token, kind, _ = cells.get(cell, (None, None, None))
                if token is None or kind != "numeric":
                    raise InputError(f"Missing or nonnumeric endpoint at {cell}")
                try:
                    value = float(token)
                except (ValueError, OverflowError) as exc:
                    raise InputError(f"Invalid numeric endpoint at {cell}") from exc
                if not math.isfinite(value) or value < 0:
                    raise InputError(f"Invalid finite nonnegative Papp at {cell}")
                rows.append({"record_id": "hori-fig5g-" + cell.lower(), "sheet": "Fig. 5G",
                             "cell": cell, "compound": compound, "group": group,
                             "source_numeric_text": token, "value": value,
                             "reported_unit": REPORTED_UNIT})
    return rows


def _dataset(rows: list[dict], workbook_name: str) -> dict:
    workbook = {"artifact_id": "hori-source-data", "uri": WORKBOOK_URL,
                "license": LICENSE_NOTE, "sha256": WORKBOOK_SHA256,
                "retrieved_on": "2026-10-09", "local_path": workbook_name}
    article = {"artifact_id": "hori-article", "uri": ARTICLE_URL,
               "license": "CC BY 4.0 article; third-party exceptions may apply",
               "sha256": None, "retrieved_on": "2026-10-09",
               "developmental_scope": {"species": "human",
                   "stage_tracks": ["organoid_or_tissue_model"], "time_unit": "model_day",
                   "start": 6, "end": 6,
                   "source_locator": "Figure 5 caption: ST or ST/HUVEC data in F and G obtained from day-6 models; does not date HU/Cont."}}
    observations = []
    descriptions = {group: label for group, _, label in GROUPS}
    for row in rows:
        day = 6 if row["group"] in {"ST", "ST/HU"} else None
        observations.append({
            "schema_version": 1, "record_id": row["record_id"],
            "evidence_status": "author_reported_summary", "species": "human",
            "stage_track": "organoid_or_tissue_model",
            "developmental_interval": {"label": "day-6 in-vitro model" if day else "model age not reported for HU/Cont",
                "time_unit": "model_day", "start": day, "end": day,
                "stage_source_artifact_id": "hori-article"},
            "model_system": {"kind": "other" if row["group"] == "Cont" else "tissue_construct",
                "label": descriptions[row["group"]]},
            "assay": {"name": "published apparent permeability", "endpoint": row["compound"] + " Papp",
                "unit": REPORTED_UNIT, "measurement_role": "function"},
            "independent_unit": {"kind": "not_reported", "id": None, "parent_id": None,
                "hierarchy_note": "Caption reports N=4 biologically independent samples; workbook does not identify units or cross-endpoint linkage."},
            "observation": {"value": row["value"], "measurement_time": None,
                "measurement_time_unit": "", "comparator_id": None, "replicate_role": "not_reported"},
            "source": {key: workbook[key] for key in ("artifact_id", "uri", "license", "sha256", "retrieved_on")},
            "limitations": [
                f"Value locator: Fig. 5G!{row['cell']}. Cell coordinates identify source values, not biological units.",
                "Published derived coefficient, not a raw concentration/flux trajectory. No physiological model contract is established.",
                "Human labels the source study's model context; the Cont comparator is acellular.",
                "In-vitro model days are not gestational ages. No between-stage or embryo-to-birth continuity is asserted."]})
    data = {"schema_version": 1, "dataset_id": "hori-2024-fig5g-candidate",
            "title": "Candidate transcription of Hori 2024 Figure 5G published Papp endpoints",
            "source_revision": {"revision_id": "hori-fig5g-agent-audit-2026-10-09",
                "citation": "Hori et al. (2024), Trophoblast stem cell-based organoid models of the human placental barrier. Nature Communications 15, 962.",
                "source_kind": "peer_reviewed_human_invitro", "source_url": ARTICLE_URL,
                "review_status": "candidate", "reviewer": "", "reviewed_on": None, "review_note": ""},
            "artifacts": [workbook, article], "observations": observations, "transitions": []}
    validate_dataset(data)
    return data


def _summaries(rows: list[dict]) -> list[dict]:
    result = []
    for compound, _, _ in COMPOUNDS:
        for group, _, _ in GROUPS:
            values = [row["value"] for row in rows if row["compound"] == compound and row["group"] == group]
            result.append({"compound": compound, "group": group, "reported_unit": REPORTED_UNIT,
                           "n_values": len(values), "n_reported_unit_ids": 0,
                           "mean": statistics.mean(values), "sample_sd": statistics.stdev(values),
                           "minimum": min(values), "maximum": max(values)})
    return result


def audit_hori_source(workbook_path: Path, output: Path) -> dict:
    """Publish a candidate transcription and descriptive summaries of pinned bytes."""
    path = Path(workbook_path)
    if any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise InputError("Workbook must be a regular, nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000:
        raise InputError("Workbook exceeds the 1 MB audit limit")
    if sha256(raw) != WORKBOOK_SHA256:
        raise InputError("Workbook SHA-256 differs from the inspected publisher revision; a new audit is required")
    rows = _extract_endpoints(_figure_cells(raw))
    dataset = _dataset(rows, path.name)
    summaries = _summaries(rows)
    qualification = {
        "schema_version": 1, "review_status": "candidate", "human_review": "pending",
        "scientific_transcription": "agent_extraction_not_human_verified",
        "descriptive_audit": "48 published endpoints in 12 exact compound/group partitions",
        "transport_benchmark": "not_eligible_from_inspected_source",
        "independent_unit_split": "cannot_freeze_without_source_unit_identifiers",
        "missing_for_dynamic_benchmark": [
            "Unit-linked donor and receiver concentration/flux time series with exact quantity/time units.",
            "Stable independent-unit, donor/batch and cross-endpoint linkage identifiers.",
            "Unit-linked capacities, interface geometry, boundary inputs and measured collection corrections.",
            "Calibration, uncertainty, exclusions and missingness needed to score held-out observations.",
            "Source-specific human review and reuse/redistribution confirmation."],
        "limits": ["No kinetic model fit, inferential test, biological unit-count inference or source-ledger promotion.",
                   "Cell positions are never paired across compounds or with TEER.",
                   "Mean and sample SD describe four values in each partition; no sampling-distribution claim is made.",
                   "Actual source units are preserved for this audit only; dimensionless software fixtures remain uncalibrated."]}
    manifest = {"schema_version": 1, "source_url": WORKBOOK_URL, "source_filename": path.name,
                "sha256": sha256(raw), "size_bytes": len(raw), "retrieved_on": "2026-10-09",
                "sheet": "Fig. 5G", "license_note": LICENSE_NOTE,
                "external_source_required": True, "source_copied_or_modified": False}
    lines = ["# Hori Figure 5G source audit", "",
             "Agent-assisted source transcription; candidate awaiting human review.",
             "48 published Papp values; 12 compound/group partitions; no source unit IDs; no transition edges.",
             "The caption reports N=4 biologically independent samples per group. The file supplies no linked identities.",
             f"[Hori et al., 2024]({ARTICLE_URL}); Figure 5G and publisher Source Data.", "",
             "Article notice: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Workbook-specific/third-party terms need human confirmation. Values were extracted and reformatted; summaries are newly calculated.", "",
             "Numeric lexemes and cell locators are retained in endpoint_cells.csv. The original workbook remains external and untouched.",
             "The generated input_dataset.json can be checked with validate-observations using the source workbook's directory as --source-root.", "",
             "| Compound | Group | Values | Mean | Sample SD | Reported unit |",
             "| --- | --- | ---: | ---: | ---: | --- |"]
    lines += [f"| {r['compound']} | {r['group']} | {r['n_values']} | {r['mean']:.6g} | {r['sample_sd']:.6g} | {REPORTED_UNIT} |" for r in summaries]
    lines += ["", "Transport benchmark: not eligible from the inspected source. Missing requirements:", ""]
    lines += ["- " + item for item in qualification["missing_for_dynamic_benchmark"]]
    lines += ["", *qualification["limits"], "",
              "ST and ST/HU carry source-caption day 6; HU/Cont bounds remain null. Model days are not gestational ages.",
              "No result establishes sustained human gestation or a healthy newborn. No biological assay was performed."]
    return publish_bundle(output, kind="published_endpoint_source_audit", input_raw=raw,
        files={"input_source_manifest.json": json_bytes(manifest), "input_dataset.json": json_bytes(dataset),
               "endpoint_cells.csv": csv_bytes(list(rows[0]), rows),
               "group_summary.csv": csv_bytes(list(summaries[0]), summaries),
               "qualification.json": json_bytes(qualification), "REPORT.md": ("\n".join(lines) + "\n").encode()},
        metadata={"source_sha256": sha256(raw), "source_review_status": "candidate",
                  "n_endpoints": 48, "n_reported_unit_ids": 0, "model_calibration_performed": False})
