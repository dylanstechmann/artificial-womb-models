"""Offline extraction of pinned Usuda terminal summaries, without a model fit."""
from __future__ import annotations

import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, reproduction_plan, sha256
from .observations import validate_dataset

SOURCE_PATH = "artifacts/usuda-2023-case-linkage-2026-10-10/PMC10484719.fullTextXML.xml"
SOURCE_SHA256 = "553bb25875e95db787249c60bab779dc05aebb32f341dce27b3f1c7405430e0a"
ARTICLE_URL = "https://doi.org/10.3389/fphys.2023.1219185"
SOURCE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10484719/fullTextXML"
TERMINAL_ROWS = (
    "Gestational age at necropsy (d)", "Body weight (necropsy) (g)",
    "Brain weight (g)", "Heart weight (g)", "Lung weight (g)",
    "Liver weight (g)", "Kidney weight (g)",
    "Humerus length gain (cm)", "Femur length gain (cm)",
)
LIMITS = [
    "These are published group summaries, not individual animals, trajectories or raw assays; no case A-F or cross-endpoint pairing is established.",
    "The table/main-text control count is eight, while the abstract says six. The source does not reconcile the count or publish an individual control-pairing map.",
    "Necropsy age varies within and between groups; group age means are not individual ages or developmental interval bounds.",
    "Edema affects body-weight interpretation; no dry-weight or fluid correction is available. Organ mass and bone length do not establish organ function or later health.",
    "Reported long-bone units and p-value/confidence-interval strings are preserved literally, including source ambiguities. No unit correction or statistical reanalysis is made.",
    "Biomarker differences do not establish a cause of impaired development or a treatment. No physiological setpoint, machine operating parameter or human requirement is inferred.",
    "Source transcription is agent-assisted and remains a candidate for human review. No author contact or biological experiment occurred.",
]


def _text(node):
    return "".join(node.itertext()).strip()


def _summary(literal):
    """Parse only the summary syntax actually printed in the pinned tables."""
    clean = literal.rstrip(" *").replace(",", "")
    if clean in {"-", "\u2014"}:
        return None, None
    number = r"[0-9]+(?:\.[0-9]+)?"
    mean_sd = re.fullmatch(rf"({number}) \u00b1 ({number})", clean)
    median_iqr = re.fullmatch(rf"({number}) \[({number})\u2013({number})\]", clean)
    matched = mean_sd or median_iqr
    if matched is None:
        raise InputError("Unsupported published summary syntax")
    values = [float(token) for token in matched.groups()]
    if not all(math.isfinite(value) for value in values):
        raise InputError("Source summary contains a nonfinite value")
    if mean_sd:
        value, sd = values
        return value, {"kind": "mean_sd", "mean": value, "standard_deviation": sd}
    value, lower, upper = values
    if not lower <= value <= upper:
        raise InputError("Source median is outside its quartiles")
    return value, {"kind": "median_iqr", "lower_quartile": lower, "upper_quartile": upper}


