"""Download the public files identified by the audit manifest."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

def read_input(item):
    url = item["url"]
    for attempt in range(2):
        try:
            with urlopen(Request(url, headers={"User-Agent": "artificial-womb-models/source-audit"}), timeout=60) as source:
                data = source.read(item["bytes"] + 1)
            break
        except HTTPError as exc:
            # A cached Figshare redirect can contain an expired storage signature.
            if attempt or exc.code not in (400, 403) or "figshare.com/" not in url:
                raise
            url += f"?download={time.time_ns()}"
    if item.get("normalization"):
        header, *rows = data.splitlines()
        data = b"\n".join([header, *sorted(rows)]) + b"\n"
    if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError(f"Archive metadata or file changed for {item['file']}, check the source before refreshing its digest")
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name("inputs.json").read_bytes())
    files = [(item["file"], read_input(item)) for item in manifest]
    args.directory.mkdir(parents=True, exist_ok=False)
    for name, content in files:
        (args.directory / name).write_bytes(content)
