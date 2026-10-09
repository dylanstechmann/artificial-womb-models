"""Pinned niche-source audit; no mechanical fit, causal estimate or embryo assay."""
from __future__ import annotations

import math
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, sha256
from .hori_source import _figure_cells
from .observations import validate_dataset

WORKBOOK_SHA256 = "c84b1faf2ebe02c812af7ec73d94a10c6640a11fba677ac85947999b9dc33e8e"
ARTICLE_URL = "https://www.nature.com/articles/s41467-025-68039-y"
WORKBOOK_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs41467-025-68039-y/MediaObjects/41467_2025_68039_MOESM18_ESM.xlsx")
LICENSE_NOTE = "Article CC BY-NC-ND 4.0; workbook-specific reuse review pending"
PANELS = (
    ("Fig4A", "reported relaxation half-time", ("40-MG", "5.5De"), (9,10), None),
    ("Fig4C", "reported Young modulus", ("40-MG", "40-MGT", "40-MGN"), (10,10,10), None),
    ("Fig4D", "reported relaxation half-time", ("40-MG", "40-MGT", "40-MGN"), (5,5,5), None),
    ("Fig4E", "two-cavity developmental percentage", ("40-MG", "40-MGT", "40-MGN"), (7,4,5), 3),
    ("Fig4F", "egg-cylinder developmental percentage", ("40-MG", "40-MGT", "40-MGN"), (7,4,5), 4),
)


def _numeric(cells, locator, *, percentage=False):
    token, kind, _ = cells.get(locator, (None,None,None))
    if kind != "numeric" or token is None or not 1 <= len(token) <= 128:
        raise InputError(f"Missing or unsupported source numeric cell {locator}")
    try:
        value = float(token)
    except (ValueError, OverflowError) as exc:
        raise InputError(f"Invalid source numeric cell {locator}") from exc
    if not math.isfinite(value) or value < 0 or (percentage and value > 100):
        raise InputError(f"Nonfinite or out-of-domain source cell {locator}")
    return token, value


def _extract(sheets):
    endpoints, curves = [], []
    for sheet, quantity, headers, counts, day in PANELS:
        cells = sheets[sheet]
        expected = set()
        for col, (header,count) in enumerate(zip(headers,counts)):
            column = chr(65+col)
            if cells.get(column+"1", (None,))[0] != header:
                raise InputError(f"Changed source condition header in {sheet}")
            for row in range(2,2+count):
                locator = column+str(row)
                expected.add(locator)
                token, value = _numeric(cells, locator, percentage=day is not None)
                endpoints.append({"record_id":f"guo-{sheet.lower()}-{locator.lower()}", "sheet":sheet,
                    "cell":locator, "source_condition":header, "quantity":quantity,
                    "numeric_text":token, "value":value, "reported_unit":"%" if day is not None else None,
                    "unit_status":"caption_reported" if day is not None else "unqualified",
                    "measurement_time":day, "measurement_time_unit":"IVC day" if day is not None else None,
                    "physical_unit_id":None, "replicate_role":"not_reported"})
        actual = {cell for cell,(token,kind,_) in cells.items() if kind == "numeric" and token is not None}
        if actual != expected:
            raise InputError(f"Source numeric inventory differs in {sheet}")
    cells = sheets["Sup 10 I"]
    for column, title in (("B","40-MG"),("D","40-MGN"),("F","40-MGT")):
        if cells.get(column+"1",(None,))[0] != title:
            raise InputError("Changed relaxation-profile source header")
    expected = set()
    for row in range(2,202):
        for column in ("A","B","D","F"):
            cell = column+str(row)
            expected.add(cell)
            token,value = _numeric(cells,cell)
            curves.append({"sheet":"Sup 10 I", "cell":cell, "column_role":"source_X_coordinate" if column == "A" else "source_response_profile",
                "source_condition":None if column == "A" else cells[column+"1"][0], "numeric_text":token,
                "value":value, "unit_status":"unqualified", "physical_unit_id":None})
    actual = {cell for cell,(token,kind,_) in cells.items() if kind == "numeric" and token is not None}
    if actual != expected:
        raise InputError("Relaxation-profile numeric inventory differs")
    return endpoints,curves


