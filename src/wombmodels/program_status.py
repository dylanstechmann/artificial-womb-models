"""Render a bounded, evidence-linked program register without advancing gates."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import re

from .artifacts import InputError, csv_bytes, json_bytes, publish_bundle, read_json, sha256

MAX_REGISTER_BYTES = 200_000
MAX_EVIDENCE_BYTES = 8_000_000
TASK_STATES = {"ready", "waiting_dependency", "held", "complete", "deferred"}
GATE_STATES = {"defined", "not_selected", "not_established", "unassessed", "deferred", "review_required"}
DOMAINS = {"planning", "software", "engineering", "evidence_curation", "biological", "clinical", "access"}


def _items(register, key, limit):
    value = register.get(key)
    if not isinstance(value, list) or not 1 <= len(value) <= limit:
        raise InputError(f"{key} must be a nonempty bounded list")
    seen = set()
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise InputError(f"{key} items need string IDs")
        if not re.fullmatch(r"[A-Z][0-9]{1,3}", item["id"]) or item["id"] in seen:
            raise InputError(f"Duplicate or malformed {key} ID")
        seen.add(item["id"])
        if not isinstance(item.get("title"), str) or not item["title"].strip():
            raise InputError(f"{key} items need a title")
        for field, text in item.items():
            if isinstance(text, str) and len(text) > 3000:
                raise InputError(f"Oversized {key} text field {field}")
    return value


def _evidence(root, ref):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise InputError("Evidence needs exactly a local path and a SHA-256")
    token, expected = ref["path"], ref["sha256"]
    if (not isinstance(token, str) or not 1 <= len(token) <= 500
            or "\\" in token or ":" in token or token.startswith("/")
            or any(part in {"", ".", ".."} for part in token.split("/"))):
        raise InputError("Evidence path must stay within the project root")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise InputError("Evidence requires an exact SHA-256")
    path = root.joinpath(*PurePosixPath(token).parts)
    # Check every component before reading, including symlinks whose targets stay inside root.
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise InputError("Evidence path contains a symlink")
    if not path.is_file():
        return {"path": token, "expected_sha256": expected, "observed_sha256": None,
                "status": "missing"}
    with path.open("rb") as stream:
        raw = stream.read(MAX_EVIDENCE_BYTES + 1)
    if len(raw) > MAX_EVIDENCE_BYTES:
        raise InputError("Program evidence file exceeds the byte limit")
    observed = sha256(raw)
    return {"path": token, "expected_sha256": expected, "observed_sha256": observed,
            "status": "matches" if observed == expected else "changed_since_assessment"}


def assess_register(register, root):
    root = Path(root).absolute()
    if not isinstance(register, dict):
        raise InputError("Program register must be an object")
    if register.get("schema_version") != 1 or register.get("program_status") != "active":
        raise InputError("Expected an active version 1 program register")
    for field in ("program_id", "assessment_date"):
        if not isinstance(register.get(field), str) or not 1 <= len(register[field]) <= 100:
            raise InputError(f"Program register needs a bounded {field}")
    if not isinstance(register.get("objective"), str) or not 1 <= len(register["objective"].strip()) <= 3000:
        raise InputError("Program register needs a bounded objective")
    requirements = _items(register, "requirements", 30)
    gates = _items(register, "gates", 12)
    milestones = _items(register, "milestones", 50)
    achievements = _items(register, "achievements", 50)
    tasks = _items(register, "tasks", 100)
    uncertainties = _items(register, "uncertainties", 30)
    ids = [item["id"] for item in requirements + gates + milestones + achievements + tasks + uncertainties]
    if len(set(ids)) != len(ids):
        raise InputError("IDs must be unique across the register")
    fields = {"requirements": ("acceptance",),
        "gates": ("acceptance", "hold_condition", "next_discriminator"),
        "milestones": ("acceptance",), "achievements": ("credit", "boundary"),
        "tasks": ("acceptance", "decision_consequence", "stop_rule"),
        "uncertainties": ("question", "status", "next_decision")}
    for collection, required in fields.items():
        for item in register[collection]:
            if any(not isinstance(item.get(field), str) or not item[field].strip() for field in required):
                raise InputError(f"{collection} item needs {', '.join(required)}")
    gate_ids = {item["id"] for item in gates}
    uncertainty_ids = {item["id"] for item in uncertainties}
    milestone_ids = {item["id"] for item in milestones}
    for item in requirements:
        if item.get("gate_id") not in gate_ids:
            raise InputError("Requirement refers to an unknown gate")
    for item in gates:
        if item.get("status") not in GATE_STATES or item.get("domain") not in DOMAINS:
            raise InputError("Gate needs a declared domain and unresolved/defined status")
        if not item.get("acceptance") or not item.get("hold_condition"):
            raise InputError("Gate needs advance and hold conditions")
    for item in milestones:
        if item.get("gate_id") not in gate_ids or item.get("status") not in TASK_STATES:
            raise InputError("Milestone status or gate is invalid")
        if item.get("domain") not in DOMAINS:
            raise InputError("Milestone needs an explicit evidence domain")
    for item in achievements:
        if item.get("domain") not in DOMAINS or item.get("status") != "complete":
            raise InputError("Achievement needs a complete status and explicit evidence domain")
    task_map = {item["id"]: item for item in tasks}
    for item in tasks:
        if (item.get("gate_id") not in gate_ids or item.get("uncertainty_id") not in uncertainty_ids
                or item.get("status") not in TASK_STATES or item.get("domain") not in DOMAINS):
            raise InputError("Task status, gate or uncertainty reference is invalid")
        if not item.get("acceptance") or not item.get("decision_consequence") or not item.get("stop_rule"):
            raise InputError("Task needs acceptance, decision consequence and stop rule")
        cap = item.get("agent_hour_cap")
        if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not 0 < cap <= 48:
            raise InputError("Task cap must be positive and at most 48 aggregate agent-hours")
        if not isinstance(item.get("depends_on"), list) or len(item["depends_on"]) > 20:
            raise InputError("Task dependencies must be bounded")
        if any(not isinstance(dep, str) for dep in item["depends_on"]):
            raise InputError("Task dependency IDs must be strings")
        if len(set(item["depends_on"])) != len(item["depends_on"]):
            raise InputError("Duplicate task dependency")
        if any(dep not in task_map and dep not in milestone_ids for dep in item["depends_on"]):
            raise InputError("Task refers to an unknown dependency")
    ordered_tasks = []
    def visit(key, visiting, visited):
        if key in visiting:
            raise InputError("Task dependencies contain a cycle")
        if key in visited:
            return
        for dep in task_map[key]["depends_on"]:
            if dep in task_map:
                visit(dep, visiting | {key}, visited)
        visited.add(key)
        ordered_tasks.append(key)
    visited = set()
    for key in task_map:
        visit(key, set(), visited)
    checks, completion_valid = [], {}
    for item in achievements + milestones + tasks:
        refs = item.get("evidence", [])
        if not isinstance(refs, list) or len(refs) > 20:
            raise InputError("Evidence references must be a bounded list")
        complete = item.get("status") == "complete"
        if complete and not refs:
            raise InputError("A completed item must cite pinned local evidence")
        rows = [{"item_id": item["id"], **_evidence(root, ref)} for ref in refs]
        checks += rows
        completion_valid[item["id"]] = complete and bool(rows) and all(row["status"] == "matches" for row in rows)
    evidence_matches = completion_valid.copy()
    # A matching completed descendant cannot bypass an incomplete or stale ancestor.
    for key in ordered_tasks:
        completion_valid[key] = completion_valid[key] and all(
            completion_valid[dep] for dep in task_map[key]["depends_on"])
    task_rows = []
    for item in tasks:
        unmet = [dep for dep in item["depends_on"] if not completion_valid.get(dep, False)]
        available = item["status"] == "ready" and not unmet
        task_rows.append({"id": item["id"], "title": item["title"],
            "gate_id": item["gate_id"], "uncertainty_id": item["uncertainty_id"],
            "declared_status": item["status"], "dependencies_satisfied": not unmet,
            "eligible_to_start": available, "unmet_dependencies": ";".join(unmet),
            "agent_hour_cap": item["agent_hour_cap"]})
    return {"schema_version": 1, "program_id": register["program_id"],
        "assessment_date": register["assessment_date"], "gate_statuses": gates,
        "tasks": task_rows, "evidence_checks": checks, "completion_evidence_matches": evidence_matches,
        "completion_dependencies_valid": completion_valid,
        "evidence_integrity_matches": all(row["status"] == "matches" for row in checks),
        "scientific_review": "not_established_by_this_tool", "biological_gate_updates": 0,
        "note": "Declared completion and matching evidence bytes do not authenticate acceptance criteria, scientific review or biological outcomes."}


def _markdown(register, report):
    def table_row(values):
        return "| " + " | ".join(str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ") for value in values) + " |"
    lines = ["# Program progress against the plan", "",
        f"Assessment date: {report['assessment_date']}. Generated from config/program/roadmap.json.", "",
        register["objective"].replace("\r", " ").replace("\n", " "), "",
        "This view checks pinned local evidence and task dependencies. It never advances a biological gate or authenticates scientific review. Declared completion is scoped to the named artifact; no readiness percentage is calculated.", "",
        "## Gate comparison", "", "| Gate | Domain | Declared state | Missing requirement |",
        "| --- | --- | --- | --- |"]
    lines += [table_row((g['id'] + " " + g['title'], g['domain'], g['status'], g['next_discriminator'])) for g in register["gates"]]
    lines += ["", "## Requirement comparison", "", "| Requirement | Gate | Acceptance condition |",
              "| --- | --- | --- |"]
    lines += [table_row((r['id'] + " " + r['title'], r['gate_id'], r['acceptance'])) for r in register["requirements"]]
    lines += ["", "## Completed contributions", "",
              "| Declared contribution | Domain | Pinned evidence matches | What it establishes | What it does not establish |",
              "| --- | --- | --- | --- | --- |"]
    lines += [table_row((a['id'] + " " + a['title'], a['domain'], report['completion_evidence_matches'][a['id']], a['credit'], a['boundary'])) for a in register["achievements"]]
    lines += ["", "## Milestone comparison", "",
              "| Milestone | Declared state | Domain | Completed evidence matches | Acceptance condition |", "| --- | --- | --- | --- | --- |"]
    lines += [table_row((m['id'] + " " + m['title'], m['status'], m['domain'], report['completion_evidence_matches'][m['id']] if m['status'] == 'complete' else 'not claimed', m['acceptance'])) for m in register["milestones"]]
    lines += ["", "## Next tasks", "",
              "| Task | Gate | Available now | Cap in aggregate agent hours | Dependencies still needed |",
              "| --- | --- | --- | ---: | --- |"]
    lines += [table_row((t['id'] + " " + t['title'], t['gate_id'], 'yes' if t['eligible_to_start'] else 'no', t['agent_hour_cap'], t['unmet_dependencies'] or 'none')) for t in report["tasks"]]
    lines += ["", "## Uncertainties", "", "| ID | Question | Current evidence state | Next decision |",
              "| --- | --- | --- | --- |"]
    lines += [table_row((u['id'], u['question'], u['status'], u['next_decision'])) for u in register["uncertainties"]]
    lines += ["", "## Evidence integrity", "", "| Item | Evidence file | Check |", "| --- | --- | --- |"]
    lines += [table_row((row['item_id'], row['path'], row['status'])) for row in report["evidence_checks"]]
    lines += ["", "For the next work cycle, read PROGRAM_PLAN.md and the original task acceptance conditions. Match each claimed result to its gate and uncertainty. Hold a branch after two cycles with no usable new information. Do not contact authors or other people. No new process or automation is started by this status command.", ""]
    return "\n".join(lines).encode("utf-8")


def publish_status(register_path, root, output):
    if Path(register_path).stat().st_size > MAX_REGISTER_BYTES:
        raise InputError("Program register exceeds the byte limit")
    register, raw = read_json(Path(register_path))
    if len(raw) > MAX_REGISTER_BYTES:
        raise InputError("Program register exceeds the byte limit")
    report = assess_register(register, root)
    files = {"input_register.json": raw, "status_report.json": json_bytes(report),
        "tasks.csv": csv_bytes(list(report["tasks"][0]), report["tasks"]),
        "evidence_checks.csv": csv_bytes(["item_id", "path", "expected_sha256", "observed_sha256", "status"], report["evidence_checks"]),
        "PROGRAM_STATUS.md": _markdown(register, report)}
    files["reproduction_plan.json"] = json_bytes({"schema_version": 1,
        "bundle_kind": "research_program_status", "declared_dependencies": ["Python standard library and this project"],
        "command": "python -m wombmodels.program_status --register <input_register.json> --root <project-root> --out <new-dir>",
        "inputs": ["input_register.json", "external pinned local evidence files"],
        "expected_outputs": sorted([*files, "reproduction_plan.json", "receipt.json"]),
        "limits": [report["note"], "No biological model, hardware action or automatic gate promotion."]})
    return publish_bundle(Path(output), kind="research_program_status", input_raw=raw,
        files=files, metadata={"program_id": report["program_id"],
            "evidence_integrity_matches": report["evidence_integrity_matches"],
            "biological_gate_updates": 0, "scientific_review": report["scientific_review"]})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    publish_status(args.register, args.root, args.out)
