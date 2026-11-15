"""Delay-matched shared-station observability counterexample (T32).

T31 established that queueing and station outage can delay a unit without
changing its local twin. T32 makes that observability gap exact: in two worlds,
unit B has the same demand, wait, service interval, complete local trajectory
and stage overshoot, while the ground-truth delay cause differs. Independent
station state and occupancy separate the worlds; a lumped unavailable flag does
not. Every value is an invented dimensionless software quantity.
"""
from __future__ import annotations

import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json, sha256
from .exchange import NOTICE, fields
from .mechanical_twin import FLUIDIC_COLUMNS, _coupled_variant_run, _validate as _validate_mechanical
from .numerics import output_times
from .transition_demand import (
    TWIN_KEYS,
    _check_work_budget as _check_t31_work_budget,
    _demand_time,
    _ready_event,
    _schedule_shared_serial,
    _validate_experiment as _validate_t31,
)
from .whole_path_twin import MAX_TOTAL_SUBSTEPS, SUBSTEP_RATE_TARGET, _variant_run

WORLDS = ("queue_only", "outage_only")
LOCAL_COLUMNS = (
    "dimensionless_time", "unit", "size", "capacity_margin", "request_fraction",
    "served_fraction", "delivered_flux", "bulk_stock", "deep_receipt_rate",
    "cumulative_unserved", "progression", "reserve", "supplement",
    "controller_reading", "wall_load", "wall_stiffness", "wall_strain",
    "wall_safety_margin", "wall_damage",
)
EVENT_COLUMNS = (
    "variant", "world", "unit", "ready", "demand_time", "wait_duration",
    "service_start", "service_end", "stage_overshoot", "ground_truth_delay_cause",
    "delayed_by_outage", "transition_completed",
)
STATION_COLUMNS = (
    "variant", "world", "dimensionless_time", "station_operational_state",
    "station_active_unit", "station_unavailable_flag",
)
B_EVENT_KEYS = ("demand_time", "wait_time", "service_start", "service_end", "stage_overshoot")


def _validate(config):
    """Validate through the unmodified T31 and T23 contracts."""
    fields(config, TWIN_KEYS + ("transition_experiment", "wall"), "config")
    mechanical_config = {key: value for key, value in config.items()
                         if key != "transition_experiment"}
    transition_config = {key: value for key, value in config.items() if key != "wall"}
    transition_config["variants"] = {
        name: {key: value for key, value in variant.items() if key != "wall_coupling"}
        for name, variant in config["variants"].items()
    }
    fluidic, wall, couplings = _validate_mechanical(mechanical_config)
    t31_fluidic, experiment, _configured_outages = _validate_t31(transition_config)
    if fluidic != t31_fluidic:
        raise InputError("T31 and mechanical validation disagree on the shared twin")
    duration, step = fluidic[:2]
    service_time = experiment["service_time"]
    if abs(service_time / step - round(service_time / step)) > 1e-9:
        raise InputError("service_time must fall on the output grid for station sampling")
    return fluidic, wall, couplings, experiment


def _check_wall_budget(wall, growth, duration):
    rate = (wall["stiffness_coefficient"]
            * (1.0 + growth["linear_rate"] * duration) ** wall["stiffness_exponent"]
            / wall["viscosity"])
    if duration * rate / SUBSTEP_RATE_TARGET > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Wall integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")


def _local_csv(rows):
    projected = [dict(row, unit="B") for row in rows]
    return csv_bytes(list(LOCAL_COLUMNS), projected)


def _event_row(variant, world, unit, event):
    return {
        "variant": variant, "world": world, "unit": unit, "ready": event["ready"],
        "demand_time": event["demand_time"], "wait_duration": event["wait_time"],
        "service_start": event["service_start"], "service_end": event["service_end"],
        "stage_overshoot": event["stage_overshoot"],
        "ground_truth_delay_cause": event["cause"],
        "delayed_by_outage": event["delayed_by_outage"],
        "transition_completed": event["transition_completed"],
    }


def _station_rows(variant, world, demand, service_time, step):
    rows = []
    for index in range(round(2 * service_time / step) + 1):
        time = demand + index * step
        in_first = demand <= time < demand + service_time
        in_second = demand + service_time <= time < demand + 2 * service_time
        if world == "queue_only":
            operational = "available"
            active = ("serving_unit_A" if in_first else
                      "serving_unit_B" if in_second else "idle")
        else:
            operational = "outage" if in_first else "available"
            active = ("idle_during_outage" if in_first else
                      "serving_unit_B" if in_second else "idle")
        unavailable = operational == "outage" or active.startswith("serving_unit_")
        rows.append({"variant": variant, "world": world, "dimensionless_time": time,
                     "station_operational_state": operational, "station_active_unit": active,
                     "station_unavailable_flag": unavailable})
    return rows


