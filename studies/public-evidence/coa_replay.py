"""Replay the archived healthy fetal circulation equations and compare with Figure 2."""

import argparse
import ctypes
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from audit import HERE, table
from doppler_figure import FIGURE, figure_curves, pillow_version, rms


MODEL = {
    "archive": "https://doi.org/10.5281/zenodo.14826951",
    "url": "https://raw.githubusercontent.com/InmaV/CoA_scenarios/5597e52fda7c1f2385a05bef41912ecf10b23142/FETAL_MODEL_CoA.c",
    "sha256": "520b47b327b613119034e6ff334616082f314ecff73911aae56a90da9564529f",
    "bytes": 67413,
}
SOLVERS = {"BDF": 1e-7, "Radau": 1e-8}


def velocity_outputs(states, constants):
    # State and parameter indices are from the pinned C file's legend.
    # The velocity conversions come from Read_results.ipynb, Fig. 4 code.
    return {
        "Aortic Valve": states[5]/constants[23],
        "Pulmonary Valve": states[16]/constants[51],
        "Mitral Valve": states[4]/constants[41],
        "Tricuspid Valve": states[15]/constants[61],
        "Aortic Isthmus": states[28]/(math.pi * 0.2329**2),
        "Ductus Arteriosus": states[69]/(math.pi * 0.2090**2),
        "Umbilical Artery": states[44]/(math.pi * 0.165915**2),
        "Middle Cerebral Artery": ((states[58] + states[63]) * 0.75 * 0.74312
                                   / (0.5 * math.pi * 0.135**2)),
    }


def solve_model(library, method, tolerance, phases):
    vector = np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags="C_CONTIGUOUS")
    library.initConsts.argtypes = [vector] * 3
    library.initConsts.restype = None
    library.computeRates.argtypes = [ctypes.c_double] + [vector] * 4
    library.computeRates.restype = None
    constants, initial, algebraic = np.zeros(163), np.zeros(73), np.zeros(181)
    library.initConsts(constants, np.zeros_like(initial), initial)
    period = constants[17]

    def derivative(time, states):
        rates = np.empty_like(initial)
        library.computeRates(time, constants, rates, np.ascontiguousarray(states), algebraic)
        return rates

    solution = solve_ivp(derivative, (0, 26 * period), initial, method=method,
                         rtol=tolerance, atol=tolerance, max_step=period / 100, dense_output=True)
    if not solution.success:
        raise RuntimeError(f"{method}: {solution.message}")

    def valve_opening(time):
        return solution.sol(time)[6] - 0.01  # LV.xi onset from the figure notebook.

    def cycle_start(cycle):
        window = np.linspace(cycle * period, (cycle + 1) * period, 2001)
        xi = solution.sol(window)[6]
        crossings = np.flatnonzero((xi[:-1] <= 0.01) & (xi[1:] > 0.01))
        if len(crossings) != 1:
            raise ValueError(f"Expected one opening event in model cycle {cycle}")
        crossing = crossings[0]
        return brentq(valve_opening, window[crossing], window[crossing + 1])

    output = {}
    for cycle in (23, 24):
        start = cycle_start(cycle)
        for site, phase in phases.items():
            velocities = velocity_outputs(solution.sol(start + period * phase), constants)[site]
            if not np.isfinite(velocities).all():
                raise ValueError(f"Nonfinite {method} output for {site}")
            output[cycle, site] = velocities
    return output


def run(model, figure, output):
    if output.exists():
        raise FileExistsError(output)
    if model.stat().st_size != MODEL["bytes"]:
        raise ValueError("Expected the pinned C source")
    source = model.read_bytes()
    if hashlib.sha256(source).hexdigest() != MODEL["sha256"]:
        raise ValueError("Expected the pinned C source")
    curves = figure_curves(figure)
    phases = {site: np.asarray(values[0]) for site, values in curves.items()}

    with tempfile.TemporaryDirectory(prefix="coa-replay-") as scratch:
        c_source = Path(scratch) / "model.c"
        c_source.write_bytes(source)
        shared_object = Path(scratch) / "model.so"
        subprocess.run(["cc", "-shared", "-fPIC", "-O2", str(c_source),
                        "-o", str(shared_object), "-lm"], check=True)
        library = ctypes.CDLL(str(shared_object))
        bdf = solve_model(library, "BDF", SOLVERS["BDF"], phases)
        radau = solve_model(library, "Radau", SOLVERS["Radau"], phases)

    rows = []
    for site, phase in phases.items():
        published = np.asarray(curves[site][1])
        replay = bdf[24, site]
        rows.append({
            "site": site,
            "replay_vs_published_rmse_cm_s": f"{rms(replay - published):.3f}",
            "replay_peak_cm_s": f"{max(replay):.3f}",
            "published_peak_cm_s": f"{max(published):.3f}",
            "replay_peak_phase": f"{phase[np.argmax(replay)]:.4f}",
            "published_peak_phase": f"{phase[np.argmax(published)]:.4f}",
            "solver_max_difference_cm_s": f"{max(abs(replay - radau[24, site])):.6f}",
            "previous_cycle_max_difference_cm_s": f"{max(abs(replay - bdf[23, site])):.6f}",
        })
    summary = table(rows)
    receipt = {
        "model_source": MODEL,
        "figure_source": FIGURE,
        "implementation_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("coa_replay.py", "doppler_figure.py", "doppler_benchmark.py", "audit.py")
        },
        "libraries": {"numpy": np.__version__, "scipy": scipy.__version__, "pillow": pillow_version},
        "absolute_and_relative_tolerances": SOLVERS,
        "max_step_fraction_of_period": 0.01,
        "cycles_integrated": 26,
        "scored_cycle_index": 24,
        "phase_bounds": [0.02, 0.98],
        "comparison": "archived_healthy_equations_vs_published_plot",
        "outputs_sha256": {"by-site.tsv": hashlib.sha256(summary).hexdigest()},
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "by-site.tsv").write_bytes(summary)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="pinned FETAL_MODEL_CoA.c source")
    parser.add_argument("figure", type=Path, help="pinned PLOS Figure 2 PNG")
    parser.add_argument("output", type=Path, help="new output directory")
    args = parser.parse_args()
    run(args.model, args.figure, args.output)
