"""Report same-image V19 load trials without treating failures as speedups."""
import argparse
import json
from pathlib import Path
from window_probe_report import analyze
from video_view_stats_report import parse, summarize
from v19_deferred_report import deferred_records


def trials(sixteen=False):
    return tuple((n,s) for n in ((16,) if sixteen else (4,8))
                 for s in ("off","on","on","off"))


def view_treatment(log,n,state):
    view=summarize(parse(log),n)
    deferred=deferred_records(log)
    if state=="off":
        if deferred or view.get("deferred",0):
            raise ValueError("deferred path active in OFF")
    else:
        if len(deferred)!=n or any(not r["draw"] for r in deferred):
            raise ValueError("not every view exercised deferred path")
        if view.get("deferred",0)!=sum(r["queued"]+r["coalesced"] for r in deferred):
            raise ValueError("publication conservation")
    return view,deferred


def report_trial(root,i,n,state,view_state=None):
    tag=f"{i:02d}-n{n}-{state}"
    def read(ext):
        return (root/(tag+"."+ext)).read_text()
    start,dispatch,play,stop,quit=(int(read(k)) for k in ("start","dispatch","play","stop","quit-time"))
    if not 0<start<dispatch<=play<stop<=quit:
        raise ValueError("invalid lifetime")
    mapping=[line.split() for line in read("map").splitlines()]
    if len(mapping)!=n or {x[1] for x in mapping}!={f"{tag}-{k}.mp4" for k in range(1,n+1)}:
        raise ValueError("invalid window identity")
    probe=analyze(read("probe"),[int(x[0]) for x in mapping])
    clock=read("probe").splitlines()
    begin,deadline,_=map(int,clock[1].split()[1:])
    end=int(clock[-1].split()[1])
    if not play<=begin<=end<=stop or deadline-begin!=15000000:
        raise ValueError("probe outside observation")
    view,deferred=view_treatment(read("stderr"),n,state if view_state is None else view_state)
    observed=stop-play
    probe_rc,player_rc=int(read("probe-exit")),int(read("exit"))
    if probe_rc not in (0,4) or (probe_rc==0)!=probe["complete"] or read("probe-stderr"):
        raise ValueError("inconsistent probe process result")
    quit_return=exit_time=None
    if (root/(tag+".quit-return")).exists() or (root/(tag+".exit-time")).exists():
        quit_return,exit_time=int(read("quit-return")),int(read("exit-time"))
        if not quit<=quit_return<=exit_time:
            raise ValueError("invalid teardown clocks")
    return dict(tag=tag,n=n,state=state,observation_us=observed,
        quit_rpc_us=quit_return-quit if quit_return is not None else None,
        teardown_us=exit_time-quit if exit_time is not None and player_rc==0 else None,
        lifetime_to_exit_us=exit_time-start if exit_time is not None and player_rc==0 else None,
        lifetime_to_quit_request_us=quit-start,dispatch_us=play-dispatch,
        probe=probe,view=view,deferred=deferred,player_exit=player_rc,
        valid=probe["playback_valid"] and player_rc==0 and 20000000<=observed<=22000000)


def report(root,sixteen=False):
    if "ai_067ee57e" not in (root/"revision.txt").read_text():
        raise ValueError("wrong image")
    rows=[]
    for i,(n,state) in enumerate(trials(sixteen)):
        tag=f"{i:02d}-n{n}-{state}"
        if not (root/(tag+".exit")).exists():
            continue
        try:
            rows.append(report_trial(root,i,n,state))
        except (ValueError,OSError,IndexError) as e:
            rows.append(dict(tag=tag,n=n,state=state,valid=False,error=str(e)))
    done=(root/"done.txt").exists() and (root/"done.txt").read_text().strip()=="0"
    return dict(complete=done and len(rows)==len(trials(sixteen)),rows=rows,
        all_valid=done and len(rows)==len(trials(sixteen)) and all(r["valid"] for r in rows))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("--sixteen",action="store_true")
    a=p.parse_args()
    print(json.dumps(report(a.root,a.sixteen),indent=2))