def _channel_separates(rows, channel):
    by_world = {world: {row["dimensionless_time"]: row[channel]
                        for row in rows if row["world"] == world} for world in WORLDS}
    return any(by_world["queue_only"][time] != by_world["outage_only"][time]
               for time in by_world["queue_only"])


def _exact_schedule(variant, world, demand, service_time, events):
    a = events[(world, "A")]
    b = events[(world, "B")]
    expected_a_demand = demand if world == "queue_only" else demand - service_time
    expected_a_end = demand + service_time if world == "queue_only" else demand
    return (
        a["demand_time"] == expected_a_demand and a["wait_time"] == 0.0
        and a["service_start"] == expected_a_demand and a["service_end"] == expected_a_end
        and b["demand_time"] == demand and b["wait_time"] == service_time
        and b["service_start"] == demand + service_time
        and b["service_end"] == demand + 2 * service_time
        and b["cause"] == ("queue" if world == "queue_only" else "station_outage")
    )


def _measurement_addendum(step):
    return {
        "schema_version": 1,
        "scope": "operational shared-station measurement addendum alongside T24/T25",
        "mutates_t24_t25_architecture_discrimination_spec": False,
        "calibration_required": True,
        "calibration_requirements": [
            "Calibrate station operational state independently of service occupancy.",
            "Calibrate active-unit identity and synchronize station and unit clocks.",
            "Verify that available, outage, active-service and idle states remain distinguishable.",
        ],
        "canonical_dimensionless_sampling_cadence": step,
        "channels": [
            {"channel": "station_operational_state", "requirement": "required",
             "values": ["available", "outage"], "independent_of_occupancy": True,
             "separates_counterexample": True, "price": None},
            {"channel": "station_active_unit", "requirement": "required",
             "values": ["serving_unit_A", "serving_unit_B", "idle_during_outage", "idle"],
             "independent_of_operational_state": True,
             "separates_counterexample": True, "price": None},
            {"channel": "station_unavailable_flag", "requirement": "insufficient",
             "values": [False, True], "lumps_active_service_with_outage": True,
             "separates_counterexample": False, "price": None},
        ],
        "total_price": None,
        "procurement_authorized": False,
        "hardware_reliability_claim": False,
    }


