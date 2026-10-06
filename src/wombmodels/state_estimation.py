"""Noise-aware state estimation and prospective forecasting for the abstract fixture."""
from __future__ import annotations

import math

from .artifacts import InputError

PROFILE_GRID_SIZE = 48
PROFILE_REFINEMENT_STEPS = 24
MAX_ESTIMATION_ROWS = 50_402
Z_95 = 1.959963984540054


def _basis(rows, start_index: int, decay: float):
    """Return unit-initial-state and powered-input responses at every row."""
    a_values = [0.0] * len(rows)
    b_values = [0.0] * len(rows)
    a_values[start_index] = 1.0
    for index in range(start_index, len(rows) - 1):
        left, right = rows[index], rows[index + 1]
        delta = right["time"] - left["time"]
        if delta < 0:
            raise InputError("Trajectory schedule is not ordered")
        attenuation = math.exp(-decay * delta)
        if decay == 0:
            input_integral = delta
        else:
            input_integral = -math.expm1(-decay * delta) / decay
        powered = left["power"] != "none"
        a_values[index + 1] = a_values[index] * attenuation
        b_values[index + 1] = b_values[index] * attenuation + (input_integral if powered else 0.0)
        if not math.isfinite(a_values[index + 1]) or not math.isfinite(b_values[index + 1]):
            raise InputError("State-model basis exceeds the supported floating-point range")
    return a_values, b_values


def _linear_fit(rows, observation_indices, decay):
    start = observation_indices[0]
    a, b = _basis(rows, start, decay)
    pairs = [(a[index], b[index], rows[index]["reading"]) for index in observation_indices]
    aa = math.fsum(x * x for x, _z, _y in pairs)
    bb = math.fsum(z * z for _x, z, _y in pairs)
    ab = math.fsum(x * z for x, z, _y in pairs)
    ay = math.fsum(x * y for x, _z, y in pairs)
    by = math.fsum(z * y for _x, z, y in pairs)
    determinant = aa * bb - ab * ab
    candidates = []
    if determinant > max(1e-30, 1e-14 * aa * bb):
        initial = (ay * bb - by * ab) / determinant
        input_rate = (by * aa - ay * ab) / determinant
        if initial >= 0 and input_rate >= 0:
            candidates.append((initial, input_rate))
    if aa > 0:
        candidates.append((max(0.0, ay / aa), 0.0))
    if bb > 0:
        candidates.append((0.0, max(0.0, by / bb)))
    candidates.append((0.0, 0.0))

    def score(parameters):
        initial, input_rate = parameters
        return math.fsum((y - initial * x - input_rate * z) ** 2 for x, z, y in pairs)

    initial, input_rate = min(candidates, key=score)
    sse = score((initial, input_rate))
    if not all(math.isfinite(value) for value in (initial, input_rate, sse)):
        raise InputError("State-model estimates exceed the supported floating-point range")
    return {"initial_state": initial, "powered_input": input_rate, "conversion": decay,
            "sum_squared_error": sse, "a": a, "b": b}


def _profile_grid():
    low, high = math.log(1e-10), math.log(1000.0)
    return [0.0, *(math.exp(low + (high - low) * index / (PROFILE_GRID_SIZE - 1))
                    for index in range(PROFILE_GRID_SIZE))]


