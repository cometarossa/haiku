#!/usr/bin/env python3
"""Run the V16 campaign on an already booted guest with focused Terminal."""
import argparse
import hashlib
import importlib
import json
import socket
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from v16_catchup_report import SPECS, SPECS_16, validate

MEDIA = Path(__file__).resolve().parent
LAB = MEDIA.parent
REV = "a1b69d83"
HOME = Path.home() / "Developer/Haiku"


def sample_host(revision=REV):
    rows = subprocess.check_output(["ps", "-axo", "pid=,comm=,%cpu=,rss=,command="], text=True)
    guests = []
    for line in rows.splitlines():
        fields = line.strip().split(None, 4)
        if len(fields) == 5 and Path(fields[4].split(None,1)[0]).name.startswith("qemu-system-"):
            guests.append(dict(pid=int(fields[0]), cpu=fields[2], rss_kib=int(fields[3]), command=fields[4]))
    haiku = [g for g in guests if f"file={HOME}/" in g["command"] or f"unix:{HOME}/" in g["command"]]
    if len(haiku) != 2 or len(guests) != 3 or not any(f"run-local-{revision}/" in g["command"] for g in haiku):
        raise RuntimeError("Unexpected VM inventory; require Beta6, experimental Haiku, Fincept")
    return dict(timestamp=time.time(), guests=guests,
                uptime=subprocess.check_output(["uptime"],text=True).strip())


def view_stats_script(script):
    """Replace the recovery treatment with view diagnostics only."""
    script=script.replace(b'v17-catchup-hd-ram',b'v18-view-hd-ram').replace(b'v17-catchup-ab',b'v18-view-sd')
    old=b'catchup=/boot/home/config/settings/haiku-lab-media-catchup\n'
    if script.count(old)!=1:
        raise ValueError("unexpected treatment marker")
    # The shell variable name is retained, but refers solely to view stats.
    script=script.replace(old,b'catchup=/boot/home/config/settings/haiku-lab-video-view-stats\n')
    anchor=b'for m in "$stats" "$preflight" "$catchup" "$adaptive"; do'
    if script.count(anchor)!=2:
        raise ValueError("unexpected marker precondition")
    script=script.replace(anchor,b'for m in "$stats" "$preflight" "$catchup" "$adaptive" /boot/home/config/settings/haiku-lab-media-catchup; do')
    subprocess.run(["sh","-n"],input=script,check=True)
    return script


