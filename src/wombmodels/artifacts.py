"""Reproducible bundles with exclusive destinations and receipt-last publication."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import platform
import shutil
import tempfile
from pathlib import Path

from . import __version__

MAX_JSON_BYTES = 16_000_000
MAX_JSON_DEPTH = 64
MAX_JSON_INTEGER_DIGITS = 256


class InputError(ValueError):
    """A bounded input contract was not met."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def csv_bytes(columns: list[str], rows: list[dict]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def decode_json(raw: bytes):
    """Decode bounded UTF-8 JSON without duplicate keys or nonfinite numbers."""
    if len(raw) > MAX_JSON_BYTES:
        raise InputError("Input JSON exceeds the 16 MB limit")
    try:
        decoded = raw.decode("utf-8")
        # Bound container nesting independently of the Python JSON decoder's
        # implementation and recursion behavior. JSON syntax within strings,
        # including escaped quotes and backslashes, does not add nesting.
        depth = 0
        in_string = escaped = False
        for character in decoded:
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character in "[{":
                depth += 1
                if depth > MAX_JSON_DEPTH:
                    raise InputError(f"Input JSON exceeds the {MAX_JSON_DEPTH}-level nesting limit")
            elif character in "]}":
                depth -= 1

        def reject_constant(value):
            raise InputError(f"Nonfinite JSON number: {value}")

        def finite_float(value):
            result = float(value)
            if not math.isfinite(result):
                raise InputError("Nonfinite JSON number")
            return result

        def bounded_integer(value):
            if len(value.lstrip("-")) > MAX_JSON_INTEGER_DIGITS:
                raise InputError(f"JSON integers must have at most {MAX_JSON_INTEGER_DIGITS} digits")
            return int(value)

        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise InputError(f"Duplicate JSON field: {key}")
                result[key] = value
            return result

        return json.loads(decoded, parse_constant=reject_constant,
                          parse_float=finite_float, parse_int=bounded_integer,
                          object_pairs_hook=unique_object)
    except InputError:
        raise
    except (ValueError, RecursionError, OverflowError) as exc:
        raise InputError("Input must be valid bounded UTF-8 JSON") from exc


def read_json(path: Path) -> tuple[dict, bytes]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise InputError("Input JSON must be an object")
    return value, raw


def implementation_hashes() -> dict[str, str]:
    directory = Path(__file__).parent
    result = {f"src/wombmodels/{path.name}": sha256(path.read_bytes())
              for path in sorted(directory.glob("*.py"))}
    root = directory.parents[1]
    result.update({f"schemas/{path.name}": sha256(path.read_bytes())
                   for path in sorted((root / "schemas").glob("*.json"))})
    project = root / "pyproject.toml"
    if project.is_file():
        result["pyproject.toml"] = sha256(project.read_bytes())
    return result


