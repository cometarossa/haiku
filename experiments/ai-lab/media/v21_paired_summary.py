"""Paired V21 load summary. Lifetime counters are not presented FPS."""
import argparse
import json
from pathlib import Path
from v21_load_report import report


def metrics(row):
    d=row["diagnostics"]
    p=d["media"]["producer"]
    c=d["media"]["consumer"]
    q=row["probe"]
    return dict(playback_valid=row["valid"], successful_queries=q["attempted"]-q["errors"],
                expected_queries=q["expected"], position_p95_us=q["by_operation"]["Position"]["p95_us"],
                fills=p["fills"], fill_timeouts=p["fill_timeouts"],
                gap_timeouts=d["proxy"]["gap_timeout"], draw_submissions=row["view"]["draw"],
                looper_fail=row["view"]["looper_fail"], late_consumer_buffers=c["late"],
                lifetime_us=row["lifetime_to_quit_request_us"], observation_us=row["observation_us"])


def aggregate(result):
    if not result["complete"] or not result["all_diagnostic_valid"]:
        raise ValueError("complete diagnostic-valid campaign required")
    rows=result["rows"]
    if [r["state"] for r in rows]!=["off","on","on","off"]:
        raise ValueError("unbalanced order")
    pairs=[]
    for a,b in ((0,1),(3,2)):
        off,on=metrics(rows[a]),metrics(rows[b])
        pairs.append(dict(off_tag=rows[a]["tag"],on_tag=rows[b]["tag"],off=off,on=on,
            both_playback_valid=off["playback_valid"] and on["playback_valid"]))
    groups={}
    for state in ("off","on"):
        m=[metrics(r) for r in rows if r["state"]==state]
        totals={k:sum(v[k] for v in m) for k in ("successful_queries","expected_queries","fills",
            "fill_timeouts","gap_timeouts","draw_submissions","looper_fail","late_consumer_buffers","lifetime_us")}
        totals["fill_timeout_fraction"]=totals["fill_timeouts"]/totals["fills"] if totals["fills"] else None
        totals["draw_requests_per_lifetime_second"]=totals["draw_submissions"]*1e6/totals["lifetime_us"]
        totals["position_p95_us"]=[v["position_p95_us"] for v in m]
        totals["valid_playback_trials"]=sum(v["playback_valid"] for v in m)
        groups[state]=totals
    return dict(groups=groups,pairs=pairs,all_playback_valid=result["all_playback_valid"],
                limitations="Lifetime counters include setup and teardown; normalized draw requests use start-to-quit-request time, not presentation FPS. Two pairs, non-isolated host.")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("streams",type=int,choices=(4,8,16))
    a=p.parse_args()
    print(json.dumps(aggregate(report(a.root,a.streams)),indent=2))
