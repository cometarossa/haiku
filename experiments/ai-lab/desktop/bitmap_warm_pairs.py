#!/usr/bin/env python3
"""Validate completed balanced blocks; report paired ratios, not pooled speedups."""
import argparse
import csv
import re
import statistics
import sys
from pathlib import Path

from bitmap_warm_report import read_run

MATRIX = [("threads", 2), ("teams", 2), ("threads", 4), ("teams", 4)]
STATES = ("off", "warm", "single", "warm", "single", "off",
          "single", "off", "warm")
METRICS = ("render_us", "lifecycle_us", "max_setup_us")


def completed(root, revision, partial=False):
    order = [(mode, n, state) for mode, n in MATRIX for state in STATES]
    names = [f"{i:02d}-{mode}-{n}-64-{state}"
             for i, (mode, n, state) in enumerate(order)]
    actual = sorted(p.name for p in root.iterdir() if p.is_dir())
    if actual != names[:len(actual)]:
        raise ValueError("unexpected or nonconsecutive runs")
    rows = []
    for i, ((mode, n, state), name) in enumerate(zip(order, actual)):
        folder = root / name
        if not (folder / "profile.json").is_file() or not (folder / "serial-final.txt").is_file():
            if i != len(actual) - 1:
                raise ValueError("incomplete interior run")
            break
        rows.append(read_run(folder, revision, i, mode, n, state))
    if not partial and len(rows) != len(order):
        raise ValueError("campaign incomplete")
    return rows


def paired(rows):
    groups = {}
    for i in range(0, len(rows) - 2, 3):
        block = rows[i:i+3]
        mode, n = block[0]["mode"], block[0]["surfaces"]
        if any((r["mode"], r["surfaces"]) != (mode, n) for r in block):
            raise ValueError("mixed block")
        states = {r["flag"]: r for r in block}
        if set(states) != {"off", "warm", "single"}:
            raise ValueError("invalid block")
        for metric in METRICS:
            for a, b in (("warm", "off"), ("single", "off"), ("single", "warm")):
                x, y = states[a][metric], states[b][metric]
                if y <= 0:
                    raise ValueError("invalid denominator")
                groups.setdefault((mode, n, metric, a, b), []).append(x / y)
    for (mode, n, metric, a, b), ratios in groups.items():
        yield dict(mode=mode, surfaces=n, metric=metric, treatment=a, reference=b,
                   blocks=len(ratios), median_ratio=round(statistics.median(ratios), 4),
                   min_ratio=round(min(ratios), 4), max_ratio=round(max(ratios), 4),
                   wins=sum(r < 1 for r in ratios))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("revision")
    p.add_argument("--partial", action="store_true")
    args = p.parse_args()
    if not re.fullmatch("[0-9a-f]{8}", args.revision):
        p.error("invalid revision")
    rows = completed(args.root, args.revision, args.partial)
    print(f"Validated {len(rows)}/36 runs; partial={len(rows)!=36}", file=sys.stderr)
    output = list(paired(rows))
    if not output:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=list(output[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(output)


if __name__ == "__main__":
    main()
