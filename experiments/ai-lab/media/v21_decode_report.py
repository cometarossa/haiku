"""Validate identical native decoded pixel digests and timestamps, not FPS."""
import re
import json
from pathlib import Path

FIXTURE_SHA="555e750e36db6608e1c18240a197fd159d4fd8e13658a354350f32751c07d50b"
REV="2f9d27bf"
THREAD=re.compile(r"LAB_VIDEO_THREADS codec=(\S+) width=(\d+) height=(\d+) original=(\d+) requested=(\d+) effective=(\d+) active_type=(\d+)")


def frames(text, count=600):
    lines=text.splitlines()
    if len(lines)!=count+2 or lines[-2]!="frames,width,height,format,hash_fnv1a64":
        raise ValueError("unexpected frame count or summary")
    rows=[]
    for i,line in enumerate(lines[:-2]):
        m=re.fullmatch(r"FRAME (\d+) (-?\d+) ([0-9a-f]{16})",line)
        if not m or int(m[1])!=i:
            raise ValueError("invalid frame index")
        pts=int(m[2])
        if abs(pts-i*1000000/30)>1000:
            raise ValueError("unexpected fixture timestamp")
        rows.append((pts,m[3]))
    if len(set(x[1] for x in rows))<count//2:
        raise ValueError("insufficient dynamic pixel content")
    if not re.fullmatch(f"{count},320,180,B_RGB32,[0-9a-f]{{16}}",lines[-1]):
        raise ValueError("invalid summary")
    return rows,lines[-1]


def threads(text,state):
    rows=[]
    for line in text.splitlines():
        if "LAB_VIDEO_THREADS" not in line:continue
        m=THREAD.fullmatch(line)
        if not m:raise ValueError("malformed thread record")
        codec=m[1]
        w,h,original,requested,effective,active=map(int,m.groups()[1:])
        if (codec,w,h,original,requested,effective)!=("h264",320,180,4,4 if state=="off" else 1,4 if state=="off" else 1):
            raise ValueError("unexpected decoder treatment")
        rows.append(dict(codec=codec,width=w,height=h,original=original,requested=requested,effective=effective,active_type=active))
    if not rows:raise ValueError("missing thread evidence")
    return rows


def validate(root):
    if (root/"done.txt").read_text().strip()!="0" or "ai_"+REV not in (root/"revision.txt").read_text():
        raise ValueError("wrong revision or incomplete")
    if FIXTURE_SHA+"  stream-a.mp4" not in (root/"input-sha256.txt").read_text().splitlines():
        raise ValueError("wrong fixture")
    data={}
    result={}
    for state in ("off","on"):
        if (root/(state+".exit")).read_text().strip()!="0":raise ValueError("decode failed")
        data[state]=frames((root/(state+".stdout")).read_text())
        start,stop=(int((root/(state+"."+k)).read_text()) for k in ("start","stop"))
        if not 0<start<stop:raise ValueError("clock")
        result[state]=dict(frames=len(data[state][0]),summary=data[state][1],elapsed_us=stop-start,
                           threads=threads((root/(state+".stderr")).read_text(),state))
    if data["off"]!=data["on"]:raise ValueError("pixel or timestamp regression")
    return dict(identical=True,results=result)


def validate_repeat(root):
    import statistics
    if (root/"done.txt").read_text().strip()!="0" or "ai_"+REV not in (root/"revision.txt").read_text():
        raise ValueError("wrong revision or incomplete")
    if FIXTURE_SHA+"  stream-a.mp4" not in (root/"input-sha256.txt").read_text().splitlines():
        raise ValueError("wrong fixture")
    rows=[]
    baseline=None
    previous=0
    for i,state in enumerate(("off","on","on","off")*2):
        tag=f"{i:02d}-{state}"
        def read(ext):
            return (root/(tag+"."+ext)).read_text()
        if read("exit").strip()!="0":raise ValueError("decode failed")
        data=frames(read("stdout"))
        if baseline is None:baseline=data
        if data!=baseline:raise ValueError("pixel or timestamp regression")
        start,stop=int(read("start")),int(read("stop"))
        if not 0<=previous<start<stop:raise ValueError("clock")
        previous=stop
        rows.append(dict(tag=tag,state=state,frames=len(data[0]),summary=data[1],
                         elapsed_us=stop-start,threads=threads(read("stderr"),state)))
    med={s:statistics.median(r["elapsed_us"] for r in rows if r["state"]==s) for s in ("off","on")}
    ratios=[rows[a]["elapsed_us"]/rows[b]["elapsed_us"] for a,b in ((0,1),(3,2),(4,5),(7,6))]
    return dict(identical=True,rows=rows,median_us=med,paired_ratios=ratios,
                median_paired_ratio=statistics.median(ratios))


if __name__=="__main__":
    import sys
    print(json.dumps(validate(Path(sys.argv[1])),indent=2))
