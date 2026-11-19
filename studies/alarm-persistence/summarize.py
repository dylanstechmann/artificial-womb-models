"""Summarize whole-window control alarms and paired offset detections from a stress replay."""
import csv
import sys
from collections import Counter
from pathlib import Path

def summarize(rows):
    groups = {}
    for row in rows:
        for rule in ("current", "separate_two", "separate_three"):
            key = row["rho"], row["case"], row["duration"], rule
            group = groups.setdefault(key, Counter())
            group["runs"] += 1
            outcome = row[f"{rule}_outcome"]
            if outcome == "false_alarm":
                group["false_alarms"] += 1
            if outcome == "detected":
                group["endpoint_inclusive"] += 1
                group["before_end"] += float(row[f"{rule}_alarm"]) < float(row["end"])
    for (rho, case, duration, rule), group in sorted(groups.items()):
        yield [rho, case, duration, rule, group["runs"], group["false_alarms"] if case == "control" else "",
               group["endpoint_inclusive"] if case == "offset" else "", group["before_end"] if case == "offset" else ""]

if __name__ == "__main__":
    with Path(sys.argv[1]).open(encoding="utf-8", newline="") as records:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["rho", "case", "duration", "rule", "runs", "false_alarms", "endpoint_inclusive", "before_end"])
        writer.writerows(summarize(csv.DictReader(records)))
