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


def _paired_runs(events, variant, shared, grid, mode, experiment, labels):
    def first_alarm(faults):
        _, observations = _fault_run("synthetic", variant, shared, *grid, mode, experiment, faults)
        return next((row["dimensionless_time"] for row in observations if row["fault_detected"]), None)

    control = first_alarm([])
    rows = [{**labels, "template_index": None, "fault_kind": "none",
             "first_alarm": control, "control_first_alarm": control,
             "outcome": "quiet" if control is None else "false_alarm"}]
    for index, event in enumerate(events, start=1):
        alarm = first_alarm([event])
        outcome, delay = _score_event(alarm, control, event["start"], event["end"])
        rows.append({**labels, "template_index": index, "fault_kind": event["kind"],
                     "magnitude": event["magnitude"], "start": event["start"], "end": event["end"],
                     "first_alarm": alarm, "control_first_alarm": control,
                     "outcome": outcome, "detection_delay": delay})
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


def benchmark_fault_detectors(config_path: Path, output: Path, *, replicates=DEFAULT_REPLICATES) -> dict:
    if type(replicates) is not int or not 1 <= replicates <= MAX_REPLICATES:
        raise InputError(f"replicates must be an integer in [1, {MAX_REPLICATES}]")
    config, raw = read_json(config_path)
    parsed, experiment, templates = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control,
     reserve, outages, cadence, noise_sd, seed, monitor_faults, variants, _) = parsed
    if "synthetic" not in variants or not templates:
        raise InputError("The benchmark requires the synthetic variant and at least one control fault")
    variant = variants["synthetic"]
    modes = MODES[1:]  # The single-sensor baseline has no alarm.
    times = output_times(duration, step)
    n_runs = replicates * len(NOISE_MULTIPLIERS) * len(modes) * (1 + len(templates))
    rate = _integration_rate(variant, bulk, internal, control, reserve)
    # Allow for grid rounding, both outage edges and a reserve depletion per outage.
    per_run = (len(times) - 1) * (1 + math.ceil(step * rate / SUBSTEP_RATE_TARGET)) + 3 * len(outages)
    if n_runs * per_run > MAX_BENCHMARK_SUBSTEPS:
        raise InputError(f"Benchmark exceeds the {MAX_BENCHMARK_SUBSTEPS}-substep work budget")

    schedules = _schedules(templates, times, step, seed, replicates)
    # Random accepts negative integer seeds by absolute value. Reserve four new
    # streams per replicate beyond every stream used by the reference fixture.
    first_seed = max(abs(seed + offset) for offset in range(4)) + 1
    all_rows, summaries = [], []
    for multiplier in NOISE_MULTIPLIERS:
        sensor_sd = noise_sd * multiplier
        actuator_sd = experiment["actuator_noise_sd"] * multiplier
        scaled = {**experiment, "actuator_noise_sd": actuator_sd}
        for mode in modes:
            rows = []
            for replicate, events in enumerate(schedules, start=1):
                run_seed = first_seed + 4 * (replicate - 1)
                shared = (growth, scaling, bulk, internal, control, reserve, outages,
                          cadence, sensor_sd, run_seed, monitor_faults)
                labels = {"mode": mode, "replicate": replicate, "noise_seed": run_seed,
                          "noise_multiplier": multiplier, "sensor_noise_sd": sensor_sd,
                          "actuator_noise_sd": actuator_sd}
                rows.extend(_paired_runs(events, variant, shared, (duration, step, boundaries),
                                         mode, scaled, labels))
            all_rows.extend(rows)
            summaries.append(_summarize(rows, mode, multiplier))

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
              "thresholds": {key: experiment[key] for key in (
                  "disagreement_threshold", "balance_threshold", "actuator_threshold", "confirmation_samples")},
              "conditions": summaries}
    lines = ["# Paired fault detector benchmark", "", NOTICE, "", scoring, "",
             "| Noise multiplier | Detector | Detected / events | Missed | False alarms / controls | Median delay |",
             "|---:|---|---:|---:|---:|---:|"]
    for row in summaries:
        delay = row["median_detection_delay"]
        lines.append(f"| {row['noise_multiplier']} | {row['mode']} | {row['detected']} / {row['events']} "
                     f"| {row['missed']} | {row['false_alarm_controls']} / {row['control_runs']} "
                     f"| {delay if delay is not None else 'n/a'} |")
    files = {"source_config.json": raw, "benchmark_runs.csv": csv_bytes(list(RUN_COLUMNS), all_rows),
             "benchmark_report.json": json_bytes(report), "REPORT.md": ("\n".join(lines) + "\n").encode()}
    return publish_bundle(output, kind="dimensionless_fault_detector_benchmark", input_raw=raw,
                          files=files, metadata=metadata)