def extract_terminal(raw):
    """Return selected exact table cells and an unreviewed observation dataset."""
    if len(raw) > 2_000_000 or sha256(raw) != SOURCE_SHA256:
        raise InputError("Usuda source size/hash differs from the inspected revision")
    root = ET.fromstring(raw)
    tables = {node.get("id"): node for node in root.findall(".//table-wrap")}
    t1, t3 = tables["T1"], tables["T3"]
    header = [[_text(cell) for cell in row] for row in t1.findall("./table/thead/tr")]
    if header[0][1:3] != ["Control group", "APT group"] or header[1][:3] != ["Number", "8", "6"]:
        raise InputError("Usuda table group/count headers differ")
    if "mean \u00b1 SD" not in _text(t1.find("caption")) or "median [IQR]" not in _text(t3.find("caption")):
        raise InputError("Usuda summary definitions differ")
    source = {"artifact_id": "usuda2023-terminal-jats", "uri": SOURCE_URL,
              "license": "CC BY 4.0 article; source-specific review pending",
              "sha256": SOURCE_SHA256, "retrieved_on": "2026-10-10"}
    cells, observations = [], []
    selected_t1 = []
    for table_id, table in (("T1", t1), ("T3", t3)):
        rows = [[_text(cell) for cell in row] for row in table.findall("./table/tbody/tr")]
        for row_index, row in enumerate(rows, 1):
            if len(row) != 5:
                raise InputError("Usuda source row does not have five cells")
            label, control, apt, test, p_ci = row
            if table_id == "T1" and label not in TERMINAL_ROWS:
                continue
            if table_id == "T1":
                selected_t1.append(label)
            match = re.fullmatch(r"(.+) \(([^()]*)\)", label)
            endpoint, unit = match.groups() if match else (label, "source ratio; no unit printed")
            for group, literal, n in (("control", control, 8), ("apt", apt, 6)):
                value, summary = _summary(literal)
                record_id = f"usuda2023-{table_id.lower()}-row{row_index:02d}-{group}"
                locator = f"Table {table_id[1:]}, row {row_index}: {label}; {group.upper() if group == 'apt' else 'Control'} group"
                cells.append({"record_id": record_id, "table_id": table_id,
                    "tbody_row": row_index, "source_endpoint_literal": label,
                    "group": group, "source_summary_literal": literal,
                    "source_statistical_test_literal": test,
                    "source_p_ci_literal": p_ci, "reported_unit": unit,
                    "source_group_n": n, "source_locator": locator})
                if summary is not None:
                    summary.update({"reported_sample_size": n,
                        "sample_size_scope": "Table-declared group animal count; individual endpoint coverage and independence are not independently verified.",
                        "sample_size_source_locator": "Table 1 Number header; Table 3 caption (eight controls, six APT animals). Abstract control count differs.",
                        "source_literal": literal})
                observation = {"value": value, "measurement_time": None,
                    "measurement_time_unit": "group-specific end of experiment",
                    "comparator_id": "usuda2023-control-summary" if group == "apt" else None,
                    "replicate_role": "summary_only",
                    "measurement_conditions": [{"name": "source_group", "value": group,
                        "unit": "", "source_locator": locator}]}
                if summary is not None:
                    observation["summary_statistic"] = summary
                else:
                    observation["missingness_reason"] = "Source table prints a dash for this group; no value or zero is inferred."
                is_morphology = table_id == "T1" and "Gestational age" not in label
                observations.append({"schema_version": 1, "record_id": record_id,
                    "evidence_status": "author_reported_summary", "species": "ovine",
                    "stage_track": "partial_fetal_support",
                    "developmental_interval": {"label": "Group terminal endpoint; individual necropsy ages and case links not available",
                        "start": None, "end": None, "time_unit": "gestational days at necropsy",
                        "stage_source_artifact_id": source["artifact_id"]},
                    "model_system": {"kind": "intact_organism",
                        "label": "Usuda 2023 ovine APT group" if group == "apt" else "Usuda 2023 in-utero ovine control group"},
                    "assay": {"name": "Published terminal morphology summary" if table_id == "T1" else "Published terminal hematological/biochemical summary",
                        "endpoint": endpoint, "unit": unit,
                        "measurement_role": "morphology" if is_morphology else "other",
                        "functional_evidence_class": "developmental_outcome" if is_morphology else "biological_response_proxy" if table_id == "T3" else "other"},
                    "independent_unit": {"kind": "not_reported", "id": None, "parent_id": None,
                        "hierarchy_note": "Published group summary; source animal, dam, specimen and control-pairing identifiers are unavailable."},
                    "observation": observation, "source": dict(source), "source_locator": locator,
                    "limitations": list(LIMITS)})
    if tuple(selected_t1) != TERMINAL_ROWS or len(cells) != 60:
        raise InputError("Selected Usuda terminal source inventory differs")
    artifact = {**source, "local_path": SOURCE_PATH}
    dataset = {"schema_version": 1, "dataset_id": "usuda2023-terminal-group-candidate",
        "title": "Usuda 2023 terminal morphology and complete Table 3 summaries; unlinked groups",
        "source_revision": {"revision_id": "usuda2023-terminal-jats-cycle346",
            "citation": "Usuda et al. (2023), Frontiers in Physiology 14:1219185. DOI 10.3389/fphys.2023.1219185.",
            "source_kind": "peer_reviewed_animal", "source_url": ARTICLE_URL,
            "review_status": "candidate", "reviewer": "", "reviewed_on": None, "review_note": ""},
        "artifacts": [artifact], "observations": observations,
        "transitions": [], "measurement_pairs": [], "limitations": list(LIMITS)}
    validate_dataset(dataset)
    return cells, dataset


