"""Spatial internal-delivery identifiability in a dimensionless chain (T20).

A compartment chain (interface -> bulk -> deep tissue) is driven by a
boundary excitation. The observed prefix of the chain (interface and bulk)
is feedforward: no hidden compartment enters any observed equation, so a
witness world may replace everything below the observation depth - rates,
service levels, even the number of compartments - while every observed
quantity stays identical. This is the structural core of the T18
measurement contract: boundary-plus-bulk readouts cannot distinguish
served from unserved internal tissue, and the model dimension of the hidden
segment is unidentifiable from the boundary.

No parameter represents physiology, time in days, a device setpoint or a
biological measurement. The witness is a structural property of this model,
not a sensor recommendation.
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
MAX_CHAIN_LENGTH = 6
SUBSTEP_RATE_TARGET = 0.2


def _validate(config):
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "boundary",
                    "observed_depth", "chain", "witness_chain"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    fields(config["dimensionless_time"], ("duration", "output_step"), "dimensionless_time")
    duration = number(config["dimensionless_time"]["duration"], "duration", 1e-6, 10_000)
    step = number(config["dimensionless_time"]["output_step"], "output_step", 1e-6, duration)
    if duration / step > MAX_OUTPUT_INTERVALS:
        raise InputError(f"At most {MAX_OUTPUT_INTERVALS} output intervals are permitted")
    fields(config["boundary"], ("excitation",), "boundary")
    excitation = number(config["boundary"]["excitation"], "excitation", 0, 1_000)
    depth = config["observed_depth"]
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 1:
        raise InputError("observed_depth must be a positive integer")

    chains = {}
    for label in ("chain", "witness_chain"):
        items = config[label]
        if not isinstance(items, list) or not 2 <= len(items) <= MAX_CHAIN_LENGTH:
            raise InputError(f"{label} must be a list of 2 to {MAX_CHAIN_LENGTH} compartments")
        if depth >= len(items):
            raise InputError(f"{label} must extend below observed_depth so a hidden segment exists")
        chain = []
        for index, item in enumerate(items):
            fields(item, ("loss", "transfer", "use"), f"{label} compartment {index + 1}")
            rates = {key: number(value, f"{label} {key}", 0, MAX_RATE) for key, value in item.items()}
            if index == len(items) - 1 and rates["transfer"] != 0:
                raise InputError(f"{label} terminal compartment transfer must be zero")
            chain.append(rates)
        chains[label] = chain

    for index in range(depth):
        if config["chain"][index] != config["witness_chain"][index]:
            raise InputError("witness_chain must share the observed prefix exactly; "
                             "only the hidden segment below observed_depth may differ")
    return duration, step, excitation, depth, chains


def _equilibrium(excitation, chain):
    """Closed-form equilibrium stocks of the linear chain."""
    stocks = []
    inflow = excitation
    for rates in chain:
        stock = inflow / (rates["loss"] + rates["transfer"] + rates["use"])
        stocks.append(stock)
        inflow = rates["transfer"] * stock
    return stocks


def _right_hand_side(excitation, chain, state):
    result = []
    for index, rates in enumerate(chain):
        inflow = excitation if index == 0 else chain[index - 1]["transfer"] * state[index - 1]
        result.append(inflow - (rates["loss"] + rates["transfer"] + rates["use"]) * state[index])
    return result


def _rk4_step(excitation, chain, state, substep):
    first = _right_hand_side(excitation, chain, state)
    second = _right_hand_side(excitation, chain,
                              [value + 0.5 * substep * rate for value, rate in zip(state, first)])
    third = _right_hand_side(excitation, chain,
                             [value + 0.5 * substep * rate for value, rate in zip(state, second)])
    fourth = _right_hand_side(excitation, chain,
                              [value + substep * rate for value, rate in zip(state, third)])
    return [value + substep * (a + 2 * b + 2 * c + d) / 6.0
            for value, a, b, c, d in zip(state, first, second, third, fourth)]


def _integrate(excitation, chain, duration, step, rate_scale=None):
    """Fixed-substep RK4 integration of one chain from zero initial stocks."""
    own_rate = max(rates["loss"] + rates["transfer"] + rates["use"] for rates in chain)
    rate_scale = max(own_rate, rate_scale or 0.0)
    substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
    times = output_times(duration, step)
    intervals = len(times) - 1
    if intervals * substeps > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
    state = [0.0] * len(chain)
    rows = []
    for index, time in enumerate(times):
        rows.append({"dimensionless_time": time,
                     **{f"compartment_{position + 1}": value
                        for position, value in enumerate(state)}})
        if index == intervals:
            break
        substep = (times[index + 1] - time) / substeps
        for _ in range(substeps):
            state = _rk4_step(excitation, chain, state, substep)
            require_finite(state)
    return rows


def _receipt_table(rows, chain, depth, world):
    """Per-compartment final stocks and trapezoid cumulative receipts."""
    table = []
    for position, rates in enumerate(chain):
        column = f"compartment_{position + 1}"
        cumulative = 0.0
        for previous, current in zip(rows, rows[1:]):
            cumulative += 0.5 * (rates["use"] * previous[column]
                                 + rates["use"] * current[column]) * (
                current["dimensionless_time"] - previous["dimensionless_time"])
        table.append({"world": world, "compartment": position + 1,
                      "observed": position < depth, "use_rate": rates["use"],
                      "final_stock": rows[-1][column], "cumulative_receipt": cumulative})
    return table


def _balance_residual(excitation, rows, chain):
    """Max trapezoid residual of the compartment balance equations."""
    residual = 0.0
    for previous, current in zip(rows, rows[1:]):
        span = current["dimensionless_time"] - previous["dimensionless_time"]
        for index, rates in enumerate(chain):
            column = f"compartment_{index + 1}"
            if index:
                inflow = chain[index - 1]["transfer"] * 0.5 * (
                    previous[f"compartment_{index}"] + current[f"compartment_{index}"])
            else:
                inflow = excitation
            expected = previous[column] + span * (
                inflow - (rates["loss"] + rates["transfer"] + rates["use"])
                * 0.5 * (previous[column] + current[column]))
            residual = max(residual, abs(expected - current[column]))
    return residual


def spatial_delivery(config_path: Path, output: Path) -> dict:
    """Publish the spatial-delivery identifiability fixture; nothing is fitted."""
    config, raw = read_json(config_path)
    duration, step, excitation, depth, chains = _validate(config)
    # A hidden fast compartment must refine both worlds equally; otherwise
    # different integration rounding creates a false observed-prefix signal.
    shared_rate = max(rates["loss"] + rates["transfer"] + rates["use"]
                      for chain in chains.values() for rates in chain)
    rows = {label: _integrate(excitation, chains[label], duration, step, shared_rate)
            for label in ("chain", "witness_chain")}

    observed_difference = {f"compartment_{position + 1}":
                           max(abs(a[f"compartment_{position + 1}"]
                                   - b[f"compartment_{position + 1}"])
                               for a, b in zip(rows["chain"], rows["witness_chain"]))
                           for position in range(depth)}
    tables = {label: _receipt_table(rows[label], chains[label], depth, label)
              for label in ("chain", "witness_chain")}
    receipt = {label: sum(item["cumulative_receipt"] for item in tables[label]
                          if not item["observed"]) for label in ("chain", "witness_chain")}
    observed_receipt = {label: sum(item["cumulative_receipt"] for item in tables[label]
                                   if item["observed"]) for label in ("chain", "witness_chain")}

    equilibrium = {label: _equilibrium(excitation, chains[label])
                   for label in ("chain", "witness_chain")}
    equilibrium_deviation = {}
    for label in ("chain", "witness_chain"):
        equilibrium_deviation[label] = max(
            abs(rows[label][-1][f"compartment_{position + 1}"] - stock)
            for position, stock in enumerate(equilibrium[label]))

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_spatial_delivery_theory",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "n_samples": len(rows["chain"]),
        "integration": {"method": "RK4", "shared_chain_substeps": True,
                        "rate_bound": shared_rate,
                        "terminal_interval": "shortened when duration is off the output grid"},
        "observed_depth": depth,
        "compartments": {"chain": len(chains["chain"]),
                         "witness_chain": len(chains["witness_chain"])},
        "structural_identity": (
            "Each compartment's derivative depends only on the boundary excitation and the "
            "stocks above it: dC_i/dt = transfer_{i-1}*C_{i-1} - (loss_i + transfer_i + use_i)*C_i. "
            "No hidden compartment enters any observed equation, so the observed prefix is "
            "bitwise shared by any world that keeps it fixed."),
        "witness_comparison": {
            "max_abs_observed_differences": observed_difference,
            "observed_series_identical": all(value == 0.0
                                              for value in observed_difference.values()),
            "hidden_segment_lengths": {"chain": len(chains["chain"]) - depth,
                                       "witness_chain": len(chains["witness_chain"]) - depth},
            "internal_receipt_configured": receipt["chain"],
            "internal_receipt_witness": receipt["witness_chain"],
            "relative_internal_receipt_difference": (
                abs(receipt["chain"] - receipt["witness_chain"]) / receipt["chain"]
                if receipt["chain"] > 0 else None),
            "observed_receipt_configured": observed_receipt["chain"],
            "observed_receipt_witness": observed_receipt["witness_chain"],
            "observed_receipt_identical": observed_receipt["chain"] == observed_receipt["witness_chain"]},
        "equilibrium": {"closed_form_stocks": equilibrium,
                        "max_abs_final_deviation": equilibrium_deviation},
        "balance": {label: {"max_abs_trapezoid_residual":
                            _balance_residual(excitation, rows[label], chains[label])}
                    for label in ("chain", "witness_chain")},
        "cut_point": {
            "resolved_compartments": depth,
            "exchangeable_below": "Everything below the deepest observation is exchangeable: "
                                  "rates, service levels and the number of hidden compartments "
                                  "are all absent from every observed quantity. Each added "
                                  "observed compartment moves the cut point one step deeper "
                                  "and resolves nothing below it."},
        "limits": [
            "All rates, stocks and times are invented dimensionless software fixture values.",
            "The chain is a feedforward linear cascade; no feedback, saturation or transport delay is modeled.",
            "The identity is a structural property of this model class, not a biological result about vasculature or tissue.",
            "Cumulative receipt is an accounting integral of the use rate, not a measured metabolic rate.",
            "The cut-point statement is a mathematical observation requirement, not a sensor or biopsy recommendation.",
            "No confidence interval, health score, physical device parameter, gestational claim or gate completion is computed."]}
    lines = ["# Dimensionless spatial internal-delivery identifiability", "", NOTICE, "",
             "A compartment chain is driven by a boundary excitation; only the observed prefix is visible.",
             "A witness world replaces the whole hidden segment - rates, service, even compartment count.",
             "", "## Structural identity", "",
             report["structural_identity"], "",
             "## Witness comparison", "",
             f"- Observed series identical: {report['witness_comparison']['observed_series_identical']}",
             f"- Max observed differences: {observed_difference}",
             f"- Hidden compartments: {report['witness_comparison']['hidden_segment_lengths']}",
             f"- Internal receipt configured: {receipt['chain']:.6g}; witness: {receipt['witness_chain']:.6g}",
             f"- Relative internal receipt difference: {report['witness_comparison']['relative_internal_receipt_difference']:.6g}",
             "", "## Cut point", "",
             report["cut_point"]["exchangeable_below"], "",
             "## Limits", ""]
    lines.extend(f"- {item}" for item in report["limits"])
    summary_rows = tables["chain"] + tables["witness_chain"]
    files = {"input_config.json": raw,
             "configured_trajectory.csv": csv_bytes(list(rows["chain"][0]), rows["chain"]),
             "witness_trajectory.csv": csv_bytes(list(rows["witness_chain"][0]), rows["witness_chain"]),
             "receipt_summary.csv": csv_bytes(list(summary_rows[0]), summary_rows),
             "spatial_delivery_report.json": json_bytes(report),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    return publish_bundle(output, kind="dimensionless_spatial_delivery_theory", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "structural_counterexample": True})
