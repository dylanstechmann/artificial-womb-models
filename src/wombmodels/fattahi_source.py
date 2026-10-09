"""Pinned functional-readout audit; preserve endpoints without cross-assay pairing."""
from __future__ import annotations

import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256
from .hori_source import _figure_cells
from .observations import validate_dataset

WORKBOOK_SHA256 = "c3bbcc7d226ffcd24f015570ff89e7894bdeb62e9143c60219883a0ec98024c0"
ARTICLE_URL = "https://www.nature.com/articles/s41551-026-01801-9"
WORKBOOK_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs41551-026-01801-9/MediaObjects/41551_2026_1801_MOESM4_ESM.xlsx")
LICENSE_NOTE = "Article CC BY-NC-ND 4.0; workbook-specific terms need human review"
# Sheet, exact metric header, header cell, condition row, first value row, columns, role.
PANELS = (("Figure 2h", "TEER (Ω·cm²)", "A2", 4, 5, "BCDEF", "barrier_electrical_resistance", "Ω·cm²"),
          ("Figure 2h", "BSA permeability (%)", "A10", 12, 13, "BCDEF", "tracer_permeability", "%"),
          ("Figure 2h", "Lucifer Yellow permeability (%)", "A18", 20, 21, "BCDEF", "tracer_permeability", "%"),
          ("Figure 2i", "β-hCG (mIU/ml)", "A2", 4, 5, "BCDEF", "hormone_concentration", "mIU/ml"),
          ("Figure 2k", "Glucose transfer rate (%)", "A3", 5, 6, "BCD", "receiver_concentration_change", "%"))


def _numeric(cells, cell):
    token, kind, _ = cells.get(cell, (None, None, None))
    if kind != "numeric" or not isinstance(token, str) or not 1 <= len(token) <= 128:
        raise InputError("Missing or nonnumeric source endpoint/condition")
    try:
        value = float(token)
    except (ValueError, OverflowError) as exc:
        raise InputError("Invalid numeric source endpoint/condition") from exc
    if not math.isfinite(value) or value < 0:
        raise InputError("Source endpoint/condition must be finite and nonnegative")
    return token, value


def _extract_panels(sheets: dict) -> list[dict]:
    rows = []
    for panel, header, header_cell, condition_row, first_row, columns, role, unit in PANELS:
        cells = sheets[panel]
        if cells.get(header_cell, (None,))[0] != header:
            raise InputError("Functional metric header differs from the inspected source")
        expected = ("0", "0.1", "1") if panel == "Figure 2k" else ("0", "0.5", "1", "5", "10")
        dose_header = f"B{condition_row-1}"
        if cells.get(dose_header, (None,))[0] != "Cadmium concentration (µM)":
            raise InputError("Missing exact source condition-unit header")
        for column, expected_token in zip(columns, expected):
            token, condition_value = _numeric(cells, f"{column}{condition_row}")
            if condition_value != float(expected_token):
                raise InputError("Source condition labels differ from the inspected panel")
            for row in range(first_row, first_row + 4):
                label = cells.get(f"A{row}", (None,))[0]
                if label != f"Sample {row-first_row+1}":
                    raise InputError("Unexpected source sample-row label")
                locator = f"{column}{row}"
                value_token, value = _numeric(cells, locator)
                rows.append({"sheet": panel, "cell": locator, "source_metric_header": header,
                    "source_sample_label": label, "condition_cell": f"{column}{condition_row}",
                    "source_condition_numeric_text": token, "source_condition_unit": "µM",
                    "source_numeric_text": value_token, "value": value, "reported_unit": unit,
                    "functional_quantity": role, "paired_unit_identity": "not_established"})
    return rows