def _fit_state(rows, eligible_indices, noise_sd):
    if len(rows) > MAX_ESTIMATION_ROWS:
        return {"estimable": False, "reason": "Trajectory exceeds the state-estimator row limit"}
    if len(eligible_indices) < 4:
        return {"estimable": False, "reason": "At least four unbiased training readings are required"}
    ranked = []
    for decay in _profile_grid():
        result = _linear_fit(rows, eligible_indices, decay)
        ranked.append((result["sum_squared_error"], decay, result))
    ranked.sort(key=lambda item: item[0])
    _best_sse, best_decay, best = ranked[0]
    if best_decay > 0:
        position = _profile_grid().index(best_decay)
        grid = _profile_grid()
        left = math.log(grid[max(1, position - 1)])
        right = math.log(grid[min(len(grid) - 1, position + 1)])
        ratio = (math.sqrt(5.0) - 1.0) / 2.0
        c = right - ratio * (right - left)
        d = left + ratio * (right - left)
        fc = _linear_fit(rows, eligible_indices, math.exp(c))["sum_squared_error"]
        fd = _linear_fit(rows, eligible_indices, math.exp(d))["sum_squared_error"]
        for _ in range(PROFILE_REFINEMENT_STEPS):
            if fc <= fd:
                right, d, fd = d, c, fc
                c = right - ratio * (right - left)
                fc = _linear_fit(rows, eligible_indices, math.exp(c))["sum_squared_error"]
            else:
                left, c, fc = c, d, fd
                d = left + ratio * (right - left)
                fd = _linear_fit(rows, eligible_indices, math.exp(d))["sum_squared_error"]
        refined = [best, _linear_fit(rows, eligible_indices, math.exp(c)),
                   _linear_fit(rows, eligible_indices, math.exp(d))]
        best = min(refined, key=lambda item: item["sum_squared_error"])

    initial_index = eligible_indices[0]
    a, b = _basis(rows, initial_index, best["conversion"])
    parameters = (best["initial_state"], best["powered_input"], best["conversion"])
    sample_count = len(eligible_indices)
    residual_scale = math.sqrt(best["sum_squared_error"] / sample_count)
    variance = noise_sd * noise_sd if noise_sd > 0 else (
        best["sum_squared_error"] / max(1, sample_count - 3))
    jacobian = []
    epsilon = max(1e-8, best["conversion"] * 1e-5)
    lower = max(0.0, best["conversion"] - epsilon)
    upper = min(1000.0, best["conversion"] + epsilon)
    lower_basis = _basis(rows, initial_index, lower) if upper > lower else None
    upper_basis = _basis(rows, initial_index, upper) if upper > lower else None
    for index in eligible_indices:
        if upper_basis is None or lower_basis is None:
            derivative_k = 0.0
        else:
            low_prediction = (best["initial_state"] * lower_basis[0][index]
                              + best["powered_input"] * lower_basis[1][index])
            high_prediction = (best["initial_state"] * upper_basis[0][index]
                               + best["powered_input"] * upper_basis[1][index])
            derivative_k = (high_prediction - low_prediction) / (upper - lower)
        jacobian.append((a[index], b[index], derivative_k))
    covariance = _covariance(jacobian, variance)
    return {"estimable": True, "parameters": {"initial_state": parameters[0],
                                                "powered_input": parameters[1],
                                                "conversion": parameters[2]},
            "parameter_standard_errors": (None if covariance is None else
                {name: math.sqrt(max(0.0, covariance[position][position]))
                 for position, name in enumerate(("initial_state", "powered_input", "conversion"))}),
            "parameter_covariance": covariance,
            "n_training_readings": sample_count,
            "training_start_time": rows[initial_index]["time"],
            "training_end_time": rows[eligible_indices[-1]]["time"],
            "training_rmse": residual_scale,
            "sensor_noise_sd_assumed": noise_sd,
            "noise_model": "Independent Gaussian observation noise with the fixture's declared sensor noise standard deviation; censored, unavailable and biased readings are excluded.",
            "a": a, "b": b}


def _covariance(jacobian, variance):
    if len(jacobian) < 3:
        return None
    matrix = [[math.fsum(row[i] * row[j] for row in jacobian) for j in range(3)]
              for i in range(3)]
    augmented = [matrix[index] + [1.0 if index == j else 0.0 for j in range(3)]
                 for index in range(3)]
    scale = max((abs(value) for row in matrix for value in row), default=0.0)
    if scale == 0:
        return None
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= scale * 1e-12:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [value - factor * source
                              for value, source in zip(augmented[row], augmented[column])]
    inverse = [row[3:] for row in augmented]
    covariance = [[inverse[i][j] * variance for j in range(3)] for i in range(3)]
    if any(not math.isfinite(value) for row in covariance for value in row):
        return None
    return covariance


def _biased_time(time, faults):
    return any(fault["kind"] == "bias" and fault["start"] <= time < fault["end"]
               for fault in faults)


def noise_aware_state_fit(rows, faults, noise_sd):
    indices = [index for index, row in enumerate(rows)
               if row["sampled"] and row["reading"] is not None
               and not _biased_time(row["time"], faults)]
    fit = _fit_state(rows, indices, noise_sd)
    return {key: value for key, value in fit.items()
            if key not in {"a", "b", "parameter_covariance"}}


