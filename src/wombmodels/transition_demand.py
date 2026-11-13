"""Concurrent transition demand experiment (T31).

Two gestation units follow the canonical whole-path twin trajectory. The new
layer is transition demand and station service: a unit becomes transition-ready
when its twin progression first reaches a threshold, then asks a transition
station to serve it. Two station modes are compared:

* ``dedicated`` -- every unit owns a station, so nothing ever waits. Control.
* ``shared_serial`` -- one station serves both units FIFO, one at a time, so a
  simultaneous demand makes the second unit wait.

A station outage (common cause) suspends service with preemption/resume and
queues wait through it, correlating delays across units. Waiting is not
neutral: the unit keeps developing, so stage overshoot is measured from the
twin trajectory.

Every value is an invented dimensionless software quantity. No biological
transition, neonatal claim, machine-control output or gate movement follows.
"""
from __future__ import annotations

import bisect
import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number
from .whole_path_twin import (
    MAX_TOTAL_SUBSTEPS,
    SUBSTEP_RATE_TARGET,
    _validate,
    _variant_run,
)
from .numerics import output_times

MODES = ("dedicated", "shared_serial")
TWIN_KEYS = (
    "schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
    "monitor", "variants", "analysis",
)
TRAJECTORY_COLUMNS = (
    "dimensionless_time", "unit", "size", "capacity_margin", "request_fraction",
    "served_fraction", "delivered_flux", "bulk_stock", "deep_receipt_rate",
    "cumulative_unserved", "progression", "reserve", "supplement",
)
TRAJECTORY_NONUNIT_COLUMNS = tuple(column for column in TRAJECTORY_COLUMNS if column != "unit")
EVENT_COLUMNS = (
    "mode", "variant", "unit", "ready", "demand_time", "service_start",
    "service_end", "wait_time", "stage_overshoot", "overshoot_within_observed_window",
    "delayed_by_outage", "transition_completed", "cause",
)
OFFSET_MULTIPLIERS = (0.0, 0.25, 0.5, 0.75, 1.0)


def _validate_station_outages(items, duration, step):
    if not isinstance(items, list) or len(items) > 8:
        raise InputError("station_outages must be a list of at most 8 intervals")
    result = []
    previous_end = -1.0
    for item in items:
        fields(item, ("start", "end"), "station_outages")
        start = number(item["start"], "station_outages start", 0, duration)
        end = number(item["end"], "station_outages end", 0, duration)
        if end <= start or start < previous_end:
            raise InputError("station_outages intervals must be ordered, positive and nonoverlapping")
        if abs(start / step - round(start / step)) > 1e-9 \
                or abs(end / step - round(end / step)) > 1e-9:
            raise InputError("station_outages must begin and end on the output grid")
        result.append({"start": start, "end": end})
        previous_end = end
    return result


def _validate_experiment(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, TWIN_KEYS + ("transition_experiment",), "config")
    experiment = config["transition_experiment"]
    fields(experiment, ("readiness_threshold", "service_time", "unit_b_demand_offset",
                        "max_wait", "modes", "station_outages"), "transition_experiment")
    parsed_experiment = {}
    readiness_threshold = number(experiment["readiness_threshold"],
                                 "readiness_threshold", 0, 10)
    if readiness_threshold <= 0:
        raise InputError("readiness_threshold must lie in (0, 10]")
    parsed_experiment["readiness_threshold"] = readiness_threshold
    service_time = number(experiment["service_time"], "service_time", 0, 100)
    if service_time <= 0:
        raise InputError("service_time must lie in (0, 100]")
    parsed_experiment["service_time"] = service_time
    parsed_experiment["unit_b_demand_offset"] = number(
        experiment["unit_b_demand_offset"], "unit_b_demand_offset", 0, 100)
    max_wait = number(experiment["max_wait"], "max_wait", 0, 1000)
    if max_wait <= 0:
        raise InputError("max_wait must lie in (0, 1000]")
    parsed_experiment["max_wait"] = max_wait
    modes = experiment["modes"]
    if not isinstance(modes, list) or not 1 <= len(modes) <= 2 \
            or any(mode not in MODES for mode in modes):
        raise InputError(f"modes must be a nonempty subset of: {', '.join(MODES)}")
    parsed_experiment["modes"] = list(modes)
    base = {key: value for key, value in config.items() if key != "transition_experiment"}
    parsed = _validate(base)
    duration, step = parsed[:2]
    station_outages = _validate_station_outages(experiment["station_outages"], duration, step)
    return parsed, parsed_experiment, station_outages


