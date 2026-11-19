"""Measure agreement between the published Figure 2 curves and the fitting cohort."""

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import linear_regression, mean, median

from PIL import Image, __version__ as pillow_version

from audit import HERE, table
from doppler_benchmark import checked_traces, interpolate, phase_points


FIGURE = {
    "url": "https://journals.plos.org/ploscompbiol/article/figure/image?size=large&id=10.1371/journal.pcbi.1013096.g002",
    "sha256": "54c4633a87b479d5400a5ffb9be6d70da23a12e1f07712b5b161a63c11f8386c",
    "bytes": 2040228,
}
# Axis-border centers and velocity tick centers in the pinned 4200 x 1800 PNG.
PHASE_AXES = ((219, 972.5), (1274, 2028), (2329, 3083), (3384, 4137.5))
PANELS = (
    ("Aortic Valve", ((100, 149), (50, 335), (0, 520.5))),
    ("Pulmonary Valve", ((50, 315), (0, 548))),
    ("Mitral Valve", ((60, 100), (40, 240), (20, 380), (0, 519.5))),
    ("Tricuspid Valve", ((50, 207.5), (25, 353), (0, 498))),
    ("Aortic Isthmus", ((100, 950.5), (50, 1134), (0, 1316.5))),
    ("Ductus Arteriosus", ((150, 898), (100, 1052), (50, 1206), (0, 1360))),
    ("Umbilical Artery", ((40, 1091), (20, 1300))),
    ("Middle Cerebral Artery", ((60, 966), (40, 1118), (20, 1269.5), (0, 1421))),
)


def rms(values):
    return math.sqrt(mean(value**2 for value in values))


def figure_curves(source):
    if source.stat().st_size != FIGURE["bytes"] or hashlib.sha256(source.read_bytes()).hexdigest() != FIGURE["sha256"]:
        raise ValueError("Expected the pinned PLOS Figure 2 PNG")
    with Image.open(source) as image:
        pixels = image.convert("RGB").load()
    curves = {}
    for index, (site, ticks) in enumerate(PANELS):
        left, right = PHASE_AXES[index % 4]
        y0, y1 = ((90, 623), (899, 1431))[index // 4]
        velocities, rows = zip(*ticks)
        slope, offset = linear_regression(rows, velocities)
        phase, black, green, threshold_differences = [], [], {}, []
        interior_pixels = range(math.ceil(left + 0.02 * (right - left)),
                                math.floor(left + 0.98 * (right - left)) + 1)
        for x in interior_pixels:
            dark, core, green_pixels = [], [], []
            for y in range(y0, y1):
                red, g, blue = pixels[x, y]
                if max(red, g, blue) <= 30:
                    dark.append(y)
                    if max(red, g, blue) <= 8:
                        core.append(y)
                if red <= 12 and blue <= 12 and 89 <= g <= 110:
                    green_pixels.append(y)
            if not core or dark[-1] - dark[0] + 1 != len(dark):
                raise ValueError(f"Ambiguous black curve in {site}, column {x}")
            phase.append((x - left) / (right - left))
            black_center = (dark[0] + dark[-1]) / 2
            black.append(offset + slope * black_center)
            threshold_differences.append(abs(slope * ((core[0] + core[-1]) / 2 - black_center)))
            if (green_pixels and green_pixels[-1] - green_pixels[0] + 1 == len(green_pixels)
                    and (green_pixels[-1] <= dark[0] - 6 or green_pixels[0] >= dark[-1] + 6)):
                green[len(phase) - 1] = offset + slope * (green_pixels[0] + green_pixels[-1]) / 2
        curves[site] = (phase, black, green, max(threshold_differences))
    return curves


def run(source, figure, output):
    traces, trace_entry, manifest_digest = checked_traces(source)
    rows = []
    for site, (phase, black, green, sensitivity) in figure_curves(figure).items():
        trace_points = [phase_points(*participant[site]) for participant in traces.values()]
        observed = [[interpolate(*points, position) for position in phase] for points in trace_points]
        observed_mean = list(map(mean, zip(*observed, strict=True)))
        rows.append({
            "site": site,
            "pixels_scored": len(phase),
            "published_model_min_cm_s": f"{min(black):.3f}",
            "published_model_peak_cm_s": f"{max(black):.3f}",
            "model_vs_observed_mean_rmse_cm_s": f"{rms(a - b for a, b in zip(black, observed_mean, strict=True)):.3f}",
            "model_vs_participant_median_rmse_cm_s": f"{median(rms(a - b for a, b in zip(black, trace, strict=True)) for trace in observed):.3f}",
            "green_mean_pixels_checked": len(green),
            "green_vs_observed_mean_rmse_cm_s": f"{rms(value - observed_mean[i] for i, value in green.items()):.3f}",
            "pixel_threshold_max_change_cm_s": f"{sensitivity:.3f}",
        })
    summary = table(rows)
    receipt = {
        "source": FIGURE,
        "observation_source": trace_entry,
        "observation_manifest_sha256": manifest_digest,
        "implementation_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("doppler_figure.py", "doppler_benchmark.py", "audit.py")
        },
        "pillow": pillow_version,
        "phase_bounds": [0.02, 0.98],
        "comparison": "in_sample_published_figure",
        "outputs_sha256": {"by-site.tsv": hashlib.sha256(summary).hexdigest()},
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "by-site.tsv").write_bytes(summary)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="pinned Dataset_S2.csv")
    parser.add_argument("figure", type=Path, help="pinned PLOS Figure 2 PNG")
    parser.add_argument("output", type=Path, help="new output directory")
    args = parser.parse_args()
    run(args.source, args.figure, args.output)
