#!/bin/sh
# AI-assisted experimental Haiku fork only.
# Download an independently-built raw CI image and boot a QCOW2 overlay.
# Never alters an official Haiku beta6 disk.
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: sh $0 <successful GitHub Actions run ID>" >&2
    exit 2
fi

RUN_ID=$1
case "$RUN_ID" in
    ''|*[!0-9]*) echo "Run ID must be decimal digits" >&2; exit 2 ;;
esac

for command in gh qemu-img qemu-system-x86_64 zstd shasum python3; do
    command -v "$command" >/dev/null 2>&1 || {
        echo "Missing host command: $command" >&2; exit 2;
    }
done
test "$(uname -s)" = Darwin || {
    echo "This boot helper targets macOS; aborting." >&2; exit 2;
}

RUN_RESULT=$(gh run view "$RUN_ID" --repo cometarossa/haiku \
    --json conclusion --jq '.conclusion')
if [ "$RUN_RESULT" != success ]; then
    echo "CI run $RUN_ID has not successfully completed: $RUN_RESULT" >&2
    echo "No disk image will be downloaded or started." >&2
    exit 3
fi

BASE="$HOME/Developer/Haiku/ai-images"
TARGET="$BASE/run-$RUN_ID"
mkdir -p "$TARGET"
gh run download "$RUN_ID" --repo cometarossa/haiku \
    --name haiku-ai-regular-x86_64 --dir "$TARGET"

ZST="$TARGET/haiku-regular-x86_64.raw.zst"
RAW="$TARGET/haiku-regular-x86_64.raw"
OVERLAY="$TARGET/haiku-ai-regular-overlay.qcow2"
MONITOR="$TARGET/haiku-ai-regular-monitor.sock"
PIDFILE="$TARGET/haiku-ai-regular-qemu.pid"
PASSFILE="$HOME/Developer/Haiku/vm/vnc-password"

check_sha()
{
    data_file=$1
    hash_file=$2
    test -s "$data_file" && test -s "$hash_file" || {
        echo "Missing artifact or checksum: $data_file / $hash_file" >&2
        exit 4
    }
    expected=$(awk 'NR == 1 {print $1}' "$hash_file")
    actual=$(shasum -a 256 "$data_file" | awk '{print $1}')
    test "$expected" = "$actual" || {
        echo "Checksum failed for $data_file" >&2; exit 4;
    }
    echo "SHA256 verified: $(basename "$data_file")"
}
check_sha "$ZST" "$ZST.sha256"

if [ ! -f "$RAW" ]; then
    echo "Extracting verified raw disk image..."
    zstd -dc "$ZST" > "$RAW.partial"
    mv "$RAW.partial" "$RAW"
fi
check_sha "$RAW" "$RAW.sha256"

if [ ! -f "$OVERLAY" ]; then
    qemu-img create -f qcow2 -F raw -b "$RAW" "$OVERLAY"
fi
test -s "$PASSFILE" || {
    echo "Missing pre-existing private VNC password on Mac" >&2
    exit 4
}

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Experimental Haiku VM already running with PID $(cat "$PIDFILE")"
    echo "Connect from the Mac: vnc://127.0.0.1:5913"
    exit 0
fi
if lsof -nP -iTCP:5913 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "VNC port 5912 is already in use; refusing to collide." >&2
    exit 5
fi

rm -f "$MONITOR" "$PIDFILE"
qemu-system-x86_64 \
    -machine pc,accel=hvf,vmport=off -cpu Penryn \
    -smp 4 -m 8192 \
    -drive "file=$OVERLAY,format=qcow2,if=ide,index=0,media=disk" \
    -vga std -nic user,model=rtl8139 \
    -vnc "127.0.0.1:13,password=on" \
    -monitor "unix:$MONITOR,server,nowait" \
    -serial "file:$TARGET/haiku-ai-regular-serial.log" \
    -pidfile "$PIDFILE" -daemonize -boot order=c

python3 - "$MONITOR" "$PASSFILE" <<'PY'
import pathlib
import socket
import sys
import time

monitor, passfile = sys.argv[1:]
secret = pathlib.Path(passfile).read_text().strip()
if not 1 <= len(secret) <= 8:
    raise SystemExit("VNC password length not allowed by QEMU VNC")
for attempt in range(50):
    try:
        sock = socket.socket(socket.AF_UNIX)
        sock.settimeout(3)
        sock.connect(monitor)
        break
    except OSError:
        time.sleep(.1)
else:
    raise SystemExit("QEMU monitor not available")
with sock:
    sock.recv(4096)
    sock.sendall(("set_password vnc " + secret + "\n").encode())
    response = sock.recv(4096)
    if b"Error:" in response or b"unknown command" in response:
        raise SystemExit("Could not set QEMU VNC password")
PY

echo "Booted experimental Haiku image via disposable QCOW2 overlay."
echo "VNC: vnc://127.0.0.1:5913"
echo "QEMU PID: $(cat "$PIDFILE")"
echo "Raw CI artifact: $RAW"
echo "Original beta6 disk: UNCHANGED"
