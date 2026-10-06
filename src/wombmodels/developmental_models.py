"""Stage-labeled, dimensionless transport and mechanics theory fixtures."""
from __future__ import annotations

import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json, sha256
from .exchange import NOTICE

STAGE_TRACKS = {
    "preimplantation", "implantation_and_placentation", "postimplantation_embryonic",
    "partial_fetal_support", "transition_to_neonatal", "developmental_outcomes",
}
MAX_DURATION = 10_000.0
MAX_RATE = 1_000.0
MAX_STEPS = 200_000
MAX_MAGNITUDE = 1_000_000.0


def _number(value, label, low=0.0, high=MAX_MAGNITUDE):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be a finite dimensionless number")
    try:
        result = float(value)
    except OverflowError:
        raise InputError(f"{label} must be a finite dimensionless number") from None
    if not math.isfinite(result) or not low <= result <= high:
        raise InputError(f"{label} must be finite and lie in [{low}, {high}]")
    return result


def _context(config):
    value = config.get("context")
    if not isinstance(value, dict) or set(value) != {"stage_track", "species", "interval_label"}:
        raise InputError("context must label one stage track, species and source interval")
    if not isinstance(value["stage_track"], str) or value["stage_track"] not in STAGE_TRACKS:
        raise InputError("context stage_track must name exactly one developmental track")
    if not isinstance(value["species"], str) or value["species"] not in {"mouse", "ovine", "human", "unspecified"}:
        raise InputError("context species must be mouse, ovine, human or unspecified")
    if not isinstance(value["interval_label"], str) or len(value["interval_label"]) > 80:
        raise InputError("context interval_label must be text of at most 80 characters")
    return {**value, "modeling_status": "theoretical_dimensionless_fixture"}


def _time_grid(value):
    if not isinstance(value, dict) or set(value) != {"duration", "step"}:
        raise InputError("dimensionless_time must contain duration and step")
    duration = _number(value["duration"], "duration", 1e-6, MAX_DURATION)
    step = _number(value["step"], "step", 1e-8, duration)
    steps = math.ceil(duration / step)
    if steps > MAX_STEPS:
        raise InputError(f"At most {MAX_STEPS} integration steps are permitted")
    return duration, step, steps


def _scope_report(model, config, assumptions, alternative, outputs, limits):
    return {
        "schema_version": 1,
        "fixture_notice": NOTICE,
        "result_kind": model,
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "stage_context": _context(config),
        "parameter_units": "All state, time, rate, stress and strain quantities are dimensionless software-fixture values.",
        "assumptions": assumptions,
        "alternative_model": alternative,
        "outputs": outputs,
        "limits": limits,
    }


