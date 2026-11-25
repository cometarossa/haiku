#!/usr/bin/env python3
"""Validate paired V16 runs; stage outcomes, not physical presentation FPS."""
import argparse
import json
import re
import statistics
from pathlib import Path
from media_stats_report import parse, summarize

SPECS_16 = [(16,"off"),(16,"on"),(16,"on"),(16,"off")]

SPECS = [(4,"off"),(4,"on"),(4,"on"),(4,"off"),
         (8,"off"),(8,"on"),(8,"on"),(8,"off")]


def validate_run(root, index, n, state):
    tag = f"{index:02d}-n{n}-{state}"
    def read(ext):
        return (root / (tag+"."+ext)).read_text()
    if read("exit").strip() != "0":
        raise ValueError(f"{tag}: bad exit")
    windows = [tuple(map(int,line.split())) for line in read("windows").splitlines()]
    mapping = dict(windows)
    if len(windows)!=n or set(mapping)!=set(range(1,n+1)) or len(set(mapping.values()))!=n:
        raise ValueError(f"{tag}: window identity")
    positions = []
    for chunk in read("positions").split("SAMPLE ")[1:]:
        matches = re.findall(r"WINDOW (\d+)\n"+re.escape(tag)+r"-(\d+)\.mp4\ntrue\nReply BMessage\(B_REPLY\):\n\s+\"result\" \(B_INT64_TYPE\) : (\d+)",chunk)
        values = {}
        for win,stream,pos in matches:
            if mapping.get(int(stream))!=int(win):
                raise ValueError(f"{tag}: mismatched window")
            values[int(stream)] = int(pos)
        if len(matches)!=n or len(values)!=n:
            raise ValueError(f"{tag}: incomplete playback")
        positions.append([int(chunk.splitlines()[0])] + [values[i] for i in range(1,n+1)])
    if [r[0] for r in positions]!=[1,2,3] or not all(all(b[k]>a[k] for k in range(1,n+1)) for a,b in zip(positions,positions[1:])):
        raise ValueError(f"{tag}: nonadvancing playback")
    start,play,stop,quit_time = [int(read(ext)) for ext in ("start","play","stop","quit-time")]
    minimum,maximum = (12000000,19000000) if n==16 else (8000000,14000000)
    if not 0<start<play<stop<quit_time or not minimum<=stop-play<=maximum:
        raise ValueError(f"{tag}: invalid observation duration")
    stdout,stderr = read("stdout"),read("stderr")
    if stdout.count("LAB_MEDIA_OVERLAY_PREFLIGHT")!=n or "trying without overlays" in stdout+stderr:
        raise ValueError(f"{tag}: overlay treatment mismatch")
    records = parse(stderr)
    summary = summarize(records)
    p,c=summary["producer"],summary["consumer"]
    if p["records"]!=n or c["records"]!=n:
        raise ValueError(f"{tag}: missing lifetime summaries")
    activations=re.findall(r"^LAB_MEDIA_CATCHUP progress from=(\d+) to=(\d+)$",stderr,re.M)
    if stderr.count("LAB_MEDIA_CATCHUP")!=len(activations):
        raise ValueError(f"{tag}: malformed activation")
    if len(activations)>n or (state=="off" and activations) or any(int(b)<=int(a) for a,b in activations):
        raise ValueError(f"{tag}: invalid catch-up treatment")
    return dict(tag=tag,n=n,state=state,activation_count=len(activations),
                positions=positions,lifetime_us=quit_time-start,
                observation_us=stop-play,producer=p,consumer=c,
                timeout_fraction=p["fill_timeouts"]/p["fills"],
                producer_late_fraction=p["late"]/(p["attempts"]+p["late"]),
                consumer_late_fraction=c["late"]/c["received"])


def validate(root, partial=False, specs=SPECS):
    if "ai_a1b69d83" not in (root/"revision.txt").read_text():
        raise ValueError("wrong guest revision")
    rows=[]
    for index,(n,state) in enumerate(specs):
        tag=f"{index:02d}-n{n}-{state}"
        if partial and not (root/(tag+".exit")).exists():
            break
        rows.append(validate_run(root,index,n,state))
    if not partial and (root/"done.txt").read_text().strip()!="0":
        raise ValueError("campaign incomplete")
    comparisons=[]
    for a,b in zip(rows[::2],rows[1::2]):
        off,on=(a,b) if a["state"]=="off" else (b,a)
        comparisons.append(dict(n=off["n"],off=off["tag"],on=on["tag"],
            activation_count=on["activation_count"],
            timeout_delta=on["timeout_fraction"]-off["timeout_fraction"],
            producer_late_delta=on["producer_late_fraction"]-off["producer_late_fraction"],
            consumer_late_delta=on["consumer_late_fraction"]-off["consumer_late_fraction"],
            send_error_delta=on["producer"]["send_errors"]-off["producer"]["send_errors"],
            target_calls_ratio=on["consumer"]["target_calls"]/off["consumer"]["target_calls"]))
    return dict(completed=len(rows),runs=rows,pairs=comparisons,
        activated_pairs=sum(p["activation_count"]>0 for p in comparisons))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("--partial",action="store_true")
    p.add_argument("--sixteen",action="store_true")
    a=p.parse_args()
    print(json.dumps(validate(a.root,a.partial,SPECS_16 if a.sixteen else SPECS),indent=2))
