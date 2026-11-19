"""Replay an Exa-informed alarm confirmation comparison on the simulated fixture."""

import argparse
import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile

from wombmodels.common_cause_fault import _fault_run, _validate_experiment
from wombmodels.fault_benchmark import _scale_thresholds, _schedules, _score_event
from wombmodels.numerics import output_times


POLICIES = ("current", "separate_two", "separate_three")
NOISE_MULTIPLIER = 4
REPLICATES = 512


def first_alarms(observations):
    alarms = dict.fromkeys(POLICIES)
    combined_streak = sensor_streak = actuator_streak = 0
    for row in observations:
        sensor = row["disagreement_triggered"] or row["balance_triggered"]
        actuator = row["actuator_triggered"]
        combined_streak = combined_streak + 1 if sensor or actuator else 0
        sensor_streak = sensor_streak + 1 if sensor else 0
        actuator_streak = actuator_streak + 1 if actuator else 0
        confirmations = (combined_streak >= 2, sensor_streak >= 2 or actuator_streak >= 2,
                         sensor_streak >= 2 or actuator_streak >= 3)
        for policy, confirmed in zip(POLICIES, confirmations):
            if confirmed and alarms[policy] is None:
                alarms[policy] = row["dimensionless_time"]
    return alarms


def read_bundle(path):
    with ZipFile(path) as bundle:
        prefix = f"{path.stem}/"
        config = json.loads(bundle.read(prefix + "source_config.json"))
        csv_text = bundle.read(prefix + "benchmark_runs.csv").decode("utf-8")
        return config, list(csv.DictReader(io.StringIO(csv_text)))


def parse_event(record):
    if record["fault_kind"] == "none":
        return None
    return {"kind": record["fault_kind"],
            **{key: float(record[key]) for key in ("start", "end", "magnitude")}}


def evaluate(config, prior_runs):
    parsed, experiment, templates = _validate_experiment(config)
    (duration, step, boundaries, growth, scaling, bulk, internal, control, reserve,
     outages, cadence, sensor_noise, fixture_seed, monitor_faults, variants, _) = parsed
    original = [row for row in prior_runs if int(row["noise_multiplier"]) == NOISE_MULTIPLIER
                and row["threshold_policy"] == "separate_actuator"]
    if len(original) != 128 or experiment["confirmation_samples"] != 2:
        raise ValueError("Expected the published 4× noise comparison with two-sample confirmation")

    settings = _scale_thresholds(
        {**experiment, "actuator_noise_sd": experiment["actuator_noise_sd"] * NOISE_MULTIPLIER},
        {key: int(original[0][key]) for key in
         ("sensor_threshold_multiplier", "actuator_threshold_multiplier")},
    )
    common = (growth, scaling, bulk, internal, control, reserve, outages, cadence,
              sensor_noise * NOISE_MULTIPLIER)

    def simulate(seed, event):
        faults = [] if event is None else [event]
        # The first alarm depends only on samples before fallback changes the trajectory.
        # With fallback disabled, the simulator exposes that common prefix for every policy.
        _, samples = _fault_run(
            "synthetic", variants["synthetic"], (*common, seed, monitor_faults),
            duration, step, boundaries, "single_sensor", settings, faults,
        )
        return first_alarms(samples)

    for row in original:
        expected = float(row["first_alarm"]) if row["first_alarm"] else None
        alarms = simulate(int(row["noise_seed"]), parse_event(row))
        if alarms["current"] != expected:
            raise ValueError(f"Published first alarm differs at seed {row['noise_seed']}")

    first_seed = max(int(row["noise_seed"]) for row in prior_runs) + 4
    schedule = _schedules(templates, output_times(duration, step), step,
                          f"confirmation-comparison/{fixture_seed}", REPLICATES)
    for replicate, events in enumerate(schedule, start=1):
        seed = first_seed + 4 * (replicate - 1)
        control_alarms = simulate(seed, None)
        for event in [None, *events]:
            record = {"replicate": replicate, "noise_seed": seed,
                      "fault_kind": event["kind"] if event else "none",
                      **{key: event[key] if event else None for key in ("magnitude", "start", "end")}}
            alarms = simulate(seed, event) if event else control_alarms
            for policy, alarm in alarms.items():
                if event:
                    outcome, delay = _score_event(alarm, control_alarms[policy],
                                                  event["start"], event["end"])
                else:
                    outcome, delay = ("quiet" if alarm is None else "false_alarm"), None
                record[f"{policy}_first_alarm"] = alarm
                record[f"{policy}_outcome"] = outcome
                record[f"{policy}_delay"] = delay
            yield record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="The published actuator-thresholds-83856bd.zip")
    parser.add_argument("output", type=Path, help="A new path for the held-out run CSV")
    args = parser.parse_args()
    rows = list(evaluate(*read_bundle(args.bundle)))
    with args.output.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