def simulate_transport(config_path: Path, output: Path) -> dict:
    config, raw = read_json(config_path)
    if set(config) != {"schema_version", "fixture_notice", "context", "dimensionless_time",
                       "initial", "rates", "boundary_concentration"}:
        raise InputError("transport config has unknown or missing fields")
    if config["schema_version"] != 1 or config["fixture_notice"] != NOTICE:
        raise InputError("transport config must retain schema version 1 and the fixture declaration")
    context = _context(config)
    duration, step, steps = _time_grid(config["dimensionless_time"])
    initial = config["initial"]
    rates = config["rates"]
    if not isinstance(initial, dict) or set(initial) != {"interface", "core"}:
        raise InputError("initial must contain interface and core stocks")
    if not isinstance(rates, dict) or set(rates) != {"boundary_exchange", "intercompartment_transport", "loss"}:
        raise InputError("rates must contain boundary exchange, intercompartment transport and loss")
    c1, c2 = (_number(initial["interface"], "initial interface"),
              _number(initial["core"], "initial core"))
    exchange = _number(rates["boundary_exchange"], "boundary_exchange", 0, MAX_RATE)
    transport = _number(rates["intercompartment_transport"], "intercompartment_transport", 0, MAX_RATE)
    loss = _number(rates["loss"], "loss", 0, MAX_RATE)
    boundary = _number(config["boundary_concentration"], "boundary_concentration")
    if step * (exchange + transport + loss) > 1.0:
        raise InputError("Explicit integration step exceeds the positivity bound for this fixture")

    t = 0.0
    cumulative_in = cumulative_loss = 0.0
    rows = []
    mixed = (c1 + c2) / 2.0
    mixed_rows = []
    for index in range(steps + 1):
        source_flux = exchange * (boundary - c1)
        internal_flux = transport * (c1 - c2)
        loss_flux = loss * (c1 + c2)
        residual = c1 + c2 - initial["interface"] - initial["core"] - cumulative_in + cumulative_loss
        rows.append({"dimensionless_time": t, "interface_state": c1, "core_state": c2,
                     "interface_core_gradient": c1 - c2, "boundary_exchange_flux": source_flux,
                     "intercompartment_flux": internal_flux, "loss_flux": loss_flux,
                     "cumulative_net_boundary_exchange": cumulative_in,
                     "cumulative_loss": cumulative_loss,
                     "accounting_residual": residual})
        mixed_rows.append({"dimensionless_time": t, "single_compartment_state": mixed})
        if index == steps:
            break
        delta = min(step, duration - t)
        if delta <= 0:
            break
        next_c1 = c1 + delta * (source_flux - internal_flux - loss * c1)
        next_c2 = c2 + delta * (internal_flux - loss * c2)
        next_mixed = mixed + delta * ((exchange / 2.0) * (boundary - mixed) - loss * mixed)
        if min(next_c1, next_c2, next_mixed) < -1e-10 or not all(
                math.isfinite(value) for value in (next_c1, next_c2, next_mixed)):
            raise InputError("Transport fixture left its finite nonnegative state range")
        cumulative_in += delta * source_flux
        cumulative_loss += delta * loss_flux
        c1, c2, mixed = max(0.0, next_c1), max(0.0, next_c2), max(0.0, next_mixed)
        t = duration if index == steps - 1 else t + delta

    final = rows[-1]
    alternative = {
        "name": "capacity-matched single well-mixed reference compartment",
        "equation": "dC/dt = (boundary_exchange / 2) × (boundary − C) − loss × C",
        "capacity_relative_to_one_compartment": 2.0,
        "initial_state": (initial["interface"] + initial["core"]) / 2.0,
        "final_state": mixed_rows[-1]["single_compartment_state"],
        "final_core_difference_from_two_compartment_model": mixed_rows[-1]["single_compartment_state"] - final["core_state"],
        "comparison_scope": "Deterministic sensitivity contrast only; no observed-data likelihood or model selection is performed.",
    }
    report = _scope_report(
        "dimensionless_two_compartment_transport",
        config,
        ["The interface and core have equal abstract capacity; the well-mixed reference has their combined capacity and the same single boundary-exchange pathway.",
         "Boundary exchange and intercompartment transfer are linear and time-invariant.",
         "The boundary concentration is a known constant; a first-order loss acts on both compartments.",
         "Forward Euler integration preserves a discrete accounting identity under the configured step bound."],
        alternative,
        {"final_interface_state": final["interface_state"], "final_core_state": final["core_state"],
         "final_gradient": final["interface_core_gradient"], "final_boundary_exchange_flux": final["boundary_exchange_flux"],
         "maximum_absolute_accounting_residual": max(abs(row["accounting_residual"]) for row in rows),
         "n_timepoints": len(rows)},
        ["This stage label preserves scope metadata; it does not convert the generic equations into a model of implantation, placentation or a specific organism.",
         "No biological rates, geometry, tissue properties, measured concentrations or physiological units are supplied.",
         "State gradients and fluxes are candidate future observables, not demonstrations of delivery, growth or developmental function.",
         "Identifiability requires separately measured boundary exposure and at least one independent spatial state; the current fixture cannot establish that those quantities are experimentally observable.",
         "Alternative-model differences are not evidence that either model is biologically correct."])
    files = {"input_config.json": raw,
             "transport_report.json": json_bytes(report),
             "transport_trajectory.csv": csv_bytes(list(rows[0]), rows),
             "well_mixed_reference.csv": csv_bytes(list(mixed_rows[0]), mixed_rows),
             "REPORT.md": _report_markdown("Dimensionless two-compartment transport fixture", report)}
    return publish_bundle(output, kind="dimensionless_transport_theory", input_raw=raw, files=files,
                          metadata={"biological_measurements": False, "physiologically_calibrated": False,
                                    "human_gestation_prediction": False, "input_sha256": sha256(raw)})


