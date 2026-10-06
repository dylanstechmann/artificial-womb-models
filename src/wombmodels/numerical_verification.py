"""Independent accuracy checks for the dimensionless transport fixture."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import shutil
import tempfile
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .developmental_models import _time_grid, simulate_mechanics, simulate_transport

REFINEMENT_FACTORS = (1.0, 0.5, 0.25, 0.125, 0.0625)
MAX_VERIFICATION_TIMEPOINTS = 100_000


def _integrated_exponential(rate: float, duration: float) -> float:
    """Return integral_0^duration exp(rate*t) dt without cancellation near zero."""
    scaled = rate * duration
    if abs(scaled) < 1e-8:
        return duration * (1.0 + scaled / 2.0 + scaled * scaled / 6.0
                           + scaled * scaled * scaled / 24.0)
    return duration * math.expm1(scaled) / scaled


def _integrated_exponential_derivative(rate: float, duration: float) -> float:
    """Return integral_0^duration t*exp(rate*t) dt stably near rate zero."""
    scaled = rate * duration
    if abs(scaled) < 1e-3:
        term = 1.0
        total = 0.0
        for order in range(11):
            if order:
                term *= scaled / order
            total += term / (order + 2)
        return duration * duration * total
    return duration * duration * ((scaled - 1.0) * math.exp(scaled) + 1.0) / (scaled * scaled)


def _exact_transport_state(interface: float, core: float, time: float, *,
                           exchange: float, transport: float, loss: float,
                           boundary: float) -> tuple[float, float]:
    """Evaluate the exact constant-coefficient two-state system by modal form.

    The Euler implementation integrates x' = A x + f. Decomposing A into
    trace(A)/2 times identity plus a traceless matrix B gives B² = s²I.
    The matrix exponential and its constant-forcing integral then reduce to
    the two real eigenvalues. This reference does not call the Euler update.
    """
    if time == 0.0:
        return interface, core
    a = -(exchange + transport + loss)
    d = -(transport + loss)
    mean_eigenvalue = (a + d) / 2.0
    diagonal = (a - d) / 2.0
    spectral_gap = math.sqrt(diagonal * diagonal + transport * transport)
    eigen_plus = mean_eigenvalue + spectral_gap
    eigen_minus = mean_eigenvalue - spectral_gap
    exp_plus = math.exp(eigen_plus * time)
    exp_minus = math.exp(eigen_minus * time)
    alpha = (exp_plus + exp_minus) / 2.0
    if spectral_gap * time < 1e-5:
        scaled_gap = spectral_gap * time
        beta = (math.exp(mean_eigenvalue * time) * time
                * (1.0 + scaled_gap * scaled_gap / 6.0
                   + scaled_gap ** 4 / 120.0))
    else:
        beta = (exp_plus - exp_minus) / (2.0 * spectral_gap)

    integral_plus = _integrated_exponential(eigen_plus, time)
    integral_minus = _integrated_exponential(eigen_minus, time)
    integral_identity = (integral_plus + integral_minus) / 2.0
    if spectral_gap * time < 1e-4:
        integral_traceless = _integrated_exponential_derivative(mean_eigenvalue, time)
    else:
        integral_traceless = (integral_plus - integral_minus) / (2.0 * spectral_gap)

    b_interface = diagonal * interface + transport * core
    b_core = transport * interface - diagonal * core
    source = exchange * boundary
    b_source_interface = diagonal * source
    b_source_core = transport * source
    exact_interface = (alpha * interface + beta * b_interface
                       + integral_identity * source + integral_traceless * b_source_interface)
    exact_core = (alpha * core + beta * b_core
                  + integral_traceless * b_source_core)
    return exact_interface, exact_core


def _read_transport_rows(path: Path) -> list[dict[str, float]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]


def _read_mechanics_rows(path: Path) -> list[dict[str, float]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return [{key: float(row[key]) for key in ("dimensionless_time", "strain")}
                for row in csv.DictReader(stream)]


def _exact_mechanics_state(initial: float, time: float, *, elasticity: float,
                           viscosity: float, schedule: list[dict[str, float]]) -> float:
    """Evaluate piecewise-load response by convolution rather than solver steps.

    For positive elasticity this sums each rectangular stress pulse convolved
    with the Kelvin–Voigt exponential kernel. At zero elasticity the equation
    reduces to linear creep, so each pulse contributes its elapsed overlap.
    """
    if elasticity == 0:
        return initial + math.fsum(
            float(event["stress"]) * max(0.0, min(time, float(event["end"]))
                                          - float(event["start"])) / viscosity
            for event in schedule)
    relaxation_rate = elasticity / viscosity
    state = initial * math.exp(-relaxation_rate * time)
    for event in schedule:
        start, end, stress = (float(event[key]) for key in ("start", "end", "stress"))
        state += (stress / elasticity) * (
            math.exp(-relaxation_rate * max(0.0, time - end))
            - math.exp(-relaxation_rate * max(0.0, time - start)))
    return state


def verify_mechanics_accuracy(config_path: Path, output: Path) -> dict:
    """Publish closed-form mechanics checks for every output and load boundary."""
    config, raw = read_json(config_path)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise InputError(f"Output already exists: {output}")
    duration, requested_step, _steps = _time_grid(config.get("dimensionless_time"))
    schedule = config.get("stress_schedule")
    if isinstance(schedule, list):
        estimated_points = math.ceil(duration / requested_step) + 1 + 2 * len(schedule)
        if estimated_points > MAX_VERIFICATION_TIMEPOINTS:
            raise InputError(f"Mechanics verification exceeds the {MAX_VERIFICATION_TIMEPOINTS}-timepoint budget; increase the requested step")

    temporary = Path(tempfile.mkdtemp(prefix="wombmodels-mechanics-verification-"))
    try:
        bundle = temporary / "mechanics"
        simulate_mechanics(config_path, bundle)
        rows = _read_mechanics_rows(bundle / "mechanics_trajectory.csv")
    finally:
        shutil.rmtree(temporary)

    rates = config["rates"]
    elasticity = float(rates["elasticity"])
    viscosity = float(rates["viscosity"])
    initial = float(config["initial_strain"])
    boundaries = {float(edge) for event in schedule for edge in (event["start"], event["end"])}
    errors = []
    pointwise_rows = []
    boundary_rows = []
    for row in rows:
        time = row["dimensionless_time"]
        reference = _exact_mechanics_state(initial, time, elasticity=elasticity,
                                           viscosity=viscosity, schedule=schedule)
        actual = row["strain"]
        error = abs(actual - reference)
        errors.append(error)
        point = {"dimensionless_time": time, "solver_strain": actual,
                 "convolution_reference_strain": reference,
                 "absolute_error": error, "is_load_boundary": time in boundaries}
        pointwise_rows.append(point)
        if time in boundaries:
            boundary_rows.append(point.copy())

    maximum_error = max(errors, default=0.0)
    rmse = math.sqrt(math.fsum(error * error for error in errors) / max(1, len(errors)))
    scaled_error = max((error / max(1.0, abs(row["strain"]), abs(point["convolution_reference_strain"]))
                        for error, row, point in zip(errors, rows, pointwise_rows)), default=0.0)
    relative_tolerance = 1e-10
    if scaled_error > relative_tolerance:
        raise InputError("Mechanics solver exceeded the closed-form verification tolerance")

    reference_name = ("piecewise rectangular-load convolution with Kelvin–Voigt exponential kernel"
                      if elasticity > 0 else "piecewise-load integral for zero-elasticity linear creep")
    report = {
        "schema_version": 1,
        "result_kind": "dimensionless_mechanics_numerical_verification",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "fixture_notice": "Dimensionless numerical verification of a software fixture; no biological calibration or prediction.",
        "reference_method": reference_name,
        "equation": "viscosity × d(strain)/dt + elasticity × strain = applied_stress",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "n_timepoints": len(rows),
        "n_load_boundaries": len(boundary_rows),
        "relative_tolerance": relative_tolerance,
        "maximum_scaled_error": scaled_error,
        "verification_passed": True,
        "errors": {"max_absolute": maximum_error, "rmse": rmse,
                   "max_boundary_absolute": max((row["absolute_error"] for row in boundary_rows), default=0.0)},
        "limits": [
            "All inputs, states and time values are dimensionless software-fixture quantities.",
            "The convolution reference checks the piecewise-constant-load solution of the stated Kelvin–Voigt equation; it does not validate that equation for a biological system.",
            "This is a closed-form consistency check, not experimental validation or a step-size convergence study.",
            "Zero-elasticity creep and positive-elasticity relaxation are separate mathematical limits; neither provides a tissue property or developmental outcome.",
        ],
    }
    report_bytes = json_bytes(report)
    boundary_columns = list(boundary_rows[0]) if boundary_rows else list(pointwise_rows[0])
    lines = ["# Dimensionless mechanics numerical verification", "", report["fixture_notice"], "",
             f"Reference: {reference_name}.", "", "All time, state and error values are dimensionless.", "",
             f"- Timepoints checked: {len(rows)}",
             f"- Load boundaries checked: {len(boundary_rows)}",
             f"- Maximum absolute error: {maximum_error:.12g}",
             f"- Root mean square error: {rmse:.12g}",
             f"- Maximum scaled error: {scaled_error:.12g} (tolerance {relative_tolerance:.1g})", "",
             "## Limits", "", *[f"- {item}" for item in report["limits"]], ""]
    files = {
        "input_config.json": raw,
        "mechanics_verification_report.json": report_bytes,
        "mechanics_pointwise_errors.csv": csv_bytes(list(pointwise_rows[0]), pointwise_rows),
        "mechanics_boundary_errors.csv": csv_bytes(boundary_columns, boundary_rows),
        "REPORT.md": "\n".join(lines).encode("utf-8"),
    }
    return publish_bundle(
        output, kind="dimensionless_mechanics_numerical_verification", input_raw=raw, files=files,
        metadata={"biological_measurements": False,
                  "physiologically_calibrated": False,
                  "human_gestation_prediction": False,
                  "n_timepoints": len(rows), "n_load_boundaries": len(boundary_rows),
                  "verification_passed": True})


def verify_transport_accuracy(config_path: Path, output: Path) -> dict:
    """Publish a bounded Euler step-halving curve against the analytic solution."""
    config, raw = read_json(config_path)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise InputError(f"Output already exists: {output}")
    duration, requested_step, _steps = _time_grid(config.get("dimensionless_time"))
    total_points = sum(math.ceil(duration / (requested_step * factor)) + 1
                       for factor in REFINEMENT_FACTORS)
    if total_points > MAX_VERIFICATION_TIMEPOINTS:
        raise InputError(f"Step-halving report exceeds the {MAX_VERIFICATION_TIMEPOINTS}-timepoint budget; increase the requested step")
    temporary = Path(tempfile.mkdtemp(prefix="wombmodels-transport-verification-"))
    try:
        baseline_bundle = temporary / "euler-level-0"
        # Reuse the production parser and its finite-state/positivity contracts
        # before reading the validated inputs for the independent reference.
        simulate_transport(config_path, baseline_bundle)
        time_settings = config["dimensionless_time"]
        duration = float(time_settings["duration"])
        requested_step = float(time_settings["step"])
        rates = config["rates"]
        exchange = float(rates["boundary_exchange"])
        transport = float(rates["intercompartment_transport"])
        loss = float(rates["loss"])
        boundary = float(config["boundary_concentration"])
        initial_interface = float(config["initial"]["interface"])
        initial_core = float(config["initial"]["core"])

        convergence_rows = []
        previous_error = None
        finest_accuracy_rows = []
        for index, factor in enumerate(REFINEMENT_FACTORS):
            if index == 0:
                euler_bundle = baseline_bundle
            else:
                refined_config = json.loads(json.dumps(config, allow_nan=False))
                refined_config["dimensionless_time"]["step"] = requested_step * factor
                refined_config_path = temporary / f"config-level-{index}.json"
                refined_config_path.write_bytes(json_bytes(refined_config))
                euler_bundle = temporary / f"euler-level-{index}"
                simulate_transport(refined_config_path, euler_bundle)

            numerical_rows = _read_transport_rows(euler_bundle / "transport_trajectory.csv")
            actual_deltas = [right["dimensionless_time"] - left["dimensionless_time"]
                             for left, right in zip(numerical_rows, numerical_rows[1:])]
            interface_errors = []
            core_errors = []
            accuracy_rows = []
            for row in numerical_rows:
                reference_interface, reference_core = _exact_transport_state(
                    initial_interface, initial_core, row["dimensionless_time"],
                    exchange=exchange, transport=transport, loss=loss, boundary=boundary)
                interface_error = abs(row["interface_state"] - reference_interface)
                core_error = abs(row["core_state"] - reference_core)
                interface_errors.append(interface_error)
                core_errors.append(core_error)
                accuracy_rows.append({
                    "dimensionless_time": row["dimensionless_time"],
                    "euler_interface_state": row["interface_state"],
                    "reference_interface_state": reference_interface,
                    "absolute_interface_error": interface_error,
                    "euler_core_state": row["core_state"],
                    "reference_core_state": reference_core,
                    "absolute_core_error": core_error,
                })
            maximum_error = max(interface_errors + core_errors, default=0.0)
            state_rmse = math.sqrt(math.fsum(value * value for value in interface_errors + core_errors)
                                   / max(1, 2 * len(numerical_rows)))
            error_ratio = (previous_error / maximum_error
                           if previous_error is not None and maximum_error > 0 else None)
            observed_order = math.log(error_ratio, 2.0) if error_ratio is not None and error_ratio > 0 else None
            convergence_rows.append({
                "refinement_factor": factor,
                "requested_step": requested_step * factor,
                "actual_max_step": max(actual_deltas, default=0.0),
                "n_intervals": len(actual_deltas),
                "n_timepoints": len(numerical_rows),
                "max_abs_interface_error": max(interface_errors, default=0.0),
                "max_abs_core_error": max(core_errors, default=0.0),
                "max_abs_state_error": maximum_error,
                "state_rmse": state_rmse,
                "error_ratio_from_previous": error_ratio,
                "observed_order": observed_order,
            })
            previous_error = maximum_error
            if index == len(REFINEMENT_FACTORS) - 1:
                finest_accuracy_rows = accuracy_rows
    finally:
        shutil.rmtree(temporary)

    report = {
        "schema_version": 1,
        "result_kind": "dimensionless_transport_numerical_verification",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "fixture_notice": "Dimensionless numerical verification of a software fixture; no biological calibration or prediction.",
        "reference_method": "Closed-form 2×2 matrix exponential and integrated constant forcing term, evaluated independently of the forward-Euler update.",
        "equations": [
            "dI/dt = exchange × (boundary − I) − transport × (I − C) − loss × I",
            "dC/dt = transport × (I − C) − loss × C",
        ],
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "n_refinement_levels": len(convergence_rows),
        "n_total_timepoints": total_points,
        "convergence": convergence_rows,
        "limits": [
            "All states, coefficients and time values are dimensionless software-fixture quantities.",
            "The analytic reference verifies the constant-coefficient equations implemented here; it does not validate the equations for a biological system.",
            "Step halving measures numerical discretization error for one supplied configuration and is not an independent experimental validation.",
            "The reported order is descriptive; very small errors or degenerate dynamics can make an order estimate unavailable.",
        ],
    }
    report_bytes = json_bytes(report)
    curve = csv_bytes(list(convergence_rows[0]), convergence_rows)
    accuracy = csv_bytes(list(finest_accuracy_rows[0]), finest_accuracy_rows)
    lines = ["# Dimensionless transport numerical verification", "", report["fixture_notice"], "",
             report["reference_method"], "", "All time steps and errors below are dimensionless.", "",
             "| Step factor | Requested step | Actual max step | Max absolute state error | State RMSE | Observed order |",
             "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for item in convergence_rows:
        order = "not reported" if item["observed_order"] is None else f"{item['observed_order']:.6g}"
        lines.append(f"| {item['refinement_factor']:.6g} | {item['requested_step']:.6g} | {item['actual_max_step']:.6g} | {item['max_abs_state_error']:.6g} | {item['state_rmse']:.6g} | {order} |")
    lines.extend(["", "## Limits", "", *[f"- {item}" for item in report["limits"]], ""])
    files = {
        "input_config.json": raw,
        "numerical_verification_report.json": report_bytes,
        "transport_convergence.csv": curve,
        "finest_step_trajectory.csv": accuracy,
        "REPORT.md": "\n".join(lines).encode("utf-8"),
    }
    return publish_bundle(
        output, kind="dimensionless_transport_numerical_verification", input_raw=raw, files=files,
        metadata={"biological_measurements": False,
                  "physiologically_calibrated": False,
                  "human_gestation_prediction": False,
                  "n_refinement_levels": len(convergence_rows),
                  "n_total_timepoints": total_points})
