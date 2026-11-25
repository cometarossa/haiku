#!/usr/bin/env python3
"""Strict V18 per-view diagnostic validation; not a presentation FPS meter."""
import argparse
import json
import re
from pathlib import Path

OUTCOMES = "null looper_fail bitmap_fail overlay invalidate draw".split()
PHASES = "update_us looper_us bitmap_us overlay_us invalidate_us draw_us".split()
FIELDS = ["calls", *OUTCOMES, "total_us", *PHASES]


def parse(text):
    rows = []
    for line in text.splitlines():
        if "LAB_VIDEO_VIEW" not in line:
            continue
        match = re.fullmatch(r"LAB_VIDEO_VIEW (.*)", line)
        if not match:
            raise ValueError("interleaved or malformed view record")
        fields = [re.fullmatch(r"([a-z_]+)=([0-9]+)", f)
                  for f in match.group(1).split()]
        if any(f is None for f in fields) or [f.group(1) for f in fields] != FIELDS:
            raise ValueError("invalid view fields")
        row = {f.group(1): int(f.group(2)) for f in fields}
        if row["calls"] != sum(row[k] for k in OUTCOMES):
            raise ValueError("view outcome conservation failure")
        if row["total_us"] < sum(row[k] for k in PHASES):
            raise ValueError("view timing conservation failure")
        for outcome in ("draw", "invalidate"):
            if not row[outcome] and row[outcome+"_us"]:
                raise ValueError("time without outcome")
        if not row["calls"] and row["total_us"]:
            raise ValueError("time without invocation")
        rows.append(row)
    return rows


def summarize(rows, expected, enabled=True):
    if not enabled:
        if rows:
            raise ValueError("unexpected view records with marker OFF")
        return {}
    if len(rows) != expected or not rows:
        raise ValueError("unexpected view lifetime count")
    totals = {key: sum(r[key] for r in rows) for key in FIELDS}
    if totals["calls"] == 0:
        raise ValueError("no sampled view activity")
    totals["records"] = len(rows)
    totals["unattributed_us"] = totals["total_us"] - sum(totals[k] for k in PHASES)
    return totals


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("log", type=Path)
    p.add_argument("--views", type=int, required=True)
    p.add_argument("--off", action="store_true")
    a = p.parse_args()
    print(json.dumps(summarize(parse(a.log.read_text()), a.views, not a.off), indent=2))
