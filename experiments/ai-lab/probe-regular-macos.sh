#!/bin/sh
# AI-assisted independent research-fork diagnostic, read-only against guest.
# Captures a QEMU screendump from a started disposable regular Haiku VM.
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: sh $0 <successful booted image run ID>" >&2
    exit 2
fi
case "$1" in
    ''|*[!0-9]*) echo "Run ID must be decimal digits" >&2; exit 2 ;;
esac
ROOT="$HOME/Developer/Haiku/ai-images/run-$1"
MONITOR="$ROOT/haiku-ai-regular-monitor.sock"
PIDFILE="$ROOT/haiku-ai-regular-qemu.pid"
PPM="$ROOT/haiku-ai-regular-screen.ppm"
PNG="$ROOT/haiku-ai-regular-screen.png"

if [ ! -S "$MONITOR" ] || [ ! -s "$PIDFILE" ]; then
    echo "Experimental VM monitor not running for this run ID." >&2
    exit 3
fi
if ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Experimental QEMU VM PID is not running." >&2
    exit 3
fi
python3 - "$MONITOR" "$PPM" <<'PY'
from pathlib import Path
import socket
import sys

monitor = sys.argv[1]
screenshot = Path(sys.argv[2])
with socket.socket(socket.AF_UNIX) as sock:
    sock.settimeout(6)
    sock.connect(monitor)
    sock.recv(8192)
    for cmd in ("info status", "info block"):
        sock.sendall((cmd + "\n").encode())
        result = sock.recv(8192).decode("utf-8", errors="replace")
        if "Error:" in result or "unknown command" in result:
            raise RuntimeError(result)
        print(cmd + ": " + result[-850:].strip())
    sock.sendall(("screendump " + str(screenshot) + "\n").encode())
    result = sock.recv(8192).decode("utf-8", errors="replace")
    if "Error:" in result or "unknown command" in result:
        raise RuntimeError(result)
if not screenshot.exists() or screenshot.stat().st_size == 0:
    raise RuntimeError("No QEMU screen capture was written")
print("Screenshot PPM:", screenshot)
PY

sips -s format png "$PPM" --out "$PNG" >/dev/null
test -s "$PNG"
shasum -a 256 "$PNG"
echo "SCREENSHOT=$PNG"
if [ -s "$ROOT/haiku-ai-regular-serial.log" ]; then
    echo "GUEST_SERIAL_LAST_LINES:"
    tail -n 22 "$ROOT/haiku-ai-regular-serial.log"
fi
echo "This proves QEMU is running and captured a screen,"
echo "not that Haiku has reached the GUI; inspect the PNG separately."
