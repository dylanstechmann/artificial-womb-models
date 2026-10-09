"""Pinned source-label linkage audit; no biological identity inference or fit."""
from __future__ import annotations

import csv
import io
import re
import zipfile
import zlib
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256

ARCHIVE_SHA256 = "36adfb6ec13b6df189c116e19ce18455f3c0b00052838657c59f0eda65784c75"
ARTICLE_URL = "https://doi.org/10.15252/embj.2022113280"
ARCHIVE_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.15252%2Fembj.2022113280/MediaObjects/44318_2023_BFEMBJ2022113280_MOESM20_ESM.zip")
MEMBERS = {
    "displacement.csv": "Figure 6/Panel i and j/Displacement analysis.csv",
    "tracks.csv": "Figure 6/Panel c and d/TB migration tracks.csv",
    "cell-counts.csv": "Figure 6/Panel h/EPI cell counts.csv",
    "lengths.csv": "Figure 6/Panel g/Embryo length quantification.csv",
}
HEADERS = {
    "displacement.csv": ["Dataset", "Orientation", "Displacing tissue", "Z stack ID",
        "Line ID", "Time post E3.5 (hours)", "Normalized displacement (um)"],
    "tracks.csv": ["Individual Track ID", "Original Track ID", "Imaging time (hours)",
        "Imaging time (min)", "X (um)", "Y (um)", "Cell track generation",
        "Cell track divergence point (division)"],
    "cell-counts.csv": ["Embryo ID", "Dataset", "Cell number", "Embryo genotype"],
    "lengths.csv": ["Embryo ID", "Dataset", "Length (um)", "Genotype"],
}


def _number(token, *, integer=False, nonnegative=False):
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise InputError("Malformed source numeric text") from exc
    if (not value.is_finite() or value.copy_abs() > Decimal("1e12")
            or nonnegative and value < 0
            or integer and value != value.to_integral_value()):
        raise InputError("Nonfinite, out-of-range or unsupported source numeric value")
    return value


def _table(raw, name):
    if len(raw) > 256_000:
        raise InputError("Source CSV exceeds byte limit")
    try:
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise InputError("Unsupported source CSV encoding or structure") from exc
    if (not 2 <= len(rows) <= 3_001 or rows[0] != HEADERS[name]
            or any(len(row) != len(rows[0]) for row in rows)
            or any(not 1 <= len(v) <= 128 or any(ord(c) < 32 for c in v)
                   for row in rows for v in row)):
        raise InputError("Changed source header, missing field or CSV bounds exceeded")
    records = []
    for i, row in enumerate(rows[1:], 2):
        item = dict(zip(rows[0], row))
        if "Dataset" in item and not re.fullmatch(r"[0-9]{6}", item["Dataset"]):
            raise InputError("Unsupported source dataset label")
        if "Embryo ID" in item and not re.fullmatch(r"E[1-9][0-9]{0,4}", item["Embryo ID"]):
            raise InputError("Unsupported source embryo label")
        if name == "displacement.csv":
            if item["Orientation"] not in {"Downward", "Upward"} or item["Displacing tissue"] not in {"EPI", "TE_inner"}:
                raise InputError("Changed orientation or tissue label")
            for field in ("Z stack ID", "Line ID"):
                if not re.fullmatch(r"[0-9]{1,6}", item[field]):
                    raise InputError("Unsupported stack or line label")
            _number(item["Time post E3.5 (hours)"], nonnegative=True)
            _number(item["Normalized displacement (um)"])
        elif name == "tracks.csv":
            for field in ("Individual Track ID", "Original Track ID", "Cell track generation"):
                if not re.fullmatch(r"[0-9]{1,6}", item[field]):
                    raise InputError("Unsupported cell-track label")
            _number(item["Imaging time (hours)"], integer=True, nonnegative=True)
            minute = _number(item["Imaging time (min)"], integer=True, nonnegative=True)
            if minute >= 60 or item["Cell track divergence point (division)"] not in {"0", "1"}:
                raise InputError("Unsupported imaging minute or division flag")
            for field in ("X (um)", "Y (um)"):
                _number(item[field])
        else:
            field = "Cell number" if name == "cell-counts.csv" else "Length (um)"
            _number(item[field], integer=name == "cell-counts.csv", nonnegative=True)
            genotype = item["Embryo genotype" if name == "cell-counts.csv" else "Genotype"]
            if genotype not in {"WT", "het", "del"}:
                raise InputError("Unsupported endpoint genotype label")
        item["source_row"] = i
        records.append(item)
    return records


