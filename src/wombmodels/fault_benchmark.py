"""Paired first-alarm evaluation of the frozen common-cause fault detectors."""
from __future__ import annotations

import math
import random
from collections import Counter
from pathlib import Path
from statistics import median

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .common_cause_fault import MODES, _fault_run, _integration_rate, _validate_experiment
from .exchange import NOTICE
from .numerics import output_times
from .whole_path_twin import SUBSTEP_RATE_TARGET

DEFAULT_REPLICATES = 12
MAX_REPLICATES = 32
MAX_BENCHMARK_SUBSTEPS = 1_000_000
NOISE_MULTIPLIERS = (1, 2, 4)
CALIBRATION_CONTROLS = 12
THRESHOLD_MULTIPLIERS = (1, 2, 4)
THRESHOLD_KEYS = ("disagreement_threshold", "balance_threshold", "actuator_threshold")
CALIBRATION_METHOD = (
    "For each detector and noise level, multiply each amplitude threshold by the same candidate "
    "factor. Select the smallest factor with zero alarms across the calibration "
    "controls. If every candidate alarms, use the largest factor and flag the unmet target. "
    "The confirmation count stays fixed. Both policies share evaluation seeds and fault timings. "
    "Calibration uses separate noise streams and sees only no-fault runs."
)
RUN_COLUMNS = (
    "mode", "replicate", "noise_seed", "noise_multiplier", "sensor_noise_sd",
    "actuator_noise_sd", "template_index", "fault_kind", "magnitude", "start", "end",
    "first_alarm", "control_first_alarm", "outcome", "detection_delay",
)


def _schedules(templates, times, step, seed, replicates):
    """Shuffle eligible grid starts without replacement before recycling a grid."""
    last = len(times) - 1
    if abs(times[-1] / step - last) > 1e-9:
        last -= 1  # A shortened terminal interval cannot complete a full grid step.
    source_starts = {round(fault["start"] / step) for fault in templates}
    schedules = [[] for _ in range(replicates)]
    for index, fault in enumerate(templates):
        width = round(fault["end"] / step) - round(fault["start"] / step)
        starts = [i for i in range(1, last - width + 1) if i not in source_starts]
        if width < 1 or not starts:
            raise InputError(f"Fault template {index + 1} has no eligible held-out grid window")
        rng = random.Random(f"fault-benchmark-onsets/{seed}/{index}")
        for run, events in enumerate(schedules):
            position = run % len(starts)
            if position == 0:
                rng.shuffle(starts)
            start = starts[position]
            events.append({**fault, "start": times[start], "end": times[start + width]})
    return schedules


def _score_event(first_alarm, control_alarm, start, end):
    if first_alarm is None:
        return "no_alarm", None
    if first_alarm < start:
        return "pre_fault_alarm", None
    if first_alarm > end:
        return "late_alarm", None
    if control_alarm is not None and control_alarm <= first_alarm:
        return "control_as_early", None
    return "detected", first_alarm - start


def _first_alarm(variant, shared, grid, mode, experiment, faults):
    _, observations = _fault_run("synthetic", variant, shared, *grid, mode, experiment, faults)
    return next((row["dimensionless_time"] for row in observations if row["fault_detected"]), None)


def _scale_thresholds(experiment, factor):
    return {**experiment, **{key: experiment[key] * factor for key in THRESHOLD_KEYS}}


def _noise_inputs(common, monitor_faults, start_seed, count):
    return [(seed, (*common, seed, monitor_faults)) for seed in range(start_seed, start_seed + 4 * count, 4)]


def _calibrate(variant, grid, mode, experiment, calibration_inputs, noise_multiplier):
    """Select from a fixed grid using only no-fault controls with identical noise per candidate."""
    records = []
    quiet_factors = []
    for factor in THRESHOLD_MULTIPLIERS:
        candidate = _scale_thresholds(experiment, factor)
        alarms = 0
        for seed, shared in calibration_inputs:
            alarm = _first_alarm(variant, shared, grid, mode, candidate, [])
            alarms += alarm is not None
            records.append({"mode": mode, "noise_multiplier": noise_multiplier, "noise_seed": seed,
                            "threshold_multiplier": factor, "first_alarm": alarm})
        if alarms == 0:
            quiet_factors.append(factor)
    # If the entire grid alarms, evaluate its upper bound and report the missed target.
    selected = min(quiet_factors) if quiet_factors else max(THRESHOLD_MULTIPLIERS)
    return {"threshold_policy": "calibrated", "threshold_multiplier": selected,
            "calibration_target_met": bool(quiet_factors)}, records


