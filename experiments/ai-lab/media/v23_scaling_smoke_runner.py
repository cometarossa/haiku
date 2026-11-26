"""Read-only native smoke for the scaling settings helper."""
import hashlib
import json
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from threading import Thread
from v16_catchup_runner import HOME,MEDIA,LAB,sample_host

SHA="f6ffdba624ddc573948ba4d219dde3f0d9647de43b3368ad4e3ec873c424494f"
REV="4ae8e7ea"

def validate(root):
    lines=(root/"smoke.txt").read_text().splitlines()
    if len(lines)!=10 or "ai_"+REV not in lines[0] or lines[1] not in ("original scaleBilinear=0","original scaleBilinear=1"):
        raise ValueError("revision or original setting")
    expected=["nearest scaleBilinear=0","bilinear scaleBilinear=1","nearest readback scaleBilinear=0","bilinear readback scaleBilinear=1","exclusive output PASS","active settings unchanged PASS"]
    if lines[2:8]!=expected or lines[8].split()[0]!=lines[9].split()[0] or len(lines[8].split()[0])!=64 or (root/"done.txt").read_text().strip()!="0":
        raise ValueError("settings smoke mismatch")
    return dict(valid=True,original=lines[1],sha256=lines[8].split()[0])

def run(root):
    helper=(HOME/"guest-files/scaling-helper-83f428d4/scaling-settings").read_bytes()
    if hashlib.sha256(helper).hexdigest()!=SHA:raise ValueError("helper checksum")
    script=(MEDIA/"v23-scaling-smoke-guest.sh").read_bytes()
    subprocess.run(["sh","-n"],input=script,check=True)
    downloads={"scaling-settings":helper,"SHA256SUMS":(SHA+"  scaling-settings\n").encode(),"run.sh":script}
    initial=sample_host(REV);pids={g["pid"] for g in initial["guests"]}
    root.mkdir()
    (root/"run.sh").write_bytes(script)
    (root/"input-sha256.txt").write_bytes(downloads["SHA256SUMS"])
    (root/"host-start.json").write_text(json.dumps(initial,indent=2)+"\n")
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            data=downloads.get(self.path[1:])
            if data is None:self.send_error(404);return
            self.send_response(200);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
        def do_PUT(self):
            name=self.path[1:]
            length=int(self.headers.get("Content-Length","-1"))
            if name not in ("smoke.txt","done.txt") or not 0<=length<=8192 or (root/name).exists():
                self.send_error(400);return
            data=self.rfile.read(length)
            if len(data)!=length:self.send_error(400);return
            (root/(name+".partial")).write_bytes(data)
            (root/(name+".partial")).rename(root/name)
            self.send_response(201);self.end_headers()
    server=HTTPServer(("127.0.0.1",8901),H)
    t=Thread(target=server.serve_forever,daemon=True);t.start()
    try:
        cmd=[sys.executable,str(LAB/"guest-hmp.py"),"--local-id",REV,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o scaling23.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh scaling23.sh"],check=True,timeout=30)
        for _ in range(30):
            if (root/"done.txt").exists():break
            time.sleep(1)
        else:raise TimeoutError("smoke incomplete")
        final=sample_host(REV)
        if {g["pid"] for g in final["guests"]}!=pids:raise ValueError("VM inventory changed")
        (root/"host-end.json").write_text(json.dumps(final,indent=2)+"\n")
        result=validate(root)
        (root/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
    finally:
        server.shutdown();server.server_close();t.join()

if __name__=="__main__":run(Path(sys.argv[1]))