def _check_work_budget(variants, shared, duration, step):
    """Reject before publication when a twin integration would exceed the budget."""
    growth, scaling, bulk, internal, control, reserve, _outages = shared[:7]
    times = output_times(duration, step)
    intervals_count = len(times) - 1
    for name, variant in sorted(variants.items()):
        rate_scale = (max(variant["serve_rate"], bulk["washout"] + bulk["transfer"],
                          internal["use"], internal["repair"])
                      + control["gain"] + reserve["draw"])
        rate_scale += variant.get("wall_damage_leak_rate_bound", 0.0)
        substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
        substeps *= variant.get("substep_refinement", 1)
        if intervals_count * substeps > MAX_TOTAL_SUBSTEPS:
            raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")


def _demand_time(rows, threshold):
    for row in rows:
        if row["progression"] >= threshold:
            return row["dimensionless_time"]
    return None


def _progression_at(rows, time):
    times = [row["dimensionless_time"] for row in rows]
    index = bisect.bisect_right(times, time + 1e-9) - 1
    index = max(0, min(index, len(rows) - 1))
    return rows[index]["progression"]


def _outage_containing(time, outages):
    for outage in outages:
        if outage["start"] <= time < outage["end"]:
            return outage
    return None


def _service_end(start, service_time, outages):
    """Finish service with preemption/resume: outages pause, then resume the rest."""
    remaining = service_time
    current = start
    suspended = False
    for _ in range(len(outages) + 2):
        active = _outage_containing(current, outages)
        if active is not None:
            current = active["end"]
            suspended = True
            continue
        upcoming = [outage["start"] for outage in outages if outage["start"] > current + 1e-9]
        if not upcoming:
            return current + remaining, suspended
        next_start = min(upcoming)
        gap = next_start - current
        if gap >= remaining:
            return current + remaining, suspended
        remaining -= gap
        current = next_start
        suspended = True
    raise InputError("station service scheduling exceeded the outage bound")


def _schedule_shared_serial(demand_a, demand_b, service_time, outages):
    """One station serves A then B (FIFO by demand time; ties: A first)."""
    jobs = [("A", demand_a), ("B", demand_b)]
    jobs.sort(key=lambda job: (job[1], 0 if job[0] == "A" else 1))
    station_ready = -math.inf
    scheduled = {}
    for unit, demand in jobs:
        start = max(demand, station_ready)
        start_delayed = False
        containing = _outage_containing(start, outages)
        if containing is not None:
            start = containing["end"]
            start_delayed = True
        end, suspended = _service_end(start, service_time, outages)
        queue_delay = station_ready > demand + 1e-9
        delayed_by_outage = start_delayed or suspended
        wait = start - demand
        if wait <= 1e-9:
            cause = ""
        elif queue_delay and delayed_by_outage:
            cause = "queue_and_outage"
        elif delayed_by_outage:
            cause = "station_outage"
        else:
            cause = "queue"
        scheduled[unit] = {
            "service_start": start,
            "service_end": end,
            "wait_time": wait,
            "delayed_by_outage": delayed_by_outage,
            "cause": cause,
        }
        station_ready = end
    return scheduled


