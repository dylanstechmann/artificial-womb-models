"""Audit specimen-level phenotype coverage; no effect estimation or biological fit."""
from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json
from .observations import _enum, _number_or_reported_text, _object, _text, validate_dataset, verify_source_files

POPULATIONS = {"human_embryo", "human_blastoid", "other", "synthetic_fixture"}
OUTCOMES = {"observed", "missing", "excluded", "not_assessed"}


def _identifier(value, label):
    result = _text(value, label, 96)
    if result != value:
        raise InputError(f"{label} must not have surrounding whitespace")
    return result


def _nullable_id(value, label):
    return None if value is None else _identifier(value, label)


def _source(value, artifacts):
    _object(value, {"artifact_id", "locator"}, set(), "metadata source")
    _identifier(value["artifact_id"], "metadata artifact_id")
    if value["artifact_id"] not in artifacts:
        raise InputError("Metadata references an unknown source artifact")
    _text(value["locator"], "metadata source locator", 1000)


def _bounded_list(value, label, maximum):
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise InputError(f"{label} must list 1–{maximum} entries")
    return value


def _index(items, field, label):
    result = {}
    for item in items:
        if not isinstance(item, dict) or field not in item:
            raise InputError(f"{label} needs {field}")
        key = _identifier(item[field], field)
        if key in result:
            raise InputError(f"Duplicate {label} identifier")
        result[key] = item
    return result


