"""Platform and resource decision worksheet from the acquisition spec (T25).

The T08 reopen condition is met: the qualified requirements changed when T24
converted the twin's produced signatures into a numeric minimum-measurement
specification. This module turns that published specification into the
owner-controlled capability worksheet the original platform options document
named as its next action - line items a future quote, diligence or
co-development conversation can be checked against.

The worksheet consumes the published acquisition-specification bundle as its
input, byte-verbatim, and derives every line item from it: required channels
become measurement capability line items with cadence, timepoints, analytic
resolution floor and units per allocation at stated instrument-noise levels;
excluded channels become stated non-requirements (no boundary flux sensing
resolution discriminates the allocations); and the three route options from
the platform comparison each get the supply obligations they would have to
meet for exactly those channels.

Prices are unknown by construction: every line item carries an explicit
unknown price and a quote need, no total is computed, and no purchase,
procurement or engagement is proposed. All quantities remain invented
dimensionless software fixture values until calibration replaces them.
"""
from __future__ import annotations

from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json, sha256
from .exchange import NOTICE, fields, number

SOURCE_REPORT = "acquisition_spec_report.json"
CAPABILITY_CLASS = {
    "wall_strain": "chamber-wall strain measurement capability",
    "deep_receipt_rate": "internal tissue receipt-rate measurement capability",
    "progression": "stage-indexed progression measurement capability",
}
ROUTES = (
    ("owner_led", "Build or qualify all required measurement capabilities in-house against this worksheet.",
     "Requirements, data custody, configuration and the resulting asset.",
     "No facility, staff, instrument cost basis, calibration route or schedule is established here.",
     "Open baseline; no quote requested."),
    ("acquisition_or_licensing", "Identify purchasable or licensable instruments covering every required channel with transferable operation, maintenance and data rights.",
     "Requirements ownership, final configuration and acceptance criteria.",
     "No availability, price, product scope, rights package or support terms are established for any channel.",
     "Open option; no availability assumed, no quote sent."),
    ("co_development", "A partner supplies calibrated coverage of the required channels while the owner holds the requirement set.",
     "The requirement set, acceptance criteria and decision gates.",
     "No partner, scope split, cost share, data-rights basis or qualification route exists here.",
     "Open option; no engagement proposed."),
)


