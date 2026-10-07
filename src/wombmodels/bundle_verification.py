"""Verify a published model bundle after it has been copied somewhere else.

The verifier reads only the bundle directory, uses the Python standard library,
and never consults the machine that produced the bundle. It reports three
separate statuses and never merges them:

* ``bytes_verified``    — do the files match the receipt's hashes and sizes?
* ``ancestry_resolved`` — does the recorded parent receipt travel with the
  bundle and match the hash this bundle declares for it?
* ``scientific_review`` — always ``not_established_by_this_tool``.

A fourth status, ``reproduction``, is always ``not_attempted``: verifying bytes
is not rerunning a model. The bundle's reproduction plan records what a rerun
would additionally require.
"""
from __future__ import annotations

from pathlib import Path

from .artifacts import InputError, read_json, sha256

MAX_FILE_BYTES = 50_000_000
MAX_FILES = 500
STATUS_NOT_REVIEWED = "not_established_by_this_tool"
KNOWN_BUNDLE_KINDS = frozenset({
    "synthetic_exchange_software_fixture",
    "synthetic_exchange_observability_diagnostic",
    "synthetic_exchange_design_sweep",
    "reviewed_evidence_ledger_report",
    "developmental_observation_dataset_report",
    "dimensionless_transport_theory",
    "dimensionless_mechanics_theory",
    "dimensionless_transport_numerical_verification",
    "dimensionless_transport_regime_matrix_verification",
    "dimensionless_mechanics_numerical_verification",
})


