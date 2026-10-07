"""Observability diagnostics for the abstract exchange fixture.

The fitted quantities are invented software-fixture rates.  This module does
not fit biological measurements or assign biological units.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .artifacts import (InputError, csv_bytes, json_bytes, publish_bundle,
                        read_json, sha256)
from .exchange import NOTICE, run_fixture, validate_config
from .state_estimation import noise_aware_state_fit, prospective_forecast

MAX_TRAJECTORY_BYTES = 12_000_000
MAX_TRAJECTORY_ROWS = 50_402
MAX_READING_MAGNITUDE = 1_000_000_000_000.0
RANK_TOLERANCE = 1e-12
REQUIRED_COLUMNS = {"dimensionless_time", "power_source", "sensor_sampled", "sensor_reading"}


def _read_trajectory(path: Path, config: dict, duration: float, step: float):
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_TRAJECTORY_BYTES + 1)
        if len(raw) > MAX_TRAJECTORY_BYTES:
            raise InputError("Trajectory CSV exceeds the 12 MB limit")
    except OSError:
        raise InputError("Trajectory CSV could not be read") from None
    try:
        reader = csv.DictReader(raw.decode("utf-8").splitlines())
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)) or REQUIRED_COLUMNS - set(columns):
            raise InputError("Trajectory CSV is missing required or has duplicate columns")
        scheduled = {0.0, duration}
        scheduled.update(min(duration, index * step)
                         for index in range(1, math.ceil(duration / step)))
        rows = []
        previous_time = -1.0
        for index, row in enumerate(reader):
            if index >= MAX_TRAJECTORY_ROWS or None in row:
                raise InputError("Trajectory CSV has too many rows or malformed columns")
            time = float(row["dimensionless_time"])
            if not math.isfinite(time) or not 0 <= time <= duration or time <= previous_time:
                raise InputError("Trajectory times must be finite, ordered and within the source configuration")
            power = row["power_source"]
            if power not in {"wall", "backup", "none"}:
                raise InputError("Trajectory has an unknown power source")
            sampled_text = row["sensor_sampled"]
            if sampled_text not in {"True", "False"}:
                raise InputError("sensor_sampled must be True or False")
            sampled = sampled_text == "True"
            if sampled != (time in scheduled):
                raise InputError("Scheduled readings must match the source fixture cadence")
            reading_text = row["sensor_reading"]
            reading = None if reading_text == "" else float(reading_text)
            if not sampled and reading is not None:
                raise InputError("Unscheduled rows cannot contain sensor readings")
            if reading is not None and (not math.isfinite(reading)
                                        or abs(reading) > MAX_READING_MAGNITUDE):
                raise InputError("Sensor readings must be finite and within the software-fixture range")
            rows.append({"time": time, "power": power,
                         "sampled": sampled, "reading": reading})
            previous_time = time
    except InputError:
        raise
    except (UnicodeError, csv.Error, TypeError, ValueError, OverflowError):
        raise InputError("Trajectory CSV must be valid bounded UTF-8 numeric data") from None
    if not rows or rows[0]["time"] != 0 or rows[-1]["time"] != duration:
        raise InputError("Trajectory must span the full source fixture duration")
    if [row["time"] for row in rows if row["sampled"]] != sorted(scheduled):
        raise InputError("Trajectory is missing one or more scheduled sensor timestamps")
    expected_rows, _summary = run_fixture(config)
    expected_schedule = [(row["dimensionless_time"], row["power_source"], row["sensor_sampled"])
                         for row in expected_rows]
    observed_schedule = [(row["time"], row["power"], row["sampled"]) for row in rows]
    if observed_schedule != expected_schedule:
        raise InputError("Trajectory event times or modeled power labels do not match the source configuration")
    return raw, rows


def _verify_simulation_receipt(config_raw: bytes, trajectory_path: Path, trajectory_raw: bytes):
    receipt_path = trajectory_path.parent / "receipt.json"
    try:
        receipt, receipt_raw = read_json(receipt_path)
    except (OSError, InputError):
        raise InputError("Trajectory must be accompanied by its valid simulate receipt") from None
    output = receipt.get("outputs", {}).get("trajectory.csv")
    if (receipt.get("schema_version") != 1
            or receipt.get("bundle_kind") != "synthetic_exchange_software_fixture"
            or receipt.get("input_sha256") != sha256(config_raw)
            or not isinstance(output, dict)
            or output.get("sha256") != sha256(trajectory_raw)
            or output.get("size_bytes") != len(trajectory_raw)):
        raise InputError("Simulation receipt does not bind this configuration and trajectory")
    return {"receipt_path": "receipt.json", "receipt_sha256": sha256(receipt_raw),
            "receipt_raw": receipt_raw,
            "input_config_sha256": sha256(config_raw),
            "trajectory_sha256": sha256(trajectory_raw)}


def _intervals(rows):
    """Integrate known synthetic power state between usable scheduled readings."""
    measurements = [index for index, row in enumerate(rows)
                    if row["sampled"] and row["reading"] is not None]
    intervals = []
    for left_index, right_index in zip(measurements, measurements[1:]):
        left, right = rows[left_index], rows[right_index]
        delta = right["time"] - left["time"]
        if delta <= 0:
            continue
        powered = math.fsum(
            rows[index + 1]["time"] - rows[index]["time"]
            for index in range(left_index, right_index)
            if rows[index]["power"] != "none")
        intervals.append({
            "start": left["time"], "end": right["time"],
            "duration": delta,
            "powered_exposure": powered,
            # Integral of the first-order conversion term, approximated using
            # the observed interval mean and labeled as such in every report.
            "conversion_exposure": -0.5 * (left["reading"] + right["reading"]) * delta,
            "observed_change": right["reading"] - left["reading"],
        })
    return intervals


def _fit(intervals):
    """Fit input and conversion rates by two-column least squares."""
    if len(intervals) < 2:
        return {"estimable": False, "reason": "Fewer than two usable intervals"}
    xs = [(item["powered_exposure"], item["conversion_exposure"]) for item in intervals]
    ys = [item["observed_change"] for item in intervals]
    norm0 = math.sqrt(math.fsum(row[0] * row[0] for row in xs))
    norm1 = math.sqrt(math.fsum(row[1] * row[1] for row in xs))
    if norm0 == 0 or norm1 == 0:
        return {"estimable": False, "reason": "At least one model term has no variation"}
    correlation = math.fsum((row[0] / norm0) * (row[1] / norm1) for row in xs)
    correlation = max(-1.0, min(1.0, correlation))
    eig_large = 1.0 + abs(correlation)
    eig_small = 1.0 - abs(correlation)
    singular_large = math.sqrt(eig_large)
    singular_small = math.sqrt(max(0.0, eig_small))
    condition = (singular_large / singular_small
                 if singular_small > 0 else None)
    if eig_small <= RANK_TOLERANCE * eig_large:
        return {"estimable": False, "rank": 1,
                "design_column_correlation": correlation,
                "normalized_design_condition_number": condition,
                "reason": "The observed input and conversion effects are collinear"}
    sxx = math.fsum(row[0] * row[0] for row in xs)
    szz = math.fsum(row[1] * row[1] for row in xs)
    sxz = math.fsum(row[0] * row[1] for row in xs)
    sxy = math.fsum(row[0] * y for row, y in zip(xs, ys))
    szy = math.fsum(row[1] * y for row, y in zip(xs, ys))
    determinant = sxx * szz - sxz * sxz
    if not math.isfinite(determinant) or determinant <= 0:
        return {"estimable": False, "rank": 1,
                "design_column_correlation": correlation,
                "normalized_design_condition_number": condition,
                "reason": "The normal equations are numerically singular"}
    input_estimate = (sxy * szz - szy * sxz) / determinant
    conversion_estimate = (szy * sxx - sxy * sxz) / determinant
    residuals = [y - (input_estimate * row[0] + conversion_estimate * row[1])
                 for row, y in zip(xs, ys)]
    rmse = math.sqrt(math.fsum(value * value for value in residuals) / len(residuals))
    if not all(math.isfinite(value) for value in (input_estimate, conversion_estimate, rmse)):
        raise InputError("Rate estimates exceed the supported floating-point range")
    return {"estimable": True, "rank": 2,
            "parameter_estimates": {"powered_input": input_estimate,
                                    "conversion": conversion_estimate},
            "design_column_correlation": correlation,
            "normalized_design_condition_number": condition,
            "fixture_scale_rmse": rmse,
            "n_intervals": len(intervals)}


def analyze(config_path: Path, trajectory_path: Path, output: Path) -> dict:
    config, config_raw = read_json(config_path)
    parsed = validate_config(config)
    trajectory_raw, rows = _read_trajectory(trajectory_path, config, parsed["duration"], parsed["step"])
    binding = _verify_simulation_receipt(config_raw, trajectory_path, trajectory_raw)
    intervals = _intervals(rows)
    split_time = parsed["duration"] * 0.7
    early = [item for item in intervals if item["end"] <= split_time]
    fit = _fit(intervals)
    early_fit = _fit(early)
    balance_residual_diagnostic = None
    if early_fit.get("estimable"):
        estimates = early_fit["parameter_estimates"]
        errors = [item["observed_change"]
                  - (estimates["powered_input"] * item["powered_exposure"]
                     + estimates["conversion"] * item["conversion_exposure"])
                  for item in intervals if item["start"] >= split_time]
        if errors:
            balance_residual_diagnostic = {
                "split_dimensionless_time": split_time,
                "n_intervals": len(errors),
                "fixture_scale_rmse": math.sqrt(math.fsum(error * error for error in errors) / len(errors)),
                "label": "Same-run balance-residual consistency diagnostic; its interval predictors include the observed endpoint readings."}
    full_state_fit = noise_aware_state_fit(rows, parsed["faults"], parsed["monitor"]["noise_sd"])
    prospective = prospective_forecast(rows, parsed["faults"], split_time,
                                        parsed["monitor"]["noise_sd"])
    report = {
        "schema_version": 2,
        "fixture_notice": NOTICE,
        "result_kind": "synthetic_exchange_observability_diagnostic",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "method": "Two complementary analyses: a dimensionless integral-balance residual diagnostic, and a nonlinear state-space fit under independent Gaussian sensor noise followed by a forward temporal forecast.",
        "observation_contract": "Only scheduled sensor readings, the receipt-bound fixture configuration, and its modeled power-source event schedule are used; hidden substrate truth and cumulative fluxes are ignored by all fits.",
        "n_rows": len(rows),
        "n_scheduled_readings": sum(row["sampled"] for row in rows),
        "n_usable_readings": sum(row["sampled"] and row["reading"] is not None for row in rows),
        "n_usable_intervals": len(intervals),
        "full_series_fit": fit,
        "early_series_fit": early_fit,
        "balance_residual_diagnostic": balance_residual_diagnostic,
        "noise_aware_state_model": {
            "equation": "dS/dt = powered_input × powered_state(t) - conversion × S; sensor reading = S + independent Gaussian error",
            "full_series_fit": full_state_fit,
            "prospective_forecast": prospective,
            "assumptions": [
                "The synthetic power schedule is known and held fixed.",
                "Initial substrate, powered input, and nonnegative conversion are constant model parameters.",
                "Sensor noise is independent Gaussian error with the standard deviation declared in the fixture configuration.",
                "Readings during configured sensor-bias intervals are excluded; unavailable readings remain missing.",
                "The approximate 95% forecast interval uses a local parameter covariance and the declared sensor noise.",
            ],
        },
        "simulation_binding": {key: value for key, value in binding.items() if key != "receipt_raw"},
        "model": {"observed_stock": "substrate", "unknown_fixture_rates": ["powered_input", "conversion"],
                  "assumed_known_schedule": "wall/backup/none labels from the synthetic trajectory"},
        "limits": [
            "All values and rates are invented dimensionless software quantities.",
            "The integral-balance regression uses readings in both the response and trapezoidal predictor, so its residual fit is not a future forecast.",
            "The state model assumes a single well-mixed stock and independently distributed Gaussian sensor error; its uncertainty is a local approximation.",
            "A low condition number, small forecast error, or nominal interval coverage does not validate the model or imply biological identifiability.",
            "The prospective forecast is a temporal split within one generated trajectory, not independent experimental validation.",
            "The modeled power schedule is assumed known; this report does not infer actual device state.",
            "No embryo, animal, patient or device data are analyzed.",
        ],
    }
    interval_rows = [{"start": item["start"], "end": item["end"],
                      "duration": item["duration"],
                      "powered_exposure": item["powered_exposure"],
                      "conversion_exposure": item["conversion_exposure"],
                      "observed_substrate_change": item["observed_change"]}
                     for item in intervals]
    lines = ["# Dimensionless exchange observability diagnostic", "", NOTICE, "",
             "The trajectory and source configuration are checked against the simulation receipt; scheduled timestamps and power-state event labels must match the source configuration.",
             "", "## Full-series fit", "", "```json",
             json_bytes(fit).decode().rstrip(), "```", "", "## Early-series fit", "", "```json",
             json_bytes(early_fit).decode().rstrip(), "```", "", "## Later-interval holdout", "",
             "### Noise-aware state fit", "", "```json", json_bytes(full_state_fit).decode().rstrip(), "```",
             "", "### Prospective temporal forecast", "", "```json", json_bytes(prospective).decode().rstrip(), "```",
             "", "### Same-run balance residual diagnostic", "",
             json_bytes(balance_residual_diagnostic).decode().rstrip() if balance_residual_diagnostic else "The early window did not identify both balance-regression fixture parameters; no residual diagnostic was computed.",
             "", "## Limits", ""]
    lines.extend(f"- {item}" for item in report["limits"])
    manifest = {"analysis": "dimensionless_exchange_observability_v2",
                "config_sha256": sha256(config_raw),
                "trajectory_sha256": sha256(trajectory_raw),
                "simulation_receipt_sha256": binding["receipt_sha256"]}
    source_raw = json_bytes(manifest)
    files = {"source_manifest.json": source_raw,
             "source_config.json": config_raw,
             "source_trajectory.csv": trajectory_raw,
             # The parent receipt travels with the bundle: a hash alone cannot
             # resolve ancestry once the source simulate directory is gone.
             "source_receipt.json": binding["receipt_raw"],
             "observability_report.json": json_bytes(report),
             "interval_design.csv": csv_bytes(list(interval_rows[0]) if interval_rows else
                                                ["start", "end", "duration", "powered_exposure",
                                                 "conversion_exposure", "observed_substrate_change"], interval_rows),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    return publish_bundle(output, kind="synthetic_exchange_observability_diagnostic",
                          input_raw=source_raw, files=files,
                          metadata={"biological_measurements": False,
                                    "physiologically_calibrated": False,
                                    "human_gestation_prediction": False,
                                    "config_sha256": manifest["config_sha256"],
                                    "trajectory_sha256": manifest["trajectory_sha256"],
                                    "parent_receipt_sha256": binding["receipt_sha256"],
                                    "parent_receipt_file": "source_receipt.json"})
