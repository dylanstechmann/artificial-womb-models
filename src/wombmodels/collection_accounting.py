"""Dimensionless aggregate-observation counterexamples, without biological fitting."""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE


def _number(value, label, maximum, *, positive=False):
    if type(value) not in (int, float):
        raise InputError(f"{label} must be a finite dimensionless number")
    try:
        valid = math.isfinite(value) and (value == 0 or 1e-12 <= value <= maximum)
    except OverflowError:
        valid = False
    if not valid or (positive and value < 1e-12):
        raise InputError(f"{label} is outside the dimensionless diagnostic domain")
    return float(value)


def _state(value):
    fields = {"donor_concentration", "donor_volume", "receiver_concentration", "receiver_volume"}
    if not isinstance(value, dict) or set(value) != fields:
        raise InputError("A snapshot needs exactly donor/receiver concentration and volume")
    return {field: _number(value[field], field, 1e6, positive=field.endswith("volume")) for field in sorted(fields)}


def validate_accounting(config):
    if not isinstance(config, dict) or set(config) != {"schema_version", "fixture_notice", "cases"}:
        raise InputError("Accounting diagnostic needs exactly schema_version, fixture_notice and cases")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1 or config["fixture_notice"] != NOTICE:
        raise InputError("Accounting diagnostic must retain version 1 and the artificial fixture declaration")
    cases = config["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 50:
        raise InputError("Accounting diagnostic needs 1–50 cases")
    seen, result = set(), []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"case_id", "initial", "final", "supplied_amount", "collected_amount", "observed_tissue_change"}:
            raise InputError("An accounting case has unknown or missing fields")
        identifier = case["case_id"]
        if not isinstance(identifier, str) or not identifier or len(identifier) > 96 or identifier.strip() != identifier or identifier in seen:
            raise InputError("Case IDs must be distinct bounded nonempty text without surrounding whitespace")
        seen.add(identifier)
        tissue = case["observed_tissue_change"]
        result.append({"case_id": identifier, "initial": _state(case["initial"]), "final": _state(case["final"]),
            "supplied_amount": _number(case["supplied_amount"], "supplied_amount", 1e12),
            "collected_amount": _number(case["collected_amount"], "collected_amount", 1e12),
            "observed_tissue_change": None if tissue is None else _number(tissue, "observed_tissue_change", 1e12)})
    return result


def _amounts(state):
    return (Fraction(state["donor_concentration"]) * Fraction(state["donor_volume"]),
            Fraction(state["receiver_concentration"]) * Fraction(state["receiver_volume"]))


def _allocation_witnesses(residual, tissue):
    """Nonnegative net accumulation/conversion/unrecovered allocations, not processes."""
    remaining = residual if tissue is None else residual - tissue
    if remaining < 0:
        return [], "no_nonnegative_partition_under_declared_assumptions"
    if tissue is None:
        candidates = [("all_tissue", residual, Fraction(0), Fraction(0)), ("all_conversion", Fraction(0), residual, Fraction(0)),
                      ("all_unrecovered", Fraction(0), Fraction(0), residual)]
    else:
        candidates = [("observed_tissue_plus_conversion", tissue, remaining, Fraction(0)),
                      ("observed_tissue_plus_unrecovered", tissue, Fraction(0), remaining)]
    distinct, rows = set(), []
    for label, retained, converted, lost in candidates:
        allocation = (retained, converted, lost)
        if allocation not in distinct:
            distinct.add(allocation)
            rows.append({"witness": label, "tissue_inventory_change": float(retained),
                         "conversion": float(converted), "unrecovered": float(lost),
                         "sum_allocated": float(sum(allocation)), "observed_residual": float(residual)})
    return rows, "multiple_indistinguishable_partitions" if len(rows) > 1 else "single_partition_at_nonnegative_boundary"


