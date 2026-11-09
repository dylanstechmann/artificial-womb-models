"""Dimensionless independent-sensor disagreement and freeze fallback (T28).

A second noisy sensor checks the controller's bulk-stock reading. A declared
threshold and confirmation count select a frozen-supplement fallback; they do
not identify which sensor is faulty or make an internal tissue measurement.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, intervals, number
from .whole_path_twin import (_fault_at, _in_outage, _rk4_step, _validate,
                              MAX_TOTAL_SUBSTEPS, SUBSTEP_RATE_TARGET)
from .numerics import output_times, require_finite

MODES = ("single_sensor", "independent_sensor_freeze")


def _validate_experiment(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
                    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
                    "monitor", "variants", "analysis", "sensor_experiment"), "config")
    experiment = config["sensor_experiment"]
    fields(experiment, ("disagreement_threshold", "confirmation_samples", "control_faults"), "sensor_experiment")
    threshold = number(experiment["disagreement_threshold"], "disagreement_threshold", 1e-9, 1_000)
    confirmations = experiment["confirmation_samples"]
    if isinstance(confirmations, bool) or not isinstance(confirmations, int) \
            or not 1 <= confirmations <= 100:
        raise InputError("confirmation_samples must be an integer in [1, 100]")
    base = {key: value for key, value in config.items() if key != "sensor_experiment"}
    parsed = _validate(base)
    duration, step = parsed[:2]
    faults = intervals(experiment["control_faults"], duration, "control faults", faults=True)
    for item in faults:
        if abs(item["start"] / step - round(item["start"] / step)) > 1e-9 \
                or abs(item["end"] / step - round(item["end"] / step)) > 1e-9:
            raise InputError("control faults must begin and end on the output grid")
    return parsed, threshold, confirmations, faults


def _sensor_run(name, variant, shared, duration, step, boundaries, mode, threshold,
                confirmations, control_faults):
    growth, scaling, bulk, internal, control, reserve, outages = shared[:7]
    cadence, noise_sd, seed, monitor_faults = shared[7:]
    parameters = (growth, scaling, bulk, internal, control, reserve, outages, variant)
    rate_scale = (max(variant["serve_rate"], bulk["washout"] + bulk["transfer"],
                      internal["use"], internal["repair"])
                  + control["gain"] + reserve["draw"])
    substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
    times = output_times(duration, step)
    if (len(times) - 1) * substeps > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
    # The primary stream is exactly the canonical controller stream. The
    # secondary stream is independent and never changes the no-fault primary.
    rng_control = random.Random(seed)
    rng_monitor = random.Random(seed + 1)
    rng_secondary = random.Random(seed + 2)
    state = [1.0, 0.0, 0.0, 0.0, 0.0, reserve["initial"], 0.0]
    held_reading = 0.0
    fallback = False
    disagreement_count = 0
    rows, observations = [], []
    work = 0
    edges = sorted({item[key] for item in outages for key in ("start", "end")})
    for index, time in enumerate(times):
        size = 1.0 + growth["linear_rate"] * time
        capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
        demand = scaling["demand_coefficient"] * size
        delivered = min(demand * state[0], capacity)
        if _in_outage(outages, time):
            delivered *= reserve["fraction"] if state[5] > 0 else 0.0
        rows.append({"dimensionless_time": time, "size": size,
                     "capacity_margin": capacity / demand, "request_fraction": state[0],
                     "served_fraction": delivered / demand, "delivered_flux": delivered,
                     "bulk_stock": state[1], "deep_receipt_rate": internal["use"] * state[2],
                     "cumulative_unserved": state[3], "progression": state[4],
                     "reserve": state[5], "supplement": state[6],
                     "controller_reading": held_reading, "fallback_active": fallback})
        if index == len(times) - 1:
            break
        primary_noise = rng_control.gauss(0.0, noise_sd) if noise_sd else 0.0
        secondary_noise = rng_secondary.gauss(0.0, noise_sd) if noise_sd else 0.0
        primary = state[1] + primary_noise
        fault = _fault_at(control_faults, time)
        primary_available = not fault or fault["kind"] != "dropout"
        observed_primary = primary if primary_available else None
        if fault and fault["kind"] == "bias":
            observed_primary += fault["magnitude"]
        secondary = state[1] + secondary_noise
        residual = abs(observed_primary - secondary) if observed_primary is not None else None
        disagrees = observed_primary is None or residual > threshold
        disagreement_count = disagreement_count + 1 if disagrees else 0
        detected = mode == "independent_sensor_freeze" and disagreement_count >= confirmations
        if detected:
            fallback = True
        observations.append({"variant": name, "mode": mode, "dimensionless_time": time,
                             "declared_fault": fault["kind"] if fault else "",
                             "primary_available": primary_available,
                             "primary_reading": observed_primary,
                             "secondary_reading": secondary,
                             "primary_noise": primary_noise, "secondary_noise": secondary_noise,
                             "absolute_residual": residual,
                             "disagreement_count": disagreement_count,
                             "fault_detected": detected, "fallback_active": fallback})
        held_reading = bulk["target"] if fallback else (
            observed_primary if observed_primary is not None else bulk["target"])
        if abs(round(time / cadence) - time / cadence) < 1e-9 or index == 0:
            monitor_fault = _fault_at(monitor_faults, time)
            if monitor_fault and monitor_fault["kind"] == "dropout":
                value = None
            else:
                value = state[1] + rng_monitor.gauss(0.0, noise_sd)
                if monitor_fault:
                    value += monitor_fault["magnitude"]
        cursor, end = time, times[index + 1]
        while cursor < end:
            stop = min([end] + [edge for edge in edges if cursor < edge < end])
            outage = _in_outage(outages, cursor)
            active_backup = outage and state[5] > 0.0
            draw = reserve["draw"] if active_backup else 0.0
            power = reserve["fraction"] if active_backup else (0.0 if outage else 1.0)
            depletion = cursor + state[5] / draw if draw > 0.0 else None
            if depletion is not None:
                stop = min(stop, depletion)
            if stop <= cursor:
                state[5] = 0.0
                continue
            count = max(1, math.ceil((stop - cursor) * rate_scale / SUBSTEP_RATE_TARGET))
            work += count
            if work > MAX_TOTAL_SUBSTEPS:
                raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
            segment_start, segment_reserve = cursor, state[5]
            substep = (stop - cursor) / count
            for inner in range(count):
                subtime = segment_start + inner * substep
                state = _rk4_step(subtime, state, substep, parameters, held_reading,
                                  (power, draw))
                require_finite(state)
                state[0] = min(max(state[0], 0.0), 1.0)
                state[6] = min(max(state[6], 0.0), control["supplement_max"])
                for position in (1, 2, 3, 4):
                    state[position] = max(state[position], 0.0)
                state[5] = max(0.0, segment_reserve - draw * (inner + 1) * substep)
            if depletion is not None and stop == depletion:
                state[5] = 0.0
            cursor = stop
    return rows, observations


def sensor_failover(config_path: Path, output: Path) -> dict:
    config, raw = read_json(config_path)
    parsed, threshold, confirmations, faults = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, variants, analysis) = parsed
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, monitor_faults)
    runs, all_observations = {}, []
    for mode in MODES:
        for name in sorted(variants):
            rows, observations = _sensor_run(name, variants[name], shared, duration, step,
                                             boundaries, mode, threshold, confirmations, faults)
            runs[(mode, name)] = rows
            all_observations.extend(observations)
    no_fault_matches = True
    if not faults:
        from .whole_path_twin import _variant_run
        for name in sorted(variants):
            canonical = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
            for actual, expected in zip(runs[("single_sensor", name)], canonical):
                if any(actual[key] != expected[key] for key in expected):
                    no_fault_matches = False
    comparisons = []
    for name in sorted(variants):
        single = runs[("single_sensor", name)]
        redundant = runs[("independent_sensor_freeze", name)]
        observations = [row for row in all_observations
                        if row["variant"] == name and row["mode"] == "independent_sensor_freeze"]
        faulted = [row for row in observations if row["declared_fault"]]
        detected = [row for row in faulted if row["fault_detected"]]
        false_alarms = [row for row in observations
                        if not row["declared_fault"] and row["fault_detected"]]
        first_detection = next((row["dimensionless_time"] for row in detected), None)
        comparisons.append({
            "variant": name,
            "fault_samples": len(faulted), "detected_fault_samples": len(detected),
            "undetected_fault_samples": len(faulted) - len(detected),
            "false_alarm_samples": len(false_alarms),
            "first_detection_time": first_detection,
            "fallback_ever_active": any(row["fallback_active"] for row in observations),
            "final_bulk_single_sensor": single[-1]["bulk_stock"],
            "final_bulk_independent_sensor_freeze": redundant[-1]["bulk_stock"],
            "final_progression_single_sensor": single[-1]["progression"],
            "final_progression_independent_sensor_freeze": redundant[-1]["progression"],
            "max_absolute_bulk_difference": max(abs(a["bulk_stock"] - b["bulk_stock"])
                                                for a, b in zip(single, redundant)),
            "max_absolute_progression_difference": max(abs(a["progression"] - b["progression"])
                                                       for a, b in zip(single, redundant))})
    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_sensor_failover",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "modes": list(MODES), "variants": sorted(variants),
        "sensor_contract": {
            "primary_noise_seed": seed, "secondary_noise_seed": seed + 2,
            "noise_streams_independent": True, "shared_noise_sd": noise_sd,
            "disagreement_threshold": threshold, "confirmation_samples": confirmations,
            "fallback": "latching frozen synthetic supplement at its pre-detection value",
            "fault_isolation": "not_attempted; disagreement does not identify the faulty sensor",
            "internal_tissue_observed_by_fallback": False},
        "declared_control_faults": faults,
        "no_fault_canonical_trajectories_match": no_fault_matches if not faults else None,
        "comparisons": comparisons,
        "interpretation": [
            "The single-sensor mode exposes declared controller faults; the independent-sensor mode uses only disagreement to enter a frozen-supplement fallback.",
            "Detection is not diagnosis: a discrepancy can come from either sensor or noise, and a latched fallback can remain after the declared fault ends.",
            "The fallback observes no internal tissue state and cannot establish developmental adequacy or correct a hidden internal shortfall."],
        "limits": [
            "All values, faults, thresholds and times are invented dimensionless software fixture quantities.",
            "Independent seeded noise is a software assumption, not demonstrated sensor independence or calibrated uncertainty.",
            "The fallback is a conservative software policy, not a hardware-safe state, operating instruction or validated alarm design.",
            "This experiment does not test common-cause sensor failures, actuator failures or physical measurement faults.",
            "No biological measurement, physiological calibration, machine control, procurement or gate movement is established."]}
    lines = ["# Dimensionless sensor disagreement and freeze fallback", "", NOTICE, "",
             f"Threshold {threshold}; {confirmations} consecutive disagreement sample(s) latch fallback.", "",
             "The fallback freezes the synthetic supplement; it does not identify the faulty sensor or observe internal tissue.", "",
             "## Variant comparisons", ""]
    for row in comparisons:
        lines.append(f"- {row['variant']}: {row['detected_fault_samples']}/{row['fault_samples']} "
                     f"fault samples detected; {row['false_alarm_samples']} false-alarm samples; "
                     f"first detection {row['first_detection_time']}; maximum bulk difference "
                     f"{row['max_absolute_bulk_difference']:.6g}.")
    lines.extend(["", *report["interpretation"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])
    files = {"input_config.json": raw, "sensor_failover_report.json": json_bytes(report),
             "sensor_observations.csv": csv_bytes(list(all_observations[0]), all_observations),
             "variant_comparisons.csv": csv_bytes(list(comparisons[0]), comparisons),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    for (mode, name), rows in sorted(runs.items()):
        files[f"trajectory_{mode}_{name}.csv"] = csv_bytes(list(rows[0]), rows)
    return publish_bundle(output, kind="dimensionless_sensor_failover", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "n_variants": len(variants), "n_modes": len(MODES)})