def _paired_runs(events, variant, shared, grid, mode, experiment, labels):
    control = _first_alarm(variant, shared, grid, mode, experiment, [])
    rows = [{**labels, "template_index": None, "fault_kind": "none",
             "first_alarm": control, "control_first_alarm": control,
             "outcome": "quiet" if control is None else "false_alarm"}]
    for index, event in enumerate(events, start=1):
        alarm = _first_alarm(variant, shared, grid, mode, experiment, [event])
        outcome, delay = _score_event(alarm, control, event["start"], event["end"])
        rows.append({**labels, "template_index": index, "fault_kind": event["kind"],
                     "magnitude": event["magnitude"], "start": event["start"], "end": event["end"],
                     "first_alarm": alarm, "control_first_alarm": control,
                     "outcome": outcome, "detection_delay": delay})
    return rows


def _evaluate_policy(variant, grid, experiment, schedules, inputs, labels):
    settings = _scale_thresholds(experiment, labels.get("threshold_multiplier", 1))
    rows = []
    for replicate, ((seed, shared), events) in enumerate(zip(inputs, schedules), start=1):
        run_labels = {**labels, "replicate": replicate, "noise_seed": seed}
        rows.extend(_paired_runs(events, variant, shared, grid, labels["mode"], settings, run_labels))
    return rows


def _event_metrics(events):
    delays = [row["detection_delay"] for row in events if row["outcome"] == "detected"]
    return {"events": len(events), "detected": len(delays), "missed": len(events) - len(delays),
            "median_detection_delay": median(delays) if delays else None,
            "outcomes": dict(Counter(row["outcome"] for row in events))}


def _summarize(rows, mode, multiplier):
    controls = [row for row in rows if row["fault_kind"] == "none"]
    events = [row for row in rows if row["fault_kind"] != "none"]
    kinds = sorted({row["fault_kind"] for row in events})
    return {"mode": mode, "noise_multiplier": multiplier, "control_runs": len(controls),
            "false_alarm_controls": sum(row["outcome"] == "false_alarm" for row in controls),
            **_event_metrics(events),
            "by_fault_kind": {kind: _event_metrics([row for row in events if row["fault_kind"] == kind])
                              for kind in kinds}}


def _markdown_report(report):
    lines = ["# Paired fault detector benchmark", "", NOTICE, "", report["scoring"], ""]
    if "calibration" in report:
        fit = report["calibration"]
        factors = ", ".join(map(str, fit["candidate_multipliers"]))
        lines.extend([fit["method"], "",
                      f"Candidate factors were {factors}, with {fit['controls_per_candidate']} controls per candidate.", ""])
    lines.extend(["| Noise multiplier | Detector | Detected / events | Missed | False alarms / controls | Median delay |",
                  "|---:|---|---:|---:|---:|---:|"])
    for row in report["conditions"]:
        detector = row["mode"]
        if "threshold_policy" in row:
            detector += f" ({row['threshold_policy']}, {row['threshold_multiplier']}× thresholds)"
            if row.get("calibration_target_met") is False:
                detector += " — calibration target missed"
        delay = row["median_detection_delay"]
        lines.append(f"| {row['noise_multiplier']} | {detector} | {row['detected']} / {row['events']} "
                     f"| {row['missed']} | {row['false_alarm_controls']} / {row['control_runs']} "
                     f"| {delay if delay is not None else 'n/a'} |")
    return ("\n".join(lines) + "\n").encode()


