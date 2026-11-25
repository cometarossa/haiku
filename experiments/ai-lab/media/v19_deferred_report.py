"""Validate V19 smoke: actual activation, state transitions and orderly shutdown."""
import argparse
import json
import re
from pathlib import Path
from window_probe_report import analyze
from video_view_stats_report import parse, summarize

KEYS = "queued coalesced failed handled cancelled draw skipped".split()


def deferred_records(text):
    records = []
    for line in text.splitlines():
        if "LAB_VIDEO_DEFERRED" not in line:
            continue
        match = re.fullmatch(r"LAB_VIDEO_DEFERRED " + " ".join(k+r"=(\d+)" for k in KEYS), line)
        if not match:
            raise ValueError("malformed deferred record")
        row = dict(zip(KEYS, map(int, match.groups())))
        if row["handled"] != row["draw"] + row["skipped"]:
            raise ValueError("handler conservation")
        if not 0 <= row["queued"] - row["handled"] - row["cancelled"] <= 1:
            raise ValueError("notification conservation")
        records.append(row)
    return records


def position(text):
    values = re.findall(r'"result" \(B_INT64_TYPE\)\s*:\s*(\d+)\s',text)
    if len(values) != 1:
        raise ValueError("position response missing or ambiguous")
    return int(values[0])


def stopped(text):
    return text.splitlines().count("false") == 1 and "true" not in text.splitlines()


def lifecycle(text, pause):
    if text.count("STOP\n") != 1 or text.count("SEEK\n") != 1:
        raise ValueError("missing lifecycle boundary")
    _, body = text.split("STOP\n",1)
    a,b=body.split("SEEK\n",1)
    if not stopped(a) or not stopped(b):
        raise ValueError("stop or seek state")
    stop,seek=position(a),position(b)
    if not 0 <= stop <= 100000 or abs(seek-30000000)>1000000:
        raise ValueError("stop or seek position")
    if not pause.startswith("PAUSE\n") or pause.count("PAUSE_LATER\n") != 1:
        raise ValueError("pause boundary")
    c,d=pause.split("PAUSE_LATER\n",1)
    p,q=position(c),position(d)
    if not stopped(c) or abs(p-q)>100000 or p<seek:
        raise ValueError("pause did not hold")
    return dict(stop_us=stop,seek_us=seek,pause_us=p,pause_later_us=q)


def validate(root):
    if (root/"done.txt").read_text().strip()!="0" or "ai_067ee57e" not in (root/"revision.txt").read_text():
        raise ValueError("completion or revision")
    results=[]
    for i,state in enumerate(("off","on")):
        tag=f"{i:02d}-n1-{state}"
        def read(ext):
            return (root/(tag+"."+ext)).read_text()
        if read("exit").strip()!="0" or read("probe-exit").strip()!="0" or read("probe-stderr"):
            raise ValueError("process failure")
        mapping=read("map").splitlines()
        if len(mapping)!=1 or mapping[0].split()[1:]!=[tag+".mp4"]:
            raise ValueError("window identity")
        probe=analyze(read("probe"),[int(mapping[0].split()[0])])
        if not probe["playback_valid"]:
            raise ValueError("playback failed")
        if any(int(l.split()[-1])<29000000 for l in read("probe").splitlines() if " Position " in l):
            raise ValueError("resume did not start at seek target")
        states=lifecycle(read("lifecycle"),read("pause"))
        stats=summarize(parse(read("stderr")),1)
        rows=deferred_records(read("stderr"))
        if state=="off":
            if rows or stats.get("deferred",0):
                raise ValueError("unexpected activation OFF")
        else:
            if len(rows)!=1 or not rows[0]["draw"] or not stats.get("deferred"):
                raise ValueError("deferred path not exercised")
            if stats["deferred"] != rows[0]["queued"]+rows[0]["coalesced"]:
                raise ValueError("publication conservation")
        results.append(dict(state=state,probe=probe,states=states,view=stats,deferred=rows))
    return results


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    a=p.parse_args()
    print(json.dumps(validate(a.root),indent=2))
