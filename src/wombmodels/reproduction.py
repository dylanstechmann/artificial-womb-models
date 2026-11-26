"""Bounded offline reruns for two synthetic bundle kinds.

This module never evaluates a bundle's command or executes bundle-supplied code.
It selects a constant trusted runner for the current package implementation. The
runner uses an isolated Python process, a scrubbed environment, a temporary
working directory, a timeout, and bounded stream capture. This is not a general
security sandbox for untrusted code.
"""
from __future__ import annotations

import argparse
import re
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

# The trusted runner is this current package file, never a path from a bundle.
# Direct execution with ``python -I`` needs the current source root added by the
# trusted runner itself; installed package imports use the normal package path.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wombmodels import __version__
from wombmodels.artifacts import (
    InputError,
    implementation_hashes,
    json_bytes,
    publish_bundle,
    read_json,
    reproduction_plan,
    sha256,
)
from wombmodels.bundle_verification import verify_bundle


RERUN_ENTRY_POINTS = {
    "synthetic_exchange_software_fixture": "simulate/1",
    "synthetic_exchange_observability_diagnostic": "identifiability/1",
}
REPRODUCTION_BUNDLE_KIND = "synthetic_bundle_reproduction_check"  # SECRETS-GUARD-IGNORE: public schema identifier, not a credential
RERUN_TIMEOUT_SECONDS = 120
MAX_CAPTURED_STREAM_BYTES = 65_536
MAX_MISMATCH_DETAILS = 32
MAX_IMPLEMENTATION_MISMATCHES = 64

_DECLARED_INPUTS = {
    "synthetic_exchange_software_fixture": ["input_config.json"],
    "synthetic_exchange_observability_diagnostic": [
        "source_manifest.json",
        "source_config.json",
        "source_trajectory.csv",
        "source_receipt.json",
    ],
}
_INPUT_MAPPINGS = {
    "synthetic_exchange_software_fixture": {"input_config.json": "config.json"},
    "synthetic_exchange_observability_diagnostic": {
        "source_config.json": "config.json",
        "source_trajectory.csv": "simulation/trajectory.csv",
        "source_receipt.json": "simulation/receipt.json",
    },
}
_EXPECTED_DECLARED_OUTPUTS = {
    "synthetic_exchange_software_fixture": {
        "input_config.json", "trajectory.csv", "simulation_summary.json", "REPORT.md",
        "reproduction_plan.json",
    },
    "synthetic_exchange_observability_diagnostic": {
        "source_manifest.json", "source_config.json", "source_trajectory.csv", "source_receipt.json",
        "observability_report.json", "interval_design.csv", "REPORT.md", "reproduction_plan.json",
    },
}
_RECEIPT_FIELDS = {
    "schema_version", "bundle_kind", "package_version", "python_version", "input_sha256",
    "implementation_sha256", "outputs", "metadata", "publication_contract",
}
_METADATA_FIELDS = {
    "synthetic_exchange_software_fixture": {
        "physiologically_calibrated", "biological_assay_performed", "human_gestation_prediction",
    },
    "synthetic_exchange_observability_diagnostic": {
        "biological_measurements", "physiologically_calibrated", "human_gestation_prediction",
        "config_sha256", "trajectory_sha256", "parent_receipt_sha256", "parent_receipt_file",
    },
}
_LIMITATION_FIELDS = {
    "synthetic_exchange_software_fixture": (
        "physiologically_calibrated", "biological_assay_performed", "human_gestation_prediction",
    ),
    "synthetic_exchange_observability_diagnostic": (
        "biological_measurements", "physiologically_calibrated", "human_gestation_prediction",
    ),
}
_PUBLICATION_CONTRACT = "Exclusive directory; atomic files; receipt published last."
_INTERPRETATION_LIMITS = [
    "Exact reproduction establishes deterministic software output for the recorded implementation and inputs only.",
    "The payload-only diagnostic cannot override a full-inventory byte mismatch; no numeric tolerance is applied.",
    "The fixed runner is not a general untrusted-code sandbox and does not execute bundle-selected code or commands.",
    "No source authenticity, scientific review, biological measurement, physiological calibration, or human gestation prediction is established.",
]


