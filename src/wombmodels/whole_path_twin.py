"""Whole-path system twin: one deterministic running world per variant (T21).

The second D12 ladder rung's components become one running world: the T19
growth-scaling geometry (sub-linear capacity surface, linear demand sink), the
T20 spatial observability constraint (a boundary-only controller), seeded
sensor noise, wall outages with reserve failover, and same-unit boundary
measurement events at each of the four interval handoffs I1-I4. The three
interface variants (living-interface, staged, synthetic) run the same path
under shared noise seeds, and the twin reports which observables separate
them - producing variant signatures instead of predicting them.

The research monitor is a separate recorded stream that never feeds the
controller. No parameter represents physiology, time in days, a device
setpoint or a biological measurement; the variants are invented
parameterizations with no capability ranking.
"""
from __future__ import annotations

import math
import random
from itertools import combinations
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, intervals, number
from .growth_scaling import analytic_crossover
from .numerics import output_times, require_finite

MAX_OUTPUT_INTERVALS = 50_000
MAX_TOTAL_SUBSTEPS = 4_000_000
MAX_RATE = 100.0
SUBSTEP_RATE_TARGET = 0.2
BOUNDARY_OBSERVABLES = ("delivered_flux", "served_fraction", "bulk_stock")
INTERNAL_OBSERVABLES = ("deep_receipt_rate", "cumulative_unserved", "progression")


