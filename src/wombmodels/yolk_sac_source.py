"""Pinned mouse yolk-sac source audit; no physiological units, fitting or repair."""
from __future__ import annotations

import math
import statistics
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256
from .hori_source import _figure_cells

WORKBOOK_SHA256 = "b2bd434213007dfab98df41c864db53a474aa74bf382f156ef0340c44a35ac6a"
ARTICLE_URL = "https://doi.org/10.1038/s42003-026-10656-4"
WORKBOOK_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs42003-026-10656-4/MediaObjects/42003_2026_10656_MOESM8_ESM.xlsx")
PANELS = (("F", "AFP concentration", 2, 4, 13, 1),
          ("G", "APOA concentration", 17, 19, 28, 1),
          ("H", "VEGFA concentration", 32, 34, 44, 0))
SHEETS = ("Figure 2", "Figure 4", "Figure 5", "Figure 6")


def _numeric(cells, locator):
    token, kind, _ = cells.get(locator, (None, None, None))
    if kind != "numeric" or not isinstance(token, str) or not 1 <= len(token) <= 128:
        raise InputError(f"Missing or unsupported source numeric cell {locator}")
    try:
        value = float(token)
    except (ValueError, OverflowError) as exc:
        raise InputError(f"Invalid source numeric cell {locator}") from exc
    if not math.isfinite(value) or value < 0:
        raise InputError(f"Nonfinite or negative source cell {locator}")
    return token, value


def _extract(cells):
    rows, summaries, mean_profiles = [], [], {}
    expected = set()
    for panel, quantity, title_row, first, last, first_day in PANELS:
        for cell, label in ((f"A{title_row-1}", panel), (f"B{title_row}", quantity),
                            (f"B{title_row+1}", "NC"), (f"G{title_row+1}", "WEC"),
                            (f"E{title_row+1}", "mean"), (f"F{title_row+1}", "SD"),
                            (f"J{title_row+1}", "mean"), (f"K{title_row+1}", "SD")):
            if cells.get(cell, (None,))[0] != label:
                raise InputError(f"Changed source header at Figure 5!{cell}")
        for index, row in enumerate(range(first, last + 1)):
            day = f"D{first_day+index}"
            if cells.get(f"A{row}", (None,))[0] != day:
                raise InputError(f"Changed source time label at Figure 5!A{row}")
            for group, cols, mean_col, sd_col in (("NC", "BCD", "E", "F"), ("WEC", "GHI", "J", "K")):
                values = []
                for col in (*cols, mean_col, sd_col):
                    locator = f"{col}{row}"
                    expected.add(locator)
                    token, value = _numeric(cells, locator)
                    role = "reported_mean" if col == mean_col else "reported_SD" if col == sd_col else "source_scalar"
                    rows.append({"sheet": "Figure 5", "panel": panel, "quantity_label": quantity,
                        "group_label": group, "time_label": day, "time_cell": f"A{row}",
                        "cell": locator, "column_role": role, "source_numeric_text": token,
                        "value": value, "reported_concentration_unit": None,
                        "unit_status": "unqualified", "biological_unit_id": None,
                        "replicate_role": "not_reported"})
                    if role == "source_scalar":
                        values.append(value)
                mean = _numeric(cells, f"{mean_col}{row}")[1]
                sd = _numeric(cells, f"{sd_col}{row}")[1]
                calculated_mean, calculated_sd = statistics.mean(values), statistics.stdev(values)
                for kind, reported, calculated, col in (("mean", mean, calculated_mean, mean_col),
                                                        ("sample_SD", sd, calculated_sd, sd_col)):
                    tolerance = 1e-12 * max(1.0, abs(calculated))
                    summaries.append({"panel": panel, "group_label": group, "time_label": day,
                        "source_cells": ";".join(f"{c}{row}" for c in cols),
                        "reported_cell": f"{col}{row}", "summary_kind": kind,
                        "reported_value": reported, "recomputed_value": calculated,
                        "absolute_difference": abs(reported-calculated), "tolerance": tolerance,
                        "arithmetic_matches": abs(reported-calculated) <= tolerance})
                if group == "WEC":
                    mean_profiles.setdefault(panel, []).append({"time_label": day,
                        "time_cell": f"A{row}", "mean_cell": f"{mean_col}{row}", "value": mean})
    actual = {cell for cell, (token, kind, _) in cells.items() if kind == "numeric" and token is not None}
    if actual != expected:
        raise InputError("Figure 5 numeric inventory differs from the selected source revision")
    return rows, summaries, mean_profiles


def _local_maxima(profile):
    """Strict adjacent interior maxima of reported means, not secretion events."""
    return [item for i, item in enumerate(profile[1:-1], 1)
            if item["value"] > profile[i-1]["value"] and item["value"] > profile[i+1]["value"]]