def _recover(raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if (len(members) > 128 or len(set(names)) != len(names)
                    or sum(item.file_size for item in members) > 20_000_000
                    or any(item.file_size > 8_000_000 or item.flag_bits & 1 for item in members)
                    or any("\\" in name or ":" in name or name.startswith("/")
                           or any(p in {"", ".", ".."} for p in name.rstrip("/").split("/")) for name in names)):
                raise InputError("Archive member paths, sizes or encryption unsupported")
            native = {}
            for name, member in MEMBERS.items():
                info = archive.getinfo(member)
                if info.file_size > 256_000:
                    raise InputError("Selected source CSV exceeds byte limit")
                native[name] = archive.read(member)
    except (zipfile.BadZipFile, KeyError, RuntimeError, EOFError, ValueError, zlib.error) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("Unsupported source archive structure") from exc
    return native, {name: _table(data, name) for name, data in native.items()}


def _unique(rows, key):
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result:
            raise InputError("Duplicate source observation key; refusing many-to-many linkage")
        result[identity] = row
    return result


def _link(tables):
    key = lambda r: (r["Dataset"], r["Embryo ID"])
    cells = _unique(tables["cell-counts.csv"], key)
    lengths = _unique(tables["lengths.csv"], key)
    endpoints = []
    for dataset, embryo in sorted(cells.keys() | lengths.keys()):
        c, l = cells.get((dataset, embryo)), lengths.get((dataset, embryo))
        status = ("key_match_candidate" if c["Embryo genotype"] == l["Genotype"]
                  else "key_match_genotype_conflict") if c and l else "cell_only" if c else "length_only"
        endpoints.append({"dataset_label": dataset, "embryo_label": embryo,
            "linkage_status": status, "cell_source_row": c["source_row"] if c else None,
            "length_source_row": l["source_row"] if l else None,
            "cell_number_text": c["Cell number"] if c else None,
            "length_um_text": l["Length (um)"] if l else None,
            "cell_genotype": c["Embryo genotype"] if c else None,
            "length_genotype": l["Genotype"] if l else None,
            "biological_identity_verified": False, "independence_verified": False})
    dkey = lambda r: (r["Dataset"], r["Orientation"], r["Z stack ID"], r["Line ID"],
                      _number(r["Time post E3.5 (hours)"]), r["Displacing tissue"])
    displacement = _unique(tables["displacement.csv"], dkey)
    pair_keys = sorted({k[:-1] for k in displacement})
    pairs = []
    for k in pair_keys:
        e, t = displacement.get((*k, "EPI")), displacement.get((*k, "TE_inner"))
        pairs.append({"dataset_label": k[0], "orientation_label": k[1], "stack_label": k[2],
            "line_label": k[3], "EPI_source_row": e["source_row"] if e else None,
            "TE_inner_source_row": t["source_row"] if t else None,
            "EPI_time_text": e["Time post E3.5 (hours)"] if e else None,
            "TE_inner_time_text": t["Time post E3.5 (hours)"] if t else None,
            "EPI_displacement_um_text": e["Normalized displacement (um)"] if e else None,
            "TE_inner_displacement_um_text": t["Normalized displacement (um)"] if t else None,
            "linkage_status": "same_measurement_labels_candidate" if e and t else "tissue_counterpart_missing",
            "embryo_id": None, "independence_verified": False})
    _unique(tables["tracks.csv"], lambda r: (r["Individual Track ID"],
        _number(r["Imaging time (hours)"]), _number(r["Imaging time (min)"])))
    groups = defaultdict(list)
    for r in tables["displacement.csv"]:
        groups[(r["Dataset"], r["Orientation"])].append(r)
    summaries = [{"dataset_label": ds, "orientation_label": orient, "n_source_rows": len(rows),
                  "n_stack_labels": len({r["Z stack ID"] for r in rows}),
                  "n_line_labels": len({r["Line ID"] for r in rows}),
                  "n_time_values": len({_number(r["Time post E3.5 (hours)"]) for r in rows}),
                  "embryo_identity": "not_reported_in_selected_table"}
                 for (ds, orient), rows in sorted(groups.items())]
    endpoint_datasets = {r["dataset_label"] for r in endpoints}
    shared = sorted({r["Dataset"] for r in tables["displacement.csv"]} & endpoint_datasets)
    tracks = tables["tracks.csv"]
    qualification = {"schema_version": 1, "source_review_status": "candidate", "human_review": "pending",
        "source_row_counts": {name: len(rows) for name, rows in tables.items()},
        "endpoint_key": ["Dataset", "Embryo ID"],
        "endpoint_linkage_counts": dict(Counter(r["linkage_status"] for r in endpoints)),
        "endpoint_embryo_labels_reused_across_datasets": sorted(e for e, n in
            Counter(r["embryo_label"] for r in endpoints).items() if n > 1),
        "displacement_pair_counts": dict(Counter(r["linkage_status"] for r in pairs)),
        "shared_dataset_labels_with_endpoints": shared,
        "boundary_to_endpoint_linkage": "not_established_missing_displacement_embryo_id",
        "n_qualified_boundary_outcome_joins": 0,
        "cell_tracks": {"n_individual_track_labels": len({r["Individual Track ID"] for r in tracks}),
            "n_original_track_labels": len({r["Original Track ID"] for r in tracks}),
            "caption_n": 29, "caption_locator": "Figure 6C/D",
            "interpretation": "CSV track-label count and caption n require definition/reconciliation; tracks are not embryos."},
        "zero_cell_counts_retained": sum(_number(r["Cell number"]) == 0 for r in cells.values()),
        "source_modified": False, "media_or_code_executed": False,
        "biological_assay_performed": False, "biological_fit_performed": False,
        "limits": [
            "Compound source-key equality is a linkage candidate, not authenticated biological identity or independence.",
            "Dataset codes are opaque source strings, not inferred dates, litter IDs or unique embryos. Sharing a code cannot join displacement to endpoints.",
            "Stack/line/time pairs remain nested observations; no averaging, trajectory gap filling, unit conversion or inferential effect is performed.",
            "EPI and TE_inner are original table labels. The caption's membrane interpretation, normalization and coordinate mapping require review.",
            "Source hour/minute labels and units are preserved. Imaging-time and post-E3.5 clocks are not concatenated or assigned to a biological model.",
            "Cell tracks have no source embryo/dataset label in this table; division/generation labels are retained without inventing lineage or independence.",
            "Starting cohort, exclusions, failures, support receipt and later function remain unqualified. No full gestation claim follows.",
        ]}
    return endpoints, pairs, summaries, qualification


def audit_boundary_source(archive_path: Path, output: Path):
    path = Path(archive_path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise InputError("Source archive must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(8_000_001)
    if len(raw) > 8_000_000 or sha256(raw) != ARCHIVE_SHA256:
        raise InputError("Source archive size/hash differs from inspected revision; a new audit is required")
    native, tables = _recover(raw)
    endpoints, pairs, summaries, qualification = _link(tables)
    manifest = {"schema_version": 1, "article_url": ARTICLE_URL, "source_url": ARCHIVE_URL,
        "filename": path.name, "sha256": sha256(raw), "size_bytes": len(raw),
        "external_source_required": True, "selected_members": [
            {"member": MEMBERS[name], "bundle_filename": name, "bytes": len(data), "sha256": sha256(data)}
            for name, data in native.items()], "source_modified": False}
    report = "\n".join(["# Mouse developmental-boundary source linkage", "",
        "AI-assisted read-only native CSV audit; human scientific review pending.",
        "Selected source CSVs are copied byte-for-byte; row locators include the header as row 1.",
        "Endpoint key matches: " + str(qualification["endpoint_linkage_counts"]) + ".",
        "Displacement tissue-label pairs: " + str(qualification["displacement_pair_counts"]) + ".",
        "No boundary-to-endpoint join is qualified: displacement has no embryo ID.",
        "A shared dataset code cannot repair that missing identity. Source-row counts are not verified biological n.",
        "", f"[Bondarenko et al., 2023]({ARTICLE_URL}). Article declares CC BY 4.0; source-specific review pending.",
        "The full source archive and its media remain external. No code or media is executed, biological model fitted or observation dataset promoted.",
        "", "## Qualification limits", "", *["- " + v for v in qualification["limits"]], ""])
    return publish_bundle(output, kind="developmental_boundary_source_linkage_audit", input_raw=raw,
        files={**native, "input_source_manifest.json": json_bytes(manifest),
            "endpoint_linkage_candidates.csv": csv_bytes(list(endpoints[0]), endpoints),
            "displacement_label_pairs.csv": csv_bytes(list(pairs[0]), pairs),
            "displacement_groups.csv": csv_bytes(list(summaries[0]), summaries),
            "qualification.json": json_bytes(qualification), "REPORT.md": report.encode()},
        metadata={"source_review_status": "candidate", "biological_fit_performed": False,
                  "biological_assay_performed": False, "source_modified": False})
