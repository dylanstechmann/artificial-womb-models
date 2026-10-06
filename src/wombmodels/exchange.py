"""Exact piecewise transitions for a dimensionless software fixture.

No parameter represents physiology, time in days, a device setpoint or an
actuator. The substrate/waste compartments are abstract accounting stocks.
"""
from __future__ import annotations

import math
import random
from bisect import bisect_left
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json

NOTICE = "Artificial dimensionless software fixture; no physiological calibration, biological prediction or machine-control output."


def number(value, label, low=0.0, high=1_000_000.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be a finite number")
    try:
        value = float(value)
    except OverflowError as error:
        raise InputError(f"{label} must be a finite number") from error
    if not math.isfinite(value) or not low <= value <= high:
        raise InputError(f"{label} must lie in [{low}, {high}]")
    return value


def fields(value, required, label):
    if not isinstance(value, dict) or set(value) != set(required):
        raise InputError(f"{label} must contain exactly: {', '.join(required)}")


def intervals(items, duration, label, *, faults=False):
    if not isinstance(items, list) or len(items) > 100:
        raise InputError(f"{label} must be a list of at most 100 intervals")
    result = []
    previous_end = -1.0
    for item in items:
        fields(item, ("start", "end", "kind", "magnitude") if faults else ("start", "end"), label)
        start = number(item["start"], f"{label} start", 0, duration)
        end = number(item["end"], f"{label} end", 0, duration)
        if end <= start or start < previous_end:
            raise InputError(f"{label} intervals must be ordered, positive and nonoverlapping")
        saved = {"start": start, "end": end}
        if faults:
            if not isinstance(item["kind"], str) or item["kind"] not in {"bias", "dropout"}:
                raise InputError("Monitor faults must be bias or dropout")
            magnitude = number(item["magnitude"], "fault magnitude", -1_000_000, 1_000_000)
            if item["kind"] == "dropout" and magnitude != 0:
                raise InputError("Dropout magnitude must be zero")
            saved.update(kind=item["kind"], magnitude=magnitude)
        result.append(saved)
        previous_end = end
    return result


def validate_config(config):
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "initial", "rates",
                    "wall_outages", "monitor", "monitor_faults"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    fields(config["dimensionless_time"], ("duration", "output_step"), "dimensionless_time")
    duration = number(config["dimensionless_time"]["duration"], "duration", 1e-6, 10_000)
    step = number(config["dimensionless_time"]["output_step"], "output_step", 1e-6, duration)
    if duration / step > 50_000:
        raise InputError("At most 50,000 output intervals are permitted")
    fields(config["initial"], ("substrate", "waste", "backup_reserve"), "initial")
    initial = {key: number(value, key) for key, value in config["initial"].items()}
    fields(config["rates"], ("powered_input", "conversion", "powered_clearance", "backup_draw"), "rates")
    rates = {key: number(value, key, 0, 1000) for key, value in config["rates"].items()}
    if rates["backup_draw"] == 0 and initial["backup_reserve"] > 0:
        raise InputError("A positive backup reserve requires a positive synthetic draw rate")
    fields(config["monitor"], ("noise_sd", "residual_threshold", "seed", "requires_exchange_power"), "monitor")
    monitor = config["monitor"]
    noise = number(monitor["noise_sd"], "noise_sd", 0, 1000)
    threshold = number(monitor["residual_threshold"], "residual_threshold", 1e-12, 1000)
    seed = monitor["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**32 - 1:
        raise InputError("seed must be an integer in [0, 2**32-1]")
    if not isinstance(monitor["requires_exchange_power"], bool):
        raise InputError("requires_exchange_power must be boolean")
    return {"duration": duration, "step": step, "initial": initial, "rates": rates,
            "outages": intervals(config["wall_outages"], duration, "wall_outages"),
            "faults": intervals(config["monitor_faults"], duration, "monitor_faults", faults=True),
            "monitor": {**monitor, "noise_sd": noise, "residual_threshold": threshold}}


def transition(substrate, waste, delta, input_rate, conversion, clearance):
    """Analytic nonnegative solution and independent accumulated flux identities."""
    if conversion == 0:
        final_substrate = substrate + input_rate * delta
        final_waste = waste * math.exp(-clearance * delta)
    else:
        decay_s = math.exp(-conversion * delta)
        q = input_rate / conversion
        final_substrate = substrate * decay_s + q * (-math.expm1(-conversion * delta))
        if clearance == 0:
            final_waste = waste + input_rate * delta + (substrate - q) * (-math.expm1(-conversion * delta))
        else:
            decay_w = math.exp(-clearance * delta)
            # expm1 avoids cancellation when rates are close. The exact equal
            # rate limit is t exp(-k t), including k == clearance.
            gap = clearance - conversion
            if gap == 0:
                convolution = delta * decay_s
            elif gap > 0:
                convolution = decay_s * (-math.expm1(-gap * delta)) / gap
            else:
                convolution = decay_w * math.expm1(gap * delta) / gap
            final_waste = (waste * decay_w + input_rate * (-math.expm1(-clearance * delta)) / clearance
                           + conversion * (substrate - q) * convolution)
    if not all(math.isfinite(value) for value in (final_substrate, final_waste)):
        raise InputError("Numerical fixture exceeds floating-point range")
    tolerance = 1e-9 * max(1.0, substrate, waste, input_rate * delta)
    if min(final_substrate, final_waste) < -tolerance:
        raise InputError("Numerical solution became negative; choose a less extreme fixture")
    final_substrate = max(0.0, final_substrate)
    final_waste = max(0.0, final_waste)
    amount_input = input_rate * delta
    amount_converted = substrate + amount_input - final_substrate
    amount_cleared = waste + amount_converted - final_waste
    if min(amount_converted, amount_cleared) < -tolerance:
        raise InputError("Numerical flux became negative; choose a less extreme fixture")
    return final_substrate, final_waste, amount_input, max(0.0, amount_converted), max(0.0, amount_cleared)


def active(items, time):
    return next((item for item in items if item["start"] <= time < item["end"]), None)


def run_fixture(config):
    parsed = validate_config(config)
    duration, step = parsed["duration"], parsed["step"]
    rates, monitor = parsed["rates"], parsed["monitor"]
    scheduled = {0.0, duration}
    scheduled.update(min(duration, index * step) for index in range(1, math.ceil(duration / step)))
    grid = set(scheduled)
    grid.update(event[edge] for events in (parsed["outages"], parsed["faults"])
                for event in events for edge in ("start", "end"))
    points = sorted(grid)
    initial = parsed["initial"]
    substrate, waste, reserve = initial["substrate"], initial["waste"], initial["backup_reserve"]
    total_input = total_converted = total_cleared = total_reserve_used = 0.0
    rng = random.Random(monitor["seed"])
    rows = []
    tp = fp = tn = fn = 0
    index = 0
    while index < len(points):
        time = points[index]
        wall_on = active(parsed["outages"], time) is None
        power_source = "wall" if wall_on else ("backup" if reserve > 0 else "none")
        powered = power_source != "none"
        fault = active(parsed["faults"], time)
        no_power = monitor["requires_exchange_power"] and not powered
        unavailable = no_power or (fault is not None and fault["kind"] == "dropout")
        sampled = time in scheduled
        reading = None if not sampled or unavailable else substrate + rng.gauss(0, monitor["noise_sd"])
        if reading is not None and fault is not None and fault["kind"] == "bias":
            reading += fault["magnitude"]
        residual = None if reading is None else reading - substrate
        alarm = (reading is None or abs(residual) > monitor["residual_threshold"]) if sampled else None
        fault_truth = no_power or fault is not None
        if sampled:
            if fault_truth and alarm:
                tp += 1
            elif fault_truth:
                fn += 1
            elif alarm:
                fp += 1
            else:
                tn += 1
        substrate_residual = substrate - initial["substrate"] - total_input + total_converted
        waste_residual = waste - initial["waste"] - total_converted + total_cleared
        rows.append({"dimensionless_time": time, "substrate": substrate, "waste": waste,
                     "backup_reserve": reserve, "power_source": power_source,
                     "cumulative_input": total_input, "cumulative_conversion": total_converted,
                     "cumulative_clearance": total_cleared, "cumulative_reserve_use": total_reserve_used,
                     "substrate_balance_residual": substrate_residual, "waste_balance_residual": waste_residual,
                     "total_balance_residual": math.fsum((substrate, waste, total_cleared,
                                                           -initial["substrate"], -initial["waste"], -total_input)),
                     "reserve_balance_residual": reserve + total_reserve_used - initial["backup_reserve"],
                     "sensor_sampled": sampled, "sensor_reading": reading, "oracle_sensor_residual": residual,
                     "synthetic_sensor_fault": fault_truth, "software_alarm": alarm})
        if index == len(points) - 1:
            break
        next_time = points[index + 1]
        depletes = False
        if power_source == "backup":
            available_delta = reserve / rates["backup_draw"]
            depletes = available_delta <= next_time - time
            if depletes:
                depletion = time + available_delta
                if depletion <= time:
                    raise InputError("Backup event is below floating-point time resolution")
                if depletion < next_time:
                    points.insert(index + 1, depletion)
                    next_time = depletion
        delta = next_time - time
        substrate, waste, supplied, converted, cleared = transition(
            substrate, waste, delta, rates["powered_input"] if powered else 0.0,
            rates["conversion"], rates["powered_clearance"] if powered else 0.0)
        total_input += supplied
        total_converted += converted
        total_cleared += cleared
        if power_source == "backup":
            used = reserve if depletes else min(reserve, rates["backup_draw"] * delta)
            reserve -= used
            total_reserve_used += used
        index += 1
    fault_intervals = list(parsed["faults"])
    # Include intervals of correlated monitor/exchange power loss in the same
    # synthetic detector evaluation, without treating wall outages as sensor faults.
    if monitor["requires_exchange_power"]:
        shared = None
        for position, row in enumerate(rows[:-1]):
            if row["power_source"] == "none":
                if shared is None:
                    shared = {"start": row["dimensionless_time"], "end": None, "kind": "shared_power_loss"}
                    fault_intervals.append(shared)
                shared["end"] = rows[position + 1]["dimensionless_time"]
            else:
                shared = None
    alarm_times = [row["dimensionless_time"] for row in rows if row["software_alarm"]]
    detection = []
    for event in fault_intervals:
        alarm_index = bisect_left(alarm_times, event["start"])
        found = (alarm_times[alarm_index] if alarm_index < len(alarm_times)
                 and alarm_times[alarm_index] < event["end"] else None)
        detection.append({"kind": event["kind"], "start": event["start"], "end": event["end"],
                          "first_alarm": found, "dimensionless_detection_delay": None if found is None else found - event["start"]})
    result = {"schema_version": 1, "fixture_notice": NOTICE,
              "result_kind": "synthetic_exchange_software_fixture", "biological_assay_performed": False,
              "physiologically_calibrated": False, "human_gestation_prediction": False,
              "n_samples": len(rows), "n_monitor_samples": len(scheduled),
              "final_state": {key: rows[-1][key] for key in ("substrate", "waste", "backup_reserve")},
              "balances": {key: max(abs(row[key]) for row in rows) for key in
                           ("substrate_balance_residual", "waste_balance_residual", "total_balance_residual", "reserve_balance_residual")},
              "software_fault_metrics": {"detector": "oracle residual or missing reading; synthetic ground truth known",
                                         "counting_unit": "scheduled output timestamp, not independent experiment",
                                         "true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
                                         "recall": tp / (tp + fn) if tp + fn else None,
                                         "false_positive_rate": fp / (fp + tn) if fp + tn else None,
                                         "fault_intervals": detection},
              "limits": ["All parameters, thresholds and time values are invented dimensionless software fixtures.",
                         "Oracle residuals use unavailable real-world ground truth and are not a deployable detector.",
                         "Sensor metrics depend on scheduled output cadence and do not establish biological safety.",
                         "Exchange and power are abstract stocks; implantation, placenta, growth and organ development are absent.",
                         "No claim about complete gestation, surrogacy or congenital-defect reduction is computed."]}
    return rows, result


def simulate(config_path: Path, output: Path) -> dict:
    config, raw = read_json(config_path)
    rows, result = run_fixture(config)
    lines = ["# Dimensionless exchange software fixture", "", NOTICE, "",
             "This run is a numerical software demonstration. Time is dimensionless and has no mapping to hours, days or nine months.",
             "", "The synthetic monitor compares readings with known simulated substrate truth. It is not a validated biological monitoring algorithm.",
             "", "## Balance residuals", ""]
    lines.extend(f"- {key}: {value:.6g}" for key, value in result["balances"].items())
    lines.extend(["", "## Software fault metrics", "", "```json", json_bytes(result["software_fault_metrics"]).decode().rstrip(), "```", "",
                  "## Limits", ""])
    lines.extend(f"- {item}" for item in result["limits"])
    files = {"input_config.json": raw, "trajectory.csv": csv_bytes(list(rows[0]), rows),
             "simulation_summary.json": json_bytes(result), "REPORT.md": ("\n".join(lines) + "\n").encode()}
    return publish_bundle(output, kind="synthetic_exchange_software_fixture", input_raw=raw, files=files,
                          metadata={"physiologically_calibrated": False, "biological_assay_performed": False,
                                    "human_gestation_prediction": False})
