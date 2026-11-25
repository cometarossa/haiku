#!/usr/bin/env python3
"""AI-assisted fork: bounded, same-binary bitmap warm lifecycle smoke on macOS."""
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



LAB = Path(__file__).resolve().parents[1]
BASE = Path.home() / "Developer/Haiku"
sys.path.insert(0, str(LAB))
hmp = importlib.import_module("guest-hmp")
OLD = BASE / "guest-results/drawing-white-lifecycle-20261125"
MARKER = "/boot/home/config/settings/haiku-lab-bitmap-warm"
PORT = 8899


def guest_script(mode, workers, batch, enabled):
    command = mode if mode in ("lab", "ordinary") else f"{mode} {workers} {batch}"
    return f"""#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-warm-lab
cd bitmap-warm-lab
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
./bitmap {command} > result.csv 2> errors.txt || rc=$?
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
    ids, ends, starts, spans, lifetimes, setups = set(), [], [], set(), set(), []
    for row in rows:
        if len(row) != 13 or row[0] != mode:
            raise ValueError("malformed worker row")
        n, b, worker, draws, start, end, span, checked, errors, setup, life, white = map(int, row[1:])
        if ((n, b, draws, checked, errors, white) != (workers, batch, 4096//workers, 65536, 0, 0, 0)
                or worker not in range(workers) or worker in ids
                or not 0 <= start < end <= span <= life or not 0 <= setup <= life):
            raise ValueError("worker verification failure")
        ids.add(worker); starts.append(start); ends.append(end); spans.add(span)
        lifetimes.add(life); setups.append(setup)
    if len(spans) != 1 or len(lifetimes) != 1 or min(starts) != 0 or max(ends) != next(iter(spans)):
        raise ValueError("inconsistent elapsed times")
    return dict(render_us=max(ends), lifecycle_us=lifetimes.pop(), max_setup_us=max(setups))


ELIGIBILITY = {
    "eligible": (262144,262144,65536),
    "boundary": (1048576,1048576,262144),
    "oversize": (2097152,2097152,524288),
    "no-clear": (262144,0,65536),
    "rgb16": (131072,131072,0),
    "no-views": (262144,262144,0),
    "neighbor": (4096,4096,0),
}


def verify_eligibility(data):
    rows = list(csv.reader(io.StringIO(data)))
    if len(rows) != len(ELIGIBILITY):
        raise ValueError("incorrect eligibility row count")
    seen = set()
    for row in rows:
        if len(row) != 5 or row[0] not in ELIGIBILITY or row[0] in seen:
            raise ValueError("invalid eligibility row")
        if tuple(map(int, row[1:])) != ELIGIBILITY[row[0]] + (0,):
            raise ValueError("eligibility pixel or byte check failed")
        seen.add(row[0])
    return {"cases": len(seen)}


def parse(text, expected, mode):
    sizes = [262144, 1048576] if expected and mode == "lab" else [262144] * expected
    records = []
    for line in text.splitlines():
        if not line.startswith("LAB_BITMAP_WARM"):
            continue
        match = re.fullmatch(r"LAB_BITMAP_WARM team=(\d+) token=(\d+) bytes=(\d+) us=(\d+)", line)
        if not match:
            raise ValueError("malformed warm record: " + line)
        team, token, length, elapsed = map(int, match.groups())
        records.append(dict(team=team,token=token,bytes=length,us=elapsed))
    if sorted(r["bytes"] for r in records) != sizes or len({(r["team"],r["token"]) for r in records}) != expected:
        raise ValueError("unexpected warm records")
    if expected and len({r["team"] for r in records}) != (1 if mode in ("threads", "lab") else expected):
        raise ValueError("unexpected client team count")
    return records


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
        raise RuntimeError("expected running experimental guest; confirm Terminal focus before invocation")
    source = BASE / "guest-results/bitmap-warm-eligibility-20261125" if args.eligibility else OLD
    binary = (source / "bitmap").read_bytes()
    manifest = (source / "SHA256SUMS").read_text()
    if manifest != hashlib.sha256(binary).hexdigest() + "  bitmap\n":
        raise ValueError("binary hash mismatch")
    root = BASE / "guest-results" / ("bitmap-warm-" + time.strftime("%Y%m%d-%H%M%S"))
    root.mkdir()
    (root / "binary-sha256.txt").write_text(manifest)
    plan = [("threads", 1, 64, False)] if args.control else [
        (mode, workers, batch, enabled)
        for mode, workers, batch in [("threads", 4, 64), ("teams", 4, 64), ("threads", 1, 64)]
        for enabled in (False, True, True, False, False, True)
    ]
    if args.eligibility:
        plan = [(mode, 1, 64, enabled) for enabled in (False, True)
                for mode in ("lab", "ordinary")]
    for i, (mode, workers, batch, enabled) in enumerate(plan):
        expected = 0 if (not enabled or args.expect_no_warm or args.control) else (
            (2 if mode == "lab" else 0) if args.eligibility else workers)
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
            subprocess.run(cmd + ["type", f"curl -fsS http://10.0.2.2:{PORT}/run.sh -o bitmapwarmlab.sh"], check=True, timeout=30)
            subprocess.run(cmd + ["type", "sh bitmapwarmlab.sh"], check=True, timeout=30)
            deadline = time.monotonic() + 60
            while not (dest / "exit.txt").exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("guest did not complete; inspect marker and terminal before retry")
                time.sleep(.2)
            time.sleep(1)
            raw = capture(serial, offset)
            # Allow end records to arrive, but never interpret incomplete lines.
            if expected:
                while (raw.count(b"LAB_BITMAP_WARM ") < expected or not raw.endswith(b"\n")) and time.monotonic() < deadline:
                    time.sleep(.2)
                    raw = capture(serial, offset)
            (dest / "serial.txt").write_bytes(raw)
            if (dest / "exit.txt").read_text().strip() != "0" or (dest / "errors.txt").read_text().strip():
                raise ValueError("guest reported failure")
            if revision not in (dest / "revision.txt").read_text():
                raise ValueError("unexpected guest revision")
            data = (dest / "result.csv").read_text()
            elapsed = verify_eligibility(data) if args.eligibility else verify_client(data, mode, workers, batch)
            records = parse(raw.decode(errors="replace"), expected, mode)
            # parse() validates counts and completion. Preserve exact serial.
            import json
            (dest / "profile.json").write_text(json.dumps(records, indent=2) + "\n")
            print(dest.name, "PASS", elapsed, len(records), "warm records", flush=True)
        finally:
            (dest / "serial-final.txt").write_bytes(capture(serial, offset))
            server.shutdown(); server.server_close(); thread.join()
    print("SMOKE_COMPLETE", root, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--control", action="store_true")
    group.add_argument("--local-id")
    p.add_argument("--eligibility", action="store_true")
    p.add_argument("--expect-no-warm", action="store_true",
                   help="negative control on a revision without the experiment")
    args = p.parse_args()
    if args.local_id is not None and re.fullmatch("[0-9a-f]{8}", args.local_id) is None:
        p.error("invalid local ID")
    run(args)


if __name__ == "__main__":
    main()
