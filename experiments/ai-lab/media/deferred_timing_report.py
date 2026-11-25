"""Aggregate elapsed notification and handler phases, never CPU or FPS."""
import re
from v19_deferred_report import deferred_records

KEYS = ("queue_us","handler_us","bitmap_us","draw_us")


def summarize_timing(text, expected):
    rows=[]
    for line in text.splitlines():
        if "LAB_VIDEO_DEFERRED_TIMING" not in line:
            continue
        match=re.fullmatch(r"LAB_VIDEO_DEFERRED_TIMING "+" ".join(k+r"=(\d+)" for k in KEYS),line)
        if not match:
            raise ValueError("malformed timing record")
        row=dict(zip(KEYS,map(int,match.groups())))
        if row["bitmap_us"]+row["draw_us"]>row["handler_us"]:
            raise ValueError("handler phase conservation")
        rows.append(row)
    if len(rows)!=expected:
        raise ValueError("timing record count")
    if not expected:
        return {}
    deferred=deferred_records(text)
    if len(deferred)!=expected:
        raise ValueError("notification record count")
    total={k:sum(r[k] for r in rows) for k in KEYS}
    handled=sum(r["handled"] for r in deferred)
    total["handled"]=handled
    total["mean_queue_us"]=total["queue_us"]/handled if handled else None
    total["mean_handler_us"]=total["handler_us"]/handled if handled else None
    return total
