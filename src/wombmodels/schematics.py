"""Render a bounded machine-concept schematic as standalone SVG and HTML.

This is a theoretical systems-layout artifact for planning and criticism. It is
not a build specification, establishes no biological capability, and advances
no gate. Rendering is deterministic: identical input bytes give identical
output bytes.
"""
from __future__ import annotations

from pathlib import Path
import re
from xml.sax.saxutils import escape

from .artifacts import InputError, json_bytes, publish_bundle, read_json

MAX_CONFIG_BYTES = 100_000
MAX_COMPONENTS = 64
MAX_CONNECTIONS = 128
MAX_NOTES = 16
MAX_TEXT = 200
COMPONENT_W = 200
COMPONENT_H = 56
LANE_PAD = 28

KIND_COLORS = {
    "vessel": "#1f5fa8",
    "fluidics": "#0f7b6c",
    "supply": "#8a6d1d",
    "sensing": "#6b4fa1",
    "control": "#a1355c",
    "robotics": "#b3541e",
    "human": "#444444",
    "power": "#7a1f1f",
    "transition": "#2e6b2e",
}
CONNECTION_STYLES = {
    "flow": ("#0f7b6c", "none"),
    "control": ("#a1355c", "6 4"),
    "signal": ("#6b4fa1", "2 4"),
    "service": ("#b3541e", "10 4 2 4"),
}

_ID = re.compile(r"[a-z][a-z0-9_]{0,39}")


def _text(value, field):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= MAX_TEXT:
        raise InputError(f"Schematic {field} must be bounded text")
    return value.strip()


def _position(value, field, limit):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= limit:
        raise InputError(f"Schematic {field} must be an integer within the canvas")
    return value


def validate_layout(layout):
    """Validate a parsed schematic layout; returns it unchanged when valid."""
    if not isinstance(layout, dict) or layout.get("schema_version") != 1:
        raise InputError("Schematic layout must be a schema version 1 object")
    title = _text(layout.get("title"), "title")
    canvas = layout.get("canvas")
    if not isinstance(canvas, dict):
        raise InputError("Schematic layout needs a canvas")
    width = _position(canvas.get("width"), "canvas width", 5000)
    height = _position(canvas.get("height"), "canvas height", 5000)
    if width < 200 or height < 200:
        raise InputError("Schematic canvas is too small")

    lanes = layout.get("lanes")
    if not isinstance(lanes, list) or not 1 <= len(lanes) <= 8:
        raise InputError("Schematic layout needs a bounded lane list")
    lane_ids = set()
    for lane in lanes:
        if not isinstance(lane, dict) or not _ID.fullmatch(str(lane.get("id", ""))):
            raise InputError("Lane IDs must be slugs")
        if lane["id"] in lane_ids:
            raise InputError("Duplicate lane ID")
        lane_ids.add(lane["id"])
        _text(lane.get("label"), "lane label")

    components = layout.get("components")
    if not isinstance(components, list) or not 1 <= len(components) <= MAX_COMPONENTS:
        raise InputError("Schematic layout needs a bounded component list")
    by_id = {}
    for comp in components:
        if not isinstance(comp, dict) or not _ID.fullmatch(str(comp.get("id", ""))):
            raise InputError("Component IDs must be slugs")
        if comp["id"] in by_id:
            raise InputError("Duplicate component ID")
        _text(comp.get("label"), f"label for {comp['id']}")
        if comp.get("lane") not in lane_ids:
            raise InputError(f"Component {comp['id']} refers to an unknown lane")
        if comp.get("kind") not in KIND_COLORS:
            raise InputError(f"Component {comp['id']} has an unknown kind")
        _position(comp.get("x"), f"x for {comp['id']}", width)
        _position(comp.get("y"), f"y for {comp['id']}", height)
        if comp["x"] + COMPONENT_W > width or comp["y"] + COMPONENT_H > height:
            raise InputError(f"Component {comp['id']} extends past the canvas")
        by_id[comp["id"]] = comp

    connections = layout.get("connections", [])
    if not isinstance(connections, list) or len(connections) > MAX_CONNECTIONS:
        raise InputError("Schematic connections must be a bounded list")
    for conn in connections:
        if not isinstance(conn, dict):
            raise InputError("Schematic connections must be objects")
        if conn.get("from") not in by_id or conn.get("to") not in by_id:
            raise InputError("Schematic connection refers to an unknown component")
        if conn["from"] == conn["to"]:
            raise InputError("Schematic connections need two distinct components")
        if conn.get("kind", "flow") not in CONNECTION_STYLES:
            raise InputError("Schematic connection has an unknown kind")
        if conn.get("label") is not None:
            _text(conn["label"], "connection label")

    notes = layout.get("notes", [])
    if not isinstance(notes, list) or len(notes) > MAX_NOTES:
        raise InputError("Schematic notes must be a bounded list")
    for note in notes:
        _text(note, "note")
    return layout