def collection_accounting(config_path: Path, output: Path):
    config, raw = read_json(config_path)
    cases = validate_accounting(config)
    observations, witness_rows, case_reports = [], [], []
    for case in cases:
        initial, final = case["initial"], case["final"]
        initial_donor, initial_receiver = _amounts(initial)
        final_donor, final_receiver = _amounts(final)
        delta_fluid = final_donor + final_receiver - initial_donor - initial_receiver
        residual = Fraction(case["supplied_amount"]) - Fraction(case["collected_amount"]) - delta_fluid
        uncorrected = Fraction(case["supplied_amount"]) - delta_fluid
        difference = Fraction(final["receiver_concentration"]) - Fraction(initial["receiver_concentration"])
        baseline = Fraction(initial["receiver_concentration"])
        relative = difference / baseline * 100 if baseline > 0 else None
        receiver_delta = final_receiver - initial_receiver
        tissue = None if case["observed_tissue_change"] is None else Fraction(case["observed_tissue_change"])
        witnesses, status = _allocation_witnesses(residual, tissue)
        observations.append({"case_id": case["case_id"], "quantity_units": "dimensionless_fixture_only",
            "initial_donor_amount": float(initial_donor), "final_donor_amount": float(final_donor),
            "initial_receiver_amount": float(initial_receiver), "final_receiver_amount": float(final_receiver),
            "receiver_concentration_change": float(difference), "receiver_concentration_change_percent": None if relative is None else float(relative),
            "relative_change_status": "available" if baseline > 0 else "unavailable_zero_receiver_baseline",
            "receiver_inventory_change": float(receiver_delta), "total_fluid_inventory_change": float(delta_fluid),
            "supplied_amount": case["supplied_amount"], "collected_amount": case["collected_amount"],
            "collection_corrected_residual": float(residual), "residual_if_collection_omitted": float(uncorrected),
            "observed_tissue_change": case["observed_tissue_change"], "allocation_status": status})
        witness_rows.extend({"case_id": case["case_id"], **witness} for witness in witnesses)
        case_reports.append({"case_id": case["case_id"], "allocation_status": status,
            "n_distinct_witnesses": len(witnesses),
            "constraint_rank": 1 if case["observed_tissue_change"] is None else 2,
            "unknown_partition_dimension_before_nonnegative_constraints": 2 if case["observed_tissue_change"] is None else 1,
            "receiver_concentration_increased_without_receiver_inventory_increase": difference > 0 and receiver_delta <= 0,
            "omitting_collection_changes_residual": case["collected_amount"] != 0})
    report = {"schema_version": 1, "fixture_notice": NOTICE, "biological_measurements": False,
        "physiologically_calibrated": False, "parameter_fitting_performed": False, "human_gestation_prediction": False,
        "cases": case_reports,
        "arithmetic": "Exact rational products/balances of validated binary-float inputs; decimal outputs are rounded representations.",
        "accounting_equation": "supplied - collected - delta_fluid = delta_tissue + conversion + unrecovered",
        "linear_constraints": {"fluid_only_matrix": [[1, 1, 1]], "fluid_only_nullspace_basis": [[1, -1, 0], [1, 0, -1]],
            "with_tissue_matrix": [[1, 1, 1], [1, 0, 0]], "with_tissue_nullspace_basis": [[0, 1, -1]],
            "column_order": ["tissue_inventory_change", "conversion", "unrecovered"]},
        "assumptions": ["Two aggregate fluid snapshots use a common tracked-analyte and control-volume definition.",
            "Supplied and collected analyte amounts are explicit totals over the same window, not inferred from concentration alone.",
            "The witness class restricts net tissue accumulation, analyte conversion and unrecovered amounts to nonnegative values.",
            "An observed tissue change, when supplied, is an additional independent observation in this artificial algebra.",
            "No dynamic route, gross turnover, flow history, selectivity, physiological control action or organismal outcome is modeled."],
        "limits": ["Multiple partitions are an exact aggregate-observation ambiguity; no mechanism is fitted or identified.",
            "A negative remainder is incompatible with this restricted partition class; it is not diagnosed as injury, assay error or a specific missing process.",
            "At the nonnegative boundary, a single feasible partition need not imply general structural identifiability or absence of gross turnover.",
            "Receiver inventory change alone does not specify the origin of analyte or a transport rate.",
            "Missing tissue information is never replaced by zero. A zero receiver baseline makes relative concentration change unavailable.",
            "All quantities are artificial and dimensionless. Source biological percentages/units cannot be inserted into this fixture as calibrated data."]}
    lines = ["# Dimensionless collection-accounting diagnostic", "", NOTICE, "",
        "Concentration, inventory, collection and unresolved disappearance remain distinct quantities.", "",
        "| Case | Allocation status | Distinct witnesses |", "| --- | --- | ---: |"]
    lines += [f"| {item['case_id']} | {item['allocation_status']} | {item['n_distinct_witnesses']} |" for item in case_reports]
    lines += ["", "observations.csv records corrected and uncorrected balances; allocation_witnesses.csv records distinct partitions of the same aggregate residual.",
        "", "## Assumptions", "", *["- " + item for item in report["assumptions"]],
        "", "## Limits", "", *["- " + item for item in report["limits"]]]
    return publish_bundle(output, kind="dimensionless_collection_accounting", input_raw=raw,
        files={"input_config.json": raw, "accounting_report.json": json_bytes(report),
            "observations.csv": csv_bytes(list(observations[0]), observations),
            "allocation_witnesses.csv": csv_bytes(["case_id", "witness", "tissue_inventory_change", "conversion", "unrecovered", "sum_allocated", "observed_residual"], witness_rows),
            "REPORT.md": ("\n".join(lines) + "\n").encode()},
        metadata={"biological_measurements": False, "physiologically_calibrated": False,
                  "human_gestation_prediction": False, "parameter_fitting_performed": False})
