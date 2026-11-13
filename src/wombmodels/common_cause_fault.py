"""Common-cause sensor and supplement-actuator fault discrimination (T29).

The canonical whole-path controller is paired with an independent bulk sensor,
a commanded-supplement shadow trajectory, and a noisy actuator meter. Pairwise
sensor disagreement alone cannot see a shared sensor bias or an actuator offset.
The augmented policy adds balance and actuator innovations, then freezes the
synthetic supplement and, for a confirmed actuator fault, isolates its offset.

Every value is an invented dimensionless software quantity. No internal tissue
channel is used by any detector or fallback.
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

MODES = ("single_sensor", "disagreement_freeze", "balance_augmented_freeze")
FAULT_KINDS = (
    "primary_bias",
    "primary_dropout",
    "common_sensor_bias",
    "common_sensor_dropout",
    "actuator_offset",
)
TRAJECTORY_COLUMNS = (
    "dimensionless_time", "size", "capacity_margin", "request_fraction",
    "served_fraction", "delivered_flux", "bulk_stock", "deep_receipt_rate",
    "cumulative_unserved", "progression", "reserve", "supplement",
    "controller_reading", "commanded_supplement", "delivered_supplement",
    "nominal_bulk_stock", "fallback_active", "actuator_isolated",
)
OBSERVATION_COLUMNS = (
    "mode", "variant", "dimensionless_time", "interval_index", "declared_fault",
    "primary_available", "secondary_available", "primary_noise", "secondary_noise",
    "actuator_meter_noise", "primary_reading", "secondary_reading", "pairwise_residual",
    "nominal_bulk_stock", "balance_residual", "commanded_supplement",
    "delivered_supplement", "metered_supplement", "actuator_residual",
    "disagreement_triggered", "balance_triggered", "actuator_triggered",
    "consecutive_fault_count", "fault_detected", "fallback_active",
    "actuator_isolated", "applied_supplement",
)


def _validate_faults(items, duration, step):
    if not isinstance(items, list) or len(items) > 16:
        raise InputError("control faults must be a list of at most 16 intervals")
    result = []
    previous_end = -1.0
    for item in items:
        fields(item, ("start", "end", "kind", "magnitude"), "control faults")
        start = number(item["start"], "control faults start", 0, duration)
        end = number(item["end"], "control faults end", 0, duration)
        if end <= start or start < previous_end:
            raise InputError("control faults intervals must be ordered, positive and nonoverlapping")
        kind = item["kind"]
        if not isinstance(kind, str) or kind not in FAULT_KINDS:
            raise InputError(f"control faults kind must be one of: {', '.join(FAULT_KINDS)}")
        magnitude = number(item["magnitude"], "fault magnitude", -1_000_000, 1_000_000)
        if kind in {"primary_dropout", "common_sensor_dropout"} and magnitude != 0:
            raise InputError("Dropout magnitude must be zero")
        if abs(start / step - round(start / step)) > 1e-9 \
                or abs(end / step - round(end / step)) > 1e-9:
            raise InputError("control faults must begin and end on the output grid")
        result.append({"start": start, "end": end, "kind": kind, "magnitude": magnitude})
        previous_end = end
    return result


def _validate_experiment(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
                    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
                    "monitor", "variants", "analysis", "fault_experiment"), "config")
    experiment = config["fault_experiment"]
    fields(experiment, ("disagreement_threshold", "balance_threshold", "actuator_threshold",
                        "actuator_noise_sd", "confirmation_samples", "fallback_policy",
                        "control_faults"), "fault_experiment")
    parsed_experiment = {}
    for key in ("disagreement_threshold", "balance_threshold", "actuator_threshold"):
        value = number(experiment[key], key, 0, 10)
        if value <= 0:
            raise InputError(f"{key} must lie in (0, 10]")
        parsed_experiment[key] = value
    parsed_experiment["actuator_noise_sd"] = number(
        experiment["actuator_noise_sd"], "actuator_noise_sd", 0, 1)
    confirmations = experiment["confirmation_samples"]
    if isinstance(confirmations, bool) or not isinstance(confirmations, int) \
            or not 1 <= confirmations <= 20:
        raise InputError("confirmation_samples must be an integer in [1, 20]")
    parsed_experiment["confirmation_samples"] = confirmations
    if experiment["fallback_policy"] != "freeze_supplement_and_isolate_actuator":
        raise InputError("fallback_policy must be freeze_supplement_and_isolate_actuator")
    parsed_experiment["fallback_policy"] = experiment["fallback_policy"]
    base = {key: value for key, value in config.items() if key != "fault_experiment"}
    parsed = _validate(base)
    duration, step = parsed[:2]
    faults = _validate_faults(experiment["control_faults"], duration, step)
    return parsed, parsed_experiment, faults


def _declared_fault_at(faults, time):
    """Return the left-hand sample fault; integration itself remains half-open."""
    for item in faults:
        if item["start"] <= time <= item["end"]:
            return item
    return None


def _delivered(commanded, fault, isolated, supplement_max):
    offset = 0.0 if isolated or not fault or fault["kind"] != "actuator_offset" \
        else fault["magnitude"]
    return min(supplement_max, max(0.0, commanded + offset))


def _actuator_rk4_step(time, state, substep, parameters, held_reading, operating, offset):
    """Canonical RK4 with only the physical bulk supplement perturbed."""
    control = parameters[4]

    def rates(clock, value):
        result = _right_hand_side(clock, value, parameters, held_reading, operating)
        physical = min(control["supplement_max"], max(0.0, value[6] + offset))
        result[1] += physical - value[6]
        return result

    first = rates(time, state)
    second = rates(time + 0.5 * substep,
                   [value + 0.5 * substep * rate for value, rate in zip(state, first)])
    third = rates(time + 0.5 * substep,
                  [value + 0.5 * substep * rate for value, rate in zip(state, second)])
    fourth = rates(time + substep,
                   [value + substep * rate for value, rate in zip(state, third)])
    return [value + substep * (a + 2 * b + 2 * c + d) / 6.0
            for value, a, b, c, d in zip(state, first, second, third, fourth)]


def _fault_run(name, variant, shared, duration, step, boundaries, mode, experiment, control_faults):
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

    # Independent streams are reset per run: every mode sees the same noise at t.
    rng_control = random.Random(seed)
    rng_monitor = random.Random(seed + 1)
    rng_secondary = random.Random(seed + 2)
    rng_actuator = random.Random(seed + 3)
    state = [1.0, 0.0, 0.0, 0.0, 0.0, reserve["initial"], 0.0]
    nominal = list(state)
    held_reading = 0.0
    fallback = False
    actuator_isolated = False
    consecutive_count = 0
    rows, observations = [], []
    work = 0
    edges = sorted({item[key] for item in outages for key in ("start", "end")})
    disagreement_threshold = experiment["disagreement_threshold"]
    balance_threshold = experiment["balance_threshold"]
    actuator_threshold = experiment["actuator_threshold"]
    actuator_noise_sd = experiment["actuator_noise_sd"]
    confirmations = experiment["confirmation_samples"]

    for index, time in enumerate(times):
        primary_noise = rng_control.gauss(0.0, noise_sd) if noise_sd else 0.0
        secondary_noise = rng_secondary.gauss(0.0, noise_sd) if noise_sd else 0.0
        actuator_noise = rng_actuator.gauss(0.0, actuator_noise_sd) if actuator_noise_sd else 0.0
        fault = _declared_fault_at(control_faults, time)
        kind = fault["kind"] if fault else ""
        primary_available = kind not in {"primary_dropout", "common_sensor_dropout"}
        secondary_available = kind != "common_sensor_dropout"
        primary = None if not primary_available else state[1] + primary_noise
        secondary = None if not secondary_available else state[1] + secondary_noise
        if kind in {"primary_bias", "common_sensor_bias"} and primary is not None:
            primary += fault["magnitude"]
        if kind == "common_sensor_bias" and secondary is not None:
            secondary += fault["magnitude"]
        pairwise = abs(primary - secondary) if primary is not None and secondary is not None else None
        balance = abs(primary - nominal[1]) if primary is not None else None

        delivered = 0.0 if index == 0 else _delivered(
            state[6], fault, actuator_isolated, control["supplement_max"])
        metered = delivered + actuator_noise
        actuator_residual = abs(metered - state[6])
        disagreement_triggered = not primary_available or not secondary_available or \
            pairwise > disagreement_threshold
        balance_triggered = balance is not None and balance > balance_threshold
        actuator_triggered = actuator_residual > actuator_threshold

        size = 1.0 + growth["linear_rate"] * time
        capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
        demand = scaling["demand_coefficient"] * size
        boundary_delivered = min(demand * state[0], capacity)
        if _in_outage(outages, time):
            boundary_delivered *= reserve["fraction"] if state[5] > 0 else 0.0
        # As in T28, a trajectory row records the policy state entering the sample;
        # the observation below records a decision made at that sample.
        rows.append({"dimensionless_time": time, "size": size,
                     "capacity_margin": capacity / demand, "request_fraction": state[0],
                     "served_fraction": boundary_delivered / demand,
                     "delivered_flux": boundary_delivered, "bulk_stock": state[1],
                     "deep_receipt_rate": internal["use"] * state[2],
                     "cumulative_unserved": state[3], "progression": state[4],
                     "reserve": state[5], "supplement": state[6],
                     "controller_reading": held_reading, "commanded_supplement": state[6],
                     "delivered_supplement": delivered, "nominal_bulk_stock": nominal[1],
                     "fallback_active": fallback, "actuator_isolated": actuator_isolated})

        if mode == "balance_augmented_freeze":
            selected_trigger = disagreement_triggered or balance_triggered or actuator_triggered
        else:
            selected_trigger = disagreement_triggered
        consecutive_count = consecutive_count + 1 if selected_trigger else 0
        detected = mode != "single_sensor" and consecutive_count >= confirmations
        if detected:
            fallback = True
            # Sensor-only fallback must not pre-clamp a later, independent actuator
            # challenge. Confirmed actuator faults latch both freeze and isolation.
            if mode == "balance_augmented_freeze" and kind == "actuator_offset":
                actuator_isolated = True
        next_fault = _fault_at(control_faults, time)
        applied = _delivered(state[6], next_fault, actuator_isolated, control["supplement_max"])
        observations.append({
            "mode": mode, "variant": name, "dimensionless_time": time,
            "interval_index": index, "declared_fault": kind,
            "primary_available": primary_available, "secondary_available": secondary_available,
            "primary_noise": primary_noise, "secondary_noise": secondary_noise,
            "actuator_meter_noise": actuator_noise, "primary_reading": primary,
            "secondary_reading": secondary, "pairwise_residual": pairwise,
            "nominal_bulk_stock": nominal[1], "balance_residual": balance,
            "commanded_supplement": state[6], "delivered_supplement": delivered,
            "metered_supplement": metered, "actuator_residual": actuator_residual,
            "disagreement_triggered": disagreement_triggered,
            "balance_triggered": balance_triggered, "actuator_triggered": actuator_triggered,
            "consecutive_fault_count": consecutive_count, "fault_detected": detected,
            "fallback_active": fallback, "actuator_isolated": actuator_isolated,
            "applied_supplement": applied,
        })
        if index == len(times) - 1:
            break

        held_reading = bulk["target"] if fallback else (primary if primary is not None else bulk["target"])
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
                state[5] = nominal[5] = 0.0
                continue
            count = max(1, math.ceil((stop - cursor) * rate_scale / SUBSTEP_RATE_TARGET))
            work += count
            if work > MAX_TOTAL_SUBSTEPS:
                raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
            segment_start, segment_reserve = cursor, state[5]
            substep = (stop - cursor) / count
            active_fault = _fault_at(control_faults, cursor)
            offset = 0.0 if actuator_isolated or not active_fault or \
                active_fault["kind"] != "actuator_offset" else active_fault["magnitude"]
            for inner in range(count):
                subtime = segment_start + inner * substep
                if offset:
                    state = _actuator_rk4_step(subtime, state, substep, parameters,
                                               held_reading, (power, draw), offset)
                else:
                    state = _rk4_step(subtime, state, substep, parameters, held_reading,
                                      (power, draw))
                nominal = _rk4_step(subtime, nominal, substep, parameters, held_reading,
                                    (power, draw))
                require_finite(state)
                require_finite(nominal)
                for value in (state, nominal):
                    value[0] = min(max(value[0], 0.0), 1.0)
                    value[6] = min(max(value[6], 0.0), control["supplement_max"])
                    for position in (1, 2, 3, 4):
                        value[position] = max(value[position], 0.0)
                    value[5] = max(0.0, segment_reserve - draw * (inner + 1) * substep)
            if depletion is not None and stop == depletion:
                state[5] = nominal[5] = 0.0
            cursor = stop
    return rows, observations


def _mode_comparison(mode, single, rows, observations):
    per_kind = {}
    for kind in FAULT_KINDS:
        kind_rows = [row for row in observations if row["declared_fault"] == kind]
        detections = [row for row in kind_rows if row["fault_detected"]]
        first = min((row["dimensionless_time"] for row in detections), default=None)
        # Confirmation is visible in the trajectory on the following output row.
        # Count only subsequent samples in the same declared fault window.
        detected_samples = sum(row["dimensionless_time"] > first for row in kind_rows) \
            if first is not None else 0
        per_kind[kind] = {
            "fault_samples": len(kind_rows),
            "detected_fault_samples": detected_samples,
            "undetected_fault_samples": len(kind_rows) - detected_samples,
            "first_detection_time": first,
        }
    detected = [row for row in observations if row["fault_detected"]]
    false_alarms = [row for row in detected if not row["declared_fault"]]
    return {
        "fault_samples": sum(item["fault_samples"] for item in per_kind.values()),
        "detected_fault_samples": sum(item["detected_fault_samples"] for item in per_kind.values()),
        "undetected_fault_samples": sum(item["undetected_fault_samples"] for item in per_kind.values()),
        "false_alarm_samples": len(false_alarms),
        "first_detection_time": min((row["dimensionless_time"] for row in detected), default=None),
        "fallback_ever_active": any(row["fallback_active"] for row in observations),
        "actuator_isolation_ever_active": any(row["actuator_isolated"] for row in observations),
        "per_fault_kind": per_kind,
        "final_bulk_single_sensor": single[-1]["bulk_stock"],
        "final_bulk_stock": rows[-1]["bulk_stock"],
        "final_progression_single_sensor": single[-1]["progression"],
        "final_progression": rows[-1]["progression"],
        "max_absolute_bulk_difference": max(abs(a["bulk_stock"] - b["bulk_stock"])
                                             for a, b in zip(single, rows)),
        "max_absolute_progression_difference": max(abs(a["progression"] - b["progression"])
                                                    for a, b in zip(single, rows)),
    }


def _canonical_and_hidden_checks(variants, shared, duration, step, boundaries, experiment):
    from .whole_path_twin import _variant_run

    no_fault_matches = True
    for name in sorted(variants):
        actual, _observations = _fault_run(
            name, variants[name], shared, duration, step, boundaries,
            "single_sensor", experiment, [])
        canonical = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        for actual_row, expected_row in zip(actual, canonical):
            if any(actual_row[key] != expected_row[key] for key in expected_row):
                no_fault_matches = False

    # Hold serve_rate fixed and change only hidden internal efficiency. All
    # detector inputs must remain bit-identical even though tissue/progression differ.
    base_name = sorted(variants)[0]
    base_variant = variants[base_name]
    alternate_efficiency = 0.0 if base_variant["internal_efficiency"] else 1.0
    alternate = {**base_variant, "internal_efficiency": alternate_efficiency}
    base_rows, base_observations = _fault_run(
        base_name, base_variant, shared, duration, step, boundaries,
        "balance_augmented_freeze", experiment, [])
    alternate_rows, alternate_observations = _fault_run(
        base_name, alternate, shared, duration, step, boundaries,
        "balance_augmented_freeze", experiment, [])
    stop = next((index for index, row in enumerate(base_observations)
                 if row["fallback_active"] or alternate_observations[index]["fallback_active"]),
                len(base_rows))
    boundary_columns = (
        "dimensionless_time", "size", "capacity_margin", "request_fraction",
        "served_fraction", "delivered_flux", "bulk_stock", "reserve", "supplement",
        "controller_reading", "commanded_supplement", "delivered_supplement",
        "nominal_bulk_stock", "fallback_active", "actuator_isolated",
    )
    residual_columns = (
        "primary_available", "secondary_available", "primary_noise", "secondary_noise",
        "actuator_meter_noise", "primary_reading", "secondary_reading", "pairwise_residual",
        "nominal_bulk_stock", "balance_residual", "commanded_supplement",
        "delivered_supplement", "metered_supplement", "actuator_residual",
        "disagreement_triggered", "balance_triggered", "actuator_triggered",
        "applied_supplement",
    )
    boundary_match = all(all(left[key] == right[key] for key in boundary_columns)
                         for left, right in zip(base_rows[:stop], alternate_rows[:stop]))
    residual_match = all(all(left[key] == right[key] for key in residual_columns)
                         for left, right in zip(base_observations[:stop], alternate_observations[:stop]))
    internal_differs = any(left["deep_receipt_rate"] != right["deep_receipt_rate"]
                           or left["progression"] != right["progression"]
                           for left, right in zip(base_rows, alternate_rows))
    hidden = {
        "internal_tissue_observed_by_fallback": False,
        "method": "Paired no-fault runs hold serve_rate fixed and alter only internal_efficiency; comparison stops before fallback.",
        "variant": base_name,
        "serve_rate": base_variant["serve_rate"],
        "internal_efficiencies": [base_variant["internal_efficiency"], alternate_efficiency],
        "pre_fallback_samples_compared": stop,
        "boundary_channels_identical_before_fallback": boundary_match,
        "sensor_balance_actuator_residuals_identical_before_fallback": residual_match,
        "internal_channels_differ": internal_differs,
        "unobservable_without_internal_channels": boundary_match and residual_match and internal_differs,
        "compared_boundary_channels": list(boundary_columns),
        "compared_residual_channels": list(residual_columns),
    }
    return no_fault_matches, hidden


def common_cause_fault(config_path: Path, output: Path) -> dict:
    """Publish the deterministic common-cause fault discriminator bundle."""
    config, raw = read_json(config_path)
    parsed, experiment, faults = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, variants, analysis) = parsed
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, monitor_faults)
    runs, all_observations = {}, []
    for mode in MODES:
        for name in sorted(variants):
            rows, observations = _fault_run(
                name, variants[name], shared, duration, step, boundaries, mode, experiment, faults)
            runs[(mode, name)] = rows
            all_observations.extend(observations)

    no_fault_matches, hidden = _canonical_and_hidden_checks(
        variants, shared, duration, step, boundaries, experiment)
    comparisons = []
    for name in sorted(variants):
        single = runs[("single_sensor", name)]
        comparisons.append({
            "variant": name,
            "disagreement_freeze": _mode_comparison(
                "disagreement_freeze", single, runs[("disagreement_freeze", name)],
                [row for row in all_observations
                 if row["variant"] == name and row["mode"] == "disagreement_freeze"]),
            "balance_augmented_freeze": _mode_comparison(
                "balance_augmented_freeze", single, runs[("balance_augmented_freeze", name)],
                [row for row in all_observations
                 if row["variant"] == name and row["mode"] == "balance_augmented_freeze"]),
        })
    qualification_status = ("dimensionless_software_checks_passed"
                            if no_fault_matches and hidden["unobservable_without_internal_channels"]
                            else "dimensionless_software_checks_failed")
    report = {
        "schema_version": 1,
        "notice": NOTICE,
        "fixture_notice": NOTICE,
        "result_kind": "dimensionless_common_cause_fault",
        "model_family": "dimensionless_whole_path_common_cause_fault_experiment",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "qualification_status": qualification_status,
        "modes": list(MODES),
        "variants": sorted(variants),
        "fault_contract": {
            "supported_faults": list(FAULT_KINDS),
            "primary_noise_seed": seed,
            "research_monitor_noise_seed": seed + 1,
            "secondary_noise_seed": seed + 2,
            "actuator_meter_noise_seed": seed + 3,
            "noise_streams_independent": True,
            "shared_sensor_noise_sd": noise_sd,
            "actuator_noise_sd": experiment["actuator_noise_sd"],
            "disagreement_threshold": experiment["disagreement_threshold"],
            "balance_threshold": experiment["balance_threshold"],
            "actuator_threshold": experiment["actuator_threshold"],
            "confirmation_samples": experiment["confirmation_samples"],
            "fallback_policy": experiment["fallback_policy"],
            "pairwise_residual": "abs(primary_reading - secondary_reading), or missing when either sensor is unavailable",
            "balance_residual": "abs(primary_reading - nominal_bulk_stock); nominal_bulk_stock integrates commanded supplement without actuator offset",
            "actuator_residual": "abs(metered_supplement - commanded_supplement)",
            "sample_fault_convention": "Declared fault samples include both endpoints (left-hand reading at end); integration fault intervals are half-open.",
            "detected_sample_convention": "For each fault kind, samples strictly after its first confirmed detection count as detected, matching the next-output-row policy response.",
            "fallback": "Latching frozen synthetic supplement at the pre-detection controller target",
            "actuator_isolation": "A confirmed actuator_offset also latches actuator isolation, clamping its declared offset to zero; sensor-only detections do not pre-clamp later actuator challenges.",
            "internal_tissue_observed_by_fallback": False,
        },
        "declared_control_faults": faults,
        "no_fault_canonical_trajectories_match": bool(no_fault_matches),
        "comparisons": comparisons,
        "hidden_internal_state_check": hidden,
        "interpretation": [
            "Pairwise disagreement detects a primary-only sensor fault but is structurally blind to an identical shared sensor bias and to a downstream actuator offset.",
            "The commanded-supplement shadow preserves nominal_bulk_stock == true bulk_stock when no actuator offset is active, so the no-fault balance residual is exactly primary sensor noise.",
            "The actuator meter and shadow-balance innovation expose the actuator offset; confirmed augmented fallback freezes the command and removes that offset.",
            "Detection and isolation are software accounting only: no internal tissue state is observed and no physical alarm, safe state or recovery is established.",
        ],
        "limits": [
            "All values, faults, thresholds, noise streams and times are invented dimensionless software fixture quantities.",
            "Seeded independent noise is a software assumption, not demonstrated sensor independence, meter accuracy or calibrated uncertainty.",
            "The frozen supplement and actuator isolation are conservative software policies, not hardware-safe states, operating instructions or validated alarm designs.",
            "Declared noise thresholds and confirmation counts do not establish detection probabilities or performance under drift, delays, saturation, combined faults or unmodelled faults.",
            "The shadow uses the same nominal model as the plant; model error and unknown common dynamics can create innovations or hide faults.",
            "No biological measurement, physiological calibration, machine control, procurement or gate movement is established.",
        ],
    }
    lines = [
        "# Dimensionless common-cause sensor and actuator fault discrimination", "", NOTICE, "",
        f"Thresholds: disagreement {experiment['disagreement_threshold']}, balance "
        f"{experiment['balance_threshold']}, actuator {experiment['actuator_threshold']}; "
        f"{experiment['confirmation_samples']} consecutive sample(s) confirm detection.", "",
        "The augmented mode adds shadow-balance and actuator-meter innovations to pairwise disagreement. "
        "It observes no internal tissue channel.", "",
        "## Variant comparisons", "",
    ]
    for comparison in comparisons:
        lines.append(f"### {comparison['variant']}")
        lines.append("")
        for mode in MODES[1:]:
            row = comparison[mode]
            kinds = ", ".join(
                f"{kind} {item['detected_fault_samples']}/{item['fault_samples']}"
                for kind, item in row["per_fault_kind"].items() if item["fault_samples"])
            lines.append(f"- {mode}: {kinds or 'no declared faults'}; "
                         f"{row['false_alarm_samples']} false-alarm samples; "
                         f"first confirmation {row['first_detection_time']}; maximum bulk difference "
                         f"{row['max_absolute_bulk_difference']:.6g}.")
        lines.append("")
    lines.extend([
        f"No-fault canonical trajectory match: {no_fault_matches}.",
        f"Hidden internal-state boundary check: {hidden['unobservable_without_internal_channels']}.",
        "", *report["interpretation"], "", "## Limits", "",
    ])
    lines.extend(f"- {item}" for item in report["limits"])
    files = {
        "source_config.json": raw,
        "fault_observations.csv": csv_bytes(list(OBSERVATION_COLUMNS), all_observations),
        "common_cause_fault_report.json": json_bytes(report),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    for (mode, name), rows in sorted(runs.items()):
        files[f"trajectory_{mode}_{name}.csv"] = csv_bytes(list(TRAJECTORY_COLUMNS), rows)
    return publish_bundle(
        output, kind="dimensionless_common_cause_fault", input_raw=raw, files=files,
        metadata={"biological_measurements": False, "physiologically_calibrated": False,
                  "human_gestation_prediction": False, "n_variants": len(variants),
                  "n_modes": len(MODES), "qualification_status": qualification_status})
