"""Stress test actuator confirmation with correlated meter noise and short offsets."""

import argparse
import csv
import hashlib
import random
from math import sqrt
from pathlib import Path

from replay import first_alarms, parse_event, read_bundle
from wombmodels.common_cause_fault import _fault_run, _validate_experiment
from wombmodels.fault_benchmark import _scale_thresholds, _schedules, _score_event
from wombmodels.numerics import output_times


SOURCE_SHA256 = "aacf3d4c98d718c5585519c691842a6b04df16f6229b9a6f6822062e694af239"
CORRELATIONS = (0.0, 0.5, 0.9)
DURATIONS = (0.5, 1.0, 3.0)
FIRST_SEED = 20263501
REPLICATES = 512


def meter_noise(innovations, correlation):
    """Start a Gaussian AR(1) stream with the innovation's marginal variance."""
    values = [innovations[0]]
    scale = sqrt(1 - correlation ** 2)
    for innovation in innovations[1:]:
        values.append(correlation * values[-1] + scale * innovation)
    return values


def measure_alarms(observations, noise, threshold):
    records = []
    for row, error in zip(observations, noise, strict=True):
        metered = row["delivered_supplement"] + error
        residual = abs(metered - row["commanded_supplement"])
        records.append({**row, "actuator_triggered": residual > threshold})
    return first_alarms(records)


def evaluate(config, prior_runs):
    parsed, experiment, templates = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control, reserve,
     outages, cadence, sensor_noise, fixture_seed, monitor_faults, variants, _) = parsed
    times = output_times(duration, step)
    original = [row for row in prior_runs if row["noise_multiplier"] == "4"
                and row["threshold_policy"] == "separate_actuator"]
    multipliers = {key: int(original[0][key]) for key in
                   ("sensor_threshold_multiplier", "actuator_threshold_multiplier")}
    settings = _scale_thresholds({**experiment, "actuator_noise_sd": 0.0}, multipliers)
    meter_sd = 4 * experiment["actuator_noise_sd"]
    common = (growth, scaling, bulk, internal, control, reserve, outages, cadence, 4 * sensor_noise)

    def samples(seed, event):
        # Measure under the trajectory shared by all policies until their own first alarm.
        _, observations = _fault_run(
            "synthetic", variants["synthetic"], (*common, seed, monitor_faults),
            duration, step, boundaries, "single_sensor", settings, [] if event is None else [event],
        )
        return observations

    def draws(seed):
        rng = random.Random(seed + 3)
        return [rng.gauss(0.0, meter_sd) for _ in times]

    for row in original:
        seed = int(row["noise_seed"])
        alarm = measure_alarms(samples(seed, parse_event(row)), draws(seed),
                               settings["actuator_threshold"])["current"]
        expected = float(row["first_alarm"]) if row["first_alarm"] else None
        if alarm != expected:
            raise ValueError(f"Independent-noise first alarm differs at seed {seed}")

    schedule = _schedules(templates, times, step, f"meter-persistence/{fixture_seed}", REPLICATES)
    for index, events in enumerate(schedule):
        seed = FIRST_SEED + 4 * index
        original_offset = next(event for event in events if event["kind"] == "actuator_offset")
        onset = original_offset["start"]
        events = [None, *({**original_offset, "end": onset + width} for width in DURATIONS)]
        traces = [samples(seed, event) for event in events]
        innovations = draws(seed)
        for rho in CORRELATIONS:
            noise = meter_noise(innovations, rho)
            control_alarms = measure_alarms(traces[0], noise, settings["actuator_threshold"])
            for event, observations in zip(events, traces, strict=True):
                record = {"seed": seed, "rho": rho, "case": "control" if event is None else "offset",
                          "duration": None if event is None else event["end"] - onset,
                          "start": None if event is None else onset,
                          "end": None if event is None else event["end"]}
                alarms = control_alarms if event is None else measure_alarms(
                    observations, noise, settings["actuator_threshold"],
                )
                for rule, alarm in alarms.items():
                    if event is None:
                        outcome, delay = ("quiet" if alarm is None else "false_alarm"), None
                    else:
                        outcome, delay = _score_event(alarm, control_alarms[rule], onset, event["end"])
                    record[f"{rule}_alarm"] = alarm
                    record[f"{rule}_outcome"] = outcome
                    record[f"{rule}_delay"] = delay
                yield record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.bundle.read_bytes()).hexdigest() != SOURCE_SHA256:
        parser.error("use the published actuator-thresholds-83856bd.zip")
    records = list(evaluate(*read_bundle(args.bundle)))
    with args.output.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    main()