def audit_usuda_terminal(source_path: Path, output: Path):
    path = Path(source_path)
    if any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise InputError("Source must be a regular nonsymlink file")
    with path.open("rb") as stream:
        raw = stream.read(2_000_001)
    cells, dataset = extract_terminal(raw)
    # Differences are arithmetic on published means, never paired animal effects.
    comparisons = []
    records = {record["record_id"]: record for record in dataset["observations"]}
    for label in TERMINAL_ROWS:
        members = [cell for cell in cells if cell["source_endpoint_literal"] == label and cell["table_id"] == "T1"]
        control, apt = (records[cell["record_id"]]["observation"]["value"] for cell in members)
        comparisons.append({"endpoint_literal": label, "control_mean": control,
            "apt_mean": apt, "source_unit": members[0]["reported_unit"],
            "apt_minus_control_mean": apt - control, "apt_over_control_mean": apt / control,
            "control_record_id": members[0]["record_id"], "apt_record_id": members[1]["record_id"],
            "calculation_basis": "Arithmetic on reported unpaired group means; no adjustment, uncertainty interval or causal effect.",
            "source_p_ci_literal": members[0]["source_p_ci_literal"]})
    qualification = {"review_status": "candidate", "human_review": "pending",
        "selection": "All nine terminal numeric Table 1 rows and all 21 Table 3 rows, including the missing control TRP cell.",
        "n_records": 60, "n_numeric_summary_records": 59, "n_missing_records": 1,
        "n_individual_unit_ids": 0, "n_measurement_pairs": 0, "n_transitions": 0,
        "feasibility_implication": "Maintained circulation and terminal body weight cannot substitute for independently assessed organ/bone development. Cause of reduced development remains unresolved.",
        "limits": list(LIMITS)}
    lines = ["# Usuda terminal development intake — Cycle 346", "",
        "Agent-assisted extraction; human source review pending. No author contacted.", "",
        "The case intake already preserves support duration, weight and adverse status. This cycle adds the previously unstructured terminal group endpoints: 18 Table 1 summaries and 42 Table 3 cells (one explicitly missing). All brain, heart and femur results remain alongside the lung, liver, kidney and humerus findings. No individual observations are created from summaries.", "",
        f"Source: [Usuda et al., 2023]({ARTICLE_URL}), Tables 1 and 3; pinned Europe PMC JATS bytes. Article declares CC BY 4.0; human source-specific review remains pending.", "",
        "The source gives eight controls in the tables/main text and six in the abstract. No individual control or terminal-organ links resolve that discrepancy. Group necropsy ages differ and vary; edema complicates body mass. Published p-value/CI text and long-bone units are retained without repair.", "",
        "| Published endpoint | Control mean | APT mean | APT/control mean |",
        "| --- | ---: | ---: | ---: |"]
    lines += [f"| {row['endpoint_literal']} | {row['control_mean']:g} | {row['apt_mean']:g} | {row['apt_over_control_mean']:.3f} |" for row in comparisons]
    lines += ["", "These ratios describe the printed means. They are neither paired individual growth effects nor age-adjusted estimates; no new significance test or uncertainty interval is calculated.", "",
        "**Design consequence:** retain independent organ/bone development and fluid-state observations as separate requirements alongside support physiology. Similar body-weight summaries do not demonstrate equivalent development. The biochemical summaries retain competing endocrine, mineral/nutritional and fluid/protein hypotheses; they do not select a causal explanation or an intervention.", "",
        "The main embryo-to-birth gap is still same-unit development across early exchange, later support, neonatal transition and assessed health. This ovine endpoint dataset does not fill it.", "", *LIMITS]
    metadata = {"source_sha256": SOURCE_SHA256, "source_review_status": "candidate",
                "n_endpoints": 60, "n_reported_unit_ids": 0, "model_calibration_performed": False}
    files = {"input_source_manifest.json": json_bytes({"source_path": SOURCE_PATH,
                   "source_url": SOURCE_URL, "sha256": SOURCE_SHA256, "size_bytes": len(raw),
                   "external_source_required": True}),
               "input_dataset.json": json_bytes(dataset),
               "endpoint_cells.csv": csv_bytes(list(cells[0]), cells),
               "reported_mean_comparisons.csv": csv_bytes(list(comparisons[0]), comparisons),
               "qualification.json": json_bytes(qualification),
               "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    plan = reproduction_plan("published_endpoint_source_audit", files, metadata)
    plan["command"] = "python -m wombmodels.usuda_source --source <external-pinned-source.xml> --out <new-dir>"
    plan["inputs"] = ["input_source_manifest.json", "external pinned JATS XML (not bundled)"]
    files["reproduction_plan.json"] = json_bytes(plan)
    return publish_bundle(output, kind="published_endpoint_source_audit", input_raw=raw,
                          files=files, metadata=metadata)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    audit_usuda_terminal(arguments.source, arguments.out)
