"""Offline artifact commands. Inputs never select hardware or executable code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import InputError
from .desk import desk_status
from .evidence import evidence_report
from .exchange import simulate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evidence and synthetic artificial-gestation research fixtures")
    commands = parser.add_subparsers(dest="command", required=True)
    evidence = commands.add_parser("evidence-report", help="Validate and report a reviewed evidence ledger")
    evidence.add_argument("--ledger", type=Path, required=True)
    evidence.add_argument("--out", type=Path, required=True)
    exchange = commands.add_parser("simulate", help="Run a dimensionless, nonphysiologic exchange fixture")
    exchange.add_argument("--config", type=Path, required=True)
    exchange.add_argument("--out", type=Path, required=True)
    desk = commands.add_parser("desk-status", help="Read-only discovery of a local ResearchDesk ectogenesis blueprint")
    desk.add_argument("--url", default="http://127.0.0.1:8092")
    args = parser.parse_args(argv)
    try:
        if args.command == "desk-status":
            print(json.dumps(desk_status(args.url), indent=2))
            return 0
        receipt = (evidence_report(args.ledger, args.out) if args.command == "evidence-report"
                   else simulate(args.config, args.out))
    except (InputError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps({"output": str(args.out), "bundle_kind": receipt["bundle_kind"],
                      "input_sha256": receipt["input_sha256"]}, indent=2))
    return 0
