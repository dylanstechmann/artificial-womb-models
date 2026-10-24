"""Minimum-measurement acquisition specification computed from the twin (T24).

The deferred D12 queue item: convert the twin's produced variant signatures
into the numeric minimum-measurement specification that the T05 challenge
demanded - compartments, timepoints, resolution and units per cohort that a
laboratory can quote and a reviewer can audit, with every number recomputed
from the running coupled twin rather than asserted.

Required channels are computed from the run, not chosen: a channel enters the
specification only if the twin separates every variant pair simultaneously
at a post-handoff and it is directly instrumentable. Each channel uses its
own earliest qualifying handoff. The resolution floor is analytic under the twin's
own relative-tolerance separation criterion with a k-sigma noise guard, and
units per cohort scale as the squared inverse of the resolution margin. A
seeded empirical sweep over noise multipliers and cohort sizes checks both
on synthetic ground truth, freezing the analysis plan before any real data
exists.

No parameter represents physiology, time in days, a device setpoint or a
biological measurement; the variants are invented parameterizations with no
capability ranking.
"""
from __future__ import annotations

import math
import random
from itertools import combinations
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number
from .growth_scaling import analytic_crossover
from .numerics import output_times
from .mechanical_twin import (FLUIDIC_COLUMNS, WALL_BOUNDARY_OBSERVABLES, WALL_INTERNAL_OBSERVABLES,
                              _boundary_events, _coupled_variant_run,
                              _validate as _validate_twin)
from .whole_path_twin import (BOUNDARY_OBSERVABLES, INTERNAL_OBSERVABLES, _first_separation,
                              _variant_run as _uncoupled_variant_run)

COHORT_UNIT_CAP = 256
SEED_STRIDE = 104_729

CHANNEL_CATALOG = {
    "delivered_flux": {"compartment": "exchange_boundary", "kind": "boundary_instrument", "dmp": "D"},
    "served_fraction": {"compartment": "exchange_boundary", "kind": "derived_ratio", "dmp": "D"},
    "bulk_stock": {"compartment": "exchange_boundary", "kind": "boundary_instrument", "dmp": "D"},
    "wall_strain": {"compartment": "chamber_wall", "kind": "mechanical_instrument", "dmp": "W"},
    "wall_damage": {"compartment": "chamber_wall", "kind": "derived_accumulator", "dmp": "W"},
    "deep_receipt_rate": {"compartment": "internal_tissue", "kind": "internal_instrument", "dmp": "M"},
    "cumulative_unserved": {"compartment": "internal_tissue", "kind": "derived_accumulator", "dmp": "M"},
    "progression": {"compartment": "staging_index", "kind": "internal_instrument", "dmp": "P"},
}
INSTRUMENTABLE = frozenset(name for name, entry in CHANNEL_CATALOG.items()
                           if entry["kind"].endswith("instrument"))
OBSERVABLES = BOUNDARY_OBSERVABLES + WALL_BOUNDARY_OBSERVABLES \
    + INTERNAL_OBSERVABLES + WALL_INTERNAL_OBSERVABLES


def _validate_spec(block):
    fields(block, ("detection_sigma", "cohort_confidence", "confirm_seeds", "noise_multipliers"), "spec")
    sigma = number(block["detection_sigma"], "detection_sigma", 0.1, 10)
    confidence = number(block["cohort_confidence"], "cohort_confidence", 0.5, 1.0)
    if confidence >= 1.0:
        raise InputError("cohort_confidence must lie below 1")
    seeds = block["confirm_seeds"]
    if isinstance(seeds, bool) or not isinstance(seeds, int) or not 1 <= seeds <= 256:
        raise InputError("confirm_seeds must be an integer in [1, 256]")
    raw = block["noise_multipliers"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= 12:
        raise InputError("noise_multipliers must be a list of 1 to 12 values")
    multipliers = [number(item, "noise multiplier", 0.01, 64.0) for item in raw]
    if multipliers != sorted(multipliers):
        raise InputError("noise_multipliers must be ascending")
    return {"detection_sigma": sigma, "cohort_confidence": confidence,
            "confirm_seeds": seeds, "noise_multipliers": multipliers}


def _validate(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
                    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
                    "monitor", "variants", "analysis", "wall", "spec"), "config")
    twin_config = {key: value for key, value in config.items() if key != "spec"}
    return (*_validate_twin(twin_config), _validate_spec(config["spec"]))


def _separated(a, b, tolerance):
    """The twin's own pairwise separation statistic, on noisy readings."""
    return abs(a - b) / max(abs(a), abs(b), 1e-12) > tolerance