def _receipt_structure_errors(receipt: dict) -> list[str]:
    errors = []
    if receipt.get("schema_version") != 1:
        errors.append("receipt schema_version must be 1")
    kind = receipt.get("bundle_kind")
    if not isinstance(kind, str) or not kind:
        errors.append("receipt bundle_kind must be a non-empty string")
    for field in ("package_version", "python_version", "input_sha256"):
        if not isinstance(receipt.get(field), str) or not receipt[field]:
            errors.append(f"receipt {field} must be a non-empty string")
    if not isinstance(receipt.get("implementation_sha256"), dict) or not receipt["implementation_sha256"]:
        errors.append("receipt implementation_sha256 must record the publishing implementation")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        errors.append("receipt outputs must list at least one file")
        return errors
    if len(outputs) > MAX_FILES:
        errors.append(f"receipt declares more than {MAX_FILES} outputs")
    for name, entry in sorted(outputs.items()):
        if Path(name).name != name or name in {".", "..", "receipt.json"}:
            errors.append(f"receipt output name is not a simple filename: {name!r}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"receipt output {name} must be an object")
            continue
        if not isinstance(entry.get("sha256"), str) or len(entry.get("sha256", "")) != 64:
            errors.append(f"receipt output {name} needs a 64-character sha256")
        if not isinstance(entry.get("size_bytes"), int) or entry["size_bytes"] < 0:
            errors.append(f"receipt output {name} needs a byte count")
    return errors


def verify_bundle(directory: Path, *, strict: bool = False) -> dict:
    """Return a verification report for one published bundle directory.

    ``strict`` additionally fails when the directory holds files the receipt does
    not declare, or when the receipt names a bundle kind this package does not
    publish.
    """
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise InputError(f"Bundle directory does not exist: {root}")
    receipt_path = root / "receipt.json"
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise InputError(f"Bundle has no receipt.json: {root}")
    try:
        receipt, receipt_raw = read_json(receipt_path)
    except InputError as exc:
        raise InputError(f"Bundle receipt is not readable bounded JSON: {exc}") from None

    errors = _receipt_structure_errors(receipt)
    warnings: list[str] = []
    kind = receipt.get("bundle_kind")
    if isinstance(kind, str) and kind not in KNOWN_BUNDLE_KINDS:
        message = f"receipt declares a bundle kind this package does not publish: {kind}"
        (errors if strict else warnings).append(message)

    outputs = receipt.get("outputs") if isinstance(receipt.get("outputs"), dict) else {}
    files: dict[str, dict] = {}
    for name, entry in sorted(outputs.items()):
        if Path(name).name != name or name in {".", "..", "receipt.json"}:
            continue
        path = root / name
        if path.is_symlink():
            errors.append(f"declared output is a symlink: {name}")
            files[name] = {"present": False, "symlink": True}
            continue
        if not path.is_file():
            errors.append(f"declared output is missing from the bundle: {name}")
            files[name] = {"present": False}
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            errors.append(f"declared output exceeds the {MAX_FILE_BYTES} byte read limit: {name}")
            files[name] = {"present": True, "bytes": size, "read": False}
            continue
        raw = path.read_bytes()
        digest = sha256(raw)
        declared = entry if isinstance(entry, dict) else {}
        hash_match = digest == declared.get("sha256")
        size_match = len(raw) == declared.get("size_bytes")
        if not hash_match:
            errors.append(f"output bytes do not match the receipt hash: {name}")
        if not size_match:
            errors.append(f"output byte count does not match the receipt: {name}")
        files[name] = {"present": True, "bytes": len(raw), "sha256": digest,
                       "hash_match": hash_match, "size_match": size_match}

    present = {path.name for path in root.iterdir() if path.is_file() and not path.is_symlink()}
    undeclared = sorted(present - set(outputs) - {"receipt.json"})
    for name in undeclared:
        message = f"bundle holds a file the receipt does not declare: {name}"
        (errors if strict else warnings).append(message)

    metadata = receipt.get("metadata") if isinstance(receipt.get("metadata"), dict) else {}
    parent_file = metadata.get("parent_receipt_file")
    parent_hash = metadata.get("parent_receipt_sha256")
    ancestry = {"declared_parent_receipt": parent_file, "declared_parent_sha256": parent_hash}
    if parent_file is None and parent_hash is None:
        ancestry_status = "no_parent_declared"
    elif not isinstance(parent_file, str) or not isinstance(parent_hash, str):
        errors.append("bundle declares a parent receipt without both a filename and a hash")
        ancestry_status = "unresolved"
    else:
        result = files.get(parent_file)
        if result is None:
            errors.append(f"declared parent receipt is not a receipt-listed output: {parent_file}")
            ancestry_status = "unresolved"
        elif not result.get("present"):
            errors.append(f"declared parent receipt is absent from the bundle: {parent_file}")
            ancestry_status = "unresolved"
        elif result.get("sha256") != parent_hash:
            errors.append(f"declared parent receipt hash does not match the archived bytes: {parent_file}")
            ancestry_status = "unresolved"
        else:
            ancestry_status = "resolved"
            ancestry["observed_parent_sha256"] = result["sha256"]

    plan = None
    if (root / "reproduction_plan.json").is_file() and not (root / "reproduction_plan.json").is_symlink():
        try:
            plan, _raw = read_json(root / "reproduction_plan.json")
        except InputError:
            errors.append("reproduction_plan.json is not readable bounded JSON")
    else:
        warnings.append("bundle has no reproduction_plan.json; it predates recorded plans")

    return {
        "schema_version": 1,
        "bundle": root.name,
        "bundle_kind": kind,
        "bytes_verified": not errors,
        "ancestry_resolved": ancestry_status,
        "scientific_review": STATUS_NOT_REVIEWED,
        "reproduction": "not_attempted",
        "receipt_sha256": sha256(receipt_raw),
        "package_version_at_publication": receipt.get("package_version"),
        "python_version_at_publication": receipt.get("python_version"),
        "declared_dependencies": (plan or {}).get("declared_dependencies"),
        "rerun_command": (plan or {}).get("command"),
        "inventory": {"declared_outputs": len(outputs), "verified_outputs":
                      sum(1 for item in files.values() if item.get("hash_match")),
                      "undeclared_files": undeclared},
        "ancestry": ancestry,
        "files": files,
        "errors": errors,
        "warnings": warnings,
        "limits": [
            "Matching hashes establish bundle integrity only. They do not establish numerical accuracy, "
            "parameter identifiability, or any biological conclusion.",
            "Ancestry resolution compares the parent receipt carried inside this bundle with the hash this "
            "bundle declares. It cannot authenticate the original run environment.",
            "Every fixture value in this package is dimensionless. Verification says nothing about human "
            "gestation, surrogacy or congenital outcomes.",
            "This command never reruns a model.",
        ],
    }