def run(root, hd=False, sixteen=False, adaptive=False, view_stats=False):
    if view_stats and sixteen:
        raise ValueError("View diagnostics start with four/eight streams")
    if view_stats:
        adaptive=True  # reuse timing and guard setup, not recovery treatment
    revision = "fb8c2e41" if view_stats else "f960376e" if adaptive else REV
    if hd and sixteen:
        raise ValueError("Choose HD or sixteen-stream SD campaign")
    specs = SPECS_16 if sixteen else SPECS
    initial = sample_host(revision)
    initial_pids = {g["pid"] for g in initial["guests"]}
    long_sd = adaptive and sixteen
    fixture_dir = HOME/"guest-files"/("v17-long-sd" if long_sd else "v16-hd" if hd else "concurrent-gui")
    source_name = "stream-long-sd.mp4" if long_sd else "stream-hd.mp4" if hd else "stream-a.mp4"
    fixture=(fixture_dir/source_name).read_bytes()
    digest=hashlib.sha256(fixture).hexdigest()
    if digest+"  "+source_name not in (fixture_dir/"SHA256SUMS").read_text():
        raise ValueError("fixture hash mismatch")
    script=(MEDIA/"v16-catchup-guest.sh").read_bytes()
    if hd:
        script=(MEDIA/"v16-catchup-hd-guest.sh").read_bytes()
    if sixteen:
        script=(MEDIA/"v16-catchup-16-guest.sh").read_bytes()
    if adaptive:
        # Both treatments get the guard marker; only ON gets catch-up.
        # Preserve the exact derived guest script in the evidence.
        script = script.replace(b'v16-catchup-hd-ram', b'v17-catchup-hd-ram').replace(b'v16-catchup-ab', b'v17-catchup-ab').replace(b'v16-catchup-16-ram', b'v17-catchup-16-long-ram')
        anchor=b'for m in "$stats" "$preflight" "$catchup"; do'
        if script.count(anchor)!=2:
            raise ValueError("unexpected marker precondition")
        script=script.replace(anchor,b'for m in "$stats" "$preflight" "$catchup" "$adaptive"; do')
        script=script.replace(b'for m in "$stats" "$preflight" "$catchup" "$adaptive"; do',b'adaptive=/boot/home/config/settings/haiku-lab-media-catchup-adaptive\nfor m in "$stats" "$preflight" "$catchup" "$adaptive"; do',1)
        script=script.replace(b's=0;p=0;c=0',b's=0;p=0;c=0;a=0')
        script=script.replace(b'cleanup() {',b'cleanup() {\n if test "$a" = 1; then rm -f "$adaptive"; a=0; fi')
        script=script.replace(b'(set -C; : > "$stats"); s=1',b'(set -C; : > "$stats"); s=1\n(set -C; : > "$adaptive"); a=1')
        subprocess.run(["sh","-n"],input=script,check=True)
        # Measure each scripting round trip separately from frame counters.
        anchor=b'   hey -o "$app" get Title of Window "$i"\n   hey -o "$app" get IsPlaying of Window "$i"\n   hey "$app" get Position of Window "$i"'
        if script.count(anchor)!=1:
            raise ValueError("unexpected sample block")
        script=script.replace(anchor,b'   timed_query title hey -o "$app" get Title of Window "$i"\n   timed_query playing hey -o "$app" get IsPlaying of Window "$i"\n   timed_query position hey "$app" get Position of Window "$i"')
        anchor=b'run=0\n'
        if script.count(anchor)!=1:
            raise ValueError("unexpected trial initialization")
        script=script.replace(anchor,b"""timed_query() {
 op="$1"; shift
 query_start=$(system_time)
 query_rc=0
 "$@" || query_rc=$?
 query_end=$(system_time)
 printf '%s %s %s %s %s %s\\n' "$sample" "$i" "$op" "$query_start" "$query_end" "$query_rc" >> "$tag.latency"
 return "$query_rc"
}
run=0
""")
        anchor=b'windows positions stdout stderr exit; do curl'
        if script.count(anchor)!=1:
            raise ValueError("unexpected upload list")
        script=script.replace(anchor,b'windows positions stdout stderr latency exit; do curl')
        subprocess.run(["sh","-n"],input=script,check=True)
    if long_sd:
        # Record when the first Play command starts; the observation window
        # begins after the last Play reply, not before serial dispatch.
        anchor=b' system_time > "$tag.play"\n while read j i; do hey "$app" do Play of Window "$i"; done < "$tag.windows"'
        if script.count(anchor)!=1:
            raise ValueError("unexpected Play dispatch block")
        script=script.replace(anchor,b' system_time > "$tag.dispatch"\n while read j i; do hey "$app" do Play of Window "$i"; done < "$tag.windows"\n system_time > "$tag.play"')
        script=script.replace(b'for ext in start play stop',b'for ext in start dispatch play stop')
        subprocess.run(["sh","-n"],input=script,check=True)
    if view_stats:
        script=view_stats_script(script)
    downloads={"run.sh":script,"stream-a.mp4":fixture,
               "SHA256SUMS":(digest+"  stream-a.mp4\n").encode()}
    allowed={"revision.txt","done.txt"}|{f"{i:02d}-n{n}-{state}.{ext}" for i,(n,state) in enumerate(specs)
            for ext in ("start","play","stop","quit-time","windows","positions","stdout","stderr","exit")}
    if adaptive:
        allowed |= {f"{i:02d}-n{n}-{state}.latency" for i,(n,state) in enumerate(specs)}
    if long_sd:
        allowed |= {f"{i:02d}-n{n}-{state}.dispatch" for i,(n,state) in enumerate(specs)}
    root.mkdir()
    (root/"runner-source.py").write_bytes(Path(__file__).read_bytes())
    (root/"report-source.py").write_bytes((MEDIA/"v16_catchup_report.py").read_bytes())
    (root/"run.sh").write_bytes(script)
    (root/"fixture-sha256.txt").write_bytes(downloads["SHA256SUMS"])
    if hd or long_sd:
        (root/"fixture-ffprobe.json").write_bytes((fixture_dir/"ffprobe.json").read_bytes())
    (root/"host-start.json").write_text(json.dumps(initial,indent=2)+"\n")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            data=downloads.get(self.path[1:])
            if data is None:
                self.send_error(404);return
            self.send_response(200)
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def do_PUT(self):
            name=self.path[1:]
            try:
                length=int(self.headers.get("Content-Length","-1"))
            except ValueError:
                self.send_error(400);return
            # Verbose dropped-frame logs can exceed 2 MB under stress.
            # Increase only stdout/stderr allowance; keep finite bounds.
            limit = 32000000 if name.endswith((".stdout",".stderr")) else 2000000
            if name not in allowed or not 0<=length<=limit or (root/name).exists():
                self.send_error(400);return
            data=self.rfile.read(length)
            if len(data)!=length:
                self.send_error(400);return
            # Publish atomically so a partial file cannot reach validation.
            temp=root/(name+".partial")
            temp.write_bytes(data)
            temp.rename(root/name)
            self.send_response(201)
            self.end_headers()

    server=HTTPServer(("127.0.0.1",8901),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        cmd=[sys.executable,str(LAB/"guest-hmp.py"),"--local-id",revision,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o "+("catchup16sd.sh" if sixteen else "catchuphd.sh" if hd else "catchup16.sh")],check=True,timeout=30)
        subprocess.run(cmd+["sh "+("catchup16sd.sh" if sixteen else "catchuphd.sh" if hd else "catchup16.sh")],check=True,timeout=30)
        sys.path.insert(0,str(LAB))
        h=importlib.import_module("guest-hmp")
        deadline=time.monotonic()+(900 if sixteen else 600 if hd else 420)
        index=0
        last_done=0
        last_screen=0
        while time.monotonic()<deadline:
            sample=sample_host(revision)
            if {g["pid"] for g in sample["guests"]}!=initial_pids:
                raise RuntimeError("VM inventory changed")
            with (root/"host-samples.jsonl").open("a") as f:
                f.write(json.dumps(sample)+"\n")
            if time.monotonic()-last_screen>=4:
                # Short HMP connection; do not reserve the monitor for the campaign.
                ppm=root/f"frame-{index:03d}.ppm"
                png=ppm.with_suffix(".png")
                with socket.socket(socket.AF_UNIX) as sock:
                    sock.settimeout(8)
                    sock.connect(str(HOME/"ai-images"/f"run-local-{revision}"/"haiku-ai-regular-monitor.sock"))
                    h.receive_prompt(sock)
                    h.exchange(sock,"screendump "+str(ppm))
                subprocess.run(["sips","-s","format","png",str(ppm),"--out",str(png)],check=True,stdout=subprocess.DEVNULL)
                ppm.unlink()
                last_screen=time.monotonic()
                index+=1
            for i,(n,state) in enumerate(specs):
                tag=f"{i:02d}-n{n}-{state}"
                e=root/(tag+".exit")
                if e.exists() and e.read_text().strip()!="0":
                    raise RuntimeError(f"{tag} guest exit failure")
                w=root/(tag+".windows")
                if w.exists() and len(w.read_text().splitlines())!=n:
                    raise RuntimeError(f"{tag} window identity failure")
            # On partial invalid evidence preserve files and continue collecting
            # subsequent runs, rather than interrupt a running guest campaign.
            done=sum(1 for f in root.glob("*.exit"))
            if done!=last_done:
                print(f"Collected {done}/{len(specs)} trials",flush=True)
                last_done=done
            if (root/"done.txt").exists():
                break
            time.sleep(2)
        else:
            raise TimeoutError("campaign incomplete; retain logs")
        (root/"host-end.json").write_text(json.dumps(sample_host(revision),indent=2)+"\n")
        report=validate(root,specs=specs,revision=revision,require_no_activation=view_stats or (adaptive and hd),require_latency=adaptive,require_dispatch=long_sd,require_view_stats=view_stats)
        (root/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
        print("V16_CAMPAIGN_PASS",json.dumps(report["pairs"],indent=2),flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("--hd",action="store_true")
    p.add_argument("--sixteen",action="store_true")
    p.add_argument("--adaptive",action="store_true")
    p.add_argument("--view-stats",action="store_true")
    a=p.parse_args()
    run(a.root,a.hd,a.sixteen,a.adaptive,a.view_stats)
