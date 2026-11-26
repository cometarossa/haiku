"""Measure rejection frequency and severity separately, not display latency."""
import argparse
import json
import statistics
from pathlib import Path
from proxy_video_stats_report import parse, summarize
from v21_load_report import report


def gap_metrics(records, n):
    totals=summarize(records,n)
    if any(r["calls"]<=0 for r in records):
        raise ValueError("track has no supplier calls")
    calls=totals["calls"]
    rejects=totals["gap_timeout"]
    return dict(calls=calls,gap_timeouts=rejects,
                affected_tracks=sum(r["gap_timeout"]>0 for r in records),
                timeout_fraction=rejects/calls,
                mean_gap_when_rejected=totals["gap_frames"]/rejects if rejects else None,
                max_gap_when_rejected=totals["max_gap"] if rejects else None,
                gap_frames_per_call=totals["gap_frames"]/calls,
                median_track_timeout_fraction=statistics.median(
                    r["gap_timeout"]/r["calls"] for r in records))


def analyze(root,n):
    result=report(root,n,gop=True)
    rows=[]
    for row in result["rows"]:
        if not row["diagnostic_valid"]:
            rows.append(dict(tag=row["tag"],diagnostic_valid=False))
            continue
        records=parse((root/(row["tag"]+".stderr")).read_text())
        m=gap_metrics(records,n)
        rows.append(dict(tag=row["tag"],gop=row["gop"],
                         playback_valid=row["valid"],diagnostic_valid=True,**m))
    return dict(complete=result["complete"],all_diagnostic_valid=result["all_diagnostic_valid"],
                rows=rows,
                limitation="Gap sizes describe rejected supplier calls, not distinct dropped frames, time spent decoding or presentation latency. Repeated requests may overlap; no sum of gap frames is a count of lost frames.")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("streams",type=int,choices=(4,8,16))
    a=p.parse_args()
    print(json.dumps(analyze(a.root,a.streams),indent=2))