def _single_unit_reliability(a, b, tolerance, noise_sd, multiplier, seeds, base_seed):
    """Fraction of seeded single-unit readings that separate beyond tolerance."""
    if noise_sd <= 0.0:
        return 1.0 if _separated(a, b, tolerance) else 0.0
    separated_count = 0
    for index in range(seeds):
        rng = random.Random(base_seed + index)
        noisy_a = a + multiplier * noise_sd * rng.gauss(0.0, 1.0)
        noisy_b = b + multiplier * noise_sd * rng.gauss(0.0, 1.0)
        if _separated(noisy_a, noisy_b, tolerance):
            separated_count += 1
    return separated_count / seeds


def _cohort_reliability(a, b, tolerance, noise_sd, multiplier, units, seeds, base_seed):
    """Separation reliability of per-allocation means over `units` synthetic units."""
    if noise_sd <= 0.0 or units <= 0:
        return 1.0 if _separated(a, b, tolerance) else 0.0
    separated_count = 0
    for index in range(seeds):
        rng = random.Random(base_seed + SEED_STRIDE * index)
        noisy_a = a + multiplier * noise_sd * sum(rng.gauss(0.0, 1.0)
                                                 for _ in range(units)) / units
        noisy_b = b + multiplier * noise_sd * sum(rng.gauss(0.0, 1.0)
                                                 for _ in range(units)) / units
        if _separated(noisy_a, noisy_b, tolerance):
            separated_count += 1
    return separated_count / seeds


def _first_crossing(rows, column, threshold):
    for row in rows:
        if row[column] > threshold:
            return row["dimensionless_time"]
    return None


def _channel_requirements(events, pair_names, tolerance):
    """Qualify a channel only at a handoff that separates every pair at once.

    First-ever pairwise separation can occur at different handoffs and can
    disappear later. It cannot by itself justify a positive noise margin.
    Each channel gets its own earliest qualifying post-handoff observation.
    """
    post = {(event["variant"], event["handoff"]): event
            for event in events if event["phase"] == "post"}
    handoffs = sorted({handoff for _name, handoff in post})
    separated = {(first, second, channel): _first_separation(
        events, first, second, channel, tolerance)
        for first, second in pair_names for channel in OBSERVABLES}
    requirements = []
    for channel in OBSERVABLES:
        entry = CHANNEL_CATALOG[channel]
        pair_count = sum(separated[(first, second, channel)] is not None
                         for first, second in pair_names)
        common = next((handoff for handoff in handoffs if all(
            _separated(post[(first, handoff)][channel], post[(second, handoff)][channel],
                       tolerance) for first, second in pair_names)), None)
        instrumentable = channel in INSTRUMENTABLE
        reason = None
        if pair_count == 0:
            reason = "never_separates_any_pair"
        elif pair_count < len(pair_names):
            reason = "separates_only_some_pairs"
        elif common is None:
            reason = "no_common_separated_handoff"
        elif not instrumentable:
            reason = "derived_not_directly_instrumentable"
        requirements.append({
            "channel": channel, "compartment": entry["compartment"], "kind": entry["kind"],
            "dmp": entry["dmp"], "separates_all_pairs": common is not None,
            "pairs_separated_ever": pair_count, "variant_pair_count": len(pair_names),
            "first_separated_handoff": common,
            "instrumentable": instrumentable, "required": common is not None and instrumentable,
            "excluded_reason": reason})
    return requirements, separated


