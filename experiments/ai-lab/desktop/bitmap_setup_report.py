#!/usr/bin/env python3
"""Revalidate a complete instrumented campaign and export paired phase deltas."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

from bitmap_warm_report import collect
from bitmap_warm_pairs import MATRIX
from bitmap_setup_phases import paired_phase_deltas


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("revision")
    args = p.parse_args()
    if not re.fullmatch("[0-9a-f]{8}", args.revision):
        p.error("invalid revision")
    rows = collect(args.root, args.revision, MATRIX, three_way=True, setup_phases=True)
    for r in rows:
        folder = args.root / f"{r['run']:02d}-{r['mode']}-{r['surfaces']}-64-{r['flag']}"
        r["phases"] = json.loads((folder / "setup-phases.json").read_text())
    out = [item for i in range(0,len(rows),3) for item in paired_phase_deltas(rows[i:i+3])]
    writer = csv.DictWriter(sys.stdout, fieldnames=list(out[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(out)


if __name__ == "__main__":
    main()
