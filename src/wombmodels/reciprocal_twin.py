"""Dimensionless reciprocal wall-to-fluidic damage-leak twin (T27)."""
from __future__ import annotations

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
    return fluidic, wall, couplings, coefficient


def reciprocal_twin(config_path: Path, output: Path) -> dict:
    config, raw = read_json(config_path)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, parsed, analysis), wall, couplings, coefficient = _validate(config)
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)
    variants, runs, all_events = {}, {}, []
    for name in sorted(parsed):
        variant = dict(parsed[name], wall_coupling=couplings[name],
                       wall_damage_leak=coefficient, wall_damage=0.0)
        variants[name] = variant
        observer = _FeedbackWall(variant, growth, scaling, wall, duration)
        rows, readings, _ = _variant_run(name, variant, shared, duration, step,
                                         boundaries, observer=observer)
        runs[name] = rows
        all_events.extend(_boundary_events(name, rows, boundaries, step))
    pairs = []
    observables = BOUNDARY_OBSERVABLES + ("wall_strain", "wall_damage") + INTERNAL_OBSERVABLES
    for first, second in combinations(sorted(variants), 2):
        separated = {key: _first_separation(all_events, first, second, key,
                                            analysis["separation_tolerance"])
                     for key in observables}
        pairs.append({"pair": [first, second], "first_separated": separated,
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
        "boundary_observables": list(BOUNDARY_OBSERVABLES),
        "pairwise_separation": pairs,
        "crossover": analytic_crossover(growth, scaling),
        "interpretation": "Synthetic reciprocal-coupling experiment only; pairwise separation is reported from this fixture run, not asserted as a physical result.",
        "limits": ["All model quantities and time are invented dimensionless software fixture values.",
                   "Held-damage reciprocal splitting is first order; full-system refinement remains unqualified.",
                   "The fluidic rate schedule lacks a damage-dependent leak stiffness bound; bounded inputs do not guarantee numerical accuracy.",
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