def station_observability(config_path: Path, output: Path) -> dict:
    """Publish the delay-matched shared-station observability bundle."""
    config, raw = read_json(config_path)
    fluidic, wall, couplings, experiment = _validate(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, base_variants, _analysis) = fluidic
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, monitor_faults)
    variants = {name: dict(base_variants[name], wall_coupling=couplings[name])
                for name in base_variants}
    _check_t31_work_budget(base_variants, shared, duration, step)
    _check_wall_budget(wall, growth, duration)

    threshold = experiment["readiness_threshold"]
    service_time = experiment["service_time"]
    max_wait = experiment["max_wait"]
    all_events = []
    all_station_rows = []
    files = {"source_config.json": raw}
    variant_results = []
    all_checks = True

    for name in sorted(variants):
        canonical = _variant_run(name, base_variants[name], shared, duration, step, boundaries)[0]
        demand = _demand_time(canonical, threshold)
        if demand is None:
            raise InputError(f"Variant {name} never reaches the T31 readiness threshold")
        if demand - service_time < 0 or demand + 2 * service_time > duration:
            raise InputError(f"Variant {name} cannot fit the delay-matched worlds in the run window")

        runs = {}
        events = {}
        local_bytes = {}
        for world in WORLDS:
            rows = _coupled_variant_run(name, variants[name], shared, duration, step,
                                        boundaries, wall)[0]
            runs[world] = rows
            if any(row[column] != reference[column]
                   for row, reference in zip(rows, canonical) for column in FLUIDIC_COLUMNS):
                raise InputError("Coupled wall run changed T31's canonical fluidic trajectory")
            demand_a = demand if world == "queue_only" else demand - service_time
            station_outages = [] if world == "queue_only" else [
                {"start": demand, "end": demand + service_time}]
            schedule = _schedule_shared_serial(demand_a, demand, service_time, station_outages)
            for unit in ("A", "B"):
                unit_demand = demand_a if unit == "A" else demand
                event = _ready_event("shared_serial", name, unit, rows, unit_demand,
                                     schedule[unit], max_wait)
                events[(world, unit)] = event
                all_events.append(_event_row(name, world, unit, event))
            local_bytes[world] = _local_csv(rows)
            files[f"unit_b_local_{world}_{name}.csv"] = local_bytes[world]
            world_station_rows = _station_rows(name, world, demand, service_time, step)
            all_station_rows.extend(world_station_rows)

        local_identical = local_bytes["queue_only"] == local_bytes["outage_only"]
        event_identical = all(events[("queue_only", "B")][key] == events[("outage_only", "B")][key]
                              for key in B_EVENT_KEYS)
        schedules_exact = all(_exact_schedule(name, world, demand, service_time, events)
                              for world in WORLDS)
        station_rows = [row for row in all_station_rows if row["variant"] == name]
        operational_separates = _channel_separates(station_rows, "station_operational_state")
        active_separates = _channel_separates(station_rows, "station_active_unit")
        lumped_separates = _channel_separates(station_rows, "station_unavailable_flag")
        queue_b = events[("queue_only", "B")]
        outage_b = events[("outage_only", "B")]
        checks = (local_identical and event_identical and schedules_exact
                  and operational_separates and active_separates and not lumped_separates)
        all_checks = all_checks and checks
        variant_results.append({
            "variant": name, "demand_time": demand, "wait_duration": service_time,
            "outage_only_unit_a_demand_time": demand - service_time,
            "service_start": queue_b["service_start"], "service_end": queue_b["service_end"],
            "stage_overshoot": queue_b["stage_overshoot"],
            "queue_only_ground_truth_delay_cause": queue_b["cause"],
            "outage_only_ground_truth_delay_cause": outage_b["cause"],
            "schedule_matches_hand_calculation": schedules_exact,
            "t31_canonical_fluidic_unchanged": True,
            "unit_b_local_bitwise_identical": local_identical,
            "unit_b_local_sha256": sha256(local_bytes["queue_only"]),
            "unit_b_wait_and_overshoot_identical": event_identical,
            "unit_local_separates": False,
            "station_operational_state_separates": operational_separates,
            "station_active_unit_separates": active_separates,
            "lumped_unavailable_separates": lumped_separates,
            "counterexample_verified": checks,
        })

    status = ("dimensionless_software_checks_passed" if all_checks
              else "dimensionless_software_checks_failed")
    report = {
        "schema_version": 1, "notice": NOTICE, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_station_observability",
        "model_family": "delay_matched_shared_station_observability_counterexample",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False, "qualification_status": status,
        "t31_canonical_unchanged": all(item["t31_canonical_fluidic_unchanged"]
                                       for item in variant_results),
        "unit_local_separates": False,
        "station_operational_state_separates": all(
            item["station_operational_state_separates"] for item in variant_results),
        "station_active_unit_separates": all(
            item["station_active_unit_separates"] for item in variant_results),
        "lumped_unavailable_separates": any(
            item["lumped_unavailable_separates"] for item in variant_results),
        "counterexample_verified": all_checks,
        "transition_contract": {
            "readiness_threshold": threshold, "service_time": service_time,
            "fifo_tiebreak": "unit_A_first", "worlds": list(WORLDS),
            "queue_only": "A and B demand at d; no outage; A [d,d+s), B [d+s,d+2s)",
            "outage_only": "A demands at d-s and ends at d; B demands at d; outage [d,d+s); B [d+s,d+2s)",
        },
        "variants": variant_results,
        "measurement_addendum": _measurement_addendum(step),
        "interpretation": [
            "No unit-local channel set, including internal D/M/P and wall channels, can attribute B's delay cause.",
            "Independent station operational state separates queueing from outage during [d,d+s).",
            "Independent active-unit occupancy also separates active service from idle outage.",
            "A coarse busy-or-outage flag is identical and therefore cannot attribute the delay cause.",
        ],
        "limits": [
            "Every schedule, trajectory, outage, wall and time value is an invented dimensionless software quantity.",
            "The addendum does not mutate T24/T25's frozen architecture-discrimination specification.",
            "Station channels require calibration; this fixture establishes no hardware reliability or independence claim.",
            "No biological, neonatal, clinical, physical-capacity or transition-procedure claim is made.",
            "All prices remain null; no procurement, external contact, machine control or gate movement is authorized.",
        ],
    }
    files["station_observability_events.csv"] = csv_bytes(list(EVENT_COLUMNS), all_events)
    files["station_observations.csv"] = csv_bytes(list(STATION_COLUMNS), all_station_rows)
    files["station_observability_report.json"] = json_bytes(report)

    lines = ["# Delay-matched shared-station observability", "", NOTICE, "",
             "| Variant | d | s | B start | B end | B overshoot | Queue cause | Outage cause |",
             "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for item in variant_results:
        lines.append(f"| {item['variant']} | {item['demand_time']} | {item['wait_duration']} | "
                     f"{item['service_start']} | {item['service_end']} | {item['stage_overshoot']} | "
                     f"{item['queue_only_ground_truth_delay_cause']} | "
                     f"{item['outage_only_ground_truth_delay_cause']} |")
    lines.extend(["", f"unit_local_separates: {report['unit_local_separates']}",
                  f"station_operational_state_separates: {report['station_operational_state_separates']}",
                  f"station_active_unit_separates: {report['station_active_unit_separates']}",
                  f"lumped_unavailable_separates: {report['lumped_unavailable_separates']}",
                  "", *report["interpretation"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])
    files["REPORT.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    return publish_bundle(
        output, kind="dimensionless_station_observability", input_raw=raw, files=files,
        metadata={"biological_measurements": False, "physiologically_calibrated": False,
                  "human_gestation_prediction": False, "n_variants": len(variant_results),
                  "qualification_status": status, "procurement_authorized": False})
