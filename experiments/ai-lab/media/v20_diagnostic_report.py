"""V20 diagnostic validation; separate valid data from playback success."""
import argparse
import json
from pathlib import Path
from v19_deferred_load_report import report_trial
from deferred_timing_report import summarize_timing
from proxy_video_stats_report import parse, summarize
from media_stats_report import parse as media_parse, summarize as media_summary


def diagnostics(log, n, state):
    proxy=summarize(parse(log),n)
    timing=summarize_timing(log,n if state=="on" else 0)
    media=media_summary(media_parse(log))
    producer=media["producer"]
    if producer["records"]!=n or media["consumer"]["records"]!=n:
        raise ValueError("media lifetime count")
    # Proxy excludes calls without a track; producer may count these.
    # A complete single-track lifetime should classify all fill timeouts.
    if proxy["timeouts"]!=producer["fill_timeouts"]:
        raise ValueError("proxy/producer timeout mismatch")
    if proxy["calls"]>producer["fills"]:
        raise ValueError("proxy calls exceed producer fills")
    return dict(proxy=proxy,timing=timing,media=media)


def report(root,n):
    if n not in (4,8,16):
        raise ValueError("unsupported stream count")
    if "ai_11904750" not in (root/"revision.txt").read_text():
        raise ValueError("wrong image")
    rows=[]
    for i,state in enumerate(("off","on","on","off")):
        tag=f"{i:02d}-n{n}-{state}"
        if not (root/(tag+".exit")).exists():
            continue
        try:
            row=report_trial(root,i,n,state)
            row["diagnostics"]=diagnostics((root/(tag+".stderr")).read_text(),n,state)
            row["diagnostic_valid"]=row["player_exit"]==0
        except (ValueError,OSError,IndexError,KeyError) as e:
            row=dict(tag=tag,n=n,state=state,valid=False,diagnostic_valid=False,error=str(e))
        rows.append(row)
    complete=(root/"done.txt").exists() and (root/"done.txt").read_text().strip()=="0" and len(rows)==4
    return dict(complete=complete,rows=rows,
                all_diagnostic_valid=complete and all(r["diagnostic_valid"] for r in rows),
                all_playback_valid=complete and all(r["valid"] for r in rows))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("streams",type=int,choices=(4,8,16))
    a=p.parse_args()
    print(json.dumps(report(a.root,a.streams),indent=2))
