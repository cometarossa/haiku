"""Run native V21 pixel/timestamp smoke from a confirmed guest Terminal."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from v16_catchup_runner import HOME, MEDIA, LAB, sample_host
from v21_decode_report import REV, FIXTURE_SHA, validate


def repeat_script(script):
    script=script.replace(b'v21-decode-smoke',b'v21-decode-repeat-retry')
    script=script.replace(b'for state in off on; do',b'run=0\nfor state in off on on off off on on off; do\n tag=$(printf "%02d-%s" "$run" "$state")')
    script=script.replace(b'"$state.',b'"$tag.').replace(b'$base/$state.',b'$base/$tag.')
    script=script.replace(b' test "$rc" = 0\ndone',b' test "$rc" = 0\n if test "$own_single" = 1; then rm -f "$single"; own_single=0; fi\n run=$((run+1))\ndone')
    return script


def run(root,repeat=False,gop=False):
    if repeat and gop:
        raise ValueError("choose one campaign")
    initial = sample_host(REV)
    pids = {g["pid"] for g in initial["guests"]}
    src = HOME/"guest-files"
    fixture = (src/"concurrent-gui/stream-a.mp4").read_bytes()
    binary = (src/"frame-digest-d087dfa7/frame-digest").read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    if digest != (src/"frame-digest-d087dfa7/SHA256SUMS").read_text().split()[0]:
        raise ValueError("probe checksum")
    if hashlib.sha256(fixture).hexdigest() != FIXTURE_SHA:
        raise ValueError("fixture checksum")
    script = (MEDIA/"v21-decode-smoke-guest.sh").read_bytes()
    if repeat:
        script=repeat_script(script)
    subprocess.run(["sh","-n"],input=script,check=True)
    manifest = f"{digest}  frame-digest\n{FIXTURE_SHA}  stream-a.mp4\n".encode()
    downloads = {"run.sh":script,"frame-digest":binary,"stream-a.mp4":fixture,"SHA256SUMS":manifest}
    tags = [f"{i:02d}-{state}" for i,state in enumerate(("off","on","on","off")*2)] if repeat else ["off","on"]
    if gop:
        from v22_gop_decode_report import HASHES,TAGS
        script=(MEDIA/"v22-gop-decode-guest.sh").read_bytes()
        subprocess.run(["sh","-n"],input=script,check=True)
        downloads={"run.sh":script,"frame-digest":binary}
        manifest=f"{digest}  frame-digest\n".encode()
        for g,expected in HASHES.items():
            name=f"gop-{g}.mp4"
            data=(src/"v22-gop"/name).read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:
                raise ValueError("GOP fixture checksum")
            downloads[name]=data
            manifest+=f"{expected}  {name}\n".encode()
        downloads["SHA256SUMS"]=manifest
        tags=TAGS
    allowed = {"revision.txt","done.txt"} | {
        f"{state}.{ext}" for state in tags
        for ext in ("start","stop","stdout","stderr","exit")}
    root.mkdir()
    (root/"run.sh").write_bytes(script)
    (root/"input-sha256.txt").write_bytes(manifest)
    (root/"runner-source.py").write_bytes(Path(__file__).read_bytes())
    (root/"host-start.json").write_text(json.dumps(initial,indent=2)+"\n")

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            data = downloads.get(self.path[1:])
            if data is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name=self.path[1:]
            try:
                length=int(self.headers.get("Content-Length","-1"))
            except ValueError:
                self.send_error(400)
                return
            if name not in allowed or not 0<=length<=2000000 or (root/name).exists():
                self.send_error(400)
                return
            data=self.rfile.read(length)
            if len(data)!=length:
                self.send_error(400)
                return
            partial=root/(name+".partial")
            partial.write_bytes(data)
            partial.rename(root/name)
            self.send_response(201)
            self.end_headers()

    server=HTTPServer(("127.0.0.1",8901),H)
    t=Thread(target=server.serve_forever,daemon=True)
    t.start()
    try:
        cmd=[sys.executable,str(LAB/"guest-hmp.py"),"--local-id",REV,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o digest21.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh digest21.sh"],check=True,timeout=30)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            sample=sample_host(REV)
            if {g["pid"] for g in sample["guests"]}!=pids:
                raise RuntimeError("VM inventory changed")
            with (root/"host-samples.jsonl").open("a") as f:
                f.write(json.dumps(sample)+"\n")
            if (root/"done.txt").exists():
                break
            for state in tags:
                path=root/(state+".exit")
                if path.exists() and path.read_text().strip()!="0":
                    raise RuntimeError(f"{state} decode failed; preserve evidence")
            time.sleep(2)
        else:
            raise TimeoutError("decode smoke incomplete; inspect guest")
        from v21_decode_report import validate_repeat
        if gop:
            from v22_gop_decode_report import validate as validate_gop
            result=validate_gop(root)
        else:
            result=validate_repeat(root) if repeat else validate(root)
        (root/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
    finally:
        server.shutdown()
        server.server_close()
        t.join()


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("root",type=Path)
    p.add_argument("--repeat",action="store_true")
    p.add_argument("--gop",action="store_true")
    a=p.parse_args()
    run(a.root,a.repeat,a.gop)
