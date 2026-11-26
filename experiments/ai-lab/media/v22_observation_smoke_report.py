"""Native V22 observation and fill-time smoke, four to sixteen streams."""
import argparse
import json
from pathlib import Path
from v21_load_report import report
from observation_report import parse,summarize
from fill_timing_report import validate

def analyze(root,mode,n=4,scaling=False):
    if mode not in ("off","on"):raise ValueError("mode")
    r=report(root,n,combined=not scaling,revision="4ae8e7ea",scaling=scaling)
    for row in r["rows"]:
        if not row["diagnostic_valid"]:continue
        tag=row["tag"]
        try:
            log=(root/(tag+".stderr")).read_text()
            row["fill_timing"]=validate(log,enabled=mode=="on")
            if mode=="off":
                if parse(log):raise ValueError("unexpected observation records")
            else:
                play=int((root/(tag+".play")).read_text())
                stop=int((root/(tag+".stop")).read_text())
                row["observation"]=summarize(log,play,stop,n,deferred=not scaling and row["state"]=="on")
                if not row["observation"]["draw_completions"]:
                    raise ValueError("no observation draw completions")
            if row["teardown_us"] is None:raise ValueError("missing exit clocks")
        except (ValueError,OSError,KeyError) as e:
            row["diagnostic_valid"]=False
            row["error"]=str(e)
    r["all_diagnostic_valid"]=r["complete"] and all(x["diagnostic_valid"] for x in r["rows"])
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("mode",choices=("off","on"))
    p.add_argument("--streams",type=int,choices=(4,8,16),default=4)
    a=p.parse_args()
    print(json.dumps(analyze(a.root,a.mode,a.streams),indent=2))
