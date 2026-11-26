"""Per-stage and per-instance completion distributions; never presentation FPS."""
import argparse
import json
import statistics
from pathlib import Path
from observation_report import parse,SECOND
from v22_observation_smoke_report import analyze


def distribution(records,stage,kind,lo,hi):
    if lo%SECOND or hi%SECOND or hi<=lo:
        raise ValueError("invalid interval")
    selected=[r for (s,_),r in records.items() if s==stage]
    if not selected:
        raise ValueError("missing stage")
    for r in selected:
        if r["created"]>lo or r["ended"]<hi or r["anchor"]+512*SECOND<hi:
            raise ValueError("incomplete interval")
    seconds=list(range(lo,hi,SECOND))
    matrix=[[r["bins"].get(t,[0]*8)[kind] for t in seconds] for r in selected]
    totals=[sum(row) for row in matrix]
    per_second=[sum(col) for col in zip(*matrix)]
    return dict(instances=len(selected),seconds=len(seconds),
        instance_totals_sorted=sorted(totals),min_instance=min(totals),
        median_instance=statistics.median(totals),max_instance=max(totals),
        zero_instance_seconds=sum(c==0 for row in matrix for c in row),
        total_instance_seconds=len(seconds)*len(selected),
        per_second=per_second,min_second=min(per_second),max_second=max(per_second),
        total=sum(totals))


def analyze_campaign(root,n):
    r=analyze(root,"on",n)
    rows=[]
    for x in r["rows"]:
        if not x["diagnostic_valid"]:
            continue
        o=x["observation"];lo,hi=o["start_us"],o["stop_us"]
        rec=parse((root/(x["tag"]+".stderr")).read_text())
        draw=distribution(rec,"deferred" if x["state"]=="on" else "view",
                          0 if x["state"]=="on" else 5,lo,hi)
        decoded=distribution(rec,"producer",0,lo,hi)
        assert draw["total"]==o["draw_completions"]
        assert decoded["total"]==o["stages"]["producer"]["observed"]["ok"]
        rows.append(dict(tag=x["tag"],playback_valid=x["valid"],draw=draw,decoded=decoded))
    return dict(complete=r["complete"],all_diagnostic_valid=r["all_diagnostic_valid"],rows=rows,
        limitations="Zero completion bins do not prove zero visible frames. Instance identities are not linked across pipeline stages or trials. No per-track causal attribution.")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("streams",type=int,choices=(4,8,16))
    a=p.parse_args()
    print(json.dumps(analyze_campaign(a.root,a.streams),indent=2))
