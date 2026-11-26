#!/usr/bin/env python3
"""Staged native persistent-query test; requires confirmed V18 Terminal."""
import hashlib
import importlib
import json
import socket
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from v16_catchup_runner import HOME, MEDIA, LAB, sample_host
from window_probe_report import analyze

REV = "fb8c2e41"
SPECS = (4, 8, 16)


def deferred_load_script(script, sixteen=False):
    """Generate a balanced, fixed-duration same-image comparison."""
    changes = [
        (b'v18-probe-load-ram', b'v19-deferred-load-16-ram' if sixteen else b'v19-deferred-load-ram', 2),
        (b'for spec in 4-on 8-on 16-on;', b'for spec in 16-off 16-on 16-on 16-off;' if sixteen else b'for spec in 4-off 4-on 4-on 4-off 8-off 8-on 8-on 8-off;', 1),
        (b'catchup=/boot/home/config/settings/haiku-lab-video-view-stats', b'catchup=/boot/home/config/settings/haiku-lab-video-deferred\nview=/boot/home/config/settings/haiku-lab-video-view-stats', 1),
        (b'for m in "$stats" "$preflight" "$catchup"', b'for m in "$stats" "$preflight" "$catchup" "$view"', 2),
        (b's=0;p=0;c=0', b's=0;p=0;c=0;v=0', 1),
        (b'cleanup() {', b'cleanup() {\n if test "$v" = 1; then rm -f "$view"; v=0; fi', 1),
        (b'(set -C; : > "$stats"); s=1', b'(set -C; : > "$stats"); s=1\n(set -C; : > "$view"); v=1', 1),
        (b' system_time > "$tag.stop"', b' # Hold the observation window at 20 s from last Play reply.\n while test "$(( $(system_time) - $(cat "$tag.play") ))" -lt 20000000; do sleep .1; done\n system_time > "$tag.stop"', 1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected source script anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def v20_diagnostic_script(script, streams):
    if streams not in (4,8,16):
        raise ValueError("Unsupported V20 load")
    script=deferred_load_script(script,False)
    order=" ".join(f"{streams}-{state}" for state in ("off","on","on","off")).encode()
    changes=[
        (b'v19-deferred-load-ram', f'v20-diagnostic-{streams}-ram'.encode(), 2),
        (b'for spec in 4-off 4-on 4-on 4-off 8-off 8-on 8-on 8-off;', b'for spec in '+order+b';', 1),
        (b'view=/boot/home/config/settings/haiku-lab-video-view-stats', b'view=/boot/home/config/settings/haiku-lab-video-view-stats\ntiming=/boot/home/config/settings/haiku-lab-video-deferred-timing\nproxy=/boot/home/config/settings/haiku-lab-video-proxy-stats', 1),
        (b'"$catchup" "$view"', b'"$catchup" "$view" "$timing" "$proxy"', 2),
        (b's=0;p=0;c=0;v=0', b's=0;p=0;c=0;v=0;t=0;x=0', 1),
        (b'cleanup() {', b'cleanup() {\n if test "$t" = 1; then rm -f "$timing"; t=0; fi\n if test "$x" = 1; then rm -f "$proxy"; x=0; fi', 1),
        (b'(set -C; : > "$view"); v=1', b'(set -C; : > "$view"); v=1\n(set -C; : > "$timing"); t=1\n(set -C; : > "$proxy"); x=1', 1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected V20 script anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def run(root, queues=False, deferred_smoke=False, deferred_load=False, sixteen=False, smoke_evidence=None, v20_streams=None, v20_evidence=None):
    if sum((queues,deferred_smoke,deferred_load,v20_streams is not None))>1 or (sixteen and not deferred_load):
        raise ValueError("Select one campaign")
    revision = "067ee57e" if deferred_smoke or deferred_load else REV
    specs = ((1,"off"),(1,"on")) if deferred_smoke else tuple((n,"on") for n in ((8,) if queues else SPECS))
    if deferred_load:
        from v19_deferred_report import validate
        if smoke_evidence is None:
            raise ValueError("A validated V19 lifecycle smoke evidence root is required")
        validate(smoke_evidence)
        specs = tuple((n,state) for n in ((16,) if sixteen else (4,8)) for state in ("off","on","on","off"))
    if v20_streams is not None:
        from v19_deferred_report import validate
        if smoke_evidence is None:
            raise ValueError("V19 lifecycle smoke evidence required")
        validate(smoke_evidence)
        if v20_streams not in (4,8,16):
            raise ValueError("Unsupported V20 load")
        if v20_streams > 4:
            from v20_diagnostic_report import report
            if v20_evidence is None:
                raise ValueError("Validated V20 four-stream campaign required")
            gate=report(v20_evidence,4)
            if not gate["complete"] or not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
                raise ValueError("V20 four-stream gate not met")
        revision="11904750"
        specs=tuple((v20_streams,state) for state in ("off","on","on","off"))
    initial = sample_host(revision)
    pids = {g["pid"] for g in initial["guests"]}
    downloads = {}
    for folder, name, alias in (
        ("v17-long-sd", "stream-long-sd.mp4", "stream-a.mp4"),
        ("window-probe-d9c8b5b9", "media-window-probe", "media-window-probe"),
    ):
        src = HOME/"guest-files"/folder
        b = (src/name).read_bytes()
        if hashlib.sha256(b).hexdigest() != (src/"SHA256SUMS").read_text().split()[0]:
            raise ValueError("input checksum mismatch")
        downloads[alias] = b
    downloads["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(b).hexdigest()}  {n}\n" for n,b in downloads.items()).encode()
    script = (MEDIA/"v18-probe-load-guest.sh").read_bytes()
    if queues:
        script=(MEDIA/"v18-queue-load-guest.sh").read_bytes()
    if deferred_smoke:
        script=(MEDIA/"v19-deferred-smoke-guest.sh").read_bytes()
    if deferred_load:
        script=deferred_load_script(script,sixteen)
    if v20_streams is not None:
        script=v20_diagnostic_script(script,v20_streams)
    subprocess.run(["sh","-n"],input=script,check=True)
    downloads["run.sh"] = script
    allowed = {"revision.txt","done.txt"} | {
        f"{i:02d}-n{n}-{state}.{ext}" for i,(n,state) in enumerate(specs)
        for ext in ("dispatch","play","stop","map","probe","probe-stderr","probe-exit",
                    "start","quit-time","windows","positions","stdout","stderr","exit","lifecycle","pause")}
    if queues:
        allowed |= {"teams.txt","00-n8-on.teams","00-n8-on.ports"} | {
            f"00-n8-on.port-{i:02d}" for i in range(1,11)}
    root.mkdir()
    (root/"run.sh").write_bytes(script)
    (root/"input-sha256.txt").write_bytes(downloads["SHA256SUMS"])
    (root/"runner-source.py").write_bytes(Path(__file__).read_bytes())
    (root/"host-start.json").write_text(json.dumps(initial,indent=2)+"\n")

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            data = downloads.get(self.path[1:])
            if data is None:
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name = self.path[1:]
            try:
                length = int(self.headers.get("Content-Length","-1"))
            except ValueError:
                self.send_error(400); return
            limit = 32000000 if name.endswith((".stdout",".stderr")) else 2000000
            if name not in allowed or not 0 <= length <= limit or (root/name).exists():
                self.send_error(400); return
            data = self.rfile.read(length)
            if len(data) != length:
                self.send_error(400); return
            temp = root/(name+".partial")
            temp.write_bytes(data)
            temp.rename(root/name)
            self.send_response(201); self.end_headers()

    server = HTTPServer(("127.0.0.1",8901),H)
    t = Thread(target=server.serve_forever,daemon=True)
    t.start()
    try:
        cmd = [sys.executable,str(LAB/"guest-hmp.py"),"--local-id",revision,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o load18.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh load18.sh"],check=True,timeout=30)
        sys.path.insert(0,str(LAB))
        h = importlib.import_module("guest-hmp")
        deadline = time.monotonic()+(1200 if deferred_load or v20_streams is not None else 600)
        index=0
        while time.monotonic()<deadline:
            sample=sample_host(revision)
            if {g["pid"] for g in sample["guests"]} != pids:
                raise RuntimeError("VM inventory changed")
            with (root/"host-samples.jsonl").open("a") as f:
                f.write(json.dumps(sample)+"\n")
            ppm=root/f"frame-{index:03d}.ppm"
            with socket.socket(socket.AF_UNIX) as sock:
                sock.settimeout(8)
                sock.connect(str(HOME/"ai-images"/f"run-local-{revision}"/"haiku-ai-regular-monitor.sock"))
                h.receive_prompt(sock)
                h.exchange(sock,"screendump "+str(ppm))
            subprocess.run(["sips","-s","format","png",str(ppm),"--out",str(ppm.with_suffix(".png"))],check=True,stdout=subprocess.DEVNULL)
            ppm.unlink()
            index+=1
            if (root/"done.txt").exists():
                break
            time.sleep(4)
        else:
            raise TimeoutError("campaign incomplete; preserve guest and logs")
        if (root/"done.txt").read_text().strip()!="0" or "ai_"+revision not in (root/"revision.txt").read_text():
            raise ValueError("completion or revision invalid")
        rows=[]
        for i,(n,state) in enumerate(specs):
            tag=f"{i:02d}-n{n}-{state}"
            mapping=[int(l.split()[0]) for l in (root/(tag+".map")).read_text().splitlines()]
            if len(mapping)!=n:
                raise ValueError("window count")
            r=analyze((root/(tag+".probe")).read_text(),mapping)
            r.update(n=n,state=state,probe_exit=int((root/(tag+".probe-exit")).read_text()),
                     player_exit=int((root/(tag+".exit")).read_text()))
            rows.append(r)
        (root/"summary.json").write_text(json.dumps(rows,indent=2)+"\n")
        print(json.dumps(rows,indent=2))
    finally:
        server.shutdown();server.server_close();t.join()


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("--queues",action="store_true")
    p.add_argument("--deferred-smoke",action="store_true")
    p.add_argument("--deferred-load",action="store_true")
    p.add_argument("--sixteen",action="store_true")
    p.add_argument("--smoke-evidence",type=Path)
    p.add_argument("--v20-streams",type=int,choices=(4,8,16))
    p.add_argument("--v20-evidence",type=Path)
    a=p.parse_args()
    run(a.root,a.queues,a.deferred_smoke,a.deferred_load,a.sixteen,a.smoke_evidence,a.v20_streams,a.v20_evidence)
