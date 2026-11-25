#!/usr/bin/env python3
"""Validate persistent BMessenger probe logs, preserving failed requests."""
import argparse
import json
from pathlib import Path
from capacity_audit import latency_summary

OPS = ("Title", "IsPlaying", "Position")


def analyze(text, indices):
    lines = text.splitlines()
    if not 1 <= len(indices) <= 16 or len(set(indices)) != len(indices):
        raise ValueError("invalid window map")
    init = lines[0].split() if lines else []
    if len(init) != 2 or init[0] != "INIT" or int(init[1]) < 0:
        raise ValueError("invalid initialization")
    if len(lines) < 3:
        raise ValueError("truncated probe")
    start_line, end_line = lines[1].split(), lines[-1].split()
    if len(start_line) != 4 or start_line[0] != "START" or len(end_line) != 4 or end_line[0] != "END":
        raise ValueError("missing probe boundary")
    start, deadline, count = map(int, start_line[1:])
    end, attempted, errors = map(int, end_line[1:])
    if count != len(indices) or not 1000000 <= deadline-start <= 30000000 or end < start:
        raise ValueError("invalid deadline or count")
    expected = [(s, i, op) for s in (1, 2, 3) for i in indices for op in OPS]
    rows = []
    previous = start
    cursor = 0
    for line in lines[2:-1]:
        fields = line.split()
        if len(fields) != 8 or fields[0] != "QUERY":
            raise ValueError("malformed query")
        sample, index = map(int, fields[1:3])
        op = fields[3]
        before, after, status, value = map(int, fields[4:])
        if cursor >= len(expected) or (sample,index,op) != expected[cursor]:
            raise ValueError("query identity or order")
        if not previous <= before <= after <= end or before >= deadline:
            raise ValueError("invalid query clock")
        if status == 0 and ((op in ("Title","IsPlaying") and value not in (0,1))
                or (op == "Title" and value != 1)
                or (op == "Position" and value < 0)):
            raise ValueError("invalid successful reply")
        rows.append(dict(sample=sample,index=index,op=op,before=before,after=after,
                         status=status,value=value))
        previous=after
        cursor += 3 if op == "Title" and status != 0 else 1
    if attempted != len(rows) or errors != sum(r["status"] != 0 for r in rows):
        raise ValueError("inconsistent footer")
    if cursor < len(expected) and end < deadline:
        raise ValueError("unexpected early termination")
    positions = {i: [r["value"] for r in rows if r["index"] == i and r["op"] == "Position" and r["status"] == 0] for i in indices}
    advance = all(len(v)==3 and v[0]<v[1]<v[2] for v in positions.values())
    playing = sum(r["op"]=="IsPlaying" and r["status"]==0 and r["value"]==1 for r in rows)
    return dict(expected=len(expected),attempted=attempted,errors=errors,
        not_attempted=len(expected)-attempted,playing_replies=playing,
        all_positions_advance=advance,initialization_us=int(init[1]),
        elapsed_us=end-start,deadline_overrun_us=max(0,end-deadline),
        complete=attempted==len(expected) and errors==0,
        playback_valid=attempted==len(expected) and errors==0 and advance and playing==count*3,
        by_operation={op: latency_summary([r["after"]-r["before"] for r in rows if r["op"]==op])
                      for op in OPS if any(r["op"]==op for r in rows)})


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("log",type=Path)
    p.add_argument("window_map",type=Path)
    a=p.parse_args()
    indices=[int(l.split()[0]) for l in a.window_map.read_text().splitlines()]
    print(json.dumps(analyze(a.log.read_text(),indices),indent=2))
