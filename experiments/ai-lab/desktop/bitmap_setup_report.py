#!/usr/bin/env python3
"""Revalidate a complete instrumented campaign and export paired phase deltas."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

from bitmap_warm_pairs import completed
from bitmap_setup_phases import paired_phase_deltas


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("revision")
    p.add_argument("--partial", action="store_true", help="report only fully verified treatment blocks")
    args = p.parse_args()
    if not re.fullmatch("[0-9a-f]{8}", args.revision):
        p.error("invalid revision")
    rows = completed(args.root, args.revision, partial=args.partial, setup_phases=True)
    print(f"Validated {len(rows)}/36 phase runs; partial={len(rows)!=36}", file=sys.stderr)
    for r in rows:
        folder = args.root / f"{r['run']:02d}-{r['mode']}-{r['surfaces']}-64-{r['flag']}"
        r["phases"] = json.loads((folder / "setup-phases.json").read_text())
    out = [item for i in range(0,len(rows)-2,3) for item in paired_phase_deltas(rows[i:i+3])]
    if not out:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=list(out[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(out)


if __name__ == "__main__":
    main()
