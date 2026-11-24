#!/usr/bin/env python3
"""AI-assisted independent Haiku fork. Explicit disposable-guest test only."""
import argparse
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import subprocess
from threading import Thread
import time

LAB = Path(__file__).resolve().parent.parent
BASE = Path.home() / "Developer/Haiku"
SOURCES = {
    "copyerr": "ipc-sweep-20261124",
    "sweep": "ipc-sweep-20261124",
    "topology": "ipc-topology-20261124",
    "cost": "ipc-cost-20261124",
    "wake": "scheduler-wakeup-20261124",
    "fair": "scheduler-throughput-20261124",
    "smode": "scheduler-mode-20261124",
}
REVISIONS = {"45302538749": "7d5672a7", "45348558239": "35eca30c",
             "45362378911": "8f8e7d06"}
OUTPUTS = {"revision.txt", "copyerr.csv", "sweep-1.csv", "sweep-4.csv",
           "sweep-8.csv", "topology.csv", "cost.csv", "wake.csv",
           "fair.csv", "result.txt"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", choices=REVISIONS)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    folder = BASE / "ai-images" / ("run-" + args.run_id)
    assert (folder / "haiku-ai-regular-monitor.sock").is_socket()
    bundle = {}
    for name, source in SOURCES.items():
        root = BASE / "guest-results" / source
        checksums = {line.split()[1]: line.split()[0]
                     for line in (root / "SHA256SUMS").read_text().splitlines()}
        blob = (root / name).read_bytes()
        assert blob[:4] == b"\x7fELF"
        assert hashlib.sha256(blob).hexdigest() == checksums[name], name
        bundle[name] = blob
    manifest = "".join(hashlib.sha256(blob).hexdigest() + "  " + name + "\n"
                       for name, blob in sorted(bundle.items()))
    bundle["SHA256SUMS"] = manifest.encode()
    script = (LAB / "kernel/v4-regression-guest.sh").read_text()
    bundle["run.sh"] = (script.replace('test "$#" = 2',
        'set -- ' + REVISIONS[args.run_id] + ' http://10.0.2.2:8899\n'
        'test "$#" = 2')).encode()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "binary-sha256.txt").write_text(manifest)
    (out / "run.sh").write_bytes(bundle["run.sh"])
    (out / "host-before.txt").write_text(subprocess.check_output(
        ["sh", "-c", "date; uptime; vm_stat; ps -axo pid,rss,%cpu,comm | grep qemu"], text=True))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            data = bundle.get(self.path[1:])
            if data is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name = self.path[1:]
            if name not in OUTPUTS:
                self.send_error(404)
                return
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 100000 or (out / name).exists():
                self.send_error(400)
                return
            data = self.rfile.read(size)
            if len(data) != size:
                self.send_error(400)
                return
            (out / name).write_bytes(data)
            self.send_response(201)
            self.end_headers()

    server = HTTPServer(("127.0.0.1", 8899), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        hmp = ["python3", str(LAB / "guest-hmp.py"), "--run-id", args.run_id]
        subprocess.run(hmp + ["type", "curl -fsS http://10.0.2.2:8899/run.sh -o v4test.sh"], check=True)
        time.sleep(.5)
        subprocess.run(hmp + ["type", "sh v4test.sh"], check=True)
        for _ in range(90):
            if (out / "result.txt").exists():
                break
            time.sleep(1)
        else:
            raise RuntimeError("Guest suite incomplete; inspect Terminal")
        assert all((out / name).is_file() for name in OUTPUTS)
        assert (out / "result.txt").read_text() == "PASS\n"
        assert "ai_" + REVISIONS[args.run_id] in (out / "revision.txt").read_text()
        print("Guest suite completed:", out)
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
        (out / "host-after.txt").write_text(subprocess.check_output(
            ["sh", "-c", "date; uptime; vm_stat; ps -axo pid,rss,%cpu,comm | grep qemu"], text=True))


if __name__ == "__main__":
    main()
