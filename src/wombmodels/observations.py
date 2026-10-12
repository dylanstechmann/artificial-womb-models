"""Validate source-linked developmental observation records without pooling studies."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json

EVIDENCE_STATUSES = {"measured", "author_reported_summary", "planned", "synthetic_fixture"}
SPECIES = {"human", "mouse", "ovine", "rat", "chick", "other", "unspecified"}
STAGE_TRACKS = {"preimplantation", "implantation_and_placentation", "postimplantation_embryonic",
                "partial_fetal_support", "transition_to_neonatal", "developmental_outcomes",
                "organoid_or_tissue_model", "unspecified"}
MODEL_KINDS = {"intact_organism", "embryo_model", "organoid", "tissue_construct", "cell_culture",
               "simulation", "other"}
MEASUREMENT_ROLES = {"morphology", "molecular_identity", "function", "viability", "genome_stability",
                     "adverse_effect", "durability", "environmental_condition", "other"}
FUNCTIONAL_EVIDENCE_CLASSES = {"direct_function_measurement", "biological_response_proxy",
                               "developmental_outcome", "other"}
FUNCTIONAL_PROCESSES = {"uptake", "intracellular_processing", "passage", "secretion",
                        "tissue_abundance", "developmental_outcome", "other", "unspecified"}
ASSESSMENT_CONTEXTS = {"in_utero", "ex_utero_whole_embryo", "isolated_tissue",
                       "cell_culture", "simulation", "other", "unspecified"}
FUNCTIONAL_CONTEXT_FIELDS = ("compartment", "material", "process", "quantity_basis",
                             "assessment_context", "source_locator")
UNIT_KINDS = {"donor", "pregnant_animal", "fetus", "embryo", "source_kidney", "organoid", "vessel_construct",
              "culture_batch", "sample_pool", "other", "not_reported"}
REPLICATE_ROLES = {"independent", "repeated_measure", "technical", "summary_only", "not_reported"}
COUNTED_ENTITIES = {"embryo", "fetus", "recipient_animal", "tissue_fragment", "imaging_subsample",
                    "assay_event", "other", "unresolved"}
COVERAGE_CATEGORIES = {"initially_included", "assessed", "attached", "retained", "shed",
                       "assay_withdrawn", "excluded", "missing", "not_assessed",
                       "endpoint_measure", "other"}
DISPOSITION_COUNT_CATEGORIES = {"assessed", "attached", "retained", "shed", "assay_withdrawn",
                               "excluded", "missing", "not_assessed"}
COVERAGE_VALUE_STATUSES = {"reported", "not_reported", "ambiguous"}
COHORT_WINDOW_STATUSES = {"source_reported_common", "source_labels_only", "not_reported", "unresolved"}
MEASUREMENT_PAIR_TYPES = {"same_sample", "same_unit_same_time", "before_after", "interface_sides", "other_source_defined"}
MEASUREMENT_PAIR_LINKAGE_BASES = {"source_explicit", "curator_linked"}
DISPOSITION_COMPLETENESS = {"complete", "partial", "unknown"}
SOURCE_DECLARATION_STATES = {"source_reported_yes", "source_reported_no", "unknown"}
SOURCE_KINDS = {"peer_reviewed_animal", "peer_reviewed_human_invitro", "peer_reviewed_human_invivo", "regulator_discussion",
                "institution_announcement", "dataset_record", "preprint", "other"}
REVIEW_STATES = {"candidate", "locally_reviewed_included", "locally_reviewed_excluded"}
HEX64 = re.compile(r"[0-9a-f]{64}")
RECORD_ID = re.compile(r"[a-z0-9][a-z0-9._-]{2,95}")
QUALIFICATION_CODE = re.compile(r"[a-z][a-z0-9_]{1,79}")
MAX_SOURCE_FILE_BYTES = 1_000_000_000
MAX_SOURCE_TOTAL_BYTES = 2_000_000_000


def _object(value, required, optional, label):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise InputError(f"{label} must contain exactly its documented fields")
    return value


def _text(value, label, maximum=1000, *, empty=False):
    if (not isinstance(value, str) or len(value) > maximum
            or (not empty and not value.strip())):
        raise InputError(f"{label} must be {'text' if empty else 'nonempty text'} of at most {maximum} characters")
    return value.strip()


def _enum(value, choices, label):
    if not isinstance(value, str) or value not in choices:
        raise InputError(f"Unknown {label}")
    return value


def _date(value, label, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InputError(f"{label} must be an ISO calendar date" if not nullable else f"{label} must be an ISO date or null")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f"{label} must be an ISO calendar date") from exc


def _url(value, label):
    value = _text(value, label, 3000)
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise InputError(f"{label} must be an HTTPS URL") from exc
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise InputError(f"{label} must be an HTTPS URL")
    return value


def _string_or_null(value, label, maximum=120):
    if value is not None:
        _text(value, label, maximum)


def _number_or_reported_text(value, label):
    if value is None or isinstance(value, str):
        if isinstance(value, str) and len(value) > 120:
            raise InputError(f"{label} is too long")
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be numeric, reported text, or null")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise InputError(f"{label} must be finite")


def _validate_developmental_scope(value):
    scope = _object(value, {"species", "stage_tracks", "time_unit", "start", "end",
                            "source_locator"}, set(), "developmental_scope")
    _enum(scope["species"], SPECIES, "source-scope species")
    stages = scope["stage_tracks"]
    if (not isinstance(stages, list) or not 1 <= len(stages) <= len(STAGE_TRACKS)
            or any(not isinstance(stage, str) or stage not in STAGE_TRACKS for stage in stages)
            or len(set(stages)) != len(stages)):
        raise InputError("developmental_scope.stage_tracks must list distinct known stages")
    _text(scope["time_unit"], "developmental_scope.time_unit", 40)
    _text(scope["source_locator"], "developmental_scope.source_locator", 1000)
    for field in ("start", "end"):
        if scope[field] is None:
            continue
        if isinstance(scope[field], bool) or not isinstance(scope[field], (int, float)):
            raise InputError("developmental_scope bounds must be finite numeric values or null")
        _number_or_reported_text(scope[field], f"developmental_scope.{field}")
    if scope["start"] is not None and scope["end"] is not None and scope["end"] < scope["start"]:
        raise InputError("developmental_scope end precedes its start")
    return scope


def _check_interval_scope(record, artifacts):
    interval = record["developmental_interval"]
    scope = artifacts[interval["stage_source_artifact_id"]].get("developmental_scope")
    if scope is None:
        return "not_declared"
    if record["species"] != scope["species"] or record["stage_track"] not in scope["stage_tracks"]:
        raise InputError("Observation species/stage lies outside its declared source developmental_scope")
    if interval["time_unit"] != scope["time_unit"]:
        raise InputError("Observation interval must use the exact source-scope time unit; no conversion is performed")
    numeric_bounds = [interval[field] for field in ("start", "end")
                      if not isinstance(interval[field], bool) and isinstance(interval[field], (int, float))]
    for bound in numeric_bounds:
        if ((scope["start"] is not None and bound < scope["start"])
                or (scope["end"] is not None and bound > scope["end"])):
            raise InputError("Observation interval lies outside its declared source developmental_scope bounds")
    if len(numeric_bounds) == 2 and scope["start"] is not None and scope["end"] is not None:
        return "contained_in_declared_scope"
    if numeric_bounds and (scope["start"] is not None or scope["end"] is not None):
        return "partially_checked"
    return "not_numeric" if not numeric_bounds else "source_bounds_unknown"


def _validate_source_revision(value):
    required = {"revision_id", "citation", "source_kind", "source_url", "review_status",
                "reviewer", "reviewed_on", "review_note"}
    source = _object(value, required, set(), "source_revision")
    revision_id = _text(source["revision_id"], "source_revision.revision_id", 96)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,95}", revision_id):
        raise InputError("source_revision.revision_id has an invalid format")
    _text(source["citation"], "source_revision.citation", 2000)
    _enum(source["source_kind"], SOURCE_KINDS, "source kind")
    _url(source["source_url"], "source_revision.source_url")
    status = _enum(source["review_status"], REVIEW_STATES, "source review state")
    reviewer = _text(source["reviewer"], "source_revision.reviewer", 200, empty=True)
    review_note = _text(source["review_note"], "source_revision.review_note", 2000, empty=True)
    if status == "candidate":
        if reviewer or source["reviewed_on"] is not None or review_note:
            raise InputError("Candidate sources cannot carry a completed local review")
    else:
        if not reviewer or not review_note:
            raise InputError("A locally reviewed source needs a reviewer and decision note")
        _date(source["reviewed_on"], "source_revision.reviewed_on")
    return source


def _validate_artifact(value, source_ids):
    required = {"artifact_id", "uri", "license", "sha256", "retrieved_on"}
    item = _object(value, required, {"local_path", "developmental_scope", "source_resolution"}, "source artifact")
    artifact_id = _text(item["artifact_id"], "artifact_id", 96)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,95}", artifact_id) or artifact_id in source_ids:
        raise InputError(f"Invalid or duplicate source artifact ID: {artifact_id}")
    _url(item["uri"], "source artifact URI")
    _text(item["license"], "source artifact license", 120)
    digest = item["sha256"]
    if digest is not None and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
        raise InputError("Source artifact SHA-256 must be 64 lowercase hexadecimal characters or null")
    _date(item["retrieved_on"], "source artifact retrieved_on", nullable=True)
    if "developmental_scope" in item:
        _validate_developmental_scope(item["developmental_scope"])
    if "source_resolution" in item:
        resolution = _object(item["source_resolution"],
            {"version_type", "version_identifier", "access_status", "oa_subset_status", "reuse_status",
             "license_expression", "checked_on", "evidence_locator", "note"}, set(),
            "source artifact source_resolution")
        _enum(resolution["version_type"], {"published_version", "accepted_manuscript", "author_manuscript",
              "preprint", "repository_record", "unknown"}, "source version type")
        _text(resolution["version_identifier"], "source version identifier", 300)
        _enum(resolution["access_status"], {"full_text_free_to_read", "metadata_only", "restricted", "unknown"},
              "source full-text access status")
        _enum(resolution["oa_subset_status"], {"included", "not_included", "not_checked", "not_applicable"},
              "source OA-subset status")
        reuse_status = _enum(resolution["reuse_status"],
            {"explicit_license", "not_confirmed", "permission_required", "public_domain"}, "source reuse status")
        license_expression = resolution["license_expression"]
        if reuse_status == "explicit_license":
            _text(license_expression, "source license expression", 200)
        elif license_expression is not None:
            raise InputError("source license expression must be null unless an explicit license is identified")
        _date(resolution["checked_on"], "source_resolution.checked_on")
        _text(resolution["evidence_locator"], "source resolution evidence locator", 1000)
        _text(resolution["note"], "source resolution note", 1200)
    item.setdefault("local_path", None)
    if item["local_path"] is not None:
        local_path = _text(item["local_path"], "source artifact local_path", 500)
        normalized = local_path.replace("\\", "/")
        components = normalized.split("/")
        if (normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized)
                or any(part in {"", ".", ".."} or ":" in part for part in components)
                or any(ord(character) < 32 for character in normalized)):
            raise InputError("source artifact local_path must be a relative path without dot segments or control characters")
        item["local_path"] = normalized
    return item


def _validate_record(value, artifacts):
    required = {"schema_version", "record_id", "evidence_status", "species", "stage_track",
                "developmental_interval", "model_system", "assay", "independent_unit",
                "observation", "source"}
    record = _object(value, required, {"limitations", "source_locator"}, "observation record")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise InputError("Observation schema_version must be 1")
    record_id = _text(record["record_id"], "record_id", 96)
    if not RECORD_ID.fullmatch(record_id):
        raise InputError("record_id has an invalid format")
    if "source_locator" in record:
        _text(record["source_locator"], "source_locator", 1000)
    _enum(record["evidence_status"], EVIDENCE_STATUSES, "evidence status")
    _enum(record["species"], SPECIES, "species")
    _enum(record["stage_track"], STAGE_TRACKS, "stage_track")

    interval = _object(record["developmental_interval"],
                       {"label", "time_unit", "stage_source_artifact_id"}, {"start", "end"},
                       "developmental_interval")
    _text(interval["label"], "developmental_interval.label", 120)
    _text(interval["time_unit"], "developmental_interval.time_unit", 40)
    stage_artifact = _text(interval["stage_source_artifact_id"], "stage_source_artifact_id", 96)
    if stage_artifact not in artifacts:
        raise InputError("developmental interval references an unknown source artifact")
    for field in ("start", "end"):
        interval.setdefault(field, None)
        _number_or_reported_text(interval[field], f"developmental_interval.{field}")
    if (isinstance(interval["start"], (int, float)) and not isinstance(interval["start"], bool)
            and isinstance(interval["end"], (int, float)) and not isinstance(interval["end"], bool)
            and interval["end"] < interval["start"]):
        raise InputError("Developmental interval end precedes its start")
    if (interval["start"] is not None and interval["end"] is not None
            and isinstance(interval["start"], (int, float)) != isinstance(interval["end"], (int, float))):
        raise InputError("Developmental interval boundaries must use the same reported value type")

    model = _object(record["model_system"], {"kind", "label"}, {"batch_id", "laboratory_id"}, "model_system")
    _enum(model["kind"], MODEL_KINDS, "model-system kind")
    _text(model["label"], "model_system.label", 500)
    for field in ("batch_id", "laboratory_id"):
        model.setdefault(field, None)
        _string_or_null(model[field], f"model_system.{field}", 120)

    assay = _object(record["assay"], {"name", "endpoint", "unit", "measurement_role"},
                    {"calibration_artifact_id", "functional_context", "functional_evidence_class"}, "assay")
    _text(assay["name"], "assay.name", 300)
    _text(assay["endpoint"], "assay.endpoint", 500)
    _text(assay["unit"], "assay.unit", 80)
    _enum(assay["measurement_role"], MEASUREMENT_ROLES, "measurement role")
    if "functional_evidence_class" in assay:
        _enum(assay["functional_evidence_class"], FUNCTIONAL_EVIDENCE_CLASSES,
              "functional evidence class")
    if "functional_context" in assay:
        context = _object(assay["functional_context"], FUNCTIONAL_CONTEXT_FIELDS, set(),
                          "assay.functional_context")
        for field in ("compartment", "material", "quantity_basis"):
            _text(context[field], f"functional_context.{field}", 300)
        _text(context["source_locator"], "functional_context.source_locator", 1000)
        _enum(context["process"], FUNCTIONAL_PROCESSES, "functional process")
        _enum(context["assessment_context"], ASSESSMENT_CONTEXTS, "assessment context")
    calibration = assay.setdefault("calibration_artifact_id", None)
    if calibration is not None:
        calibration = _text(calibration, "calibration_artifact_id", 96)
        if calibration not in artifacts:
            raise InputError("Calibration references an unknown source artifact")

    unit = _object(record["independent_unit"], {"kind", "id", "parent_id"}, {"hierarchy_note", "members"}, "independent_unit")
    _enum(unit["kind"], UNIT_KINDS, "independent-unit kind")
    for field in ("id", "parent_id"):
        _string_or_null(unit[field], f"independent_unit.{field}")
        if unit[field] is not None:
            unit[field] = _text(unit[field], f"independent_unit.{field}", 120)
    unit.setdefault("hierarchy_note", "")
    _text(unit["hierarchy_note"], "independent_unit.hierarchy_note", 500, empty=True)
    if unit["kind"] == "not_reported" and (unit["id"] is not None or unit["parent_id"] is not None):
        raise InputError("A not_reported unit cannot carry an asserted unit identifier")
    pool_members = unit.setdefault("members", [])
    if not isinstance(pool_members, list) or len(pool_members) > 100:
        raise InputError("Pool members must list at most 100 source-reported identifiers")
    if pool_members and (unit["kind"] != "sample_pool" or unit["id"] is None):
        raise InputError("Pool members require a reported sample_pool identifier")
    member_keys = set()
    for member in pool_members:
        _object(member, {"kind", "id"}, {"parent_id"}, "pool member")
        _enum(member["kind"], UNIT_KINDS - {"sample_pool", "not_reported"}, "pool-member kind")
        member["id"] = _text(member["id"], "pool-member id", 120)
        parent = member.setdefault("parent_id", None)
        _string_or_null(parent, "pool-member parent_id")
        if parent is not None:
            member["parent_id"] = _text(parent, "pool-member parent_id", 120)
        key = (member["kind"], member["id"], member["parent_id"])
        if key in member_keys:
            raise InputError("Pool members must have distinct source identifiers")
        member_keys.add(key)

    observation = _object(record["observation"],
                          {"value", "measurement_time", "comparator_id", "replicate_role"},
                          {"measurement_time_unit", "measurement_uncertainty", "missingness_reason",
                           "source_qualifications", "summary_statistic", "measurement_conditions"},
                          "observation")
    _number_or_reported_text(observation["value"], "observation.value")
    _number_or_reported_text(observation["measurement_time"], "observation.measurement_time")
    observation.setdefault("measurement_time_unit", "")
    observation.setdefault("measurement_uncertainty", None)
    observation.setdefault("missingness_reason", "")
    _text(observation["measurement_time_unit"], "measurement_time_unit", 80, empty=True)
    _number_or_reported_text(observation["measurement_uncertainty"], "measurement_uncertainty")
    if (isinstance(observation["measurement_uncertainty"], (int, float))
            and not isinstance(observation["measurement_uncertainty"], bool)
            and observation["measurement_uncertainty"] < 0):
        raise InputError("measurement_uncertainty cannot be negative")
    if observation["measurement_time"] is not None and not observation["measurement_time_unit"]:
        raise InputError("A reported measurement_time needs its reported time unit")
    missingness = _text(observation["missingness_reason"], "missingness_reason", 500, empty=True)
    value_is_missing = observation["value"] is None or observation["value"] == ""
    if value_is_missing and not missingness:
        raise InputError("A missing observation value needs a missingness_reason")
    if not value_is_missing and missingness:
        raise InputError("A nonmissing observation cannot carry a missingness_reason")
    _string_or_null(observation["comparator_id"], "observation.comparator_id")
    role = _enum(observation["replicate_role"], REPLICATE_ROLES, "replicate role")
    summary_statistic = observation.get("summary_statistic")
    if "summary_statistic" in observation:
        if not isinstance(summary_statistic, dict):
            raise InputError("summary_statistic must be an object")
        common = {"kind", "reported_sample_size", "sample_size_scope",
                  "sample_size_source_locator", "source_literal"}
        kind = _enum(summary_statistic.get("kind"), {"median_iqr", "mean_sd", "reported_plus_minus"},
                     "summary statistic kind")
        if kind == "median_iqr":
            summary_statistic = _object(summary_statistic,
                common | {"lower_quartile", "upper_quartile"}, set(), "summary_statistic")
            fields = ("lower_quartile", "upper_quartile")
        elif kind == "mean_sd":
            summary_statistic = _object(summary_statistic,
                common | {"mean", "standard_deviation"}, set(), "summary_statistic")
            fields = ("mean", "standard_deviation")
        else:
            summary_statistic = _object(summary_statistic,
                common | {"estimate", "plus_minus", "plus_minus_type"}, set(), "summary_statistic")
            fields = ("estimate", "plus_minus")
        for field in fields:
            number = summary_statistic[field]
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise InputError(f"summary_statistic.{field} must be finite numeric")
            _number_or_reported_text(number, f"summary_statistic.{field}")
        central_value = observation["value"]
        if isinstance(central_value, bool) or not isinstance(central_value, (int, float)):
            raise InputError(f"A {kind} summary needs a numeric observation.value")
        if kind == "median_iqr":
            lower = summary_statistic["lower_quartile"]
            upper = summary_statistic["upper_quartile"]
            if lower > central_value or central_value > upper:
                raise InputError("Median and quartiles must be ordered lower <= median <= upper")
        elif kind == "mean_sd":
            if central_value != summary_statistic["mean"]:
                raise InputError("A mean_sd summary's observation.value must equal its reported mean")
            if summary_statistic["standard_deviation"] < 0:
                raise InputError("summary_statistic.standard_deviation cannot be negative")
        else:
            if central_value != summary_statistic["estimate"]:
                raise InputError("A reported_plus_minus summary's observation.value must equal its reported estimate")
            if summary_statistic["plus_minus"] < 0:
                raise InputError("summary_statistic.plus_minus cannot be negative")
            _enum(summary_statistic["plus_minus_type"],
                  {"standard_deviation", "standard_error", "confidence_interval",
                   "measurement_uncertainty", "not_reported"}, "plus-minus type")
        sample_size = summary_statistic["reported_sample_size"]
        if sample_size is not None and (isinstance(sample_size, bool)
                                        or not isinstance(sample_size, int)
                                        or not 1 <= sample_size <= 1_000_000_000):
            raise InputError("summary_statistic.reported_sample_size must be a positive integer or null")
        _text(summary_statistic["sample_size_scope"], "summary_statistic.sample_size_scope", 500)
        _text(summary_statistic["sample_size_source_locator"],
              "summary_statistic.sample_size_source_locator", 1000)
        _text(summary_statistic["source_literal"], "summary_statistic.source_literal", 200)
        if record["evidence_status"] != "author_reported_summary" or role != "summary_only":
            raise InputError("A typed distribution summary must be author_reported_summary with summary_only role")
    if role == "independent" and unit["kind"] == "not_reported":
        raise InputError("An independent replicate needs a source-reported unit kind")
    conditions = observation.setdefault("measurement_conditions", [])
    if not isinstance(conditions, list) or len(conditions) > 20:
        raise InputError("measurement_conditions must be a list of at most 20 declarations")
    condition_names = set()
    for condition in conditions:
        condition = _object(condition, {"name", "value", "unit", "source_locator"},
                            set(), "measurement condition")
        name = _text(condition["name"], "measurement condition name", 80)
        if not QUALIFICATION_CODE.fullmatch(name):
            raise InputError("measurement condition name must be a lowercase code")
        if name in condition_names:
            raise InputError("measurement condition names must be unique within a record")
        condition_names.add(name)
        value = condition["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise InputError("measurement condition value must be finite numeric or reported text")
        if isinstance(value, str):
            _text(value, "measurement condition value", 200)
        else:
            _number_or_reported_text(value, "measurement condition value")
        condition["unit"] = _text(condition["unit"], "measurement condition unit", 80, empty=True)
        _text(condition["source_locator"], "measurement condition source_locator", 1000)
    qualifications = observation.setdefault("source_qualifications", [])
    if not isinstance(qualifications, list) or len(qualifications) > 20:
        raise InputError("source_qualifications must be a list of at most 20 declarations")
    qualification_keys = set()
    for qualification in qualifications:
        qualification = _object(qualification,
            {"criterion_code", "status_code", "criterion_label", "source_artifact_id",
             "source_locator", "reference_value", "reference_unit"}, set(), "source qualification")
        for field in ("criterion_code", "status_code"):
            token = _text(qualification[field], f"source qualification {field}", 80)
            if not QUALIFICATION_CODE.fullmatch(token):
                raise InputError(f"source qualification {field} must be a lowercase code")
        _text(qualification["criterion_label"], "source qualification criterion_label", 300)
        qualification_artifact_id = _text(qualification["source_artifact_id"],
                                           "source qualification source_artifact_id", 96)
        if qualification_artifact_id not in artifacts:
            raise InputError("Source qualification references an unknown source artifact")
        _text(qualification["source_locator"], "source qualification source_locator", 1000)
        reference_value = qualification["reference_value"]
        if reference_value is not None:
            _number_or_reported_text(reference_value, "source qualification reference_value")
            if isinstance(reference_value, bool) or not isinstance(reference_value, (int, float)):
                raise InputError("source qualification reference_value must be numeric or null")
        qualification["reference_unit"] = _text(
            qualification["reference_unit"], "source qualification reference_unit", 80, empty=True)
        if reference_value is not None and not qualification["reference_unit"]:
            raise InputError("A numeric source qualification reference needs its reported unit")
        key = (qualification["criterion_code"], qualification_artifact_id,
               qualification["source_locator"])
        if key in qualification_keys:
            raise InputError("Source qualifications must have distinct criterion/source locators")
        qualification_keys.add(key)

    source = _object(record["source"], {"artifact_id", "uri", "license", "sha256"},
                     {"retrieved_on"}, "record source")
    source_artifact_id = _text(source["artifact_id"], "source.artifact_id", 96)
    if source_artifact_id not in artifacts:
        raise InputError("Observation references an unknown source artifact")
    artifact = artifacts[source_artifact_id]
    _url(source["uri"], "source.uri")
    _text(source["license"], "source.license", 120)
    _date(source.setdefault("retrieved_on", artifact["retrieved_on"]), "source.retrieved_on", nullable=True)
    if any(source[field] != artifact[field] for field in ("uri", "license", "sha256")):
        raise InputError("Observation source metadata must match its source artifact revision")
    if source["retrieved_on"] != artifact["retrieved_on"]:
        raise InputError("Observation retrieval date must match its source artifact revision")

    limitations = record.setdefault("limitations", [])
    if (not isinstance(limitations, list) or len(limitations) > 50
            or not all(isinstance(item, str) and 8 <= len(item) <= 1000 for item in limitations)):
        raise InputError("limitations must be a list of at most 50 explanatory strings")
    return record


def _validate_transition(value, records):
    required = {"transition_id", "from_record_ids", "to_record_ids", "continuity_status", "note"}
    transition = _object(value, required, set(), "transition")
    identifier = _text(transition["transition_id"], "transition_id", 96)
    if not RECORD_ID.fullmatch(identifier):
        raise InputError("transition_id has an invalid format")
    left, right = transition["from_record_ids"], transition["to_record_ids"]
    if (not isinstance(left, list) or not left or not isinstance(right, list) or not right
            or len(left) > 100 or len(right) > 100
            or not all(isinstance(item, str) for item in left + right)
            or len(set(left)) != len(left) or len(set(right)) != len(right)
            or set(left + right) - set(records) or set(left) & set(right)):
        raise InputError("Transition sides must list distinct known observation IDs")
    status = _enum(transition["continuity_status"], {"demonstrated", "contradicted", "not_reported"},
                   "same-unit continuity status")
    _text(transition["note"], "transition.note", 1000)
    members = [records[item] for item in left + right]
    if len({item["species"] for item in members}) != 1:
        raise InputError("A transition cannot combine species or model species")
    if status == "demonstrated":
        if any(item["independent_unit"]["kind"] == "sample_pool" for item in members):
            raise InputError("A sample pool cannot establish demonstrated individual developmental continuity")
        units = {(item["independent_unit"]["kind"], item["independent_unit"]["id"],
                  item["independent_unit"]["parent_id"]) for item in members}
        artifacts = {item["source"]["artifact_id"] for item in members}
        if (len(units) != 1 or next(iter(units))[0] == "not_reported"
                or next(iter(units))[1] is None or len(artifacts) != 1):
            raise InputError("Demonstrated continuity needs the same reported unit and source artifact on both sides")
        left_records = [records[item] for item in left]
        right_records = [records[item] for item in right]
        model_systems = {(item["model_system"]["kind"], item["model_system"]["label"])
                         for item in members}
        if len(model_systems) != 1:
            raise InputError("Demonstrated continuity needs the same reported model system on both sides")
        intervals = [item["developmental_interval"] for item in left_records + right_records]
        if (len({item["time_unit"] for item in intervals}) != 1
                or any(not isinstance(item.get("start"), (int, float))
                       or isinstance(item.get("start"), bool)
                       or not isinstance(item.get("end"), (int, float))
                       or isinstance(item.get("end"), bool) for item in intervals)):
            raise InputError("Demonstrated continuity needs comparable numeric intervals in one reported time unit")
        if max(item["end"] for item in (records[key]["developmental_interval"] for key in left)) > min(
                item["start"] for item in (records[key]["developmental_interval"] for key in right)):
            raise InputError("Demonstrated transitions must be time ordered without overlapping reported intervals")
    return transition


def _validate_measurement_pair(value, records, artifacts):
    required = {"pair_id", "pair_type", "linkage_basis", "source_artifact_id", "members", "source_locator", "note"}
    pair = _object(value, required, set(), "measurement pair")
    pair_id = _text(pair["pair_id"], "measurement pair pair_id", 96)
    if not RECORD_ID.fullmatch(pair_id):
        raise InputError("measurement pair pair_id has an invalid format")
    _enum(pair["pair_type"], MEASUREMENT_PAIR_TYPES, "measurement pair type")
    _enum(pair["linkage_basis"], MEASUREMENT_PAIR_LINKAGE_BASES, "measurement pair linkage basis")
    artifact_id = _text(pair["source_artifact_id"], "measurement pair source_artifact_id", 96)
    if artifact_id not in artifacts:
        raise InputError("measurement pair references an unknown source artifact")
    _text(pair["source_locator"], "measurement pair source_locator", 1000)
    _text(pair["note"], "measurement pair note", 1000)
    members = pair["members"]
    if not isinstance(members, list) or not 2 <= len(members) <= 20:
        raise InputError("measurement pair members must contain 2–20 observation records")
    record_ids = set()
    member_records = []
    for member in members:
        _object(member, {"record_id", "role"}, set(), "measurement pair member")
        record_id = _text(member["record_id"], "measurement pair member record_id", 96)
        if not RECORD_ID.fullmatch(record_id) or record_id in record_ids:
            raise InputError("measurement pair members need distinct valid record IDs")
        if record_id not in records:
            raise InputError("measurement pair references an unknown observation record")
        _text(member["role"], "measurement pair member role", 120)
        if records[record_id]["source"]["artifact_id"] != artifact_id:
            raise InputError("measurement pair members must use its declared source artifact")
        record_ids.add(record_id)
        member_records.append(records[record_id])
    if pair["pair_type"] == "same_unit_same_time":
        units = {(item["independent_unit"]["kind"], item["independent_unit"]["id"],
                  item["independent_unit"]["parent_id"]) for item in member_records}
        times = [item["observation"]["measurement_time"] for item in member_records]
        time_units = {item["observation"]["measurement_time_unit"] for item in member_records}
        if len(units) != 1 or next(iter(units))[0] == "not_reported" or next(iter(units))[1] is None:
            raise InputError("A same_unit_same_time pair needs one shared, reported unit identifier")
        if (any(time is None for time in times)
                or len({type(time) for time in times}) != 1
                or any(time != times[0] for time in times[1:])
                or len(time_units) != 1 or not next(iter(time_units))):
            raise InputError("A same_unit_same_time pair needs the exact shared reported measurement time and unit")
    return pair


def _validate_coverage_declaration(value):
    declaration = _object(value,
        {"category", "scope", "reported_label", "quantity_kind", "value", "value_status", "source_locator"},
        {"note"}, "cohort coverage declaration")
    _enum(declaration["category"], COVERAGE_CATEGORIES, "cohort disposition category")
    _enum(declaration["scope"], {"within_denominator", "outside_denominator", "unresolved"},
          "cohort declaration denominator scope")
    _text(declaration["reported_label"], "cohort declaration reported_label", 500)
    quantity_kind = _enum(declaration["quantity_kind"], {"count", "percentage", "other"},
                          "cohort declaration quantity kind")
    value_status = _enum(declaration["value_status"], COVERAGE_VALUE_STATUSES,
                         "cohort declaration value status")
    reported_value = declaration["value"]
    if value_status == "reported":
        if quantity_kind == "count":
            if (type(reported_value) is not int or reported_value < 0 or reported_value > 1_000_000_000):
                raise InputError("A reported cohort count must be an integer from 0 to 1,000,000,000")
        elif not isinstance(reported_value, str) or len(reported_value) > 120 or not reported_value.strip():
            raise InputError("A reported percentage or other cohort value must preserve its source text")
    elif reported_value is not None:
        raise InputError("An unreported or ambiguous cohort value must be null")
    _text(declaration["source_locator"], "cohort declaration source_locator", 1000)
    _text(declaration.setdefault("note", ""), "cohort declaration note", 1000, empty=True)
    return declaration


def _validate_coverage(value, artifacts):
    required = {"coverage_id", "source_artifact_id", "reported_group_label", "group_label_status",
                "counted_entity_kind", "counted_entity_label", "endpoint_label", "population_frame",
                "measurement_window", "selection_definition", "selection_definition_source_locator",
                "denominator", "declarations",
                "selection_statements", "cohort_window_status", "disposition_completeness",
                "categories_mutually_exclusive", "categories_exhaustive"}
    coverage = _object(value, required, set(), "cohort coverage record")
    coverage_id = _text(coverage["coverage_id"], "coverage_id", 96)
    if not RECORD_ID.fullmatch(coverage_id):
        raise InputError("coverage_id has an invalid format")
    source_artifact_id = _text(coverage["source_artifact_id"], "coverage source_artifact_id", 96)
    if source_artifact_id not in artifacts:
        raise InputError("Cohort coverage references an unknown source artifact")
    group_label = coverage["reported_group_label"]
    if group_label is not None:
        _text(group_label, "reported_group_label", 300)
    label_status = _enum(coverage["group_label_status"], {"reported", "not_reported", "ambiguous"},
                         "group-label status")
    if ((label_status == "reported" and group_label is None)
            or (label_status == "not_reported" and group_label is not None)):
        raise InputError("A reported group label must be present, and an unreported label must be null")
    _enum(coverage["counted_entity_kind"], COUNTED_ENTITIES, "counted entity")
    _string_or_null(coverage["counted_entity_label"], "counted_entity_label", 300)
    for field, maximum in (("endpoint_label", 500), ("population_frame", 500),
                           ("measurement_window", 300), ("selection_definition", 2000),
                           ("selection_definition_source_locator", 1000)):
        _text(coverage[field], f"cohort coverage {field}", maximum)
    denominator = _object(coverage["denominator"],
        {"value", "value_status", "reported_label", "source_locator"}, set(), "cohort denominator")
    denominator_status = _enum(denominator["value_status"], COVERAGE_VALUE_STATUSES,
                               "denominator value status")
    denominator_value = denominator["value"]
    if denominator_status == "reported":
        if type(denominator_value) is not int or denominator_value < 0 or denominator_value > 1_000_000_000:
            raise InputError("A reported cohort denominator must be an integer from 0 to 1,000,000,000")
    elif denominator_value is not None:
        raise InputError("An unreported or ambiguous denominator must be null")
    _text(denominator["reported_label"], "cohort denominator reported_label", 500)
    _text(denominator["source_locator"], "cohort denominator source_locator", 1000)
    declarations = coverage["declarations"]
    if not isinstance(declarations, list) or not 1 <= len(declarations) <= 100:
        raise InputError("cohort declarations must contain 1–100 source-linked entries")
    for item in declarations:
        _validate_coverage_declaration(item)
    statements = coverage["selection_statements"]
    if not isinstance(statements, list) or len(statements) > 20:
        raise InputError("selection_statements must contain at most 20 source-linked statements")
    for item in statements:
        statement = _object(item, {"text", "source_locator"}, set(), "cohort selection statement")
        _text(statement["text"], "cohort selection statement text", 2000)
        _text(statement["source_locator"], "cohort selection statement source_locator", 1000)
    _enum(coverage["cohort_window_status"], COHORT_WINDOW_STATUSES, "cohort/window linkage status")
    _enum(coverage["disposition_completeness"], DISPOSITION_COMPLETENESS,
          "disposition completeness")
    _enum(coverage["categories_mutually_exclusive"], SOURCE_DECLARATION_STATES,
          "mutual-exclusivity declaration")
    _enum(coverage["categories_exhaustive"], SOURCE_DECLARATION_STATES,
          "exhaustiveness declaration")
    return coverage


def _coverage_closure(coverage):
    """Check source-declared aggregate arithmetic only when the source defines the accounting frame."""
    eligible = (
        coverage["denominator"]["value_status"] == "reported"
        and coverage["cohort_window_status"] == "source_reported_common"
        and coverage["disposition_completeness"] == "complete"
        and coverage["categories_mutually_exclusive"] == "source_reported_yes"
        and coverage["categories_exhaustive"] == "source_reported_yes"
    )
    all_counts = [item for item in coverage["declarations"] if item["quantity_kind"] == "count"]
    if any(item["scope"] == "unresolved" for item in all_counts):
        return {"coverage_id": coverage["coverage_id"], "status": "not_assessed",
                "disposition_sum": None, "denominator": coverage["denominator"]["value"],
                "difference": None, "reason": "Denominator membership of one or more counts is unresolved."}
    counted = [item for item in all_counts if item["scope"] == "within_denominator"]
    if any(item["category"] not in DISPOSITION_COUNT_CATEGORIES for item in counted):
        return {"coverage_id": coverage["coverage_id"], "status": "not_assessed",
                "disposition_sum": None, "denominator": coverage["denominator"]["value"],
                "difference": None, "reason": "Endpoint measurements or population counts are not disposition categories."}
    if not eligible:
        return {"coverage_id": coverage["coverage_id"], "status": "not_assessed",
                "disposition_sum": None, "denominator": coverage["denominator"]["value"],
                "difference": None,
                "reason": "A common source-reported cohort/window and complete, mutually exclusive, exhaustive dispositions were not all declared."}
    if not counted or any(item["value_status"] != "reported" for item in counted):
        return {"coverage_id": coverage["coverage_id"], "status": "not_assessed",
                "disposition_sum": None, "denominator": coverage["denominator"]["value"],
                "difference": None, "reason": "One or more source disposition counts were not reported."}
    categories = [item["category"] for item in counted]
    if len(categories) != len(set(categories)):
        return {"coverage_id": coverage["coverage_id"], "status": "not_assessed",
                "disposition_sum": None, "denominator": coverage["denominator"]["value"],
                "difference": None, "reason": "Disposition categories are not distinct, so they cannot be summed as a partition."}
    total = sum(item["value"] for item in counted)
    denominator = coverage["denominator"]["value"]
    return {"coverage_id": coverage["coverage_id"],
            "status": "matches" if total == denominator else "mismatch",
            "disposition_sum": total, "denominator": denominator,
            "difference": total - denominator,
            "reason": "Source-declared aggregate arithmetic only; no specimen identity or biological outcome is inferred."}


def _unit_membership_groups(records):
    """Index declared direct units and pool members without quadratic pair expansion."""
    groups = defaultdict(list)
    for record in records:
        unit = record["independent_unit"]
        keys = {(member["kind"], member["id"], member.get("parent_id"))
                for member in unit.get("members", [])}
        if unit["id"] is not None:
            keys.add((unit["kind"], unit["id"], unit["parent_id"]))
        for key in keys:
            context = (record["source"]["artifact_id"], record["species"], record["stage_track"],
                       record["assay"]["name"], record["assay"]["endpoint"])
            groups[context + key].append(record)
    return groups


def _reject_independent_membership_conflicts(records):
    for items in _unit_membership_groups(records).values():
        if len(items) > 1 and any(item["observation"]["replicate_role"] == "independent" for item in items):
            raise InputError("Repeated rows or overlapping pool members cannot all be asserted as independent; mark repeated/technical/summary roles")


def validate_dataset(dataset):
    required = {"schema_version", "dataset_id", "title", "source_revision", "artifacts", "observations"}
    dataset = _object(dataset, required, {"transitions", "limitations", "cohort_coverage", "measurement_pairs"}, "observation dataset")
    if type(dataset["schema_version"]) is not int or dataset["schema_version"] != 1:
        raise InputError("Dataset schema_version must be 1")
    dataset_id = _text(dataset["dataset_id"], "dataset_id", 96)
    if not RECORD_ID.fullmatch(dataset_id):
        raise InputError("dataset_id has an invalid format")
    _text(dataset["title"], "dataset title", 300)
    revision = _validate_source_revision(dataset["source_revision"])
    artifacts_raw = dataset["artifacts"]
    if not isinstance(artifacts_raw, list) or not 1 <= len(artifacts_raw) <= 100:
        raise InputError("artifacts must contain 1–100 source files")
    artifacts = {}
    for value in artifacts_raw:
        item = _validate_artifact(value, artifacts)
        artifacts[item["artifact_id"]] = item
    observations = dataset["observations"]
    if not isinstance(observations, list) or not 1 <= len(observations) <= 5000:
        raise InputError("observations must contain 1–5000 source-linked records")
    records = {}
    for item in observations:
        record = _validate_record(item, artifacts)
        _check_interval_scope(record, artifacts)
        if record["record_id"] in records:
            raise InputError(f"Duplicate observation record ID: {record['record_id']}")
        records[record["record_id"]] = record
    _reject_independent_membership_conflicts(observations)
    transitions = dataset.setdefault("transitions", [])
    if not isinstance(transitions, list) or len(transitions) > 500:
        raise InputError("transitions must contain at most 500 records")
    transition_ids = set()
    for item in transitions:
        transition = _validate_transition(item, records)
        if transition["transition_id"] in transition_ids:
            raise InputError("Transition IDs must be unique")
        transition_ids.add(transition["transition_id"])
    measurement_pairs = dataset.setdefault("measurement_pairs", [])
    if not isinstance(measurement_pairs, list) or len(measurement_pairs) > 5000:
        raise InputError("measurement_pairs must contain at most 5000 records")
    measurement_pair_ids = set()
    for item in measurement_pairs:
        pair = _validate_measurement_pair(item, records, artifacts)
        if pair["pair_id"] in measurement_pair_ids:
            raise InputError("Measurement pair IDs must be unique")
        measurement_pair_ids.add(pair["pair_id"])
    coverage_records = dataset.setdefault("cohort_coverage", [])
    if not isinstance(coverage_records, list) or len(coverage_records) > 500:
        raise InputError("cohort_coverage must contain at most 500 aggregate source-linked records")
    coverage_ids = set()
    for item in coverage_records:
        coverage = _validate_coverage(item, artifacts)
        if coverage["coverage_id"] in coverage_ids:
            raise InputError("Cohort coverage IDs must be unique")
        coverage_ids.add(coverage["coverage_id"])
    limitations = dataset.setdefault("limitations", [])
    if (not isinstance(limitations, list) or len(limitations) > 50
            or not all(isinstance(item, str) and 8 <= len(item) <= 1000 for item in limitations)):
        raise InputError("Dataset limitations must be a list of at most 50 explanatory strings")
    return dataset


def verify_source_files(artifacts, source_root):
    """Compare user-declared source hashes with bounded local files; never fetch or copy them."""
    if source_root is None:
        return {
            "status": "not_requested", "source_root_configured": False,
            "n_artifacts": len(artifacts), "n_paths_declared": sum(item.get("local_path") is not None for item in artifacts),
            "n_verified": 0, "n_mismatched": 0, "n_not_checked": len(artifacts), "bytes_hashed": 0,
            "files": [{"artifact_id": item["artifact_id"], "relative_path": item.get("local_path") or "",
                       "declared_sha256": item["sha256"] or "", "observed_sha256": "",
                       "verification_status": "not_requested", "bytes_hashed": 0,
                       "note": "No --source-root was supplied."} for item in artifacts],
        }
    root = Path(source_root)
    if root.is_symlink() or not root.is_dir():
        raise InputError("--source-root must be an existing directory and cannot be a symlink")
    try:
        root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InputError("--source-root could not be resolved") from exc

    rows = []
    bytes_hashed = 0
    for item in artifacts:
        relative = item.get("local_path")
        base_row = {"artifact_id": item["artifact_id"], "relative_path": relative or "",
                    "declared_sha256": item["sha256"] or "", "observed_sha256": "",
                    "verification_status": "not_provided", "bytes_hashed": 0, "note": ""}
        if relative is None:
            base_row["note"] = "No local_path was declared for this artifact."
            rows.append(base_row)
            continue
        if item["sha256"] is None:
            base_row["verification_status"] = "hash_not_declared"
            base_row["note"] = "A local file is mapped but no declared SHA-256 is available to compare."
            rows.append(base_row)
            continue
        candidate = root.joinpath(*relative.split("/"))
        current = root
        has_symlink = False
        for part in relative.split("/"):
            current = current / part
            if current.is_symlink():
                has_symlink = True
                break
        if has_symlink:
            base_row["verification_status"] = "symlink_rejected"
            base_row["note"] = "Symlink source paths are not followed."
            rows.append(base_row)
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            if not resolved.is_file():
                raise OSError("not a regular file")
            before = resolved.stat()
            if before.st_size > MAX_SOURCE_FILE_BYTES:
                base_row["verification_status"] = "file_limit_exceeded"
                base_row["note"] = f"File exceeds the {MAX_SOURCE_FILE_BYTES} byte per-file limit."
                rows.append(base_row)
                continue
            if bytes_hashed + before.st_size > MAX_SOURCE_TOTAL_BYTES:
                base_row["verification_status"] = "total_limit_exceeded"
                base_row["note"] = f"Hashing would exceed the {MAX_SOURCE_TOTAL_BYTES} byte total limit."
                rows.append(base_row)
                continue
            digest = hashlib.sha256()
            read_count = 0
            with resolved.open("rb") as stream:
                opened_before = os.fstat(stream.fileno())
                while read_count < before.st_size:
                    block = stream.read(min(1024 * 1024, before.st_size - read_count))
                    if not block:
                        break
                    digest.update(block)
                    read_count += len(block)
                opened_after = os.fstat(stream.fileno())
            after = resolved.stat()
            base_row["bytes_hashed"] = read_count
            bytes_hashed += read_count
            if (read_count != before.st_size or opened_before.st_size != opened_after.st_size
                    or opened_before.st_mtime_ns != opened_after.st_mtime_ns
                    or opened_before.st_dev != opened_after.st_dev or opened_before.st_ino != opened_after.st_ino
                    or before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns
                    or before.st_dev != after.st_dev or before.st_ino != after.st_ino):
                base_row["verification_status"] = "changed_during_hash"
                base_row["note"] = "File metadata or size changed while it was being hashed."
                rows.append(base_row)
                continue
            observed = digest.hexdigest()
            base_row["observed_sha256"] = observed
            base_row["verification_status"] = "verified" if observed == item["sha256"] else "mismatch"
            base_row["note"] = ("Declared hash matches the bytes read." if observed == item["sha256"]
                                else "Declared hash does not match the bytes read.")
        except (OSError, ValueError, RuntimeError):
            base_row["verification_status"] = "unavailable"
            base_row["note"] = "The relative source file was missing, unreadable, or resolved outside --source-root."
        rows.append(base_row)

    verified = sum(row["verification_status"] == "verified" for row in rows)
    mismatched = sum(row["verification_status"] == "mismatch" for row in rows)
    not_checked = len(rows) - verified - mismatched
    status = "mismatch" if mismatched else "complete" if verified == len(artifacts) else "partial"
    return {"status": status, "source_root_configured": True, "n_artifacts": len(artifacts),
            "n_paths_declared": sum(item.get("local_path") is not None for item in artifacts),
            "n_verified": verified, "n_mismatched": mismatched, "n_not_checked": not_checked,
            "bytes_hashed": bytes_hashed, "files": rows}


def observation_report(dataset_path: Path, output: Path, source_root: Path | None = None) -> dict:
    dataset, raw = read_json(dataset_path)
    validate_dataset(dataset)
    revision = dataset["source_revision"]
    source_verification = verify_source_files(dataset["artifacts"], source_root)
    artifacts = {item["artifact_id"]: item for item in dataset["artifacts"]}
    records = dataset["observations"]
    context_rows = [{"record_id": item["record_id"], "source_artifact_id": item["source"]["artifact_id"],
                     **item["assay"]["functional_context"]}
                    for item in records if "functional_context" in item["assay"]]
    interval_checks = [{"record_id": item["record_id"],
                        "stage_source_artifact_id": item["developmental_interval"]["stage_source_artifact_id"],
                        "status": _check_interval_scope(item, artifacts)} for item in records]
    n_contained = sum(item["status"] == "contained_in_declared_scope" for item in interval_checks)
    n_partially_checked = sum(item["status"] == "partially_checked" for item in interval_checks)
    coverage_records = dataset["cohort_coverage"]
    measurement_pairs = dataset["measurement_pairs"]
    coverage_checks = [_coverage_closure(item) for item in coverage_records]
    coverage_declaration_rows = [
        {"coverage_id": coverage["coverage_id"], "source_artifact_id": coverage["source_artifact_id"],
         "category": declaration["category"], "scope": declaration["scope"],
         "reported_label": declaration["reported_label"],
         "quantity_kind": declaration["quantity_kind"], "value": declaration["value"],
         "value_status": declaration["value_status"], "source_locator": declaration["source_locator"],
         "note": declaration.get("note", "")}
        for coverage in coverage_records for declaration in coverage["declarations"]]
    coverage_rows = [
        {"coverage_id": item["coverage_id"], "source_artifact_id": item["source_artifact_id"],
         "reported_group_label": item["reported_group_label"] or "",
         "group_label_status": item["group_label_status"],
         "counted_entity_kind": item["counted_entity_kind"],
         "counted_entity_label": item["counted_entity_label"] or "",
         "endpoint_label": item["endpoint_label"], "population_frame": item["population_frame"],
         "measurement_window": item["measurement_window"],
         "selection_definition": item["selection_definition"],
         "selection_definition_source_locator": item["selection_definition_source_locator"],
         "denominator_value": item["denominator"]["value"],
         "denominator_value_status": item["denominator"]["value_status"],
         "denominator_label": item["denominator"]["reported_label"],
         "denominator_source_locator": item["denominator"]["source_locator"],
         "cohort_window_status": item["cohort_window_status"],
         "disposition_completeness": item["disposition_completeness"],
         "categories_mutually_exclusive": item["categories_mutually_exclusive"],
         "categories_exhaustive": item["categories_exhaustive"],
         "selection_statements": " | ".join(
             f"{statement['text']} [{statement['source_locator']}]" for statement in item["selection_statements"])}
        for item in coverage_records]
    group_fields = ("species", "stage_track", "developmental_interval", "model_system", "assay", "source")
    groups = defaultdict(list)
    for record in records:
        key = tuple(json_bytes(record[field]).decode("utf-8") for field in group_fields) + (
            json_bytes(record["observation"].get("measurement_conditions", [])).decode("utf-8"),)
        groups[key].append(record)
    membership_rows = []
    for key, items in sorted(_unit_membership_groups(records).items(),
                             key=lambda entry: tuple("" if item is None else item for item in entry[0])):
        if len(items) > 1:
            membership_rows.append({"source_artifact_id": key[0], "species": key[1],
                "stage_track": key[2], "assay": key[3], "endpoint": key[4],
                "unit_kind": key[5], "unit_id": key[6], "parent_id": key[7],
                "n_records": len(items), "record_ids": ";".join(sorted(item["record_id"] for item in items)),
                "interpretation": "Shared declared identifier within this source/assay scope; neither independent biological n nor a verified identity."})

    group_rows = []
    for index, (_, members) in enumerate(sorted(groups.items()), 1):
        first = members[0]
        group_rows.append({
            "group_id": f"g{index:04d}", "species": first["species"], "stage_track": first["stage_track"],
            "interval_label": first["developmental_interval"]["label"],
            "interval_start": first["developmental_interval"].get("start"),
            "interval_end": first["developmental_interval"].get("end"),
            "interval_unit": first["developmental_interval"]["time_unit"],
            "model_system": first["model_system"]["label"], "assay": first["assay"]["name"],
            "endpoint": first["assay"]["endpoint"], "unit": first["assay"]["unit"],
            "measurement_role": first["assay"]["measurement_role"],
            "functional_evidence_class": first["assay"].get("functional_evidence_class", ""),
            "source_artifact_id": first["source"]["artifact_id"],
            "measurement_conditions_json": json.dumps(
                first["observation"].get("measurement_conditions", []),
                sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            "n_records": len(members),
            "n_distinct_reported_unit_keys": len({(item["independent_unit"]["kind"], item["independent_unit"]["id"],
                                                  item["independent_unit"]["parent_id"])
                                                 for item in members if item["independent_unit"]["id"] is not None}),
            "record_ids": ";".join(sorted(item["record_id"] for item in members)),
            "grouping_note": "Exact recorded species, stage, interval, assay, unit, source and measurement conditions match only; no unit conversion or pooling.",
        })

    source_status = dataset["source_revision"]["review_status"]
    source_kind = dataset["source_revision"]["source_kind"]
    warnings = []
    source_resolutions = [
        {"artifact_id": item["artifact_id"], **item["source_resolution"]}
        for item in dataset["artifacts"] if "source_resolution" in item]
    unconfirmed_rights = [item for item in source_resolutions if item["reuse_status"] == "not_confirmed"]
    if unconfirmed_rights:
        warnings.append("Reuse rights are unconfirmed for one or more artifacts; public access and repository status do not establish a reuse license.")
    if coverage_records:
        warnings.append("Aggregate cohort declarations retain source-reported populations and denominators; they do not create individual specimen IDs or developmental continuity. Equal group labels are not joined.")
    if any(item["status"] == "not_assessed" for item in coverage_checks):
        warnings.append("Some aggregate count-closure checks are unassessed because the source did not establish a common cohort/window and complete, mutually exclusive, exhaustive dispositions.")
    if any(item["status"] == "mismatch" for item in coverage_checks):
        warnings.append("At least one source-declared aggregate disposition sum differs from its denominator; the discrepancy is retained without repair or biological interpretation.")
    if measurement_pairs:
        warnings.append("Measurement-pair rows preserve source-explicit or curator-linked record relationships and member labels; the declared link is not independently verified and does not establish exchange sufficiency or biological continuity.")
    if context_rows:
        warnings.append("Functional contexts are source-linked declarations, not verified mechanisms, fluxes or paired specimen identities. Compartment abundance does not establish passage, secretion or embryonic use.")
    if source_kind == "preprint":
        warnings.append("Source is declared a preprint; local review does not establish journal peer review or validate its findings.")
    if n_contained < len(records):
        warnings.append("Some developmental intervals have missing source or record bounds; known numeric constraints were checked where available, but full containment was not assessed.")
    if source_status == "candidate":
        warnings.append("Source revision is a candidate awaiting local human review.")
    if source_status == "locally_reviewed_included":
        warnings.append("Local review is user-recorded metadata; reviewer identity and decision were not authenticated by this tool.")
    if source_status == "locally_reviewed_excluded":
        warnings.append("Source revision is locally marked excluded; records remain preserved for audit and are not promoted.")
    if any(item["species"] == "unspecified" for item in records):
        warnings.append("Some records have unspecified species/model identity; they cannot support species-specific comparisons.")
    if any(item["stage_track"] == "unspecified" for item in records):
        warnings.append("Some records have unspecified developmental stage; they cannot support stage-specific comparisons.")
    if any(item["independent_unit"]["kind"] == "not_reported" or item["independent_unit"]["id"] is None for item in records):
        warnings.append("Some independent-unit identities are not reported; record counts are not verified biological n.")
    if any(item["observation"]["replicate_role"] in {"summary_only", "not_reported"} for item in records):
        warnings.append("Some replicate roles are summary-only or not reported; no independent-unit inference is made.")
    pool_records = [item for item in records if item["independent_unit"]["kind"] == "sample_pool"]
    if pool_records:
        warnings.append("Sample pools preserve reported collection identities and declared members only. Their names/member counts are not verified biological n; individual developmental continuity is not established.")
    if membership_rows:
        warnings.append("Some records share declared source-unit identifiers, directly or through pool membership. Shared-membership details are retained without counting records as independent units.")
    if any(item["observation"]["comparator_id"] is None for item in records):
        warnings.append("Some comparator IDs are absent; comparative effect estimation is not implied.")
    if any(artifacts[item["artifact_id"]]["sha256"] is None for item in dataset["artifacts"]):
        warnings.append("At least one source file has no SHA-256; byte-level source identity is incomplete.")
    if source_verification["status"] == "not_requested":
        warnings.append("Local source-file bytes were not checked; declared hashes remain unverified metadata.")
    elif source_verification["status"] == "mismatch":
        warnings.append("At least one local source-file hash does not match its declared SHA-256.")
    elif source_verification["status"] == "partial":
        warnings.append("Some source files were not checked because their local path, declared hash, access, or size limit was unavailable.")
    not_reported_edges = sum(item["continuity_status"] == "not_reported" for item in dataset["transitions"])
    source_qualification_count = sum(len(item["observation"].get("source_qualifications", []))
                                     for item in records)
    records_with_source_qualifications = sum(bool(item["observation"].get("source_qualifications"))
                                             for item in records)
    summary_statistic_records = [item for item in records
                                 if item["observation"].get("summary_statistic") is not None]
    verification_summary = {key: value for key, value in source_verification.items() if key != "files"}
    report = {
        "schema_version": 1, "report_kind": "developmental_observation_intake",
        "dataset_id": dataset["dataset_id"], "title": dataset["title"],
        "source_revision_id": dataset["source_revision"]["revision_id"],
        "source_kind": source_kind,
        "source_review_status": source_status, "n_source_artifacts": len(artifacts),
        "source_resolution": {"n_assessed": len(source_resolutions),
            "n_reuse_unconfirmed": len(unconfirmed_rights), "artifacts": source_resolutions,
            "interpretation": "dated curation separates version identity, access, OA-subset membership and reuse rights; it is not authenticated by this tool"},
        "n_observation_records": len(records), "n_exact_comparison_groups": len(group_rows),
        "n_cohort_coverage_records": len(coverage_records),
        "n_cohort_coverage_declarations": len(coverage_declaration_rows),
        "cohort_coverage_checks": coverage_checks,
        "source_qualifications": {"n_records_with_declarations": records_with_source_qualifications,
                                   "n_declarations": source_qualification_count,
                                   "interpretation": "source-linked declarations; not scientific validation"},
        "measurement_conditions": {"n_records_with_conditions": sum(
            bool(item["observation"].get("measurement_conditions")) for item in records),
            "n_condition_declarations": sum(len(item["observation"].get("measurement_conditions", []))
                                             for item in records),
            "interpretation": "source-linked test context; conditions do not establish replicates or measurement pairs"},
        "summary_statistics": {"n_records": len(summary_statistic_records),
                               "n_median_iqr": sum(item["observation"]["summary_statistic"]["kind"] == "median_iqr"
                                                   for item in summary_statistic_records),
                               "n_mean_sd": sum(item["observation"]["summary_statistic"]["kind"] == "mean_sd"
                                                for item in summary_statistic_records),
                               "n_reported_plus_minus": sum(item["observation"]["summary_statistic"]["kind"] == "reported_plus_minus"
                                                             for item in summary_statistic_records),
                               "interpretation": "typed source-reported mean ± explicitly named SD, source-neutral estimate ± reported quantity, or median [IQR]; these are not individual observations or independent replicates"},
        "n_transitions": len(dataset["transitions"]), "n_continuity_not_reported": not_reported_edges,
        "measurement_pairing": {"n_pairs": len(measurement_pairs),
                                "n_members": sum(len(item["members"]) for item in measurement_pairs),
                                "interpretation": "source-explicit or curator-linked record relationships; not independently verified"},
        "biological_assay_performed": False,
        "analysis_eligibility": "requires source-specific human review and a frozen analysis plan",
        "source_file_verification": verification_summary,
        "functional_context": {"n_declared": len(context_rows),
                               "n_not_declared": len(records) - len(context_rows),
                               "scientific_transcription": "not_verified"},
        "functional_evidence_classes": {
            "counts": {label: sum(item["assay"].get("functional_evidence_class") == label
                                   for item in records)
                       for label in sorted(FUNCTIONAL_EVIDENCE_CLASSES)},
            "n_not_declared": sum("functional_evidence_class" not in item["assay"]
                                  for item in records),
            "interpretation": "Curated endpoint relation to a functional question; not proof of sufficiency, mechanism, or health. Omitted values are not inferred.",
        },
        "source_interval_containment": {"n_contained": n_contained,
                                        "n_partially_checked": n_partially_checked,
                                        "n_not_assessed": len(records) - n_contained,
                                        "scientific_transcription": "not_verified"},
        "declared_unit_membership": {"n_pool_records": len(pool_records),
            "n_pools_without_declared_members": sum(not item["independent_unit"]["members"] for item in pool_records),
            "n_shared_identifier_keys": len(membership_rows),
            "assessment": "declared source/assay identifiers only; membership completeness and biological identity not verified"},
        "groups": group_rows[:100], "n_groups_in_report": min(len(group_rows), 100),
        "groups_truncated": len(group_rows) > 100, "warnings": warnings,
        "limits": [
            "This validates record structure and source bindings; it does not verify scientific transcription, source rights, calibration, or measurement validity.",
            "Counts of distinct identifier strings are not verified donors, embryos, organoids, or independent experimental units.",
            "Groups are partitioned by exact reported categories and units; no unit conversion, study concatenation, or summary-statistic pooling is performed.",
            "A locally recorded source review is not authenticated and does not promote a candidate into the evidence ledger.",
            "Declared source SHA-256 values are checked for format and matched between records and artifact metadata. Optional local byte checks hash only the relative files named under --source-root; source URIs are never fetched.",
            "Source files are read-only inputs and are not copied into the bundle. Hash verification records bytes observed at that time; rerun if files change.",
            "Transition status is a source-recorded assertion. Demonstrated continuity requires matching recorded unit identifiers within one source artifact.",
            "Sample-pool members are source-recorded identifiers, not inferred specimens. Overlap with another pool or a direct unit prevents independent-replicate assertions in the same source/species/stage/assay/endpoint scope. Pool records cannot establish individual developmental continuity; missing members do not prove disjointness.",
            "Source interval containment compares curated metadata in exact recorded units. It does not verify a source transcription, infer numeric bounds from prose, or establish biological continuity.",
            "Optional functional contexts retain observed compartment/material, reported process, quantity basis, assessment context and source locator. Absence is not filled from endpoint prose; a declaration does not identify a mechanism or establish functional sufficiency.",
            "Aggregate cohort coverage stores source-level counts and selection statements separately from individual observation records. Matching group labels do not authenticate cohort identity or continuity.",
            "Aggregate count closure is assessed only when the source metadata explicitly declares one common cohort/window, complete dispositions, and mutually exclusive and exhaustive categories. Other accounting remains unassessed; eligible arithmetic does not establish biological identity.",
            "Optional source qualifications are per-observation declarations tied to a source artifact and locator. Their status codes retain source-specific criteria; they are not independently verified by intake validation.",
        ],
    }
    lines = ["# Developmental observation intake", "",
             f"Dataset: {dataset['title']} (`{dataset['dataset_id']}`)",
             f"Source revision: `{dataset['source_revision']['revision_id']}` · {source_status}",
             f"Declared source class: {source_kind}",
             f"Records: {len(records)} · exact comparison groups: {len(group_rows)} · transitions: {len(dataset['transitions'])}", "",
             "No biological assay was performed by this command. Source URIs are never fetched. Optional local byte checks use only files beneath --source-root and do not copy their contents into this bundle.",
             "Analysis eligibility still requires source-specific human review and a frozen analysis plan.", "",
             "## Source qualifications", "",
             f"Declared on {records_with_source_qualifications}/{len(records)} records ({source_qualification_count} declarations). They preserve source-reported criteria and locators; they do not establish scientific validity or analysis eligibility.", "",
             f"Measurement conditions: {report['measurement_conditions']['n_condition_declarations']} declarations on {report['measurement_conditions']['n_records_with_conditions']} records. They preserve source-linked operating context and do not establish replicates or pairs.", "",
             "## Typed distribution summaries", "",
             f"Records with typed summary statistics: {len(summary_statistic_records)} (mean ± SD: {report['summary_statistics']['n_mean_sd']}; reported value ± quantity: {report['summary_statistics']['n_reported_plus_minus']}; median [IQR]: {report['summary_statistics']['n_median_iqr']}). The quantity type is preserved as not reported when the source does not define it; these remain group summaries and do not create participant-level rows or independent replicates.", "",
             "## Declared measurement pairs", "",
             f"Pairs: {len(measurement_pairs)} · linked record memberships: {sum(len(item['members']) for item in measurement_pairs)}. See measurement_pairs.csv. Pair links require a source locator and explicit source or curator basis; they do not establish unreported identity, flux, or sufficiency.", "",
             "## Aggregate cohort coverage", "",
             f"Coverage records: {len(coverage_records)} · source-linked declarations: {len(coverage_declaration_rows)} · closure checks unassessed: {sum(item['status'] == 'not_assessed' for item in coverage_checks)} · mismatches: {sum(item['status'] == 'mismatch' for item in coverage_checks)}.",
             "See cohort_coverage.csv, cohort_dispositions.csv and cohort_coverage_checks.csv. Aggregate counts stay separate from specimen records; matching labels do not create identities or continuity. A count check runs only when the source explicitly defines a common cohort/window and a complete, mutually exclusive, exhaustive disposition set.", "",
             "## Declared functional contexts", "",
             f"Declared: {len(context_rows)} records; not declared: {len(records) - len(context_rows)}. See functional_contexts.csv. Compartment/material and readout context are curated metadata, not verified mechanisms or specimen pairing.", "",
             "## Functional evidence classification", "",
             f"Classified: {len(records) - report['functional_evidence_classes']['n_not_declared']}/{len(records)} records; not declared: {report['functional_evidence_classes']['n_not_declared']}. See observation_records.csv. Classes distinguish direct process measurements, response proxies, developmental outcomes, and other declarations; they do not establish sufficiency or health.", "",
             "## Declared source interval containment", "",
             f"Contained in declared numeric scope: {n_contained}/{len(records)} records; full containment unassessed: {len(records) - n_contained}, including {n_partially_checked} with known numeric bounds checked. Missing bounds were not inferred. See source_interval_checks.csv and source_scopes.csv. Scientific transcription was not verified.", "",
             "## Local source-file byte verification", "",
             f"Status: {source_verification['status']} · verified: {source_verification['n_verified']}/{source_verification['n_artifacts']} artifacts · bytes hashed: {source_verification['bytes_hashed']}",
             "The receipt covers the submitted dataset JSON and generated outputs, not the external source bytes.", ""]
    for row in source_verification["files"]:
        lines.append(f"- {row['artifact_id']} · {row['relative_path'] or 'no local path'} · {row['verification_status']} · {row['observed_sha256'] or 'no observed hash'}{': ' + row['note'] if row['note'] else ''}")
    lines.extend(["", "## Source review", "",
             f"{dataset['source_revision']['citation']} — [{dataset['source_revision']['source_url']}]({dataset['source_revision']['source_url']})",
             f"Recorded review state: {source_status}. A locally recorded review is not authenticated by this tool.", "",
             "## Source version, access and reuse", "",
             f"Artifacts with a recorded resolution: {len(source_resolutions)}; reuse rights unconfirmed: {len(unconfirmed_rights)}."])
    for resolution in source_resolutions:
        lines.append(f"- {resolution['artifact_id']}: {resolution['version_type']} `{resolution['version_identifier']}`; full text `{resolution['access_status']}`; PMC OA-subset `{resolution['oa_subset_status']}`; reuse `{resolution['reuse_status']}`; checked {resolution['checked_on']}. {resolution['note']} Evidence: {resolution['evidence_locator']}")
    lines.extend(["", "Access status and OA-subset membership are not reuse permission. These fields preserve the inspected route and date; they do not authenticate rights or transcription.", "",
             "## Exact groups", "",
            "Records are grouped only when species, stage, interval, model, endpoint, reported unit, source artifact, and declared measurement conditions match exactly. No conversion or pooling is performed. The conditions are shown in interval_groups.csv.", ""])
    for row in group_rows[:100]:
        lines.append(f"- {row['group_id']}: {row['species']} · {row['stage_track']} · {row['interval_label']} ({row['interval_unit']}) · {row['endpoint']} [{row['unit']}] · {row['n_records']} records · {row['n_distinct_reported_unit_keys']} distinct reported unit keys")
    if len(group_rows) > 100:
        lines.append(f"- Showing 100 of {len(group_rows)} groups; interval_groups.csv contains the full exact-group table.")
    lines.extend(["", "## Warnings", ""] + ([f"- {item}" for item in warnings] or ["- No structural warning was emitted; this does not imply data eligibility."]))
    lines.extend(["", "## Declared pool membership", "",
                  f"Pool records: {len(pool_records)}; pools without declared members: {report['declared_unit_membership']['n_pools_without_declared_members']}; shared source/assay identifier keys: {len(membership_rows)}.",
                  "See unit_members.csv and shared_unit_membership.csv. Identifier and member counts are not verified biological n. Missing members do not establish independence."])
    lines.extend(["", "## Limits", ""] + [f"- {item}" for item in report["limits"]])
    observation_rows = []
    for item in records:
        interval, model, assay, unit, observation, source = (item[key] for key in
            ("developmental_interval", "model_system", "assay", "independent_unit", "observation", "source"))
        observation_rows.append({
            "record_id": item["record_id"], "evidence_status": item["evidence_status"], "species": item["species"],
            "stage_track": item["stage_track"], "interval_label": interval["label"],
            "interval_start": interval.get("start"), "interval_end": interval.get("end"),
            "interval_unit": interval["time_unit"], "model_kind": model["kind"], "model_label": model["label"],
            "assay": assay["name"], "endpoint": assay["endpoint"], "unit": assay["unit"],
            "measurement_role": assay["measurement_role"], "independent_unit_kind": unit["kind"],
            "functional_evidence_class": assay.get("functional_evidence_class", ""),
            "measurement_conditions_json": json.dumps(observation.get("measurement_conditions", []),
                sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            "independent_unit_id": unit["id"], "independent_unit_parent_id": unit["parent_id"],
            "n_declared_pool_members": len(unit["members"]),
            "value": observation["value"], "measurement_time": observation["measurement_time"],
            "measurement_time_unit": observation.get("measurement_time_unit", ""),
            "comparator_id": observation["comparator_id"], "replicate_role": observation["replicate_role"],
            "measurement_uncertainty": observation.get("measurement_uncertainty"),
            "summary_statistic_json": json.dumps(observation.get("summary_statistic"),
                sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            "missingness_reason": observation.get("missingness_reason", ""),
            "source_qualifications_json": json.dumps(observation.get("source_qualifications", []),
                sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            "measurement_conditions_json": json.dumps(observation.get("measurement_conditions", []),
                sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            "source_locator": item.get("source_locator", ""),
            "source_artifact_id": source["artifact_id"], "source_sha256": source["sha256"],
        })
    transition_rows = [{"transition_id": item["transition_id"],
                        "from_record_ids": ";".join(item["from_record_ids"]),
                        "to_record_ids": ";".join(item["to_record_ids"]),
                       "continuity_status": item["continuity_status"], "note": item["note"]}
                       for item in dataset["transitions"]]
    measurement_pair_rows = [{
        "pair_id": item["pair_id"], "pair_type": item["pair_type"],
        "linkage_basis": item["linkage_basis"], "source_artifact_id": item["source_artifact_id"],
        "record_ids": ";".join(member["record_id"] for member in item["members"]),
        "member_roles": json.dumps([member["role"] for member in item["members"]],
                                    ensure_ascii=False, separators=(",", ":")),
        "source_locator": item["source_locator"], "note": item["note"],
    } for item in measurement_pairs]
    source_file_rows = [{key: row[key] for key in
                         ("artifact_id", "relative_path", "declared_sha256", "observed_sha256",
                          "verification_status", "bytes_hashed", "note")}
                        for row in source_verification["files"]]
    files = {
        "input_dataset.json": raw,
        "observation_intake_report.json": json_bytes(report),
        "observation_records.csv": csv_bytes(list(observation_rows[0]), observation_rows),
        "functional_contexts.csv": csv_bytes(["record_id", "source_artifact_id", *FUNCTIONAL_CONTEXT_FIELDS], context_rows),
        "interval_groups.csv": csv_bytes(list(group_rows[0]), group_rows),
        "transitions.csv": csv_bytes(["transition_id", "from_record_ids", "to_record_ids", "continuity_status", "note"], transition_rows),
        "measurement_pairs.csv": csv_bytes(["pair_id", "pair_type", "linkage_basis", "source_artifact_id",
            "record_ids", "member_roles", "source_locator", "note"], measurement_pair_rows),
        "source_files.csv": csv_bytes(["artifact_id", "relative_path", "declared_sha256", "observed_sha256",
                                        "verification_status", "bytes_hashed", "note"], source_file_rows),
        "unit_members.csv": csv_bytes(["record_id", "source_artifact_id", "pool_id", "member_kind", "member_id", "member_parent_id"],
            [{"record_id": item["record_id"], "source_artifact_id": item["source"]["artifact_id"],
              "pool_id": item["independent_unit"]["id"], "member_kind": member["kind"],
              "member_id": member["id"], "member_parent_id": member["parent_id"]}
             for item in pool_records for member in sorted(item["independent_unit"]["members"],
                 key=lambda member: (member["kind"], member["id"], member["parent_id"] or ""))]),
        "shared_unit_membership.csv": csv_bytes(["source_artifact_id", "species", "stage_track", "assay", "endpoint",
            "unit_kind", "unit_id", "parent_id", "n_records", "record_ids", "interpretation"], membership_rows),
        "source_interval_checks.csv": csv_bytes(["record_id", "stage_source_artifact_id", "status"], interval_checks),
        "cohort_coverage.csv": csv_bytes(list(coverage_rows[0]) if coverage_rows else
            ["coverage_id", "source_artifact_id", "reported_group_label", "group_label_status",
             "counted_entity_kind", "counted_entity_label", "endpoint_label", "population_frame",
             "measurement_window", "selection_definition", "selection_definition_source_locator",
             "denominator_value", "denominator_value_status",
             "denominator_label", "denominator_source_locator", "cohort_window_status",
             "disposition_completeness", "categories_mutually_exclusive", "categories_exhaustive",
             "selection_statements"], coverage_rows),
        "cohort_dispositions.csv": csv_bytes(["coverage_id", "source_artifact_id", "category", "scope",
            "reported_label", "quantity_kind", "value", "value_status", "source_locator", "note"],
            coverage_declaration_rows),
        "cohort_coverage_checks.csv": csv_bytes(["coverage_id", "status", "disposition_sum",
            "denominator", "difference", "reason"], coverage_checks),
        "source_scopes.csv": csv_bytes(["artifact_id", "species", "stage_tracks", "time_unit", "start", "end", "source_locator"],
            [{"artifact_id": item["artifact_id"], **item["developmental_scope"],
              "stage_tracks": ";".join(item["developmental_scope"]["stage_tracks"])}
             for item in dataset["artifacts"] if "developmental_scope" in item]),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    return publish_bundle(output, kind="developmental_observation_intake", input_raw=raw, files=files,
                          metadata={"dataset_id": dataset["dataset_id"], "source_revision_id": revision["revision_id"],
                                    "source_review_status": revision["review_status"],
                                    "n_cohort_coverage_records": len(coverage_records),
                                    "source_file_verification_status": source_verification["status"],
                                    "biological_assay_performed": False})