def _validate(config):
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    fields(config, ("schema_version", "fixture_notice", "source_bundle_kind",
                    "degradation_multipliers"), "config")
    if config["schema_version"] != 1 or isinstance(config["schema_version"], bool):
        raise InputError("config schema_version must be integer 1")
    if config["fixture_notice"] != NOTICE:
        raise InputError("fixture_notice must retain the artificial-software declaration")
    if config["source_bundle_kind"] != "dimensionless_acquisition_spec":
        raise InputError("source_bundle_kind must be the published acquisition specification")
    raw = config["degradation_multipliers"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= 12:
        raise InputError("degradation_multipliers must be a list of 1 to 12 values")
    multipliers = [number(item, "degradation multiplier", 0.01, 64.0) for item in raw]
    if multipliers != sorted(multipliers):
        raise InputError("degradation_multipliers must be ascending")
    return multipliers


def _load_spec_report(spec_dir: Path):
    report_path = Path(spec_dir) / SOURCE_REPORT
    if not report_path.is_file():
        raise InputError(f"Source bundle is missing {SOURCE_REPORT}: {spec_dir}")
    report, raw = read_json(report_path)
    if report.get("result_kind") != "dimensionless_acquisition_spec":
        raise InputError("Source bundle is not the acquisition specification")
    if report.get("fixture_notice") != NOTICE:
        raise InputError("Source specification lost the artificial-software declaration")
    if report.get("biological_measurements") or report.get("physiologically_calibrated") \
            or report.get("human_gestation_prediction"):
        raise InputError("Source specification claims it is not allowed to make")
    return report, raw


def platform_requirements(config_path: Path, spec_dir: Path, output: Path) -> dict:
    """Publish the capability worksheet; every price stays unknown."""
    config, raw = read_json(config_path)
    multipliers = _validate(config)
    spec, spec_raw = _load_spec_report(spec_dir)

    swept = set(spec["spec_parameters"]["noise_multipliers"])
    unknown = [value for value in multipliers if value not in swept]
    if unknown:
        raise InputError(f"degradation_multipliers not confirmed by the source sweep: {unknown}")

    required = [row for row in spec["channel_requirements"] if row["required"]]
    excluded = [row for row in spec["channel_requirements"] if not row["required"]]
    timing = spec["timing"]
    resolution = spec["resolution"]

    line_items = []
    for row in required:
        channel = row["channel"]
        units = {}
        confirmed = {}
        for value in spec["units_per_cohort"][channel]["sweep"]:
            if value["multiplier"] in multipliers:
                units[value["multiplier"]] = value["analytic_units"]
                confirmed[value["multiplier"]] = bool(value["confirmed"]) and not value["capped"]
        if set(units) != set(multipliers):
            raise InputError(f"Source sweep does not cover the worksheet levels: {channel}")
        line_items.append({
            "channel": channel, "compartment": row["compartment"], "dmp": row["dmp"],
            "capability_class": CAPABILITY_CLASS.get(channel, "measurement capability"),
            "sampling_cadence": timing["sampling_cadence"],
            "discrimination_timepoints": timing["discrimination_timepoints"],
            "surveillance_timepoints": timing["surveillance_timepoints"],
            "resolution_floor_multiplier": resolution["channel_floor_multiplier"][channel],
            "binding_pair": spec["binding_pair"][channel]["pair"],
            "binding_margin": spec["binding_pair"][channel]["margin"],
            "reference_noise_sd": resolution["reference_noise_sd"],
            "detection_sigma": resolution["detection_sigma"],
            "units_per_allocation_by_multiplier": units,
            "confirmed_by_seeded_sweep": confirmed,
            "price": None, "price_state": "unknown_quote_needed",
            "quote_need": "written scope and price quote needed after calibration replaces the invented dimensionless values"})
    if not line_items:
        raise InputError("Source specification requires no channel; no worksheet can form")

    fluidic_boundary = ("delivered_flux", "served_fraction", "bulk_stock")
    non_requirements = [{
        "channel": row["channel"], "compartment": row["compartment"], "dmp": row["dmp"],
        "excluded_reason": row["excluded_reason"],
        "note": ("no boundary flux sensing resolution discriminates the allocations"
                 if row["channel"] in fluidic_boundary else
                 "derived from instrumented channels; not separately procured")}
        for row in excluded]
    route_comparison = [{
        "route": route, "supplies": supplies, "owner_retains": retains,
        "critical_unknowns": unknowns, "disposition": disposition,
        "covers_channels": [row["channel"] for row in required]}
        for route, supplies, retains, unknowns, disposition in ROUTES]

    report = {
        "schema_version": 1, "fixture_notice": NOTICE,
        "result_kind": "dimensionless_platform_requirements",
        "biological_measurements": False, "physiologically_calibrated": False,
        "human_gestation_prediction": False,
        "source_spec": {
            "result_kind": "dimensionless_acquisition_spec",
            "report_path": SOURCE_REPORT,
            "report_sha256": sha256(spec_raw),
            "n_variants": spec["source_twin"]["n_variants"],
            "n_intervals": spec["source_twin"]["n_intervals"],
            "one_way_coupling_verified": spec["source_twin"]["one_way_coupling_verified"]},
        "worksheet_noise_multipliers": multipliers,
        "line_items": line_items,
        "non_requirements": non_requirements,
        "route_comparison": route_comparison,
        "price_totals_computed": False,
        "interpretation": {
            "line_items": "Each required channel becomes one measurement capability line item; the numbers come from the published specification unchanged, and the price of every line is unknown with an explicit quote need.",
            "non_requirements": "The excluded channels are stated non-requirements: no boundary flux sensing resolution discriminates the allocations, wall damage is derived from instrumented strain history, and cumulative deficit is variant-identical.",
            "routes": "The three route options from the platform comparison each carry the supply obligations they would have to meet for exactly these channels; dispositions stay open and no quote, availability or engagement is assumed.",
            "t08": "This is the T08 reopen: the qualified requirements changed when the twin's signatures became a numeric specification, and this worksheet is the owner-controlled capability list a future quote, diligence or co-development conversation is checked against."},
        "limits": [
            "All channels, cadences, timepoints, floors, unit counts and route terms are derived from a dimensionless software fixture specification; nothing here names a real instrument, vendor, price or facility.",
            "Every price is unknown by construction: no total, budget, quote, availability or timeline is computed or implied.",
            "The worksheet inherits the source specification's template status: quotable only after calibration replaces the invented dimensionless values.",
            "Route comparison refreshes the 2026-10-11 platform options document; it does not choose a route, authorize engagement or move any gate.",
            "No purchase, procurement, external contact or author approach arises from this worksheet."]}

    lines = ["# Dimensionless platform and resource decision worksheet", "", NOTICE, "",
             "Consumed source: published acquisition specification "
             f"({report['source_spec']['report_sha256'][:12]}...), byte-verbatim in this bundle.",
             "",
             f"{len(line_items)} measurement capability line items; "
             f"{len(non_requirements)} stated non-requirements; prices unknown.",
             "", "## Line items", ""]
    for item in line_items:
        parts = "; ".join(
            f"m={value:g}: {item['units_per_allocation_by_multiplier'][value]} unit(s)/allocation"
            + ("" if item["confirmed_by_seeded_sweep"][value] else " (unconfirmed)")
            for value in multipliers)
        lines.append(
            f"- {item['channel']} ({item['capability_class']}, {item['dmp']}): cadence "
            f"{item['sampling_cadence']}; discrimination needs "
            f"{item['discrimination_timepoints']} timepoints, surveillance "
            f"{item['surveillance_timepoints']}; floor "
            f"{item['resolution_floor_multiplier']:.4g}x reference noise; binding pair "
            f"{item['binding_pair']}; {parts}; price unknown - quote needed.")
    lines.extend(["", "## Non-requirements", ""])
    for row in non_requirements:
        lines.append(f"- {row['channel']} ({row['dmp']}): {row['excluded_reason']}; {row['note']}.")
    lines.extend(["", "## Route comparison (all dispositions open)", ""])
    for row in route_comparison:
        lines.append(f"- {row['route']}: supplies {row['supplies']} Unknowns: "
                     f"{row['critical_unknowns']} Disposition: {row['disposition']}")
    lines.extend(["", report["interpretation"]["t08"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])

    files = {"input_config.json": raw,
             "consumed_spec_report.json": spec_raw,
             "line_items.csv": csv_bytes(list(line_items[0]), line_items),
             "non_requirements.csv": csv_bytes(list(non_requirements[0]), non_requirements),
             "route_comparison.csv": csv_bytes(list(route_comparison[0]), route_comparison),
             "platform_requirements_report.json": json_bytes(report),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    return publish_bundle(output, kind="dimensionless_platform_requirements", input_raw=raw,
                          files=files, metadata={"biological_measurements": False,
                                                 "physiologically_calibrated": False,
                                                 "human_gestation_prediction": False,
                                                 "n_line_items": len(line_items),
                                                 "n_non_requirements": len(non_requirements),
                                                 "n_routes": len(route_comparison)})