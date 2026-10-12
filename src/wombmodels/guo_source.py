"""Pinned niche-source audit; no mechanical fit, causal estimate or embryo assay."""
from __future__ import annotations

import math
import statistics
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256
from .hori_source import _figure_cells
from .observations import validate_dataset

WORKBOOK_SHA256 = "c84b1faf2ebe02c812af7ec73d94a10c6640a11fba677ac85947999b9dc33e8e"
ARTICLE_URL = "https://www.nature.com/articles/s41467-025-68039-y"
ARTICLE_HTML_SHA256 = "3f6a9116d3e2daca4aa1e91c68a322dd918ffc230d02db3b89df5567c558f65a"
ARTICLE_HTML_SIZE_BYTES = 536319
WORKBOOK_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs41467-025-68039-y/MediaObjects/41467_2025_68039_MOESM18_ESM.xlsx")
SUPPLEMENTARY_INFO_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs41467-025-68039-y/MediaObjects/41467_2025_68039_MOESM1_ESM.pdf")
SUPPLEMENTARY_INFO_SHA256 = "eeef1dba62e161983b2e1a7ca58e28251fefb617fca622757319036e7e7a3d9f"
SUPPLEMENTARY_INFO_SIZE_BYTES = 3383310
LICENSE_NOTE = "Article CC BY-NC-ND 4.0; workbook-specific reuse review pending"
PANELS = (
    ("Fig4A", "reported relaxation half-time", ("40-MG", "5.5De"), (9,10), None),
    ("Fig4C", "reported Young modulus", ("40-MG", "40-MGT", "40-MGN"), (10,10,10), None),
    ("Fig4D", "reported relaxation half-time", ("40-MG", "40-MGT", "40-MGN"), (5,5,5), None),
    ("Fig4E", "two-cavity developmental percentage", ("40-MG", "40-MGT", "40-MGN"), (7,4,5), 3),
    ("Fig4F", "egg-cylinder developmental percentage", ("40-MG", "40-MGT", "40-MGN"), (7,4,5), 4),
)
MECHANICAL_AXIS_CONTEXT = {
    "Fig4A":{"unit":"s", "axis_scale":"linear", "measure":"stress-relaxation half-time, τ1/2",
        "caption_n":"n=10, 9 independent experiments (E5.5 decidua and 40-MG, respectively)",
        "method_mapping_status":"The caption describes the relaxation timescale and sample groups but names no assay or instrument; the Results text also does not assign a method."},
    "Fig4C":{"unit":"Pa", "axis_scale":"logarithmic (10^1 and 10^2 ticks)", "measure":"Young's modulus, E",
        "caption_n":"n=10; unit counted by n not specified"},
    "Fig4D":{"unit":"s", "axis_scale":"linear", "measure":"stress-relaxation half-time, τ1/2",
        "caption_n":"n=5; unit counted by n not specified",
        "method_mapping_status":"Figure caption explicitly identifies nanoindentation."},
}
MECHANICAL_MEASUREMENT_CONTEXT = {
    "rheometer_relaxation": {
        "source_locator":"Methods > Rheological test",
        "instrument":"MCR-302 rheometer with parallel plate",
        "pretest_condition":"Hydrogel held at 37 °C for 60 min before the stress-relaxation test",
        "loading_mode":"fixed strain, 1%",
        "response_normalization":"stress normalized to initial maximum stress",
        "fit_model":"three-element generalized Maxwell–Wiechert model",
        "repeat_statement":"Methods state all tests were repeated at least three times",
        "figure_link_limit":"Figure 4A's caption and Results text describe a relaxation timescale for E5.5 decidua and 40-MG but do not name an assay or instrument; Supplementary Fig. 10I/J explicitly identifies rheometer data. Individual run IDs and mapping to the Figure 4A workbook values are not supplied"
    },
    "nanoindentation_relaxation": {
        "source_locator":"Methods > Nanoindentation test",
        "instrument":"Optics11 Piuma nanoindenter",
        "loading_history":"4 s loading to 15,000 nm indentation depth, 40 s hold, then 4 s unloading",
        "probe_context":"3 μm radius probe; cantilever stiffness 0.024 N/m",
        "response_fit":"generalized Maxwell/Prony load-decay model during the holding phase",
        "repeat_statement":"Methods state three experiments per tested sample",
        "figure_link_limit":"Figure 4D caption identifies nanoindentation, but source sample IDs and the aggregation from repeated experiments to the five plotted values per condition are not reported"
    },
    "young_modulus_method_mapping": {
        "figure_4c_caption":"Young's modulus detected using a nanoindenter",
        "methods_modulus_description":"A separate Methods description specifies an AFM/Hertz load-displacement method for decidua and Matrigel, with loading-curve fit from contact point to maximum load.",
        "mapping_status":"not_explicitly_established_for_figure_4c",
        "interpretation_limit":"Do not assume the separately described AFM/Hertz modulus method is the protocol used for Figure 4C's nanoindenter measurements; exact sample and replicate hierarchy remain unqualified."
    }
}
SUPPLEMENTARY_PROFILE_CONTEXT = {
    "source_locator":"Supplementary Fig. 10I axis and caption, PDF pp. 18-19",
    "workbook_sheet":"Sup 10 I",
    "workbook_mapping_basis":"The sheet title names the same supplementary panel and its three condition headers match the plotted legend; source column order is retained separately.",
    "x_axis_label":"Time (s)",
    "x_unit":"s",
    "x_axis_scale":"linear",
    "x_axis_ticks":[0,250,500,750,1000],
    "response_axis_label":"σ/σ₀",
    "response_unit":"dimensionless",
    "response_normalization":"Stress levels normalized to the initial stress level.",
    "assay":"rheometer",
    "source_condition_headers_in_sheet_order":["40-MG","40-MGN","40-MGT"],
    "source_condition_legend_order":["40-MG","40-MGT","40-MGN"],
    "panel_i_replicate_scope":"The Supplementary Fig. 10I caption gives no n or profile aggregation level; the workbook does not state whether each curve is an individual run, mean, or another summary.",
    "adjacent_panel_j_scope":"Supplementary Fig. 10J reports a rheometer relaxation half-time as mean ± s.d. with n=3 independent experiments; those summary replicates are not assigned to Fig. 10I profile rows.",
    "interpretation_limit":"Axes, normalization, assay and condition labels are qualified; biological/technical unit IDs, per-curve hierarchy and mapping from profile rows to the n=3 panel-J summaries remain unknown. Keep profiles out of observation intake and fitting."
}
SUPPLEMENTARY_PANEL_J_CONTEXT = {
    "source_locator":"Supplementary Fig. 10J axis and caption, PDF pp. 18-19",
    "workbook_sheet":"Sup10J",
    "quantity":"stress-relaxation half-time, τ1/2",
    "unit":"s",
    "axis_scale":"linear",
    "assay":"rheometer",
    "caption_n":"n=3 independent experiments per condition",
    "caption_summary":"mean ± s.d.",
    "condition_headers_in_sheet_order":["40-MG","40-MGT","40-MGN"],
    "source_to_caption_count_alignment":"The workbook contains three source values per condition, matching the caption's n=3; the sheet provides no experiment IDs to verify one cell per independent experiment.",
    "cross_condition_row_pairing":"not_established",
    "profile_row_linkage":"The sheet does not identify which Fig. 10I trace or profile rows correspond to any Fig. 10J value.",
    "interpretation_limit":"The three values per condition and experiment-level n are source-qualified, but IDs and cross-condition pairing are absent. Keep these mechanical values out of biological observation intake and fitting."
}


