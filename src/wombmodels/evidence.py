"""Validate evidence without pooling species, stages, or source classes."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json

CLAIM_STATUSES = {"source_reported", "discussion_scope", "announced", "unassessed", "undemonstrated"}
SOURCE_KINDS = {"peer_reviewed_animal", "peer_reviewed_human_invitro",
                "regulator_discussion", "institution_announcement"}
PROTECTED_CLAIMS = {"complete-human-gestation", "surrogacy-replacement", "fewer-congenital-defects"}


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise InputError(f"{label} must be nonempty text of at most 4000 characters")
    return value


def indexed(items, label):
    if not isinstance(items, list) or not 1 <= len(items) <= 500:
        raise InputError(f"{label} must contain 1–500 objects")
    result = {}
    for item in items:
        if not isinstance(item, dict):
            raise InputError(f"{label} entries must be objects")
        identifier = text(item.get("id"), f"{label}.id")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,95}", identifier) or identifier in result:
            raise InputError(f"Invalid or duplicate {label} ID: {identifier}")
        result[identifier] = item
    return result


def references(value, allowed, label, *, allow_empty=False):
    if (not isinstance(value, list) or (not value and not allow_empty)
            or not all(isinstance(item, str) for item in value)
            or len(set(value)) != len(value) or set(value) - set(allowed)):
        raise InputError(f"{label} must contain unique known IDs")
    return value


def validate_ledger(ledger):
    if not isinstance(ledger, dict) or ledger.get("schema_version") != 1 or isinstance(ledger.get("schema_version"), bool):
        raise InputError("Evidence schema_version must be 1")
    try:
        reviewed_on = ledger.get("reviewed_on", "")
        if not isinstance(reviewed_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reviewed_on):
            raise ValueError("Invalid calendar date representation")
        date.fromisoformat(reviewed_on)
    except (TypeError, ValueError) as exc:
        raise InputError("reviewed_on must be an ISO calendar date") from exc
    text(ledger.get("scope"), "scope")
    stages = indexed(ledger.get("stages"), "stages")
    sources = indexed(ledger.get("sources"), "sources")
    claims = indexed(ledger.get("claims"), "claims")
    requirements = indexed(ledger.get("requirements"), "requirements")
    for stage in stages.values():
        text(stage.get("label"), "stage label")
        text(stage.get("boundary"), "stage boundary")
    for source in sources.values():
        for field in ("title", "species", "interval", "boundary"):
            text(source.get(field), f"source {field}")
        if not isinstance(source.get("kind"), str) or source["kind"] not in SOURCE_KINDS:
            raise InputError("Unknown source kind")
        try:
            parsed = urlsplit(text(source.get("url"), "source url"))
        except ValueError as exc:
            raise InputError("Invalid source URL") from exc
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise InputError("Sources must use public HTTPS URLs")
        references(source.get("stage_ids"), stages, "source stages")
    for claim in claims.values():
        for field in ("text", "species", "interval", "boundary"):
            text(claim.get(field), f"claim {field}")
        status = claim.get("status")
        if not isinstance(status, str) or status not in CLAIM_STATUSES:
            raise InputError("Unknown claim status")
        references(claim.get("stage_ids"), stages, "claim stages")
        references(claim.get("source_ids"), sources, "claim sources",
                   allow_empty=status in {"unassessed", "undemonstrated"})
        for source_id in claim["source_ids"]:
            source = sources[source_id]
            if claim["species"] != source["species"]:
                raise InputError(f"Claim {claim['id']} changes its source species/model")
            if set(claim["stage_ids"]) - set(source["stage_ids"]):
                raise InputError(f"Claim {claim['id']} extends its source stage coverage")
            expected = {"peer_reviewed_animal": "source_reported",
                        "peer_reviewed_human_invitro": "source_reported",
                        "regulator_discussion": "discussion_scope",
                        "institution_announcement": "announced"}[source["kind"]]
            if status not in {expected, "unassessed", "undemonstrated"}:
                raise InputError(f"Claim {claim['id']} upgrades its source class")
        if claim["id"] in PROTECTED_CLAIMS and (status not in {"unassessed", "undemonstrated"}
                                                 or claim["species"] != "human"):
            raise InputError("Complete gestation and proposed human benefits remain unassessed/undemonstrated")
    if PROTECTED_CLAIMS - set(claims):
        raise InputError("Ledger must explicitly retain complete gestation and proposed benefit gaps")
    for requirement in requirements.values():
        text(requirement.get("text"), "requirement text")
        if not isinstance(requirement.get("status"), str) or requirement["status"] not in {"unassessed", "partially_documented"}:
            raise InputError("Requirement status must preserve incomplete evidence")
        references(requirement.get("stage_ids"), stages, "requirement stages")
        references(requirement.get("claim_ids"), claims, "requirement claims")
        if requirement["status"] == "partially_documented" and not any(
                claims[item]["status"] == "source_reported" for item in requirement["claim_ids"]):
            raise InputError("Partially documented requirements need a source-reported claim")
    return ledger


def evidence_report(ledger_path: Path, output: Path) -> dict:
    ledger, raw = read_json(ledger_path)
    validate_ledger(ledger)
    source_map = {item["id"]: item for item in ledger["sources"]}
    claim_rows = [{"claim_id": item["id"], "status": item["status"],
                   "species": item["species"], "interval": item["interval"],
                   "stage_ids": ";".join(item["stage_ids"]),
                   "source_ids": ";".join(item["source_ids"]),
                   "source_kinds": ";".join(sorted({source_map[s]["kind"] for s in item["source_ids"]})),
                   "claim": item["text"], "boundary": item["boundary"]}
                  for item in ledger["claims"]]
    stage_rows = []
    for stage in ledger["stages"]:
        selected = [claim for claim in ledger["claims"] if stage["id"] in claim["stage_ids"]]
        for species in sorted({claim["species"] for claim in selected}) or ["no reviewed model"]:
            selected_species = [claim for claim in selected if claim["species"] == species]
            stage_rows.append({"stage_id": stage["id"], "stage": stage["label"], "species": species,
                               "claim_ids": ";".join(item["id"] for item in selected_species),
                               "statuses": ";".join(sorted({item["status"] for item in selected_species})),
                               "boundary": stage["boundary"]})
    requirement_rows = [{"requirement_id": item["id"], "requirement": item["text"],
                         "status": item["status"], "stage_ids": ";".join(item["stage_ids"]),
                         "claim_ids": ";".join(item["claim_ids"])} for item in ledger["requirements"]]
    report = {"schema_version": 1, "report_kind": "reviewed_evidence_map", "reviewed_on": ledger["reviewed_on"],
              "biological_assay_performed": False, "complete_human_gestation_demonstrated": False,
              "scope": ledger["scope"], "stages": ledger["stages"], "sources": ledger["sources"],
              "claims": ledger["claims"], "requirements": ledger["requirements"],
              "limits": ["This bounded ledger is not a systematic review or evidence of absence.",
                         "Stage coverage is not a readiness score; different species and studies are not concatenated.",
                         "Publications, regulator discussions and institutional announcements remain distinct."]}
    lines = ["# Artificial gestation evidence map", "", f"Reviewed: {ledger['reviewed_on']}.", "",
             ledger["scope"], "", "Complete human gestation, surrogacy replacement and fewer congenital defects remain undemonstrated in this ledger.",
             "No biological assay was performed. This is a bounded reviewed-source ledger, not a systematic review.", ""]
    for item in ledger["claims"]:
        lines.extend([f"## {item['id']}", "", f"Status: {item['status']}; model: {item['species']}; interval: {item['interval']}.",
                      "", item["text"], "", f"Boundary: {item['boundary']}", ""])
        for source_id in item["source_ids"]:
            source = source_map[source_id]
            lines.extend([f"Source ({source['kind']}): [{source['title']}]({source['url']}).", ""])
    files = {"input_ledger.json": raw, "evidence_report.json": json_bytes(report),
             "claims.csv": csv_bytes(list(claim_rows[0]), claim_rows),
             "stage_map.csv": csv_bytes(list(stage_rows[0]), stage_rows),
             "requirements.csv": csv_bytes(list(requirement_rows[0]), requirement_rows),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    return publish_bundle(output, kind="reviewed_evidence_map", input_raw=raw, files=files,
                          metadata={"reviewed_on": ledger["reviewed_on"], "biological_assay_performed": False,
                                    "complete_human_gestation_demonstrated": False})
