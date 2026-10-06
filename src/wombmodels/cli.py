"""Offline artifact commands. Inputs never select hardware or executable code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import InputError
from .desk import desk_status
from .design_sweep import sweep
from .evidence import evidence_report
from .exchange import simulate
from .identifiability import analyze


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evidence and synthetic artificial-gestation research fixtures")
    commands = parser.add_subparsers(dest="command", required=True)
    evidence = commands.add_parser("evidence-report", help="Validate and report a reviewed evidence ledger")
    evidence.add_argument("--ledger", type=Path, required=True)
    evidence.add_argument("--out", type=Path, required=True)
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
    args = parser.parse_args(argv)
    try:
        if args.command == "desk-status":
            print(json.dumps(desk_status(args.url), indent=2))
            return 0
        if args.command == "evidence-report":
            receipt = evidence_report(args.ledger, args.out)
        elif args.command == "identifiability-report":
            receipt = analyze(args.config, args.trajectory, args.out)
        elif args.command == "design-sweep":
            receipt = sweep(args.config, args.out, replicates=args.replicates)
        else:
            receipt = simulate(args.config, args.out)
    except (InputError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps({"output": str(args.out), "bundle_kind": receipt["bundle_kind"],
                      "input_sha256": receipt["input_sha256"]}, indent=2))
    return 0