def _dataset(endpoints,filename):
    artifact = {"artifact_id":"guo-niche-workbook", "uri":WORKBOOK_URL, "license":LICENSE_NOTE,
        "sha256":WORKBOOK_SHA256, "retrieved_on":"2026-10-09", "local_path":filename}
    records = []
    for cell in endpoints:
        if cell["unit_status"] != "caption_reported":
            continue
        records.append({"schema_version":1,"record_id":cell["record_id"],"evidence_status":"author_reported_summary",
            "species":"mouse", "stage_track":"postimplantation_embryonic",
            "developmental_interval":{"label":"E3.5 mouse embryo entry; elapsed culture outcome, in-vivo ending age unqualified",
                "time_unit":"embryonic_day", "start":3.5, "end":None, "stage_source_artifact_id":artifact["artifact_id"]},
            "model_system":{"kind":"intact_organism", "label":"Ex vivo mouse embryos in source niche condition " + cell["source_condition"]},
            "assay":{"name":"Source " + cell["sheet"] + " developmental outcome", "endpoint":cell["quantity"], "unit":"%", "measurement_role":"morphology"},
            "independent_unit":{"kind":"not_reported", "id":None, "parent_id":None,
                "hierarchy_note":"Worksheet rows lack explicit embryo/run/material identities; cross-panel pairing and starting-cohort denominators are unqualified."},
            "observation":{"value":cell["value"], "measurement_time":cell["measurement_time"],
                "measurement_time_unit":"IVC day", "comparator_id":None, "replicate_role":"not_reported"},
            "source":{k:artifact[k] for k in ("artifact_id","uri","license","sha256","retrieved_on")},
            "limitations":[f"Original source locator: {cell['sheet']}!{cell['cell']}; condition header {cell['cell'][0]}1; numeric lexeme {cell['numeric_text']}.",
                "Published developmental percentage; original embryo numerator/denominator and experiment mapping are absent from the selected sheet.",
                "Matching row positions and condition titles do not establish pairing with mechanical measurements or later outcomes.",
                "Source condition codes identify the published comparison; they are not a preparation recipe or operating recommendation.",
                "Culture days are not silently added to embryonic age; mouse progression does not establish continuous human development."]})
    return validate_dataset({"schema_version":1,"dataset_id":"guo-niche-development-candidate",
        "title":"Candidate Figure 4E/F mouse developmental percentages",
        "source_revision":{"revision_id":"guo-niche-agent-audit-2026-10-09", "citation":"Guo et al. (2026), 3D biomimetic niche modulates embryo development in vitro. Nature Communications 17, 1279.",
            "source_kind":"peer_reviewed_animal", "source_url":ARTICLE_URL, "review_status":"candidate", "reviewer":"", "reviewed_on":None, "review_note":""},
        "artifacts":[artifact], "observations":records, "transitions":[]})


def audit_guo_source(workbook_path: Path, output: Path):
    path = Path(workbook_path)
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():
        raise InputError("Workbook must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000 or sha256(raw) != WORKBOOK_SHA256:
        raise InputError("Workbook size/hash differs from the inspected Guo revision; a new audit is required")
    sheets = {name:_figure_cells(raw,name) for name in [p[0] for p in PANELS]+["Sup 10 I"]}
    endpoints,curves = _extract(sheets)
    dataset = _dataset(endpoints,path.name)
    qualification = {"schema_version":1, "review_status":"candidate", "human_review":"pending",
        "n_endpoint_cells":len(endpoints), "n_developmental_percentage_cells":len(dataset["observations"]),
        "n_profile_cells":len(curves), "n_verified_physical_unit_ids":0,
        "starting_cohort_denominators":None, "cross_panel_pairing":"not_established",
        "mechanical_units_loading_normalization":"unqualified; excluded from observation intake",
        "stiffness_equivalence":"not_established_by_nonsignificant_difference",
        "missing":["Physical embryo/run/material IDs and experiment/subsample hierarchy across panels.",
            "Original developmental numerators, starting denominators, attrition and exclusions.",
            "Mechanical units, loading/holding history, normalization and profile replicate mapping.",
            "Reviewed equivalence margin, confound controls, source-specific rights and frozen analysis plan."],
        "mechanical_fit_performed":False,"causal_effect_estimated":False,"biological_assay_performed":False}
    manifest = {"schema_version":1,"source_url":WORKBOOK_URL,"filename":path.name,"sha256":sha256(raw),"size_bytes":len(raw),
        "selected_sheets":list(sheets),"source_modified":False,"external_source_required":True}
    report = "\n".join(["# Niche mechanics and developmental-source audit", "", "AI-assisted candidate transcription; human review pending.",
        f"{len(endpoints)} endpoint cells; {len(dataset['observations'])} developmental-percentage records; {len(curves)} profile cells.",
        "Original scalar lexemes/locators are retained. Row counts are not verified biological n. Mechanical units remain unqualified and those values are excluded from observation intake.",
        "Cross-panel correlation, mechanical calibration, stiffness equivalence and causal estimates are not performed.",
        "",f"[Guo et al., 2026]({ARTICLE_URL}). Article CC BY-NC-ND 4.0; workbook-specific reuse review pending. External source is untouched; local scalar inventories are reformatted candidate transcriptions.",
        "", "## Required qualification", "", *["- "+v for v in qualification["missing"]], ""])
    return publish_bundle(output,kind="niche_mechanics_development_source_audit",input_raw=raw,
        files={"input_source_manifest.json":json_bytes(manifest),"input_dataset.json":json_bytes(dataset),
            "endpoint_cells.csv":csv_bytes(list(endpoints[0]),endpoints),"profile_cells.csv":csv_bytes(list(curves[0]),curves),
            "qualification.json":json_bytes(qualification),"REPORT.md":report.encode()},
        metadata={"source_review_status":"candidate","biological_assay_performed":False,"mechanical_fit_performed":False,"causal_effect_estimated":False})