def _numeric(cells, locator, *, percentage=False):
    token, kind, _ = cells.get(locator, (None,None,None))
    if kind != "numeric" or token is None or not 1 <= len(token) <= 128:
        raise InputError(f"Missing or unsupported source numeric cell {locator}")
    try:
        value = float(token)
    except (ValueError, OverflowError) as exc:
        raise InputError(f"Invalid source numeric cell {locator}") from exc
    if not math.isfinite(value) or value < 0 or (percentage and value > 100):
        raise InputError(f"Nonfinite or out-of-domain source cell {locator}")
    return token, value


def _extract(sheets):
    endpoints, curves = [], []
    for sheet, quantity, headers, counts, day in PANELS:
        cells = sheets[sheet]
        expected = set()
        for col, (header,count) in enumerate(zip(headers,counts)):
            column = chr(65+col)
            if cells.get(column+"1", (None,))[0] != header:
                raise InputError(f"Changed source condition header in {sheet}")
            for row in range(2,2+count):
                locator = column+str(row)
                expected.add(locator)
                token, value = _numeric(cells, locator, percentage=day is not None)
                mechanical_axis = MECHANICAL_AXIS_CONTEXT.get(sheet)
                endpoints.append({"record_id":f"guo-{sheet.lower()}-{locator.lower()}", "sheet":sheet,
                    "cell":locator, "source_condition":header, "quantity":quantity,
                    "numeric_text":token, "value":value,
                    "reported_unit":"%" if day is not None else mechanical_axis["unit"],
                    "unit_status":"caption_reported" if day is not None else "axis_reported",
                    "reported_axis_scale":"not_applicable" if day is not None else mechanical_axis["axis_scale"],
                    "measurement_time":day, "measurement_time_unit":"IVC day" if day is not None else None,
                    "physical_unit_id":None, "replicate_role":"not_reported"})
        actual = {cell for cell,(token,kind,_) in cells.items() if kind == "numeric" and token is not None}
        if actual != expected:
            raise InputError(f"Source numeric inventory differs in {sheet}")
    cells = sheets["Sup 10 I"]
    for column, title in (("B","40-MG"),("D","40-MGN"),("F","40-MGT")):
        if cells.get(column+"1",(None,))[0] != title:
            raise InputError("Changed relaxation-profile source header")
    expected = set()
    for row in range(2,202):
        for column in ("A","B","D","F"):
            cell = column+str(row)
            expected.add(cell)
            token,value = _numeric(cells,cell)
            is_time = column == "A"
            curves.append({"sheet":"Sup 10 I", "source_panel":"Supplementary Fig. 10I", "cell":cell,
                "column_role":"source_time_coordinate" if is_time else "source_response_profile",
                "source_condition":None if is_time else cells[column+"1"][0], "numeric_text":token,
                "value":value, "reported_unit":"s" if is_time else "dimensionless",
                "reported_axis_label":"Time (s)" if is_time else "σ/σ₀",
                "unit_status":"axis_reported" if is_time else "axis_and_caption_reported",
                "normalization":"not_applicable" if is_time else "stress normalized to initial stress level",
                "physical_unit_id":None})
    actual = {cell for cell,(token,kind,_) in cells.items() if kind == "numeric" and token is not None}
    if actual != expected:
        raise InputError("Relaxation-profile numeric inventory differs")
    return endpoints,curves


