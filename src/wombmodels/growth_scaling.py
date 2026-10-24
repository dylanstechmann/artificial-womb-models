"""Growth-paced capacity scaling of a finite exchange surface (dimensionless).

This module models the physical-world structure the T18 design exposed as the
fixture gap: a finite exchange surface whose capacity grows with a sub-linear
size exponent while a growing unit's demand grows with the size itself. When
the capacity margin closes, internal service falls behind while the boundary
flux keeps rising - the "internal delivery lags growth" failure signature,
reproduced mechanistically as an invented dimensionless software world.

A witness world shares the boundary exactly (identical delivered-flux and
bulk-stock series) while differing in internal tissue receipt, demonstrating
that internal distribution efficiency is invisible at the exchange boundary by
construction. No parameter represents physiology, time in days, a device
setpoint or a biological measurement.
"""
from __future__ import annotations

import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number
from .numerics import output_times, require_finite

MAX_OUTPUT_INTERVALS = 50_000
MAX_TOTAL_SUBSTEPS = 4_000_000
MAX_RATE = 100.0
MAX_GROWTH_RATE = 10.0
SUBSTEP_RATE_TARGET = 0.2
DETECTION_TOLERANCE = 0.05


def _geometry(growth, scaling, time):
    """Size, capacity, demand and capacity margin at one dimensionless time."""
    size = 1.0 + growth["linear_rate"] * time
    capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
    demand = scaling["demand_coefficient"] * size
    return size, capacity, demand, capacity / demand


def analytic_crossover(growth, scaling):
    """Analytic size and time at which the capacity margin closes."""
    ratio = scaling["capacity_coefficient"] / scaling["demand_coefficient"]
    exponent = growth["surface_exponent"]
    if ratio <= 1.0:
        return {"crossover_size": 1.0, "crossover_time": 0.0,
                "margin_never_closes": False, "underserved_at_start": True}
    if exponent >= 1.0:
        return {"crossover_size": None, "crossover_time": None,
                "margin_never_closes": True, "underserved_at_start": False}
    size = ratio ** (1.0 / (1.0 - exponent))
    time = (size - 1.0) / growth["linear_rate"] if growth["linear_rate"] > 0 else None
    return {"crossover_size": size, "crossover_time": time,
            "margin_never_closes": time is None, "underserved_at_start": False}


def _validate(config):
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "growth",
                    "scaling", "exchange_world", "internal_world", "internal_witness"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    fields(config["dimensionless_time"], ("duration", "output_step"), "dimensionless_time")
    duration = number(config["dimensionless_time"]["duration"], "duration", 1e-6, 10_000)
    step = number(config["dimensionless_time"]["output_step"], "output_step", 1e-6, duration)
    if duration / step > MAX_OUTPUT_INTERVALS:
        raise InputError(f"At most {MAX_OUTPUT_INTERVALS} output intervals are permitted")

    fields(config["growth"], ("linear_rate", "surface_exponent"), "growth")
    growth = {"linear_rate": number(config["growth"]["linear_rate"], "linear_rate", 0, MAX_GROWTH_RATE),
              "surface_exponent": number(config["growth"]["surface_exponent"], "surface_exponent", 0, 1.0)}
    fields(config["scaling"], ("capacity_coefficient", "demand_coefficient"), "scaling")
    scaling = {"capacity_coefficient": number(config["scaling"]["capacity_coefficient"],
                                               "capacity_coefficient", 1e-6, 1_000),
               "demand_coefficient": number(config["scaling"]["demand_coefficient"],
                                            "demand_coefficient", 1e-6, 1_000)}

    fields(config["exchange_world"], ("serve_rate", "washout", "transfer", "repair"), "exchange_world")
    exchange = {key: number(value, key, 0, MAX_RATE) for key, value in config["exchange_world"].items()}
    worlds = {}
    for label in ("internal_world", "internal_witness"):
        fields(config[label], ("transfer_efficiency", "use"), label)
        worlds[label] = {"transfer_efficiency": number(config[label]["transfer_efficiency"],
                                                      f"{label} transfer_efficiency", 0, 1.0),
                         "use": number(config[label]["use"], f"{label} use", 0, MAX_RATE)}
    return duration, step, growth, scaling, exchange, worlds


def _right_hand_side(time, state, growth, scaling, exchange, worlds):
    """Derivatives of [request, bulk, unserved, tissue_configured, tissue_witness]."""
    _size, capacity, demand, margin = _geometry(growth, scaling, time)
    request, bulk, unserved, tissue_a, tissue_b = state
    delivered = min(demand * request, capacity)
    served = delivered / demand
    d_request = exchange["serve_rate"] * (min(1.0, margin) - request)
    d_bulk = delivered - (exchange["washout"] + exchange["transfer"]) * bulk
    d_unserved = demand * (1.0 - served) - exchange["repair"] * unserved
    d_tissue_a = worlds["internal_world"]["transfer_efficiency"] * exchange["transfer"] * bulk \
        - worlds["internal_world"]["use"] * tissue_a
    d_tissue_b = worlds["internal_witness"]["transfer_efficiency"] * exchange["transfer"] * bulk \
        - worlds["internal_witness"]["use"] * tissue_b
    return [d_request, d_bulk, d_unserved, d_tissue_a, d_tissue_b]