def benchmark_fault_detectors(config_path: Path, output: Path, *, replicates=DEFAULT_REPLICATES,
                             calibrate_thresholds=False) -> dict:
    if type(replicates) is not int or not 1 <= replicates <= MAX_REPLICATES:
        raise InputError(f"replicates must be an integer in [1, {MAX_REPLICATES}]")
    if type(calibrate_thresholds) is not bool:
        raise InputError("calibrate_thresholds must be a boolean")
    config, raw = read_json(config_path)
    parsed, experiment, templates = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, variants, _) = parsed
    if "synthetic" not in variants or not templates:
        raise InputError("The benchmark requires the synthetic variant and at least one control fault")
    variant = variants["synthetic"]
    modes = MODES[1:]  # The single-sensor baseline has no alarm.
    times = output_times(duration, step)
    grid = (duration, step, boundaries)
    conditions = len(NOISE_MULTIPLIERS) * len(modes)
    n_evaluation = replicates * conditions * (1 + len(templates)) * (2 if calibrate_thresholds else 1)
    n_calibration = conditions * CALIBRATION_CONTROLS * len(THRESHOLD_MULTIPLIERS) if calibrate_thresholds else 0
    n_runs = n_evaluation + n_calibration
    rate = _integration_rate(variant, bulk, internal, control, reserve)
    # Allow for grid rounding, both outage edges and a reserve depletion per outage.
    per_run = (len(times) - 1) * (1 + math.ceil(step * rate / SUBSTEP_RATE_TARGET)) + 3 * len(outages)
    if n_runs * per_run > MAX_BENCHMARK_SUBSTEPS:
        raise InputError(f"Benchmark exceeds the {MAX_BENCHMARK_SUBSTEPS}-substep work budget")

    schedule_seed = f"threshold-comparison/{seed}" if calibrate_thresholds else seed
    schedules = _schedules(templates, times, step, schedule_seed, replicates)
    # Random accepts negative integer seeds by absolute value. Reserve four new
    # streams per replicate beyond every stream used by the reference fixture.
    first_seed = max(abs(seed + offset) for offset in range(4)) + 1
    # Keep all four streams of every calibration and evaluation seed disjoint from
    # each other and from even the largest original fixed-threshold benchmark.
    calibration_start = first_seed + 4 * MAX_REPLICATES
    evaluation_start = calibration_start + 4 * CALIBRATION_CONTROLS if calibrate_thresholds else first_seed
    all_rows, summaries, calibration_rows = [], [], []
    for multiplier in NOISE_MULTIPLIERS:
        sensor_sd = noise_sd * multiplier
        actuator_sd = experiment["actuator_noise_sd"] * multiplier
        scaled = {**experiment, "actuator_noise_sd": actuator_sd}
        common = (growth, scaling, bulk, internal, control, reserve, outages, cadence, sensor_sd)
        evaluation_inputs = _noise_inputs(common, monitor_faults, evaluation_start, replicates)
        for mode in modes:
            if calibrate_thresholds:
                calibration_inputs = _noise_inputs(common, monitor_faults, calibration_start, CALIBRATION_CONTROLS)
                fitted, records = _calibrate(variant, grid, mode, scaled, calibration_inputs, multiplier)
                calibration_rows.extend(records)
                policies = [{"threshold_policy": "fixed", "threshold_multiplier": 1}, fitted]
            else:
                policies = [{}]  # Preserve the original fixed-only report and CSV schema.
            for policy in policies:
                labels = {"mode": mode, "noise_multiplier": multiplier, "sensor_noise_sd": sensor_sd,
                          "actuator_noise_sd": actuator_sd, **policy}
                rows = _evaluate_policy(variant, grid, scaled, schedules, evaluation_inputs, labels)
                all_rows.extend(rows)
                summaries.append({**_summarize(rows, mode, multiplier), **policy})

    metadata = {"replicates": replicates, "variant": "synthetic", "biological_measurements": False,
                "physiologically_calibrated": False, "human_gestation_prediction": False}
    scoring = (
        "Each injected event is a separate run. A detection requires the first confirmation "
        "inside the inclusive fault window and strictly before any confirmation in its paired "
        "control. All other events count as missed. Delay is measured from onset to confirmation "
        "in dimensionless time and summarized only for detections. Each control with any "
        "confirmation counts as one false alarm."
    )
    report = {"schema_version": 1, "fixture_notice": NOTICE, **metadata, "scoring": scoring,
              "simulation_runs": n_runs, "noise_multipliers": list(NOISE_MULTIPLIERS),
              "thresholds": {key: experiment[key] for key in (*THRESHOLD_KEYS, "confirmation_samples")},
              "conditions": summaries}
    columns = list(RUN_COLUMNS)
    files = {"source_config.json": raw}
    if calibrate_thresholds:
        metadata["calibrate_thresholds"] = True
        report.update(schema_version=2, evaluation_runs=n_evaluation, calibration_runs=n_calibration,
                      calibration={"method": CALIBRATION_METHOD, "controls_per_candidate": CALIBRATION_CONTROLS,
                                   "candidate_multipliers": list(THRESHOLD_MULTIPLIERS)})
        columns.extend(("threshold_policy", "threshold_multiplier", "calibration_target_met"))
        files["calibration_runs.csv"] = csv_bytes(
            ["mode", "noise_multiplier", "noise_seed", "threshold_multiplier", "first_alarm"], calibration_rows)
    files.update({"benchmark_runs.csv": csv_bytes(columns, all_rows), "benchmark_report.json": json_bytes(report),
                  "REPORT.md": _markdown_report(report)})
    return publish_bundle(output, kind="dimensionless_fault_detector_benchmark", input_raw=raw,
                          files=files, metadata=metadata)