def audit_yolk_sac_source(workbook_path: Path, output: Path):
    path = Path(workbook_path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise InputError("Workbook must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000 or sha256(raw) != WORKBOOK_SHA256:
        raise InputError("Workbook size/hash differs from the inspected Jin revision; a new audit is required")
    sheets = {name: _figure_cells(raw, name) for name in SHEETS}
    rows, summaries, profiles = _extract(sheets["Figure 5"])
    maxima = _local_maxima(profiles["H"])
    coverage = [{"sheet": name, "nonempty_scalar_cells": sum(token is not None for token, _, _ in cells.values()),
                 "numeric_cells": sum(token is not None and kind == "numeric" for token, kind, _ in cells.values())}
                for name, cells in sheets.items()]
    qualification = {"schema_version": 1, "source_review_status": "candidate", "human_review": "pending",
        "n_source_numeric_cells": len(rows), "n_source_scalar_columns": 6,
        "n_source_time_rows": len(rows)//10, "n_summary_arithmetic_checks": len(summaries),
        "n_summary_arithmetic_mismatches": sum(not item["arithmetic_matches"] for item in summaries),
        "numeric_observation_intake": "excluded_pending_concentration_units_and_assay_quantity_review",
        "starting_cohort_denominators": None, "unit_linkage": "unqualified",
        "NC_definition_background_handling": "unqualified; no subtraction performed",
        "analyte_label": "Source workbook/caption APOA versus Results APOA1; specificity review pending",
        "timing_reconciliation": {"manuscript_reported_peak_labels": ["D2", "D6"],
            "manuscript_locator": "Results: Coagulation and angiogenesis in the YS endoderm, VEGFA paragraph; Figure 5H",
            "workbook_mean_interior_maxima": maxima,
            "labels_agree": [item["time_label"] for item in maxima] == ["D2", "D6"],
            "rule": "strict adjacent interior maxima of unmodified WEC reported means; endpoints excluded",
            "interpretation": "Text/table timing needs reconciliation; this does not identify secretion timing or repair source labels."},
        "selected_sheet_coverage": coverage,
        "source_modified": False, "source_formula_execution": False,
        "biological_assay_performed": False, "biological_fit_performed": False,
        "missing": ["Figure 1 starting rosters, developmental numerators/denominators, exclusions and endpoint-unit identities.",
            "Concentration units, NC definition, analyte specificity, volume/renewal accounting, normalization and calibration.",
            "Biological versus technical replication and longitudinal identity of each scalar column.",
            "Linked support function, embryonic material receipt and embryo-proper progression including failed units.",
            "Direct quantitative sources for uptake/CFU outcomes; inspected workbook sheets lack these selected panels.",
            "Manuscript/table timing reconciliation, source-specific reuse and human scientific review."]}
    manifest = {"schema_version": 1, "article_url": ARTICLE_URL, "source_url": WORKBOOK_URL,
        "filename": path.name, "sha256": sha256(raw), "size_bytes": len(raw),
        "selected_sheets": list(SHEETS), "source_modified": False, "external_source_required": True}
    report = "\n".join(["# Mouse yolk-sac functional source audit", "",
        "AI-assisted source transcription and arithmetic checks; human review pending.",
        f"{len(rows)} numeric source cells across {len(rows)//10} time rows; {len(summaries)} arithmetic checks.",
        "Source lexemes, labels and locators are retained; column/cell counts are not verified biological n.",
        "Concentration units and specimen linkage are unqualified. No numeric observation dataset, subtraction, mass-flux estimate or biological fit is produced.",
        "", "## Source timing discrepancy", "",
        "Manuscript text names D2/D6; strict adjacent interior maxima of the WEC reported mean column occur at "
            + ", ".join(item["time_label"] for item in maxima) + ".",
        "Both source representations are preserved; no relabeling or secretion-mechanism inference is performed.",
        "", f"[Jin et al., 2026]({ARTICLE_URL}). Article in press; CC BY-NC-ND 4.0 banner, workbook-specific reuse pending.",
        "External workbook is unchanged and not bundled. The receipt pins this audit, not scientific validity.",
        "", "## Required qualification", "", *["- " + item for item in qualification["missing"]], ""])
    return publish_bundle(output, kind="yolk_sac_functional_source_audit", input_raw=raw,
        files={"input_source_manifest.json": json_bytes(manifest), "source_cells.csv": csv_bytes(list(rows[0]), rows),
               "summary_arithmetic.csv": csv_bytes(list(summaries[0]), summaries),
               "qualification.json": json_bytes(qualification), "REPORT.md": report.encode()},
        metadata={"source_review_status": "candidate", "biological_assay_performed": False,
                  "biological_fit_performed": False, "source_modified": False})
