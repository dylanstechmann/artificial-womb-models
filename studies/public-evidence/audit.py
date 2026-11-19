"""Audit public ovine RNA count libraries and two raw human placental meshes offline."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent

def table(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, list(rows[0]), delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()

def samples(soft, ena):
    by_gsm = {}
    for line in soft.read_text(encoding="utf-8").splitlines():
        if line.startswith("^SAMPLE = "):
            gsm = line.split(" = ", 1)[1]
            by_gsm[gsm] = {"gsm": gsm}
        elif line.startswith("!Sample_title = "):
            by_gsm[gsm]["column"] = line.rsplit(", ", 1)[1]
        elif line.startswith("!Sample_characteristics_ch1 = "):
            name, value = line.split(" = ", 1)[1].split(": ", 1)
            by_gsm[gsm][name] = value
    with ena.open(encoding="utf-8", newline="") as stream:
        runs = list(csv.DictReader(stream, delimiter="\t"))
    keys = [r["sample_alias"] for r in runs]
    if len(set(keys)) != len(keys) or set(keys) != set(by_gsm):
        raise ValueError("GEO and ENA accessions do not match one to one")
    for row in runs:
        sample = by_gsm[row["sample_alias"]]
        sample.update(run=row["run_accession"], biosample=row["sample_accession"])
    return sorted(by_gsm.values(), key=lambda row: row["column"])

def count_audit(path, meta):
    with gzip.open(path, "rt", newline="") as stream:
        reader = csv.reader(stream)
        columns = next(reader)[1:]
        if sorted(columns) != [s["column"] for s in meta] or len(columns) != 36:
            raise ValueError("Count columns do not match the 36 annotated preparations")
        idx = {key: i for i, key in enumerate(columns)}
        genes, counts = set(), []
        for gene, *values in reader:
            row = list(map(int, values))
            if gene in genes or len(row) != len(columns) or min(row) < 0:
                raise ValueError(f"Invalid count row {gene}")
            genes.add(gene)
            counts.append(row)
    totals = list(map(sum, zip(*counts)))
    for sample in meta:
        sample["assigned_gene_counts"] = totals[idx[sample["column"]]]
        sample["paper_qc"] = "excluded_low_counts" if sample["column"] == "H4" else "retained"
    # Cerebellum has only one retained early control. Use the three balanced regions.
    subset = [s for s in meta if s["tissue"] != "cerebellum"]
    profiles = {s["column"]: [] for s in subset}
    for row in counts:
        cpm = {key: row[idx[key]] * 1_000_000 / totals[idx[key]] for key in profiles}
        if sum(value >= 1 for value in cpm.values()) >= 4:
            for key, value in cpm.items():
                profiles[key].append(math.log2(1 + value))
    results = []
    animal_distances = defaultdict(lambda: defaultdict(list))
    for sample in subset:
        if sample["experimental group"] != "Experimental":
            continue
        profile = profiles[sample["column"]]
        distances = defaultdict(list)
        for other in subset:
            group = other["experimental group"]
            if group != "Experimental" and other["tissue"] == sample["tissue"]:
                differences = [abs(x-y) for x, y in zip(profile, profiles[other["column"]], strict=True)]
                distance = mean(differences)
                distances[group].append(distance)
                animal_distances[sample["sheep"]][group, other["sheep"]].append(distance)
        if sorted(map(len, distances.values())) != [2, 2]:
            raise ValueError("Expected two animals in each reference group in this region")
        early, late = (mean(distances[g]) for g in ("Pre-term ctrl", "Late pre-term ctrl"))
        results.append(dict(animal=sample["sheep"], tissue=sample["tissue"],
                            mean_distance_early=round(early, 6), mean_distance_late=round(late, 6),
                            closer="late" if late < early else "early" if early < late else "tie"))
    animals = []
    for animal, comparisons in sorted(animal_distances.items()):
        if any(len(regions) != 3 for regions in comparisons.values()):
            raise ValueError("An animal is missing a region")
        early_refs = [mean(regions) for (group, _), regions in comparisons.items() if group == "Pre-term ctrl"]
        late_refs = [mean(regions) for (group, _), regions in comparisons.items() if group == "Late pre-term ctrl"]
        animals.append({"animal": animal, "regions": 3, "mean_distance_early": round(mean(early_refs), 6),
                        "mean_distance_late": round(mean(late_refs), 6),
                        "reference_pairs_favoring_late_of_four": sum(late < early for late in late_refs for early in early_refs)})
    return results, animals, len(genes), len(next(iter(profiles.values())))

def mesh_audit(path):
    raw = path.read_bytes()
    triangles, = struct.unpack_from("<I", raw, 80)
    if len(raw) != 84 + 50 * triangles:
        raise ValueError("Invalid binary STL length")
    vertices, degenerate = set(), 0
    for facet in struct.iter_unpack("<12fH", raw[84:]):
        a, b, c = facet[3:6], facet[6:9], facet[9:12]
        if not all(map(math.isfinite, (*a, *b, *c))):
            raise ValueError("Nonfinite STL vertex")
        vertices.update((a, b, c))
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        degenerate += all(u[i]*v[j] == u[j]*v[i] for i,j in ((0,1), (1,2), (2,0)))
    return {"file": path.name, "facets": triangles, "unique_xyz": len(vertices),
            "zero_area_facets": degenerate}

def doppler_audit(path):
    cases_by_site = defaultdict(set)
    pairs_by_site = Counter()
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            site, case = row["Doppler Label"], row["Case"]
            times = list(map(float, row["Time"].split(",")))
            speeds = list(map(float, row["Velocity"].split(",")))
            if len(times) != len(speeds) or not times or case in cases_by_site[site]:
                raise ValueError("Unpaired or repeated Doppler trace")
            if not all(map(math.isfinite, times + speeds)):
                raise ValueError("Nonfinite tracing value")
            cases_by_site[site].add(case)
            pairs_by_site[site] += len(times)
    return [{"site": site, "cases": len(cases), "time_velocity_pairs": pairs_by_site[site]}
            for site, cases in sorted(cases_by_site.items())]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = (HERE / "inputs.json").read_bytes()
    for item in json.loads(manifest):
        if hashlib.sha256((args.inputs / item["file"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Source changed: {item['file']}")
    meta = samples(args.inputs / "family.soft", args.inputs / "ena.tsv")
    results, animals, rows, retained = count_audit(args.inputs / "GSE275228_rawStarCounts.csv.gz", meta)
    meshes = [mesh_audit(args.inputs / f"Specimen1_{part}.stl") for part in ("Vasculature", "Villi")]
    outputs = {"samples.tsv": table(meta), "ovine_distances.tsv": table(results), "human_meshes.tsv": table(meshes)}
    outputs["ovine_animals.tsv"] = table(animals)
    outputs["human_traces.tsv"] = table(doppler_audit(args.inputs / "Dataset_S2.csv"))
    receipt = {"input_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
               "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "count_rows": rows, "genes_compared": retained, "counts_by_closer_reference": dict(Counter(r["closer"] for r in results)),
               "outputs_sha256": {name: hashlib.sha256(data).hexdigest() for name,data in outputs.items()}}
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in outputs.items():
        (args.output / name).write_bytes(data)
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
