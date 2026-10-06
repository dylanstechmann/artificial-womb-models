"""Bounded synthetic cadence/noise, monitor-fault and event-timing sweeps."""
from __future__ import annotations

import copy
import math
import statistics
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json, sha256
from .exchange import NOTICE, run_fixture, validate_config
from .identifiability import RANK_TOLERANCE, _fit, _intervals
from .state_estimation import prospective_forecast

CADENCE_FACTORS = (0.5, 1.0, 2.0)
NOISE_MULTIPLIERS = (0.0, 1.0, 2.0)
CONFIGURED_FAULTS = "configured monitor faults"
FAULT_FREE_PROFILE = "injected monitor faults removed"
AS_CONFIGURED_TIMING = "configured event timing"
REFLECTED_TIMING = "time-reflected event timing"
MAX_REPLICATES = 20
MIN_REPLICATES = 1
MIN_STEP = 1e-6
MAX_STEP_INTERVALS = 50_000
MAX_NOISE_SD = 1_000.0
MAX_TOTAL_SCHEDULED_SAMPLES = 4_000_000


def _median(values):
    finite = [value for value in values if isinstance(value, (int, float))
              and not isinstance(value, bool) and math.isfinite(value)]
    return statistics.median(finite) if finite else None


def _percentile(values, percentile):
    finite = sorted(value for value in values
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                    and math.isfinite(value))
    if not finite:
        return None
    return finite[max(0, math.ceil(percentile * len(finite)) - 1)]


def _compact_rows(rows):
    return [{"time": row["dimensionless_time"], "power": row["power_source"],
             "sampled": row["sensor_sampled"], "reading": row["sensor_reading"]}
            for row in rows]


def _reflect_intervals(events, duration):
    """Reflect event intervals across the fixture midpoint, preserving lengths."""
    reflected = []
    for event in events:
        item = dict(event)
        item["start"] = duration - event["end"]
        item["end"] = duration - event["start"]
        reflected.append(item)
    return sorted(reflected, key=lambda item: (item["start"], item["end"]))


def _fit_record(fit, true_rates):
    estimates = fit.get("parameter_estimates", {})
    record = {"estimable": fit.get("estimable", False),
              "rank": fit.get("rank", 0),
              "normalized_design_condition_number": fit.get("normalized_design_condition_number"),
              "fixture_scale_rmse": fit.get("fixture_scale_rmse")}
    for name in ("powered_input", "conversion"):
        estimate = estimates.get(name)
        truth = true_rates[name]
        record[f"estimated_{name}"] = estimate
        record[f"true_{name}_for_synthetic_scoring_only"] = truth
        record[f"absolute_error_{name}"] = abs(estimate - truth) if estimate is not None else None
        record[f"relative_absolute_error_{name}"] = (
            abs(estimate - truth) / abs(truth) if estimate is not None and truth != 0 else None)
    return record


def _temporal_holdout(intervals, duration):
    """Fit the first 70% of one run and score only its later intervals."""
    split_time = duration * 0.7
    training = [item for item in intervals if item["end"] <= split_time]
    heldout = [item for item in intervals if item["start"] >= split_time]
    result = {"estimable": False, "split_time": split_time,
              "n_intervals": len(heldout), "fixture_scale_rmse": None,
              "reason": None}
    fit = _fit(training)
    if not fit.get("estimable"):
        result["reason"] = "The first 70% of intervals did not identify both fixture rates"
        return result
    if not heldout:
        result["reason"] = "No complete later intervals remain after the split"
        return result
    estimates = fit["parameter_estimates"]
    errors = [item["observed_change"]
              - (estimates["powered_input"] * item["powered_exposure"]
                 + estimates["conversion"] * item["conversion_exposure"])
              for item in heldout]
    rmse = math.sqrt(math.fsum(error * error for error in errors) / len(errors))
    if not math.isfinite(rmse):
        raise InputError("Temporal holdout residuals exceed the supported floating-point range")
    result.update(estimable=True, fixture_scale_rmse=rmse, reason=None)
    return result


