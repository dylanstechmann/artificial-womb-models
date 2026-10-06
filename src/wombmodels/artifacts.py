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

MAX_JSON_BYTES = 2_000_000


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
        raise InputError("Input JSON exceeds the 2 MB limit")
    try:
        def reject_constant(value):
            raise InputError(f"Nonfinite JSON number: {value}")

        def finite_float(value):
            result = float(value)
            if not math.isfinite(result):
                raise InputError("Nonfinite JSON number")
            return result

        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise InputError(f"Duplicate JSON field: {key}")
                result[key] = value
            return result

        return json.loads(raw.decode("utf-8"), parse_constant=reject_constant,
                          parse_float=finite_float, object_pairs_hook=unique_object)
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
    project = directory.parents[1] / "pyproject.toml"
    if project.is_file():
        result["pyproject.toml"] = sha256(project.read_bytes())
    return result


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
