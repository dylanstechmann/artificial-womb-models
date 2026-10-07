"""Offline artifact commands. Inputs never select hardware or executable code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import InputError
from .bundle_verification import verify_bundle
from .desk import desk_status
from .design_sweep import sweep
from .developmental_models import simulate_mechanics, simulate_transport
from .evidence import evidence_report
from .exchange import simulate
from .identifiability import analyze
from .numerical_verification import (
    verify_mechanics_accuracy,
    verify_transport_accuracy,
    verify_transport_matrix,
)
from .observations import observation_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evidence and synthetic artificial-gestation research fixtures")
    commands = parser.add_subparsers(dest="command", required=True)
    evidence = commands.add_parser("evidence-report", help="Validate and report a reviewed evidence ledger")
    evidence.add_argument("--ledger", type=Path, required=True)
    evidence.add_argument("--out", type=Path, required=True)
    observations = commands.add_parser("validate-observations", help="Validate source-linked developmental observations and preserve exact-unit groups")
    observations.add_argument("--dataset", type=Path, required=True,
                               help="Dataset card and observation records in observation-dataset.schema.json format")
    observations.add_argument("--source-root", type=Path,
                               help="Optional local source directory; hashes only declared relative local_path files")
    observations.add_argument("--out", type=Path, required=True)
    exchange = commands.add_parser("simulate", help="Run a dimensionless, nonphysiologic exchange fixture")
    exchange.add_argument("--config", type=Path, required=True)
    exchange.add_argument("--out", type=Path, required=True)
    observability = commands.add_parser("identifiability-report", help="Analyze dimensionless input/conversion identifiability from a synthetic trajectory")
    observability.add_argument("--config", type=Path, required=True,
                               help="Original exchange fixture configuration")
    observability.add_argument("--trajectory", type=Path, required=True,
                               help="trajectory.csv produced by wombmodels simulate")
    observability.add_argument("--out", type=Path, required=True)
    sweep_parser = commands.add_parser("design-sweep", help="Compare bounded seeded cadence/noise, monitor-fault and event-timing profiles")
    sweep_parser.add_argument("--config", type=Path, required=True)
    sweep_parser.add_argument("--out", type=Path, required=True)
    sweep_parser.add_argument("--replicates", type=int, default=8,
                              help="Replicates per design (1-20; default 8)")
    desk = commands.add_parser("desk-status", help="Read-only discovery of a local ResearchDesk ectogenesis blueprint")
    desk.add_argument("--url", default="http://127.0.0.1:8092")
    transport = commands.add_parser("transport-model", help="Run a dimensionless two-compartment transport theory fixture")
    transport.add_argument("--config", type=Path, required=True)
    transport.add_argument("--out", type=Path, required=True)
    mechanics = commands.add_parser("mechanics-model", help="Run a dimensionless Kelvin–Voigt mechanics theory fixture")
    mechanics.add_argument("--config", type=Path, required=True)
    mechanics.add_argument("--out", type=Path, required=True)
    verification = commands.add_parser(
        "verify-transport", help="Measure dimensionless transport Euler error against a closed-form reference")
    verification.add_argument("--config", type=Path, required=True)
    verification.add_argument("--out", type=Path, required=True)
    mechanics_verification = commands.add_parser(
        "verify-mechanics", help="Check dimensionless mechanics against a closed-form piecewise-load reference")
    mechanics_verification.add_argument("--config", type=Path, required=True)
    mechanics_verification.add_argument("--out", type=Path, required=True)
    matrix_verification = commands.add_parser(
        "verify-transport-matrix", help="Check transport Euler convergence across seven dimensionless rate regimes")
    matrix_verification.add_argument("--config", type=Path, required=True)
    matrix_verification.add_argument("--out", type=Path, required=True)
    verify_bundle_parser = commands.add_parser(
        "verify-bundle",
        help="Verify a published bundle's receipt, files, parent ancestry and declared dependencies")
    verify_bundle_parser.add_argument("--bundle", type=Path, required=True)
    verify_bundle_parser.add_argument("--strict", action="store_true",
                                      help="also fail on undeclared files and unknown bundle kinds")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify-bundle":
            report = verify_bundle(args.bundle, strict=args.strict)
            print(json.dumps(report, indent=2))
            return 0 if report["bytes_verified"] else 1
        if args.command == "desk-status":
            print(json.dumps(desk_status(args.url), indent=2))
            return 0
        if args.command == "evidence-report":
            receipt = evidence_report(args.ledger, args.out)
        elif args.command == "validate-observations":
            receipt = observation_report(args.dataset, args.out, source_root=args.source_root)
        elif args.command == "identifiability-report":
            receipt = analyze(args.config, args.trajectory, args.out)
        elif args.command == "design-sweep":
            receipt = sweep(args.config, args.out, replicates=args.replicates)
        elif args.command == "transport-model":
            receipt = simulate_transport(args.config, args.out)
        elif args.command == "mechanics-model":
            receipt = simulate_mechanics(args.config, args.out)
        elif args.command == "verify-transport":
            receipt = verify_transport_accuracy(args.config, args.out)
        elif args.command == "verify-mechanics":
            receipt = verify_mechanics_accuracy(args.config, args.out)
        elif args.command == "verify-transport-matrix":
            receipt = verify_transport_matrix(args.config, args.out)
        else:
            receipt = simulate(args.config, args.out)
    except (InputError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps({"output": str(args.out), "bundle_kind": receipt["bundle_kind"],
                      "input_sha256": receipt["input_sha256"]}, indent=2))
    return 0
