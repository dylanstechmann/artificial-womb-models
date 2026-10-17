"""Growth-accommodation mechanics of a chamber wall (dimensionless, T22).

A Kelvin--Voigt chamber wall (viscosity eta, stiffness E) carries a load
that grows with unit size while wall stiffness scales with a sub-linear
exponent - the mechanical square-cube analogue of the growth-scaling
fixture. The equilibrium strain grows with size and crosses the strain
limit at an analytic time, so growth-paced accommodation is a measured
property, not an assumption.

Two structural results. First, accommodation regimes differ in the
observable channel: a growth-paced wall and a fixed-stiffness wall under
the same load separate in measured strain immediately and fail at
different times - unlike internal delivery, the mechanical channel has no
spatial observability problem. Second, cumulative damage accrues from
strain beyond a safe threshold and never enters the strain equation: two
walls with different damage rates share one strain series exactly, so
hidden wear is invisible in strain readings by construction.

No parameter represents physiology, time in days, a device setpoint or a
biological measurement.
"""
from __future__ import annotations

import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .exchange import NOTICE, fields, number

MAX_OUTPUT_INTERVALS = 50_000
MAX_TOTAL_SUBSTEPS = 4_000_000
MAX_RATE = 100.0
MAX_GROWTH_RATE = 10.0
SUBSTEP_RATE_TARGET = 0.2