def acquisition_spec(config_path: Path, output: Path) -> dict:
    """Publish the acquisition specification; nothing is fitted or measured."""
    config, raw = read_json(config_path)
    fluidic, wall, couplings, spec = _validate(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, parsed, analysis) = fluidic
    variants = {name: dict(parsed[name], wall_coupling=couplings[name]) for name in parsed}
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)
    sigma_k = spec["detection_sigma"]
    confidence = spec["cohort_confidence"]
    seeds = spec["confirm_seeds"]
    multipliers = spec["noise_multipliers"]
    tolerance = analysis["separation_tolerance"]

    rows_by_variant = {}
    for name in sorted(variants):
        rows, _readings = _coupled_variant_run(name, variants[name], shared, duration,
                                               step, boundaries, wall)
        rows_by_variant[name] = rows
    one_way = True
    for name in sorted(variants):
        uncoupled = _uncoupled_variant_run(name, variants[name], shared, duration, step,
                                           boundaries)[0]
        for coupled_row, uncoupled_row in zip(rows_by_variant[name], uncoupled):
            if any(coupled_row[column] != uncoupled_row[column] for column in FLUIDIC_COLUMNS):
                one_way = False
    all_events = [event for name in sorted(variants)
                  for event in _boundary_events(name, rows_by_variant[name], boundaries, step)]
    pair_names = list(combinations(sorted(variants), 2))
    channel_requirements, separated = _channel_requirements(all_events, pair_names, tolerance)
    required_channels = [row["channel"] for row in channel_requirements if row["required"]]
    if not required_channels:
        raise InputError("No instrumentable channel separates every variant pair at a common "
                         "handoff; no specification can form")
    channel_handoffs = {row["channel"]: row["first_separated_handoff"]
                        for row in channel_requirements if row["required"]}
    first_handoff = min(channel_handoffs.values())
    handoff = max(channel_handoffs.values())
    readings = {(name, channel): next(event[channel] for event in all_events
                                      if event["variant"] == name
                                      and event["handoff"] == channel_handoffs[channel]
                                      and event["phase"] == "post")
                for name in sorted(variants) for channel in required_channels}

    pair_resolution = {}
    channel_floor = {}
    binding_pair = {}
    for channel in required_channels:
        pair_resolution[channel] = {}
        margins = []
        for first, second in pair_names:
            a, b = readings[(first, channel)], readings[(second, channel)]
            effect = abs(a - b)
            scale = max(abs(a), abs(b), 1e-12)
            margin = effect - tolerance * scale
            if not math.isfinite(margin) or margin <= 0.0:
                raise InputError(f"No positive separation margin for {channel}: {first}|{second}")
            floor = None
            if margin > 0.0 and noise_sd > 0.0:
                floor = margin / (sigma_k * math.sqrt(2.0) * noise_sd)
            pair_resolution[channel][f"{first}|{second}"] = {
                "effect": effect, "scale": scale, "margin": margin,
                "floor_multiplier": floor}
            margins.append((margin, f"{first}|{second}"))
        worst = min(margins)
        binding_pair[channel] = {"pair": worst[1], "margin": worst[0]}
        floors = [pair_resolution[channel][label]["floor_multiplier"]
                  for label in pair_resolution[channel]]
        channel_floor[channel] = min((value for value in floors if value is not None),
                                     default=None)

    floor_sweep = []
    for channel_index, channel in enumerate(required_channels):
        for pair_index, (first, second) in enumerate(pair_names):
            a, b = readings[(first, channel)], readings[(second, channel)]
            floor = pair_resolution[channel][f"{first}|{second}"]["floor_multiplier"]
            base_seed = seed + 7919 * (pair_index + 1) + SEED_STRIDE * (channel_index + 1)
            for multiplier in multipliers:
                reliability = _single_unit_reliability(a, b, tolerance, noise_sd, multiplier,
                                                       seeds, base_seed)
                floor_sweep.append({
                    "channel": channel, "pair": f"{first}|{second}",
                    "multiplier": multiplier, "analytic_floor_multiplier": floor,
                    "analytic_separated_with_margin": noise_sd == 0.0 or (
                        floor is not None and multiplier <= floor),
                    "empirical_reliability": reliability,
                    "separated_at_confidence": reliability >= confidence})

    cohort = {}
    for channel_index, channel in enumerate(required_channels):
        label = binding_pair[channel]["pair"]
        first, second = label.split("|")
        a, b = readings[(first, channel)], readings[(second, channel)]
        margin = binding_pair[channel]["margin"]
        base_seed = seed + 7919 * (pair_names.index((first, second)) + 1) \
            + SEED_STRIDE * (channel_index + 1)
        sweep = []
        for multiplier in multipliers:
            units = 1
            if noise_sd > 0.0:
                units = max(1, math.ceil(2.0 * (sigma_k * multiplier * noise_sd / margin) ** 2))
            if units <= COHORT_UNIT_CAP:
                reliability = _cohort_reliability(a, b, tolerance, noise_sd, multiplier,
                                                  units, seeds, base_seed)
                capped = False
            else:
                reliability = None
                capped = True
            sweep.append({"multiplier": multiplier, "analytic_units": units,
                          "empirical_reliability": reliability, "capped": capped,
                          "confirmed": reliability is not None and reliability >= confidence})
        cohort[channel] = {"binding_pair": label, "margin": margin, "sweep": sweep}

    by_channel = {row["channel"]: row for row in channel_requirements}

    def _discriminates(channels):
        return any(by_channel[channel]["separates_all_pairs"] for channel in channels)

    dmp_contract = {
        "D_delivery_at_boundary": {
            "channels": ["delivered_flux", "served_fraction", "bulk_stock"],
            "discriminates_allocations": _discriminates(
                ["delivered_flux", "served_fraction", "bulk_stock"])},
        "M_internal_receipt": {
            "channels": ["deep_receipt_rate", "cumulative_unserved"],
            "discriminates_allocations": _discriminates(
                ["deep_receipt_rate", "cumulative_unserved"])},
        "P_progression": {
            "channels": ["progression"],
            "discriminates_allocations": _discriminates(["progression"])},
        "W_chamber_wall_mechanics": {
            "channels": ["wall_strain", "wall_damage"],
            "discriminates_allocations": _discriminates(["wall_strain", "wall_damage"])}}

    crossover = analytic_crossover(growth, scaling)
    crossover["margin_at_end"] = rows_by_variant[sorted(variants)[0]][-1]["capacity_margin"]
    wall_crossings = {name: _first_crossing(rows_by_variant[name], "wall_strain",
                                            wall["strain_limit"])
                      for name in sorted(variants)}
    timing = {
        "sampling_cadence": step, "monitor_cadence": cadence, "handoff_times": boundaries,
        "first_separated_handoff": first_handoff,
        "first_separated_time": boundaries[first_handoff - 1],
        "plan_complete_handoff": handoff,
        "plan_complete_time": boundaries[handoff - 1],
        "channel_handoffs": channel_handoffs,
        "channel_times": {channel: boundaries[value - 1]
                          for channel, value in channel_handoffs.items()},
        "selection_rule": "Each channel uses its earliest post-handoff with simultaneous "
                          "separation of every pair; the plan covers the latest selected handoff.",
        "discrimination_timepoints": round(boundaries[handoff - 1] / step) + 1,
        "surveillance_timepoints": len(output_times(duration, step)),
        "capacity_crossover_time": crossover["crossover_time"],
        "wall_limit_crossing_times": wall_crossings}

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_acquisition_spec",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "source_twin": {"result_kind": "dimensionless_mechanical_twin",
                        "n_variants": len(variants), "n_intervals": len(boundaries) + 1,
                        "one_way_coupling_verified": one_way, "crossover": crossover},
        "channel_requirements": channel_requirements,
        "pairwise_first_separated": [
            {"pair": [first, second], "channel": channel,
             "first_separated_handoff": separated[(first, second, channel)]}
            for first, second in pair_names for channel in OBSERVABLES],
        "timing": timing,
        "resolution": {
            "reference_noise_sd": noise_sd, "separation_tolerance": tolerance,
            "detection_sigma": sigma_k,
            "floor_status": "not_applicable_zero_reference_noise" if noise_sd == 0.0
                            else "finite_positive_reference_noise",
            "floor_formula": "m* = (effect - tolerance * scale) / (detection_sigma * sqrt(2) * reference_noise)",
            "units_formula": "N(m) = ceil(2 * (detection_sigma * m * reference_noise / margin)^2)",
            "pairs": pair_resolution, "channel_floor_multiplier": channel_floor},
        "binding_pair": binding_pair, "noise_floor_sweep": floor_sweep,
        "units_per_cohort": cohort, "dmp_contract": dmp_contract,
        "spec_parameters": {"detection_sigma": sigma_k, "cohort_confidence": confidence,
                            "confirm_seeds": seeds, "noise_multipliers": multipliers},
        "interpretation": {
            "required": "A channel enters the specification only if every variant pair separates simultaneously at a post-handoff and the channel is directly instrumentable. Effects and margins use that channel's earliest qualifying handoff; the sampling plan extends through the latest selected handoff.",
            "resolution": "The floor multiplier is a first-order k-sigma approximation under the twin's relative-tolerance criterion. With zero reference noise its multiplier is not applicable (null); noiseless separated readings need one unit.",
            "cohort": "Units per allocation scale as the squared inverse of the positive separation margin. The seeded sweep reports confirmation or failure at each swept noise level; it does not guarantee confirmation.",
            "negative": "Excluded channels retain distinct reasons: no pair separates, only some pairs separate, all pairs separate at different handoffs without a common observation, or the channel is derived rather than directly instrumentable. Exclusion from this single-handoff-per-channel plan does not rule out a joint-channel or longitudinal discriminator.",
            "t08": "This numeric specification is the qualified-requirements input a future owned-platform and resource decision consumes: a laboratory can quote the channels, cadence, resolution and units per cohort after calibration replaces the invented dimensionless values, and a reviewer can audit every number back to the running twin."},
        "limits": [
            "All channels, effects, floors, cohort sizes and times are invented dimensionless software fixture values computed from the twin.",
            "The specification is a template: a laboratory can quote these numbers only after calibration replaces every invented dimensionless value with a measured one.",
            "The k-sigma resolution guard and the cohort-size formula are first-order approximations under the twin's seeded Gaussian stream, not a validated statistical power analysis.",
            "Instrumentability is a declared catalog of this fixture, not a claim about real sensors.",
            "The seeded sweep freezes the analysis plan on synthetic ground truth; it is not a cohort study of any real population.",
            "No price, procurement, vendor, timeline, biological capability or gate completion is computed."]}

    def _show(value):
        return "none" if value is None else format(value, ".6g")

    lines = ["# Dimensionless minimum-measurement acquisition specification", "", NOTICE, "",
             "Computed from the running coupled twin: every number below is an output of the run, not an assertion.",
             "",
             f"Source twin: {len(variants)} variants, {len(boundaries) + 1} intervals, one-way coupling verified: {one_way}.",
             f"Capacity crossover: size {crossover['crossover_size']}, time {crossover['crossover_time']}.",
             "", "## Required channels (procurement)", ""]
    for channel in required_channels:
        entry = CHANNEL_CATALOG[channel]
        selected_handoff = channel_handoffs[channel]
        units_one = next((row["analytic_units"] for row in cohort[channel]["sweep"]
                          if row["multiplier"] == 1.0), None)
        lines.append(f"- {channel} ({entry['compartment']}, {entry['dmp']}): separates every pair "
                     f"at handoff {selected_handoff} (t={boundaries[selected_handoff - 1]}); "
                     + ("noise multiplier floor not applicable (zero reference noise)"
                        if noise_sd == 0.0 else
                        f"floor {_show(channel_floor[channel])}x reference noise")
                     + (f"; {units_one} unit(s) per allocation at reference noise"
                        if units_one else "") + ".")
    lines.extend(["", "## Excluded channels", ""])
    for row in channel_requirements:
        if not row["required"]:
            lines.append(f"- {row['channel']} ({row['compartment']}, {row['dmp']}): "
                         f"{row['excluded_reason']}.")
    lines.extend(["", "## Timing", "",
                  f"- Sampling cadence {step}; the full plan needs {timing['discrimination_timepoints']} "
                  f"timepoints through handoff {handoff} (t={timing['plan_complete_time']}).",
                  f"- Surveillance of the failure arc needs {timing['surveillance_timepoints']} "
                  f"timepoints through t={duration}.",
                  "- Wall strain-limit crossings: " + ", ".join(
                      f"{name} {_show(value)}"
                      for name, value in wall_crossings.items()) + ".",
                  "", "## Resolution and cohort sweep", "",
                  f"- Detection sigma {sigma_k}; confidence {confidence}; {seeds} seeds; "
                  f"noise multipliers {multipliers}.",
                  "- Analytic units per allocation and empirical confirmation, per binding pair:"])
    for channel in required_channels:
        parts = []
        for row in cohort[channel]["sweep"]:
            suffix = ", capped" if row["capped"] else \
                f", {'confirmed' if row['confirmed'] else 'unconfirmed'} " \
                f"(reliability {row['empirical_reliability']:.6g})"
            parts.append(f"m={row['multiplier']:g}: N={row['analytic_units']}{suffix}")
        lines.append(f"- {channel} (binding pair {cohort[channel]['binding_pair']}): "
                     + "; ".join(parts))
    lines.extend(["", report["interpretation"]["negative"], "",
                  report["interpretation"]["t08"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])

    files = {"input_config.json": raw,
             "channel_requirements.csv": csv_bytes(list(channel_requirements[0]),
                                                   channel_requirements),
             "pairwise_first_separated.csv": csv_bytes(
                 list(report["pairwise_first_separated"][0]),
                 report["pairwise_first_separated"]),
             "noise_floor_sweep.csv": csv_bytes(list(floor_sweep[0]), floor_sweep)}
    cohort_rows = [{"channel": channel, **row} for channel in required_channels
                   for row in cohort[channel]["sweep"]]
    files["units_per_cohort.csv"] = csv_bytes(list(cohort_rows[0]), cohort_rows)
    files["acquisition_spec_report.json"] = json_bytes(report)
    files["REPORT.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    return publish_bundle(output, kind="dimensionless_acquisition_spec", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "n_required_channels": len(required_channels),
                                                 "n_variants": len(variants)})