def _validate_destination(output: Path, source: Path) -> Path:
    destination = Path(output).absolute()
    if destination.exists() or destination.is_symlink():
        raise InputError("Rerun output must be a new, non-symlink directory")
    if destination.name in {"", ".", ".."} or destination.parent == destination:
        raise InputError("Rerun output destination is invalid")
    for ancestor in (destination.parent, *destination.parent.parents):
        if ancestor.is_symlink():
            raise InputError("Rerun output destination has a symlinked parent")
        if ancestor.exists() and not ancestor.is_dir():
            raise InputError("Rerun output parent is not a directory")
    try:
        destination.resolve(strict=False).relative_to(Path(source).resolve())
    except ValueError:
        pass
    else:
        raise InputError("Rerun output cannot be created inside the source bundle")
    return destination


def _require_exact_root_inventory(root: Path, receipt: dict):
    outputs = _validated_output_inventory(receipt, "Bundle receipt")
    expected = set(outputs) | {"receipt.json"}
    observed = {path.name for path in root.iterdir()}
    if observed != expected:
        raise InputError("Bundle directory inventory contains unsafe or undeclared entries")


def _read_declared_input(root: Path, receipt: dict, name: str) -> bytes:
    path = root / name
    try:
        raw = path.read_bytes()
    except OSError:
        raise InputError("A declared rerun input could not be read") from None
    outputs = _validated_output_inventory(receipt, "Source receipt")
    entry = outputs.get(name)
    if entry is None:
        raise InputError("A declared rerun input has no receipt entry")
    if entry["sha256"] != sha256(raw) or entry["size_bytes"] != len(raw):
        raise InputError("A declared rerun input changed during preflight")
    return raw


def _is_digest(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value)


def _validated_output_inventory(receipt: dict, description: str) -> dict:
    """Validate every output container and value before any nested access."""
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        raise InputError(f"{description} outputs must be an object")
    for name, entry in outputs.items():
        if not isinstance(entry, dict):
            raise InputError(f"{description} output {name!r} must be an object")
        if set(entry) != {"sha256", "size_bytes"}:
            raise InputError(f"{description} output {name!r} has invalid fields")
        if not _is_digest(entry.get("sha256")):
            raise InputError(f"{description} output {name!r} has an invalid SHA-256")
        size = entry.get("size_bytes")
        if type(size) is not int or size < 0:
            raise InputError(f"{description} output {name!r} has an invalid byte count")
    return outputs


def _implementation_comparison(receipt: dict) -> tuple[dict, bool]:
    stored = receipt.get("implementation_sha256")
    if not isinstance(stored, dict):
        stored = {}
    current = implementation_hashes()
    mismatches = []
    for name, current_hash in sorted(current.items()):
        stored_hash = stored.get(name)
        if stored_hash != current_hash:
            mismatches.append({
                "implementation": name,
                "stored_sha256": stored_hash if _is_digest(stored_hash) else None,
                "current_sha256": current_hash,
            })
    unexpected_count = len(set(stored) - set(current))
    match = not mismatches and unexpected_count == 0 and receipt.get("package_version") == __version__
    details = {
        "stored_implementation_count": len(stored),
        "current_implementation_count": len(current),
        "unexpected_stored_implementation_count": unexpected_count,
        "mismatch_count": len(mismatches) + unexpected_count,
        "mismatches": mismatches[:MAX_IMPLEMENTATION_MISMATCHES],
        "mismatch_details_omitted": max(0, len(mismatches) - MAX_IMPLEMENTATION_MISMATCHES),
    }
    return details, match


def _validate_version_metadata(container: dict, description: str):
    for field in ("package_version", "python_version"):
        value = container.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,127}", value):
            raise InputError(f"{description} {field} is not safe deterministic version metadata")


def _validate_limitations(metadata: dict, kind: str, description: str):
    for field in _LIMITATION_FIELDS[kind]:
        if metadata.get(field) is not False:
            raise InputError(f"{description} {field} must be the literal boolean false")


def _validate_archived_implementation(receipt: dict):
    stored = receipt.get("implementation_sha256")
    if not isinstance(stored, dict) or set(stored) != set(implementation_hashes()):
        raise InputError("Parent receipt implementation inventory is invalid")
    if any(not _is_digest(value) for value in stored.values()):
        raise InputError("Parent receipt implementation hashes must be lowercase SHA-256 values")