def _interval_statistics(intervals):
    """Keep bounded sufficient statistics for seed-group holdout scoring."""
    return {
        "n_intervals": len(intervals),
        "powered_squared": math.fsum(item["powered_exposure"] ** 2 for item in intervals),
        "conversion_squared": math.fsum(item["conversion_exposure"] ** 2 for item in intervals),
        "cross_product": math.fsum(item["powered_exposure"] * item["conversion_exposure"]
                                   for item in intervals),
        "powered_change": math.fsum(item["powered_exposure"] * item["observed_change"]
                                    for item in intervals),
        "conversion_change": math.fsum(item["conversion_exposure"] * item["observed_change"]
                                       for item in intervals),
        "change_squared": math.fsum(item["observed_change"] ** 2 for item in intervals),
    }


def _combine_statistics(groups):
    names = ("powered_squared", "conversion_squared", "cross_product",
             "powered_change", "conversion_change", "change_squared")
    return {"n_intervals": sum(item["n_intervals"] for item in groups),
            **{name: math.fsum(item[name] for item in groups) for name in names}}


def _fit_statistics(stats):
    """Fit a pooled seed group from sufficient statistics, without truth values."""
    if stats["n_intervals"] < 2:
        return {"estimable": False, "reason": "Fewer than two training intervals"}
    norm0 = math.sqrt(stats["powered_squared"])
    norm1 = math.sqrt(stats["conversion_squared"])
    if norm0 == 0 or norm1 == 0:
        return {"estimable": False, "reason": "At least one model term has no variation"}
    correlation = (stats["cross_product"] / norm0) / norm1
    correlation = max(-1.0, min(1.0, correlation))
    eig_large = 1.0 + abs(correlation)
    eig_small = 1.0 - abs(correlation)
    singular_large = math.sqrt(eig_large)
    singular_small = math.sqrt(max(0.0, eig_small))
    condition = singular_large / singular_small if singular_small > 0 else None
    if eig_small <= RANK_TOLERANCE * eig_large:
        return {"estimable": False, "rank": 1,
                "design_column_correlation": correlation,
                "normalized_design_condition_number": condition,
                "reason": "The pooled training effects are collinear"}
    denominator = 1.0 - correlation * correlation
    normalized_xy0 = stats["powered_change"] / norm0
    normalized_xy1 = stats["conversion_change"] / norm1
    normalized_beta0 = (normalized_xy0 - correlation * normalized_xy1) / denominator
    normalized_beta1 = (normalized_xy1 - correlation * normalized_xy0) / denominator
    estimates = {"powered_input": normalized_beta0 / norm0,
                 "conversion": normalized_beta1 / norm1}
    if not all(math.isfinite(value) for value in estimates.values()):
        return {"estimable": False, "rank": 2,
                "design_column_correlation": correlation,
                "normalized_design_condition_number": condition,
                "reason": "Pooled training estimates exceed the supported floating-point range"}
    return {"estimable": True, "rank": 2, "parameter_estimates": estimates,
            "design_column_correlation": correlation,
            "normalized_design_condition_number": condition,
            "n_intervals": stats["n_intervals"]}


def _prediction_rmse(stats, estimates):
    """Score a separate replicate from its sufficient statistics."""
    powered = estimates["powered_input"]
    conversion = estimates["conversion"]
    terms = [stats["change_squared"],
             -2.0 * powered * stats["powered_change"],
             -2.0 * conversion * stats["conversion_change"],
             powered * powered * stats["powered_squared"],
             2.0 * powered * conversion * stats["cross_product"],
             conversion * conversion * stats["conversion_squared"]]
    try:
        residual_sum = math.fsum(terms)
    except OverflowError:
        raise InputError("Cross-replicate residuals exceed the supported floating-point range") from None
    if not math.isfinite(residual_sum):
        raise InputError("Cross-replicate residuals exceed the supported floating-point range")
    if residual_sum < 0:
        tolerance = 1e-12 * max(1.0, math.fsum(abs(value) for value in terms))
        if abs(residual_sum) <= tolerance:
            residual_sum = 0.0
        else:
            raise InputError("Cross-replicate residual sum is numerically inconsistent")
    rmse = math.sqrt(residual_sum / stats["n_intervals"])
    if not math.isfinite(rmse):
        raise InputError("Cross-replicate RMSE exceeds the supported floating-point range")
    return rmse


