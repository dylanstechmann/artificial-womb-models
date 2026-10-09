"""Recover pinned native Prism tables from DOCX without launching OLE or analyses."""
from __future__ import annotations

import csv
import io
import math
import re
import struct
import zipfile
from pathlib import Path

from .artifacts import InputError, csv_bytes, decode_json, json_bytes, publish_bundle, sha256
from .roelofsen_intake import candidate_intake

SUPPLEMENT_SHA256 = "ccab1bae3d666024b35e256cf9fb421217fcbba226ea5a294182002ab0a8e108"
ARTICLE_URL = "https://link.springer.com/article/10.1007/s00204-026-04418-8"
SUPPLEMENT_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1007%2Fs00204-026-04418-8/MediaObjects/204_2026_4418_MOESM1_ESM.docx")
END, FREE = 0xFFFFFFFE, 0xFFFFFFFF
GUID = re.compile(r"[0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12}")


def _regular_contents(raw: bytes) -> bytes:
    """Limited MS-CFB v3 reader: one regular-sector CONTENTS stream, no mini streams.

    Header layout: https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cfb/68530324-9d3d-4441-9ea9-66a2c8f79567
    """
    if (not 1024 <= len(raw) <= 131072 or len(raw) % 512 or raw[:8] != bytes.fromhex("d0cf11e0a1b11ae1")
            or struct.unpack_from("<4H", raw, 26) != (3, 0xFFFE, 9, 6)):
        raise InputError("Unsupported bounded CFB version/sector layout")
    u32 = lambda offset: struct.unpack_from("<I", raw, offset)[0]
    if u32(40) != 0 or u32(56) != 4096 or u32(68) != END or u32(72) != 0:
        raise InputError("External DIFAT or nonstandard CFB layout is unsupported")
    count = len(raw)//512 - 1
    n_fat = u32(44)
    if not 1 <= n_fat <= 4:
        raise InputError("Unsupported FAT sector count")
    inline = struct.unpack_from("<109I", raw, 76)
    fat_ids = inline[:n_fat]
    if len(set(fat_ids)) != n_fat or any(s >= count for s in fat_ids) or any(s != FREE for s in inline[n_fat:]):
        raise InputError("Invalid or duplicate inline FAT sectors")
    sector = lambda s: raw[(s+1)*512:(s+2)*512]
    fat_bytes = b"".join(sector(s) for s in fat_ids)
    fat = struct.unpack("<" + "I"*(len(fat_bytes)//4), fat_bytes)
    if len(fat) < count or any(fat[s] != 0xFFFFFFFD for s in fat_ids):
        raise InputError("Invalid FAT coverage/markers")

    def chain(start, forbidden):
        result, seen = [], set()
        while start != END:
            if start >= count or start in seen or start in forbidden:
                raise InputError("CFB chain is cyclic, out of range or overlaps reserved sectors")
            seen.add(start)
            result.append(start)
            start = fat[start]
        return result

    directory_ids = chain(u32(48), set(fat_ids))
    directory = b"".join(sector(s) for s in directory_ids)
    candidates = []
    for offset in range(0, len(directory), 128):
        entry = directory[offset:offset+128]
        if entry[66] != 2:
            continue
        length = struct.unpack_from("<H", entry, 64)[0]
        if not 2 <= length <= 64 or length % 2 or entry[length-2:length] != b"\0\0":
            raise InputError("Invalid CFB directory stream name")
        try:
            name = entry[:length-2].decode("utf-16-le")
        except UnicodeError as exc:
            raise InputError("Invalid CFB stream-name encoding") from exc
        if name == "CONTENTS":
            candidates.append((struct.unpack_from("<I", entry, 116)[0], struct.unpack_from("<Q", entry, 120)[0]))
    if len(candidates) != 1:
        raise InputError("Expected exactly one CONTENTS stream")
    start, size = candidates[0]
    if not 4096 <= size <= 131072:
        raise InputError("Mini-stream or oversized CONTENTS is unsupported")
    ids = chain(start, set(fat_ids) | set(directory_ids))
    if len(ids) != (size+511)//512:
        raise InputError("CONTENTS chain length differs from declared size")
    content = b"".join(sector(s) for s in ids)[:size]
    if struct.unpack_from("<I", content)[0] != len(content) or content[4:8] != b"PK\x03\x04":
        raise InputError("Unsupported Prism CONTENTS length prefix/native ZIP")
    return content[4:]


def _bounded_zip(raw, maximum_members, maximum_total, maximum_member):
    archive = zipfile.ZipFile(io.BytesIO(raw))
    members = archive.infolist()
    if (len(members) > maximum_members or len({i.filename for i in members}) != len(members)
            or sum(i.file_size for i in members) > maximum_total
            or any(i.file_size > maximum_member or i.flag_bits & 1 for i in members)):
        archive.close()
        raise InputError("Source archive exceeds bounds or has duplicate/encrypted members")
    return archive


def _uid(value):
    if not isinstance(value, str) or not GUID.fullmatch(value):
        raise InputError("Native table/set identifier must be a supported GUID")
    return value


def _title(value):
    if isinstance(value, dict):
        value = value.get("string")
    if not isinstance(value, str) or not value.strip() or len(value) > 300:
        raise InputError("Native source title must be bounded text")
    return value


def _tables(native: bytes, object_index: int):
    """Recover selected native CSV bytes and metadata, never evaluate saved analyses."""
    result = []
    with _bounded_zip(native, 200, 2_000_000, 500_000) as archive:
        names = sorted(name for name in archive.namelist() if re.fullmatch(r"data/sheets/[0-9A-F-]+/sheet\.json", name))
        expected_count = 4 if object_index == 5 else 1
        if len(names) != expected_count:
            raise InputError("Native sheet inventory differs from the inspected object")
        for name in names:
            sheet = decode_json(archive.read(name))
            table = sheet["table"]
            title = _title(sheet["title"])
            if (object_index == 5 and (table["format"] != "xy" or table["replicatesCount"] != 4
                    or title not in {"THAL % of ID", "AM % of ID", "VA % of ID", "AP % of ID"})):
                raise InputError("Unexpected normalized trajectory table structure")
            if object_index == 6 and (table["format"] != "grouped" or table["replicatesCount"] != 6):
                raise InputError("Unexpected tissue table structure")
            sets = [decode_json(archive.read("data/sets/" + _uid(uid) + ".json")) for uid in table["dataSets"]]
            if len(sets) != (2 if object_index == 5 else 4) or any(s["format"] != "y_replicates" for s in sets):
                raise InputError("Unexpected native data-set structure")
            if object_index == 5:
                axis_member = "data/sets/" + _uid(table["xDataSet"]) + ".json"
                axis_raw = archive.read(axis_member)
                axis = decode_json(axis_raw)
                if (table["xDataSetFormat"] != "y_single" or axis["format"] != "y_single"
                        or _title(axis["title"]) != "Time (min)" or "DS_ATTR_X" not in axis["attributes"]):
                    raise InputError("Unexpected native trajectory time-axis metadata")
                axis_metadata = {"axis_metadata_member": axis_member, "axis_metadata_sha256": sha256(axis_raw),
                    "source_axis_title": _title(axis["title"]), "measurement_time_unit": "min"}
            else:
                label_member = "data/sets/" + _uid(table["rowTitlesDataSet"]) + ".json"
                label_raw = archive.read(label_member)
                if decode_json(label_raw)["format"] != "text":
                    raise InputError("Unexpected native tissue row-label metadata")
                axis_metadata = {"row_label_metadata_member": label_member, "row_label_metadata_sha256": sha256(label_raw),
                    "source_axis_title": None, "measurement_time_unit": "minutes"}
            csv_member = "data/tables/" + _uid(table["uid"]) + "/data.csv"
            raw_csv = archive.read(csv_member)
            rows = list(csv.reader(io.StringIO(raw_csv.decode("utf-8"))))
            expected_rows, expected_width = (11, 9) if object_index == 5 else (4, 25)
            if len(rows) != expected_rows or any(len(r) != expected_width for r in rows):
                raise InputError("Native CSV shape differs from the inspected source")
            for row in rows:
                for token in row[0 if object_index == 5 else 1:]:
                    if not 1 <= len(token) <= 128:
                        raise InputError("Missing or oversized native numeric token")
                    value = float(token)
                    if not math.isfinite(value):
                        raise InputError("Nonfinite native numeric token")
            result.append({"object_index": object_index, "sheet_member": name, "sheet_title": title,
                **axis_metadata, "source_set_ids": list(table["dataSets"]),
                "source_figure": "Supplementary Fig. S9" if object_index == 5 else "Supplementary Fig. S10",
                "source_object_paragraph_locator": "word/document.xml w:p[129]" if object_index == 5 else "word/document.xml w:p[132]",
                "source_caption_paragraph_locator": "word/document.xml w:p[130]" if object_index == 5 else "word/document.xml w:p[133]",
                "locator_convention": "1-based document-order w:p including nested paragraphs; figure caption follows object paragraph",
                "source_assay": "ex vivo human placental perfusion, compounds in mixture",
                "source_quantity": "percent of initial dose in maternal/foetal circulation" if object_index == 5 else "percent of initial dose in perfused placental tissue",
                "caption_reported_interval": "over 3 hours" if object_index == 5 else "after 180 minutes, per successful experiment",
                "caption_reported_biological_replicates": 4,
                "verified_biological_unit_mapping": False,
                "table_id": table["uid"], "csv_member": csv_member, "csv_sha256": sha256(raw_csv),
                "n_rows": len(rows), "n_columns": expected_width, "source_set_titles": [_title(s["title"]) for s in sets],
                "replicate_slots_per_set": table["replicatesCount"], "source_row_labels": [r[0] for r in rows] if object_index == 6 else [],
                "n_y_values": len(rows)*(expected_width-1), "csv_raw": raw_csv})
    return result


def audit_roelofsen_source(supplement_path: Path, output: Path):
    path = Path(supplement_path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise InputError("Supplement must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000 or sha256(raw) != SUPPLEMENT_SHA256:
        raise InputError("Supplement size/hash differs from the inspected revision; a new audit is required")
    tables, objects = [], []
    try:
        with _bounded_zip(raw, 512, 8_000_000, 2_000_000) as supplement:
            for index in (5,6):
                member = f"word/embeddings/oleObject{index}.bin"
                object_raw = supplement.read(member)
                native = _regular_contents(object_raw)
                objects.append({"member": member, "ole_sha256": sha256(object_raw), "native_zip_sha256": sha256(native)})
                tables.extend(_tables(native, index))
    except (zipfile.BadZipFile, KeyError, UnicodeError, ValueError, struct.error, RuntimeError, EOFError, TypeError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("Unsupported bounded native Prism source structure") from exc
    files = {}
    inventory = []
    for index, table in enumerate(tables, 1):
        filename = f"source-table-{index}.csv"
        files[filename] = table["csv_raw"]
        inventory.append({key:value for key,value in table.items() if key != "csv_raw"} | {"output_file": filename})
    cells, dataset, qualification = candidate_intake(tables, path.name, sha256(raw))
    manifest = {"schema_version": 1, "source_url": SUPPLEMENT_URL, "source_filename": path.name,
        "sha256": sha256(raw), "size_bytes": len(raw), "objects": objects,
        "external_source_required": True, "source_modified": False, "saved_analyses_executed": False}
    report = {"schema_version": 1, "review_status": "candidate", "human_review": "pending", "tables": inventory,
        "n_recovered_tables": len(tables), "n_published_y_values": sum(t["n_y_values"] for t in tables),
        "trajectory_quantity": "Author-processed percent-of-initial-dose trajectories; not original concentration observations.",
        "replicate_identity": "Native column slots retained; physical donor mapping/cross-compartment pairing not authenticated.",
        "tissue_linkage": "Source Placenta labels retained; no mapping to trajectory slots or technical subsamples inferred.",
        "analysis_eligibility": "Candidate cell-level observation intake; dynamic fit not qualified.",
        "limits": ["Percent normalization, sampling/hydrolysis corrections, actual capacities and original instrument observations remain unqualified.",
            "Repeated slot positions do not establish matching physical donors across compounds, compartments or the tissue table.",
            "The native source spelling, including Antipryine, is retained without semantic renaming.",
            "The inspected DOCX relationship/caption maps objects 5/6 to Fig. S9/S10; reported assay intervals and replicate counts are source declarations, not authenticated donor identities.",
            "Trajectory time unit min is explicit in referenced native Time (min) metadata; tissue elapsed time 180 minutes is caption-reported. These assay times are not developmental ages.",
            "Tissue normalization/subcolumn definitions remain unqualified; six slots do not establish six independent biological donors.",
            "The supplement defines successful perfusions using a transfer-based inclusion criterion; the starting/excluded attempt roster is absent from the selected tables and cannot be reconstructed from four included rows.",
            "No OLE program, embedded code, saved Prism analysis, kinetic fit or biological assay was executed.",
            "Term placental transport and choriocarcinoma-cell results remain separate from embryo development and complete gestation."]}
    lines = ["# Recovered native placental source tables", "", "AI-assisted candidate recovery; human review pending.",
        f"Recovered {len(tables)} native tables and {report['n_published_y_values']} published Y values from two embedded Prism objects.",
        "CSV source bytes are preserved exactly; slot identities are not promoted to biological unit identities.",
        "native_cells.csv and input_dataset.json retain cell locators, numeric text and reported assay times. qualification.json retains unresolved selection, unit linkage and fit requirements.",
        "", f"[Roelofsen et al., 2026]({ARTICLE_URL}); supplementary revision downloaded 2026-10-09.",
        "Article declares CC BY 4.0; source-specific reuse review remains pending. Selected embedded CSVs were recovered without modification; metadata inventories are new.",
        "", "## Qualification", "", report["analysis_eligibility"], "", *["- "+item for item in report["limits"]]]
    files.update({"input_source_manifest.json":json_bytes(manifest), "native_table_report.json":json_bytes(report),
        "native_cells.csv": csv_bytes(list(cells[0]), cells), "input_dataset.json": json_bytes(dataset),
        "qualification.json": json_bytes(qualification),
        "table_inventory.csv":csv_bytes(["output_file","object_index","sheet_title","csv_member","csv_sha256","n_rows","n_columns","replicate_slots_per_set","n_y_values"],
            [{key:t[key] for key in ("output_file","object_index","sheet_title","csv_member","csv_sha256","n_rows","n_columns","replicate_slots_per_set","n_y_values")} for t in inventory]),
        "REPORT.md":("\n".join(lines)+"\n").encode()})
    return publish_bundle(output,kind="native_placental_source_recovery",input_raw=raw,files=files,
        metadata={"source_review_status":"candidate","biological_assay_performed":False,"saved_analyses_executed":False,"model_fit":False})
