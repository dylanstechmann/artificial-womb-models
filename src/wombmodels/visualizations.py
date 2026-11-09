"""Standalone 3D views of published dimensionless twin trajectories.

The viewer is a local HTML/SVG software artifact. It has no external resources,
network calls, biological units, machine controls or scientific interpretation.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

from .artifacts import InputError, json_bytes, publish_bundle, read_json, sha256
from .bundle_verification import verify_bundle
from .exchange import NOTICE

MAX_TRAJECTORY_BYTES = 12_000_000
MAX_TRAJECTORY_ROWS = 50_002
MAX_VARIANTS = 6
SOURCE_KINDS = {
    "dimensionless_whole_path_twin",
    "dimensionless_mechanical_twin",
    "dimensionless_reciprocal_twin",
}
COMMON_AXES = (
    "dimensionless_time", "size", "capacity_margin", "request_fraction",
    "served_fraction", "delivered_flux", "bulk_stock", "deep_receipt_rate",
    "cumulative_unserved", "progression", "reserve", "supplement",
    "controller_reading",
)
MECHANICAL_AXES = ("wall_load", "wall_stiffness", "wall_strain",
                   "wall_safety_margin", "wall_damage")
COLORS = ("#1769aa", "#c43c39", "#16836f", "#8659a8", "#a66a00", "#bc477b")


def _read_trajectory(path, expected):
    if path.is_symlink():
        raise InputError("Trajectory must not be a symlink")
    with path.open("rb") as stream:
        raw = stream.read(MAX_TRAJECTORY_BYTES + 1)
    if len(raw) > MAX_TRAJECTORY_BYTES:
        raise InputError("Trajectory CSV exceeds the 12 MB limit")
    if sha256(raw) != expected.get("sha256") or len(raw) != expected.get("size_bytes"):
        raise InputError(f"Trajectory does not match the source receipt: {path.name}")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)) or "dimensionless_time" not in columns:
            raise InputError("Trajectory needs unique columns and dimensionless_time")
        rows = []
        previous = -1.0
        for row in reader:
            if len(rows) >= MAX_TRAJECTORY_ROWS or None in row:
                raise InputError("Trajectory has too many rows or malformed columns")
            values = {}
            for name, text in row.items():
                if text is None:
                    raise InputError("Trajectory has a missing field")
                value = float(text)
                if not math.isfinite(value):
                    raise InputError("Trajectory values must be finite")
                values[name] = value
            if values["dimensionless_time"] <= previous:
                raise InputError("Trajectory times must be strictly increasing")
            previous = values["dimensionless_time"]
            rows.append(values)
    except InputError:
        raise
    except (UnicodeError, csv.Error, TypeError, ValueError, OverflowError):
        raise InputError("Trajectory must be bounded UTF-8 numeric CSV") from None
    if len(rows) < 2:
        raise InputError("Trajectory needs at least two samples")
    return raw, rows, columns


def load_twin_bundle(directory):
    root = Path(directory)
    checked = verify_bundle(root, strict=True)
    if not checked["bytes_verified"]:
        raise InputError("Source twin bundle fails strict verification: " + "; ".join(checked["errors"]))
    if checked["bundle_kind"] not in SOURCE_KINDS:
        raise InputError("3D visualization requires a whole-path, mechanical or reciprocal twin bundle")
    receipt, receipt_raw = read_json(root / "receipt.json")
    variants = receipt.get("metadata", {}).get("n_variants")
    if isinstance(variants, bool) or not isinstance(variants, int) or not 2 <= variants <= MAX_VARIANTS:
        raise InputError("Source receipt has an invalid variant count")
    series = []
    for filename, expected in sorted(receipt.get("outputs", {}).items()):
        if not filename.startswith("trajectory_") or not filename.endswith(".csv"):
            continue
        name = filename[len("trajectory_"):-len(".csv")]
        if not name:
            raise InputError("Trajectory variant name must not be empty")
        raw, rows, columns = _read_trajectory(root / filename, expected)
        series.append({"name": name, "rows": rows, "columns": columns, "raw": raw})
    if len(series) != variants:
        raise InputError("Source trajectory count does not match its receipt")
    axes = [name for name in COMMON_AXES + MECHANICAL_AXES
            if all(name in item["columns"] for item in series)]
    if len(axes) < 3:
        raise InputError("Trajectories need at least three shared numeric axes")
    return {"kind": checked["bundle_kind"], "receipt": receipt,
            "receipt_raw": receipt_raw, "series": series, "axes": axes}


def _extent(series, axis):
    low = min(row[axis] for item in series for row in item["rows"])
    high = max(row[axis] for item in series for row in item["rows"])
    if low == high:
        padding = max(abs(low) * 0.05, 0.5)
        return low - padding, high + padding
    return low, high


def _project(point, extents, yaw=-0.65, pitch=0.48, width=1000, height=650):
    centered = [2 * (value - low) / (high - low) - 1
                for value, (low, high) in zip(point, extents)]
    x, y, z = centered
    horizontal = x * math.cos(yaw) - y * math.sin(yaw)
    depth = x * math.sin(yaw) + y * math.cos(yaw)
    vertical = z * math.cos(pitch) - depth * math.sin(pitch)
    return (width / 2 + horizontal * width * 0.32,
            height * 0.53 - vertical * height * 0.36)


def render_svg(series, axes=("dimensionless_time", "bulk_stock", "progression")):
    extents = [_extent(series, axis) for axis in axes]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 650" '
        'role="img" aria-label="Three-dimensional dimensionless twin trajectory view">',
        '<rect width="1000" height="650" fill="#f7f9fc"/>',
        '<text x="36" y="42" font-family="sans-serif" font-size="23" font-weight="600" fill="#172536">Dimensionless twin trajectories</text>',
        '<text x="36" y="68" font-family="sans-serif" font-size="14" fill="#526174">Static 3D projection; open index.html for interactive rotation and axis selection.</text>',
    ]
    corners = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    edges = [(a, b) for a in corners for b in corners
             if sum(x != y for x, y in zip(a, b)) == 1]
    for start, end in edges:
        one = _project(start, extents)
        two = _project(end, extents)
        parts.append(f'<line x1="{one[0]:.3f}" y1="{one[1]:.3f}" x2="{two[0]:.3f}" y2="{two[1]:.3f}" stroke="#c7d0dc" stroke-width="1"/>')
    for index, item in enumerate(series):
        points = [_project([row[axis] for axis in axes], extents) for row in item["rows"]]
        path = " ".join(f"{'M' if i == 0 else 'L'} {x:.3f} {y:.3f}" for i, (x, y) in enumerate(points))
        color = COLORS[index % len(COLORS)]
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
        x, y = points[-1]
        parts.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="4" fill="{color}"/>')
        parts.append(f'<text x="{36 + (index % 3) * 300}" y="{580 + (index // 3) * 25}" font-family="sans-serif" font-size="15" fill="{color}">{escape(item["name"])}</text>')
    labels = [f"X: {axes[0]}", f"Y: {axes[1]}", f"Z: {axes[2]}"]
    parts.append(f'<text x="36" y="105" font-family="sans-serif" font-size="14" fill="#526174">{escape("  |  ".join(labels))}</text>')
    parts.append('<text x="36" y="635" font-family="sans-serif" font-size="12" fill="#68788a">Artificial dimensionless software fixture; not biological data or a machine-control view.</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_html(source):
    axes = source["axes"]
    defaults = [axis for axis in ("dimensionless_time", "bulk_stock", "progression") if axis in axes]
    defaults += [axis for axis in axes if axis not in defaults][:3 - len(defaults)]
    data = {"axes": axes, "defaults": defaults, "colors": COLORS,
            "series": [{"name": item["name"],
                        "points": [[row[axis] for axis in axes] for row in item["rows"]]}
                       for item in source["series"]]}
    encoded = json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    options = "".join(f'<option value="{escape(axis)}">{escape(axis.replace("_", " "))}</option>' for axis in axes)
    variants = "".join(
        f'<label class="variant"><input type="checkbox" data-variant="{index}" checked> '
        f'<span style="--color:{COLORS[index % len(COLORS)]}"></span>{escape(item["name"])}</label>'
        for index, item in enumerate(source["series"]))
    template = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dimensionless twin 3D trajectories</title>
<style>
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#172536;background:#f3f6fa}
*{box-sizing:border-box}body{margin:0;padding:28px}main{max-width:1250px;margin:auto}h1{font-size:26px;margin:0 0 8px}p{line-height:1.5;color:#526174}.notice{background:#fff8df;border:1px solid #e6d79b;padding:12px 16px;border-radius:8px;font-size:14px}.panel{background:white;border:1px solid #d9e0e9;border-radius:12px;padding:18px;margin-top:18px;box-shadow:0 3px 14px #1725360a}.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:end}.control{display:grid;gap:5px;font-size:13px;color:#526174}select,button{font:inherit;padding:8px 10px;border:1px solid #bcc8d6;border-radius:6px;background:white;color:#172536}button{cursor:pointer}button:hover{background:#edf3f9}.variants{display:flex;gap:14px;flex-wrap:wrap;margin-top:16px}.variant{display:flex;align-items:center;gap:6px;font-size:14px}.variant span{width:12px;height:12px;border-radius:50%;background:var(--color)}#plot{display:block;width:100%;height:auto;min-height:360px;background:#f7f9fc;border-radius:8px;margin-top:16px;touch-action:none;cursor:grab}#plot:active{cursor:grabbing}.hint{font-size:13px;margin-bottom:0}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}#readout{font-variant-numeric:tabular-nums;font-size:13px;min-height:1.5em}noscript{display:block;margin-top:16px}a{color:#1769aa}@media(max-width:650px){body{padding:14px}.controls{display:grid;grid-template-columns:1fr 1fr}.panel{padding:12px}h1{font-size:22px}}
</style></head><body><main>
<h1>Dimensionless twin trajectories in 3D</h1>
<p>Explore the published software trajectories as three selected quantities. Each axis is scaled independently for visibility; distances between axes are not physical distances.</p>
<div class="notice">__NOTICE__ No biological measurements, physiological calibration, health assessment or machine-control output.</div>
<section class="panel" aria-label="3D trajectory controls">
<div class="controls">
<label class="control">X axis<select id="x">__OPTIONS__</select></label>
<label class="control">Y axis<select id="y">__OPTIONS__</select></label>
<label class="control">Z axis<select id="z">__OPTIONS__</select></label>
<button id="reset" type="button">Reset view</button><button id="download" type="button">Download SVG</button>
</div>
<div class="variants" aria-label="Visible variants">__VARIANTS__</div>
<svg id="plot" viewBox="0 0 1000 650" role="img" aria-labelledby="plot-title plot-desc" tabindex="0">
<title id="plot-title">Interactive three-dimensional twin trajectories</title><desc id="plot-desc">Drag to rotate, use the mouse wheel to zoom, or use arrow keys to rotate and plus or minus to zoom.</desc>
</svg>
<p id="readout" aria-live="polite"></p>
<p class="hint">Drag to rotate · Scroll to zoom · Arrow keys rotate · +/− zoom · Hover a trajectory for values. <a href="trajectory.svg">Static SVG preview</a></p>
<noscript>JavaScript is disabled. Use the <a href="trajectory.svg">static 3D SVG preview</a>; no network access is needed.</noscript>
</section>
</main><script id="trajectory-data" type="application/json">__DATA__</script>
<script>
'use strict';
const data=JSON.parse(document.getElementById('trajectory-data').textContent);
const svg=document.getElementById('plot'), NS='http://www.w3.org/2000/svg';
const selectors=['x','y','z'].map(id=>document.getElementById(id));
let yaw=-0.65,pitch=0.48,zoom=1,drag=null,hover=null;
const visible=data.series.map(()=>true);
function node(name,attrs,text){const e=document.createElementNS(NS,name);for(const [k,v] of Object.entries(attrs||{}))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;}
function extent(axis){let lo=Infinity,hi=-Infinity;for(const s of data.series)for(const p of s.points){lo=Math.min(lo,p[axis]);hi=Math.max(hi,p[axis]);}if(lo===hi){const d=Math.max(Math.abs(lo)*.05,.5);lo-=d;hi+=d;}return[lo,hi];}
function project(p,extents){const c=p.map((v,i)=>2*(v-extents[i][0])/(extents[i][1]-extents[i][0])-1);const[x,y,z]=c;const h=x*Math.cos(yaw)-y*Math.sin(yaw),d=x*Math.sin(yaw)+y*Math.cos(yaw),v=z*Math.cos(pitch)-d*Math.sin(pitch);return[500+h*320*zoom,344.5-v*234*zoom];}
function draw(){const axes=selectors.map(s=>Number(s.value)),extents=axes.map(extent);svg.querySelectorAll('.generated').forEach(e=>e.remove());
 const corners=[];for(const x of[0,1])for(const y of[0,1])for(const z of[0,1])corners.push([x,y,z]);
 for(const a of corners)for(const b of corners){if(a.reduce((n,v,i)=>n+(v!==b[i]),0)!==1)continue;const p=project(a,extents),q=project(b,extents);svg.append(node('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'#c7d0dc','stroke-width':1,class:'generated'}));}
 const title=node('text',{x:32,y:36,'font-size':19,'font-weight':600,fill:'#172536',class:'generated'},'3D projection · independently normalized axes');svg.append(title);
 const labels=node('text',{x:32,y:62,'font-size':14,fill:'#526174',class:'generated'},axes.map((a,i)=>'XYZ'[i]+': '+data.axes[a]).join('  |  '));svg.append(labels);
 data.series.forEach((s,i)=>{if(!visible[i])return;const points=s.points.map(p=>project(axes.map(a=>p[a]),extents));const d=points.map((p,j)=>(j?'L':'M')+p[0].toFixed(2)+' '+p[1].toFixed(2)).join(' ');const path=node('path',{d,fill:'none',stroke:data.colors[i],'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round',class:'generated'});svg.append(path);
  points.forEach((p,j)=>{if(j%Math.max(1,Math.floor(points.length/80))!==0&&j!==points.length-1)return;const dot=node('circle',{cx:p[0],cy:p[1],r:7,fill:'transparent',class:'generated',tabindex:-1});dot.addEventListener('pointerenter',()=>{hover={s,i,j,p};draw();});dot.addEventListener('pointerleave',()=>{hover=null;draw();});svg.append(dot);});
  const end=points[points.length-1];svg.append(node('circle',{cx:end[0],cy:end[1],r:4,fill:data.colors[i],class:'generated'}));});
 if(hover){const{s,i,j,p}=hover;svg.append(node('circle',{cx:p[0],cy:p[1],r:6,fill:'white',stroke:data.colors[i],'stroke-width':3,class:'generated'}));document.getElementById('readout').textContent=s.name+' · '+axes.map((a,k)=>'XYZ'[k]+' '+data.axes[a]+' = '+s.points[j][a]).join(' · ');}else document.getElementById('readout').textContent='';
}
function reset(){yaw=-.65;pitch=.48;zoom=1;selectors.forEach((s,i)=>s.value=data.defaults[i]);visible.fill(true);document.querySelectorAll('[data-variant]').forEach(c=>c.checked=true);draw();}
selectors.forEach(s=>s.addEventListener('change',draw));document.getElementById('reset').addEventListener('click',reset);
document.querySelectorAll('[data-variant]').forEach(c=>c.addEventListener('change',()=>{visible[Number(c.dataset.variant)]=c.checked;draw();}));
svg.addEventListener('pointerdown',e=>{if(e.target.tagName==='circle')return;drag={x:e.clientX,y:e.clientY};svg.setPointerCapture(e.pointerId);});
svg.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-drag.x)*.008;pitch=Math.max(-1.4,Math.min(1.4,pitch+(e.clientY-drag.y)*.008));drag={x:e.clientX,y:e.clientY};draw();});
svg.addEventListener('pointerup',()=>drag=null);svg.addEventListener('pointercancel',()=>drag=null);
svg.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.45,Math.min(2.5,zoom*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
svg.addEventListener('keydown',e=>{const keys={ArrowLeft:()=>yaw-=.1,ArrowRight:()=>yaw+=.1,ArrowUp:()=>pitch=Math.min(1.4,pitch+.1),ArrowDown:()=>pitch=Math.max(-1.4,pitch-.1),'+':()=>zoom=Math.min(2.5,zoom*1.1),'=':()=>zoom=Math.min(2.5,zoom*1.1),'-':()=>zoom=Math.max(.45,zoom/1.1)};if(keys[e.key]){e.preventDefault();keys[e.key]();draw();}});
document.getElementById('download').addEventListener('click',()=>{const blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='twin-trajectory-view.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),0);});
reset();
</script></body></html>
'''
    return (template.replace("__NOTICE__", escape(NOTICE))
            .replace("__OPTIONS__", options).replace("__VARIANTS__", variants)
            .replace("__DATA__", encoded))


def publish_visualization(bundle, output):
    source = load_twin_bundle(bundle)
    svg = render_svg(source["series"])
    files = {
        "index.html": render_html(source).encode("utf-8"),
        "trajectory.svg": svg.encode("utf-8"),
        "source_receipt.json": source["receipt_raw"],
        "visualization_report.json": json_bytes({
            "schema_version": 1,
            "result_kind": "dimensionless_twin_3d_visualization",
            "fixture_notice": NOTICE,
            "source_bundle_kind": source["kind"],
            "source_receipt_sha256": sha256(source["receipt_raw"]),
            "source_strictly_verified": True,
            "variants": [item["name"] for item in source["series"]],
            "axes": source["axes"],
            "samples_per_variant": {item["name"]: len(item["rows"]) for item in source["series"]},
            "external_resources": False,
            "biological_measurements": False,
            "physiologically_calibrated": False,
            "human_gestation_prediction": False,
            "limits": [
                "Three selected dimensionless quantities are independently normalized for display.",
                "Projection, rotation and zoom change presentation only, not model values or scientific meaning.",
                "This is a software trajectory view, not biological data, a physical reconstruction or a machine-control interface.",
            ],
        }),
        "reproduction_plan.json": json_bytes({
            "schema_version": 1,
            "bundle_kind": "dimensionless_twin_3d_visualization",
            "declared_dependencies": ["Python standard library and this project; browser for optional interaction"],
            "command": "wombmodels visualize-twin --bundle <source-twin-bundle> --out <new-dir>",
            "inputs": ["source_receipt.json", "receipt-declared source trajectory CSV files (not duplicated)"],
            "expected_outputs": ["index.html", "receipt.json", "reproduction_plan.json",
                                 "source_receipt.json", "trajectory.svg", "visualization_report.json"],
            "limits": ["Source integrity is checked before rendering; visualization does not rerun or validate the model.",
                       "Every displayed value is dimensionless and synthetic."],
        }),
    }
    return publish_bundle(Path(output), kind="dimensionless_twin_3d_visualization",
                          input_raw=source["receipt_raw"], files=files,
                          metadata={"biological_measurements": False,
                                    "physiologically_calibrated": False,
                                    "human_gestation_prediction": False,
                                    "n_variants": len(source["series"]),
                                    "parent_receipt_file": "source_receipt.json",
                                    "parent_receipt_sha256": sha256(source["receipt_raw"])})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    publish_visualization(args.bundle, args.out)
