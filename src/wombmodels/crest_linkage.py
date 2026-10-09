"""Pinned CREST sample-pool metadata audit; never execute author code or read variants."""
from __future__ import annotations

import csv
import io
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256
from .observations import validate_dataset

SDRF_SHA256 = "4394e7b377e10c7bd47fab7cb387ccccdd87f26b3f66e2db9453793663584391"
ARCHIVE_SHA256 = "f7af5da0b98f050c98f037698b02297e79571592f4a936ff9368f3a47c0e96b9"
SDRF_URL = "https://www.ebi.ac.uk/biostudies/files/E-MTAB-13629/E-MTAB-13629.sdrf.txt"
CODE_URL = "https://zenodo.org/records/17955321"
PREFIX = "Rugg-Gunn-Lab-CREST-3865ca4/"
METADATA_MEMBER = PREFIX + "Files/MatteoMeta_and_QC.csv"
CODE_MEMBER = PREFIX + "Rscripts/InitialProcessing/Step1_Final.R"
SDRF_FIELDS = ("Source Name", "Characteristics[organism]", "Characteristics[age]",
               "Characteristics[organism part]", "Characteristics[individual]",
               "Characteristics[cell type]", "Characteristics[developmental stage]",
               "Characteristics[cell line]", "Characteristics[sample group]", "Assay Name")


def _pools(raw: bytes) -> list[dict]:
    if len(raw) > 128_000:
        raise InputError("SDRF exceeds the 128 kB audit bound")
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8")), delimiter="\t")
        headers = next(reader)
        if len(headers) > 150 or any(headers.count(field) != 1 for field in SDRF_FIELDS):
            raise InputError("Missing or duplicate selected SDRF metadata header")
        indices = {field: headers.index(field) for field in SDRF_FIELDS}
        groups = defaultdict(list)
        for line, row in enumerate(reader, 2):
            if line > 201 or len(row) != len(headers):
                raise InputError("SDRF row count/width exceeds the supported contract")
            selected = {key: row[index] for key, index in indices.items()}
            if any(not value.strip() or len(value) > 250 for value in selected.values()):
                raise InputError("SDRF selected metadata must be bounded nonempty text")
            selected["source_line"] = line
            groups[selected["Source Name"]].append(selected)
        if not groups or len(groups) > 50:
            raise InputError("Expected 1–50 source-named SDRF preparations")
        pools = []
        for name, rows in sorted(groups.items()):
            for field in SDRF_FIELDS[:-1]:
                if len({row[field] for row in rows}) != 1:
                    raise InputError("A Source Name has conflicting specimen/stage metadata")
            first = rows[0]
            if first["Characteristics[organism]"] != "Homo sapiens" or first["Characteristics[age]"] != "Embryo day 14":
                raise InputError("Unexpected species/age in the inspected CREST metadata")
            members = first["Characteristics[individual]"].split("+")
            if (not 1 <= len(members) <= 100 or len(set(members)) != len(members)
                    or any(not re.fullmatch(r"Em\d{1,4}", member) for member in members)):
                raise InputError("Unsupported or duplicate declared embryo member labels")
            pools.append({"sample_name": name, "reported_individuals": first["Characteristics[individual]"],
                          "members": sorted(members), "n_sdrf_rows": len(rows),
                          "n_assay_labels": len({row["Assay Name"] for row in rows}),
                          "source_lines": [row["source_line"] for row in rows],
                          "age_label": first["Characteristics[age]"],
                          "model_label": first["Characteristics[organism part]"],
                          "cell_type_label": first["Characteristics[cell type]"],
                          "stage_label": first["Characteristics[developmental stage]"],
                          "stromal_label": first["Characteristics[cell line]"],
                          "sample_group": first["Characteristics[sample group]"]})
        return pools
    except (UnicodeError, StopIteration, csv.Error) as exc:
        raise InputError("SDRF is not supported bounded UTF-8 tabular metadata") from exc