def load_layout(path):
    path = Path(path)
    if path.stat().st_size > MAX_CONFIG_BYTES:
        raise InputError("Schematic config exceeds the byte limit")
    layout, raw = read_json(path)
    if len(raw) > MAX_CONFIG_BYTES:
        raise InputError("Schematic config exceeds the byte limit")
    return validate_layout(layout), raw


def _anchor(comp, side):
    x, y = comp["x"], comp["y"]
    if side == "left":
        return x, y + COMPONENT_H // 2
    return x + COMPONENT_W, y + COMPONENT_H // 2


def render_svg(layout):
    """Render the validated layout as a self-contained SVG string."""
    canvas = layout["canvas"]
    width, height = canvas["width"], canvas["height"]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(layout["title"])}">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#333333"/></marker>',
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width // 2}" y="30" text-anchor="middle" font-family="sans-serif" '
        f'font-size="20" font-weight="bold">{escape(layout["title"])}</text>',
    ]
    by_id = {c["id"]: c for c in layout["components"]}
    # Lane bands span the vertical extent of their components.
    for lane in layout["lanes"]:
        members = [c for c in layout["components"] if c["lane"] == lane["id"]]
        if not members:
            continue
        top = min(c["y"] for c in members) - LANE_PAD
        bottom = max(c["y"] for c in members) + COMPONENT_H + LANE_PAD
        parts.append(
            f'<rect x="8" y="{top}" width="{width - 16}" height="{bottom - top}" '
            f'fill="#f4f4f4" stroke="#dddddd" rx="8"/>')
        parts.append(
            f'<text x="18" y="{top + 20}" font-family="sans-serif" font-size="13" '
            f'fill="#666666">{escape(lane["label"])}</text>')
    for conn in layout["connections"]:
        source, target = by_id[conn["from"]], by_id[conn["to"]]
        forward = target["x"] >= source["x"]
        x1, y1 = _anchor(source, "right" if forward else "left")
        x2, y2 = _anchor(target, "left" if forward else "right")
        color, dash = CONNECTION_STYLES[conn.get("kind", "flow")]
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="2" stroke-dasharray="{dash}" marker-end="url(#arrow)"/>')
        label = conn.get("label")
        if label:
            parts.append(
                f'<text x="{(x1 + x2) // 2}" y="{(y1 + y2) // 2 - 6}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="11" fill="{color}">{escape(label)}</text>')
    for comp in layout["components"]:
        color = KIND_COLORS[comp["kind"]]
        x, y = comp["x"], comp["y"]
        parts.append(
            f'<rect id="{comp["id"]}" x="{x}" y="{y}" width="{COMPONENT_W}" '
            f'height="{COMPONENT_H}" rx="10" fill="#ffffff" stroke="{color}" stroke-width="2.5"/>')
        lines = comp["label"].split("\n")
        start = y + COMPONENT_H // 2 - (len(lines) - 1) * 8 + 4
        for offset, line in enumerate(lines):
            parts.append(
                f'<text x="{x + COMPONENT_W // 2}" y="{start + offset * 16}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="12" fill="#222222">{escape(line)}</text>')
    if layout.get("notes"):
        base = height - 12 - (len(layout["notes"]) - 1) * 16
        for offset, note in enumerate(layout["notes"]):
            parts.append(
                f'<text x="{width // 2}" y="{base + offset * 16}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="11" fill="#888888">{escape(note)}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_html(title, svg):
    body = svg.split("\n", 1)[1]  # drop the XML declaration for inline use
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{escape(title)}</title>\n"
        "<style>body{font-family:sans-serif;margin:2rem;background:#fafafa}"
        "svg{max-width:100%;height:auto;border:1px solid #ddd;background:#fff}</style>\n"
        "</head>\n<body>\n"
        f"{body}"
        "<p>Generated by <code>python -m wombmodels.schematics</code>. Concept layout "
        "only; not a build specification.</p>\n"
        "</body>\n</html>\n"
    )


def publish_schematic(config_path, output):
    layout, raw = load_layout(config_path)
    svg = render_svg(layout)
    files = {
        "schematic.svg": svg.encode("utf-8"),
        "index.html": render_html(layout["title"], svg).encode("utf-8"),
        "layout_snapshot.json": raw,
        "reproduction_plan.json": json_bytes({
            "schema_version": 1,
            "bundle_kind": "machine_schematic",
            "declared_dependencies": ["Python standard library and this project"],
            "command": "python -m wombmodels.schematics --config <layout.json> --out <new-dir>",
            "inputs": ["layout_snapshot.json"],
            "expected_outputs": sorted(
                ["schematic.svg", "index.html", "layout_snapshot.json",
                 "reproduction_plan.json", "receipt.json"]),
            "limits": [
                "Concept layout only; not a build specification.",
                "No component or connection here is evidence of biological capability.",
            ],
        }),
    }
    return publish_bundle(Path(output), kind="machine_schematic", input_raw=raw,
                          files=files, metadata={
                              "title": layout["title"],
                              "components": len(layout["components"]),
                              "connections": len(layout.get("connections", [])),
                              "asserts_biological_capability": False})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    publish_schematic(args.config, args.out)
