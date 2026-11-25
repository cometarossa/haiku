#!/usr/bin/env python3
"""Inspect completed trials individually, including failed acceptance tests."""
import argparse
import json
import statistics
from pathlib import Path
from v16_catchup_report import SPECS_16, validate_run, query_latency
from media_stats_report import parse, summarize


def latency_summary(values):
    values=sorted(values)
    return dict(count=len(values), median_us=statistics.median(values),
                p95_us=values[(95*len(values)+99)//100-1],
                max_us=values[-1], total_us=sum(values))


def audit_trial(root, index, n, state):
    tag=f"{index:02d}-n{n}-{state}"
    def read(ext):
        return (root/(tag+"."+ext)).read_text()
    # Keep a failed acceptance result distinct from valid component data.
    try:
        validate_run(root,index,n,state,True,True)
        valid=True
        error=None
    except (ValueError, ZeroDivisionError) as e:
        valid=False
        error=str(e)
    result=dict(tag=tag,valid=valid,acceptance_error=error,
                exit=read("exit").strip())
    start,dispatch,play,stop,quit_time=(int(read(ext)) for ext in
        ("start","dispatch","play","stop","quit-time"))
    if not 0<start<dispatch<=play<stop<quit_time:
        raise ValueError("invalid lifetime timestamps")
    result.update(play_dispatch_us=play-dispatch,observation_us=stop-play,
                  lifetime_us=quit_time-start,stop_to_quit_us=quit_time-stop)
    windows=[tuple(map(int,l.split())) for l in read("windows").splitlines()]
    mapping=dict(windows)
    if len(windows)!=n or set(mapping)!=set(range(1,n+1)) or len(set(mapping.values()))!=n:
        raise ValueError("invalid window mapping")
    result["query_latency"]=query_latency(root,tag,mapping,play,stop)
    # query_latency has checked the identity, order, timestamps and exit.
    rows=[]
    for line in read("latency").splitlines():
        sample,win,op,a,b,rc=line.split()
        rows.append((int(sample),int(win),op,int(a),int(b)))
    result["latency_by_operation"]={op:latency_summary([b-a for _,_,o,a,b in rows if o==op])
        for op in ("title","playing","position")}
    result["sample_spans_us"]=[max(b for s,_,_,_,b in rows if s==i)-
                               min(a for s,_,_,a,_ in rows if s==i)
                               for i in (1,2,3)]
    positions=read("positions").splitlines()
    result["playing_replies"]=positions.count("true")
    result["not_playing_replies"]=positions.count("false")
    counters=summarize(parse(read("stderr")))
    if counters["producer"]["records"]!=n or counters["consumer"]["records"]!=n:
        raise ValueError("unexpected lifetime count")
    result.update(counters)
    return result


def audit(root):
    rows=[]
    for index,(n,state) in enumerate(SPECS_16):
        tag=f"{index:02d}-n{n}-{state}"
        if not (root/(tag+".exit")).exists():
            continue
        try:
            rows.append(audit_trial(root,index,n,state))
        except (ValueError, OSError, ZeroDivisionError) as e:
            rows.append(dict(tag=tag,valid=False,component_error=str(e)))
    return dict(completion_marker=(root/"done.txt").exists(),trials=rows)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    a=p.parse_args()
    print(json.dumps(audit(a.root),indent=2))