def simulate_mechanics(config_path: Path, output: Path) -> dict:
    config, raw = read_json(config_path)
    if set(config) != {"schema_version", "fixture_notice", "context", "dimensionless_time",
                       "initial_strain", "rates", "stress_schedule"}:
        raise InputError("mechanics config has unknown or missing fields")
    if config["schema_version"] != 1 or config["fixture_notice"] != NOTICE:
        raise InputError("mechanics config must retain schema version 1 and the fixture declaration")
    _context(config)
    duration, step, steps = _time_grid(config["dimensionless_time"])
    initial = _number(config["initial_strain"], "initial_strain")
    rates = config["rates"]
    if not isinstance(rates, dict) or set(rates) != {"elasticity", "viscosity"}:
        raise InputError("rates must contain elasticity and viscosity")
    elasticity = _number(rates["elasticity"], "elasticity", 0, MAX_RATE)
    viscosity = _number(rates["viscosity"], "viscosity", 1e-12, MAX_RATE)
    if elasticity == 0 and viscosity == 0:
        raise InputError("viscosity must remain positive")
    schedule = config["stress_schedule"]
    if not isinstance(schedule, list) or len(schedule) > 100:
        raise InputError("stress_schedule must contain at most 100 bounded intervals")
    parsed = []
    previous_end = 0.0
    for event in schedule:
        if not isinstance(event, dict) or set(event) != {"start", "end", "stress"}:
            raise InputError("each stress interval must contain exactly start, end and stress")
        start = _number(event["start"], "stress start", 0, duration)
        end = _number(event["end"], "stress end", 0, duration)
        stress = _number(event["stress"], "stress")
        if start < previous_end or end <= start:
            raise InputError("stress intervals must be ordered, positive and nonoverlapping")
        parsed.append({"start": start, "end": end, "stress": stress})
        previous_end = end

    sample_times = {min(duration, index * step) for index in range(1, steps + 1)} | {0.0, duration}
    sample_times.update(edge for event in parsed for edge in (event["start"], event["end"]))
    times = sorted(sample_times)
    strain = initial
    rows = []
    elastic_rows = []
    for index, time in enumerate(times):
        stress = next((event["stress"] for event in parsed if event["start"] <= time < event["end"]), 0.0)
        rows.append({"dimensionless_time": time, "applied_stress": stress, "strain": strain,
                     "elastic_equilibrium_strain": stress / elasticity if elasticity > 0 else None})
        elastic_rows.append({"dimensionless_time": time,
                             "instantaneous_elastic_reference_strain": stress / elasticity if elasticity > 0 else None})
        if index == len(times) - 1:
            break
        next_time = times[index + 1]
        delta = next_time - time
        if elasticity == 0:
            strain += stress * delta / viscosity
        else:
            relaxation_rate = elasticity / viscosity
            attenuation = math.exp(-relaxation_rate * delta)
            strain = strain * attenuation + (stress / elasticity) * (-math.expm1(-relaxation_rate * delta))
        if not math.isfinite(strain) or abs(strain) > MAX_MAGNITUDE:
            raise InputError("Mechanical fixture exceeds the supported state range")

    relaxation_time = viscosity / elasticity if elasticity > 0 else None
    elastic_differences = [row["strain"] - reference["instantaneous_elastic_reference_strain"]
                           for row, reference in zip(rows, elastic_rows)
                           if reference["instantaneous_elastic_reference_strain"] is not None]
    report = _scope_report(
        "dimensionless_kelvin_voigt_mechanics",
        config,
        ["The material is a homogeneous, linear Kelvin–Voigt element with constant dimensionless elasticity and viscosity.",
         "Applied stress is piecewise constant and dimensionless; no geometry or boundary-value problem is represented.",
         "The exact constant-load state transition is used between scheduled samples and load changes."],
        {"name": "instantaneous linear-elastic reference", "equation": "strain = stress / elasticity",
         "final_state": elastic_rows[-1]["instantaneous_elastic_reference_strain"],
         "trajectory_rmse_from_kelvin_voigt": (math.sqrt(math.fsum(value * value for value in elastic_differences)
                                                           / len(elastic_differences)) if elastic_differences else None),
         "comparison_scope": "The elastic reference omits relaxation and is a theoretical contrast, not a fitted biological alternative."},
        {"final_strain": rows[-1]["strain"], "peak_strain": max(row["strain"] for row in rows),
         "dimensionless_relaxation_time": relaxation_time, "n_timepoints": len(rows)},
        ["This stage label preserves scope metadata; it does not convert the generic equations into a model of an embryo, uterus, placenta or tissue construct.",
         "No material recipe, geometry, physical stress, strain target or biological parameter is encoded.",
         "Strain response alone is not a measurement of developmental progression or a favorable outcome.",
         "Identification of elasticity and viscosity would require independent load and strain traces with calibrated measurement uncertainty; the synthetic curve does not establish that identifiability.",
         "The instantaneous elastic reference is an alternative equation for comparison, not a claim that one material law is correct."])
    files = {"input_config.json": raw,
             "mechanics_report.json": json_bytes(report),
             "mechanics_trajectory.csv": csv_bytes(list(rows[0]), rows),
             "elastic_reference.csv": csv_bytes(list(elastic_rows[0]), elastic_rows),
             "REPORT.md": _report_markdown("Dimensionless Kelvin–Voigt mechanics fixture", report)}
    return publish_bundle(output, kind="dimensionless_mechanics_theory", input_raw=raw, files=files,
                          metadata={"biological_measurements": False, "physiologically_calibrated": False,
                                    "human_gestation_prediction": False, "input_sha256": sha256(raw)})


def _report_markdown(title, report):
    return ("# " + title + "\n\n" + report["fixture_notice"] + "\n\n"
            + "The stage and species fields organize future research questions; they do not calibrate the generic equations to that biological context.\n\n"
            + "## Model and assumptions\n\n"
            + "\n".join("- " + item for item in report["assumptions"])
            + "\n\n## Outputs\n\n```json\n"
            + json_bytes(report["outputs"]).decode("utf-8").rstrip()
            + "\n```\n\n## Alternative model\n\n```json\n"
            + json_bytes(report["alternative_model"]).decode("utf-8").rstrip()
            + "\n```\n\n## Limits\n\n"
            + "\n".join("- " + item for item in report["limits"]) + "\n").encode("utf-8")
