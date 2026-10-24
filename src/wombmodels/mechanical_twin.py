"""Coupled mechanical twin: the whole-path world plus a chamber wall (T23).

The second twin iteration couples the T22 growth-accommodation wall into
the T21 whole-path running world. Each interface variant carries a wall
whose load is driven by the variant's interface coupling to the delivered
flux and bulk stock, and the wall never feeds anything back: the coupling
is one-way, so the fluidic trajectories of this twin are identical to the
uncoupled T21 twin's, which the run verifies explicitly.

The produced signature refines the boundary observability result. The
fluidic exchange channel still never separates any variant pair, but the
wall strain - a boundary-observable mechanical channel - separates every
pair at the first handoff, because interface coupling transmits variant
identity into an observable. Wall damage stays hidden by construction: it
never enters the derivative of any observable, exactly as in the growth
mechanics module.

No parameter represents physiology, time in days, a device setpoint or a
biological measurement; the variants are invented parameterizations with
no capability ranking.
"""
from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number
from .growth_scaling import analytic_crossover
from .numerics import require_finite
from .whole_path_twin import (BOUNDARY_OBSERVABLES, INTERNAL_OBSERVABLES,
                              MAX_TOTAL_SUBSTEPS, SUBSTEP_RATE_TARGET,
                              _first_separation, _validate as _validate_fluidic,
                              _variant_run as _uncoupled_variant_run)

MAX_WALL_COUPLING = 100.0
WALL_BOUNDARY_OBSERVABLES = ("wall_strain",)
WALL_INTERNAL_OBSERVABLES = ("wall_damage",)