def _archive_summary(raw: bytes) -> tuple[list[dict], dict]:
    """Inspect only annotation CSV and literal processing-label assignments."""
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            inventory = archive.infolist()
            if (len(inventory) > 128 or len({i.filename for i in inventory}) != len(inventory)
                    or sum(i.file_size for i in inventory) > 10_000_000
                    or any(i.file_size > 3_000_000 or i.flag_bits & 1 for i in inventory)):
                raise InputError("CREST archive exceeds bounds or has duplicate/encrypted members")
            metadata = archive.read(METADATA_MEMBER)
            code = archive.read(CODE_MEMBER)
        reader = csv.reader(io.StringIO(metadata.decode("utf-8")))
        headers = next(reader)
        if len(headers) > 64 or any(headers.count(field) != 1 for field in ("Batch", "Inferred ID")):
            raise InputError("Unexpected CREST annotation headers")
        bi, ci = headers.index("Batch"), headers.index("Inferred ID")
        counts = Counter()
        n_rows = 0
        for row in reader:
            n_rows += 1
            if n_rows > 20_000 or len(row) != len(headers):
                raise InputError("CREST annotation row bound/width exceeded")
            if any(not row[index].strip() or len(row[index]) > 120 for index in (bi, ci)):
                raise InputError("Annotation batch/class must be bounded nonempty text")
            counts[row[bi], row[ci]] += 1
        if not n_rows:
            raise InputError("CREST annotation metadata is empty")
        mappings = re.findall(r'^\s*(D\d+B?)\$ID3\s*<-\s*"(C\d+)"\s*$', code.decode("utf-8"), re.MULTILINE)
        if (not 1 <= len(mappings) <= 20 or len({a for a, _ in mappings}) != len(mappings)
                or len({b for _, b in mappings}) != len(mappings)):
            raise InputError("Processing-label assignments are absent or ambiguous")
        observed = {batch for batch, _ in counts}
        declared = {batch for _, batch in mappings}
        if observed - declared:
            raise InputError("Annotation batch has no selected source-code label assignment")
        batches = [{"processing_object": obj, "declared_processing_label": batch,
                    "n_annotation_cell_rows": sum(count for (b, _), count in counts.items() if b == batch),
                    "n_annotation_classes": sum(b == batch for b, _ in counts),
                    "status": "present_in_annotation_csv" if batch in observed else "no_rows_in_supplied_annotation_csv",
                    "interpretation": "Literal author-code label and CSV category comparison; no specimen/phenotype linkage inferred."}
                   for obj, batch in mappings]
        return batches, {"n_cell_rows": n_rows, "n_batch_categories": len(observed),
                         "n_class_labels": len({cell_class for _, cell_class in counts}),
                         "metadata_member": METADATA_MEMBER, "metadata_sha256": sha256(metadata),
                         "processing_code_member": CODE_MEMBER, "processing_code_sha256": sha256(code),
                         "author_code_executed": False, "genomic_variant_contents_read": False}
    except (zipfile.BadZipFile, KeyError, UnicodeError, StopIteration, csv.Error, RuntimeError, EOFError) as exc:
        raise InputError("Unsupported bounded CREST code archive") from exc