def _validate(config):
    fields(config, ("schema_version", "fixture_notice", "dimensionless_time", "growth",
                    "scaling", "chamber", "damage"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    fields(config["dimensionless_time"], ("duration", "output_step"), "dimensionless_time")
    duration = number(config["dimensionless_time"]["duration"], "duration", 1e-6, 10_000)
    step = number(config["dimensionless_time"]["output_step"], "output_step", 1e-6, duration)
    if duration / step > MAX_OUTPUT_INTERVALS:
        raise InputError(f"At most {MAX_OUTPUT_INTERVALS} output intervals are permitted")

    fields(config["growth"], ("linear_rate", "load_exponent", "stiffness_exponent"), "growth")
    growth = {"linear_rate": number(config["growth"]["linear_rate"], "linear_rate", 0, MAX_GROWTH_RATE),
              "load_exponent": number(config["growth"]["load_exponent"], "load_exponent", 0, 10),
              "stiffness_exponent": number(config["growth"]["stiffness_exponent"],
                                           "stiffness_exponent", 0, 10)}
    fields(config["scaling"], ("load_coefficient", "stiffness_coefficient"), "scaling")
    scaling = {"load_coefficient": number(config["scaling"]["load_coefficient"],
                                           "load_coefficient", 1e-6, 1_000),
               "stiffness_coefficient": number(config["scaling"]["stiffness_coefficient"],
                                               "stiffness_coefficient", 1e-6, 1_000)}
    fields(config["chamber"], ("viscosity", "strain_limit", "safe_strain", "detection_fraction"),
           "chamber")
    chamber = {"viscosity": number(config["chamber"]["viscosity"], "viscosity", 1e-6, MAX_RATE),
               "strain_limit": number(config["chamber"]["strain_limit"], "strain_limit", 1e-6, 1_000),
               "safe_strain": number(config["chamber"]["safe_strain"], "safe_strain", 0, 1_000),
               "detection_fraction": number(config["chamber"]["detection_fraction"],
                                            "detection_fraction", 0, 1.0)}
    if chamber["safe_strain"] >= chamber["strain_limit"]:
        raise InputError("safe_strain must lie below strain_limit")
    fields(config["damage"], ("configured_rate", "witness_rate"), "damage")
    damage = {"configured_rate": number(config["damage"]["configured_rate"],
                                        "configured_rate", 0, MAX_RATE),
              "witness_rate": number(config["damage"]["witness_rate"], "witness_rate", 0, MAX_RATE)}
    if damage["configured_rate"] == damage["witness_rate"]:
        raise InputError("damage witness must use a different rate from the configured wall")
    return duration, step, growth, scaling, chamber, damage


def equilibrium_strain(growth, scaling, time):
    """Closed-form equilibrium strain of the wall at one dimensionless time."""
    size = 1.0 + growth["linear_rate"] * time
    load = scaling["load_coefficient"] * size ** growth["load_exponent"]
    stiffness = scaling["stiffness_coefficient"] * size ** growth["stiffness_exponent"]
    return load / stiffness


def analytic_failure(growth, scaling, limit):
    """Analytic size and time at which the equilibrium strain crosses the limit."""
    ratio = limit * scaling["stiffness_coefficient"] / scaling["load_coefficient"]
    exponent = growth["load_exponent"] - growth["stiffness_exponent"]
    if exponent <= 0:
        return {"failure_size": None, "failure_time": None, "never_fails": True}
    size = ratio ** (1.0 / exponent)
    if size <= 1.0:
        return {"failure_size": 1.0, "failure_time": 0.0, "never_fails": False}
    time = (size - 1.0) / growth["linear_rate"] if growth["linear_rate"] > 0 else None
    return {"failure_size": size, "failure_time": time, "never_fails": time is None}


def _stiffness(scaling, growth, time, paced):
    size = 1.0 + growth["linear_rate"] * time
    if paced:
        return scaling["stiffness_coefficient"] * size ** growth["stiffness_exponent"]
    return scaling["stiffness_coefficient"]


def _right_hand_side(time, state, growth, scaling, chamber, paced):
    """Derivatives of [strain, damage]; damage never enters the strain equation."""
    size = 1.0 + growth["linear_rate"] * time
    load = scaling["load_coefficient"] * size ** growth["load_exponent"]
    stiffness = _stiffness(scaling, growth, time, paced)
    strain, _damage = state
    d_strain = (load - stiffness * strain) / chamber["viscosity"]
    return [d_strain, 0.0]


def _rk4_step(time, state, substep, growth, scaling, chamber, paced):
    first = _right_hand_side(time, state, growth, scaling, chamber, paced)
    second = _right_hand_side(time + 0.5 * substep,
                              [value + 0.5 * substep * rate for value, rate in zip(state, first)],
                              growth, scaling, chamber, paced)
    third = _right_hand_side(time + 0.5 * substep,
                             [value + 0.5 * substep * rate for value, rate in zip(state, second)],
                             growth, scaling, chamber, paced)
    fourth = _right_hand_side(time + substep,
                             [value + substep * rate for value, rate in zip(state, third)],
                             growth, scaling, chamber, paced)
    return [value + substep * (a + 2 * b + 2 * c + d) / 6.0
            for value, a, b, c, d in zip(state, first, second, third, fourth)]


def _integrate(duration, step, growth, scaling, chamber, paced, damage_rate):
    """RK4 strain integration; damage accrues from the output series."""
    rate_scale = (scaling["stiffness_coefficient"]
                  * (1.0 + growth["linear_rate"] * duration) ** growth["stiffness_exponent"]
                  / chamber["viscosity"])
    substeps = max(1, math.ceil(step * rate_scale / SUBSTEP_RATE_TARGET))
    intervals = int(duration / step)
    if intervals * substeps > MAX_TOTAL_SUBSTEPS:
        raise InputError(f"Integration exceeds the {MAX_TOTAL_SUBSTEPS}-substep budget")
    initial = equilibrium_strain(growth, scaling, 0.0)
    state = [initial, 0.0]
    rows = []
    for index in range(intervals + 1):
        time = duration if index == intervals else index * step
        load = scaling["load_coefficient"] * (1.0 + growth["linear_rate"] * time) ** growth["load_exponent"]
        stiffness = _stiffness(scaling, growth, time, paced)
        strain = state[0]
        rows.append({"dimensionless_time": time, "size": 1.0 + growth["linear_rate"] * time,
                     "load": load, "stiffness": stiffness,
                     "equilibrium_strain": load / stiffness,
                     "strain": strain, "safety_margin": chamber["strain_limit"] - strain,
                     "cumulative_damage": None})
        if index == intervals:
            break
        substep = step / substeps
        for _ in range(substeps):
            state = _rk4_step(time, state, substep, growth, scaling, chamber, paced)
    cumulative = 0.0
    for previous, current in zip(rows, rows[1:]):
        span = current["dimensionless_time"] - previous["dimensionless_time"]
        cumulative += damage_rate * 0.5 * (
            max(0.0, previous["strain"] - chamber["safe_strain"])
            + max(0.0, current["strain"] - chamber["safe_strain"])) * span
        current["cumulative_damage"] = cumulative
    rows[0]["cumulative_damage"] = 0.0
    return rows


def _first_crossing(rows, column, threshold):
    for row in rows:
        if row[column] > threshold:
            return row["dimensionless_time"]
    return None


def _balance_residual(rows, chamber):
    """Max trapezoid residual of the viscoelastic strain equation."""
    residual = 0.0
    for previous, current in zip(rows, rows[1:]):
        span = current["dimensionless_time"] - previous["dimensionless_time"]
        expected = previous["strain"] + span / chamber["viscosity"] * 0.5 * (
            previous["load"] - previous["stiffness"] * previous["strain"]
            + current["load"] - current["stiffness"] * current["strain"])
        residual = max(residual, abs(expected - current["strain"]))
    return residual


def growth_mechanics(config_path: Path, output: Path) -> dict:
    """Publish the growth-accommodation fixture; nothing is fitted."""
    config, raw = read_json(config_path)
    duration, step, growth, scaling, chamber, damage = _validate(config)
    worlds = {
        "paced": _integrate(duration, step, growth, scaling, chamber, True,
                            damage["configured_rate"]),
        "damage_witness": _integrate(duration, step, growth, scaling, chamber, True,
                                    damage["witness_rate"]),
        "fixed_stiffness": _integrate(duration, step, growth, scaling, chamber, False,
                                      damage["configured_rate"]),
    }

    failure = analytic_failure(growth, scaling, chamber["strain_limit"])
    detection_threshold = chamber["detection_fraction"] * chamber["strain_limit"]
    detection = _first_crossing(worlds["paced"], "strain", detection_threshold)
    failure_time = _first_crossing(worlds["paced"], "strain", chamber["strain_limit"])
    fixed_failure = _first_crossing(worlds["fixed_stiffness"], "strain", chamber["strain_limit"])
    damage_onset = _first_crossing(worlds["paced"], "strain", chamber["safe_strain"])
    damage_at_detection = next((row["cumulative_damage"] for row in worlds["paced"]
                                if detection is not None
                                and row["dimensionless_time"] == detection), None)

    witness_strain_difference = max(
        abs(left["strain"] - right["strain"])
        for left, right in zip(worlds["paced"], worlds["damage_witness"]))
    final_damage = {name: rows[-1]["cumulative_damage"] for name, rows in worlds.items()}
    accommodation_difference = max(
        abs(left["strain"] - right["strain"])
        for left, right in zip(worlds["paced"], worlds["fixed_stiffness"]))

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_growth_mechanics_theory",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "n_samples": len(worlds["paced"]),
        "analytic_failure": failure,
        "timeline": {"damage_onset_time": damage_onset,
                     "detection_threshold": detection_threshold,
                     "paced_detection_time": detection,
                     "paced_failure_time": failure_time,
                     "fixed_stiffness_failure_time": fixed_failure,
                     "cumulative_damage_at_detection": damage_at_detection,
                     "final_safety_margin": worlds["paced"][-1]["safety_margin"]},
        "damage_witness": {
            "max_abs_strain_difference": witness_strain_difference,
            "strain_series_identical": witness_strain_difference == 0.0,
            "final_damage_configured": final_damage["paced"],
            "final_damage_witness": final_damage["damage_witness"],
            "relative_damage_difference": (
                abs(final_damage["paced"] - final_damage["damage_witness"]) / final_damage["paced"]
                if final_damage["paced"] > 0 else None)},
        "accommodation_comparison": {
            "max_abs_strain_difference": accommodation_difference,
            "separated_in_observable_channel": accommodation_difference > 0.0,
            "final_strain_paced": worlds["paced"][-1]["strain"],
            "final_strain_fixed": worlds["fixed_stiffness"][-1]["strain"]},
        "balance": {"max_abs_trapezoid_residual": _balance_residual(worlds["paced"], chamber)},
        "interpretation": {
            "square_cube": "When the load exponent exceeds the stiffness exponent, equilibrium strain grows with size and crosses the strain limit at an analytic time; growth-paced accommodation is a measured property of the wall, not an assumption.",
            "observable": "Unlike internal delivery, the mechanical channel is observable: a growth-paced and a fixed-stiffness wall under the same load separate in measured strain immediately and fail at different times.",
            "damage": "Cumulative damage accrues from strain beyond the safe threshold and never enters the strain equation: two walls with different damage rates share one strain series exactly, so hidden wear is invisible in strain readings by construction."},
        "limits": [
            "All loads, stiffnesses, strains and times are invented dimensionless software fixture values.",
            "The Kelvin-Voigt wall is an abstract viscoelastic element, not a validated uterine or chamber material model.",
            "The power-law load and stiffness scaling are a geometric software world, not a measured allometric law.",
            "Cumulative damage is an invented linear accounting of strain excess; it is not a fatigue, injury or rupture prediction.",
            "The witness demonstrates a structural property of this model only; it is not a sensor or inspection recommendation.",
            "No confidence interval, health score, physical device parameter, gestational claim or gate completion is computed."]}
    def show(value):
        return "not reached" if value is None else format(value, ".6g")

    lines = ["# Dimensionless growth-accommodation mechanics fixture", "", NOTICE, "",
             "A Kelvin-Voigt chamber wall carries a load growing with unit size against stiffness scaling sub-linearly.",
             "Equilibrium strain grows with size and crosses the strain limit at an analytic time.", "",
             "## Failure analysis (growth-paced wall)", "",
             f"- Analytic failure size: {show(failure['failure_size'])}; time: {show(failure['failure_time'])}",
             f"- Damage onset (strain > safe {chamber['safe_strain']}): {show(damage_onset)}",
             f"- Detection time (strain > {show(detection_threshold)}): {show(detection)}",
             f"- Strain-limit crossing time: {show(failure_time)}",
             f"- Cumulative damage at detection: {show(damage_at_detection)}",
             f"- Fixed-stiffness failure time: {show(fixed_failure)}", "",
             "## Damage witness", "",
             f"- Strain series identical: {report['damage_witness']['strain_series_identical']}",
             f"- Final damage configured: {show(final_damage['paced'])}; witness: {show(final_damage['damage_witness'])}",
             f"- Relative damage difference: {show(report['damage_witness']['relative_damage_difference'])}",
             "", report["interpretation"]["observable"], "",
             report["interpretation"]["damage"], "",
             "## Limits", ""]
    lines.extend(f"- {item}" for item in report["limits"])
    files = {"input_config.json": raw}
    for name, rows in worlds.items():
        files[f"trajectory_{name}.csv"] = csv_bytes(list(rows[0]), rows)
    files["growth_mechanics_report.json"] = json_bytes(report)
    files["REPORT.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    return publish_bundle(output, kind="dimensionless_growth_mechanics_theory", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "structural_counterexample": True})