def _validate(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "interval_boundaries",
                    "growth", "scaling", "bulk", "internal", "control", "reserve", "outages",
                    "monitor", "variants", "analysis", "wall"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    fields(config["wall"], ("load_coefficient", "viscosity", "stiffness_coefficient",
                            "stiffness_exponent", "safe_strain", "strain_limit",
                            "damage_rate"), "wall")
    wall = {"load_coefficient": number(config["wall"]["load_coefficient"],
                                        "load_coefficient", 1e-6, 1_000),
            "viscosity": number(config["wall"]["viscosity"], "viscosity", 1e-6, 100),
            "stiffness_coefficient": number(config["wall"]["stiffness_coefficient"],
                                             "stiffness_coefficient", 1e-6, 1_000),
            "stiffness_exponent": number(config["wall"]["stiffness_exponent"],
                                         "stiffness_exponent", 0, 1.0),
            "safe_strain": number(config["wall"]["safe_strain"], "safe_strain", 0, 1_000),
            "strain_limit": number(config["wall"]["strain_limit"], "strain_limit", 1e-6, 1_000),
            "damage_rate": number(config["wall"]["damage_rate"], "damage_rate", 0, 100)}
    if wall["safe_strain"] >= wall["strain_limit"]:
        raise InputError("wall safe_strain must lie below strain_limit")

    couplings = {}
    if not isinstance(config["variants"], dict):
        raise InputError("variants must map named interface parameterizations")
    for name, item in config["variants"].items():
        if not isinstance(item, dict):
            raise InputError(f"variant {name} must be a JSON object")
        couplings[name] = number(item.get("wall_coupling"), f"{name} wall_coupling",
                                1e-6, MAX_WALL_COUPLING)

    stripped = {key: value for key, value in config.items() if key != "wall"}
    stripped["variants"] = {name: {key: value for key, value in item.items()
                                   if key != "wall_coupling"}
                            for name, item in config["variants"].items()}
    fluidic = _validate_fluidic(stripped)
    return fluidic, wall, couplings


class _WallObserver:
    """One-way wall subcycling on the canonical fluidic RK4 continuous extension.

    The cubic dense extension interpolates fluidic stage derivatives within
    one event-free substep. It is third-order in the interior and agrees with
    the fluidic RK4 endpoints. No interpolation spans a power discontinuity.
    Only the wall is refined: it cannot change fluidic arithmetic or RNG draws.
    """
    def __init__(self, variant, growth, scaling, wall, duration):
        self.variant, self.growth, self.scaling, self.wall = variant, growth, scaling, wall
        self.rate = (wall["stiffness_coefficient"]
                     * (1.0 + growth["linear_rate"] * duration) ** wall["stiffness_exponent"]
                     / wall["viscosity"])
        if duration * self.rate / SUBSTEP_RATE_TARGET > MAX_TOTAL_SUBSTEPS:
            raise InputError(f"Wall integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
        load = wall["load_coefficient"] * variant["wall_coupling"] * min(
            scaling["demand_coefficient"], scaling["capacity_coefficient"])
        self.state = [load / wall["stiffness_coefficient"], 0.0]
        self.work = 0

    def observe(self, time, row):
        load = self.wall["load_coefficient"] * (
            row["bulk_stock"] + self.variant["wall_coupling"] * row["delivered_flux"])
        stiffness = self.wall["stiffness_coefficient"] * row["size"] ** self.wall["stiffness_exponent"]
        return {"wall_load": load, "wall_stiffness": stiffness, "wall_strain": self.state[0],
                "wall_safety_margin": self.wall["strain_limit"] - self.state[0],
                "wall_damage": self.state[1]}

    def advance(self, time, fluidic, span, stages, operating):
        count = max(1, math.ceil(span * self.rate / SUBSTEP_RATE_TARGET))
        self.work += count
        if self.work > MAX_TOTAL_SUBSTEPS:
            raise InputError(f"Wall integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
        power, _draw = operating

        def rhs(offset, state):
            theta = offset / span
            square, cube = theta * theta, theta * theta * theta
            weights = (theta - 1.5 * square + 2.0 * cube / 3.0,
                       square - 2.0 * cube / 3.0,
                       square - 2.0 * cube / 3.0,
                       -0.5 * square + 2.0 * cube / 3.0)
            request, stock = (fluidic[position] + span * sum(
                weight * stage[position] for weight, stage in zip(weights, stages))
                for position in (0, 1))
            size = 1.0 + self.growth["linear_rate"] * (time + offset)
            capacity = self.scaling["capacity_coefficient"] * size ** self.growth["surface_exponent"]
            demand = self.scaling["demand_coefficient"] * size
            delivered = min(demand * min(max(request, 0.0), 1.0), capacity) * power
            load = self.wall["load_coefficient"] * (
                max(stock, 0.0) + self.variant["wall_coupling"] * delivered)
            stiffness = self.wall["stiffness_coefficient"] * size ** self.wall["stiffness_exponent"]
            return [(load - stiffness * state[0]) / self.wall["viscosity"],
                    self.wall["damage_rate"] * max(0.0, state[0] - self.wall["safe_strain"])]

        substep = span / count
        for index in range(count):
            offset = index * substep
            first = rhs(offset, self.state)
            second = rhs(offset + substep / 2.0,
                         [value + substep * rate / 2.0 for value, rate in zip(self.state, first)])
            third = rhs(offset + substep / 2.0,
                        [value + substep * rate / 2.0 for value, rate in zip(self.state, second)])
            fourth = rhs(offset + substep,
                         [value + substep * rate for value, rate in zip(self.state, third)])
            self.state = [value + substep * (a + 2 * b + 2 * c + d) / 6.0
                          for value, a, b, c, d in zip(self.state, first, second, third, fourth)]
            require_finite(self.state)
            self.state = [max(0.0, value) for value in self.state]


def _coupled_variant_run(name, variant, shared, duration, step, boundaries, wall):
    """Reuse the exact fluidic calculation; refine the one-way wall independently."""
    observer = _WallObserver(variant, shared[0], shared[1], wall, duration)
    rows, readings, _events = _uncoupled_variant_run(
        name, variant, shared, duration, step, boundaries, observer=observer)
    return rows, readings


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
                           "progression": row["progression"], "size": row["size"],
                           "wall_strain": row["wall_strain"], "wall_damage": row["wall_damage"]})
    return events


def _first_crossing(rows, column, threshold):
    for row in rows:
        if row[column] > threshold:
            return row["dimensionless_time"]
    return None


FLUIDIC_COLUMNS = ("dimensionless_time", "size", "capacity_margin", "request_fraction",
                   "served_fraction", "delivered_flux", "bulk_stock", "deep_receipt_rate",
                   "cumulative_unserved", "progression", "reserve", "supplement",
                   "controller_reading")


def mechanical_twin(config_path: Path, output: Path) -> dict:
    """Publish the coupled mechanical twin; nothing is fitted or measured."""
    config, raw = read_json(config_path)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, faults, parsed, analysis), wall, couplings = _validate(config)
    variants = {name: dict(parsed[name], wall_coupling=couplings[name]) for name in parsed}
    shared = (growth, scaling, bulk, internal, control, reserve, outages,
              cadence, noise_sd, seed, faults)

    runs = {}
    uncoupled = {}
    for name in sorted(variants):
        rows, readings = _coupled_variant_run(name, variants[name], shared, duration, step,
                                              boundaries, wall)
        runs[name] = {"rows": rows, "readings": readings}
        uncoupled[name] = _uncoupled_variant_run(name, variants[name], shared, duration, step,
                                                 boundaries)[0]

    one_way = all(all(row[column] == other[column]
                      for row, other in zip(runs[name]["rows"], uncoupled[name])
                      for column in FLUIDIC_COLUMNS)
                  for name in sorted(variants))

    crossover = analytic_crossover(growth, scaling)
    crossover["margin_at_end"] = runs[sorted(variants)[0]]["rows"][-1]["capacity_margin"]
    all_events = [event for name in sorted(variants) for event
                  in _boundary_events(name, runs[name]["rows"], boundaries, step)]
    observables = BOUNDARY_OBSERVABLES + WALL_BOUNDARY_OBSERVABLES \
        + INTERNAL_OBSERVABLES + WALL_INTERNAL_OBSERVABLES
    pairs = []
    for first, second in combinations(sorted(variants), 2):
        record = {"pair": [first, second], "first_separated": {}}
        for observable in observables:
            record["first_separated"][observable] = _first_separation(
                all_events, first, second, observable, analysis["separation_tolerance"])
        record["fluidic_boundary_ever_separate"] = any(
            record["first_separated"][key] is not None for key in BOUNDARY_OBSERVABLES)
        record["wall_strain_ever_separates"] = (
            record["first_separated"]["wall_strain"] is not None)
        record["internal_ever_separate"] = any(
            record["first_separated"][key] is not None
            for key in INTERNAL_OBSERVABLES + WALL_INTERNAL_OBSERVABLES)
        pairs.append(record)

    wall_summaries = {}
    for name in sorted(variants):
        rows = runs[name]["rows"]
        final = rows[-1]
        wall_summaries[name] = {
            "wall_coupling": variants[name]["wall_coupling"],
            "final_wall_strain": final["wall_strain"],
            "final_wall_damage": final["wall_damage"],
            "final_wall_safety_margin": final["wall_safety_margin"],
            "strain_limit_crossing_time": _first_crossing(rows, "wall_strain",
                                                           wall["strain_limit"])}

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_mechanical_twin",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "n_intervals": len(boundaries) + 1, "boundaries": boundaries,
        "variants": sorted(variants), "crossover": crossover,
        "integration": {
            "fluidic_solver": "canonical whole-path RK4 with event-split power modes",
            "wall_solver": "independent RK4 subcycling bounded by maximum stiffness/viscosity",
            "wall_forcing": "cubic dense fluidic RK4 extension, third order in the interior",
            "interpolates_across_power_events": False,
            "max_substeps_per_variant_per_solver": MAX_TOTAL_SUBSTEPS,
            "terminal_interval": "shortened when duration is off the output grid"},
        "one_way_coupling": {
            "wall_states_enter_fluidic_derivatives": False,
            "fluidic_trajectories_match_uncoupled_twin": one_way,
            "compared_columns": list(FLUIDIC_COLUMNS)},
        "wall_summaries": wall_summaries, "pairwise_separation": pairs,
        "separation_tolerance": analysis["separation_tolerance"],
        "interpretation": {
            "one_way": "The wall observes the running world; the running world never observes the wall. The run re-executes the uncoupled whole-path twin in the same process and the fluidic trajectories match exactly, so every fluidic result of the first twin iteration is carried over unchanged.",
            "mechanical": "Interface coupling transmits variant identity into a boundary-observable channel: the fluidic exchange observables still never separate any pair, but wall strain separates every pair, giving the boundary a variant-revealing observable the fluidic channel alone never provides.",
            "damage": "Wall damage stays hidden by construction: it enters no observable's derivative, so no reading distinguishes walls that differ only in accumulated damage."},
        "limits": [
            "All sizes, fluxes, strains, damages and times are invented dimensionless software fixture values.",
            "The variants are invented parameterizations; no capability, safety or biological ranking is asserted, and the wall couplings are invented interface constants.",
            "The Kelvin-Voigt wall is an abstract viscoelastic element, not a validated uterine or chamber material model.",
            "Wall damage is invented linear accounting of strain excess; it is not a fatigue, injury or rupture prediction.",
            "The one-way coupling is a modeling choice of this fixture, not a claim that a physical wall cannot feed back.",
            "Wall forcing uses a third-order interior dense interpolation of fluidic RK4 stages; wall subcycling does not remove fluidic discretization error. Step refinement must control that error separately.",
            "Separation analysis compares synthetic runs of one model; it is not a cohort study and sets no sampling requirement.",
            "No confidence interval, health score, physical device parameter, gestational claim or gate completion is computed."]}
    lines = ["# Dimensionless coupled mechanical twin", "", NOTICE, "",
             f"{len(variants)} interface variants run the I1-I4 path with a coupled chamber wall; "
             "the wall observes the world, the world never observes the wall.", "",
             f"One-way coupling verified against the uncoupled twin: {one_way}.", "",
             f"Capacity crossover: size {crossover['crossover_size']}, time {crossover['crossover_time']}; "
             f"margin at end {crossover['margin_at_end']:.6g}.", "",
             "## Pairwise variant separation", "",
             "Fluidic boundary observables: " + ", ".join(BOUNDARY_OBSERVABLES) + ".",
             "Mechanical boundary observable: wall_strain.",
             "Internal observables: " + ", ".join(INTERNAL_OBSERVABLES) + ", wall_damage.", ""]
    for record in pairs:
        lines.append(f"- {record['pair'][0]} vs {record['pair'][1]}: " + ", ".join(
            f"{key} at handoff {value}" if value is not None else f"{key} not separated"
            for key, value in record["first_separated"].items()))
    lines.extend(["", report["interpretation"]["mechanical"], "",
                  report["interpretation"]["damage"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])
    files = {"input_config.json": raw}
    for name in sorted(variants):
        files[f"trajectory_{name}.csv"] = csv_bytes(list(runs[name]["rows"][0]), runs[name]["rows"])
    files["boundary_events.csv"] = csv_bytes(list(all_events[0]), all_events)
    files["mechanical_twin_report.json"] = json_bytes(report)
    files["REPORT.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    return publish_bundle(output, kind="dimensionless_mechanical_twin", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "n_variants": len(variants),
                                                 "n_intervals": len(boundaries) + 1})