def _extract_supplementary_panel_j(cells):
    values = []
    conditions = SUPPLEMENTARY_PANEL_J_CONTEXT["condition_headers_in_sheet_order"]
    expected = set()
    for column_index, condition in enumerate(conditions):
        column = chr(65+column_index)
        if cells.get(column+"1", (None,))[0] != condition:
            raise InputError(f"Changed source condition header in Sup10J at {column}1")
        for row in range(2,5):
            locator = column+str(row)
            expected.add(locator)
            token, value = _numeric(cells, locator)
            values.append({
                "record_id":f"guo-sup10j-{locator.lower()}",
                "sheet":"Sup10J",
                "source_panel":"Supplementary Fig. 10J",
                "cell":locator,
                "source_condition":condition,
                "quantity":SUPPLEMENTARY_PANEL_J_CONTEXT["quantity"],
                "numeric_text":token,
                "value":value,
                "reported_unit":SUPPLEMENTARY_PANEL_J_CONTEXT["unit"],
                "unit_status":"axis_reported",
                "reported_axis_scale":SUPPLEMENTARY_PANEL_J_CONTEXT["axis_scale"],
                "caption_n":SUPPLEMENTARY_PANEL_J_CONTEXT["caption_n"],
                "replicate_role":"source scalar; experiment IDs and row-wise pairing are not reported",
                "physical_unit_id":None,
            })
    actual = {cell for cell,(token,kind,_) in cells.items() if kind == "numeric" and token is not None}
    if actual != expected:
        raise InputError("Sup10J numeric inventory differs from the expected three values per condition")
    return values


def _summarize_supplementary_panel_j(values):
    summaries = {}
    for condition in SUPPLEMENTARY_PANEL_J_CONTEXT["condition_headers_in_sheet_order"]:
        selected = [item["value"] for item in values if item["source_condition"] == condition]
        if len(selected) != 3:
            raise InputError(f"Expected three Sup10J values for {condition}")
        summaries[condition] = {
            "n_source_values":len(selected),
            "caption_n":3,
            "n_cell_count_matches_caption_n":True,
            "mean_from_source_cells":statistics.mean(selected),
            "sample_sd_from_source_cells":statistics.stdev(selected),
            "sd_convention":"sample standard deviation (n-1) used for arithmetic reconciliation; caption does not state the formula",
        }
    return summaries


def _summarize_40mg_cross_panel_scale(endpoints, panel_j_values):
    """Compare the 40-MG half-time source scales without asserting assay equivalence."""
    panel_definitions = (
        ("Fig4A", "Figure 4A", 9,
         "method identity is not explicitly mapped for this panel in the inspected source"),
        ("Fig4D", "Figure 4D", 5,
         "figure caption identifies nanoindentation"),
    )
    summaries = {}
    for sheet, panel, expected_n, method_status in panel_definitions:
        selected = [item["value"] for item in endpoints
                    if item["sheet"] == sheet and item["source_condition"] == "40-MG"]
        if len(selected) != expected_n:
            raise InputError(f"Expected {expected_n} 40-MG half-time values for {sheet}")
        summaries[panel] = {
            "workbook_sheet":sheet,
            "source_condition":"40-MG",
            "quantity":"stress-relaxation half-time, τ1/2",
            "unit":"s",
            "n_source_values":len(selected),
            "minimum_seconds":min(selected),
            "maximum_seconds":max(selected),
            "mean_seconds":statistics.mean(selected),
            "median_seconds":statistics.median(selected),
            "method_status":method_status,
        }
    selected_j = [item["value"] for item in panel_j_values
                  if item["source_condition"] == "40-MG"]
    if len(selected_j) != 3:
        raise InputError("Expected three Supplementary Fig. 10J 40-MG values")
    summaries["Supplementary Fig. 10J"] = {
        "workbook_sheet":"Sup10J",
        "source_condition":"40-MG",
        "quantity":"stress-relaxation half-time, τ1/2",
        "unit":"s",
        "n_source_values":len(selected_j),
        "minimum_seconds":min(selected_j),
        "maximum_seconds":max(selected_j),
        "mean_seconds":statistics.mean(selected_j),
        "median_seconds":statistics.median(selected_j),
        "method_status":"figure caption identifies rheometer",
    }
    j_mean = summaries["Supplementary Fig. 10J"]["mean_seconds"]
    a_mean = summaries["Figure 4A"]["mean_seconds"]
    d_mean = summaries["Figure 4D"]["mean_seconds"]
    j_min = summaries["Supplementary Fig. 10J"]["minimum_seconds"]
    j_max = summaries["Supplementary Fig. 10J"]["maximum_seconds"]
    a_min = summaries["Figure 4A"]["minimum_seconds"]
    a_max = summaries["Figure 4A"]["maximum_seconds"]
    d_min = summaries["Figure 4D"]["minimum_seconds"]
    d_max = summaries["Figure 4D"]["maximum_seconds"]
    ranges_overlap = {
        "with_figure_4a":max(j_min, a_min) <= min(j_max, a_max),
        "with_figure_4d":max(j_min, d_min) <= min(j_max, d_max),
    }
    separated = not any(ranges_overlap.values())
    scale_interpretation = (
        "The same nominal condition, half-time quantity and seconds unit show a clear scale separation: "
        "the Supplementary Fig. 10J mean is about eight times the Figure 4A/D means and its observed range "
        "does not overlap either Figure 4 range."
        if separated else
        "The same nominal condition, half-time quantity and seconds unit are transcribed across panels, but "
        "these source-cell ranges do not show a complete separation from both Figure 4 ranges."
    )
    return {
        "condition":"40-MG",
        "quantity":"stress-relaxation half-time, τ1/2",
        "common_reported_unit":"s",
        "descriptive_summaries":summaries,
        "supplementary_10j_mean_to_figure_4_mean_ratios":{
            "vs_figure_4a":j_mean / a_mean if a_mean else None,
            "vs_figure_4d":j_mean / d_mean if d_mean else None,
            "ratio_definition":"ratio of source-cell arithmetic means; descriptive only",
        },
        "supplementary_10j_range_overlap_with_figure_4":ranges_overlap,
        "comparability_status":"unresolved_protocol_and_run_hierarchy",
        "interpretation_limit":(
            scale_interpretation + " Figure 4A's method mapping is not explicit here; Figure 4D "
            "is identified as nanoindentation and Supplementary Fig. 10J as rheometer. Without a panel-specific "
            "protocol and run/sample hierarchy, treat this as a source-reconciliation flag, not a direct contradiction, "
            "assay comparison, or biological result. Keep all mechanical values outside biological intake and fitting."
        ),
        "values_enter_observation_intake":False,
        "values_enter_mechanical_fit":False,
    }


