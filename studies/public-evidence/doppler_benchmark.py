"""Score empirical phase templates on participant-held-out public S2 Doppler traces."""

import argparse
import hashlib
import json
import math
from bisect import bisect_right
from pathlib import Path
from statistics import mean, median

from audit import HERE, read_doppler, table


PHASE_INTERVALS = 200
SITES = (
    "Aortic Isthmus", "Aortic Valve", "Ductus Arteriosus",
    "Middle Cerebral Artery", "Mitral Valve", "Pulmonary Valve",
    "Tricuspid Valve", "Umbilical Artery",
)


def phase_points(times, velocities):
    points = []
    for time, velocity in zip(times, velocities, strict=True):
        if points and time <= points[-1][0]:
            last_time, last_velocity = points[-1]
            if time < last_time or abs(velocity - last_velocity) > 1e-10:
                raise ValueError("Time goes backwards or duplicate velocities disagree")
            continue
        points.append((time, velocity))
    if len(points) < 2:
        raise ValueError("Trace must span a positive duration")
    xs, ys = zip(*points)
    duration = xs[-1] - xs[0]
    phase = [(time - xs[0]) / duration for time in xs]
    return phase, ys


def interpolate(phase, values, position):
    if position == phase[-1]:
        return values[-1]
    right = bisect_right(phase, position)
    fraction = (position - phase[right - 1]) / (phase[right] - phase[right - 1])
    return values[right - 1] + fraction * (values[right] - values[right - 1])


def phase_samples(times, velocities):
    phase, values = phase_points(times, velocities)
    samples = [interpolate(phase, values, step / PHASE_INTERVALS) for step in range(PHASE_INTERVALS + 1)]
    return samples, len(times) - len(phase)


def phase_mean(values):
    return math.fsum([values[0] / 2, *values[1:-1], values[-1] / 2]) / PHASE_INTERVALS


def score_folds(traces):
    """Every site from the withheld participant stays outside template fitting."""
    scores = {}
    for held_out in traces:
        training = [sites for case, sites in traces.items() if case != held_out]
        scores[held_out] = {}
        for site, observed in traces[held_out].items():
            template = list(map(mean, zip(*(sites[site] for sites in training), strict=True)))
            flat = phase_mean(template)
            differences = [actual - expected for actual, expected in zip(observed, template, strict=True)]
            scores[held_out][site] = {
                "mae": phase_mean(list(map(abs, differences))),
                "rmse": math.sqrt(phase_mean([value**2 for value in differences])),
                "flat_rmse": math.sqrt(phase_mean([(value - flat)**2 for value in observed])),
                "peak_error": abs(max(observed) - max(template)),
            }
    return scores


def checked_traces(source):
    manifest = (HERE / "inputs.json").read_bytes()
    entry = next(item for item in json.loads(manifest) if item["file"] == "Dataset_S2.csv")
    if source.stat().st_size != entry["bytes"] or hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Expected pinned Dataset_S2.csv bytes")
    traces = read_doppler(source)
    if len(traces) != 7 or any(set(sites) != set(SITES) for sites in traces.values()):
        raise ValueError("Expected seven participants with all eight sites")
    return traces, entry, hashlib.sha256(manifest).hexdigest()


def run(source, output):
    traces, entry, manifest_digest = checked_traces(source)
    by_case = {}
    durations = {site: [] for site in SITES}
    duplicate_times = 0
    for case, sites in sorted(traces.items()):
        by_case[case] = {}
        for site, (times, velocities) in sites.items():
            by_case[case][site], collapsed = phase_samples(times, velocities)
            duplicate_times += collapsed
            durations[site].append(times[-1] - times[0])
    folds = score_folds(by_case)
    rows = []
    for site in SITES:
        results = [sites[site] for sites in folds.values()]
        rmses = [result["rmse"] for result in results]
        rows.append({
            "site": site,
            "participants": len(results),
            "trace_span_min_s": f"{min(durations[site]):.6f}",
            "trace_span_max_s": f"{max(durations[site]):.6f}",
            "template_mae_median_cm_s": f"{median(r['mae'] for r in results):.6f}",
            "template_rmse_median_cm_s": f"{median(rmses):.6f}",
            "template_rmse_min_cm_s": f"{min(rmses):.6f}",
            "template_rmse_max_cm_s": f"{max(rmses):.6f}",
            "flat_rmse_median_cm_s": f"{median(r['flat_rmse'] for r in results):.6f}",
            "peak_absolute_error_median_cm_s": f"{median(r['peak_error'] for r in results):.6f}",
            "lower_template_rmse": sum(r["rmse"] < r["flat_rmse"] for r in results),
        })

    summary = table(rows)
    receipt = {
        "source": entry,
        "input_manifest_sha256": manifest_digest,
        "implementation_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("doppler_benchmark.py", "audit.py")
        },
        "participants": len(folds),
        "traces": sum(map(len, by_case.values())),
        "phase_intervals": PHASE_INTERVALS,
        "duplicate_timestamps_collapsed": duplicate_times,
        "folds_with_lower_template_rmse": sum(r["lower_template_rmse"] for r in rows),
        "outputs_sha256": {"by-site.tsv": hashlib.sha256(summary).hexdigest()},
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "by-site.tsv").write_bytes(summary)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="pinned Dataset_S2.csv")
    parser.add_argument("output", type=Path, help="new output directory")
    args = parser.parse_args()
    run(args.source, args.output)
