"""V21 decoder-thread treatment: keep deferred rendering off in both arms."""
import argparse
import json
from pathlib import Path
from v19_deferred_load_report import report_trial
from v20_diagnostic_report import diagnostics
from v21_decode_report import threads,REV


def report(root,n,combined=False,gop=False,revision=REV,scaling=False):
    if sum((combined,gop,scaling))>1:
        raise ValueError("choose one treatment")
    if gop:
        from v22_gop_decode_report import HASHES
        manifest=(root/"input-sha256.txt").read_text().splitlines()
        if any(f"{h}  gop-{g}.mp4" not in manifest for g,h in HASHES.items()):
            raise ValueError("wrong GOP fixture manifest")
    if n not in (4,8,16):
        raise ValueError("unsupported stream count")
    if "ai_"+revision not in (root/"revision.txt").read_text():
        raise ValueError("wrong image")
    rows=[]
    for i,state in enumerate(("off","on","on","off")):
        tag=f"{i:02d}-n{n}-{state}"
        if not (root/(tag+".exit")).exists():
            continue
        try:
            view_state=state if combined else "off"
            row=report_trial(root,i,n,state,view_state=view_state)
            log=(root/(tag+".stderr")).read_text()
            records=threads(log,"on" if combined or gop or scaling else state)
            if len(records)!=n:
                raise ValueError("decoder negotiation count")
            if gop:
                row["gop"]=15 if state=="on" else 120
            row["threads"]=records
            row["diagnostics"]=diagnostics(log,n,view_state)
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
    p.add_argument("--combined",action="store_true")
    p.add_argument("--gop",action="store_true")
    a=p.parse_args()
    print(json.dumps(report(a.root,a.streams,a.combined,a.gop),indent=2))
