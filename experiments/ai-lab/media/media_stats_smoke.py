#!/usr/bin/env python3
"""Run isolated V15 native smoke over the existing local HMP guest channel."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from media_stats_report import parse, summarize

MEDIA = Path(__file__).resolve().parent
LAB = MEDIA.parent


def validate(root, revision):
    if (root / "done.txt").read_text().strip() != "0":
        raise ValueError("guest did not complete")
    if "ai_" + revision not in (root / "revision.txt").read_text():
        raise ValueError("guest revision mismatch")
    results = {}
    for state in ("off", "on"):
        p = root / state
        def read(ext):
            return p.with_suffix("." + ext).read_text()
        if read("exit").strip() != "0":
            raise ValueError("player exit failure")
        text = read("positions")
        positions = [int(x) for x in re.findall(r"\(B_INT64_TYPE\) : (\d+)", text)]
        if text.count("\ntrue\n") != 3 or len(positions) != 3 or not all(b > a for a,b in zip(positions,positions[1:])):
            raise ValueError("playback not advancing")
        start, stop = int(read("start")), int(read("stop"))
        if not 0 < start < stop:
            raise ValueError("invalid guest clock")
        log = read("log")
        if log.count("LAB_MEDIA_OVERLAY_PREFLIGHT") != 1 or "trying without overlays" in log:
            raise ValueError("preflight treatment mismatch")
        records = parse(log)
        summary = summarize(records, state == "on")
        for row in records["CONSUMER"]:
            # Target may also receive a buffer during shutdown; first
            # target must belong to the observed live playback interval.
            if row["first_target_us"] and not start <= row["first_target_us"] <= stop:
                raise ValueError("first target outside playback")
        results[state] = {"start_us": start, "stop_us": stop,
                          "positions_us": positions, "stats": summary,
                          "raw_records": records}
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--revision", required=True)
    p.add_argument("--validate-only", action="store_true")
    args = p.parse_args()
    if not re.fullmatch("[0-9a-f]{8}", args.revision):
        p.error("invalid revision")
    root = args.root
    if args.validate_only:
        print(json.dumps(validate(root, args.revision), indent=2))
        return
    fixture_root = Path.home() / "Developer/Haiku/guest-files/concurrent-gui"
    fixture = (fixture_root / "stream-a.mp4").read_bytes()
    digest = hashlib.sha256(fixture).hexdigest()
    if digest + "  stream-a.mp4" not in (fixture_root / "SHA256SUMS").read_text():
        raise ValueError("fixture hash mismatch")
    root.mkdir()
    script = (MEDIA / "media-stats-smoke-guest.sh").read_bytes()
    downloads = {"run.sh": script, "stream-a.mp4": fixture,
                 "SHA256SUMS": (digest + "  stream-a.mp4\n").encode()}
    (root/"run.sh").write_bytes(script)
    (root/"fixture-sha256.txt").write_bytes(downloads["SHA256SUMS"])
    allowed = {"revision.txt", "done.txt"} | {f"{state}.{ext}" for state in ("off","on") for ext in ("start","stop","log","positions","quit","exit")}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            data = downloads.get(self.path[1:])
            if data is None:
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def do_PUT(self):
            name = self.path[1:]
            length = int(self.headers.get("Content-Length", "-1"))
            if name not in allowed or not 0 <= length <= 2000000 or (root/name).exists():
                self.send_error(400); return
            data = self.rfile.read(length)
            if len(data) != length:
                self.send_error(400); return
            (root/name).write_bytes(data)
            self.send_response(201)
            self.end_headers()
    server = HTTPServer(("127.0.0.1",8901), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        cmd = [sys.executable, str(LAB/"guest-hmp.py"), "--local-id",args.revision,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o stats15.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh stats15.sh"],check=True,timeout=30)
        deadline = time.monotonic()+120
        while not (root/"done.txt").exists():
            if any(f.read_text().strip() != "0" for f in root.glob("*.exit")):
                raise RuntimeError("guest player failed")
            if time.monotonic()>deadline:
                raise TimeoutError("native smoke incomplete")
            time.sleep(.3)
        results=validate(root,args.revision)
        (root/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
        print("V15_NATIVE_SMOKE_PASS",json.dumps(results,indent=2),flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