def _validate_identifiability_bindings(receipt: dict, inputs: dict[str, bytes]):
    try:
        manifest, _ = read_json_from_bytes(inputs["source_manifest.json"])
        parent, _ = read_json_from_bytes(inputs["source_receipt.json"])
    except InputError:
        raise InputError("Identifiability ancestry inputs are malformed") from None
    config_hash = sha256(inputs["source_config.json"])
    trajectory_hash = sha256(inputs["source_trajectory.csv"])
    parent_hash = sha256(inputs["source_receipt.json"])
    if (receipt.get("input_sha256") != sha256(inputs["source_manifest.json"])
            or manifest.get("analysis") != "dimensionless_exchange_observability_v2"
            or manifest.get("config_sha256") != config_hash
            or manifest.get("trajectory_sha256") != trajectory_hash
            or manifest.get("simulation_receipt_sha256") != parent_hash):
        raise InputError("Identifiability source manifest does not bind the staged inputs")
    parent_outputs = _validated_output_inventory(parent, "Parent receipt")
    parent_metadata = parent.get("metadata")
    if not isinstance(parent_metadata, dict):
        raise InputError("Parent receipt metadata must be an object")
    if (set(parent) != _RECEIPT_FIELDS
            or set(parent_metadata) != _METADATA_FIELDS["synthetic_exchange_software_fixture"]
            or parent.get("schema_version") != 1
            or parent.get("bundle_kind") != "synthetic_exchange_software_fixture"):
        raise InputError("Identifiability parent receipt has an invalid structure")
    _validate_version_metadata(parent, "Parent receipt")
    if any(parent.get(field) != receipt.get(field)
           for field in ("package_version", "python_version")):
        raise InputError("Parent receipt version metadata does not match the source receipt")
    _validate_archived_implementation(parent)
    if (parent.get("publication_contract") != _PUBLICATION_CONTRACT
            or set(parent_outputs) != _EXPECTED_DECLARED_OUTPUTS["synthetic_exchange_software_fixture"]):
        raise InputError("Parent receipt does not match the simulation publication contract")
    _validate_limitations(parent_metadata, "synthetic_exchange_software_fixture",
                          "Parent receipt metadata")
    configuration = parent_outputs["input_config.json"]
    trajectory = parent_outputs["trajectory.csv"]
    if (parent.get("input_sha256") != config_hash
            or configuration["sha256"] != config_hash
            or configuration["size_bytes"] != len(inputs["source_config.json"])
            or trajectory["sha256"] != trajectory_hash
            or trajectory["size_bytes"] != len(inputs["source_trajectory.csv"])):
        raise InputError("Identifiability parent receipt does not bind the staged inputs")
    metadata = receipt.get("metadata")
    if not isinstance(metadata, dict):
        raise InputError("Source receipt metadata must be an object")
    if (metadata.get("config_sha256") != config_hash
            or metadata.get("trajectory_sha256") != trajectory_hash
            or metadata.get("parent_receipt_sha256") != parent_hash
            or metadata.get("parent_receipt_file") != "source_receipt.json"):
        raise InputError("Identifiability receipt ancestry metadata is inconsistent")


def read_json_from_bytes(raw: bytes) -> tuple[dict, bytes]:
    """Decode an already bounded declared input through the package JSON contract."""
    from wombmodels.artifacts import decode_json
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise InputError("Input JSON must be an object")
    return value, raw


