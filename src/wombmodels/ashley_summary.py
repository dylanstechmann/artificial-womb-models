"""Recompute Ashley et al. 2022 endpoint summaries from the five source labels."""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

from .artifacts import InputError
from .ashley_source import audit_ashley_source_cells
from .faure_bardon_source import _workbook_cells

ABSOLUTE_TOLERANCE = 1e-12
SAMPLE_LABELS = ("252", "254", "275", "343", "402")
SUMMARY_GROUPS = {
    "25d_maternal_loss": {
        "record_prefix": "ashley2022-25d-maternal-loss-p",
        "summary_cells": {"mean": "G6", "sample_sd": "H6", "sem": "I6"},
    },
    "25d_metabolized": {
        "record_prefix": "ashley2022-25d-metabolized-p",
        "summary_cells": {"mean": "G7", "sample_sd": "H7", "sem": "I7"},
    },
    "25d_fetal_appearance": {
        "record_prefix": "ashley2022-25d-fetal-transfer-p",
        "summary_cells": {"mean": "R6", "sample_sd": "S6", "sem": "T6"},
    },
    "25d_placental_retention": {
        "record_prefix": "ashley2022-25d-placental-storage-p",
        "summary_cells": {"mean": "R7", "sample_sd": "S7", "sem": "T7"},
    },
    "125d_maternal": {
        "record_prefix": "ashley2022-125d-maternal-p",
        "summary_cells": {"mean": "G26", "sample_sd": "H26", "sem": "I26"},
    },
    "125d_fetal": {
        "record_prefix": "ashley2022-125d-fetal-p",
        "summary_cells": {"mean": "G34", "sample_sd": "H34", "sem": "I34"},
    },
}


def _number(value: object, *, label: str) -> float:
    if isinstance(value, bool):
        raise InputError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise InputError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise InputError(f"{label} must be finite")
    return result


def derive_ashley_endpoint_summaries(repository_root: Path) -> dict:
    """Recompute the six included group summaries and five-label closure checks.

    The source-cell audit must pass first. Derived components are compared to
    their workbook summary cells as arithmetic consistency checks only.
    """
    root = Path(repository_root)
    source_audit = audit_ashley_source_cells(root)
    source_manifest_path = root / "artifacts/ashley-2022-vitamin-d-perfusion/SOURCE.json"
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    workbook_path = root / manifest["local_path"]
    cells = _workbook_cells(workbook_path.read_bytes(), expected_sheet="Sheet1")
    candidate_path = root / "config/observations/ashley_2022_vitamin_d_perfusion_candidate.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    observations = candidate["observations"]

    derived = {}
    endpoint_values: dict[str, dict[str, float]] = {}
    for name, spec in SUMMARY_GROUPS.items():
        selected = [item for item in observations
                    if isinstance(item, dict)
                    and isinstance(item.get("record_id"), str)
                    and item["record_id"].startswith(spec["record_prefix"])]
        values_by_label = {}
        for item in selected:
            sample_label = item["record_id"][len(spec["record_prefix"]):]
            if sample_label not in SAMPLE_LABELS or sample_label in values_by_label:
                raise InputError(f"Duplicate or unexpected source label in summary group {name}")
            values_by_label[sample_label] = _number(
                item.get("observation", {}).get("value"), label=f"{name} {sample_label}")
        if set(values_by_label) != set(SAMPLE_LABELS):
            raise InputError(f"Summary group {name} must contain each of five labels exactly once")
        values = [values_by_label[label] for label in SAMPLE_LABELS]
        mean = statistics.mean(values)
        sample_sd = statistics.stdev(values)
        sem = sample_sd / math.sqrt(len(values))
        actual = {key: _number(cells[cell]["value"], label=f"{name} {cell}")
                  for key, cell in spec["summary_cells"].items()}
        errors = {key: abs(value - actual[key])
                  for key, value in (("mean", mean), ("sample_sd", sample_sd), ("sem", sem))}
        if any(error > ABSOLUTE_TOLERANCE for error in errors.values()):
            raise InputError(f"Recomputed summary differs from workbook for {name}")
        derived[name] = {
            "n": len(values),
            "values_by_source_label": values_by_label,
            "recomputed": {"mean": mean, "sample_sd": sample_sd, "sem": sem},
            "workbook_cells": spec["summary_cells"],
            "workbook_summary": actual,
            "absolute_error": errors,
            "matched_within_abs_tolerance": ABSOLUTE_TOLERANCE,
        }
        endpoint_values[name] = values_by_label

    closure = {}
    for label in SAMPLE_LABELS:
        maternal_loss = endpoint_values["25d_maternal_loss"][label]
        components = (
            endpoint_values["25d_metabolized"][label]
            + endpoint_values["25d_placental_retention"][label]
            + endpoint_values["25d_fetal_appearance"][label]
        )
        residual = maternal_loss - components
        if abs(residual) > ABSOLUTE_TOLERANCE:
            raise InputError(f"25(OH)D3 source components do not close for label {label}")
        closure[label] = {
            "maternal_loss": maternal_loss,
            "sum_metabolized_retained_fetal_appearance": components,
            "residual": residual,
            "matches_within_abs_tolerance": ABSOLUTE_TOLERANCE,
        }

    return {
        "status": "pass",
        "source_workbook_sha256": source_audit["source_workbook_sha256"],
        "candidate_dataset_sha256": source_audit["candidate_dataset_sha256"],
        "summary_groups_checked": len(derived),
        "summary_cells_checked": len(derived) * 3,
        "summaries": derived,
        "vitamin_d_25d_within_label_partition_check": closure,
        "partition_check_is_independent_validation": False,
        "article_group_summary_reconciliation_assessed": False,
        "observation_values_added": False,
        "dimensional_transport_fit_assessed": False,
        "human_source_review_complete": False,
    }