def _mechanical_value_overlaps(endpoints):
    """Report exact source-lexeme overlaps without implying paired specimens."""
    groups = {}
    for endpoint in endpoints:
        if endpoint["sheet"] not in MECHANICAL_AXIS_CONTEXT:
            continue
        key = (endpoint["sheet"], endpoint["source_condition"])
        groups.setdefault(key, {}).setdefault(endpoint["numeric_text"], []).append(endpoint["cell"])

    keys = list(groups)
    overlaps = []
    for left_index, left_key in enumerate(keys):
        for right_key in keys[left_index + 1:]:
            common = sorted(set(groups[left_key]) & set(groups[right_key]))
            if not common:
                continue
            matches = [{
                "numeric_text": value,
                "left_cells": groups[left_key][value],
                "right_cells": groups[right_key][value],
            } for value in common]
            overlaps.append({
                "left_panel": left_key[0],
                "left_condition": left_key[1],
                "right_panel": right_key[0],
                "right_condition": right_key[1],
                "match_method": "exact numeric source-lexeme equality",
                "n_matching_lexemes": len(matches),
                "n_left_source_cells": sum(len(item["left_cells"]) for item in matches),
                "n_right_source_cells": sum(len(item["right_cells"]) for item in matches),
                "matches": matches,
                "interpretation_limit": (
                    "Exact transcription overlap only. The source data do not identify specimens or runs, "
                    "or say whether these entries are shared, remeasured, reused or coincident; do not infer "
                    "pairing, duplication or independent replication."
                ),
            })
    return overlaps


def _profile_grid_qualification(curves):
    """Describe source-grid structure without fitting or smoothing curves."""
    coordinates = [item["value"] for item in curves
                   if item["column_role"] == "source_time_coordinate"]
    if len(coordinates) != 200 or any(
            right <= left for left, right in zip(coordinates, coordinates[1:])):
        raise InputError("Supplementary Fig. 10I time coordinates must be 200 strictly increasing values")
    steps = [right-left for left, right in zip(coordinates, coordinates[1:])]
    response_by_condition = {}
    conditions = []
    for item in curves:
        if item["column_role"] != "source_response_profile":
            continue
        condition = item["source_condition"]
        if condition not in response_by_condition:
            response_by_condition[condition] = []
            conditions.append(condition)
        response_by_condition[condition].append(item["value"])
    if len(response_by_condition) != 3 or any(len(values) != 200 for values in response_by_condition.values()):
        raise InputError("Supplementary Fig. 10I must contain three 200-value condition profiles")
    summaries = {}
    for condition in conditions:
        values = response_by_condition[condition]
        summaries[condition] = {
            "n_source_values":len(values),
            "first_value_at_first_recorded_time":values[0],
            "last_value_at_last_recorded_time":values[-1],
            "minimum_value":min(values),
            "maximum_value":max(values),
            "n_values_above_one":sum(value > 1 for value in values),
            "n_adjacent_increases":sum(right > left for left, right in zip(values, values[1:])),
        }
    return {
        "n_time_coordinates":len(coordinates),
        "time_grid_unique":len(set(coordinates)) == len(coordinates),
        "time_grid_strictly_increasing":True,
        "time_range_seconds":[min(coordinates),max(coordinates)],
        "time_step_range_seconds":[round(min(steps),6),round(max(steps),6)],
        "zero_second_coordinate_present":0 in coordinates,
        "first_recorded_time_seconds":coordinates[0],
        "condition_profiles":summaries,
        "interpretation_limit":"Structural source-grid facts only. The workbook has no zero-second row and does not label the first recorded point as the measured initial instant; no zero-time value was inserted, no profile was smoothed or fit, and adjacent increases are retained as source values rather than edited away.",
    }


