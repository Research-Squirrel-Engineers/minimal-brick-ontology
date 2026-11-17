"""Fetch the Rebrickable CSV downloads (colours, part categories, parts).

This is the ONLY step that uses the network, and it is never part of the
default run: `python main.py fetch`. Files are stored unchanged (decompressed)
in data/raw/rebrickable/ together with a FETCHED.txt that records the source
URL, size, SHA-256 and the server's Last-Modified header (no local clock).
Run standalone: python py/step_fetch.py
"""
from __future__ import annotations

import gzip
import hashlib
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mbo_utils as U

BASE = "https://cdn.rebrickable.com/media/downloads/"
FILES = ["colors", "part_categories", "parts"]


def main() -> int:
    U.ensure_dirs()
    lines = ["Rebrickable CSV downloads, stored unchanged (decompressed).",
             "Source: https://rebrickable.com/downloads/ (free for any purpose per the dataset description; see README)."]
    for name in FILES:
        url = f"{BASE}{name}.csv.gz"
        print(f"fetching {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "minimal-brick-ontology/" + U.VERSION})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
                modified = resp.headers.get("Last-Modified", "unknown")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: could not fetch {url}: {exc}")
            print("Download the three files manually from https://rebrickable.com/downloads/ and unzip them into data/raw/rebrickable/")
            return 1
        data = gzip.decompress(raw)
        (U.RAW / f"{name}.csv").write_bytes(data)
        lines.append(f"{name}.csv  url={url}  bytes={len(data)}  sha256={hashlib.sha256(data).hexdigest()}  last-modified={modified}")
        print(f"  {name}.csv: {len(data)} bytes")
    U.write_text(U.RAW / "FETCHED.txt", "\n".join(lines))
    print("done. Now run: python main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
