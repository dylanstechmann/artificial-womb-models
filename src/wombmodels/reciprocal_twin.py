"""Dimensionless reciprocal wall-to-fluidic damage-leak twin (T27)."""
from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number
from .growth_scaling import analytic_crossover
from .mechanical_twin import (_WallObserver, _boundary_events,
                              _validate as _validate_mechanical)
from .whole_path_twin import (BOUNDARY_OBSERVABLES, INTERNAL_OBSERVABLES,
                              _first_separation, _variant_run)


class _FeedbackWall(_WallObserver):
    def feedback_state(self):
        return self.state[1]


def _validate(config):
    if not isinstance(config, dict) or "feedback" not in config:
        raise InputError("config must include feedback")
    fields(config["feedback"], ("leak_coefficient",), "feedback")
    coefficient = number(config["feedback"]["leak_coefficient"],
                         "feedback.leak_coefficient", 0, 100)
    mechanical = dict(config)
    mechanical.pop("feedback")
    fluidic, wall, couplings = _validate_mechanical(mechanical)
    duration = fluidic[0]
    growth, scaling, bulk, control = fluidic[3:6] + fluidic[7:8]
    parsed = fluidic[14]
    size = 1.0 + growth["linear_rate"] * duration
    capacity = scaling["capacity_coefficient"] * size ** growth["surface_exponent"]
    demand = scaling["demand_coefficient"] * size
    delivery = min(demand, capacity)
    loss = bulk["washout"] + bulk["transfer"]
    if not loss and (delivery or control["supplement_max"]):
        raise InputError("reciprocal feedback requires positive bulk loss when inflow is possible")
    stock_bound = max(delivery + control["supplement_max"], bulk["target"]) / loss if loss else 0.0
    for name, variant in parsed.items():
        initial_load = wall["load_coefficient"] * couplings[name] * min(
            scaling["demand_coefficient"], scaling["capacity_coefficient"])
        strain_bound = max(initial_load / wall["stiffness_coefficient"],
                           wall["load_coefficient"] * (stock_bound + couplings[name] * delivery)
                           / wall["stiffness_coefficient"])
        damage_bound = wall["damage_rate"] * max(
            0.0, strain_bound - wall["safe_strain"]) * duration
        variant["wall_damage_leak_rate_bound"] = coefficient * damage_bound
        if not math.isfinite(variant["wall_damage_leak_rate_bound"]):
            raise InputError("reciprocal feedback rate bound must be finite")
    return fluidic, wall, couplings, coefficient


def reciprocal_twin(config_path: Path, output: Path) -> dict:
    config, raw = read_json(config_path)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, parsed, analysis), wall, couplings, coefficient = _validate(config)
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)
    variants, runs, all_events, baseline_events = {}, {}, [], []
    for name in sorted(parsed):
        variant = dict(parsed[name], wall_coupling=couplings[name],
                       wall_damage_leak=coefficient, wall_damage=0.0)
        variants[name] = variant
        observer = _FeedbackWall(variant, growth, scaling, wall, duration)
        rows, readings, _ = _variant_run(name, variant, shared, duration, step,
                                         boundaries, observer=observer)
        runs[name] = rows
        all_events.extend(_boundary_events(name, rows, boundaries, step))
        if coefficient:
            baseline = dict(variant, wall_damage_leak=0.0,
                            wall_damage_leak_rate_bound=0.0)
            baseline_observer = _FeedbackWall(baseline, growth, scaling, wall, duration)
            baseline_rows, _, _ = _variant_run(name, baseline, shared, duration, step,
                                               boundaries, observer=baseline_observer)
            baseline_events.extend(_boundary_events(name, baseline_rows, boundaries, step))
    pairs = []
    observables = BOUNDARY_OBSERVABLES + ("wall_strain", "wall_damage") + INTERNAL_OBSERVABLES
    for first, second in combinations(sorted(variants), 2):
        separated = {key: _first_separation(all_events, first, second, key,
                                            analysis["separation_tolerance"])
                     for key in observables}
        baseline_separated = {key: _first_separation(baseline_events, first, second, key,
                                                     analysis["separation_tolerance"])
                              for key in observables} if coefficient else dict(separated)
        pairs.append({"pair": [first, second], "first_separated": separated,
                      "zero_feedback_first_separated": baseline_separated,
                      "feedback_only_first_separated": {
                          key: value for key, value in separated.items()
                          if value is not None and baseline_separated[key] is None},
                      "boundary_observables_ever_separate": any(
                          separated[key] is not None for key in BOUNDARY_OBSERVABLES)})
    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_reciprocal_twin",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "feedback": {"law": "bulk' -= leak_coefficient * wall_damage * bulk_stock",
                     "leak_coefficient": coefficient,
                     "coupling": "damage held over each canonical event-free fluidic substep"},
        "integration": {
            "fluidic_rate_bound": "base whole-path rates plus a conservative damage-dependent leak bound",
            "damage_bound": "maximum strain envelope times damage rate and duration",
            "wall_damage_leak_rate_bounds": {name: variant["wall_damage_leak_rate_bound"]
                                               for name, variant in sorted(variants.items())},
            "splitting_order": 1,
            "full_system_refinement": "qualified for the regression case in tests/test_reciprocal_twin.py"},
        "boundary_observables": list(BOUNDARY_OBSERVABLES),
        "pairwise_separation": pairs,
        "crossover": analytic_crossover(growth, scaling),
        "interpretation": "Synthetic reciprocal-coupling experiment only; pairwise separation is reported from this fixture run, not asserted as a physical result.",
        "limits": ["All model quantities and time are invented dimensionless software fixture values.",
                   "Held-damage reciprocal splitting is first order; refinement is qualified only for the stated regression case.",
                   "The conservative damage-dependent rate bound and work budget do not guarantee accuracy for every allowed configuration.",
                   "The damage-gated leak is a proposed mathematical coupling, not a measured mechanism.",
                   "Wall damage is accounting, not a fatigue, injury, rupture or biological prediction.",
                   "No physiological calibration, biological measurement, device parameter or gate movement is established."]}
    lines = ["# Dimensionless reciprocal twin", "", NOTICE, "",
             "Damage-gated bulk leakage is tested as an invented reciprocal coupling.", "",
             f"Leak coefficient: {coefficient}.", "", "## Pairwise variant separation", ""]
    for pair in pairs:
        lines.append(f"- {pair['pair'][0]} vs {pair['pair'][1]}: " + ", ".join(
            f"{k} at handoff {v}" if v is not None else f"{k} not separated"
            for k, v in pair["first_separated"].items()))
    lines.extend(["", report["interpretation"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])
    files = {"input_config.json": raw,
             "reciprocal_twin_report.json": json_bytes(report),
             "boundary_events.csv": csv_bytes(list(all_events[0]), all_events),
             "REPORT.md": ("\n".join(lines) + "\n").encode()}
    for name, rows in sorted(runs.items()):
        files[f"trajectory_{name}.csv"] = csv_bytes(list(rows[0]), rows)
    return publish_bundle(output, kind="dimensionless_reciprocal_twin", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "n_variants": len(variants)})