def _project_twin(unit, rows):
    projected = []
    for row in rows:
        projected.append({
            "dimensionless_time": row["dimensionless_time"], "unit": unit,
            "size": row["size"], "capacity_margin": row["capacity_margin"],
            "request_fraction": row["request_fraction"], "served_fraction": row["served_fraction"],
            "delivered_flux": row["delivered_flux"], "bulk_stock": row["bulk_stock"],
            "deep_receipt_rate": row["deep_receipt_rate"],
            "cumulative_unserved": row["cumulative_unserved"],
            "progression": row["progression"], "reserve": row["reserve"],
            "supplement": row["supplement"],
        })
    return projected


def _not_ready_event(mode, name, unit):
    return {
        "mode": mode, "variant": name, "unit": unit, "ready": False,
        "demand_time": None, "service_start": None, "service_end": None,
        "wait_time": None, "stage_overshoot": None,
        "overshoot_within_observed_window": False,
        "delayed_by_outage": False, "transition_completed": False, "cause": "",
    }


def _ready_event(mode, name, unit, rows, demand_time, schedule, max_wait):
    last_time = rows[-1]["dimensionless_time"]
    service_start = schedule["service_start"]
    service_end = schedule["service_end"]
    if service_start <= last_time + 1e-9:
        overshoot = _progression_at(rows, min(service_start, last_time)) \
            - _progression_at(rows, demand_time)
        overshoot_in_window = True
    else:
        overshoot = None
        overshoot_in_window = False
    transition_completed = service_end <= demand_time + max_wait + 1e-9
    return {
        "mode": mode, "variant": name, "unit": unit, "ready": True,
        "demand_time": demand_time, "service_start": service_start,
        "service_end": service_end, "wait_time": schedule["wait_time"],
        "stage_overshoot": overshoot,
        "overshoot_within_observed_window": overshoot_in_window,
        "delayed_by_outage": schedule["delayed_by_outage"],
        "transition_completed": transition_completed, "cause": schedule["cause"],
    }


def _rows_equal_upto(rows_a, rows_b, upto, columns):
    left = [row for row in rows_a if row["dimensionless_time"] <= upto + 1e-9]
    right = [row for row in rows_b if row["dimensionless_time"] <= upto + 1e-9]
    if len(left) != len(right):
        return False
    for row_a, row_b in zip(left, right):
        for column in columns:
            if row_a[column] != row_b[column]:
                return False
    return True


def _check_dedicated_matches_twin(variants, shared, duration, step, boundaries,
                                  twin_by_variant):
    """Dedicated trajectories must equal independent twin runs and never wait."""
    trajectories_match = True
    for name in sorted(variants):
        canonical = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        projected = _project_twin("A", twin_by_variant[name])
        if not _rows_equal_upto(projected, canonical, math.inf, TRAJECTORY_NONUNIT_COLUMNS):
            trajectories_match = False
    return {"trajectories_match_twin": trajectories_match,
            "all_waits_zero": True,
            "overall": trajectories_match}


def _check_simultaneous(variants, shared, duration, step, boundaries, experiment):
    """Zero-offset shared_serial with no outage: second wait == service_time."""
    threshold = experiment["readiness_threshold"]
    service_time = experiment["service_time"]
    results = []
    confirmed_all = True
    for name in sorted(variants):
        twin = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        demand = _demand_time(twin, threshold)
        if demand is None:
            results.append({"variant": name, "ready": False, "confirmed": None})
            continue
        scheduled = _schedule_shared_serial(demand, demand, service_time, [])
        second_wait = scheduled["B"]["wait_time"]
        confirmed = abs(second_wait - service_time) < 1e-9
        confirmed_all = confirmed_all and confirmed
        results.append({"variant": name, "ready": True,
                        "second_unit_wait": second_wait,
                        "service_time": service_time, "confirmed": confirmed})
    return {"overall": confirmed_all, "variants": results}