def prospective_forecast(rows, faults, split_time: float, noise_sd: float):
    """Fit only the temporal prefix and score later measurements from its initial state."""
    training_indices = [index for index, row in enumerate(rows)
                        if row["sampled"] and row["reading"] is not None
                        and row["time"] <= split_time and not _biased_time(row["time"], faults)]
    heldout_indices = [index for index, row in enumerate(rows)
                       if row["sampled"] and row["reading"] is not None
                       and row["time"] > split_time and not _biased_time(row["time"], faults)]
    excluded_biased = sum(row["sampled"] and row["reading"] is not None
                          and row["time"] > split_time and _biased_time(row["time"], faults)
                          for row in rows)
    result = {"estimable": False, "split_time": split_time,
              "n_training_readings": len(training_indices), "n_scored_readings": 0,
              "n_excluded_biased_readings": excluded_biased,
              "fixture_scale_rmse": None, "baseline_last_observation_rmse": None,
              "mae": None, "mean_error": None, "coverage_95": None,
              "mean_95_interval_width": None, "reason": None}
    fit = _fit_state(rows, training_indices, noise_sd)
    if not fit["estimable"]:
        result["reason"] = fit["reason"]
        result["state_fit"] = {key: value for key, value in fit.items()
                               if key not in {"a", "b", "parameter_covariance"}}
        return result
    if not heldout_indices:
        result["reason"] = "No unbiased scheduled readings occur after the split"
        result["state_fit"] = {key: value for key, value in fit.items()
                               if key not in {"a", "b", "parameter_covariance"}}
        return result
    parameters = fit["parameters"]
    origin_index = training_indices[0]
    origin_time = rows[origin_index]["time"]
    a, b = _basis(rows, origin_index, parameters["conversion"])
    epsilon = max(1e-8, parameters["conversion"] * 1e-5)
    lower, upper = max(0.0, parameters["conversion"] - epsilon), min(1000.0, parameters["conversion"] + epsilon)
    lower_basis = _basis(rows, origin_index, lower) if upper > lower else None
    upper_basis = _basis(rows, origin_index, upper) if upper > lower else None
    errors, baseline_errors, covered, widths = [], [], [], []
    for index in heldout_indices:
        prediction = parameters["initial_state"] * a[index] + parameters["powered_input"] * b[index]
        actual = rows[index]["reading"]
        errors.append(actual - prediction)
        last_training_value = rows[training_indices[-1]]["reading"]
        baseline_errors.append(actual - last_training_value)
        variance = noise_sd * noise_sd
        if fit["parameter_covariance"] is not None:
            derivative_k = 0.0
            if lower_basis is not None and upper_basis is not None:
                derivative_k = (parameters["initial_state"] * (upper_basis[0][index] - lower_basis[0][index])
                                + parameters["powered_input"] * (upper_basis[1][index] - lower_basis[1][index])) / (upper - lower)
            gradient = (a[index], b[index], derivative_k)
            variance += math.fsum(gradient[i] * fit["parameter_covariance"][i][j] * gradient[j]
                                  for i in range(3) for j in range(3))
        half_width = Z_95 * math.sqrt(max(0.0, variance))
        covered.append(abs(actual - prediction) <= half_width)
        widths.append(2 * half_width)
    rmse = math.sqrt(math.fsum(error * error for error in errors) / len(errors))
    baseline_rmse = math.sqrt(math.fsum(error * error for error in baseline_errors) / len(baseline_errors))
    if not all(math.isfinite(value) for value in (rmse, baseline_rmse, *errors, *widths)):
        raise InputError("Prospective forecast exceeds the supported floating-point range")
    result.update(estimable=True, training_start_time=origin_time,
                  n_scored_readings=len(errors), fixture_scale_rmse=rmse,
                  baseline_last_observation_rmse=baseline_rmse,
                  mae=math.fsum(abs(error) for error in errors) / len(errors),
                  mean_error=math.fsum(errors) / len(errors),
                  coverage_95=sum(covered) / len(covered),
                  mean_95_interval_width=math.fsum(widths) / len(widths),
                  uncertainty_method="Delta-method state-parameter covariance plus the declared independent Gaussian sensor noise; approximate, synthetic-fixture-only.",
                  reason=None,
                  state_fit={key: value for key, value in fit.items()
                             if key not in {"a", "b", "parameter_covariance"}})
    return result
