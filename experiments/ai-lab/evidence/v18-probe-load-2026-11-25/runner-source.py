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


def run(root):
    initial = sample_host(REV)
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
    subprocess.run(["sh","-n"],input=script,check=True)
    downloads["run.sh"] = script
    allowed = {"revision.txt","done.txt"} | {
        f"{i:02d}-n{n}-on.{ext}" for i,n in enumerate(SPECS)
        for ext in ("dispatch","play","stop","map","probe","probe-stderr","probe-exit",
                    "start","quit-time","windows","positions","stdout","stderr","exit")}
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
        cmd = [sys.executable,str(LAB/"guest-hmp.py"),"--local-id",REV,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o load18.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh load18.sh"],check=True,timeout=30)
        sys.path.insert(0,str(LAB))
        h = importlib.import_module("guest-hmp")
        deadline = time.monotonic()+600
        index=0
        while time.monotonic()<deadline:
            sample=sample_host(REV)
            if {g["pid"] for g in sample["guests"]} != pids:
                raise RuntimeError("VM inventory changed")
            with (root/"host-samples.jsonl").open("a") as f:
                f.write(json.dumps(sample)+"\n")
            ppm=root/f"frame-{index:03d}.ppm"
            with socket.socket(socket.AF_UNIX) as sock:
                sock.settimeout(8)
                sock.connect(str(HOME/"ai-images"/f"run-local-{REV}"/"haiku-ai-regular-monitor.sock"))
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
        if (root/"done.txt").read_text().strip()!="0" or "ai_"+REV not in (root/"revision.txt").read_text():
            raise ValueError("completion or revision invalid")
        rows=[]
        for i,n in enumerate(SPECS):
            tag=f"{i:02d}-n{n}-on"
            mapping=[int(l.split()[0]) for l in (root/(tag+".map")).read_text().splitlines()]
            if len(mapping)!=n:
                raise ValueError("window count")
            r=analyze((root/(tag+".probe")).read_text(),mapping)
            r.update(n=n,probe_exit=int((root/(tag+".probe-exit")).read_text()),
                     player_exit=int((root/(tag+".exit")).read_text()))
            rows.append(r)
        (root/"summary.json").write_text(json.dumps(rows,indent=2)+"\n")
        print(json.dumps(rows,indent=2))
    finally:
        server.shutdown();server.server_close();t.join()


if __name__=="__main__":
    run(Path(sys.argv[1]))
