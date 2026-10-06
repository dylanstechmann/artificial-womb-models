"""Validate source-linked developmental observation records without pooling studies."""
from __future__ import annotations

import hashlib
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
UNIT_KINDS = {"donor", "pregnant_animal", "embryo", "source_kidney", "organoid", "vessel_construct",
              "culture_batch", "other", "not_reported"}
REPLICATE_ROLES = {"independent", "repeated_measure", "technical", "summary_only", "not_reported"}
SOURCE_KINDS = {"peer_reviewed_animal", "peer_reviewed_human_invitro", "regulator_discussion",
                "institution_announcement", "dataset_record", "other"}
REVIEW_STATES = {"candidate", "locally_reviewed_included", "locally_reviewed_excluded"}
HEX64 = re.compile(r"[0-9a-f]{64}")
RECORD_ID = re.compile(r"[a-z0-9][a-z0-9._-]{2,95}")
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
    if not math.isfinite(value):
        raise InputError(f"{label} must be finite")


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
    item = _object(value, required, {"local_path"}, "source artifact")
    artifact_id = _text(item["artifact_id"], "artifact_id", 96)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,95}", artifact_id) or artifact_id in source_ids:
        raise InputError(f"Invalid or duplicate source artifact ID: {artifact_id}")
    _url(item["uri"], "source artifact URI")
    _text(item["license"], "source artifact license", 120)
    digest = item["sha256"]
    if digest is not None and (not isinstance(digest, str) or not HEX64.fullmatch(digest)):
        raise InputError("Source artifact SHA-256 must be 64 lowercase hexadecimal characters or null")
    _date(item["retrieved_on"], "source artifact retrieved_on", nullable=True)
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
    record = _object(value, required, {"limitations"}, "observation record")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise InputError("Observation schema_version must be 1")
    record_id = _text(record["record_id"], "record_id", 96)
    if not RECORD_ID.fullmatch(record_id):
        raise InputError("record_id has an invalid format")
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
                    {"calibration_artifact_id"}, "assay")
    _text(assay["name"], "assay.name", 300)
    _text(assay["endpoint"], "assay.endpoint", 500)
    _text(assay["unit"], "assay.unit", 80)
    _enum(assay["measurement_role"], MEASUREMENT_ROLES, "measurement role")
    calibration = assay.setdefault("calibration_artifact_id", None)
    if calibration is not None:
        calibration = _text(calibration, "calibration_artifact_id", 96)
        if calibration not in artifacts:
            raise InputError("Calibration references an unknown source artifact")

    unit = _object(record["independent_unit"], {"kind", "id", "parent_id"}, {"hierarchy_note"}, "independent_unit")
    _enum(unit["kind"], UNIT_KINDS, "independent-unit kind")
    for field in ("id", "parent_id"):
        _string_or_null(unit[field], f"independent_unit.{field}")
    unit.setdefault("hierarchy_note", "")
    _text(unit["hierarchy_note"], "independent_unit.hierarchy_note", 500, empty=True)
    if unit["kind"] == "not_reported" and (unit["id"] is not None or unit["parent_id"] is not None):
        raise InputError("A not_reported unit cannot carry an asserted unit identifier")

    observation = _object(record["observation"],
                          {"value", "measurement_time", "comparator_id", "replicate_role"},
                          {"measurement_time_unit", "measurement_uncertainty", "missingness_reason"},
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
    if role == "independent" and (unit["kind"] == "not_reported" or unit["id"] is None):
        raise InputError("An independent replicate needs a source-reported unit identifier")

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


def validate_dataset(dataset):
    required = {"schema_version", "dataset_id", "title", "source_revision", "artifacts", "observations"}
    dataset = _object(dataset, required, {"transitions", "limitations"}, "observation dataset")
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
        if record["record_id"] in records:
            raise InputError(f"Duplicate observation record ID: {record['record_id']}")
        records[record["record_id"]] = record
    transitions = dataset.setdefault("transitions", [])
    if not isinstance(transitions, list) or len(transitions) > 500:
        raise InputError("transitions must contain at most 500 records")
    transition_ids = set()
    for item in transitions:
        transition = _validate_transition(item, records)
        if transition["transition_id"] in transition_ids:
            raise InputError("Transition IDs must be unique")
        transition_ids.add(transition["transition_id"])
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
    source_verification = verify_source_files(dataset["artifacts"], source_root)
    artifacts = {item["artifact_id"]: item for item in dataset["artifacts"]}
    records = dataset["observations"]
    group_fields = ("species", "stage_track", "developmental_interval", "model_system", "assay", "source")
    groups = defaultdict(list)
    duplicate_units = defaultdict(list)
    for record in records:
        key = tuple(json_bytes(record[field]).decode("utf-8") for field in group_fields)
        groups[key].append(record)
        unit = record["independent_unit"]
        if unit["id"] is not None:
            unit_key = (record["source"]["artifact_id"], record["species"], record["stage_track"],
                        record["assay"]["name"], record["assay"]["endpoint"], unit["kind"],
                        unit["id"], unit["parent_id"])
            duplicate_units[unit_key].append(record)
    independent_conflicts = []
    for unit_key, items in duplicate_units.items():
        if len(items) > 1 and any(item["observation"]["replicate_role"] == "independent" for item in items):
            independent_conflicts.append({"record_ids": sorted(item["record_id"] for item in items),
                                          "unit_id": unit_key[6], "assay": unit_key[3],
                                          "endpoint": unit_key[4]})
    if independent_conflicts:
        raise InputError("Repeated rows for a source-reported unit cannot all be asserted as independent; mark repeated/technical roles")

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
            "source_artifact_id": first["source"]["artifact_id"],
            "n_records": len(members),
            "n_distinct_reported_unit_keys": len({(item["independent_unit"]["kind"], item["independent_unit"]["id"],
                                                  item["independent_unit"]["parent_id"])
                                                 for item in members if item["independent_unit"]["id"] is not None}),
            "record_ids": ";".join(sorted(item["record_id"] for item in members)),
            "grouping_note": "Exact recorded species, stage, interval, assay, unit and source match only; no unit conversion or pooling.",
        })

    source_status = dataset["source_revision"]["review_status"]
    warnings = []
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
    verification_summary = {key: value for key, value in source_verification.items() if key != "files"}
    report = {
        "schema_version": 1, "report_kind": "developmental_observation_intake",
        "dataset_id": dataset["dataset_id"], "title": dataset["title"],
        "source_revision_id": dataset["source_revision"]["revision_id"],
        "source_review_status": source_status, "n_source_artifacts": len(artifacts),
        "n_observation_records": len(records), "n_exact_comparison_groups": len(group_rows),
        "n_transitions": len(dataset["transitions"]), "n_continuity_not_reported": not_reported_edges,
        "biological_assay_performed": False,
        "analysis_eligibility": "requires source-specific human review and a frozen analysis plan",
        "source_file_verification": verification_summary,
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
        ],
    }
    lines = ["# Developmental observation intake", "",
             f"Dataset: {dataset['title']} (`{dataset['dataset_id']}`)",
             f"Source revision: `{dataset['source_revision']['revision_id']}` · {source_status}",
             f"Records: {len(records)} · exact comparison groups: {len(group_rows)} · transitions: {len(dataset['transitions'])}", "",
             "No biological assay was performed by this command. Source URIs are never fetched. Optional local byte checks use only files beneath --source-root and do not copy their contents into this bundle.",
             "Analysis eligibility still requires source-specific human review and a frozen analysis plan.", "",
             "## Local source-file byte verification", "",
             f"Status: {source_verification['status']} · verified: {source_verification['n_verified']}/{source_verification['n_artifacts']} artifacts · bytes hashed: {source_verification['bytes_hashed']}",
             "The receipt covers the submitted dataset JSON and generated outputs, not the external source bytes.", ""]
    for row in source_verification["files"]:
        lines.append(f"- {row['artifact_id']} · {row['relative_path'] or 'no local path'} · {row['verification_status']} · {row['observed_sha256'] or 'no observed hash'}{': ' + row['note'] if row['note'] else ''}")
    lines.extend(["", "## Source review", "",
             f"{dataset['source_revision']['citation']} — [{dataset['source_revision']['source_url']}]({dataset['source_revision']['source_url']})",
             f"Recorded review state: {source_status}. A locally recorded review is not authenticated by this tool.", "",
             "## Exact groups", "",
             "Records are grouped only when species, stage, interval, model, endpoint, reported unit, and source artifact match exactly. No conversion or pooling is performed.", ""]
    for row in group_rows[:100]:
        lines.append(f"- {row['group_id']}: {row['species']} · {row['stage_track']} · {row['interval_label']} ({row['interval_unit']}) · {row['endpoint']} [{row['unit']}] · {row['n_records']} records · {row['n_distinct_reported_unit_keys']} distinct reported unit keys")
    if len(group_rows) > 100:
        lines.append(f"- Showing 100 of {len(group_rows)} groups; interval_groups.csv contains the full exact-group table.")
    lines.extend(["", "## Warnings", ""] + ([f"- {item}" for item in warnings] or ["- No structural warning was emitted; this does not imply data eligibility."]))
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
            "independent_unit_id": unit["id"], "independent_unit_parent_id": unit["parent_id"],
            "value": observation["value"], "measurement_time": observation["measurement_time"],
            "measurement_time_unit": observation.get("measurement_time_unit", ""),
            "comparator_id": observation["comparator_id"], "replicate_role": observation["replicate_role"],
            "measurement_uncertainty": observation.get("measurement_uncertainty"),
            "missingness_reason": observation.get("missingness_reason", ""),
            "source_artifact_id": source["artifact_id"], "source_sha256": source["sha256"],
        })
    transition_rows = [{"transition_id": item["transition_id"],
                        "from_record_ids": ";".join(item["from_record_ids"]),
                        "to_record_ids": ";".join(item["to_record_ids"]),
                       "continuity_status": item["continuity_status"], "note": item["note"]}
                       for item in dataset["transitions"]]
    source_file_rows = [{key: row[key] for key in
                         ("artifact_id", "relative_path", "declared_sha256", "observed_sha256",
                          "verification_status", "bytes_hashed", "note")}
                        for row in source_verification["files"]]
    files = {
        "input_dataset.json": raw,
        "observation_intake_report.json": json_bytes(report),
        "observation_records.csv": csv_bytes(list(observation_rows[0]), observation_rows),
        "interval_groups.csv": csv_bytes(list(group_rows[0]), group_rows),
        "transitions.csv": csv_bytes(["transition_id", "from_record_ids", "to_record_ids", "continuity_status", "note"], transition_rows),
        "source_files.csv": csv_bytes(["artifact_id", "relative_path", "declared_sha256", "observed_sha256",
                                        "verification_status", "bytes_hashed", "note"], source_file_rows),
        "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8"),
    }
    return publish_bundle(output, kind="developmental_observation_intake", input_raw=raw, files=files,
                          metadata={"dataset_id": dataset["dataset_id"], "source_revision_id": revision["revision_id"],
                                    "source_review_status": revision["review_status"],
                                    "source_file_verification_status": source_verification["status"],
                                    "biological_assay_performed": False})