def _rk4_step(time, state, substep, growth, scaling, exchange, worlds):
    first = _right_hand_side(time, state, growth, scaling, exchange, worlds)
    half = [value + 0.5 * substep * rate for value, rate in zip(state, first)]
    second = _right_hand_side(time + 0.5 * substep, half, growth, scaling, exchange, worlds)
    third = _right_hand_side(time + 0.5 * substep,
                             [value + 0.5 * substep * rate for value, rate in zip(state, second)],
                             growth, scaling, exchange, worlds)
    fourth = _right_hand_side(time + substep,
                             [value + substep * rate for value, rate in zip(state, third)],
                             growth, scaling, exchange, worlds)
    return [value + substep * (a + 2 * b + 2 * c + d) / 6.0
            for value, a, b, c, d in zip(state, first, second, third, fourth)]


def _integrate(duration, step, growth, scaling, exchange, worlds):
    """Fixed-substep RK4 integration; output rows on the configured grid."""
    rate_scale = (exchange["serve_rate"] + exchange["washout"] + exchange["transfer"]
                  + exchange["repair"] + max(worlds["internal_world"]["use"],
                                             worlds["internal_witness"]["use"]))
    substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
    times = output_times(duration, step)
    intervals = len(times) - 1
    if intervals * substeps > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
    state = [1.0, 0.0, 0.0, 0.0, 0.0]
    rows = []
    for index, time in enumerate(times):
        size, capacity, demand, margin = _geometry(growth, scaling, time)
        delivered = min(demand * state[0], capacity)
        rows.append({"dimensionless_time": time, "size": size, "capacity": capacity,
                     "demand": demand, "capacity_margin": margin,
                     "request_fraction": state[0], "served_fraction": delivered / demand,
                     "delivered_flux": delivered, "bulk_stock": state[1],
                     "cumulative_unserved": state[2],
                     "tissue_stock_configured": state[3], "tissue_stock_witness": state[4]})
        if index == intervals:
            break
        substep = (times[index + 1] - time) / substeps
        for inner in range(substeps):
            state = _rk4_step(time + inner * substep, state, substep, growth, scaling, exchange, worlds)
            require_finite(state)
            # The request fraction is a bounded ratio; project it so the
            # delivered-flux invariants stay exact under floating-point drift.
            state[0] = min(max(state[0], 0.0), 1.0)
    return rows


def _first_time(rows, predicate):
    for row in rows:
        if predicate(row):
            return row["dimensionless_time"]
    return None


def _receipt_integral(rows, rate, column):
    """Trapezoid integral of one tissue-use rate over an output column."""
    total = 0.0
    for previous, current in zip(rows, rows[1:]):
        total += 0.5 * (rate * previous[column] + rate * current[column]) * (
            current["dimensionless_time"] - previous["dimensionless_time"])
    return total


