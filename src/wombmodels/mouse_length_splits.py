"""Audit held-out mouse embryo length groups and compare their reported means."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from statistics import fmean

from .artifacts import InputError, json_bytes, publish_bundle, read_json, reproduction_plan, sha256
from .hori_source import _figure_cells
from .mathiesen_source import _read_pinned
from .observations import validate_dataset

DATASET_SHA256 = "2d5890793c4d1bce1f29bbec42f1760b06ac7fd70954b06835ceb97abeae1c94"
CONDITIONS = {"intact_organism": "in utero", "embryo_model": "ex utero"}
AXES = {
    "Embryonic length along the antero-posterior axis": "antero-posterior",
    "Embryonic length along the crown-rump axis": "crown-rump",
}


def _group_holdouts(records: list[dict]) -> tuple[list[dict], list[dict]]:
    partitions = defaultdict(lambda: defaultdict(list))
    for record in records:
        assay = record["assay"]
        observation = record["observation"]
        axis_label = assay["endpoint"].partition(" (source grouping:")[0]
        condition = CONDITIONS[record["model_system"]["kind"]]
        context = (condition, AXES[axis_label], observation["measurement_time_unit"], assay["unit"])
        partitions[context][observation["measurement_time"]].append(record)

    groups, holdouts = [], []
    for (condition, axis, clock, unit), measurements in sorted(partitions.items()):
        times = sorted(measurements)
        group_ids = {time: f"{condition}/{axis}/{time:g}" for time in times}
        means = {time: fmean(row["observation"]["value"] for row in rows)
                 for time, rows in measurements.items()}
        for index, time in enumerate(times):
            record_ids = [row["record_id"] for row in measurements[time]]
            groups.append({
                "group_id": group_ids[time], "condition": condition, "measurement_axis": axis,
                "source_time": time, "source_time_unit": clock, "length_unit": unit,
                "source_measurement_count": len(record_ids), "observation_ids": record_ids,
                "mean_length": means[time],
            })
            training_times = [other for other in times if other != time]
            comparison = None
            if len(training_times) < 2:
                coverage = "insufficient_training_times"
            elif training_times[0] < time < training_times[-1]:
                coverage = "interpolation"
                left, right = times[index - 1], times[index + 1]
                fraction = (time - left) / (right - left)
                reference = means[left] + fraction * (means[right] - means[left])
                comparison = {
                    "earlier_group_id": group_ids[left], "later_group_id": group_ids[right],
                    "fraction_of_time_interval": fraction, "interpolated_mean_length": reference,
                    "observed_minus_interpolated": means[time] - reference,
                }
            else:
                coverage = "extrapolation"
            holdouts.append({
                "held_out_group_id": group_ids[time],
                "training_group_ids": [group_ids[other] for other in training_times],
                "training_times": training_times,
                "time_coverage": coverage,
                "group_mean_comparison": comparison,
            })
    return groups, holdouts


def _match_panel_cells(cells: dict, records: list[dict]) -> int:
    remaining = {address for address, (token, kind, _) in cells.items()
                 if kind == "numeric" and token is not None}
    for record in records:
        locator = record["source_locator"]
        match = re.fullmatch(r"Panel e!([A-Z]+)([1-9][0-9]*); row label '([^']+)'", locator)
        if match is None:
            raise InputError(f"Unrecognized Panel e locator: {locator}")
        column, row, row_label = match.groups()
        address = column + row
        if address not in remaining:
            raise InputError(f"Missing or repeated numeric source cell at {address}")
        remaining.remove(address)
        group_label = record["model_system"]["label"].partition("; source group ")[2]
        if cells.get(column + "2", (None,))[0] != group_label:
            raise InputError(f"Source group label differs for {address}")
        if cells.get("A" + row, (None,))[0] != row_label:
            raise InputError(f"Source row label differs for {address}")
        try:
            source_length = float(cells[address][0])
        except (ValueError, OverflowError) as exc:
            raise InputError(f"Invalid source length at {address}") from exc
        if source_length != record["observation"]["value"]:
            raise InputError(f"Source length differs for {address}")
    if remaining:
        raise InputError("Panel e contains numeric cells missing from the candidate card")
    return len(records)


def _verify_workbook(path: Path, dataset: dict) -> dict:
    digest = dataset["artifacts"][0]["sha256"]
    raw = _read_pinned(path, label="Mouse length workbook", expected_hash=digest, limit=1_000_000)
    matched = _match_panel_cells(_figure_cells(raw, "Panel e"), dataset["observations"])
    return {"status": "matched", "sheet": "Panel e", "matched_cells": matched,
            "numeric_comparison": "binary64 equality", "sha256": digest, "size_bytes": len(raw)}


def audit_mouse_length_splits(dataset_path: Path, output: Path, workbook_path: Path | None = None) -> dict:
    dataset, raw = read_json(dataset_path)
    if sha256(raw) != DATASET_SHA256:
        raise InputError("Mouse embryo length candidate differs from the pinned data card")
    validate_dataset(dataset)
    records = dataset["observations"]
    groups, holdouts = _group_holdouts(records)
    revision = dataset["source_revision"]
    summary = {
        "source_measurement_count": len(records),
        "records_with_reported_embryo_id": sum(
            record["independent_unit"]["id"] is not None for record in records
        ),
        "source_revision_id": revision["revision_id"],
        "source_review_status": revision["review_status"],
        "split_specimen_independence": "unresolved",
        "workbook_verification": (
            _verify_workbook(workbook_path, dataset) if workbook_path is not None
            else {"status": "not_supplied"}
        ),
    }
    lines = [
        "# Mouse embryo length holdout audit", "",
        f"The {revision['review_status']} data card contains {len(records)} source measurements and "
        f"{summary['records_with_reported_embryo_id']} records with reported embryo IDs.",
        "Specimen independence between held-out and training groups is unresolved. "
        "The comparisons use source-group means and their reported times.", "",
        "| Condition | Axis | Held-out time | Source clock | Measurements | Training times | Coverage |",
        "| --- | --- | ---: | --- | ---: | --- | --- |",
    ]
    for group, holdout in zip(groups, holdouts):
        training = ", ".join(f"{time:g}" for time in holdout["training_times"]) or "—"
        coverage = holdout["time_coverage"].replace("_", " ")
        lines.append(f"| {group['condition']} | {group['measurement_axis']} | {group['source_time']:g} | "
                     f"{group['source_time_unit']} | {group['source_measurement_count']} | {training} | {coverage} |")
    lines.extend([
        "", "## Middle group means", "",
        "The reference is the straight line between the nearest earlier and later group means "
        "on the same measurement axis and source clock. The difference is observed minus reference.", "",
        "| Condition | Held-out time | Source clock | Length unit | Linear reference | Observed mean | Difference |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: |",
    ])
    for group, holdout in zip(groups, holdouts):
        comparison = holdout["group_mean_comparison"]
        if comparison is not None:
            lines.append(f"| {group['condition']} | {group['source_time']:g} | {group['source_time_unit']} | "
                         f"{group['length_unit']} | {comparison['interpolated_mean_length']:.1f} | "
                         f"{group['mean_length']:.1f} | {comparison['observed_minus_interpolated']:+.1f} |")
    if workbook_path is not None:
        matched = summary["workbook_verification"]["matched_cells"]
        lines.extend(["", f"Matched the column headers, row labels, and numeric values for all "
                          f"{matched} Panel e measurements against the pinned publisher workbook."])
    files = {
        "input_dataset.json": raw,
        "splits.json": json_bytes({**summary, "groups": groups, "holdouts": holdouts}),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    kind = "mouse_embryo_length_split_audit"
    if workbook_path is not None:
        plan = reproduction_plan(kind, files, summary)
        plan["command"] += " --workbook <publisher-workbook.xlsx>"
        plan["inputs"].append("external publisher workbook with the SHA-256 recorded in splits.json")
        files["reproduction_plan.json"] = json_bytes(plan)
    return publish_bundle(output, kind=kind, input_raw=raw, files=files, metadata=summary)