def _load_rerun_source(bundle: Path) -> dict:
    root = Path(bundle)
    verification = verify_bundle(root, strict=True)
    if not verification["bytes_verified"]:
        raise InputError("Source bundle failed strict verification")
    receipt, receipt_raw = read_json(root / "receipt.json")
    kind = receipt.get("bundle_kind")
    if not isinstance(kind, str) or kind not in RERUN_ENTRY_POINTS:
        raise InputError(f"Bundle kind is not supported for rerun: {kind}")
    if set(receipt) != _RECEIPT_FIELDS:
        raise InputError("Source receipt does not match the fixed synthetic bundle inventory")
    outputs = _validated_output_inventory(receipt, "Source receipt")
    metadata = receipt.get("metadata")
    if not isinstance(metadata, dict):
        raise InputError("Source receipt metadata must be an object")
    if (set(outputs) != _EXPECTED_DECLARED_OUTPUTS[kind]
            or set(metadata) != _METADATA_FIELDS[kind]
            or receipt.get("publication_contract") != _PUBLICATION_CONTRACT):
        raise InputError("Source receipt does not match the fixed synthetic bundle inventory")
    _validate_version_metadata(receipt, "Source receipt")
    _validate_limitations(metadata, kind, "Source receipt metadata")
    required_ancestry = ("no_parent_declared" if kind == "synthetic_exchange_software_fixture"
                         else "resolved")
    if verification["ancestry_resolved"] != required_ancestry:
        raise InputError("Source bundle ancestry does not meet the rerun contract")
    _require_exact_root_inventory(root, receipt)
    plan_path = root / "reproduction_plan.json"
    if not plan_path.is_file() or plan_path.is_symlink():
        raise InputError("Source bundle has no safe reproduction plan")
    plan, plan_raw = read_json(plan_path)
    _validate_version_metadata(plan, "Source reproduction plan")
    declared_files = {name: b"" for name in outputs if name != "reproduction_plan.json"}
    expected_plan = reproduction_plan(kind, declared_files, metadata)
    # Receipt-bound versions keep the structural plan check separate from the
    # reportable package/implementation compatibility result.
    expected_plan["package_version"] = receipt["package_version"]
    expected_plan["python_version"] = receipt["python_version"]
    if plan != expected_plan:
        raise InputError("Source reproduction plan does not match the fixed rerun contract")
    inputs = {name: _read_declared_input(root, receipt, name) for name in _DECLARED_INPUTS[kind]}
    if kind == "synthetic_exchange_software_fixture":
        if receipt.get("input_sha256") != sha256(inputs["input_config.json"]):
            raise InputError("Simulation receipt does not bind its declared configuration")
    else:
        _validate_identifiability_bindings(receipt, inputs)
    implementation, implementation_match = _implementation_comparison(receipt)
    return {
        "root": root,
        "kind": kind,
        "entry_point": RERUN_ENTRY_POINTS[kind],
        "receipt": receipt,
        "receipt_raw": receipt_raw,
        "plan_raw": plan_raw,
        "inputs": inputs,
        "verification": verification,
        "implementation": implementation,
        "implementation_match": implementation_match,
    }


def _safe_staged_path(staging: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise InputError("Fixed staging mapping contains an unsafe path")
    destination = staging / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise InputError("Staging destination already exists")
    return destination


def _stage_inputs(source: dict, staging: Path) -> dict:
    kind = source["kind"]
    entries = []
    for name, relative in sorted(_INPUT_MAPPINGS[kind].items()):
        raw = source["inputs"][name]
        destination = _safe_staged_path(staging, relative)
        with destination.open("xb") as stream:
            stream.write(raw)
        entries.append({"source": name, "staged": relative,
                        "sha256": sha256(raw), "size_bytes": len(raw)})
    return {"schema_version": 1, "entry_point": source["entry_point"], "inputs": entries}


def _empty_stream_summary() -> dict:
    return {"captured_sha256": sha256(b""), "captured_size_bytes": 0,
            "total_bytes_observed": 0, "truncated": False}


def _execute_entry_point(entry_point: str, staging: Path, output: Path, *, timeout: float) -> dict:
    """Execute only the current trusted runner with bounded captured output."""
    if entry_point not in set(RERUN_ENTRY_POINTS.values()):
        return {"outcome": "start_error", "returncode": None,
                "stdout": _empty_stream_summary(), "stderr": _empty_stream_summary()}
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
               "--entry-point", entry_point, "--staged", str(staging), "--out", str(output)]
    environment = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"}
    try:
        process = subprocess.Popen(
            command, cwd=str(staging), env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0,
        )
    except OSError:
        return {"outcome": "start_error", "returncode": None,
                "stdout": _empty_stream_summary(), "stderr": _empty_stream_summary()}

    overflow = threading.Event()
    states = {}
    streams = {}

    def consume(stream, summary):
        captured = bytearray()
        total = 0
        try:
            while True:
                chunk = stream.read(65_536)
                if not chunk:
                    break
                total += len(chunk)
                remaining = MAX_CAPTURED_STREAM_BYTES - len(captured)
                if remaining > 0:
                    captured.extend(chunk[:remaining])
                if total > MAX_CAPTURED_STREAM_BYTES:
                    overflow.set()
        finally:
            stream.close()
        summary.update({
            "captured_sha256": sha256(bytes(captured)),
            "captured_size_bytes": len(captured),
            "total_bytes_observed": total,
            "truncated": total > len(captured),
        })

    for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        states[name] = _empty_stream_summary()
        thread = threading.Thread(target=consume, args=(stream, states[name]), daemon=True)
        streams[name] = thread
        thread.start()

    deadline = time.monotonic() + timeout
    outcome = None
    returncode = None
    while True:
        if overflow.is_set():
            process.kill()
            outcome = "output_limit"
            returncode = process.wait()
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            process.kill()
            outcome = "timeout"
            returncode = process.wait()
            break
        try:
            returncode = process.wait(timeout=min(0.05, remaining))
            break
        except subprocess.TimeoutExpired:
            continue
    for thread in streams.values():
        thread.join(timeout=5)
    if outcome is None and overflow.is_set():
        outcome = "output_limit"
    if outcome is None:
        outcome = "completed" if returncode == 0 else "nonzero_exit"
    return {"outcome": outcome, "returncode": returncode, **states}