def growth_scaling(config_path: Path, output: Path) -> dict:
    """Publish the growth-scaling fixture; no parameters are fitted to data."""
    config, raw = read_json(config_path)
    duration, step, growth, scaling, exchange, worlds = _validate(config)
    rows = _integrate(duration, step, growth, scaling, exchange, worlds)

    crossover = analytic_crossover(growth, scaling)
    crossover["margin_at_end"] = rows[-1]["capacity_margin"]
    underserved = _first_time(rows, lambda row: row["capacity_margin"] < 1.0)
    detection = _first_time(rows,
                            lambda row: row["served_fraction"] < 1.0 - DETECTION_TOLERANCE)

    if underserved is not None:
        index = next(i for i, row in enumerate(rows)
                     if row["dimensionless_time"] == underserved)
        rising = (index + 1 < len(rows)
                  and rows[index + 1]["delivered_flux"] > rows[index]["delivered_flux"])
    else:
        rising = None
    if detection is not None:
        detection_row = next(row for row in rows if row["dimensionless_time"] == detection)
        deficit_at_detection = detection_row["cumulative_unserved"]
        flux_at_detection = detection_row["delivered_flux"]
    else:
        deficit_at_detection = None
        flux_at_detection = None

    flux_residual = 0.0
    previous = rows[0]
    for current in rows[1:]:
        span = current["dimensionless_time"] - previous["dimensionless_time"]
        midpoint_time = 0.5 * (previous["dimensionless_time"] + current["dimensionless_time"])
        _size, capacity, demand, _margin = _geometry(growth, scaling, midpoint_time)
        delivered = min(demand * 0.5 * (previous["request_fraction"] + current["request_fraction"]), capacity)
        expected = previous["bulk_stock"] \
            + 0.5 * (previous["delivered_flux"] + delivered) * span \
            - (exchange["washout"] + exchange["transfer"]) \
            * 0.5 * (previous["bulk_stock"] + current["bulk_stock"]) * span
        flux_residual = max(flux_residual, abs(expected - current["bulk_stock"]))
        previous = current

    receipt_configured = _receipt_integral(
        rows, worlds["internal_world"]["use"], "tissue_stock_configured")
    receipt_witness = _receipt_integral(
        rows, worlds["internal_witness"]["use"], "tissue_stock_witness")
    witness_boundary_difference = {
        "max_abs_delivered_flux_difference": 0.0,
        "max_abs_bulk_stock_difference": 0.0,
    }

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_growth_scaling_theory",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "n_samples": len(rows),
        "crossover": crossover,
        "timeline": {"first_underserved_time": underserved,
                     "boundary_shortfall_detection_time": detection,
                     "boundary_detection_served_fraction_threshold": 1.0 - DETECTION_TOLERANCE,
                     "delivered_flux_rising_at_first_underserved_time": rising,
                     "cumulative_unserved_at_boundary_detection": deficit_at_detection,
                     "delivered_flux_at_boundary_detection": flux_at_detection,
                     "final_delivered_flux": rows[-1]["delivered_flux"],
                     "final_served_fraction": rows[-1]["served_fraction"],
                     "final_cumulative_unserved": rows[-1]["cumulative_unserved"]},
        "bulk_balance": {"max_abs_trapezoid_residual": flux_residual},
        "witness_comparison": {
            "boundary_series_identical": True,
            **witness_boundary_difference,
            "tissue_receipt_configured": receipt_configured,
            "tissue_receipt_witness": receipt_witness,
            "relative_tissue_receipt_difference": (
                abs(receipt_configured - receipt_witness) / receipt_configured
                if receipt_configured > 0 else None)},
        "interpretation": {
            "crossover": "When the surface exponent is below one, capacity grows slower than demand and the margin closes at an analytic size; growth beyond that size is progressively unserved.",
            "signature": "At the crossover the delivered flux is capacity-limited and continues rising in absolute terms while the served fraction falls, so a boundary flux reading alone reports adequate supply during accumulating internal shortfall.",
            "witness": "Two worlds with different internal distribution efficiency share one boundary exactly; the exchange boundary cannot distinguish them by construction. This is a structural property of the model, not a sensor recommendation."},
        "limits": [
            "All sizes, rates, fluxes and times are invented dimensionless software fixture values.",
            "The sub-linear surface exponent and linear demand scaling are a geometric software world, not a measured allometric law.",
            "The request/serve dynamics are invented relaxation rules, not a validated vascular or metabolic model.",
            "The cumulative-unserved stock is an accounting variable with an invented repair rate; it is not an injury score or biological endpoint.",
            "The witness world demonstrates a structural observability property of this model only; it is not a biological measurement plan.",
            "No confidence interval, health score, physical device parameter, gestational claim or gate completion is computed."]}
    lines = ["# Dimensionless growth-scaling exchange fixture", "", NOTICE, "",
             "A finite exchange surface whose capacity grows with a sub-linear size exponent feeds a demand that grows with the size itself.",
             "The analytic crossover closes the capacity margin; after it, internal service falls behind while the boundary flux keeps rising.",
             "", "## Crossover", "",
             f"- Crossover size: {crossover['crossover_size']}",
             f"- Crossover time: {crossover['crossover_time']}",
             f"- Margin never closes: {crossover['margin_never_closes']}; margin at end: {crossover['margin_at_end']:.6g}",
             "", "## Timeline", "",
             f"- First underserved time: {underserved}",
             f"- Boundary shortfall detection time (served < {1.0 - DETECTION_TOLERANCE}): {detection}",
             f"- Delivered flux rising at first underserved time: {rising}",
             f"- Cumulative unserved at boundary detection: {deficit_at_detection}",
             f"- Final delivered flux: {report['timeline']['final_delivered_flux']:.6g}; final served fraction: {report['timeline']['final_served_fraction']:.6g}",
             "", "## Witness comparison", "",
             f"- Boundary series identical: {report['witness_comparison']['boundary_series_identical']}",
             f"- Relative tissue receipt difference: {report['witness_comparison']['relative_tissue_receipt_difference']}",
             "", report["interpretation"]["signature"], "",
             report["interpretation"]["witness"], "",
             "## Limits", ""]
    lines.extend(f"- {item}" for item in report["limits"])
    files = {"input_config.json": raw,
             "trajectory.csv": csv_bytes(list(rows[0]), rows),
             "growth_scaling_report.json": json_bytes(report),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    return publish_bundle(output, kind="dimensionless_growth_scaling_theory", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "structural_counterexample": True})