def _leave_one_replicate_out(groups):
    """Fit all other seeded runs of one design and score the omitted run."""
    results = []
    for index, heldout in enumerate(groups):
        training = [group for other, group in enumerate(groups) if other != index]
        base = {"estimable": False, "training_replicates": len(training),
                "fixture_scale_rmse": None, "reason": None}
        if not training:
            base["reason"] = "At least two seeded replicates are required"
        else:
            fit = _fit_statistics(_combine_statistics(training))
            if not fit.get("estimable"):
                base["reason"] = fit.get("reason", "Pooled training fit was not estimable")
            elif heldout["n_intervals"] < 1:
                base["reason"] = "Held-out replicate has no usable intervals"
            else:
                base.update(estimable=True,
                            fixture_scale_rmse=_prediction_rmse(heldout, fit["parameter_estimates"]))
        results.append(base)
    return results


def sweep(config_path: Path, output: Path, *, replicates: int = 8) -> dict:
    """Compare cadence/noise, monitor-fault and event-timing profiles with seeded runs."""
    if isinstance(replicates, bool) or not isinstance(replicates, int) or not MIN_REPLICATES <= replicates <= MAX_REPLICATES:
        raise InputError(f"replicates must be an integer from {MIN_REPLICATES} to {MAX_REPLICATES}")
    config, config_raw = read_json(config_path)
    parsed = validate_config(config)
    base_step = parsed["step"]
    base_noise = parsed["monitor"]["noise_sd"]
    noise_reference = (base_noise if base_noise > 0 else
                       min(100.0, max(1e-6, parsed["monitor"]["residual_threshold"] * 0.25)))
    fault_profiles = ([CONFIGURED_FAULTS, FAULT_FREE_PROFILE]
                      if parsed["faults"] else [CONFIGURED_FAULTS])
    timing_profiles = ([AS_CONFIGURED_TIMING, REFLECTED_TIMING]
                       if parsed["outages"] or parsed["faults"] else [AS_CONFIGURED_TIMING])
    base_seed = parsed["monitor"]["seed"]
    steps = []
    for factor in CADENCE_FACTORS:
        requested_step = min(parsed["duration"], base_step * factor)
        steps.append(max(MIN_STEP, requested_step, parsed["duration"] / MAX_STEP_INTERVALS))
    scheduled_samples = (sum(math.ceil(parsed["duration"] / step) + 1 for step in steps)
                         * len(NOISE_MULTIPLIERS) * len(fault_profiles)
                         * len(timing_profiles) * replicates)
    if scheduled_samples > MAX_TOTAL_SCHEDULED_SAMPLES:
        raise InputError("Sweep exceeds the 4,000,000 scheduled-sample budget; reduce --replicates or use a coarser source fixture")
    event_schedules = {}
    for timing_profile in timing_profiles:
        wall_events = parsed["outages"]
        monitor_events = parsed["faults"]
        if timing_profile == REFLECTED_TIMING:
            wall_events = _reflect_intervals(wall_events, parsed["duration"])
            monitor_events = _reflect_intervals(monitor_events, parsed["duration"])
        event_schedules[timing_profile] = {
            "wall_outages": wall_events,
            "monitor_faults_before_fault_removal_profile": monitor_events,
        }
    true_rates = {"powered_input": parsed["rates"]["powered_input"],
                  "conversion": parsed["rates"]["conversion"]}
    scenario_rows = []
    run_rows = []
    cell_index = 0

    for cadence_factor, step in zip(CADENCE_FACTORS, steps):
        for noise_multiplier in NOISE_MULTIPLIERS:
            noise_sd = min(MAX_NOISE_SD, noise_reference * noise_multiplier)
            for timing_profile in timing_profiles:
                for fault_profile in fault_profiles:
                    cell_runs = []
                    cell_statistics = []
                    for replicate in range(replicates):
                        candidate = copy.deepcopy(config)
                        candidate["dimensionless_time"]["output_step"] = step
                        candidate["monitor"]["noise_sd"] = noise_sd
                        if timing_profile == REFLECTED_TIMING:
                            candidate["wall_outages"] = _reflect_intervals(
                                candidate["wall_outages"], parsed["duration"])
                            candidate["monitor_faults"] = _reflect_intervals(
                                candidate["monitor_faults"], parsed["duration"])
                        if fault_profile == FAULT_FREE_PROFILE:
                            candidate["monitor_faults"] = []
                        candidate["monitor"]["seed"] = (base_seed + cell_index * replicates + replicate) % (2**32)
                        rows, _simulation_summary = run_fixture(candidate)
                        compact = _compact_rows(rows)
                        scheduled = sum(row["sampled"] for row in compact)
                        usable = sum(row["sampled"] and row["reading"] is not None for row in compact)
                        intervals = _intervals(compact)
                        fit = _fit(intervals)
                        holdout = _temporal_holdout(intervals, parsed["duration"])
                        forecast = prospective_forecast(
                            compact, candidate["monitor_faults"], parsed["duration"] * 0.7, noise_sd)
                        state_fit = forecast.get("state_fit", {})
                        state_parameters = state_fit.get("parameters", {})
                        state_errors = {name: (abs(state_parameters[name] - true_rates[name])
                                               if name in state_parameters else None)
                                        for name in ("powered_input", "conversion")}
                        cell_statistics.append(_interval_statistics(intervals))
                        result = {
                            "cadence_factor_requested": cadence_factor,
                            "actual_output_step": step,
                            "noise_multiplier_requested": noise_multiplier,
                            "actual_noise_sd": noise_sd,
                            "monitor_fault_profile": fault_profile,
                            "event_timing_profile": timing_profile,
                            "replicate": replicate + 1,
                            "seed": candidate["monitor"]["seed"],
                            "n_scheduled_readings": scheduled,
                            "n_usable_readings": usable,
                            "temporal_holdout_estimable": holdout["estimable"],
                            "temporal_holdout_split_time": holdout["split_time"],
                            "temporal_holdout_n_intervals": holdout["n_intervals"],
                            "temporal_holdout_fixture_scale_rmse": holdout["fixture_scale_rmse"],
                            "temporal_holdout_reason": holdout["reason"],
                            "prospective_forecast_estimable": forecast["estimable"],
                            "prospective_forecast_training_readings": forecast["n_training_readings"],
                            "prospective_forecast_scored_readings": forecast["n_scored_readings"],
                            "prospective_forecast_rmse": forecast["fixture_scale_rmse"],
                            "prospective_forecast_last_value_baseline_rmse": forecast["baseline_last_observation_rmse"],
                            "prospective_forecast_mae": forecast["mae"],
                            "prospective_forecast_bias": forecast["mean_error"],
                            "prospective_forecast_coverage_95": forecast["coverage_95"],
                            "prospective_forecast_mean_interval_width_95": forecast["mean_95_interval_width"],
                            "prospective_forecast_reason": forecast["reason"],
                            "state_fit_estimated_powered_input": state_parameters.get("powered_input"),
                            "state_fit_estimated_conversion": state_parameters.get("conversion"),
                            "state_fit_absolute_error_powered_input": state_errors["powered_input"],
                            "state_fit_absolute_error_conversion": state_errors["conversion"],
                            **_fit_record(fit, true_rates),
                        }
                        run_rows.append(result)
                        cell_runs.append(result)
                    cross_holdouts = _leave_one_replicate_out(cell_statistics)
                    for item, holdout in zip(cell_runs, cross_holdouts):
                        item.update(
                            cross_replicate_holdout_estimable=holdout["estimable"],
                            cross_replicate_holdout_training_replicates=holdout["training_replicates"],
                            cross_replicate_holdout_fixture_scale_rmse=holdout["fixture_scale_rmse"],
                            cross_replicate_holdout_reason=holdout["reason"])
                    estimable = [item for item in cell_runs if item["estimable"]]
                    holdout_estimable = [item for item in cell_runs
                                         if item["temporal_holdout_estimable"]]
                    cross_holdout_estimable = [item for item in cell_runs
                                               if item["cross_replicate_holdout_estimable"]]
                    forecast_estimable = [item for item in cell_runs
                                          if item["prospective_forecast_estimable"]]
                    scenario_rows.append({
                        "cadence_factor_requested": cadence_factor,
                        "actual_output_step": step,
                        "noise_multiplier_requested": noise_multiplier,
                        "actual_noise_sd": noise_sd,
                        "monitor_fault_profile": fault_profile,
                        "event_timing_profile": timing_profile,
                        "replicates": replicates,
                        "estimable_replicates": len(estimable),
                        "estimable_fraction": len(estimable) / replicates,
                        "temporal_holdout_estimable_replicates": len(holdout_estimable),
                        "temporal_holdout_estimable_fraction": len(holdout_estimable) / replicates,
                        "median_temporal_holdout_fixture_scale_rmse": _median(
                            [item["temporal_holdout_fixture_scale_rmse"] for item in holdout_estimable]),
                        "p90_temporal_holdout_fixture_scale_rmse": _percentile(
                            [item["temporal_holdout_fixture_scale_rmse"] for item in holdout_estimable], 0.9),
                        "cross_replicate_holdout_estimable_replicates": len(cross_holdout_estimable),
                        "cross_replicate_holdout_estimable_fraction": len(cross_holdout_estimable) / replicates,
                        "median_cross_replicate_holdout_fixture_scale_rmse": _median(
                            [item["cross_replicate_holdout_fixture_scale_rmse"] for item in cross_holdout_estimable]),
                        "p90_cross_replicate_holdout_fixture_scale_rmse": _percentile(
                            [item["cross_replicate_holdout_fixture_scale_rmse"] for item in cross_holdout_estimable], 0.9),
                        "prospective_forecast_estimable_replicates": len(forecast_estimable),
                        "prospective_forecast_estimable_fraction": len(forecast_estimable) / replicates,
                        "median_prospective_forecast_rmse": _median(
                            [item["prospective_forecast_rmse"] for item in forecast_estimable]),
                        "p90_prospective_forecast_rmse": _percentile(
                            [item["prospective_forecast_rmse"] for item in forecast_estimable], 0.9),
                        "median_prospective_forecast_baseline_rmse": _median(
                            [item["prospective_forecast_last_value_baseline_rmse"] for item in forecast_estimable]),
                        "median_prospective_forecast_coverage_95": _median(
                            [item["prospective_forecast_coverage_95"] for item in forecast_estimable]),
                        "median_prospective_forecast_interval_width_95": _median(
                            [item["prospective_forecast_mean_interval_width_95"] for item in forecast_estimable]),
                        "median_usable_readings": _median([item["n_usable_readings"] for item in cell_runs]),
                        "median_design_condition_number": _median(
                            [item["normalized_design_condition_number"] for item in cell_runs]),
                        "p90_design_condition_number": _percentile(
                            [item["normalized_design_condition_number"] for item in cell_runs], 0.9),
                        "median_fixture_scale_rmse": _median([item["fixture_scale_rmse"] for item in estimable]),
                        "median_absolute_error_powered_input": _median(
                            [item["absolute_error_powered_input"] for item in estimable]),
                        "p90_absolute_error_powered_input": _percentile(
                            [item["absolute_error_powered_input"] for item in estimable], 0.9),
                        "median_absolute_error_conversion": _median(
                            [item["absolute_error_conversion"] for item in estimable]),
                        "p90_absolute_error_conversion": _percentile(
                            [item["absolute_error_conversion"] for item in estimable], 0.9),
                        "median_relative_absolute_error_powered_input": _median(
                            [item["relative_absolute_error_powered_input"] for item in estimable]),
                        "median_relative_absolute_error_conversion": _median(
                            [item["relative_absolute_error_conversion"] for item in estimable]),
                    })
                    cell_index += 1

    plan = {
        "schema_version": 1,
        "design": "3 output-cadence factors × 3 sensor-noise multipliers × available monitor-fault profiles × event-timing profiles × seeded replicates",
        "cadence_factors": list(CADENCE_FACTORS),
        "cadence_designs": [
            {"cadence_factor_requested": factor, "actual_output_step": step}
            for factor, step in zip(CADENCE_FACTORS, steps)],
        "noise_multipliers": list(NOISE_MULTIPLIERS),
        "noise_designs": [
            {"noise_multiplier_requested": multiplier,
             "actual_noise_sd": min(MAX_NOISE_SD, noise_reference * multiplier)}
            for multiplier in NOISE_MULTIPLIERS],
        "monitor_fault_profiles": fault_profiles,
        "event_timing_profiles": timing_profiles,
        "event_schedules": event_schedules,
        "event_reflection_contract": "Each interval [start, end) maps to [duration-end, duration-start); interval lengths are preserved.",
        "noise_reference_sd": noise_reference,
        "replicates_per_design": replicates,
        "maximum_fixture_output_intervals": MAX_STEP_INTERVALS,
        "maximum_total_scheduled_samples": MAX_TOTAL_SCHEDULED_SAMPLES,
        "estimated_scheduled_samples": scheduled_samples,
        "source_config_sha256": sha256(config_raw),
        "fixed_wall_outage_count": len(parsed["outages"]),
        "configured_monitor_fault_count": len(parsed["faults"]),
        "wall_outages_retained_in_all_profiles": True,
        "power-loss-related_missing_readings_retained_in_all_profiles": True,
        "scoring_boundary": "Generator-known rates are used only to score estimates after fitting; they are not fit inputs.",
        "prospective_forecast_contract": "Fit the nonnegative single-stock state model only on unbiased scheduled sensor readings at or before 70% of dimensionless run duration; propagate its fitted state and the receipt-bound known power schedule forward without assimilating later readings; score later unbiased readings against a last-training-reading baseline.",
        "prospective_forecast_training_cutoff": "0.7 × dimensionless duration (not 70% of interval count)",
        "prospective_forecast_noise_contract": "Independent Gaussian sensor noise with the configured standard deviation; local covariance plus observation noise gives an approximate 95% prediction interval.",
        "temporal_holdout_contract": "The legacy integral-balance residual diagnostic uses endpoint readings both in the response and trapezoidal predictors; it is consistency checking and not a forecast.",
        "temporal_holdout_training_fraction": 0.7,
        "cross_replicate_holdout_contract": "Leave one seeded synthetic replicate out, fit pooled intervals from other replicates of the same design and score the omitted run. These runs share the same fixture and schedule; this is not independent experimental validation.",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
    }
    report = {
        "schema_version": 2,
        "fixture_notice": NOTICE,
        "result_kind": "synthetic_exchange_design_sweep",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "n_designs": len(scenario_rows),
        "n_synthetic_runs": len(run_rows),
        "noise_reference_sd": noise_reference,
        "fixture_truth_used_for_scoring_only": true_rates,
        "method": "Seeded synthetic replicate sweep; the primary forecast fits a nonnegative state-space model to the first 70% of dimensionless run time and scores untouched future sensor readings against a last-observation baseline. The integral-balance analysis remains as a separately labeled residual diagnostic.",
        "prospective_forecast_contract": "Each temporal forecast is trained only on scheduled, unbiased prefix readings. No future sensor values enter its predictors; intervals use local parameter covariance and declared fixture sensor noise.",
        "prospective_forecast_training_cutoff": "0.7 × dimensionless duration (not 70% of interval count)",
        "temporal_holdout_contract": "Legacy balance-residual diagnostic; endpoint readings appear in the trapezoidal predictors and therefore the score is not a forecast.",
        "cross_replicate_holdout_contract": "For each seeded run, fit pooled intervals from other seeds in its design and score the omitted run. The seeds share one fixture, configuration and event schedule; this is not independent experimental validation.",
        "design_summaries": scenario_rows,
        "event_timing_profiles": timing_profiles,
        "limits": [
            "All values, rates, noise and times are invented dimensionless software quantities.",
            "Cadence and noise contrasts describe this fixture only and are not biological measurement recommendations.",
            "Event timing profiles compare the configured schedule with its time reflection; they do not represent realistic outage or fault distributions.",
            "The unconstrained two-rate integral regression may be biased by trapezoidal approximation, noise and model mismatch; its residual scores are not forecasts.",
            "Prospective forecasts are temporal holdouts within one synthetic trajectory; the fixture's known state equation and noise distribution do not establish performance on measured biological systems.",
            "Forecast uncertainty uses a local linear covariance approximation and is unreliable near parameter boundaries or weakly identified designs.",
            "Cross-replicate holdout fits use other seeded runs of the same fixture and event schedule; they are software checks, not independent experiments.",
            "Generator-known rates are excluded from each fit and appear only in explicitly labeled synthetic recovery scoring.",
            "Within each design profile, replicates share one model, input configuration and event schedule; they are not independent experiments.",
            "No embryo, animal, patient, device or clinical-outcome data are analyzed.",
        ],
    }
    fault_note = ("A fault-free profile removes configured monitor bias/dropout intervals; modeled wall outages and power-loss-related missing readings remain."
                  if FAULT_FREE_PROFILE in fault_profiles else
                  "No monitor-fault removal profile was needed because the source fixture has no configured monitor faults.")
    timing_note = ("The reflected-timing profile maps each configured interval [start, end) to [duration-end, duration-start), preserving duration while changing its location on the fixture timeline."
                   if REFLECTED_TIMING in timing_profiles else
                   "No event-timing reflection was needed because the source fixture has no outage or monitor-fault intervals.")
    lines = ["# Dimensionless exchange design sweep", "", NOTICE, "",
             f"The bounded sweep contains {len(scenario_rows)} cadence/noise/fault/timing designs and {len(run_rows)} seeded software-fixture runs.",
             "Generator-known rates are used only after fitting to score synthetic recovery; they are not fit inputs.",
             "Prospective forecasts fit a nonnegative state-space model through 70% of run duration and propagate its state forward without using later sensor readings in predictors. Scores are compared with a last-training-reading baseline.",
             "The integral-balance temporal and leave-one-seed-out results are residual consistency diagnostics because endpoint readings appear in their predictors. They are not forecasts.",
             "Forecast intervals use a local parameter-covariance approximation plus configured Gaussian sensor noise; they are not calibrated biological uncertainty intervals.",
             fault_note, timing_note,
             "All times, rates, cadence and noise are dimensionless fixture quantities.", "",
             "## Design-level summaries", "",
             "`design_sweep.csv` reports prospective state-model forecast error, a last-observation baseline, approximate interval coverage, legacy balance-residual diagnostics, fit conditioning and synthetic rate-recovery errors.",
             "These summaries do not recommend biological measurement schedules.", "", "## Limits", ""]
    lines.extend(f"- {item}" for item in report["limits"])
    files = {
        "input_config.json": config_raw,
        "sweep_plan.json": json_bytes(plan),
        "design_sweep_report.json": json_bytes(report),
        "design_sweep.csv": csv_bytes(list(run_rows[0]) if run_rows else [], run_rows),
        "design_summaries.csv": csv_bytes(list(scenario_rows[0]) if scenario_rows else [], scenario_rows),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    return publish_bundle(
        output, kind="synthetic_exchange_design_sweep", input_raw=config_raw, files=files,
        metadata={"biological_measurements": False,
                  "physiologically_calibrated": False,
                  "human_gestation_prediction": False,
                  "source_config_sha256": sha256(config_raw),
                  "replicates_per_design": replicates,
                  "n_synthetic_runs": len(run_rows)})
