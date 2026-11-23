#!/bin/sh
# AI-assisted independent fork QEMU screenshot/serial collector.
# Read-only, limited to the single selected and already running VM.
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: sh $0 <booted GitHub Actions run ID>" >&2
    exit 2
fi
case "$1" in
    ''|*[!0-9]*) echo "Run ID must be decimal digits" >&2; exit 2 ;;
esac

LAB="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
ROOT="$HOME/Developer/Haiku/ai-images/run-$1"
PIDFILE="$ROOT/haiku-ai-regular-qemu.pid"
PNG="$ROOT/haiku-ai-regular-screen.png"
PPM="$ROOT/haiku-ai-current-screen.ppm"

if [ ! -s "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "The experimental QEMU VM is not running for run $1" >&2
    exit 3
fi

python3 "$LAB/guest-hmp.py" --run-id "$1" info
python3 "$LAB/guest-hmp.py" --run-id "$1" screenshot
test -s "$PPM"
sips -s format png "$PPM" --out "$PNG" >/dev/null
test -s "$PNG"
shasum -a 256 "$PNG"
echo "SCREENSHOT=$PNG"
if [ -s "$ROOT/haiku-ai-regular-serial.log" ]; then
    echo "GUEST_SERIAL_LAST_LINES:"
    tail -n 22 "$ROOT/haiku-ai-regular-serial.log"
fi
echo "Inspect the screenshot to establish that Haiku reached the desktop."