def _dataset(pools: list[dict], source_name: str) -> dict:
    artifact = {"artifact_id": "crest-sdrf", "uri": SDRF_URL,
                "license": "Public ArrayExpress metadata; source-specific reuse review pending",
                "sha256": SDRF_SHA256, "retrieved_on": "2026-10-09", "local_path": source_name,
                "developmental_scope": {"species": "human", "stage_tracks": ["implantation_and_placentation"],
                    "time_unit": "reported_embryo_day", "start": 14, "end": 14,
                    "source_locator": "SDRF Characteristics[age]: Embryo day 14; metadata age, not a continuous support interval."}}
    records = []
    for index, pool in enumerate(pools, 1):
        records.append({"schema_version": 1, "record_id": f"crest-sdrf-pool-{index:02d}",
            "evidence_status": "author_reported_summary", "species": "human",
            "stage_track": "implantation_and_placentation",
            "developmental_interval": {"label": pool["age_label"], "time_unit": "reported_embryo_day",
                "start": 14, "end": 14, "stage_source_artifact_id": "crest-sdrf"},
            "model_system": {"kind": "tissue_construct", "label": pool["model_label"]},
            "assay": {"name": "SDRF sequencing sample metadata", "endpoint": "declared pooled individual labels",
                "unit": "source identifier text", "measurement_role": "other"},
            "independent_unit": {"kind": "sample_pool", "id": pool["sample_name"], "parent_id": None,
                "members": [{"kind": "embryo", "id": member} for member in pool["members"]],
                "hierarchy_note": "Source-named preparation and declared embryo labels only; completeness, biological independence and endometrial donor identity are not verified."},
            "observation": {"value": pool["reported_individuals"], "measurement_time": None,
                "measurement_time_unit": "", "comparator_id": None, "replicate_role": "summary_only"},
            "source": {key: artifact[key] for key in ("artifact_id", "uri", "license", "sha256", "retrieved_on")},
            "limitations": [f"Source rows: {','.join(str(line) for line in pool['source_lines'])}; member names come only from Characteristics[individual].",
                "Metadata text only; no gene-expression value, image phenotype, developmental outcome or biological assay was produced.",
                "Sequencing/preparation labels and declared members cannot be used as independent n or as Figure 7 specimen links.",
                "Maternal contributors are not fully enumerated by these embryo member labels; no complete pool membership is asserted."]})
    data = {"schema_version": 1, "dataset_id": "crest-day14-pool-metadata-candidate",
        "title": "Candidate CREST day-14 source pool metadata; no phenotype measurements",
        "source_revision": {"revision_id": "crest-linkage-agent-audit-2026-10-09",
            "citation": "E-MTAB-13629 source metadata associated with Mole et al., Modeling human embryo implantation in vitro (Cell, 2026).",
            "source_kind": "dataset_record", "source_url": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-13629",
            "review_status": "candidate", "reviewer": "", "reviewed_on": None, "review_note": ""},
        "artifacts": [artifact], "observations": records, "transitions": []}
    validate_dataset(data)
    return data