def _validate(config):
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
                    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
                    "monitor", "variants", "analysis"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    fields(config["dimensionless_time"], ("duration", "output_step"), "dimensionless_time")
    duration = number(config["dimensionless_time"]["duration"], "duration", 1e-6, 10_000)
    step = number(config["dimensionless_time"]["output_step"], "output_step", 1e-6, duration)
    if duration / step > MAX_OUTPUT_INTERVALS:
        raise InputError(f"At most {MAX_OUTPUT_INTERVALS} output intervals are permitted")

    raw_boundaries = config["interval_boundaries"]
    if not isinstance(raw_boundaries, list) or not 1 <= len(raw_boundaries) <= 5:
        raise InputError("interval_boundaries must be a list of 1 to 5 handoff times")
    boundaries = []
    previous = 0.0
    for item in raw_boundaries:
        value = number(item, "interval boundary", step, duration - step)
        if value <= previous:
            raise InputError("interval_boundaries must be strictly increasing")
        if abs(value / step - round(value / step)) > 1e-9:
            raise InputError("interval_boundaries must fall on the output grid")
        boundaries.append(value)
        previous = value

    fields(config["growth"], ("linear_rate", "surface_exponent"), "growth")
    growth = {"linear_rate": number(config["growth"]["linear_rate"], "linear_rate", 0, 10),
              "surface_exponent": number(config["growth"]["surface_exponent"], "surface_exponent", 0, 1.0)}
    fields(config["scaling"], ("capacity_coefficient", "demand_coefficient"), "scaling")
    scaling = {"capacity_coefficient": number(config["scaling"]["capacity_coefficient"],
                                               "capacity_coefficient", 1e-6, 1_000),
               "demand_coefficient": number(config["scaling"]["demand_coefficient"],
                                            "demand_coefficient", 1e-6, 1_000)}
    fields(config["bulk"], ("target", "washout", "transfer"), "bulk")
    bulk = {key: number(value, key, 0, MAX_RATE) for key, value in config["bulk"].items()}
    if bulk["target"] <= 0:
        raise InputError("bulk target must be positive")
    fields(config["internal"], ("use", "repair", "progression_rate"), "internal")
    internal = {key: number(value, key, 0, MAX_RATE) for key, value in config["internal"].items()}
    fields(config["control"], ("gain", "rate_limit", "supplement_max"), "control")
    control = {"gain": number(config["control"]["gain"], "gain", 0, MAX_RATE),
               "rate_limit": number(config["control"]["rate_limit"], "rate_limit", 0, MAX_RATE),
               "supplement_max": number(config["control"]["supplement_max"],
                                         "supplement_max", 0, 1_000)}
    fields(config["reserve"], ("initial", "draw", "fraction"), "reserve")
    reserve = {"initial": number(config["reserve"]["initial"], "initial", 0, 1_000),
               "draw": number(config["reserve"]["draw"], "draw", 0, 1_000),
               "fraction": number(config["reserve"]["fraction"], "fraction", 0, 1.0)}
    outages = intervals(config["outages"], duration, "outages")

    fields(config["monitor"], ("cadence", "noise_sd", "seed", "faults"), "monitor")
    cadence = number(config["monitor"]["cadence"], "cadence", step, duration)
    noise_sd = number(config["monitor"]["noise_sd"], "noise_sd", 0, 1_000)
    seed = config["monitor"]["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise InputError("monitor seed must be an integer")
    if abs(cadence / step - round(cadence / step)) > 1e-9:
        raise InputError("monitor cadence must be a multiple of the output step")
    faults = intervals(config["monitor"]["faults"], duration, "monitor faults", faults=True)

    variants = config["variants"]
    if not isinstance(variants, dict) or not 2 <= len(variants) <= 6:
        raise InputError("variants must map 2 to 6 named interface parameterizations")
    parsed = {}
    for name, item in variants.items():
        if not isinstance(name, str) or not name:
            raise InputError("variant names must be non-empty strings")
        fields(item, ("serve_rate", "internal_efficiency"), f"variant {name}")
        parsed[name] = {"serve_rate": number(item["serve_rate"], f"{name} serve_rate", 0, MAX_RATE),
                        "internal_efficiency": number(item["internal_efficiency"],
                                                        f"{name} internal_efficiency", 0, 1.0)}
    fields(config["analysis"], ("separation_tolerance", "served_threshold"), "analysis")
    analysis = {"separation_tolerance": number(config["analysis"]["separation_tolerance"],
                                                "separation_tolerance", 1e-9, 10),
                "served_threshold": number(config["analysis"]["served_threshold"],
                                            "served_threshold", 0, 1.0)}
    return (duration, step, boundaries, growth, scaling, bulk, internal, control,
            reserve, outages, cadence, noise_sd, seed, faults, parsed, analysis)


def _in_outage(outages, time):
    return any(item["start"] <= time < item["end"] for item in outages)


def _fault_at(faults, time):
    for item in faults:
        if item["start"] <= time < item["end"]:
            return item
    return None


def _right_hand_side(time, state, parameters, held_reading, operating=None):
    """Derivatives of [request, bulk, tissue, unserved, progression, reserve, supplement]."""
    growth, scaling, bulk, internal, control, reserve, outages, variant = parameters
    size = 1.0 + growth["linear_rate"] * time
    capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
    demand = scaling["demand_coefficient"] * size
    margin = capacity / demand
    request, stock, tissue, unserved, progression, remaining, supplement = state
    if operating is None:
        outage = _in_outage(outages, time)
        active_backup = outage and remaining > 0
        multiplier = reserve["fraction"] if active_backup else (0.0 if outage else 1.0)
        draw = reserve["draw"] if active_backup else 0.0
    else:
        multiplier, draw = operating
    d_request = variant["serve_rate"] * (min(1.0, margin) - request)
    delivered = min(demand * request, capacity) * multiplier
    served = delivered / demand
    d_bulk = delivered + supplement - (bulk["washout"] + bulk["transfer"]) * stock
    # Optional reciprocal wall feedback. Existing fixtures omit this key, so
    # their canonical arithmetic and trajectories remain unchanged.
    if variant.get("wall_damage_leak", 0.0):
        d_bulk -= variant["wall_damage_leak"] * variant.get("wall_damage", 0.0) * stock
    d_tissue = variant["internal_efficiency"] * bulk["transfer"] * stock - internal["use"] * tissue
    d_unserved = demand * (1.0 - served) - internal["repair"] * unserved
    receipt = internal["use"] * tissue
    d_progression = internal["progression_rate"] * min(1.0, receipt / demand)
    d_reserve = -draw
    correction = control["gain"] * (bulk["target"] - held_reading)
    d_supplement = max(-control["rate_limit"], min(control["rate_limit"], correction))
    return [d_request, d_bulk, d_tissue, d_unserved, d_progression, d_reserve, d_supplement]


def _rk4_step(time, state, substep, parameters, held_reading, operating=None, observer=None):
    if observer is not None and hasattr(observer, "feedback_state"):
        parameters[-1]["wall_damage"] = observer.feedback_state()
    first = _right_hand_side(time, state, parameters, held_reading, operating)
    second = _right_hand_side(time + 0.5 * substep,
                              [value + 0.5 * substep * rate for value, rate in zip(state, first)],
                              parameters, held_reading, operating)
    third = _right_hand_side(time + 0.5 * substep,
                             [value + 0.5 * substep * rate for value, rate in zip(state, second)],
                             parameters, held_reading, operating)
    fourth = _right_hand_side(time + substep,
                              [value + substep * rate for value, rate in zip(state, third)],
                             parameters, held_reading, operating)
    if observer is not None:
        observer.advance(time, state, substep, (first, second, third, fourth), operating)
    return [value + substep * (a + 2 * b + 2 * c + d) / 6.0
            for value, a, b, c, d in zip(state, first, second, third, fourth)]


def _variant_run(name, variant, shared, duration, step, boundaries, observer=None):
    """One deterministic whole-path run; control and monitor use separate streams."""
    growth, scaling, bulk, internal, control, reserve, outages = shared[:7]
    cadence, noise_sd, seed, faults = shared[7:]
    parameters = (growth, scaling, bulk, internal, control, reserve, outages, variant)
    rate_scale = (max(variant["serve_rate"], bulk["washout"] + bulk["transfer"],
                      internal["use"], internal["repair"])
                  + control["gain"] + reserve["draw"])
    # Reciprocal runs add their static damage-dependent leak stiffness bound to
    # the rate scale so the schedule resolves the stiffest allowed leak rate.
    # Existing fixtures omit the key, so their canonical arithmetic is unchanged.
    rate_scale += variant.get("wall_damage_leak_rate_bound", 0.0)
    substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
    # Reciprocal refinement multiplies the event-free substep count, which also
    # refines the held-damage splitting interval. Existing fixtures omit the
    # key (multiplied by 1), so their canonical arithmetic is unchanged.
    substeps *= variant.get("substep_refinement", 1)
    times = output_times(duration, step)
    intervals_count = len(times) - 1
    if intervals_count * substeps > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
    rng_control = random.Random(seed)
    rng_monitor = random.Random(seed + 1)
    state = [1.0, 0.0, 0.0, 0.0, 0.0, reserve["initial"], 0.0]
    held_reading = 0.0
    rows = []
    readings = []
    work = 0
    edges = sorted({item[key] for item in outages for key in ("start", "end")})
    for index, time in enumerate(times):
        size = 1.0 + growth["linear_rate"] * time
        capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
        demand = scaling["demand_coefficient"] * size
        delivered = min(demand * state[0], capacity)
        if _in_outage(outages, time):
            delivered *= reserve["fraction"] if state[5] > 0 else 0.0
        rows.append({"dimensionless_time": time, "size": size, "capacity_margin": capacity / demand,
                     "request_fraction": state[0],
                     "served_fraction": delivered / demand, "delivered_flux": delivered,
                     "bulk_stock": state[1], "deep_receipt_rate": internal["use"] * state[2],
                     "cumulative_unserved": state[3], "progression": state[4],
                     "reserve": state[5], "supplement": state[6], "controller_reading": held_reading})
        if observer is not None:
            rows[-1].update(observer.observe(time, rows[-1]))
        if index == intervals_count:
            break
        if noise_sd:
            held_reading = state[1] + rng_control.gauss(0.0, noise_sd)
        else:
            held_reading = state[1]
        if abs(round(time / cadence) - time / cadence) < 1e-9 or index == 0:
            fault = _fault_at(faults, time)
            if fault and fault["kind"] == "dropout":
                value = None
            else:
                value = state[1] + rng_monitor.gauss(0.0, noise_sd)
                if fault and fault["kind"] == "bias":
                    value += fault["magnitude"]
            readings.append({"dimensionless_time": time, "reading": value,
                             "fault": fault["kind"] if fault else ""})
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
                # A positive reserve below clock resolution has no representable
                # remaining operating interval. Pin it empty without looping.
                state[5] = 0.0
                continue
            count = max(1, math.ceil((stop - cursor) * rate_scale / SUBSTEP_RATE_TARGET))
            count *= variant.get("substep_refinement", 1)
            work += count
            if work > MAX_TOTAL_SUBSTEPS:
                raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
            segment_start, segment_reserve = cursor, state[5]
            substep = (stop - cursor) / count
            for inner in range(count):
                subtime = segment_start + inner * substep
                state = _rk4_step(subtime, state, substep, parameters, held_reading,
                                  (power, draw), observer)
                require_finite(state)
                state[0] = min(max(state[0], 0.0), 1.0)
                state[6] = min(max(state[6], 0.0), control["supplement_max"])
                for position in (1, 2, 3, 4):
                    state[position] = max(state[position], 0.0)
                state[5] = max(0.0, segment_reserve - draw * (inner + 1) * substep)
            if depletion is not None and stop == depletion:
                state[5] = 0.0
            cursor = stop
    events = _boundary_events(name, rows, boundaries, step)
    return rows, readings, events


def _boundary_events(name, rows, boundaries, step):
    events = []
    for index, boundary in enumerate(boundaries):
        post = rows[round(boundary / step)]
        pre = rows[round(boundary / step) - 1]
        for phase, row in (("pre", pre), ("post", post)):
            events.append({"variant": name, "handoff": index + 1,
                           "interval_transition": f"I{index + 1}->I{index + 2}",
                           "phase": phase, "dimensionless_time": row["dimensionless_time"],
                           "delivered_flux": row["delivered_flux"],
                           "served_fraction": row["served_fraction"],
                           "bulk_stock": row["bulk_stock"],
                           "deep_receipt_rate": row["deep_receipt_rate"],
                           "cumulative_unserved": row["cumulative_unserved"],
                           "progression": row["progression"], "size": row["size"]})
    return events


def _first_separation(events, first, second, observable, tolerance):
    """First handoff at which two variants differ beyond tolerance (post rows)."""
    left = [row for row in events if row["variant"] == first and row["phase"] == "post"]
    right = [row for row in events if row["variant"] == second and row["phase"] == "post"]
    for one, other in zip(left, right):
        scale = max(abs(one[observable]), abs(other[observable]), 1e-12)
        if abs(one[observable] - other[observable]) / scale > tolerance:
            return one["handoff"]
    return None


def whole_path_twin(config_path: Path, output: Path) -> dict:
    """Publish the whole-path twin; nothing is fitted and nothing is measured."""
    config, raw = read_json(config_path)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, variants, analysis) = _validate(config)
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)
    runs = {}
    for name in sorted(variants):
        rows, readings, events = _variant_run(name, variants[name], shared, duration, step, boundaries)
        runs[name] = {"rows": rows, "readings": readings, "events": events}

    crossover = analytic_crossover(growth, scaling)
    crossover["margin_at_end"] = runs[sorted(variants)[0]]["rows"][-1]["capacity_margin"]
    all_events = [event for name in sorted(variants) for event in runs[name]["events"]]
    pairs = []
    for first, second in combinations(sorted(variants), 2):
        record = {"pair": [first, second], "first_separated": {}}
        for observable in BOUNDARY_OBSERVABLES + INTERNAL_OBSERVABLES:
            record["first_separated"][observable] = _first_separation(
                all_events, first, second, observable, analysis["separation_tolerance"])
        record["boundary_observables_ever_separate"] = any(
            record["first_separated"][key] is not None for key in BOUNDARY_OBSERVABLES)
        record["internal_observables_ever_separate"] = any(
            record["first_separated"][key] is not None for key in INTERNAL_OBSERVABLES)
        pairs.append(record)

    dispositions = {}
    for name in sorted(variants):
        rows = runs[name]["rows"]
        final = rows[-1]
        engaged = [row["dimensionless_time"] for row in rows if row["supplement"] > 1e-9]
        closure_rows = [row for row in rows
                        if row["dimensionless_time"] > crossover["crossover_time"]]
        dispositions[name] = {
            "final_served_fraction": final["served_fraction"],
            "final_capacity_margin": final["capacity_margin"],
            "final_progression": final["progression"],
            "final_cumulative_unserved": final["cumulative_unserved"],
            "final_deep_receipt_rate": final["deep_receipt_rate"],
            "final_reserve": final["reserve"],
            "supplement_ever_engaged": bool(engaged),
            "supplement_first_engaged": min(engaged) if engaged else None,
            "supplement_last_engaged": max(engaged) if engaged else None,
            "boundary_actuation_during_capacity_closure": any(
                row["supplement"] > 1e-9 for row in closure_rows),
            "event_dispositions": ["supported" if event["served_fraction"]
                                   >= analysis["served_threshold"] else "underserved"
                                   for event in runs[name]["events"] if event["phase"] == "post"]}

    monitor_rows = []
    for name in sorted(variants):
        missing = 0
        for reading in runs[name]["readings"]:
            value = reading["reading"]
            if value is None:
                missing += 1
            monitor_rows.append({"variant": name,
                                 "dimensionless_time": reading["dimensionless_time"],
                                 "reading": "" if value is None else value,
                                 "active_fault": reading["fault"]})
        dispositions[name]["monitor_missing_readings"] = missing

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_whole_path_twin",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "n_intervals": len(boundaries) + 1, "boundaries": boundaries,
        "variants": sorted(variants), "crossover": crossover,
        "integration": {"method": "RK4 with advancing substep clocks",
                        "power_events": "split at outage edges and reserve exhaustion; modes frozen per segment",
                        "reserve_accounting": "analytic draw over each segment, pinned zero at exhaustion",
                        "max_substeps_per_variant": MAX_TOTAL_SUBSTEPS,
                        "terminal_interval": "shortened when duration is off the output grid"},
        "variant_summaries": dispositions, "pairwise_separation": pairs,
        "separation_tolerance": analysis["separation_tolerance"],
        "interpretation": {
            "boundary": "The boundary actuator is a rate-limited supplement driven by a noisy bulk reading. It engages during the outage failover and is idle through the capacity-closure epoch: no boundary actuation ever announces the accumulating internal shortfall, and the served fraction falls only because capacity closes while the request stays full.",
            "variants": "The interface variants run the same path under shared noise seeds. Whether the boundary can tell them apart is an output of the run, not an assumption: boundary observables separate a pair only if the run says so, and internal receipt separates them whenever internal efficiency differs.",
            "monitor": "The recorded monitor stream is separate from the controller stream and never feeds control; dropout and bias faults perturb the record only."},
        "limits": [
            "All sizes, rates, fluxes, progressions and times are invented dimensionless software fixture values.",
            "The variants are invented parameterizations of serve rate and internal efficiency; no capability, safety or biological ranking is asserted.",
            "The controller is an invented integral rule on a noisy boundary reading, not a validated clinical control law.",
            "Progression is an accumulator driven by internal receipt; it is a stage index proxy, not a developmental outcome.",
            "The reserve and outage rules are invented failover accounting, not a power-system design.",
            "Separation analysis compares synthetic runs of one model; it is not a cohort study and sets no sampling requirement.",
            "No confidence interval, health score, physical device parameter, gestational claim or gate completion is computed."]}
    lines = ["# Dimensionless whole-path system twin", "", NOTICE, "",
             f"{len(variants)} interface variants run the I1-I4 path ({len(boundaries) + 1} intervals) "
             "with shared noise seeds, one wall outage with reserve failover, and same-unit "
             "boundary events at every handoff.", "",
             f"Capacity crossover: size {crossover['crossover_size']}, time {crossover['crossover_time']}; "
             f"margin at end {crossover['margin_at_end']:.6g}.", "",
             "## Pairwise variant separation", "",
             "Boundary observables: " + ", ".join(BOUNDARY_OBSERVABLES) + ".",
             "Internal (true) observables: " + ", ".join(INTERNAL_OBSERVABLES) + ".", ""]
    for record in pairs:
        lines.append(f"- {record['pair'][0]} vs {record['pair'][1]}: " + ", ".join(
            f"{key} at handoff {value}" if value is not None else f"{key} not separated"
            for key, value in record["first_separated"].items()))
    lines.extend(["", report["interpretation"]["boundary"], "",
                  report["interpretation"]["monitor"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])
    files = {"input_config.json": raw}
    for name in sorted(variants):
        rows = runs[name]["rows"]
        files[f"trajectory_{name}.csv"] = csv_bytes(list(rows[0]), rows)
    files["boundary_events.csv"] = csv_bytes(list(all_events[0]), all_events)
    files["monitor_readings.csv"] = csv_bytes(list(monitor_rows[0]), monitor_rows)
    files["whole_path_twin_report.json"] = json_bytes(report)
    files["REPORT.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    return publish_bundle(output, kind="dimensionless_whole_path_twin", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "n_variants": len(variants),
                                                 "n_intervals": len(boundaries) + 1})