def validate_phenotype_intake(data):
    """Validate complete declared matrices, retaining uncertainty about actual coverage."""
    _object(data, {"schema_version", "observation_dataset", "cohorts"}, set(), "phenotype intake")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InputError("Phenotype intake schema_version must be 1")
    dataset = validate_dataset(data["observation_dataset"])
    if dataset["transitions"]:
        raise InputError("Phenotype intake cannot assert developmental transition edges")
    artifacts = {a["artifact_id"]: a for a in dataset["artifacts"]}
    records = {r["record_id"]: r for r in dataset["observations"]}
    cohorts = _index(_bounded_list(data["cohorts"], "cohorts", 20), "cohort_id", "cohort")
    used_records, specimen_namespaces = set(), set()
    n_expected = 0
    for cohort in cohorts.values():
        _object(cohort, {"cohort_id", "population", "selection_frame", "source", "conditions",
                         "endpoints", "specimens", "outcomes"}, set(), "cohort")
        _enum(cohort["population"], POPULATIONS, "phenotype population")
        _enum(cohort["selection_frame"], {"reported_complete", "partial", "not_reported"}, "selection frame")
        _source(cohort["source"], artifacts)
        conditions = _index(_bounded_list(cohort["conditions"], "conditions", 20), "condition_id", "condition")
        for condition in conditions.values():
            _object(condition, {"condition_id", "label", "role", "assignment_note", "source"}, set(), "condition")
            _text(condition["label"], "condition label", 300)
            _enum(condition["role"], {"comparator", "exposure", "other"}, "condition role")
            if condition["assignment_note"] is not None:
                _text(condition["assignment_note"], "assignment note", 1000)
            _source(condition["source"], artifacts)
        endpoints = _index(_bounded_list(cohort["endpoints"], "endpoints", 20), "endpoint_id", "endpoint")
        endpoint_keys = set()
        for endpoint in endpoints.values():
            _object(endpoint, {"endpoint_id", "assay_name", "endpoint", "unit", "measurement_time",
                               "measurement_time_unit", "definition", "version", "calibration_note",
                               "uncertainty_note", "source"}, set(), "endpoint")
            for field, maximum in (("assay_name", 300), ("endpoint", 500), ("unit", 80),
                                   ("measurement_time_unit", 40)):
                _text(endpoint[field], field, maximum)
            time = endpoint["measurement_time"]
            if time is not None and type(time) not in (int, float):
                raise InputError("Endpoint ascertainment time must be finite numeric or null")
            _number_or_reported_text(time, "Endpoint ascertainment time")
            for field in ("definition", "version", "calibration_note", "uncertainty_note"):
                if endpoint[field] is not None:
                    _text(endpoint[field], field, 1000)
            _source(endpoint["source"], artifacts)
            endpoint_key = tuple(endpoint[field] for field in ("assay_name", "endpoint", "unit", "measurement_time", "measurement_time_unit"))
            if endpoint_key in endpoint_keys:
                raise InputError("Duplicate endpoint definitions require an explicit separate cohort/ascertainment")
            endpoint_keys.add(endpoint_key)
        specimens = _index(_bounded_list(cohort["specimens"], "specimens", 1000), "specimen_id", "specimen")
        for specimen in specimens.values():
            _object(specimen, {"specimen_id", "experiment_id", "endometrial_source_id", "condition_id", "source"}, set(), "specimen")
            _nullable_id(specimen["experiment_id"], "experiment_id")
            _nullable_id(specimen["endometrial_source_id"], "endometrial_source_id")
            _identifier(specimen["condition_id"], "condition_id")
            if specimen["condition_id"] not in conditions:
                raise InputError("Specimen references an unknown condition")
            _source(specimen["source"], artifacts)
            namespace = (cohort["source"]["artifact_id"], specimen["specimen_id"])
            if namespace in specimen_namespaces:
                raise InputError("A source specimen cannot be duplicated across phenotype cohorts")
            specimen_namespaces.add(namespace)
        n_expected += len(specimens) * len(endpoints)
        if n_expected > 5000:
            raise InputError("Phenotype matrix exceeds 5000 outcomes")
        outcomes = _bounded_list(cohort["outcomes"], "outcomes", 5000)
        covered, context = set(), None
        for outcome in outcomes:
            _object(outcome, {"specimen_id", "endpoint_id", "record_id", "status", "reason", "source"}, set(), "phenotype outcome")
            _source(outcome["source"], artifacts)
            for field in ("specimen_id", "endpoint_id", "record_id"):
                _identifier(outcome[field], field)
            pair = (outcome["specimen_id"], outcome["endpoint_id"])
            if pair[0] not in specimens or pair[1] not in endpoints or pair in covered:
                raise InputError("Unknown or duplicate specimen/endpoint outcome")
            covered.add(pair)
            rid = outcome["record_id"]
            if rid not in records or rid in used_records:
                raise InputError("Unknown or reused phenotype observation record")
            used_records.add(rid)
            record, endpoint = records[rid], endpoints[pair[1]]
            _enum(outcome["status"], OUTCOMES, "phenotype outcome status")
            _text(outcome["reason"], "outcome reason", 1000, empty=outcome["status"] == "observed")
            value = record["observation"]["value"]
            if value is not None and type(value) not in (int, float):
                raise InputError("Phenotype value must be finite numeric or null")
            if outcome["status"] == "observed" and value is None:
                raise InputError("An observed phenotype needs a numeric value")
            if outcome["status"] in {"missing", "not_assessed"} and value is not None:
                raise InputError("Missing/not_assessed outcomes cannot carry numeric values")
            unit = record["independent_unit"]
            if unit["kind"] in {"sample_pool", "not_reported"} or unit["members"] or unit["id"] != pair[0]:
                raise InputError("Phenotypes require a matching individual specimen identifier; pools are unsupported")
            if record["observation"]["replicate_role"] not in {"independent", "repeated_measure", "not_reported"}:
                raise InputError("Summary or technical rows cannot stand in for an individual phenotype")
            if record["evidence_status"] not in {"measured", "synthetic_fixture"}:
                raise InputError("Phenotype intake needs individual measurements, not planned/summary records")
            if record["assay"]["measurement_role"] not in {"function", "morphology", "other"}:
                raise InputError("Molecular identity alone is not a phenotype endpoint in this intake")
            for field, target in (("name", "assay_name"), ("endpoint", "endpoint"), ("unit", "unit")):
                if record["assay"][field] != endpoint[target]:
                    raise InputError("Phenotype assay/endpoint/unit must match exactly; no conversion is performed")
            for field in ("measurement_time", "measurement_time_unit"):
                if record["observation"][field] != endpoint[field]:
                    raise InputError("Phenotype ascertainment must match its endpoint contract exactly")
            if record["source"]["artifact_id"] != cohort["source"]["artifact_id"]:
                raise InputError("A phenotype cohort must retain a single observation source namespace")
            if outcome["source"]["artifact_id"] != record["source"]["artifact_id"]:
                raise InputError("Outcome value locator must refer to its observation source")
            interval = record["developmental_interval"]
            bounds = (interval["start"], interval["end"])
            if (endpoint["measurement_time"] is not None and endpoint["measurement_time_unit"] == interval["time_unit"]
                    and all(type(bound) in (int, float) for bound in bounds)
                    and not bounds[0] <= endpoint["measurement_time"] <= bounds[1]):
                raise InputError("Phenotype ascertainment lies outside its exact-unit developmental interval")
            population = cohort["population"]
            synthetic = record["evidence_status"] == "synthetic_fixture"
            if synthetic != (population == "synthetic_fixture"):
                raise InputError("Synthetic and source-measured phenotype populations must remain separate")
            if not synthetic and record["model_system"]["kind"] == "simulation":
                raise InputError("Simulation records cannot be relabeled as measured phenotypes")
            if synthetic and (record["species"] != "unspecified" or record["model_system"]["kind"] != "simulation"
                              or endpoint["unit"] != "dimensionless" or endpoint["measurement_time_unit"] != "dimensionless_fixture_time"):
                raise InputError("Synthetic phenotypes must remain unspecified dimensionless software fixtures")
            if population.startswith("human_") and record["species"] != "human":
                raise InputError("Human phenotype population must retain human species")
            if population == "human_embryo" and (unit["kind"] != "embryo" or record["model_system"]["kind"] not in {"intact_organism", "tissue_construct"}):
                raise InputError("Human embryo phenotypes require embryo identifiers and intact/scaffold model context")
            if population == "human_blastoid" and record["model_system"]["kind"] != "embryo_model":
                raise InputError("A blastoid phenotype must retain its embryo-model context")
            model = record["model_system"]
            current_context = (record["species"], record["stage_track"], model["kind"], model["label"], model["laboratory_id"],
                               json_bytes(record["developmental_interval"]))
            if context is not None and current_context != context:
                raise InputError("Different species/stages/model contexts/intervals require separate phenotype cohorts")
            context = current_context
        if len(covered) != len(specimens) * len(endpoints):
            raise InputError("Every roster specimen needs every declared endpoint, including explicit missing/excluded/not_assessed outcomes")
    if used_records != set(records):
        raise InputError("All observation records must be used exactly once in phenotype outcomes")
    return data


