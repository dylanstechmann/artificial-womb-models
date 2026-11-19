"""Download a dated bibliography from Europe PMC. Indexed records are candidates for review."""
import argparse
import csv
import io
import json
import time
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
QUERIES = {
    "device": '(TITLE_ABS:"artificial placenta" OR TITLE_ABS:"artificial womb" OR TITLE_ABS:"artificial uterus" OR TITLE_ABS:"ectogenesis" OR TITLE_ABS:"extrauterine environment for newborn development" OR TITLE_ABS:"extrauterine life support" OR TITLE_ABS:"extra-uterine life support" OR TITLE_ABS:"extra-uterine system" OR TITLE_ABS:"extrauterine physiology")',
    "early_development": '(TITLE_ABS:"human embryo" OR TITLE_ABS:"mouse embryo" OR TITLE_ABS:"monkey embryo" OR TITLE_ABS:"blastoid" OR TITLE_ABS:"embryo model") AND (TITLE_ABS:"postimplantation" OR TITLE_ABS:"peri-implantation" OR TITLE_ABS:"post-implantation" OR TITLE_ABS:"gastrulation") AND (TITLE_ABS:"in vitro" OR TITLE_ABS:"ex utero" OR TITLE_ABS:"ex vivo" OR TITLE_ABS:"stem cell-derived")',
    "human_placental_perfusion": '(TITLE_ABS:"human placenta" OR TITLE_ABS:"human placental" OR TITLE_ABS:"human cotyledon") AND (TITLE_ABS:"perfusion" OR TITLE_ABS:"perfused") AND (TITLE_ABS:"ex vivo" OR TITLE_ABS:"dual" OR TITLE_ABS:"dual-sided")',
    "computational": '(TITLE_ABS:"fetal circulation" OR TITLE_ABS:"placental transport" OR TITLE_ABS:"fetoplacental" OR TITLE_ABS:"feto-placental" OR TITLE_ABS:"placental blood flow") AND (TITLE_ABS:"computational" OR TITLE_ABS:"simulation" OR TITLE_ABS:"mathematical model" OR TITLE_ABS:"digital twin")',
}
FIELDS = ("source", "id", "pmid", "pmcid", "doi", "title", "pubYear", "pubType")

def fetch(parameters):
    url = API + "?" + urlencode(parameters)
    for attempt in range(3):
        try:
            with urlopen(url, timeout=45) as response:
                return json.load(response)
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def snapshot(cutoff):
    records, searches = {}, {}
    for label, expression in QUERIES.items():
        query = f"({expression}) AND FIRST_PDATE:[1800-01-01 TO {cutoff}]"
        params = dict(query=query, format="json", pageSize=500, cursorMark="*")
        found = set()
        visited = set()
        while True:
            if params["cursorMark"] in visited or len(visited) >= 50:
                raise ValueError(f"Search pagination exceeded its bound for {label}")
            visited.add(params["cursorMark"])
            page = fetch(params)
            hits = page["hitCount"]
            batch = page["resultList"]["result"]
            for item in batch:
                key = item["source"], item["id"]
                found.add(key)
                if key not in records:
                    records[key] = {f: item.get(f, "") for f in FIELDS} | {"searches": []}
                if label not in records[key]["searches"]:
                    records[key]["searches"].append(label)
            if len(found) == hits:
                break
            cursor = page.get("nextCursorMark")
            if not batch or not cursor or cursor == params["cursorMark"]:
                raise ValueError(f"Incomplete search for {label}: {len(found)} of {hits}")
            params["cursorMark"] = cursor
        searches[label] = {"query": query, "hits": hits}
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=(*FIELDS, "searches"), delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for key in sorted(records):
        record = records[key]
        writer.writerow(record | {"searches": ",".join(record["searches"])})
    return buffer.getvalue().encode(), searches, len(records)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cutoff", type=date.fromisoformat)
    p.add_argument("output", type=Path, help="new directory")
    args = p.parse_args()
    raw, searches, total = snapshot(args.cutoff)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "records.tsv").write_bytes(raw)
    receipt = {"api": API, "retrieved_utc": datetime.now(timezone.utc).date().isoformat(),
               "publication_cutoff": args.cutoff.isoformat(), "searches": searches,
               "unique_source_id_pairs": total, "records_sha256": sha256(raw).hexdigest(),
               "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