def _dataset(rows: list[dict], filename: str):
    artifact = {"artifact_id": "fattahi-figure2-source", "uri": WORKBOOK_URL,
        "license": LICENSE_NOTE, "sha256": WORKBOOK_SHA256, "retrieved_on": "2026-10-09", "local_path": filename}
    observations = []
    for row in rows:
        observations.append({"schema_version": 1,
            "record_id": "fattahi-" + row["sheet"].lower().replace(" ", "-") + "-" + row["cell"].lower(),
            "evidence_status": "author_reported_summary", "species": "human", "stage_track": "organoid_or_tissue_model",
            "developmental_interval": {"label": "Engineered human placental barrier; source model age not qualified",
                "time_unit": "model_day", "start": None, "end": None, "stage_source_artifact_id": artifact["artifact_id"]},
            "model_system": {"kind": "tissue_construct", "label": "Engineered human placental exposure model; "
                + row["source_condition_numeric_text"] + " µM source exposure condition"},
            "assay": {"name": "published functional readout: " + row["functional_quantity"],
                "endpoint": row["source_metric_header"], "unit": row["reported_unit"], "measurement_role": "function"},
            "independent_unit": {"kind": "not_reported", "id": None, "parent_id": None,
                "hierarchy_note": "Sample 1–4 are worksheet labels; cross-condition/panel physical identities, donor and experiment linkage are unverified."},
            "observation": {"value": row["value"], "measurement_time": None, "measurement_time_unit": "",
                "comparator_id": None, "replicate_role": "not_reported"},
            "source": {key: artifact[key] for key in ("artifact_id", "uri", "license", "sha256", "retrieved_on")},
            "limitations": [f"Original-value locator: {row['sheet']}!{row['cell']}; source sample label: {row['source_sample_label']}; condition locator: {row['condition_cell']}.",
                "Published endpoint values, not linked inlet/outlet/tissue-inventory trajectories. No individual pairing or donor n is inferred.",
                "Glucose percentage is a receiver concentration-change readout, not mass flux, donor recovery fraction, permeability coefficient or oxygen supply.",
                "Source exposure labels preserve the published comparison; they are not operating settings or a biological procedure.",
                "In-vitro tissue function is not embryo support, developmental continuity or a demonstrated healthy-human outcome."]})
    data = {"schema_version": 1, "dataset_id": "fattahi-2026-functional-endpoints-candidate",
        "title": "Candidate Figure 2 barrier, hormone and glucose-transfer readouts",
        "source_revision": {"revision_id": "fattahi-figure2-agent-audit-2026-10-09",
            "citation": "Fattahi et al. (2026), A bioengineered model of human placental exposure to environmental metals during pregnancy. Nature Biomedical Engineering.",
            "source_kind": "peer_reviewed_human_invitro", "source_url": ARTICLE_URL,
            "review_status": "candidate", "reviewer": "", "reviewed_on": None, "review_note": ""},
        "artifacts": [artifact], "observations": observations, "transitions": []}
    return validate_dataset(data)


def audit_fattahi_source(workbook_path: Path, output: Path):
    path = Path(workbook_path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise InputError("Workbook must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000 or sha256(raw) != WORKBOOK_SHA256:
        raise InputError("Workbook size/hash differs from the inspected Fattahi revision; a new audit is required")
    sheets = {name: _figure_cells(raw, name) for name in sorted({panel[0] for panel in PANELS})}
    rows = _extract_panels(sheets)
    dataset = _dataset(rows, path.name)
    manifest = {"schema_version": 1, "source_url": WORKBOOK_URL, "filename": path.name,
        "sha256": sha256(raw), "size_bytes": len(raw), "external_source_required": True,
        "selected_sheets": list(sheets), "source_copied_or_modified": False, "license_note": LICENSE_NOTE}
    qualification = {"schema_version": 1, "review_status": "candidate", "human_review": "pending",
        "n_published_values": len(rows), "n_functional_readouts": len(PANELS),
        "n_verified_unit_ids": 0, "cross_assay_pairing": "not_established",
        "scientific_transcription": "agent_extraction_not_human_verified",
        "dynamic_model_eligibility": "not_eligible_from_inspected_inputs",
        "glucose_quantity": "reported_percent_receiver_concentration_change; not a physical mass-transfer rate",
        "missing": ["Original inlet/outlet and tissue-inventory observations with collection corrections and calibration.",
            "Explicit cross-assay/condition specimen mapping, donor/source and experiment hierarchy.",
            "Starting cohort, exclusions, assay timing, uncertainty and source-specific reuse review."],
        "model_fit": "not_performed", "gestation_claim": "not_assessed"}
    lines = ["# Fattahi functional-readout source audit", "", "AI-assisted candidate transcription; human review pending.",
        f"{len(rows)} published values in five readouts; no verified unit IDs, pairing, model fit or continuity edges.",
        "", "TEER, two tracer permeabilities, hormone concentration and glucose receiver concentration change remain separate quantities.",
        "Glucose's source percentage is not mass flux or a fraction of maternal input recovered.",
        "Repeated worksheet Sample labels do not establish paired physical specimens.",
        "", f"[Fattahi et al., 2026]({ARTICLE_URL}); publisher Figure 2 Source Data.",
        "Article: CC BY-NC-ND 4.0. Workbook-specific reuse terms remain unqualified. Original source files are external and untouched; this local audit extracts/reformats selected scalar cells.",
        "", "## Missing for a dynamic benchmark", "", *["- " + m for m in qualification["missing"]],
        "", "No operating recommendation, biological assay, inferred gestational age or healthy-human outcome is produced."]
    return publish_bundle(output, kind="functional_readout_source_audit", input_raw=raw,
        files={"input_source_manifest.json": json_bytes(manifest), "input_dataset.json": json_bytes(dataset),
            "endpoint_cells.csv": csv_bytes(list(rows[0]), rows), "qualification.json": json_bytes(qualification),
            "REPORT.md": ("\n".join(lines) + "\n").encode()},
        metadata={"source_review_status": "candidate", "n_published_values": len(rows),
            "model_calibration_performed": False, "biological_assay_performed": False})
