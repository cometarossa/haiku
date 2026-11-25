#!/usr/bin/env python3
"""Parse native listport snapshots; sampled fullness is not a blocked-write count."""
import argparse
import json
import re
from pathlib import Path


def parse(text, team):
    current = None
    result = {}
    seen_team = False
    for line in text.splitlines():
        match = re.fullmatch(r"TEAM\s+(\d+)\s+\((.*)\):", line)
        if match:
            current = int(match.group(1))
            if current == team:
                if seen_team:
                    raise ValueError("duplicate team")
                seen_team = True
            continue
        if current != team:
            continue
        if not line.strip() or line.strip().startswith(("ID ", "---", "port:")):
            continue
        m = re.fullmatch(r"\s*(\d+)\s+(.*?)\s+(\d+)\s+(\d+)\s*", line)
        if not m:
            raise ValueError("malformed port row")
        pid, name, capacity, queued = m.groups()
        pid, capacity, queued = map(int, (pid,capacity,queued))
        if not capacity or queued>capacity or pid in result:
            raise ValueError("invalid queue depth or port identity")
        result[pid] = dict(name=name.strip(),capacity=capacity,queued=queued)
    if not seen_team or not result:
        raise ValueError("requested team or ports missing")
    return result


def summarize(snapshots, team):
    if not snapshots:
        raise ValueError("no snapshots")
    ports={}
    previous=None
    for timestamp,text in snapshots:
        if previous is not None and timestamp<=previous:
            raise ValueError("nonmonotonic snapshot")
        previous=timestamp
        for pid,row in parse(text,team).items():
            stat=ports.setdefault(pid,dict(name=row["name"],capacity=row["capacity"],
                observations=0,full=0,max_queued=0))
            if stat["capacity"]!=row["capacity"] or stat["name"]!=row["name"]:
                raise ValueError("port identity changed; do not merge lifetimes")
            stat["observations"]+=1
            stat["full"]+=row["queued"]==row["capacity"]
            stat["max_queued"]=max(stat["max_queued"],row["queued"])
    return dict(team=team,snapshots=len(snapshots),ports=ports)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("--team",type=int,required=True)
    a=p.parse_args()
    # Filename stores guest monotonic microseconds; keep the raw output intact.
    files=sorted(a.root.glob("port-*.txt"),key=lambda f:int(f.stem.split("-")[1]))
    print(json.dumps(summarize([(int(f.stem.split("-")[1]),f.read_text())
        for f in files],a.team),indent=2))