def _profile_half_response_crossing_check(curves, panel_j_values):
    """Bracket raw sigma/sigma0 half-response crossings without interpolation."""
    threshold = 0.5
    times_by_row = {}
    profiles = {}
    for item in curves:
        row = int(item["cell"][1:])
        if item["column_role"] == "source_time_coordinate":
            times_by_row[row] = item["value"]
        elif item["column_role"] == "source_response_profile":
            profiles.setdefault(item["source_condition"], {})[row] = item
    panel_j_means = {}
    for condition in SUPPLEMENTARY_PANEL_J_CONTEXT["condition_headers_in_sheet_order"]:
        selected = [item["value"] for item in panel_j_values
                    if item["source_condition"] == condition]
        if selected:
            panel_j_means[condition] = statistics.mean(selected)
    by_condition = {}
    for condition, response_rows in profiles.items():
        ordered_rows = sorted(response_rows)
        downward, upward = [], []
        for left_row, right_row in zip(ordered_rows, ordered_rows[1:]):
            left = response_rows[left_row]
            right = response_rows[right_row]
            left_value, right_value = left["value"], right["value"]
            crossing = {
                "source_cells":[left["cell"],right["cell"]],
                "time_interval_seconds":[times_by_row[left_row],times_by_row[right_row]],
                "response_values":[left_value,right_value],
            }
            if left_value >= threshold and right_value < threshold:
                downward.append(crossing)
            elif left_value < threshold and right_value >= threshold:
                upward.append(crossing)
        first_downward = downward[0] if downward else None
        summary_mean = panel_j_means.get(condition)
        if first_downward is None or summary_mean is None:
            mean_position = "not_comparable"
            gap_seconds = None
        else:
            lower, upper = first_downward["time_interval_seconds"]
            if lower <= summary_mean <= upper:
                mean_position, gap_seconds = "within_observed_bracket", 0.0
            elif summary_mean < lower:
                mean_position, gap_seconds = "before_observed_bracket", lower-summary_mean
            else:
                mean_position, gap_seconds = "after_observed_bracket", summary_mean-upper
        by_condition[condition] = {
            "threshold_response":threshold,
            "response_unit":"dimensionless σ/σ₀",
            "n_observed_downward_crossings":len(downward),
            "n_observed_upward_crossings":len(upward),
            "first_downward_crossing_bracket":first_downward,
            "sup10j_mean_seconds":summary_mean,
            "sup10j_mean_position_vs_first_bracket":mean_position,
            "gap_from_sup10j_mean_to_first_bracket_seconds":gap_seconds,
        }
    return {
        "source_profile_panel":"Supplementary Fig. 10I",
        "summary_panel":"Supplementary Fig. 10J",
        "condition_checks":by_condition,
        "crossing_rule":"Record every adjacent raw response transition across 0.5; use the first downward-crossing time interval only. Do not interpolate, smooth, or fit.",
        "comparability_status":"descriptive_scale_check_only_profile_run_and_aggregation_mapping_unknown",
        "interpretation_limit":"The source profile first-crossing brackets and Fig. 10J source-cell means can be compared only as panel-level timing scales. The profile caption supplies no run/summary hierarchy, and no IDs map a profile to any of the three independent Fig. 10J values. This does not establish shared observations, replicate matching, or an estimated half-time.",
        "values_enter_observation_intake":False,
        "values_enter_mechanical_fit":False,
    }


def _dataset(endpoints,filename):
    artifact = {"artifact_id":"guo-niche-workbook", "uri":WORKBOOK_URL, "license":LICENSE_NOTE,
        "sha256":WORKBOOK_SHA256, "retrieved_on":"2026-10-09", "local_path":filename}
    records = []
    for cell in endpoints:
        if cell["unit_status"] != "caption_reported":
            continue
        records.append({"schema_version":1,"record_id":cell["record_id"],"evidence_status":"author_reported_summary",
            "species":"mouse", "stage_track":"postimplantation_embryonic",
            "developmental_interval":{"label":"E3.5 mouse embryo entry; elapsed culture outcome, in-vivo ending age unqualified",
                "time_unit":"embryonic_day", "start":3.5, "end":None, "stage_source_artifact_id":artifact["artifact_id"]},
            "model_system":{"kind":"intact_organism", "label":"Ex vivo mouse embryos in source niche condition " + cell["source_condition"]},
            "assay":{"name":"Source " + cell["sheet"] + " developmental outcome", "endpoint":cell["quantity"], "unit":"%", "measurement_role":"morphology"},
            "independent_unit":{"kind":"not_reported", "id":None, "parent_id":None,
                "hierarchy_note":"Worksheet rows lack explicit embryo/run/material identities; cross-panel pairing and starting-cohort denominators are unqualified."},
            "observation":{"value":cell["value"], "measurement_time":cell["measurement_time"],
                "measurement_time_unit":"IVC day", "comparator_id":None, "replicate_role":"not_reported"},
            "source":{k:artifact[k] for k in ("artifact_id","uri","license","sha256","retrieved_on")},
            "limitations":[f"Original source locator: {cell['sheet']}!{cell['cell']}; condition header {cell['cell'][0]}1; numeric lexeme {cell['numeric_text']}.",
                "Figure 4E/F caption reports n ≥ 4 but does not define whether n counts embryos, culture experiments, or another unit; exact group n remains unqualified.",
                "The selected workbook contains 7/4/5 percentage cells by condition, but these cell counts are not assumed to be biological n or independent-unit counts; embryo numerators/denominators and experiment mapping are absent.",
                "Matching row positions and condition titles do not establish pairing with mechanical measurements or later outcomes.",
                "Source condition codes identify the published comparison; they are not a preparation recipe or operating recommendation.",
                "Culture days are not silently added to embryonic age; mouse progression does not establish continuous human development."]})
    return validate_dataset({"schema_version":1,"dataset_id":"guo-niche-development-candidate",
        "title":"Candidate Figure 4E/F mouse developmental percentages",
        "source_revision":{"revision_id":"guo-niche-agent-audit-2026-10-09", "citation":"Guo et al. (2026), 3D biomimetic niche modulates embryo development in vitro. Nature Communications 17, 1279.",
            "source_kind":"peer_reviewed_animal", "source_url":ARTICLE_URL, "review_status":"candidate", "reviewer":"", "reviewed_on":None, "review_note":""},
        "artifacts":[artifact], "observations":records, "transitions":[]})


