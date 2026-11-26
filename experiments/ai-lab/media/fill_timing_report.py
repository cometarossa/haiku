"""Validate per-producer fill outcome elapsed-time conservation."""
import re
from media_stats_report import parse

OUTCOMES=("ok","cached","timeout","end","error")
FIELDS=("thread",)+OUTCOMES+tuple(x+"_us" for x in OUTCOMES)
PATTERN=re.compile("LAB_MEDIA_FILL_TIMING "+" ".join(k+r"=(\d+)" for k in FIELDS))


def validate(text,enabled=True):
    producers=parse(text)["PRODUCER"]
    rows=[]
    for line in text.splitlines():
        if "LAB_MEDIA_FILL_TIMING" not in line:
            continue
        m=PATTERN.fullmatch(line)
        if not m:
            raise ValueError("malformed fill timing")
        rows.append(dict(zip(FIELDS,map(int,m.groups()))))
    if not enabled:
        if rows:raise ValueError("unexpected timing")
        return []
    by_thread={r["thread"]:r for r in producers}
    if not rows or len(by_thread)!=len(producers) or len(rows)!=len(by_thread) or {r["thread"] for r in rows}!=set(by_thread):
        raise ValueError("thread coverage")
    for r in rows:
        p=by_thread[r["thread"]]
        if sum(r[k] for k in OUTCOMES)!=p["fills"] or sum(r[k+"_us"] for k in OUTCOMES)!=p["fill_us"]:
            raise ValueError("fill conservation")
        if (r["timeout"],r["end"],r["error"])!=(p["fill_timeouts"],p["end_buffers"],p["fill_errors"]):
            raise ValueError("outcome conservation")
        if any(r[k]==0 and r[k+"_us"] for k in OUTCOMES):
            raise ValueError("elapsed without calls")
    return rows
