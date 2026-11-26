"""Native V23 serial acceptance; lifetime phases, not observation rates."""
import argparse
import json
import sys
from pathlib import Path
from v22_observation_smoke_report import analyze

REV="e8db1a1c"

def profile_script(script,mode,n=4):
    if mode not in ("off","on") or n not in (4,8,16):
        raise ValueError("invalid profile mode or streams")
    changes=[
        (f"v22-observation-on-{n}-ram".encode(),f"v23-appserver-{mode}-{n}-ram".encode(),2),
        (b'filltiming=/boot/home/config/settings/haiku-lab-video-fill-timing',b'filltiming=/boot/home/config/settings/haiku-lab-video-fill-timing\nserverprofile=/boot/home/config/settings/haiku-lab-media-appserver-profile',1),
        (b'"$observation" "$filltiming"',b'"$observation" "$filltiming" "$serverprofile"',2),
        (b'own_filltiming=0\ncleanup()',b'own_filltiming=0;own_serverprofile=0\ncleanup()',1),
        (b'cleanup() {',b'cleanup() {\n if test "$own_serverprofile" = 1; then rm -f "$serverprofile"; own_serverprofile=0; fi',1),
    ]
    if mode=="on":
        changes.append((b'(set -C; : > "$filltiming"); own_filltiming=1',b'(set -C; : > "$filltiming"); own_filltiming=1\n(set -C; : > "$serverprofile"); own_serverprofile=1',1))
    for old,new,count in changes:
        if script.count(old)!=count:raise ValueError("Unexpected profile anchor: "+repr(old))
        script=script.replace(old,new)
    return script

def serial_profiles(log,mode,n):
    if mode not in ("off","on"):raise ValueError("invalid profile mode")
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"desktop"))
    from appwin_profile import parse
    rows=parse(log,0 if mode=="off" else None,None,media=True)
    teams={}
    for r in rows:teams.setdefault(r["team"],[]).append(r)
    if mode=="on":
        if len(teams)!=4:raise ValueError("expected four distinct MediaPlayer teams")
        for group in teams.values():
            if sum(r["bitmap"]["n"]>0 for r in group)<n:
                raise ValueError("insufficient bitmap-active windows")
    return rows

def report(root,mode,n=4):
    r=analyze(root,"on",n,revision=REV)
    if r["complete"]:
        r["server_windows"]=serial_profiles((root/"appserver-serial.log").read_text(errors="replace"),mode,n)
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("mode",choices=("off","on"))
    p.add_argument("--streams",type=int,choices=(4,8,16),default=4)
    a=p.parse_args()
    print(json.dumps(report(a.root,a.mode,a.streams),indent=2))
