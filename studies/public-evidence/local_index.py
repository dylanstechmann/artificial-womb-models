"""Connect searchable citations to tracked source records by literal identifiers."""
import csv
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def build():
    with (HERE / "bibliography/records.tsv").open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream, delimiter="\t"))
    with (HERE / "studies.tsv").open(encoding="utf-8", newline="") as stream:
        curated = list(csv.DictReader(stream, delimiter="\t"))
    dois = {r["doi"].lower() for r in records if r["doi"]}
    dois.update(r["primary_url"].removeprefix("https://doi.org/").lower() for r in curated
                if r["primary_url"].startswith("https://doi.org/"))
    pattern = re.compile(r"(?:" + "|".join(re.escape(d) for d in sorted(dois, key=lambda x: (-len(x), x)))
                         + r")(?![a-z0-9_.-])", re.IGNORECASE)
    paths = [ROOT / "config/evidence.json"]
    for directory in ("observations", "source_inventories", "perfusion_observations"):
        paths.extend(sorted((ROOT / "config" / directory).glob("*")))
    for path in paths:
        if path.is_file() and path.suffix in {".csv", ".json"}:
            matches = sorted({m.group().lower() for m in pattern.finditer(path.read_text(encoding="utf-8"))})
            yield {"repo_path": path.relative_to(ROOT).as_posix(), "matched_dois": " ".join(matches)}

if __name__ == "__main__":
    import sys
    writer = csv.DictWriter(sys.stdout, ("matched_dois", "repo_path"), delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(build())
