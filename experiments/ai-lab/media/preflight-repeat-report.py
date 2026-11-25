#!/usr/bin/env python3
"""Verify native startup proxy polls and aggregate observed diagnostic events."""
import argparse
import csv
import statistics
import sys
from pathlib import Path

STATES = "off on on off off on on off off on on off".split()


def read_run(root, i, state):
    p = root / f"{i:02d}-{state}"
    def read(ext):
        return p.with_suffix("." + ext).read_text()
    if read("exit").strip() != "0":
        raise ValueError(f"{p.name}: player failed")
    start, previous, before, after, valid = map(int, read("timing").strip().split(","))
    polls = list(csv.DictReader(read("poll").splitlines()))
    if not polls or valid != 1 or not start <= previous <= before <= after:
        raise ValueError(f"{p.name}: invalid timing")
    last = start
    for index, row in enumerate(polls):
        a, b, pos = (int(row[k]) for k in ("before_us", "after_us", "position_us"))
        if not last <= a <= b or row["playing"] not in ("true", "false"):
            raise ValueError(f"{p.name}: nonmonotonic poll")
        positive = row["playing"] == "true" and pos > 0
        if positive != (index == len(polls) - 1):
            raise ValueError(f"{p.name}: inconsistent first positive observation")
        last = b
    if (int(polls[-1]["before_us"]), last) != (before, after):
        raise ValueError(f"{p.name}: timing/poll mismatch")
    expected_previous = int(polls[-2]["after_us"]) if len(polls) > 1 else start
    if previous != expected_previous:
        raise ValueError(f"{p.name}: previous poll mismatch")
    full, prequit = read("log"), read("prequit")
    if not full.startswith(prequit):
        raise ValueError(f"{p.name}: prequit log not a prefix")
    preflight = full.count("LAB_MEDIA_OVERLAY_PREFLIGHT")
    retry = full.count("trying without overlays")
    if (preflight, retry) != ((0, 1) if state == "off" else (1, 0)):
        raise ValueError(f"{p.name}: treatment mismatch")
    def count(text, needle):
        return text.lower().count(needle)
    return dict(run=i, state=state, startup_proxy_us=after-start,
                last_nonpositive_us=previous-start, query_us=after-before,
                position_us=int(polls[-1]["position_us"]), polls=len(polls),
                overlay_retry=retry, preflight=preflight,
                drop_messages=count(full,"videoproducer: dropped frame"),
                drop_visible_prequit=count(prequit,"videoproducer: dropped frame"),
                send_errors=count(full,"error sending buffer"),
                send_errors_visible_prequit=count(prequit,"error sending buffer"))


def collect(root, partial):
    if "ai_63cc5489" not in (root/"revision.txt").read_text():
        raise ValueError("wrong guest revision")
    rows = []
    for i, state in enumerate(STATES):
        p = root / f"{i:02d}-{state}.exit"
        if not p.exists():
            if partial:
                break
            raise ValueError("incomplete campaign")
        rows.append(read_run(root, i, state))
    if not partial and (root/"done.txt").read_text().strip() != "0":
        raise ValueError("missing successful completion")
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--partial", action="store_true")
    args = p.parse_args()
    rows = collect(args.root, args.partial)
    print(f"Verified {len(rows)}/12", file=sys.stderr)
    if not rows:
        return
    w = csv.DictWriter(sys.stdout,fieldnames=list(rows[0]),lineterminator="\n")
    w.writeheader();w.writerows(rows)
    ratios=[]
    for i in range(0,len(rows)-1,2):
        pair={r["state"]:r for r in rows[i:i+2]}
        ratios.append(pair["on"]["startup_proxy_us"]/pair["off"]["startup_proxy_us"])
    if ratios:
        print(f"Paired ON/OFF startup proxy ratio: median={statistics.median(ratios):.4f}, range={min(ratios):.4f}..{max(ratios):.4f}, wins={sum(r<1 for r in ratios)}/{len(ratios)}",file=sys.stderr)
    print("Log counts are observed messages, not total presentation losses; stdout may buffer.",file=sys.stderr)


if __name__ == "__main__":
    main()
