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
from v16_catchup_report import SPECS, validate

MEDIA = Path(__file__).resolve().parent
LAB = MEDIA.parent
REV = "a1b69d83"
HOME = Path.home() / "Developer/Haiku"


def sample_host():
    rows = subprocess.check_output(["ps", "-axo", "pid=,comm=,%cpu=,rss=,command="], text=True)
    guests = []
    for line in rows.splitlines():
        fields = line.strip().split(None, 4)
        if len(fields) == 5 and Path(fields[4].split(None,1)[0]).name.startswith("qemu-system-"):
            guests.append(dict(pid=int(fields[0]), cpu=fields[2], rss_kib=int(fields[3]), command=fields[4]))
    haiku = [g for g in guests if f"file={HOME}/" in g["command"] or f"unix:{HOME}/" in g["command"]]
    if len(haiku) != 2 or len(guests) != 3 or not any(f"run-local-{REV}/" in g["command"] for g in haiku):
        raise RuntimeError("Unexpected VM inventory; require Beta6, V16, Fincept")
    return dict(timestamp=time.time(), guests=guests,
                uptime=subprocess.check_output(["uptime"],text=True).strip())


def run(root):
    initial = sample_host()
    initial_pids = {g["pid"] for g in initial["guests"]}
    fixture_dir = HOME/"guest-files/concurrent-gui"
    fixture=(fixture_dir/"stream-a.mp4").read_bytes()
    digest=hashlib.sha256(fixture).hexdigest()
    if digest+"  stream-a.mp4" not in (fixture_dir/"SHA256SUMS").read_text():
        raise ValueError("fixture hash mismatch")
    script=(MEDIA/"v16-catchup-guest.sh").read_bytes()
    downloads={"run.sh":script,"stream-a.mp4":fixture,
               "SHA256SUMS":(digest+"  stream-a.mp4\n").encode()}
    allowed={"revision.txt","done.txt"}|{f"{i:02d}-n{n}-{state}.{ext}" for i,(n,state) in enumerate(SPECS)
            for ext in ("start","play","stop","quit-time","windows","positions","stdout","stderr","exit")}
    root.mkdir()
    (root/"run.sh").write_bytes(script)
    (root/"fixture-sha256.txt").write_bytes(downloads["SHA256SUMS"])
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
            if name not in allowed or not 0<=length<=2000000 or (root/name).exists():
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
        cmd=[sys.executable,str(LAB/"guest-hmp.py"),"--local-id",REV,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o catchup16.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh catchup16.sh"],check=True,timeout=30)
        sys.path.insert(0,str(LAB))
        h=importlib.import_module("guest-hmp")
        deadline=time.monotonic()+420
        index=0
        last_done=0
        last_screen=0
        while time.monotonic()<deadline:
            sample=sample_host()
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
                    sock.connect(str(HOME/"ai-images"/f"run-local-{REV}"/"haiku-ai-regular-monitor.sock"))
                    h.receive_prompt(sock)
                    h.exchange(sock,"screendump "+str(ppm))
                subprocess.run(["sips","-s","format","png",str(ppm),"--out",str(png)],check=True,stdout=subprocess.DEVNULL)
                ppm.unlink()
                last_screen=time.monotonic()
                index+=1
            for i,(n,state) in enumerate(SPECS):
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
                print(f"Collected {done}/{len(SPECS)} trials",flush=True)
                last_done=done
            if (root/"done.txt").exists():
                break
            time.sleep(2)
        else:
            raise TimeoutError("campaign incomplete; retain logs")
        (root/"host-end.json").write_text(json.dumps(sample_host(),indent=2)+"\n")
        report=validate(root)
        (root/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
        print("V16_CAMPAIGN_PASS",json.dumps(report["pairs"],indent=2),flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    a=p.parse_args()
    run(a.root)
