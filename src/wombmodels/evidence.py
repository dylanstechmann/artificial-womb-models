"""Validate evidence without pooling species, stages, or source classes."""
from __future__ import annotations

import json
import math
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


def unit_ids(value, label):
    """Validate bounded source unit identifiers without inventing missing IDs."""
    if (not isinstance(value, list) or len(value) > 1000
            or any(not isinstance(item, str)
                   or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", item)
                   for item in value)
            or len(set(value)) != len(value)):
        raise InputError(f"{label} must contain at most 1000 unique stable unit IDs")
    return value


def interval_components(item, label):
    """Validate exact-axis numeric intervals without converting reported units."""
    components = item.get("interval_components", [])
    if not isinstance(components, list) or len(components) > 16:
        raise InputError(f"{label}.interval_components must contain at most 16 objects")
    result = {}
    expected_fields = {"axis", "unit", "minimum", "maximum"}
    for component in components:
        if not isinstance(component, dict) or set(component) != expected_fields:
            raise InputError(f"{label} interval components need axis, unit, minimum and maximum")
        axis, unit = component["axis"], component["unit"]
        if (not isinstance(axis, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", axis)
                or axis in result or not isinstance(unit, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,63}", unit)):
            raise InputError(f"{label} interval axes and units must be unique stable identifiers")
        minimum, maximum = component["minimum"], component["maximum"]
        if (isinstance(minimum, bool) or not isinstance(minimum, (int, float))
                or isinstance(maximum, bool) or not isinstance(maximum, (int, float))):
            raise InputError(f"{label} interval bounds must be finite numbers with minimum <= maximum")
        try:
            finite_bounds = math.isfinite(float(minimum)) and math.isfinite(float(maximum))
        except OverflowError:
            finite_bounds = False
        if not finite_bounds or minimum > maximum:
            raise InputError(f"{label} interval bounds must be finite numbers with minimum <= maximum")
        result[axis] = {"axis": axis, "unit": unit, "minimum": minimum, "maximum": maximum}
    return result


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
    transitions = indexed(ledger.get("transitions"), "transitions")
    source_interval_scopes = {}
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
        source_interval_scopes[source["id"]] = interval_components(source, f"source {source['id']}")
    for claim in claims.values():
        for field in ("text", "species", "interval", "boundary"):
            text(claim.get(field), f"claim {field}")
        status = claim.get("status")
        if not isinstance(status, str) or status not in CLAIM_STATUSES:
            raise InputError("Unknown claim status")
        unit_ids(claim.get("unit_ids", []), f"claim {claim['id']} unit_ids")
        references(claim.get("stage_ids"), stages, "claim stages")
        references(claim.get("source_ids"), sources, "claim sources",
                   allow_empty=status in {"unassessed", "undemonstrated"})
        claim_intervals = interval_components(claim, f"claim {claim['id']}")
        if claim_intervals and not claim["source_ids"]:
            raise InputError(f"Claim {claim['id']} cannot assert structured intervals without a source")
        for source_id in claim["source_ids"]:
            source = sources[source_id]
            if claim["species"] != source["species"]:
                raise InputError(f"Claim {claim['id']} changes its source species/model")
            if set(claim["stage_ids"]) - set(source["stage_ids"]):
                raise InputError(f"Claim {claim['id']} extends its source stage coverage")
            source_intervals = source_interval_scopes[source_id]
            if source_intervals and not claim_intervals:
                raise InputError(f"Claim {claim['id']} omits structured intervals reported by source {source_id}")
            for axis, interval in claim_intervals.items():
                source_interval = source_intervals.get(axis)
                if (source_interval is None or interval["unit"] != source_interval["unit"]
                        or interval["minimum"] < source_interval["minimum"]
                        or interval["maximum"] > source_interval["maximum"]):
                    raise InputError(f"Claim {claim['id']} extends or changes source {source_id} interval {axis}")
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
    for transition in transitions.values():
        from_stage = transition.get("from_stage_id")
        to_stage = transition.get("to_stage_id")
        if (not isinstance(from_stage, str) or from_stage not in stages
                or not isinstance(to_stage, str) or to_stage not in stages
                or from_stage == to_stage):
            raise InputError("Transitions need two distinct known stage IDs")
        for field in ("species", "required_observation", "boundary"):
            text(transition.get(field), f"transition {field}")
        continuity = transition.get("continuity_state")
        if not isinstance(continuity, str) or continuity not in {"demonstrated", "contradicted", "not_reported"}:
            raise InputError("Transition continuity_state must be demonstrated, contradicted or not_reported")
        transition_units = unit_ids(transition.get("unit_ids"), f"transition {transition['id']} unit_ids")
        if continuity == "not_reported" and transition_units:
            raise InputError("Unreported transition continuity cannot name unit IDs")
        if continuity != "not_reported" and not transition_units:
            raise InputError("Reported transition continuity needs source unit IDs")
        source_ids = references(transition.get("source_ids"), sources, "transition sources", allow_empty=True)
        claim_ids = references(transition.get("claim_ids"), claims, "transition claims", allow_empty=True)
        locations = transition.get("source_locations")
        if not isinstance(locations, list) or len(locations) > 50:
            raise InputError("Transition source_locations must contain at most 50 objects")
        located_sources = set()
        for location in locations:
            if not isinstance(location, dict) or set(location) != {"source_id", "locator"}:
                raise InputError("Transition source locations need source_id and locator")
            source_id = location["source_id"]
            if not isinstance(source_id, str) or source_id not in sources or source_id in located_sources:
                raise InputError("Transition source locations must identify unique known sources")
            text(location["locator"], "transition source locator")
            located_sources.add(source_id)
        if located_sources != set(source_ids):
            raise InputError("Every transition source needs exactly one source locator")
        linked_sources = set()
        linked_unit_sets = []
        for claim_id in claim_ids:
            claim = claims[claim_id]
            if claim["species"] != transition["species"]:
                raise InputError(f"Transition {transition['id']} changes its claim species/model")
            if {from_stage, to_stage} - set(claim["stage_ids"]):
                raise InputError(f"Transition {transition['id']} extends its claim stage coverage")
            linked_sources.update(claim["source_ids"])
            linked_unit_sets.append(set(unit_ids(claim.get("unit_ids", []),
                                               f"claim {claim_id} unit_ids")))
        if linked_sources != set(source_ids):
            raise InputError("Transition source IDs must match the sources cited by its linked claims")
        if transition_units:
            if not linked_unit_sets:
                raise InputError("Transition unit IDs need linked claims")
            common_claim_units = set.intersection(*linked_unit_sets)
            if not set(transition_units) <= common_claim_units:
                raise InputError("Transition unit IDs must be present in every linked claim")
        for source_id in source_ids:
            source = sources[source_id]
            if source["species"] != transition["species"]:
                raise InputError(f"Transition {transition['id']} changes its source species/model")
            if {from_stage, to_stage} - set(source["stage_ids"]):
                raise InputError(f"Transition {transition['id']} extends its source stage coverage")
        if continuity in {"demonstrated", "contradicted"}:
            if not source_ids or not claim_ids:
                raise InputError("Reported transition continuity needs source-linked claims")
            if any(sources[item]["kind"] not in {"peer_reviewed_animal", "peer_reviewed_human_invitro"}
                   for item in source_ids):
                raise InputError("Announcements and regulator discussions cannot establish transition continuity")
            if any(claims[item]["status"] != "source_reported" for item in claim_ids):
                raise InputError("Reported transition continuity needs source_reported claims")
    return ledger


def evidence_report(ledger_path: Path, output: Path) -> dict:
    ledger, raw = read_json(ledger_path)
    validate_ledger(ledger)
    source_map = {item["id"]: item for item in ledger["sources"]}
    claim_rows = [{"claim_id": item["id"], "status": item["status"],
                   "species": item["species"], "interval": item["interval"],
                   "unit_ids": ";".join(item.get("unit_ids", [])),
                   "interval_components": json.dumps(
                       item.get("interval_components", []), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")),
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
    transition_rows = [{"transition_id": item["id"], "from_stage_id": item["from_stage_id"],
                        "to_stage_id": item["to_stage_id"], "species": item["species"],
                        "continuity_state": item["continuity_state"],
                        "unit_ids": ";".join(item["unit_ids"]),
                        "source_ids": ";".join(item["source_ids"]),
                        "claim_ids": ";".join(item["claim_ids"]),
                        "source_locations": json.dumps(item["source_locations"], ensure_ascii=False,
                                                        sort_keys=True, separators=(",", ":")),
                        "required_observation": item["required_observation"],
                        "boundary": item["boundary"]} for item in ledger["transitions"]]
    report = {"schema_version": 1, "report_kind": "reviewed_evidence_map", "reviewed_on": ledger["reviewed_on"],
              "biological_assay_performed": False, "complete_human_gestation_demonstrated": False,
              "scope": ledger["scope"], "stages": ledger["stages"], "sources": ledger["sources"],
              "claims": ledger["claims"], "requirements": ledger["requirements"],
              "transitions": ledger["transitions"],
              "limits": ["This bounded ledger is not a systematic review or evidence of absence.",
                         "Stage coverage is not a readiness score; different species and studies are not concatenated.",
                         "Publications, regulator discussions and institutional announcements remain distinct."]}
    lines = ["# Artificial gestation evidence map", "", f"Reviewed: {ledger['reviewed_on']}.", "",
             ledger["scope"], "", "Complete human gestation, surrogacy replacement and fewer congenital defects remain undemonstrated in this ledger.",
             "No biological assay was performed. This is a bounded reviewed-source ledger, not a systematic review.", ""]
    lines.extend(["## Stage transitions", "",
                  "Continuity is recorded only when a cited source and linked claim support the same transition. Unknown edges are not joined across species or studies.", ""])
    for transition in ledger["transitions"]:
        from_label = next(stage["label"] for stage in ledger["stages"] if stage["id"] == transition["from_stage_id"])
        to_label = next(stage["label"] for stage in ledger["stages"] if stage["id"] == transition["to_stage_id"])
        lines.extend([f"### {from_label} → {to_label}", "",
                      f"Continuity: {transition['continuity_state']}; model: {transition['species']}; source unit IDs: {', '.join(transition['unit_ids']) or 'not reported'}.", "",
                      f"Evidence needed: {transition['required_observation']}", "",
                      f"Boundary: {transition['boundary']}", ""])
        for location in transition["source_locations"]:
            source = source_map[location["source_id"]]
            lines.append(f"Source locator ({source['kind']}): [{source['title']}]({source['url']}) — {location['locator']}")
            lines.append("")
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
             "transitions.csv": csv_bytes(list(transition_rows[0]), transition_rows),
             "REPORT.md": ("\n".join(lines) + "\n").encode("utf-8")}
    return publish_bundle(output, kind="reviewed_evidence_map", input_raw=raw, files=files,
                          metadata={"reviewed_on": ledger["reviewed_on"], "biological_assay_performed": False,
                                    "complete_human_gestation_demonstrated": False})