def _inventory(files: dict[str, bytes]) -> dict:
    return {"count": len(files), "files": {
        name: {"sha256": sha256(raw), "size_bytes": len(raw)}
        for name, raw in sorted(files.items())
    }}


def _compare_inventories(expected_inventory: dict, actual_inventory: dict,
                         input_names: set[str]) -> dict:
    expected = expected_inventory["files"]
    actual = actual_inventory["files"]
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
    mismatch_names = sorted(set(missing) | set(extra) | set(changed))
    details = []
    for name in mismatch_names[:MAX_MISMATCH_DETAILS]:
        reason = "missing" if name in missing else "extra" if name in extra else "changed"
        details.append({"name": name, "reason": reason,
                        "expected": expected.get(name), "actual": actual.get(name)})
    excluded = set(input_names) | {"reproduction_plan.json", "receipt.json"}
    payload_expected = {name: entry for name, entry in expected.items() if name not in excluded}
    payload_actual = {name: entry for name, entry in actual.items() if name not in excluded}
    payload_missing = sorted(set(payload_expected) - set(payload_actual))
    payload_extra = sorted(set(payload_actual) - set(payload_expected))
    payload_changed = sorted(name for name in set(payload_expected) & set(payload_actual)
                             if payload_expected[name] != payload_actual[name])
    payload = {
        "exact_match": not (payload_missing or payload_extra or payload_changed),
        "expected_count": len(payload_expected),
        "actual_count": len(payload_actual),
        "expected_inventory": {"count": len(payload_expected), "files": payload_expected},
        "actual_inventory": {"count": len(payload_actual), "files": payload_actual},
        "missing": payload_missing[:MAX_MISMATCH_DETAILS],
        "extra": payload_extra[:MAX_MISMATCH_DETAILS],
        "changed": payload_changed[:MAX_MISMATCH_DETAILS],
        "interpretation": "Payload-only equality is diagnostic and cannot override exact full-inventory failure.",
    }
    return {
        "exact_match": not mismatch_names,
        "expected_inventory": expected_inventory,
        "actual_inventory": actual_inventory,
        "missing": missing[:MAX_MISMATCH_DETAILS],
        "extra": extra[:MAX_MISMATCH_DETAILS],
        "changed": changed[:MAX_MISMATCH_DETAILS],
        "mismatch_count": len(mismatch_names),
        "mismatch_details": details,
        "mismatch_details_omitted": max(0, len(mismatch_names) - MAX_MISMATCH_DETAILS),
        "payload_diagnostic": payload,
    }


def _compare_output_bytes(expected: dict[str, bytes], actual: dict[str, bytes],
                          input_names: set[str]) -> dict:
    """Compare complete exact-byte inventories and a separate payload diagnostic."""
    return _compare_inventories(_inventory(expected), _inventory(actual), input_names)