def phenotype_report(dataset_path: Path, output: Path, source_root: Path | None = None) -> dict:
    data, raw = read_json(dataset_path)
    validate_phenotype_intake(data)
    dataset = data["observation_dataset"]
    verification = verify_source_files(dataset["artifacts"], source_root)
    records = {r["record_id"]: r for r in dataset["observations"]}
    outcome_rows, groups, blockers = [], defaultdict(list), []
    synthetic = any(r["evidence_status"] == "synthetic_fixture" for r in records.values())
    if synthetic:
        blockers.append("Contains artificial dimensionless software fixtures; biological analysis is inapplicable.")
    if dataset["source_revision"]["review_status"] != "locally_reviewed_included":
        blockers.append("Source has no recorded included human review decision.")
    if verification["status"] != "complete":
        blockers.append("Not all declared local source bytes have verified hashes.")
    artifacts = {a["artifact_id"]: a for a in dataset["artifacts"]}
    if any("developmental_scope" not in artifacts[r["developmental_interval"]["stage_source_artifact_id"]]
           or any(type(r["developmental_interval"][field]) not in (int, float) for field in ("start", "end"))
           or r["observation"]["measurement_time_unit"] != r["developmental_interval"]["time_unit"] for r in records.values()):
        blockers.append("Some ascertainment/developmental intervals lack exact-unit numeric source containment.")
    hierarchy, measurement_gaps = [], []
    for cohort in data["cohorts"]:
        cid = cohort["cohort_id"]
        if cohort["selection_frame"] != "reported_complete":
            blockers.append(f"{cid}: starting selection frame is partial or unreported.")
        conditions = {c["condition_id"]: c for c in cohort["conditions"]}
        if not any(c["role"] == "comparator" for c in conditions.values()):
            blockers.append(f"{cid}: no comparator condition is declared.")
        if any(c["assignment_note"] is None for c in conditions.values()):
            blockers.append(f"{cid}: condition assignment metadata is missing.")
        endpoints = {e["endpoint_id"]: e for e in cohort["endpoints"]}
        for endpoint in endpoints.values():
            missing = [field for field in ("definition", "version", "calibration_note", "uncertainty_note") if endpoint[field] is None]
            if endpoint["measurement_time"] is None:
                missing.append("measurement_time")
            if missing:
                measurement_gaps.append({"cohort_id": cid, "endpoint_id": endpoint["endpoint_id"], "missing_fields": missing})
        specimens = {s["specimen_id"]: s for s in cohort["specimens"]}
        present_conditions = {s["condition_id"] for s in specimens.values()}
        if set(conditions) - present_conditions:
            blockers.append(f"{cid}: some declared conditions have no roster specimens.")
        experiments, sources, edges = set(), set(), set()
        for specimen in specimens.values():
            if specimen["experiment_id"] is not None:
                experiments.add(specimen["experiment_id"])
            if specimen["endometrial_source_id"] is not None:
                sources.add(specimen["endometrial_source_id"])
            if specimen["experiment_id"] is not None and specimen["endometrial_source_id"] is not None:
                edges.add((specimen["experiment_id"], specimen["endometrial_source_id"]))
        missing_hierarchy = sum(s["experiment_id"] is None or s["endometrial_source_id"] is None for s in specimens.values())
        if missing_hierarchy:
            blockers.append(f"{cid}: {missing_hierarchy} declared specimens lack experiment or endometrial-source IDs.")
        hierarchy.append({"cohort_id": cid, "population": cohort["population"], "selection_frame": cohort["selection_frame"],
            "n_declared_specimens": len(specimens),
            "n_experiment_labels": len(experiments), "n_endometrial_source_labels": len(sources),
            "n_experiment_source_links": len(edges), "n_specimens_with_incomplete_hierarchy": missing_hierarchy,
            "interpretation": "Declared label counts, not verified independent biological n."})
        for outcome in cohort["outcomes"]:
            specimen, endpoint = specimens[outcome["specimen_id"]], endpoints[outcome["endpoint_id"]]
            record = records[outcome["record_id"]]
            row = {"cohort_id": cid, "population": cohort["population"], "specimen_id": specimen["specimen_id"],
                "experiment_id": specimen["experiment_id"], "endometrial_source_id": specimen["endometrial_source_id"],
                "condition_id": specimen["condition_id"], "condition_role": conditions[specimen["condition_id"]]["role"],
                "endpoint_id": endpoint["endpoint_id"], "endpoint": endpoint["endpoint"], "unit": endpoint["unit"],
                "species": record["species"], "stage_track": record["stage_track"],
                "model_kind": record["model_system"]["kind"], "model_label": record["model_system"]["label"],
                "interval_label": record["developmental_interval"]["label"],
                "interval_start": record["developmental_interval"]["start"], "interval_end": record["developmental_interval"]["end"],
                "interval_time_unit": record["developmental_interval"]["time_unit"],
                "status": outcome["status"], "reason": outcome["reason"], "record_id": outcome["record_id"],
                "value": record["observation"]["value"], "evidence_status": record["evidence_status"],
                "measurement_time": record["observation"]["measurement_time"],
                "measurement_time_unit": record["observation"]["measurement_time_unit"],
                "measurement_uncertainty": record["observation"]["measurement_uncertainty"],
                "missingness_reason": record["observation"]["missingness_reason"],
                "independent_unit_kind": record["independent_unit"]["kind"], "independent_unit_parent_id": record["independent_unit"]["parent_id"],
                "source_artifact_id": record["source"]["artifact_id"], "specimen_source_locator": specimen["source"]["locator"],
                "endpoint_source_locator": endpoint["source"]["locator"], "value_source_locator": outcome["source"]["locator"]}
            outcome_rows.append(row)
            key = (cid, endpoint["endpoint_id"], specimen["experiment_id"], specimen["endometrial_source_id"], specimen["condition_id"])
            groups[key].append(row)
        for endpoint in endpoints.values():
            for condition in conditions.values():
                if not any(outcome["status"] == "observed" and outcome["endpoint_id"] == endpoint["endpoint_id"]
                           and specimens[outcome["specimen_id"]]["condition_id"] == condition["condition_id"]
                           for outcome in cohort["outcomes"]):
                    blockers.append(f"{cid}/{endpoint['endpoint_id']}/{condition['condition_id']}: no observed values in this declared condition.")
    if measurement_gaps:
        blockers.append("Some endpoints lack measurement definition/version/calibration/uncertainty/ascertainment metadata.")
    summaries = []
    for key, rows in sorted(groups.items(), key=lambda item: tuple("" if x is None else x for x in item[0])):
        values = [row["value"] for row in rows if row["status"] == "observed"]
        ordered = sorted(values)
        middle = len(ordered) // 2
        med = None
        if values:
            med = ordered[middle]
            if len(ordered) % 2 == 0:
                left, right = ordered[middle - 1], ordered[middle]
                total = left + right
                # Use the sum for subnormal precision; halve first only for float overflow.
                med = left / 2 + right / 2 if isinstance(total, float) and not math.isfinite(total) else total / 2
        summaries.append({"cohort_id": key[0], "population": rows[0]["population"], "evidence_status": rows[0]["evidence_status"],
            "endpoint_id": key[1], "experiment_id": key[2],
            "endometrial_source_id": key[3], "condition_id": key[4], "unit": rows[0]["unit"],
            **{field: rows[0][field] for field in ("species", "stage_track", "model_kind", "model_label", "interval_label",
                "interval_start", "interval_end", "interval_time_unit", "measurement_time", "measurement_time_unit")},
            "n_declared_specimens": len(rows), **{f"n_{status}": sum(row["status"] == status for row in rows) for status in sorted(OUTCOMES)},
            "observed_min": min(values) if values else None, "observed_median": med,
            "observed_max": max(values) if values else None})
    report = {"schema_version": 1, "dataset_id": dataset["dataset_id"], "source_review_status": dataset["source_revision"]["review_status"],
        "source_file_verification": verification, "n_outcomes": len(outcome_rows), "hierarchy": hierarchy,
        "measurement_metadata_gaps": measurement_gaps, "analysis_blockers": blockers,
        "structural_status": "declared_specimen_endpoint_matrix_complete",
        "qualification_status": "unresolved" if blockers else "recorded_requirements_present_for_human_review",
        "human_review_authenticated": False, "effect_estimation": "not_performed", "paired_identity_function_linkage": "not_assessed",
        "limits": ["Roster completeness, metadata accuracy and review assertions are not authenticated by software.",
            "Observed summaries exclude excluded/missing/not-assessed outcomes; excluded numeric values remain in phenotype_outcomes.csv.",
            "Experiment/source labels are separate grouping dimensions; their counts do not prove biological independence.",
            "No cross-experiment pooled effect, hypothesis test, uncertainty interval, biological fit or gestation outcome is produced.",
            "Source units and ascertainment are exact; no conversion or phenotype/transcriptomic linkage is inferred."]}
    lines = ["# Specimen phenotype intake", "", f"Dataset: {dataset['dataset_id']}",
        f"Declared specimen/endpoint outcomes: {len(outcome_rows)}. Qualification: {report['qualification_status']}.",
        "", "This is a coverage and hierarchy audit. No biological effect is estimated.", "",
        "## Unresolved requirements", ""]
    lines += ["- " + b for b in blockers] or ["- Recorded requirements are present; human review and provenance authentication remain external."]
    lines += ["", "## Outputs", "", "phenotype_outcomes.csv retains every value and exclusion; endpoint_groups.csv separates experiment/source/condition groups; hierarchy.csv inventories declared labels.",
        "", "## Limits", "", *["- " + limit for limit in report["limits"]]]
    return publish_bundle(output, kind="specimen_phenotype_intake", input_raw=raw,
        files={"input_phenotypes.json": raw, "phenotype_report.json": json_bytes(report),
            "phenotype_outcomes.csv": csv_bytes(list(outcome_rows[0]), outcome_rows),
            "endpoint_groups.csv": csv_bytes(list(summaries[0]), summaries),
            "hierarchy.csv": csv_bytes(list(hierarchy[0]), hierarchy), "REPORT.md": ("\n".join(lines) + "\n").encode()},
        metadata={"source_review_status": dataset["source_revision"]["review_status"], "contains_synthetic_fixture": synthetic,
            "biological_assay_performed": False, "effect_estimation": "not_performed"})