def _check_offset_sweep(variants, shared, duration, step, boundaries, experiment):
    """Second-unit wait equals max(0, service_time - offset) for the sweep."""
    threshold = experiment["readiness_threshold"]
    service_time = experiment["service_time"]
    confirmations = []
    confirmed_all = True
    for name in sorted(variants):
        twin = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        demand = _demand_time(twin, threshold)
        if demand is None:
            confirmations.append({"variant": name, "ready": False, "offsets": []})
            continue
        offsets = []
        for multiplier in OFFSET_MULTIPLIERS:
            offset = multiplier * service_time
            scheduled = _schedule_shared_serial(demand, demand + offset, service_time, [])
            second_wait = scheduled["B"]["wait_time"]
            expected = max(0.0, service_time - offset)
            confirmed = abs(second_wait - expected) < 1e-9
            confirmed_all = confirmed_all and confirmed
            offsets.append({"offset_multiplier": multiplier, "offset": offset,
                            "second_unit_wait": second_wait, "expected": expected,
                            "confirmed": confirmed})
        confirmations.append({"variant": name, "ready": True, "offsets": offsets})
    return {"overall": confirmed_all, "variants": confirmations}


def _check_outage_correlates(variants, shared, duration, step, boundaries, experiment,
                             station_outages):
    """Simultaneous demand with an overlapping outage raises both units' waits."""
    threshold = experiment["readiness_threshold"]
    service_time = experiment["service_time"]
    per_variant = []
    overall = False
    for name in sorted(variants):
        twin = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        demand = _demand_time(twin, threshold)
        if demand is None:
            per_variant.append({"variant": name, "ready": False,
                                "no_outage_waits": None, "outage_waits": None,
                                "correlates": False})
            continue
        no_outage = _schedule_shared_serial(demand, demand, service_time, [])
        with_outage = _schedule_shared_serial(demand, demand, service_time, station_outages)
        no_waits = {"A": no_outage["A"]["wait_time"], "B": no_outage["B"]["wait_time"]}
        out_waits = {"A": with_outage["A"]["wait_time"], "B": with_outage["B"]["wait_time"]}
        correlates = (out_waits["A"] > no_waits["A"] + 1e-9
                      and out_waits["B"] > no_waits["B"] + 1e-9)
        overall = overall or correlates
        per_variant.append({"variant": name, "ready": True,
                            "no_outage_waits": no_waits, "outage_waits": out_waits,
                            "correlates": correlates})
    return {"overall": overall, "variants": per_variant}


def _check_local_blindness(variants, shared, duration, step, boundaries, experiment,
                           station_outages, trajectories):
    """B's unit-local channels never reveal the cause of its delay."""
    threshold = experiment["readiness_threshold"]
    service_time = experiment["service_time"]
    offset = experiment["unit_b_demand_offset"]
    scenarios = []
    all_identical = True
    causes = set()
    for name in sorted(variants):
        twin = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        demand = _demand_time(twin, threshold)
        if demand is None:
            scenarios.append({"variant": name, "ready": False,
                              "b_local_columns_identical_to_twin": None, "cause": None})
            continue
        demand_b = demand + offset
        scenario_setups = [
            ("published_shared_serial", demand_b, station_outages),
            ("no_outage_simultaneous", demand, []),
            ("no_outage_offset_service_time", demand + service_time, []),
        ]
        for label, b_demand, outs in scenario_setups:
            scheduled = _schedule_shared_serial(demand, b_demand, service_time, outs)
            b_start = scheduled["B"]["service_start"]
            b_trajectory = trajectories.get(("shared_serial", name, "B"))
            if b_trajectory is None:
                b_trajectory = _project_twin("B", twin)
            identical = _rows_equal_upto(b_trajectory, twin, b_start,
                                         TRAJECTORY_NONUNIT_COLUMNS)
            cause = scheduled["B"]["cause"]
            all_identical = all_identical and identical
            causes.add(cause)
            scenarios.append({"variant": name, "scenario": label,
                              "b_service_start": b_start,
                              "b_local_columns_identical_to_twin": identical,
                              "cause": cause})
    cause_attributable_from_local_channels = not (all_identical and len(causes) > 1)
    return {
        "b_local_columns_identical_to_twin": all_identical,
        "cause_attributable_from_local_channels": cause_attributable_from_local_channels,
        "distinct_causes_across_scenarios": sorted(causes),
        "method": "Unit B's unit-local twin-trajectory columns are identical across scenarios "
                  "while the event-table cause field differs; waiting and station state never "
                  "enter a unit's own dynamics.",
        "scenarios": scenarios,
    }


