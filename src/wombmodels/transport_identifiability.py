"""Construct exact observation ambiguities in the existing dimensionless model."""
from __future__ import annotations

import copy
import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .developmental_models import MAX_RATE, _context, transport_parameters
from .exchange import NOTICE
from .numerical_verification import _exact_transport_state

MAX_DIAGNOSTIC_POINTS = 20_001


def core_coefficients(exchange: float, transport: float, loss: float) -> dict:
    """Coefficients of y'' + a1*y' + a0*y = gain*boundary(t)."""
    return {"a1": exchange + 2 * transport + 2 * loss,
            "a0": exchange * transport + loss * (exchange + 2 * transport) + loss * loss,
            "gain": exchange * transport}


def equilibrium(exchange: float, transport: float, loss: float, boundary: float) -> tuple:
    determinant = core_coefficients(exchange, transport, loss)["a0"]
    if determinant <= 0:
        raise InputError("This diagnostic requires a unique equilibrium")
    return (exchange * (transport + loss) * boundary / determinant,
            exchange * transport * boundary / determinant)


def transport_identifiability(config_path: Path, output: Path) -> dict:
    """Publish a structural counterexample; no measurements or parameters are fitted."""
    config, raw = read_json(config_path)
    values = transport_parameters(config)
    if values["interface"] != 0 or values["core"] != 0:
        raise InputError("Rate-swap proof requires zero initial interface and core states")
    e, d, loss = (values[key] for key in ("exchange", "transport", "loss"))
    if e < 1e-6 or d < 1e-6 or values["boundary"] <= 0:
        raise InputError("Diagnostic requires exchange and transport >= 1e-6 and positive dimensionless boundary excitation")
    if max(e, d, loss) > MAX_RATE / 2:
        raise InputError("Doubled witness rates exceed the supported rate bound")
    if values["steps"] + 1 > MAX_DIAGNOSTIC_POINTS:
        raise InputError(f"Diagnostic exceeds the {MAX_DIAGNOSTIC_POINTS}-point budget")

    def witness_config(exchange, transport, removal, *, stationary=False):
        derived = copy.deepcopy(config)
        derived["rates"] = {"boundary_exchange": exchange,
                            "intercompartment_transport": transport, "loss": removal}
        # The illustrations use the closed-form reference on the original grid.
        # Keep saved configs independently valid for the Euler command as well.
        derived["dimensionless_time"]["step"] = min(values["step"], 0.5 / (exchange + transport + removal))
        if stationary:
            c1, c2 = equilibrium(exchange, transport, removal, values["boundary"])
            derived["initial"] = {"interface": c1, "core": c2}
        transport_parameters(derived)
        return derived

    swapped = witness_config(2 * d, e / 2, loss)
    stationary = witness_config(e, d, loss, stationary=True)
    doubled = witness_config(2 * e, 2 * d, 2 * loss, stationary=True)
    coefficients = core_coefficients(e, d, loss)
    swapped_coefficients = core_coefficients(2 * d, e / 2, loss)
    eq = equilibrium(e, d, loss, values["boundary"])
    eq_double = equilibrium(2 * e, 2 * d, 2 * loss, values["boundary"])
    rows = []
    for index in range(values["steps"] + 1):
        time = values["duration"] if index == values["steps"] else index * values["step"]
        baseline = _exact_transport_state(0, 0, time, exchange=e, transport=d, loss=loss, boundary=values["boundary"])
        alternative = _exact_transport_state(0, 0, time, exchange=2 * d, transport=e / 2, loss=loss, boundary=values["boundary"])
        if not all(math.isfinite(v) for v in (*baseline, *alternative)):
            raise InputError("Closed-form diagnostic produced an unsupported nonfinite state")
        rows.append({"dimensionless_time": time, "baseline_interface": baseline[0],
                     "swapped_interface": alternative[0], "interface_difference": alternative[0] - baseline[0],
                     "baseline_core": baseline[1], "swapped_core": alternative[1],
                     "core_difference": alternative[1] - baseline[1]})
    core_error = max(abs(row["core_difference"]) for row in rows)
    interface_difference = max(abs(row["interface_difference"]) for row in rows)
    # This tolerance checks numerical evaluation of the algebraic identity. It
    # is never an assay noise level or a biological distinguishability threshold.
    tolerance = 1e-9 * max(1.0, values["boundary"])
    if core_error > tolerance:
        raise InputError("Closed-form evaluation failed the core-equivalence check")
    distinct = e != 2 * d
    scale_rows = [
        {"case": "baseline_stationary", "exchange": e, "transport": d, "loss": loss,
         "equilibrium_interface": eq[0], "equilibrium_core": eq[1]},
        {"case": "doubled_stationary", "exchange": 2 * e, "transport": 2 * d, "loss": 2 * loss,
         "equilibrium_interface": eq_double[0], "equilibrium_core": eq_double[1]}]
    report = {
        "schema_version": 1, "result_kind": "dimensionless_transport_identifiability",
        "fixture_notice": NOTICE, "stage_context": _context(config),
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False, "parameter_fitting_performed": False,
        "rates": config["rates"], "swapped_rates": swapped["rates"],
        "core_only": {"symbolic_identity": "(e, d, loss) -> (2*d, e/2, loss) preserves a1, a0 and gain",
            "equation": "core'' + (e+2*d+2*loss)*core' + (e*d+loss*(e+2*d)+loss^2)*core = e*d*boundary(t)",
            "assumptions": "Equal capacities, constant nonnegative rates, common first-order loss, known boundary input and zero initial states.",
            "baseline_coefficients": coefficients, "swapped_coefficients": swapped_coefficients,
            "distinct_rate_allocations": distinct,
            "configured_witness_status": "distinct_equivalent_core_traces" if distinct else "coincident_swap_at_e_equals_2d",
            "max_absolute_core_difference": core_error,
            "max_absolute_interface_difference": interface_difference,
            "numeric_check_tolerance": tolerance,
            "interpretation": "Core-only input/output cannot globally distinguish the two rate allocations under the stated assumptions. More core readings alone cannot break an exact symmetry."},
        "steady_state_only": {"symbolic_identity": "Scaling all three rates by any positive q preserves both equilibrium states.",
            "scale_factor": 2, "max_absolute_equilibrium_difference": max(abs(a - b) for a, b in zip(eq, eq_double)),
            "interpretation": "Both spatial states at equilibrium do not identify the absolute rate scale; a time-resolved transient or independently measured flux is required."},
        "paired_transient": {"configured_swap_has_different_interface": distinct and interface_difference > tolerance,
            "scope": "An independently observed interface trace can distinguish this particular swapped pair when it differs; this is not a proof that every rate is identifiable in noisy data or every model is distinguishable.",
            "unexcited_control": "With zero initial states and zero boundary input, both state traces stay zero for any rates. Even paired traces then contain no rate information."},
        "limits": ["All curves, rate allocations, clock values and tolerances are invented dimensionless software diagnostics.",
                   "The symbolic identity holds for any prescribed boundary history with zero initial states; the published numerical illustration uses a constant boundary.",
                   "The shared-loss assumption does not identify a biochemical uptake mechanism or distinguish uptake from adsorption or other unmodeled losses.",
                   "Different interface traces establish a mathematical observation requirement, not a sensor specification, biological measurement plan or operating recommendation.",
                   "No published Papp value, embryo image or transcriptome is used as a model parameter.",
                   "No confidence interval, health score, physical device parameter or gate completion is computed."]}
    lines = ["# Transport observation ambiguity", "", NOTICE, "",
             "This report constructs rate-allocation and equilibrium counterexamples in the existing abstract equations. It does not fit biological data.", "",
             f"Configured swapped pair: {report['core_only']['configured_witness_status']}.",
             f"Maximum absolute core difference: {core_error:.6g}; interface difference: {interface_difference:.6g} (dimensionless).", "",
             "Core elimination gives:", "", "```text", report["core_only"]["equation"], "```", "",
             report["core_only"]["symbolic_identity"],
             "Both core initial conditions are zero. Equal scalar equation, input and initial conditions imply equal core traces for all time.", "",
             report["core_only"]["interpretation"], "",
             report["steady_state_only"]["symbolic_identity"], report["steady_state_only"]["interpretation"], "",
             report["paired_transient"]["scope"], report["paired_transient"]["unexcited_control"], "",
             "Witness configurations remain valid inputs to transport-model. The comparison CSV uses the closed-form reference at the source configuration's grid times; saved Euler configurations may use a smaller step.", "",
             "## Limits", "", *["- " + item for item in report["limits"]]]
    return publish_bundle(output, kind="dimensionless_transport_identifiability", input_raw=raw,
        files={"input_config.json": raw, "swapped_config.json": json_bytes(swapped),
               "stationary_config.json": json_bytes(stationary), "doubled_stationary_config.json": json_bytes(doubled),
               "observation_contrasts.csv": csv_bytes(list(rows[0]), rows),
               "equilibrium_contrasts.csv": csv_bytes(list(scale_rows[0]), scale_rows),
               "transport_identifiability_report.json": json_bytes(report),
               "REPORT.md": ("\n".join(lines) + "\n").encode()},
        metadata={"biological_measurements": False, "physiologically_calibrated": False,
                  "human_gestation_prediction": False, "structural_counterexample": True})
