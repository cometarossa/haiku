"""Count completion events in complete monotonic bins inside observation."""
import re
from media_stats_report import parse as media_parse
from video_view_stats_report import parse as view_parse
from v19_deferred_report import deferred_records

SECOND=1000000
HEADER=re.compile(r"LAB_OBSERVATION stage=(producer|view|deferred) id=(\d+) anchor=(\d+) created=(\d+) ended=(\d+) overflow=(\d+) valid=([01])")
BIN=re.compile(r"LAB_OBSERVATION_BIN stage=(producer|view|deferred) id=(\d+) bin=(\d+) "+" ".join(fr"c{i}=(\d+)" for i in range(8)))
KEYS={
    "producer":("ok","cached","timeout","end","error","sent","suppressed","send_error"),
    "view":("null","looper_fail","bitmap_fail","overlay","invalidate","draw","deferred","unused"),
    "deferred":("draw","skipped","unused2","unused3","unused4","unused5","unused6","unused7"),
}

def parse(text):
    records={}
    for line in text.splitlines():
        if "LAB_OBSERVATION" not in line:continue
        h=HEADER.fullmatch(line)
        b=BIN.fullmatch(line)
        if h:
            stage,ident,anchor,created,ended,overflow,valid=h.groups()
            key=(stage,int(ident))
            anchor,created,ended,overflow,valid=map(int,(anchor,created,ended,overflow,valid))
            if key in records or not valid or overflow or anchor%SECOND or not anchor<=created<anchor+SECOND or ended<created:
                raise ValueError("invalid observation header")
            records[key]=dict(anchor=anchor,created=created,ended=ended,bins={})
        elif b:
            stage,ident,stamp,*counts=b.groups()
            key=(stage,int(ident)); stamp=int(stamp); counts=list(map(int,counts))
            if key not in records:raise ValueError("bin without header")
            r=records[key]
            if stamp%SECOND or not r["anchor"]<=stamp<r["anchor"]+512*SECOND or stamp>r["ended"] or stamp in r["bins"] or not any(counts):
                raise ValueError("invalid observation bin")
            r["bins"][stamp]=counts
        else:raise ValueError("malformed observation record")
    return records

def summarize(text,play,stop,n,deferred=False):
    records=parse(text)
    lo=(play+SECOND-1)//SECOND*SECOND
    hi=stop//SECOND*SECOND
    if hi<=lo:raise ValueError("empty observation interval")
    media=media_parse(text)["PRODUCER"]; views=view_parse(text)
    ds=deferred_records(text)
    expected={"producer":len(media),"view":n,"deferred":n if deferred else 0}
    if len(media)!=n or len(views)!=n or len(ds)!=expected["deferred"]:
        raise ValueError("lifetime coverage")
    sums={}
    for stage,names in KEYS.items():
        selected=[r for (s,_),r in records.items() if s==stage]
        if len(selected)!=expected[stage]:raise ValueError("stage coverage")
        all_counts=[0]*8; observed=[0]*8
        for r in selected:
            if r["created"]>lo or r["ended"]<hi or r["anchor"]+512*SECOND<hi:
                raise ValueError("incomplete observation coverage")
            for stamp,counts in r["bins"].items():
                for i,c in enumerate(counts):
                    all_counts[i]+=c
                    if lo<=stamp<hi:observed[i]+=c
        sums[stage]={"lifetime":dict(zip(names,all_counts)),"observed":dict(zip(names,observed))}
    p=sums["producer"]["lifetime"]
    if set(ident for stage,ident in records if stage=="producer")!={r["thread"] for r in media}:
        raise ValueError("producer identity")
    if sum(p[k] for k in KEYS["producer"][:5])!=sum(r["fills"] for r in media):
        raise ValueError("producer fill conservation")
    for a,b in (("timeout","fill_timeouts"),("end","end_buffers"),("error","fill_errors"),("sent","sent"),("suppressed","suppressed"),("send_error","send_errors")):
        if p[a]!=sum(r[b] for r in media):raise ValueError("producer outcome conservation")
    v=sums["view"]["lifetime"]
    if v["unused"] or any(v[k]!=sum(r.get(k,0) for r in views) for k in KEYS["view"][:7]):
        raise ValueError("view conservation")
    d=sums["deferred"]["lifetime"]
    if any(d[k]!=sum(r.get(k,0) for r in ds) for k in KEYS["deferred"]):
        raise ValueError("deferred conservation")
    return dict(start_us=lo,stop_us=hi,seconds=(hi-lo)/SECOND,stages=sums,
        draw_completions=sums["view"]["observed"]["draw"]+sums["deferred"]["observed"]["draw"],
        limitation="Completion events only; partial boundary bins excluded. Not actual presented FPS.")