def _source_inventory(source: dict) -> dict:
    files = {name: {"sha256": entry["sha256"], "size_bytes": entry["size_bytes"]}
             for name, entry in sorted(source["receipt"]["outputs"].items())}
    files["receipt.json"] = {"sha256": sha256(source["receipt_raw"]),
                             "size_bytes": len(source["receipt_raw"])}
    return {"count": len(files), "files": files}


def _actual_inventory(actual: Path, kind: str, ancestry: str) -> dict:
    verification = verify_bundle(actual, strict=True)
    if (not verification["bytes_verified"] or verification["bundle_kind"] != kind
            or verification["ancestry_resolved"] != ancestry):
        raise InputError("Generated bundle failed strict verification")
    receipt, receipt_raw = read_json(actual / "receipt.json")
    _require_exact_root_inventory(actual, receipt)
    files = {name: {"sha256": entry["sha256"], "size_bytes": entry["size_bytes"]}
             for name, entry in sorted(receipt["outputs"].items())}
    files["receipt.json"] = {"sha256": sha256(receipt_raw), "size_bytes": len(receipt_raw)}
    return {"count": len(files), "files": files}


def _markdown_report(report: dict) -> bytes:
    comparison = report["comparison"]
    lines = [
        "# Synthetic bundle reproduction check",
        "",
        f"- Status: `{report['reproduction_status']}`",
        f"- Source kind: `{report['source_bundle_kind']}`",
        f"- Entry point: `{report['entry_point']}`",
        f"- Source receipt SHA-256: `{report['source_receipt_sha256']}`",
        f"- Source plan SHA-256: `{report['source_plan_sha256']}`",
        f"- Stored/current package: `{report['stored_package_version']}` / `{report['current_package_version']}`",
        f"- Stored/current Python: `{report['stored_python_version']}` / `{report['current_python_version']}`",
        f"- Implementation match: `{report['implementation_match']}`",
        f"- Expected/actual full-inventory files: {comparison['expected_inventory']['count']} / {comparison['actual_inventory']['count']}",
        f"- Missing/extra/changed mismatches: {len(comparison['missing'])} / {len(comparison['extra'])} / {len(comparison['changed'])} (bounded lists)",
        f"- Payload-only exact match (diagnostic only): `{report['payload_diagnostic']['exact_match']}`",
        "",
        "## Interpretation limits",
        "",
    ]
    lines.extend(f"- {item}" for item in report["interpretation_limits"])
    return ("\n".join(lines) + "\n").encode("utf-8")


def _publish_reproduction_report(source: dict, output: Path, manifest: dict,
                                 report: dict) -> dict:
    files = {
        "source_bundle_receipt.json": source["receipt_raw"],
        "source_reproduction_plan.json": source["plan_raw"],
        "rerun_input_manifest.json": json_bytes(manifest),
        **source["inputs"],
        "reproduction_report.json": json_bytes(report),
        "REPORT.md": _markdown_report(report),
    }
    metadata = {
        "source_bundle_kind": source["kind"],
        "source_receipt_sha256": report["source_receipt_sha256"],
        "source_plan_sha256": report["source_plan_sha256"],
        "entry_point": source["entry_point"],
        "reproduction_status": report["reproduction_status"],
        "scientific_review": "not_established_by_this_tool",
        "biological_measurements": False,
        "physiologically_calibrated": False,
        "human_gestation_prediction": False,
    }
    plan = reproduction_plan(REPRODUCTION_BUNDLE_KIND, files, metadata)
    plan.update({
        "command": "wombmodels verify-bundle --bundle <reproduction-report-bundle> --strict",
        "inputs": ["source_bundle_receipt.json", "source_reproduction_plan.json",
                   "rerun_input_manifest.json", *sorted(source["inputs"])],
        "expected_outputs": sorted({*files, "reproduction_plan.json", "receipt.json"}),
        "limits": [*plan["limits"],
                   "A reproduction report is verified as evidence and is not recursively rerunnable."],
    })
    files["reproduction_plan.json"] = json_bytes(plan)
    publish_bundle(output, kind=REPRODUCTION_BUNDLE_KIND, input_raw=source["receipt_raw"],
                   files=files, metadata=metadata)
    return report


