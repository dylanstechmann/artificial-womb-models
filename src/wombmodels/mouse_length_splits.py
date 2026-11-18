"""Audit held-out group coverage in the pinned mouse embryo length candidate."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .artifacts import InputError, json_bytes, publish_bundle, read_json, sha256
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
        partitions[context][observation["measurement_time"]].append(record["record_id"])

    groups, holdouts = [], []
    for (condition, axis, clock, unit), measurements in sorted(partitions.items()):
        times = sorted(measurements)
        group_ids = {time: f"{condition}/{axis}/{time:g}" for time in times}
        for time in times:
            record_ids = measurements[time]
            groups.append({
                "group_id": group_ids[time], "condition": condition, "measurement_axis": axis,
                "source_time": time, "source_time_unit": clock, "length_unit": unit,
                "source_measurement_count": len(record_ids), "observation_ids": record_ids,
            })
            training_times = [other for other in times if other != time]
            if len(training_times) < 2:
                coverage = "insufficient_training_times"
            elif training_times[0] < time < training_times[-1]:
                coverage = "interpolation"
            else:
                coverage = "extrapolation"
            holdouts.append({
                "held_out_group_id": group_ids[time],
                "training_group_ids": [group_ids[other] for other in training_times],
                "training_times": training_times,
                "time_coverage": coverage,
            })
    return groups, holdouts


def audit_mouse_length_splits(dataset_path: Path, output: Path) -> dict:
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
    }
    lines = [
        "# Mouse embryo length holdout audit", "",
        f"The {revision['review_status']} data card contains {len(records)} source measurements and "
        f"{summary['records_with_reported_embryo_id']} records with reported embryo IDs.",
        "Specimen independence between held-out and training groups is unresolved. "
        "This audit describes time coverage for a future benchmark.", "",
        "| Condition | Axis | Held-out time | Source clock | Measurements | Training times | Coverage |",
        "| --- | --- | ---: | --- | ---: | --- | --- |",
    ]
    for group, holdout in zip(groups, holdouts):
        training = ", ".join(f"{time:g}" for time in holdout["training_times"]) or "—"
        coverage = holdout["time_coverage"].replace("_", " ")
        lines.append(f"| {group['condition']} | {group['measurement_axis']} | {group['source_time']:g} | "
                     f"{group['source_time_unit']} | {group['source_measurement_count']} | {training} | {coverage} |")
    files = {
        "input_dataset.json": raw,
        "splits.json": json_bytes({**summary, "groups": groups, "holdouts": holdouts}),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    return publish_bundle(output, kind="mouse_embryo_length_split_audit", input_raw=raw,
                          files=files, metadata=summary)
