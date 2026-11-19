"""Paired first-alarm evaluation of the frozen common-cause fault detectors."""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
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
ACTUATOR_COMPARISON_METHOD = (
    "Fit a shared multiplier for all three thresholds on no-fault controls. Hold both sensor "
    "thresholds at that fit and try each actuator multiplier on the same controls. Each stage "
    "uses the complete balance-augmented detector and selects the smallest candidate with zero "
    "alarms, or the largest candidate if all alarm. Evaluate both fits on the same fresh noise "
    "streams and fault timings. The confirmation count stays fixed."
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


def _scale_thresholds(experiment, policy):
    sensor = policy.get("sensor_threshold_multiplier", policy.get("threshold_multiplier", 1))
    actuator = policy.get("actuator_threshold_multiplier", sensor)
    return {**experiment,
            "disagreement_threshold": experiment["disagreement_threshold"] * sensor,
            "balance_threshold": experiment["balance_threshold"] * sensor,
            "actuator_threshold": experiment["actuator_threshold"] * actuator}


def _noise_inputs(common, monitor_faults, start_seed, count):
    return [(seed, (*common, seed, monitor_faults)) for seed in range(start_seed, start_seed + 4 * count, 4)]


def _calibrate(variant, grid, mode, experiment, calibration_inputs, noise_multiplier, candidates):
    """Test an ascending grid on matched no-fault controls, retaining the first quiet candidate."""
    records = []
    selected = None
    for candidate in candidates:
        settings = _scale_thresholds(experiment, candidate)
        alarms = 0
        for seed, shared in calibration_inputs:
            alarm = _first_alarm(variant, shared, grid, mode, settings, [])
            alarms += alarm is not None
            records.append({"mode": mode, "noise_multiplier": noise_multiplier, "noise_seed": seed,
                            **candidate, "first_alarm": alarm})
        if alarms == 0 and selected is None:
            selected = candidate
    return {**(selected or candidates[-1]), "calibration_target_met": selected is not None}, records


def _fit_policies(variant, grid, mode, experiment, inputs, noise_multiplier, compare_actuator):
    def fit(candidates):
        return _calibrate(variant, grid, mode, experiment, inputs, noise_multiplier, candidates)

    if not compare_actuator:
        calibrated, records = fit([{"threshold_multiplier": factor} for factor in THRESHOLD_MULTIPLIERS])
        return [{"threshold_policy": "fixed", "threshold_multiplier": 1},
                {"threshold_policy": "calibrated", **calibrated}], records

    shared, records = fit([{"threshold_policy": "shared", "sensor_threshold_multiplier": factor,
                            "actuator_threshold_multiplier": factor} for factor in THRESHOLD_MULTIPLIERS])
    separate, actuator_records = fit([
        {"threshold_policy": "separate_actuator", "sensor_threshold_multiplier": shared["sensor_threshold_multiplier"],
         "actuator_threshold_multiplier": factor} for factor in THRESHOLD_MULTIPLIERS])
    return [shared, separate], records + actuator_records


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
    settings = _scale_thresholds(experiment, labels)
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


def _paired_outcomes(rows):
    """Count gains and losses on identical challenges, including matched control alarms."""
    pairs = defaultdict(dict)
    for row in rows:
        key = (row["noise_multiplier"], row["fault_kind"], row["noise_seed"], row["template_index"],
               row.get("start"), row.get("end"), row.get("magnitude"))
        target = "false_alarm" if row["fault_kind"] == "none" else "detected"
        pairs[key][row["threshold_policy"]] = row["outcome"] == target
    categories = {(True, True): "both", (True, False): "shared_only",
                  (False, True): "separate_actuator_only", (False, False): "neither"}
    groups = defaultdict(Counter)
    for (noise, kind, *_), outcomes in pairs.items():
        category = categories[outcomes["shared"], outcomes["separate_actuator"]]
        groups[noise, kind][category] += 1
    return [{"noise_multiplier": noise, "fault_kind": kind,
             "counted_outcome": "false_alarm" if kind == "none" else "detected",
             **{name: counts[name] for name in categories.values()}}
            for (noise, kind), counts in sorted(groups.items())]


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
        if "actuator_threshold_multiplier" in row:
            detector += (f" ({row['threshold_policy']}, sensors {row['sensor_threshold_multiplier']}×, "
                         f"actuator {row['actuator_threshold_multiplier']}×)")
        elif "threshold_policy" in row:
            detector += f" ({row['threshold_policy']}, {row['threshold_multiplier']}× thresholds)"
        if row.get("calibration_target_met") is False:
            detector += " — calibration target missed"
        delay = row["median_detection_delay"]
        lines.append(f"| {row['noise_multiplier']} | {detector} | {row['detected']} / {row['events']} "
                     f"| {row['missed']} | {row['false_alarm_controls']} / {row['control_runs']} "
                     f"| {delay if delay is not None else 'n/a'} |")
    if "paired_outcomes" in report:
        lines.extend(["", "## Outcomes on matched runs", "",
                      "Fault rows count credited detections. No-fault control rows count false alarms.", "",
                      "| Noise multiplier | Challenge | Both | Shared only | Separate actuator only | Neither |",
                      "|---:|---|---:|---:|---:|---:|"])
        for pair in report["paired_outcomes"]:
            kind = pair["fault_kind"]
            label = "No-fault control" if kind == "none" else kind.replace("_", " ")
            lines.append(f"| {pair['noise_multiplier']} | {label} | {pair['both']} | {pair['shared_only']} "
                         f"| {pair['separate_actuator_only']} | {pair['neither']} |")
    return ("\n".join(lines) + "\n").encode()


def benchmark_fault_detectors(config_path: Path, output: Path, *, replicates=DEFAULT_REPLICATES,
                             calibrate_thresholds=False, compare_actuator_thresholds=False) -> dict:
    if type(replicates) is not int or not 1 <= replicates <= MAX_REPLICATES:
        raise InputError(f"replicates must be an integer in [1, {MAX_REPLICATES}]")
    if type(calibrate_thresholds) is not bool:
        raise InputError("calibrate_thresholds must be a boolean")
    if type(compare_actuator_thresholds) is not bool:
        raise InputError("compare_actuator_thresholds must be a boolean")
    if calibrate_thresholds and compare_actuator_thresholds:
        raise InputError("Choose one threshold comparison per benchmark")
    fitting = calibrate_thresholds or compare_actuator_thresholds
    config, raw = read_json(config_path)
    parsed, experiment, templates = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, variants, _) = parsed
    if "synthetic" not in variants or not templates:
        raise InputError("The benchmark requires the synthetic variant and at least one control fault")
    variant = variants["synthetic"]
    # Only the balance-augmented detector uses the actuator meter.
    modes = ("balance_augmented_freeze",) if compare_actuator_thresholds else MODES[1:]
    times = output_times(duration, step)
    grid = (duration, step, boundaries)
    conditions = len(NOISE_MULTIPLIERS) * len(modes)
    n_evaluation = replicates * conditions * (1 + len(templates)) * (2 if fitting else 1)
    calibration_stages = 2 if compare_actuator_thresholds else int(calibrate_thresholds)
    n_calibration = conditions * CALIBRATION_CONTROLS * len(THRESHOLD_MULTIPLIERS) * calibration_stages
    n_runs = n_evaluation + n_calibration
    rate = _integration_rate(variant, bulk, internal, control, reserve)
    # Allow for grid rounding, both outage edges and a reserve depletion per outage.
    per_run = (len(times) - 1) * (1 + math.ceil(step * rate / SUBSTEP_RATE_TARGET)) + 3 * len(outages)
    if n_runs * per_run > MAX_BENCHMARK_SUBSTEPS:
        raise InputError(f"Benchmark exceeds the {MAX_BENCHMARK_SUBSTEPS}-substep work budget")

    # Random accepts negative integer seeds by absolute value. Reserve four new
    # streams per replicate beyond every stream used by the reference fixture.
    first_seed = max(abs(seed + offset) for offset in range(4)) + 1
    # Keep all four streams of every calibration and evaluation seed disjoint from
    # each other and from even the largest original fixed-threshold benchmark.
    calibration_start = first_seed + 4 * MAX_REPLICATES
    evaluation_start = calibration_start + 4 * CALIBRATION_CONTROLS if fitting else first_seed
    schedule_seed = f"threshold-comparison/{seed}" if fitting else seed
    if compare_actuator_thresholds:
        # Refit on the original controls and reserve a third evaluation block
        # beyond all streams available to the preceding shared-threshold comparison.
        evaluation_start += 4 * MAX_REPLICATES
        schedule_seed = f"actuator-comparison/{seed}"
    schedules = _schedules(templates, times, step, schedule_seed, replicates)
    all_rows, summaries, calibration_rows = [], [], []
    for multiplier in NOISE_MULTIPLIERS:
        sensor_sd = noise_sd * multiplier
        actuator_sd = experiment["actuator_noise_sd"] * multiplier
        scaled = {**experiment, "actuator_noise_sd": actuator_sd}
        common = (growth, scaling, bulk, internal, control, reserve, outages, cadence, sensor_sd)
        evaluation_inputs = _noise_inputs(common, monitor_faults, evaluation_start, replicates)
        for mode in modes:
            if fitting:
                calibration_inputs = _noise_inputs(common, monitor_faults, calibration_start, CALIBRATION_CONTROLS)
                policies, records = _fit_policies(variant, grid, mode, scaled, calibration_inputs,
                                                  multiplier, compare_actuator_thresholds)
                calibration_rows.extend(records)
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
    if fitting:
        if compare_actuator_thresholds:
            metadata["compare_actuator_thresholds"] = True
            report["paired_outcomes"] = _paired_outcomes(all_rows)
            factors = ["sensor_threshold_multiplier", "actuator_threshold_multiplier"]
            fit_columns = ["threshold_policy", *factors]
            method = ACTUATOR_COMPARISON_METHOD
        else:
            metadata["calibrate_thresholds"] = True
            factors = fit_columns = ["threshold_multiplier"]
            method = CALIBRATION_METHOD
        report.update(schema_version=3 if compare_actuator_thresholds else 2,
                      evaluation_runs=n_evaluation, calibration_runs=n_calibration,
                      calibration={"method": method, "controls_per_candidate": CALIBRATION_CONTROLS,
                                   "candidate_multipliers": list(THRESHOLD_MULTIPLIERS)})
        columns.extend(("threshold_policy", *factors, "calibration_target_met"))
        files["calibration_runs.csv"] = csv_bytes(
            ["mode", "noise_multiplier", "noise_seed", *fit_columns, "first_alarm"], calibration_rows)
    files.update({"benchmark_runs.csv": csv_bytes(columns, all_rows), "benchmark_report.json": json_bytes(report),
                  "REPORT.md": _markdown_report(report)})
    return publish_bundle(output, kind="dimensionless_fault_detector_benchmark", input_raw=raw,
                          files=files, metadata=metadata)