def audit_guo_source(workbook_path: Path, output: Path):
    path = Path(workbook_path)
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():
        raise InputError("Workbook must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000 or sha256(raw) != WORKBOOK_SHA256:
        raise InputError("Workbook size/hash differs from the inspected Guo revision; a new audit is required")
    supplement_path = path.parent / "guo-supplementary-information.pdf"
    supplementary_snapshot_verified = False
    if supplement_path.exists() or supplement_path.is_symlink():
        if supplement_path.is_symlink() or not supplement_path.is_file():
            raise InputError("Supplementary information snapshot must be a regular nonsymlink file")
        with supplement_path.open("rb") as stream:
            supplement_raw = stream.read(SUPPLEMENTARY_INFO_SIZE_BYTES + 1)
        if (len(supplement_raw) != SUPPLEMENTARY_INFO_SIZE_BYTES
                or sha256(supplement_raw) != SUPPLEMENTARY_INFO_SHA256):
            raise InputError("Supplementary information snapshot size/hash differs from the inspected revision")
        supplementary_snapshot_verified = True
    article_path = path.parent / "guo-niche.html"
    article_snapshot_verified = False
    if article_path.exists() or article_path.is_symlink():
        if article_path.is_symlink() or not article_path.is_file():
            raise InputError("Article text snapshot must be a regular nonsymlink file")
        with article_path.open("rb") as stream:
            article_raw = stream.read(ARTICLE_HTML_SIZE_BYTES + 1)
        if (len(article_raw) != ARTICLE_HTML_SIZE_BYTES
                or sha256(article_raw) != ARTICLE_HTML_SHA256):
            raise InputError("Article text snapshot size/hash differs from the inspected revision")
        article_snapshot_verified = True
    sheets = {name:_figure_cells(raw,name) for name in [p[0] for p in PANELS]+["Sup 10 I","Sup10J"]}
    endpoints,curves = _extract(sheets)
    mechanical_value_overlaps = _mechanical_value_overlaps(endpoints)
    supplementary_panel_j_values = _extract_supplementary_panel_j(sheets["Sup10J"])
    supplementary_panel_j_summaries = _summarize_supplementary_panel_j(supplementary_panel_j_values)
    mechanical_40mg_cross_panel_scale = _summarize_40mg_cross_panel_scale(
        endpoints, supplementary_panel_j_values)
    dataset = _dataset(endpoints,path.name)
    development_cell_counts = {}
    for sheet in ("Fig4E", "Fig4F"):
        development_cell_counts[sheet] = {
            condition: sum(1 for endpoint in endpoints
                           if endpoint["sheet"] == sheet and endpoint["source_condition"] == condition)
            for condition in ("40-MG", "40-MGT", "40-MGN")
        }
    outcome_n_qualification = {
        "panels":["Fig4E", "Fig4F"],
        "caption_n_statement":"n ≥ 4",
        "caption_locator":"Figure 4 caption, panels E/F",
        "minimum_n_stated":4,
        "exact_n_by_condition":None,
        "n_unit_definition":"not specified; the caption does not say whether n counts individual embryos, culture experiments, or another unit",
        "populated_percentage_cell_counts_by_condition":development_cell_counts,
        "cell_count_semantics":"Counts of percentage-valued source cells in the selected workbook only; not verified biological n or independent replicate counts.",
        "embryo_numerators_and_starting_denominators":"not reported in the selected source workbook or qualified from the inspected article text"
    }
    mechanical_axis_qualification = []
    for panel, context in MECHANICAL_AXIS_CONTEXT.items():
        mechanical_axis_qualification.append({
            "panel":panel,
            "source_locator":"Figure 4, panel axis and caption",
            **context,
            "unit_status":"publisher_figure_axis_reported",
            "source_replicate_count_scope":"caption wording only; unit hierarchy and cross-panel identities are not implied"
        })
    mechanical_measurement_context = MECHANICAL_MEASUREMENT_CONTEXT
    supplementary_panel_j_qualification = {
        **SUPPLEMENTARY_PANEL_J_CONTEXT,
        "n_source_cells":len(supplementary_panel_j_values),
        "n_source_values_by_condition":{
            condition:sum(1 for item in supplementary_panel_j_values if item["source_condition"] == condition)
            for condition in SUPPLEMENTARY_PANEL_J_CONTEXT["condition_headers_in_sheet_order"]
        },
        "derived_summary_reconstruction":supplementary_panel_j_summaries,
        "values_enter_observation_intake":False,
        "values_enter_mechanical_fit":False,
    }
    profile_times = [item["value"] for item in curves
                     if item["column_role"] == "source_time_coordinate"]
    supplementary_profile_half_response_check = _profile_half_response_crossing_check(
        curves, supplementary_panel_j_values)
    supplementary_profile_qualification = {
        **SUPPLEMENTARY_PROFILE_CONTEXT,
        "source_time_coordinate_count":len(profile_times),
        "source_time_coordinate_min_seconds":min(profile_times) if profile_times else None,
        "source_time_coordinate_max_seconds":max(profile_times) if profile_times else None,
        "n_source_response_columns":len({item["source_condition"] for item in curves
            if item["column_role"] == "source_response_profile"}),
        "profile_grid_qualification":_profile_grid_qualification(curves),
        "profiles_enter_observation_intake":False,
        "profiles_enter_mechanical_fit":False
    }
    qualification = {"schema_version":1, "review_status":"candidate", "human_review":"pending",
        "n_endpoint_cells":len(endpoints), "n_developmental_percentage_cells":len(dataset["observations"]),
        "n_profile_cells":len(curves), "n_supplementary_panel_j_summary_cells":len(supplementary_panel_j_values),
        "n_verified_physical_unit_ids":0,
        "starting_cohort_denominators":None, "cross_panel_pairing":"not_established",
        "developmental_outcome_n_qualification":outcome_n_qualification,
        "mechanical_panel_axis_qualification":mechanical_axis_qualification,
        "mechanical_measurement_context":mechanical_measurement_context,
        "mechanical_panel_exact_value_overlaps":mechanical_value_overlaps,
        "mechanical_40mg_cross_panel_scale_check":mechanical_40mg_cross_panel_scale,
        "supplementary_profile_qualification":supplementary_profile_qualification,
        "supplementary_panel_j_qualification":supplementary_panel_j_qualification,
        "supplementary_profile_half_response_crossing_check":supplementary_profile_half_response_check,
        "mechanical_units_loading_normalization":"Figure 4 axes report s for Fig4A/D and Pa for Fig4C (log axis); Methods define loading/normalization context for rheometer and nanoindentation relaxation, but panel-specific modulus mapping, hierarchy and cross-panel identities remain unqualified, so these values stay excluded from observation intake",
        "stiffness_equivalence":"not_established_by_nonsignificant_difference",
        "missing":["Physical embryo/run/material IDs and experiment/subsample hierarchy across panels.",
            "Original developmental numerators, starting denominators, attrition and exclusions.",
            "Panel-specific mapping of the modulus methods, material/run hierarchy and linkage to developmental outcomes.",
            "Experiment IDs and cross-condition pairing for Sup10J values; the caption defines n=3 independent experiments but the workbook supplies no IDs.",
            "Independent-unit hierarchy and aggregation for nanoindentation values and Sup 10 I profiles; source data identify no sample/run IDs or profile-to-summary mapping.",
            "Assay assignment for Figure 4A; its caption and Results text name no instrument, while the Methods describe both rheometry and nanoindentation protocols.",
            "Protocol/run reconciliation for the approximately eightfold 40-MG half-time scale gap between Figure 4A/D and Supplementary Fig. 10J.",
            "Point-to-profile mapping between Sup 10 I traces and Sup10J half-time values.",
            "Source mapping for any exact mechanical value overlap across panels; no specimen/run IDs determine whether matches are shared, remeasured, reused or coincident.",
            "Reviewed equivalence margin, confound controls, source-specific rights and frozen analysis plan."],
        "mechanical_fit_performed":False,"causal_effect_estimated":False,"biological_assay_performed":False}
    manifest = {"schema_version":1,"source_url":WORKBOOK_URL,"filename":path.name,"sha256":sha256(raw),"size_bytes":len(raw),
        "selected_sheets":list(sheets),"source_modified":False,"external_source_required":True,
        "linked_context_source":{"source_url":SUPPLEMENTARY_INFO_URL,
            "filename":"41467_2025_68039_MOESM1_ESM.pdf","sha256":SUPPLEMENTARY_INFO_SHA256,
            "size_bytes":SUPPLEMENTARY_INFO_SIZE_BYTES,
            "reviewed_locator":"Supplementary Fig. 10I/J, PDF pp. 18-19",
            "local_snapshot_path":"artifacts/feasibility-strategy-2026-10-09/guo-supplementary-information.pdf",
            "local_snapshot_hash_verified_during_audit":supplementary_snapshot_verified},
        "linked_article_context_source":{"source_url":ARTICLE_URL,
            "filename":"guo-niche.html","sha256":ARTICLE_HTML_SHA256,
            "size_bytes":ARTICLE_HTML_SIZE_BYTES,
            "reviewed_locators":["Results > Stress relaxation regulates embryonic development in vitro",
                "Figure 4 caption, panels A and D","Methods > Rheological test",
                "Methods > Nanoindentation test"],
            "local_snapshot_path":"artifacts/feasibility-strategy-2026-10-09/guo-niche.html",
            "local_snapshot_hash_verified_during_audit":article_snapshot_verified}}
    if mechanical_value_overlaps:
        overlap_summary = "; ".join(
            f"{item['left_panel']} {item['left_condition']} vs {item['right_panel']} {item['right_condition']} "
            f"({item['n_matching_lexemes']} lexemes; {item['n_left_source_cells']} and {item['n_right_source_cells']} cells)"
            for item in mechanical_value_overlaps
        )
        overlap_note = (
            "Exact numeric-lexeme overlaps found: " + overlap_summary + ". This is a source-level collision check only; "
            "no specimen/run IDs establish whether values are shared, remeasured, reused or coincident, so it does not establish pairing or independent replication."
        )
    else:
        overlap_note = (
            "No exact numeric-lexeme overlap was found across the inspected mechanical panel-condition groups; "
            "this does not establish that their specimens or runs are independent."
        )
    profile_grid = supplementary_profile_qualification["profile_grid_qualification"]
    profile_first_values = ", ".join(
        f"{condition}={summary['first_value_at_first_recorded_time']:g}"
        for condition, summary in profile_grid["condition_profiles"].items()
    )
    profile_increase_counts = ", ".join(
        f"{condition}={summary['n_adjacent_increases']}"
        for condition, summary in profile_grid["condition_profiles"].items()
    )
    profile_grid_note = (
        f"The Sup 10 I workbook grid contains {profile_grid['n_time_coordinates']} unique increasing time coordinates "
        f"from {profile_grid['time_range_seconds'][0]:g} to {profile_grid['time_range_seconds'][1]:g} s; "
        f"it has no zero-second row. First-recorded response values are {profile_first_values}; "
        f"raw adjacent increases by condition are {profile_increase_counts}. No zero-time point was inserted and no curve was smoothed or fit."
    )
    article_snapshot_note = (
        f"The linked article text snapshot guo-niche.html was hash-verified ({ARTICLE_HTML_SHA256}); "
        "reviewed locators were the stress-relaxation Results paragraph, Figure 4 caption panels A/D, "
        "and the Rheological test and Nanoindentation test Methods sections."
        if article_snapshot_verified else
        "The linked article text snapshot was not present beside this workbook, so its reviewed method context "
        "was not byte-verified in this audit run."
    )
    crossing_parts = []
    for condition in ("40-MG", "40-MGT", "40-MGN"):
        result = supplementary_profile_half_response_check["condition_checks"][condition]
        bracket = result["first_downward_crossing_bracket"]
        if bracket is None:
            crossing_parts.append(f"{condition}=no observed downward crossing")
            continue
        low, high = bracket["time_interval_seconds"]
        crossing_parts.append(
            f"{condition}=[{low:.3f}, {high:.3f}] s, Sup10J mean="
            f"{result['sup10j_mean_seconds']:.3f} s, gap="
            f"{result['gap_from_sup10j_mean_to_first_bracket_seconds']:.3f} s"
        )
    profile_half_response_note = (
        "Raw Sup 10 I first-downward brackets across σ/σ₀=0.5, compared descriptively with Sup10J means: "
        + "; ".join(crossing_parts)
        + ". These are adjacent source coordinates with no interpolation; the check does not map profile traces "
        "to individual Fig. 10J experiments or establish a fitted half-time."
    )
    cross_panel_scale_note = (
        "Cross-panel 40-MG scale check (descriptive source-cell means): "
        f"Figure 4A={mechanical_40mg_cross_panel_scale['descriptive_summaries']['Figure 4A']['mean_seconds']:.3f} s, "
        f"Figure 4D={mechanical_40mg_cross_panel_scale['descriptive_summaries']['Figure 4D']['mean_seconds']:.3f} s, "
        f"Supplementary Fig. 10J={mechanical_40mg_cross_panel_scale['descriptive_summaries']['Supplementary Fig. 10J']['mean_seconds']:.3f} s; "
        f"the 10J mean is {mechanical_40mg_cross_panel_scale['supplementary_10j_mean_to_figure_4_mean_ratios']['vs_figure_4a']:.1f}x and "
        f"{mechanical_40mg_cross_panel_scale['supplementary_10j_mean_to_figure_4_mean_ratios']['vs_figure_4d']:.1f}x the Figure 4 means. "
        +
        ("The nonoverlapping source ranges trigger a protocol/run reconciliation flag, not a direct contradiction: "
         if not any(mechanical_40mg_cross_panel_scale["supplementary_10j_range_overlap_with_figure_4"].values())
         else "The source ranges are not fully separated, so no strong scale-separation flag is raised: ") +
        "Figure 4A method linkage is unresolved, Figure 4D names nanoindentation, and 10J names rheometer. "
        "No mechanical values enter biological intake or fitting."
    )
    report = "\n".join(["# Niche mechanics and developmental-source audit", "", "AI-assisted candidate transcription; human review pending.",
        f"{len(endpoints)} endpoint cells; {len(dataset['observations'])} developmental-percentage records; {len(curves)} profile cells; {len(supplementary_panel_j_values)} Sup10J summary cells.",
        "Original scalar lexemes/locators are retained. Figure 4 axes report stress-relaxation half-time in seconds (Fig4A/D) and Young's modulus in Pa (Fig4C; logarithmic axis). Methods specify a fixed-strain, normalized rheometer relaxation test and a load/hold/unload nanoindentation test; Figure 4C's caption-to-method mapping and mechanical unit hierarchy remain unresolved, so mechanical values stay out of observation intake.",
        "The Figure 4A caption calls its endpoint a characteristic relaxation timescale for E5.5 decidua and 40-MG but names no assay or instrument; the Results paragraph likewise does not assign the method. Figure 4D explicitly names nanoindentation, while Supplementary Fig. 10J explicitly names a rheometer. Keep Figure 4A's method assignment open.",
        article_snapshot_note,
        profile_half_response_note,
        "Supplementary Fig. 10I and workbook sheet Sup 10 I align by panel title and condition headers: the profile uses rheometer stress, plotted as σ/σ₀ against time in seconds. The adjacent Fig. 10J caption states n=3 independent experiments for the half-time summary; it does not assign those repeats to profile rows or identify the curves as runs versus means, so the 800 profile cells remain outside observation intake and fitting.",
        "The Sup10J workbook tab contains three half-time values for each of 40-MG, 40-MGT, and 40-MGN, matching Fig. 10J's caption count of n=3 independent experiments per condition. Recalculated means and sample SDs are retained as arithmetic checks; experiment IDs, row-wise pairing across conditions, and links to profile traces are absent, so no mechanical values enter biological intake or fitting.",
        cross_panel_scale_note,
        profile_grid_note,
        overlap_note,
        "Figure 4E/F's caption states n ≥ 4 but does not define the unit counted by n or give exact group n. The workbook contains 7/4/5 percentage cells per condition; these are source-cell counts, not verified biological denominators or independent replicate counts.",
        "Cross-panel correlation, mechanical calibration, stiffness equivalence and causal estimates are not performed.",
        "",f"[Guo et al., 2026]({ARTICLE_URL}). Article CC BY-NC-ND 4.0; workbook-specific reuse review pending. External source is untouched; local scalar inventories are reformatted candidate transcriptions.",
        "", "## Required qualification", "", *["- "+v for v in qualification["missing"]], ""])
    return publish_bundle(output,kind="niche_mechanics_development_source_audit",input_raw=raw,
        files={"input_source_manifest.json":json_bytes(manifest),"input_dataset.json":json_bytes(dataset),
            "endpoint_cells.csv":csv_bytes(list(endpoints[0]),endpoints),"profile_cells.csv":csv_bytes(list(curves[0]),curves),
            "supplementary_panel_j_cells.csv":csv_bytes(list(supplementary_panel_j_values[0]),supplementary_panel_j_values),
            "qualification.json":json_bytes(qualification),"REPORT.md":report.encode()},
        metadata={"source_review_status":"candidate","biological_assay_performed":False,"mechanical_fit_performed":False,"causal_effect_estimated":False})
