#!/usr/bin/env python3
"""AI-assisted fork: bounded, same-binary app_server profile smoke on macOS."""
import argparse
import csv
import hashlib
import importlib
import io
import re
import socket
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from appwin_profile import parse

LAB = Path(__file__).resolve().parents[1]
BASE = Path.home() / "Developer/Haiku"
sys.path.insert(0, str(LAB))
hmp = importlib.import_module("guest-hmp")
OLD = BASE / "guest-results/drawing-fixed-work-corrected-20261125"
MARKER = "/boot/home/config/settings/haiku-lab-appserver-profile"
PORT = 8899


def guest_script(mode, workers, batch, enabled):
    return f"""#!/bin/sh
set -eu
cd /boot/home
mkdir -p appwin-profile-lab
cd appwin-profile-lab
for f in bitmap SHA256SUMS; do curl -fsS --max-time 20 http://10.0.2.2:{PORT}/"$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x bitmap
marker={MARKER}
test ! -e "$marker" && test ! -L "$marker"
created=0
cleanup() {{ if test "$created" = 1; then rm -f "$marker"; fi; }}
trap cleanup 0
trap 'exit 125' 1 2 15
if test {int(enabled)} = 1; then
    (set -C; : > "$marker")
    created=1
fi
rc=0
./bitmap {mode} {workers} {batch} > result.csv 2> errors.txt || rc=$?
cleanup
created=0
test ! -e "$marker" && test ! -L "$marker"
uname -a > revision.txt
printf '%s\\n' "$rc" > exit.txt
for f in result.csv errors.txt revision.txt exit.txt; do curl -fsS --max-time 20 -T "$f" http://10.0.2.2:{PORT}/"$f"; done
"""


def verify_client(data, mode, workers, batch):
    rows = list(csv.reader(io.StringIO(data)))
    if len(rows) != workers:
        raise ValueError("incorrect worker row count")
    ids, ends, starts, spans = set(), [], [], set()
    for row in rows:
        if len(row) != 10 or row[0] != mode:
            raise ValueError("malformed worker row")
        n, b, worker, draws, start, end, span, checked, errors = map(int, row[1:])
        if ((n, b, draws, checked, errors) != (workers, batch, 4096//workers, 65536, 0)
                or worker not in range(workers) or worker in ids
                or not 0 <= start < end <= span):
            raise ValueError("worker verification failure")
        ids.add(worker); starts.append(start); ends.append(end); spans.add(span)
    if len(spans) != 1 or min(starts) != 0 or max(ends) != next(iter(spans)):
        raise ValueError("inconsistent elapsed times")
    return max(ends)


def capture(serial, offset):
    with serial.open("rb") as f:
        f.seek(offset)
        return f.read()


def run(args):
    if args.control:
        target = ["--run-id", "45504533141"]
        folder = BASE / "ai-images/run-45504533141"
        revision = "ai_87d37528"
    else:
        target = ["--local-id", args.local_id]
        folder = BASE / "ai-images" / ("run-local-" + args.local_id)
        revision = "ai_" + args.local_id
    monitor = folder / "haiku-ai-regular-monitor.sock"
    serial = folder / "haiku-ai-regular-serial.log"
    if not monitor.is_socket() or not serial.is_file():
        raise RuntimeError("expected running experimental guest")
    binary = (OLD / "bitmap").read_bytes()
    manifest = (OLD / "SHA256SUMS").read_text()
    if manifest != hashlib.sha256(binary).hexdigest() + "  bitmap\n":
        raise ValueError("binary hash mismatch")
    root = BASE / "guest-results" / ("appwin-profile-" + time.strftime("%Y%m%d-%H%M%S"))
    root.mkdir()
    (root / "binary-sha256.txt").write_text(manifest)
    plan = [("threads", 1, 64, False)] if args.control else [
        (mode, workers, batch, enabled)
        for mode, workers, batch in [("threads", 1, 64), ("threads", 4, 64), ("teams", 4, 64)]
        for enabled in (False, True, True, False)
    ]
    for i, (mode, workers, batch, enabled) in enumerate(plan):
        dest = root / ("%02d-%s-%d-%d-%s" % (i, mode, workers, batch, "on" if enabled else "off"))
        dest.mkdir()
        script = guest_script(mode, workers, batch, enabled)
        (dest / "run.sh").write_text(script)
        downloads = {"run.sh": script.encode(), "bitmap": binary, "SHA256SUMS": manifest.encode()}
        uploads = {"result.csv", "errors.txt", "revision.txt", "exit.txt"}

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
                try:
                    size = int(self.headers.get("Content-Length", "-1"))
                except ValueError:
                    size = -1
                if name not in uploads or not 0 <= size <= 1000000 or (dest/name).exists():
                    self.send_error(400); return
                data = self.rfile.read(size)
                if len(data) != size:
                    self.send_error(400); return
                (dest/name).write_bytes(data)
                self.send_response(201); self.end_headers()

        server = HTTPServer(("127.0.0.1", PORT), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        offset = serial.stat().st_size
        try:
            with socket.socket(socket.AF_UNIX) as sock:
                sock.settimeout(8)
                sock.connect(str(monitor))
                hmp.receive_prompt(sock)
                hmp.exchange(sock, "mouse_move 10 10")
                hmp.exchange(sock, "sendkey shift")
            cmd = [sys.executable, str(LAB / "guest-hmp.py")] + target
            subprocess.run(cmd + ["type", f"curl -fsS http://10.0.2.2:{PORT}/run.sh -o appwinlab.sh"], check=True, timeout=30)
            subprocess.run(cmd + ["type", "sh appwinlab.sh"], check=True, timeout=30)
            deadline = time.monotonic() + 60
            while not (dest / "exit.txt").exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("guest did not complete; inspect marker and terminal before retry")
                time.sleep(.2)
            time.sleep(1)
            raw = capture(serial, offset)
            # Allow end records to arrive, but never interpret incomplete lines.
            if enabled:
                while (raw.count(b"LAB_APPWIN_END ") < workers or not raw.endswith(b"\n")) and time.monotonic() < deadline:
                    time.sleep(.2)
                    raw = capture(serial, offset)
            (dest / "serial.txt").write_bytes(raw)
            if (dest / "exit.txt").read_text().strip() != "0" or (dest / "errors.txt").read_text().strip():
                raise ValueError("guest reported failure")
            if revision not in (dest / "revision.txt").read_text():
                raise ValueError("unexpected guest revision")
            elapsed = verify_client((dest / "result.csv").read_text(), mode, workers, batch)
            records = parse(raw.decode(errors="replace"), workers if enabled else 0, 4096 if enabled else 0)
            # parse() validates counts and completion. Preserve exact serial.
            import json
            (dest / "profile.json").write_text(json.dumps(records, indent=2) + "\n")
            print(dest.name, "PASS", elapsed, "us", len(records), "profiles", flush=True)
        finally:
            (dest / "serial-final.txt").write_bytes(capture(serial, offset))
            server.shutdown(); server.server_close(); thread.join()
    print("SMOKE_COMPLETE", root, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--control", action="store_true")
    group.add_argument("--local-id")
    args = p.parse_args()
    if args.local_id is not None and re.fullmatch("[0-9a-f]{8}", args.local_id) is None:
        p.error("invalid local ID")
    run(args)


if __name__ == "__main__":
    main()
