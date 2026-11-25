"""Strict per-track timeout categories, excluding calls without a supplier."""
import re

KEYS="calls cached gap_timeout seek_timeout read_timeout other_errors success gap_frames max_gap".split()

def parse(text):
    rows=[]
    for line in text.splitlines():
        if "LAB_VIDEO_PROXY" not in line:
            continue
        m=re.fullmatch("LAB_VIDEO_PROXY "+" ".join(k+r"=(\d+)" for k in KEYS),line)
        if not m:
            raise ValueError("malformed proxy record")
        r=dict(zip(KEYS,map(int,m.groups())))
        if r["calls"]!=sum(r[k] for k in KEYS[1:7]):
            raise ValueError("outcome conservation")
        if r["gap_timeout"]:
            if not 6<=r["max_gap"]<=r["gap_frames"]<=r["gap_timeout"]*r["max_gap"] or r["gap_frames"]<6*r["gap_timeout"]:
                raise ValueError("gap conservation")
        elif r["max_gap"] or r["gap_frames"]:
            raise ValueError("gap without timeout")
        rows.append(r)
    return rows

def summarize(rows,expected):
    if len(rows)!=expected:
        raise ValueError("proxy record count")
    if not rows:return {}
    result={k:sum(r[k] for r in rows) for k in KEYS if k!="max_gap"}
    result["max_gap"]=max(r["max_gap"] for r in rows)
    result["records"]=len(rows)
    result["timeouts"]=sum(result[k] for k in ("gap_timeout","seek_timeout","read_timeout"))
    return result