def _source(path: Path, expected: str, maximum: int) -> bytes:
    path = Path(path)
    if any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise InputError("Source must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum or sha256(raw) != expected:
        raise InputError("Source size/hash differs from the inspected CREST revision; a new audit is required")
    return raw


def audit_crest_linkage(sdrf_path: Path, archive_path: Path, output: Path) -> dict:
    sdrf = _source(sdrf_path, SDRF_SHA256, 128_000)
    archive = _source(archive_path, ARCHIVE_SHA256, 1_000_000)
    pools = _pools(sdrf)
    batches, annotations = _archive_summary(archive)
    dataset = _dataset(pools, Path(sdrf_path).name)
    declared = defaultdict(list)
    for pool in pools:
        for member in pool["members"]:
            declared[member].append(pool["sample_name"])
    shared = [{"declared_member_id": member, "sample_names": ";".join(names), "n_preparation_labels": len(names)}
              for member, names in sorted(declared.items()) if len(names) > 1]
    manifest = {"schema_version": 1, "external_sources_required": True,
        "sources": [{"role": "sdrf", "source_url": SDRF_URL, "filename": Path(sdrf_path).name,
                     "sha256": sha256(sdrf), "size_bytes": len(sdrf)},
                    {"role": "code_archive", "source_url": CODE_URL, "filename": Path(archive_path).name,
                     "sha256": sha256(archive), "size_bytes": len(archive)}],
        "sources_copied_or_modified": False, "retrieved_on": "2026-10-09"}
    report = {"schema_version": 1, "review_status": "candidate", "human_review": "pending",
        "n_sdrf_rows": sum(pool["n_sdrf_rows"] for pool in pools), "n_source_named_preparations": len(pools),
        "n_distinct_declared_embryo_labels": len(declared), "n_shared_declared_member_labels": len(shared),
        "n_distinct_declared_member_sets": len({tuple(pool["members"]) for pool in pools}),
        "annotation_inventory": annotations,
        "phenotype_linkage": "not_established_in_inspected_inputs",
        "biological_independence": "not_verified; source labels and cell rows are not independent n",
        "analysis_eligibility": "descriptive source hierarchy only; Figure 7 functional reanalysis deferred",
        "missing_for_functional_reanalysis": ["Figure 7 original area/length values with individual specimen IDs and experiment/source hierarchy.",
            "Source-established linkage to transcriptomic specimens if paired identity/function claims are intended.",
            "Starting cohort, assignment/exclusions, image-analysis contract and calibrated uncertainty.",
            "Source-specific human review and reuse confirmation."],
        "limits": ["SDRF row multiplicity and assay names reflect submitted metadata; they are not biological replicate counts.",
                   "Declared embryo labels enumerate only named contributors; maternal contributors and membership completeness are unresolved.",
                   "An absent processing label in the supplied final annotation CSV is not embryo loss, attrition or absent cell biology.",
                   "The selected R script is read as text only. Genomic variant contents and expression objects are not read or analyzed.",
                   "No phenotype points are digitized, no treatment effect is recomputed and no individual developmental transition is asserted."]}
    pool_rows = [{**{key: value for key, value in pool.items() if key not in {"members", "source_lines"}},
                  "member_ids": ";".join(pool["members"]), "source_lines": ";".join(map(str, pool["source_lines"]))}
                 for pool in pools]
    lines = ["# CREST early-interface linkage audit", "", "Agent-assisted candidate inspection; human review pending.", "",
        f"SDRF rows: {report['n_sdrf_rows']}; source preparation labels: {len(pools)}; declared embryo label strings: {len(declared)}; shared labels: {len(shared)}.",
        "These are metadata counts, not verified biological n. Source day-14 annotation is not a continuous support interval.", "",
        "## Source pool hierarchy", "", "| Preparation | Declared embryo labels | SDRF rows | Assay labels |",
        "| --- | --- | ---: | ---: |"]
    lines += [f"| {pool['sample_name']} | {pool['reported_individuals']} | {pool['n_sdrf_rows']} | {pool['n_assay_labels']} |" for pool in pools]
    lines += ["", "## Annotation inventory", "",
        f"Supplied annotation CSV: {annotations['n_cell_rows']} cell rows, {annotations['n_class_labels']} class labels and {annotations['n_batch_categories']} batch categories.",
        "Literal processing-code assignments and final CSV label presence are compared in processing_labels.csv. No physical-specimen or phenotype mapping is inferred.", "",
        "## Functional reanalysis gate", "", report["analysis_eligibility"], ""]
    lines += ["- " + item for item in report["missing_for_functional_reanalysis"]]
    lines += ["", "## Limits", "", *["- " + item for item in report["limits"]], "",
        f"[ArrayExpress source metadata]({SDRF_URL}); [publication code archive]({CODE_URL}).",
        "The code repository declares CC BY 4.0; [licence](https://creativecommons.org/licenses/by/4.0/). Source-specific reuse review remains pending. Tables here are extracted/reformatted metadata, not author-code execution.",
        "The original files remain external and untouched. input_dataset.json can be validated with the SDRF directory as --source-root."]
    raw_manifest = json_bytes(manifest)
    return publish_bundle(output, kind="early_interface_source_linkage_audit", input_raw=raw_manifest,
        files={"input_source_manifest.json": raw_manifest, "input_dataset.json": json_bytes(dataset),
               "sample_pools.csv": csv_bytes(list(pool_rows[0]), pool_rows),
               "shared_members.csv": csv_bytes(["declared_member_id", "sample_names", "n_preparation_labels"], shared),
               "processing_labels.csv": csv_bytes(list(batches[0]), batches),
               "linkage_report.json": json_bytes(report), "REPORT.md": ("\n".join(lines) + "\n").encode()},
        metadata={"source_review_status": "candidate", "phenotype_linkage": report["phenotype_linkage"],
                  "biological_assay_performed": False, "source_files_verified_by_pinned_hash": True})
