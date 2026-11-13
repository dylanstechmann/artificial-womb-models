"""Multi-unit shared-service contention experiment (T30).

Two gestation units share a common bulk stock reservoir. Each unit runs its own
controller, monitor and internal state, but both draw supplement from and return
waste to the same shared reservoir. The experiment tests whether a fault in unit A
propagates to unit B through the shared resource, and whether per-unit boundary
monitoring can distinguish local failure from shared-resource depletion.

Every value is an invented dimensionless software quantity. No internal tissue
channel is used to detect cross-unit propagation.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number
from .whole_path_twin import (
    MAX_TOTAL_SUBSTEPS,
    SUBSTEP_RATE_TARGET,
    _fault_at,
    _in_outage,
    _right_hand_side,
    _rk4_step,
    _validate,
)
from .numerics import output_times, require_finite

MODES = ("isolated", "shared")
FAULT_KINDS = ("none", "sensor_bias", "actuator_offset")
TRAJECTORY_COLUMNS = (
    "dimensionless_time", "unit", "size", "capacity_margin", "request_fraction",
    "served_fraction", "delivered_flux", "local_stock", "deep_receipt_rate",
    "cumulative_unserved", "progression", "reserve", "supplement",
    "shared_reservoir",
)
OBSERVATION_COLUMNS = (
    "mode", "variant", "dimensionless_time", "unit", "declared_fault",
    "shared_reservoir", "unit_a_progression", "unit_b_progression",
    "progression_divergence", "cross_unit_propagation",
)


def _validate_faults(items, duration, step):
    if not isinstance(items, list) or len(items) > 8:
        raise InputError("unit_a_faults must be a list of at most 8 intervals")
    result = []
    previous_end = -1.0
    for item in items:
        fields(item, ("start", "end", "kind", "magnitude"), "unit_a_faults")
        start = number(item["start"], "unit_a_faults start", 0, duration)
        end = number(item["end"], "unit_a_faults end", 0, duration)
        if end < start or start < previous_end:
            raise InputError("unit_a_faults intervals must be ordered, nonnegative and nonoverlapping")
        kind = item["kind"]
        if not isinstance(kind, str) or kind not in FAULT_KINDS:
            raise InputError(f"unit_a_faults kind must be one of: {', '.join(FAULT_KINDS)}")
        magnitude = number(item["magnitude"], "fault magnitude", -1_000_000, 1_000_000)
        if abs(start / step - round(start / step)) > 1e-9 \
                or abs(end / step - round(end / step)) > 1e-9:
            raise InputError("unit_a_faults must begin and end on the output grid")
        result.append({"start": start, "end": end, "kind": kind, "magnitude": magnitude})
        previous_end = end
    return result


def _validate_experiment(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
                    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
                    "monitor", "variants", "analysis", "contention_experiment"), "config")
    experiment = config["contention_experiment"]
    fields(experiment, ("shared_reservoir", "modes", "unit_a_faults", "noise_sd", "seed"),
           "contention_experiment")
    parsed_experiment = {}
    reservoir = experiment["shared_reservoir"]
    fields(reservoir, ("initial", "replenishment_rate", "washout"), "shared_reservoir")
    for key in ("initial", "replenishment_rate", "washout"):
        value = number(reservoir[key], f"shared_reservoir {key}", 0, 1_000_000)
        parsed_experiment[f"reservoir_{key}"] = value
    modes = experiment["modes"]
    if not isinstance(modes, list) or not 1 <= len(modes) <= 2 or \
            any(m not in MODES for m in modes):
        raise InputError(f"modes must be a nonempty subset of: {', '.join(MODES)}")
    parsed_experiment["modes"] = list(modes)
    parsed_experiment["noise_sd"] = number(experiment["noise_sd"], "noise_sd", 0, 10)
    seed = experiment["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise InputError("seed must be an integer")
    parsed_experiment["seed"] = seed
    base = {key: value for key, value in config.items() if key != "contention_experiment"}
    parsed = _validate(base)
    duration, step = parsed[:2]
    faults = _validate_faults(experiment["unit_a_faults"], duration, step)
    return parsed, parsed_experiment, faults


def _unit_run(name, variant, shared, duration, step, boundaries, rng_control, rng_monitor,
              noise_sd, seed_offset, fault_list, shared_reservoir_initial, reservoir_params,
              is_isolated, unit_label):
    """Run a single unit, drawing supplement from a shared or isolated reservoir."""
    growth, scaling, bulk, internal, control, reserve, outages = shared[:7]
    cadence, canonical_noise_sd, canonical_seed, monitor_faults = shared[7:]
    parameters = (growth, scaling, bulk, internal, control, reserve, outages, variant)
    rate_scale = (max(variant["serve_rate"], bulk["washout"] + bulk["transfer"],
                       internal["use"], internal["repair"])
                  + control["gain"] + reserve["draw"])
    substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
    times = output_times(duration, step)
    if (len(times) - 1) * substeps > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")

    if is_isolated:
        rng_control = random.Random(canonical_seed)
        rng_monitor = random.Random(canonical_seed + 1)
        noise_sd = canonical_noise_sd

    state = [1.0, 0.0, 0.0, 0.0, 0.0, reserve["initial"], 0.0]
    held_reading = 0.0
    if isinstance(shared_reservoir_initial, dict):
        reservoir_trace = list(shared_reservoir_initial["trace"])
        shared_val = reservoir_trace[0] if reservoir_trace else shared_reservoir_initial["initial"]
        ref_initial = shared_reservoir_initial["initial"]
    else:
        reservoir_trace = None
        shared_val = float(shared_reservoir_initial)
        ref_initial = float(shared_reservoir_initial) if shared_reservoir_initial > 0 else 5.0

    out_trace = []
    rows = []
    work = 0
    edges = sorted({item[key] for item in outages for key in ("start", "end")})
    replenishment = reservoir_params["replenishment_rate"]
    reservoir_washout = reservoir_params["washout"]
    trace_idx = 0

    for index, time in enumerate(times):
        fault = _declared_fault_at(fault_list, time)
        kind = fault["kind"] if fault else ""

        size = 1.0 + growth["linear_rate"] * time
        capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
        demand = scaling["demand_coefficient"] * size
        supply_factor = 1.0 if is_isolated else min(1.0, max(0.0, shared_val / ref_initial))
        boundary_delivered = min(demand * state[0], capacity) * supply_factor
        if _in_outage(outages, time):
            boundary_delivered *= reserve["fraction"] if state[5] > 0 else 0.0

        rows.append({"dimensionless_time": time, "unit": unit_label, "size": size,
                     "capacity_margin": capacity / demand, "request_fraction": state[0],
                     "served_fraction": boundary_delivered / demand if demand else 0.0,
                     "delivered_flux": boundary_delivered, "local_stock": state[1],
                     "deep_receipt_rate": internal["use"] * state[2],
                     "cumulative_unserved": state[3], "progression": state[4],
                     "reserve": state[5], "supplement": state[6],
                     "shared_reservoir": shared_val})

        if index == len(times) - 1:
            break

        sensor_noise = rng_control.gauss(0.0, noise_sd) if noise_sd else 0.0
        reading = state[1] + sensor_noise
        if kind == "sensor_bias":
            reading -= abs(fault["magnitude"])
        held_reading = reading

        if abs(round(time / cadence) - time / cadence) < 1e-9 or index == 0:
            monitor_fault = _fault_at(monitor_faults, time)
            if monitor_fault and monitor_fault["kind"] == "dropout":
                pass
            else:
                _monitor_value = state[1] + rng_monitor.gauss(0.0, noise_sd)

        cursor, end = time, times[index + 1]
        while cursor < end:
            stop = min([end] + [edge for edge in edges if cursor < edge < end])
            outage = _in_outage(outages, cursor)
            active_backup = outage and state[5] > 0.0
            draw_reserve = reserve["draw"] if active_backup else 0.0
            base_power = reserve["fraction"] if active_backup else (0.0 if outage else 1.0)
            depletion = cursor + state[5] / draw_reserve if draw_reserve > 0.0 else None
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
                if is_isolated:
                    shared_val += (replenishment - reservoir_washout * shared_val - state[6]) * substep
                    shared_val = max(0.0, shared_val)
                    power = base_power
                else:
                    if reservoir_trace is not None and trace_idx < len(reservoir_trace):
                        shared_val = reservoir_trace[trace_idx]
                        trace_idx += 1
                    active_f = _declared_fault_at(fault_list, subtime)
                    f_kind = active_f["kind"] if active_f else ""
                    fault_draw = (demand * (1.0 + abs(active_f["magnitude"]) * 10.0)
                                  if f_kind in ("sensor_bias", "actuator_offset") else 0.0)
                    shared_val += (replenishment - reservoir_washout * shared_val - state[6] - fault_draw) * substep
                    shared_val = max(0.0, shared_val)
                    out_trace.append(shared_val)
                    supply_factor = min(1.0, max(0.0, shared_val / ref_initial))
                    power = base_power * supply_factor

                state = _rk4_step(subtime, state, substep, parameters, held_reading,
                                  (power, draw_reserve))
                if not is_isolated and kind == "actuator_offset":
                    state[1] += fault["magnitude"] * substep
                if not is_isolated and reservoir_trace is not None:
                    state[6] = min(state[6], supply_factor * control["supplement_max"])
                require_finite(state)
                state[0] = min(max(state[0], 0.0), 1.0)
                state[6] = min(max(state[6], 0.0), control["supplement_max"])
                for pos in (1, 2, 3, 4):
                    state[pos] = max(state[pos], 0.0)
                state[5] = max(0.0, segment_reserve - draw_reserve * (inner + 1) * substep)

            if depletion is not None and stop == depletion:
                state[5] = 0.0
            cursor = stop

    if not is_isolated and reservoir_trace is None:
        return rows, {"initial": ref_initial, "trace": out_trace, "final": shared_val}
    return rows, shared_val


def _declared_fault_at(faults, time):
    for item in faults:
        if item["start"] <= time <= item["end"]:
            return item
    return None


def _run_experiment(config_path: Path, output: Path) -> dict:
    """Publish the deterministic multi-unit contention discriminator bundle."""
    config, raw = read_json(config_path)
    parsed, experiment, faults = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, _seed, monitor_faults, variants, analysis) = parsed
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, _seed, monitor_faults)

    reservoir_params = {
        "replenishment_rate": experiment["reservoir_replenishment_rate"],
        "washout": experiment["reservoir_washout"],
    }
    reservoir_initial = experiment["reservoir_initial"]
    exp_noise_sd = experiment["noise_sd"]
    exp_seed = experiment["seed"]
    modes = experiment["modes"]

    all_trajectories = {}
    all_observations = []

    isolated_baseline = {}
    if "isolated" in modes:
        for name in sorted(variants):
            rng_a_ctrl = random.Random(exp_seed)
            rng_a_mon = random.Random(exp_seed + 1)
            rng_b_ctrl = random.Random(exp_seed + 100)
            rng_b_mon = random.Random(exp_seed + 101)
            rows_a, _ = _unit_run(name, variants[name], shared, duration, step, boundaries,
                                  rng_a_ctrl, rng_a_mon, exp_noise_sd, 0, [],
                                  reservoir_initial, reservoir_params, True, "A")
            rows_b, _ = _unit_run(name, variants[name], shared, duration, step, boundaries,
                                  rng_b_ctrl, rng_b_mon, exp_noise_sd, 100, [],
                                  reservoir_initial, reservoir_params, True, "B")
            all_trajectories[("isolated", name, "A")] = rows_a
            all_trajectories[("isolated", name, "B")] = rows_b
            isolated_baseline[name] = {"A": rows_a, "B": rows_b}

    for fault in faults:
        fault_list = [fault] if fault["kind"] != "none" else []
        fault_label = fault["kind"]

        for name in sorted(variants):
            rng_a_ctrl = random.Random(exp_seed)
            rng_a_mon = random.Random(exp_seed + 1)
            rng_b_ctrl = random.Random(exp_seed + 100)
            rng_b_mon = random.Random(exp_seed + 101)

            if "shared" in modes:
                rows_a, remaining_reservoir = _unit_run(
                    name, variants[name], shared, duration, step, boundaries,
                    rng_a_ctrl, rng_a_mon, exp_noise_sd, 0, fault_list,
                    reservoir_initial, reservoir_params, False, "A")
                rows_b, _ = _unit_run(
                    name, variants[name], shared, duration, step, boundaries,
                    rng_b_ctrl, rng_b_mon, exp_noise_sd, 100, [],
                    remaining_reservoir, reservoir_params, False, "B")

                all_trajectories[("shared", name, fault_label, "A")] = rows_a
                all_trajectories[("shared", name, fault_label, "B")] = rows_b

                isolated_b = isolated_baseline.get(name, {}).get("B", [])

                for i, (row_a, row_b) in enumerate(zip(rows_a, rows_b)):
                    prog_a = row_a["progression"]
                    prog_b = row_b["progression"]
                    divergence = abs(prog_a - prog_b)

                    isolated_prog_b = isolated_b[i]["progression"] if i < len(isolated_b) else prog_b
                    cross_unit = False
                    if isolated_prog_b > 0.001:
                        cross_unit = (isolated_prog_b - prog_b) / isolated_prog_b > 0.05

                    all_observations.append({
                        "mode": "shared",
                        "variant": name,
                        "dimensionless_time": row_a["dimensionless_time"],
                        "unit": "comparison",
                        "declared_fault": fault_label,
                        "shared_reservoir": row_a["shared_reservoir"],
                        "unit_a_progression": prog_a,
                        "unit_b_progression": prog_b,
                        "progression_divergence": divergence,
                        "cross_unit_propagation": cross_unit,
                    })

    comparisons = []
    for name in sorted(variants):
        for fault in faults:
            fault_label = fault["kind"]
            if fault_label == "none":
                continue
            key = ("shared", name, fault_label, "A")
            if key not in all_trajectories:
                continue
            obs = [o for o in all_observations
                   if o["variant"] == name and o["declared_fault"] == fault_label]
            propagated = [o for o in obs if o["cross_unit_propagation"]]
            first_propagation = min((o["dimensionless_time"] for o in propagated), default=None)
            max_divergence = max((o["progression_divergence"] for o in obs), default=0.0)
            comparisons.append({
                "variant": name,
                "fault_kind": fault_label,
                "fault_start": fault["start"],
                "fault_end": fault["end"],
                "fault_magnitude": fault["magnitude"],
                "cross_unit_propagation_detected": len(propagated) > 0,
                "propagated_samples": len(propagated),
                "total_samples": len(obs),
                "first_propagation_time": first_propagation,
                "max_progression_divergence": max_divergence,
            })

    hidden_check = _hidden_contention_check(variants, shared, duration, step, boundaries,
                                            experiment, reservoir_initial, reservoir_params)

    no_fault_isolated_match = _check_isolated_matches_twin(
        variants, shared, duration, step, boundaries, isolated_baseline)

    qualification_status = ("dimensionless_software_checks_passed"
                            if no_fault_isolated_match and hidden_check["contention_boundary_blind"]
                            else "dimensionless_software_checks_failed")

    report = {
        "schema_version": 1,
        "notice": NOTICE,
        "fixture_notice": NOTICE,
        "result_kind": "dimensionless_multi_unit_contention",
        "model_family": "dimensionless_multi_unit_shared_reservoir_contention",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "qualification_status": qualification_status,
        "modes": list(modes),
        "variants": sorted(variants),
        "fault_contract": {
            "supported_faults": list(FAULT_KINDS),
            "shared_reservoir_initial": reservoir_initial,
            "shared_reservoir_replenishment": reservoir_params["replenishment_rate"],
            "shared_reservoir_washout": reservoir_params["washout"],
            "noise_sd": exp_noise_sd,
            "seed": exp_seed,
            "faults_applied_to": "unit_A_only",
            "cross_unit_propagation_threshold": 0.05,
        },
        "comparisons": comparisons,
        "no_fault_isolated_matches_twin": no_fault_isolated_match,
        "hidden_contention_check": hidden_check,
        "interpretation": [
            "In shared mode, a sensor bias fault on unit A causes excessive supplement draw, depleting the shared reservoir and starving unit B of supplement — cross-unit propagation through a shared resource.",
            "Unit B's local stock and boundary observables cannot distinguish 'shared reservoir depletion caused by unit A's fault' from 'local delivery failure' — both manifest as falling local stock.",
            "Isolated mode (separate reservoirs) eliminates cross-unit propagation by construction but does not represent the shared-infrastructure architecture.",
        ],
        "limits": [
            "All values, faults, thresholds, noise streams and times are invented dimensionless software fixture quantities.",
            "Seeded independent noise is a software assumption, not demonstrated sensor independence or calibrated uncertainty.",
            "The shared reservoir model assumes instantaneous mixing and proportional allocation; real fluidic systems have transport delays, spatial gradients and nonlinear withdrawal effects.",
            "Two-unit sequential integration (A then B) does not model simultaneous contention or real-time scheduling.",
            "No biological measurement, physiological calibration, machine control, procurement or gate movement is established.",
        ],
    }

    lines = [
        "# Dimensionless multi-unit shared-service contention experiment", "", NOTICE, "",
        f"Shared reservoir: initial {reservoir_initial}, replenishment "
        f"{reservoir_params['replenishment_rate']}, washout {reservoir_params['washout']}. "
        f"Noise SD {exp_noise_sd}, seed {exp_seed}.", "",
        "Unit A faults propagate to unit B through the shared reservoir. "
        "Unit B's boundary observables cannot distinguish shared depletion from local failure.", "",
        "## Cross-unit propagation summary", "",
    ]
    for c in comparisons:
        lines.append(f"- {c['variant']} / {c['fault_kind']} (magnitude {c['fault_magnitude']}, "
                     f"t=[{c['fault_start']}, {c['fault_end']}]): "
                     f"{c['propagated_samples']}/{c['total_samples']} samples show cross-unit "
                     f"propagation, first at t={c['first_propagation_time']}, "
                     f"max divergence {c['max_progression_divergence']:.6g}")
    lines.extend([
        "", f"No-fault isolated matches twin: {no_fault_isolated_match}.",
        f"Hidden contention boundary blindness: {hidden_check['contention_boundary_blind']}.",
        "", *report["interpretation"], "", "## Limits", "",
    ])
    lines.extend(f"- {item}" for item in report["limits"])

    files = {
        "source_config.json": raw,
        "contention_observations.csv": csv_bytes(list(OBSERVATION_COLUMNS), all_observations),
        "multi_unit_contention_report.json": json_bytes(report),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    for key, rows in sorted(all_trajectories.items()):
        if len(key) == 3:
            mode, name, unit = key
            files[f"trajectory_{mode}_{name}_{unit}.csv"] = csv_bytes(list(TRAJECTORY_COLUMNS), rows)
        else:
            mode, name, fault_label, unit = key
            files[f"trajectory_{mode}_{name}_{fault_label}_{unit}.csv"] = \
                csv_bytes(list(TRAJECTORY_COLUMNS), rows)

    return publish_bundle(
        output, kind="dimensionless_multi_unit_contention", input_raw=raw, files=files,
        metadata={"biological_measurements": False, "physiologically_calibrated": False,
                   "human_gestation_prediction": False, "n_variants": len(variants),
                   "n_modes": len(modes), "qualification_status": qualification_status})


def _hidden_contention_check(variants, shared, duration, step, boundaries, experiment,
                              reservoir_initial, reservoir_params):
    """Verify unit B's boundary channels cannot distinguish shared depletion from local failure."""
    base_name = sorted(variants)[0]
    base_variant = variants[base_name]
    exp_seed = experiment["seed"]
    exp_noise_sd = experiment["noise_sd"]

    fault = {"kind": "sensor_bias", "start": 15.0, "end": 18.0, "magnitude": 0.3}

    rng_a = random.Random(exp_seed)
    rows_a1, remaining = _unit_run(base_name, base_variant, shared, duration, step, boundaries,
                                    rng_a, random.Random(exp_seed + 1), exp_noise_sd, 0,
                                    [fault], reservoir_initial, reservoir_params, False, "A")
    rng_b1 = random.Random(exp_seed + 100)
    rows_b1, _ = _unit_run(base_name, base_variant, shared, duration, step, boundaries,
                            rng_b1, random.Random(exp_seed + 101), exp_noise_sd, 100,
                            [], remaining, reservoir_params, False, "B")

    alt_variant = {**base_variant, "internal_efficiency": 0.0 if base_variant["internal_efficiency"] else 1.0}
    rng_a2 = random.Random(exp_seed)
    rows_a2, remaining2 = _unit_run(base_name, base_variant, shared, duration, step, boundaries,
                                     rng_a2, random.Random(exp_seed + 1), exp_noise_sd, 0,
                                     [fault], reservoir_initial, reservoir_params, False, "A")
    rng_b2 = random.Random(exp_seed + 100)
    rows_b2, _ = _unit_run(base_name, alt_variant, shared, duration, step, boundaries,
                            rng_b2, random.Random(exp_seed + 101), exp_noise_sd, 100,
                            [], remaining2, reservoir_params, False, "B")

    boundary_cols = ("dimensionless_time", "size", "capacity_margin", "request_fraction",
                     "served_fraction", "delivered_flux", "local_stock", "reserve",
                     "supplement", "shared_reservoir")
    a_boundary_match = all(
        all(row1[key] == row2[key] for key in boundary_cols)
        for row1, row2 in zip(rows_a1, rows_a2)
    )

    b_boundary_match = all(
        all(row1[key] == row2[key] for key in boundary_cols)
        for row1, row2 in zip(rows_b1, rows_b2)
    )

    b_internal_differs = any(
        row1["deep_receipt_rate"] != row2["deep_receipt_rate"]
        or row1["progression"] != row2["progression"]
        for row1, row2 in zip(rows_b1, rows_b2)
    )

    return {
        "contention_boundary_blind": b_boundary_match and b_internal_differs,
        "method": "Unit A has identical sensor_bias fault in both runs. Unit B varies only internal_efficiency. Unit B's boundary channels are identical while internal channels differ — shared-reservoir depletion looks the same as local failure to unit B's boundary.",
        "variant": base_name,
        "unit_a_boundary_identical": a_boundary_match,
        "unit_b_boundary_identical": b_boundary_match,
        "unit_b_internal_differs": b_internal_differs,
    }


def _check_isolated_matches_twin(variants, shared, duration, step, boundaries, isolated_baseline):
    """Verify isolated mode trajectories match independent whole_path_twin runs."""
    from .whole_path_twin import _variant_run

    for name in sorted(variants):
        if name not in isolated_baseline:
            continue
        canonical = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        for unit in ("A", "B"):
            isolated_rows = isolated_baseline[name][unit]
            for actual_row, expected_row in zip(isolated_rows, canonical):
                if actual_row["local_stock"] != expected_row["bulk_stock"]:
                    return False
                for key in expected_row:
                    if key in actual_row and actual_row[key] != expected_row[key]:
                        return False
    return True