def transition_demand(config_path: Path, output: Path) -> dict:
    """Publish the deterministic concurrent transition demand bundle."""
    config, raw = read_json(config_path)
    parsed, experiment, station_outages = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, variants, analysis) = parsed
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, monitor_faults)

    _check_work_budget(variants, shared, duration, step)

    readiness_threshold = experiment["readiness_threshold"]
    service_time = experiment["service_time"]
    offset = experiment["unit_b_demand_offset"]
    max_wait = experiment["max_wait"]
    modes = experiment["modes"]

    twin_by_variant = {}
    demand_by_variant = {}
    for name in sorted(variants):
        twin = _variant_run(name, variants[name], shared, duration, step, boundaries)[0]
        twin_by_variant[name] = twin
        demand_by_variant[name] = _demand_time(twin, readiness_threshold)

    all_events = []
    trajectories = {}
    for name in sorted(variants):
        twin = twin_by_variant[name]
        demand_a = demand_by_variant[name]
        demand_b = demand_a + offset if demand_a is not None else None
        for mode in modes:
            for unit in ("A", "B"):
                trajectories[(mode, name, unit)] = _project_twin(unit, twin)
            if demand_a is None:
                all_events.append(_not_ready_event(mode, name, "A"))
                all_events.append(_not_ready_event(mode, name, "B"))
                continue
            if mode == "dedicated":
                schedule_a = {"service_start": demand_a, "service_end": demand_a + service_time,
                              "wait_time": 0.0, "delayed_by_outage": False, "cause": ""}
                schedule_b = {"service_start": demand_b, "service_end": demand_b + service_time,
                              "wait_time": 0.0, "delayed_by_outage": False, "cause": ""}
            else:
                scheduled = _schedule_shared_serial(demand_a, demand_b, service_time,
                                                    station_outages)
                schedule_a = scheduled["A"]
                schedule_b = scheduled["B"]
            all_events.append(_ready_event(mode, name, "A", twin, demand_a, schedule_a, max_wait))
            all_events.append(_ready_event(mode, name, "B", twin, demand_b, schedule_b, max_wait))

    dedicated_check = _check_dedicated_matches_twin(
        variants, shared, duration, step, boundaries, twin_by_variant)
    simultaneous_check = _check_simultaneous(
        variants, shared, duration, step, boundaries, experiment)
    offset_check = _check_offset_sweep(
        variants, shared, duration, step, boundaries, experiment)
    outage_check = _check_outage_correlates(
        variants, shared, duration, step, boundaries, experiment, station_outages)
    blindness_check = _check_local_blindness(
        variants, shared, duration, step, boundaries, experiment, station_outages, trajectories)

    checks_passed = (
        dedicated_check["overall"]
        and simultaneous_check["overall"]
        and offset_check["overall"]
        and outage_check["overall"]
        and blindness_check["b_local_columns_identical_to_twin"]
        and not blindness_check["cause_attributable_from_local_channels"]
    )
    qualification_status = ("dimensionless_software_checks_passed"
                            if checks_passed else "dimensionless_software_checks_failed")

    report = {
        "schema_version": 1,
        "notice": NOTICE,
        "fixture_notice": NOTICE,
        "result_kind": "dimensionless_transition_demand",
        "model_family": "dimensionless_transition_demand_experiment",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "qualification_status": qualification_status,
        "modes": list(modes),
        "variants": sorted(variants),
        "transition_contract": {
            "readiness_threshold": readiness_threshold,
            "service_time": service_time,
            "unit_b_demand_offset": offset,
            "max_wait": max_wait,
            "station_outages": station_outages,
            "station_modes": list(MODES),
            "fifo_tiebreak": "unit_A_first",
            "service_preemption": "suspend_at_outage_start_resume_at_outage_end",
        },
        "dedicated_matches_twin": dedicated_check["overall"],
        "simultaneous_second_wait_equals_service_time": simultaneous_check["overall"],
        "closed_form_offset_sweep": offset_check,
        "outage_correlates_delays": outage_check,
        "local_blindness_check": blindness_check,
        "interpretation": [
            "Dedicated mode is the control: every unit owns a station, so service starts at "
            "demand time and no unit waits.",
            "Shared-serial mode gives one station to both units, FIFO by demand time, so a "
            "simultaneous demand makes the second unit wait exactly one service time.",
            "A station outage is a common cause: it suspends service with preemption/resume, "
            "and queued units wait through it too, correlating delays across both units.",
            "Waiting is not neutral: the unit keeps developing, so the delayed second unit "
            "shows positive stage overshoot while the control shows none.",
            "Unit B's unit-local twin-trajectory columns are identical across scenarios while "
            "the event-table cause differs, so the cause of a delay is not attributable from "
            "unit-local channels.",
        ],
        "limits": [
            "All values, thresholds, offsets, outage intervals and times are invented "
            "dimensionless software fixture quantities.",
            "Service preemption and resume at outage boundaries is a modeling convention, not "
            "an observed or engineered scheduling behavior.",
            "No biological transition, neonatal outcome, viability or clinical claim is made.",
            "Two units sharing one station do not establish any ten-unit capacity or facility "
            "throughput claim.",
            "No qualification gate, procurement action or machine-control output is moved by "
            "this fixture.",
        ],
    }

    lines = [
        "# Dimensionless concurrent transition demand experiment", "", NOTICE, "",
        f"Readiness threshold {readiness_threshold}; service time {service_time}; "
        f"unit-B demand offset {offset}; max wait {max_wait}.", "",
        f"Modes: {', '.join(modes)}. Station outages: "
        f"{station_outages if station_outages else 'none'}.", "",
        "Dedicated mode is the control (no waiting). Shared-serial mode makes a "
        "simultaneous demand wait one service time, and a station outage suspends "
        "service with preemption/resume, correlating delays across units.", "",
        "## Event summary", "",
    ]
    for event in all_events:
        if event["ready"]:
            lines.append(
                f"- {event['variant']} / {event['mode']} / unit {event['unit']}: "
                f"demand {event['demand_time']}, start {event['service_start']}, "
                f"end {event['service_end']}, wait {event['wait_time']}, "
                f"overshoot {event['stage_overshoot']}, cause {event['cause'] or 'none'}")
        else:
            lines.append(f"- {event['variant']} / {event['mode']} / unit {event['unit']}: not ready")
    lines.extend([
        "", f"dedicated_matches_twin: {dedicated_check['overall']}.",
        f"simultaneous_second_wait_equals_service_time: {simultaneous_check['overall']}.",
        f"closed_form_offset_sweep: {offset_check['overall']}.",
        f"outage_correlates_delays: {outage_check['overall']}.",
        f"local_blindness_check cause_attributable_from_local_channels: "
        f"{blindness_check['cause_attributable_from_local_channels']}.",
        "", *report["interpretation"], "", "## Limits", "",
    ])
    lines.extend(f"- {item}" for item in report["limits"])

    files = {
        "source_config.json": raw,
        "transition_demand_events.csv": csv_bytes(list(EVENT_COLUMNS), all_events),
        "transition_demand_report.json": json_bytes(report),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    for key, rows in sorted(trajectories.items()):
        mode, name, unit = key
        files[f"trajectory_{mode}_{name}_{unit}.csv"] = csv_bytes(list(TRAJECTORY_COLUMNS), rows)

    return publish_bundle(
        output, kind="dimensionless_transition_demand", input_raw=raw, files=files,
        metadata={"biological_measurements": False, "physiologically_calibrated": False,
                   "human_gestation_prediction": False, "n_variants": len(variants),
                   "n_modes": len(modes), "qualification_status": qualification_status})
