#!/usr/bin/env python3
"""Revalidate completed V11 lifecycle campaigns and emit CSV summaries."""
import argparse
import csv
import json
import re
import statistics
import sys
from pathlib import Path

from bitmap_warm_smoke import parse, verify_client, verify_single_clear


def collect(root, revision, matrix, single_clear=False, three_way=False, setup_phases=False):
    states = ("off", "warm", "single", "warm", "single", "off",
              "single", "off", "warm") if three_way else ("off", "on", "on", "off", "off", "on")
    order = [(mode, n, state) for mode, n in matrix for state in states]
    expected = {f"{i:02d}-{mode}-{n}-64-{state}"
                for i, (mode, n, state) in enumerate(order)}
    actual = {p.name for p in root.iterdir() if p.is_dir()}
    if actual != expected:
        raise ValueError(f"incomplete/unexpected campaign: missing={expected-actual}, extra={actual-expected}")
    rows = []
    for i, (mode, n, state) in enumerate(order):
        folder = root / f"{i:02d}-{mode}-{n}-64-{state}"
        rows.append(read_run(folder, revision, i, mode, n, state, single_clear, setup_phases))
    return rows



def read_run(folder, revision, i, mode, n, state, single_clear=False, setup_phases=False):
    if ((folder / "exit.txt").read_text().strip() != "0"
            or (folder / "errors.txt").read_text().strip()
            or not re.search(r"(?<![0-9a-f])ai_" + re.escape(revision) + r"(?![0-9a-f])",
                             (folder / "revision.txt").read_text())):
        raise ValueError(f"failed execution/revision: {folder.name}")
    data = (folder / "result.csv").read_text()
    if setup_phases:
        from bitmap_setup_phases import verify_phases
        measured, phases = verify_phases(data, mode, n, 64)
        if phases != json.loads((folder / "setup-phases.json").read_text()):
            raise ValueError(f"phase evidence mismatch: {folder.name}")
    else:
        measured = verify_client(data, mode, n, 64)
    count = n if state != "off" else 0
    records = parse((folder / "serial.txt").read_text(), count, mode)
    final = parse((folder / "serial-final.txt").read_text(), count, mode)
    verify_single_clear((folder / "serial.txt").read_text(), records,
                        state == "single" or (single_clear and state == "on"))
    verify_single_clear((folder / "serial-final.txt").read_text(), final,
                        state == "single" or (single_clear and state == "on"))
    if records != final or records != json.loads((folder / "profile.json").read_text()):
        raise ValueError(f"serial/profile discrepancy: {folder.name}")
    return dict(run=i, mode=mode, surfaces=n, batch=64, flag=state,
                     **measured, warm_records=count,
                     warm_total_us=sum(r["us"] for r in records))

def summarize(rows):
    groups = {}
    for row in rows:
        groups.setdefault((row["mode"], row["surfaces"], row["flag"]), []).append(row)
    for (mode, n, state), group in groups.items():
        if len(group) != 3:
            raise ValueError("expected three independent observations")
        yield dict(mode=mode, surfaces=n, flag=state,
                   **{"median_" + field: statistics.median(r[field] for r in group)
                      for field in ("render_us", "lifecycle_us", "max_setup_us", "warm_total_us")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("revision")
    parser.add_argument("--two-surface", action="store_true")
    parser.add_argument("--single-clear", action="store_true")
    parser.add_argument("--three-way", action="store_true")
    parser.add_argument("--setup-phases", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch("[0-9a-f]{8}", args.revision):
        parser.error("invalid revision")
    matrix = [("threads", 2), ("teams", 2)] if args.two_surface else [
        ("threads", 4), ("teams", 4), ("threads", 1)]
    if args.setup_phases and not args.three_way:
        parser.error("--setup-phases requires --three-way")
    if args.three_way:
        if args.two_surface or args.single_clear:
            parser.error("--three-way is a separate campaign")
        matrix = [("threads", 2), ("teams", 2), ("threads", 4), ("teams", 4)]
    rows = list(summarize(collect(args.root, args.revision, matrix, args.single_clear, args.three_way, args.setup_phases)))
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
