"""Controller timeline advancement with query latency bounds, not display FPS."""
import argparse
import json
import statistics
from pathlib import Path
from window_probe_report import analyze


def progress(text, indices):
    validation=analyze(text,indices)
    positions={i:[] for i in indices}
    playing={}
    for line in text.splitlines()[2:-1]:
        _,sample,index,op,before,after,status,value=line.split()
        sample,index,before,after,status,value=map(int,(sample,index,before,after,status,value))
        if op=="IsPlaying":
            playing[index,sample]=status==0 and value==1
        if op=="Position" and status==0:
            positions[index].append((sample,before,after,value))
    rows=[]
    for i in indices:
        points=positions[i]
        # Only compare complete, continuously reported playing samples.
        if [p[0] for p in points]!=[1,2,3] or not all(playing.get((i,s)) for s in (1,2,3)):
            continue
        _,a,b,p=points[0]
        _,c,d,q=points[-1]
        lower_time=c-b
        upper_time=d-a
        delta=q-p
        if lower_time<=0 or delta<0:
            continue
        rows.append(dict(index=i,position_delta_us=delta,wall_time_lower_us=lower_time,
            wall_time_upper_us=upper_time,rate_lower=delta/upper_time,
            rate_upper=delta/lower_time,rate_midpoint=2*delta/(lower_time+upper_time)))
    return dict(expected_windows=len(indices),measured_windows=len(rows),
        all_playback_valid=validation["playback_valid"],
        median_midpoint_rate=statistics.median(r["rate_midpoint"] for r in rows) if rows else None,
        rows=rows, limitation="Controller-reported position, not physical frame presentation; bounds assume sample occurs during request and do not bound controller clock staleness.")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("log",type=Path)
    p.add_argument("window_map",type=Path)
    a=p.parse_args()
    print(json.dumps(progress(a.log.read_text(),[int(l.split()[0]) for l in a.window_map.read_text().splitlines()]),indent=2))