def rerun_bundle(bundle: Path, output: Path) -> dict:
    """Strictly verify, conditionally rerun, compare, and publish a report."""
    destination = _validate_destination(Path(output), Path(bundle))
    source = _load_rerun_source(Path(bundle))
    expected_inventory = _source_inventory(source)
    with tempfile.TemporaryDirectory(prefix="wombmodels-rerun-") as temporary:
        workspace = Path(temporary)
        staging = workspace / "inputs"
        actual = workspace / "actual"
        staging.mkdir()
        manifest = _stage_inputs(source, staging)
        execution = {
            "outcome": "not_attempted_implementation_mismatch",
            "returncode": None,
            "stdout": _empty_stream_summary(),
            "stderr": _empty_stream_summary(),
        }
        generated_bundle_bytes_verified = False
        if source["implementation_match"]:
            try:
                execution = _execute_entry_point(source["entry_point"], staging, actual,
                                                 timeout=RERUN_TIMEOUT_SECONDS)
            except OSError:
                execution = {"outcome": "start_error", "returncode": None,
                             "stdout": _empty_stream_summary(), "stderr": _empty_stream_summary()}
        if not source["implementation_match"]:
            status = "could_not_run"
            comparison = _compare_inventories(expected_inventory, {"count": 0, "files": {}},
                                              set(source["inputs"]))
        elif execution["outcome"] != "completed":
            status = "could_not_run"
            comparison = _compare_inventories(expected_inventory, {"count": 0, "files": {}},
                                              set(source["inputs"]))
        else:
            try:
                actual_inventory = _actual_inventory(actual, source["kind"],
                                                     source["verification"]["ancestry_resolved"])
            except (InputError, OSError):
                status = "could_not_run"
                execution = {**execution, "generated_bundle_error": "strict_verification_failed"}
                comparison = _compare_inventories(expected_inventory, {"count": 0, "files": {}},
                                                  set(source["inputs"]))
            else:
                generated_bundle_bytes_verified = True
                comparison = _compare_inventories(expected_inventory, actual_inventory,
                                                  set(source["inputs"]))
                status = "reproduced_exact" if comparison["exact_match"] else "not_reproduced"
        report = {
            "schema_version": 1,
            "report_kind": REPRODUCTION_BUNDLE_KIND,
            "source_bundle_kind": source["kind"],
            "source_receipt_sha256": sha256(source["receipt_raw"]),
            "source_plan_sha256": sha256(source["plan_raw"]),
            "entry_point": source["entry_point"],
            "reproduction_status": status,
            "bytes_verified": True,
            "ancestry_resolved": source["verification"]["ancestry_resolved"],
            "stored_package_version": source["receipt"].get("package_version"),
            "current_package_version": __version__,
            "stored_python_version": source["receipt"].get("python_version"),
            "current_python_version": platform.python_version(),
            "implementation_match": source["implementation_match"],
            "implementation": source["implementation"],
            "generated_bundle_bytes_verified": generated_bundle_bytes_verified,
            "expected_inventory": comparison["expected_inventory"],
            "actual_inventory": comparison["actual_inventory"],
            "comparison": comparison,
            "payload_diagnostic": comparison["payload_diagnostic"],
            "execution": execution,
            "scientific_review": "not_established_by_this_tool",
            "biological_measurements": False,
            "physiologically_calibrated": False,
            "human_gestation_prediction": False,
            "interpretation_limits": _INTERPRETATION_LIMITS,
        }
        return _publish_reproduction_report(source, destination, manifest, report)


def _runner_main(argv=None) -> int:
    """Trusted process target; arguments are supplied only by _execute_entry_point."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--entry-point", required=True, choices=set(RERUN_ENTRY_POINTS.values()))
    parser.add_argument("--staged", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.entry_point == "simulate/1":
            from wombmodels.exchange import simulate
            simulate(args.staged / "config.json", args.out)
        else:
            from wombmodels.identifiability import analyze
            analyze(args.staged / "config.json", args.staged / "simulation" / "trajectory.csv", args.out)
    except (InputError, OSError):
        print("trusted rerun rejected its staged inputs or destination", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_runner_main())