def reproduction_plan(kind: str, files: dict[str, bytes], metadata: dict) -> dict:
    """Describe what rerunning this bundle would require, without absolute paths.

    The plan travels inside the bundle so a relocated copy stays self-describing.
    Verifying bytes and rerunning the model are separate statuses; neither
    establishes that a model is biologically valid.
    """
    command = {
        "synthetic_exchange_software_fixture": "wombmodels simulate --config <config.json> --out <new-dir>",
        "synthetic_exchange_observability_diagnostic":
            "wombmodels identifiability-report --config <config.json> --trajectory <trajectory.csv> --out <new-dir>",
        "synthetic_exchange_design_sweep": "wombmodels design-sweep --config <config.json> --out <new-dir>",
        "reviewed_evidence_ledger_report": "wombmodels evidence-report --ledger <evidence.json> --out <new-dir>",
        "developmental_observation_dataset_report":
            "wombmodels validate-observations --dataset <dataset.json> --out <new-dir>",
        "developmental_observation_intake":
            "wombmodels validate-observations --dataset <input_dataset.json> --out <new-dir>",
        "yolk_sac_functional_source_audit":
            "wombmodels audit-yolk-sac-source --workbook <external-pinned-source.xlsx> --out <new-dir>",
        "developmental_boundary_source_linkage_audit":
            "wombmodels audit-boundary-source --archive <external-pinned-source.zip> --out <new-dir>",
        "specimen_phenotype_intake":
            "wombmodels validate-phenotypes --dataset <input_phenotypes.json> --source-root <external-source-dir> --out <new-dir>",
        "published_endpoint_source_audit":
            "wombmodels audit-hori-source --workbook <external-pinned-source.xlsx> --out <new-dir>",
        "functional_readout_source_audit":
            "wombmodels audit-fattahi-source --workbook <external-pinned-source.xlsx> --out <new-dir>",
        "native_placental_source_recovery":
            "wombmodels audit-roelofsen-source --supplement <external-pinned-source.docx> --out <new-dir>",
        "human_placental_perfusion_observation_audit":
            "wombmodels audit-mathiesen-source --article <external-pinned-article.html> --workbook <external-pinned-observations.xlsx> --table1 <external-pinned-run-map.png> --success-table <external-pinned-selection.docx> --s3-table <external-pinned-unit-key-screen.docx> --out <new-dir>",
        "niche_mechanics_development_source_audit":
            "wombmodels audit-guo-source --workbook <external-pinned-source.xlsx> --out <new-dir>",
        "early_interface_source_linkage_audit":
            "wombmodels audit-crest-linkage --sdrf <external-pinned-source.sdrf.txt> --archive <external-pinned-code.zip> --out <new-dir>",
        "dimensionless_transport_theory": "wombmodels transport-model --config <config.json> --out <new-dir>",
        "dimensionless_transport_identifiability": "wombmodels transport-identifiability --config <input_config.json> --out <new-dir>",
        "dimensionless_collection_accounting": "wombmodels collection-accounting --config <input_config.json> --out <new-dir>",
        "dimensionless_mechanics_theory": "wombmodels mechanics-model --config <config.json> --out <new-dir>",
    }.get(kind)
    parent = metadata.get("parent_receipt_file")
    return {
        "schema_version": 1,
        "bundle_kind": kind,
        "package_version": __version__,
        "python_version": platform.python_version(),
        "declared_dependencies": ["python>=3.10 standard library only"],
        "command": command or f"no recorded command template for bundle kind {kind}",
        "inputs": (["input_source_manifest.json", "external pinned source workbook (not bundled)"]
                   if kind in {"published_endpoint_source_audit", "functional_readout_source_audit", "niche_mechanics_development_source_audit", "yolk_sac_functional_source_audit"} else
                   ["input_source_manifest.json", "external pinned source supplement (not bundled)"]
                   if kind == "native_placental_source_recovery" else
                   ["input_source_manifest.json", "external pinned article, data workbook, run table and selection table (not bundled)"]
                   if kind == "human_placental_perfusion_observation_audit" else
                   ["input_source_manifest.json", "external pinned source archive (not bundled)"]
                   if kind == "developmental_boundary_source_linkage_audit" else
                   ["input_source_manifest.json", "external pinned SDRF and code archive (not bundled)"]
                   if kind == "early_interface_source_linkage_audit" else
                   ["input_phenotypes.json", "external source files for optional byte verification (not bundled)"]
                   if kind == "specimen_phenotype_intake" else
                   ["input_config.json"] if kind in {"dimensionless_transport_identifiability", "dimensionless_collection_accounting"} else
                   ["input_dataset.json"] if kind == "developmental_observation_intake"
                   else ["source_config.json"] if "source_config.json" in files else []),
        "parent_bundle_receipt": parent,
        # The plan lists itself and the receipt: a reviewer checking a relocated
        # bundle should see the complete published file set.
        "expected_outputs": sorted({*files, "reproduction_plan.json", "receipt.json"}),
        "limits": [
            "Matching hashes establish bundle integrity only, not numerical correctness, "
            "parameter identifiability or biological validity.",
            ("Source audit/intake preserves reported units; it does not establish measurement validity, rights, analysis eligibility or predict human gestation."
             if kind in {"developmental_observation_intake", "published_endpoint_source_audit", "functional_readout_source_audit", "native_placental_source_recovery", "human_placental_perfusion_observation_audit", "niche_mechanics_development_source_audit", "yolk_sac_functional_source_audit", "developmental_boundary_source_linkage_audit", "early_interface_source_linkage_audit", "specimen_phenotype_intake"} else
             "Every value in these fixtures is dimensionless. Nothing here predicts human gestation."),
            "Verification never reruns the model. A rerun needs the recorded package version and "
            "the exact inputs listed above.",
        ],
    }


def publish_bundle(output: Path, *, kind: str, input_raw: bytes,
                   files: dict[str, bytes], metadata: dict) -> dict:
    """Publish individual files atomically; receipt.json commits a complete bundle.

    A fresh directory is reserved using mkdir (exclusive on every supported OS).
    Files are hard-linked from a sibling staging directory, so no existing file
    can be overwritten. A failed publication leaves no valid receipt. Consumers
    must require and verify the receipt before using a bundle.
    """
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise InputError(f"Output already exists: {output}")
    if not files or any(Path(name).name != name or name in {".", "..", "receipt.json"}
                        for name in files):
        raise InputError("Bundle artifact names must be simple non-receipt filenames")
    if "reproduction_plan.json" not in files:
        files = {**files, "reproduction_plan.json": json_bytes(reproduction_plan(kind, files, metadata))}
    receipt = {"schema_version": 1, "bundle_kind": kind,
               "package_version": __version__, "python_version": platform.python_version(),
               "input_sha256": sha256(input_raw),
               "implementation_sha256": implementation_hashes(),
               "outputs": {name: {"sha256": sha256(raw), "size_bytes": len(raw)}
                           for name, raw in sorted(files.items())},
               "metadata": metadata,
               "publication_contract": "Exclusive directory; atomic files; receipt published last."}
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for name, raw in files.items():
            (staging / name).write_bytes(raw)
        (staging / "receipt.json").write_bytes(json_bytes(receipt))
        try:
            output.mkdir()
        except FileExistsError as exc:
            raise InputError(f"Output already exists: {output}") from exc
        for name in sorted(files):
            os.link(staging / name, output / name)
        os.link(staging / "receipt.json", output / "receipt.json")
    finally:
        shutil.rmtree(staging)
    return receipt
