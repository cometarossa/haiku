#!/bin/sh
# AI-assisted experimental Haiku fork only.
# Import a local or CI-built raw image and boot a QCOW2 overlay.
# Never alters an official Haiku beta6 disk.
set -eu
LOCAL_ARTIFACT=
if [ "$#" -eq 2 ] && [ "$1" = --local ]; then
    LOCAL_ARTIFACT=$(cd "$2" && pwd)
    test -s "$LOCAL_ARTIFACT/provenance.txt" || {
        echo "Missing local build provenance" >&2; exit 2;
    }
    SOURCE_SHA=$(sed -n 's/^source=//p' "$LOCAL_ARTIFACT/provenance.txt")
    case "$SOURCE_SHA" in
        ''|*[!0-9a-f]*) echo "Invalid local source SHA" >&2; exit 2 ;;
    esac
    test "${#SOURCE_SHA}" -eq 40 || {
        echo "Invalid local source SHA length" >&2; exit 2;
    }
    SHORT_SHA=$(printf '%s' "$SOURCE_SHA" | cut -c1-8)
    grep -qx "revision=hrev60465+ai_$SHORT_SHA" "$LOCAL_ARTIFACT/provenance.txt" || {
        echo "Local revision mismatch" >&2; exit 2;
    }
    # Bind local artifact to a known commit in the independent fork.
    ROOT=$(cd "$(dirname "$0")/../.." && pwd)
    git -C "$ROOT" merge-base --is-ancestor "$SOURCE_SHA" ai-experimental || {
        echo "Local source not in ai-experimental history" >&2; exit 2;
    }
    RUN_ID=local-$SHORT_SHA
elif [ "$#" -eq 1 ]; then
    RUN_ID=$1
    case "$RUN_ID" in
        ''|*[!0-9]*) echo "Run ID must be decimal digits" >&2; exit 2 ;;
    esac
else
    echo "Usage: sh $0 <successful CI run ID> | --local <artifact directory>" >&2
    exit 2
fi

# Leave the older full Haiku on VNC 5913 while testing the patched
# fork on a distinct port 5914. Only bounded localhost ports allowed.
VNC_DISPLAY=$(printenv HAIKU_REGULAR_VNC_DISPLAY 2>/dev/null || echo 13)
case "$VNC_DISPLAY" in
    13|14|15|16|17|18|19|20|21|22) ;;
    *) echo "HAIKU_REGULAR_VNC_DISPLAY must be 13..22" >&2; exit 2 ;;
esac
VNC_PORT=$((5900 + VNC_DISPLAY))

for command in qemu-img qemu-system-x86_64 zstd shasum python3; do
    command -v "$command" >/dev/null 2>&1 || {
        echo "Missing host command: $command" >&2; exit 2;
    }
done
test "$(uname -s)" = Darwin || {
    echo "This boot helper targets macOS; aborting." >&2; exit 2;
}

if [ -z "$LOCAL_ARTIFACT" ]; then
    command -v gh >/dev/null || { echo "Missing gh" >&2; exit 2; }
    # Reject unrelated successful workflows before touching any local image.
    RUN_KIND=$(gh run view "$RUN_ID" --repo cometarossa/haiku \
        --json workflowName,headBranch \
        --jq '(.workflowName == "Haiku fork x86-64 regular desktop image") and (.headBranch == "ai-experimental")')
    if [ "$RUN_KIND" != true ]; then
        echo "Run $RUN_ID is not a regular desktop build of ai-experimental." >&2
        exit 3
    fi

    RUN_RESULT=$(gh run view "$RUN_ID" --repo cometarossa/haiku \
        --json conclusion --jq '.conclusion')
    if [ "$RUN_RESULT" != success ]; then
        echo "CI run $RUN_ID has not successfully completed: $RUN_RESULT" >&2
        echo "No disk image will be downloaded or started." >&2
        exit 3
    fi

fi

BASE="$HOME/Developer/Haiku/ai-images"
# AI-assisted: never recreate a dangling image-storage symlink locally.
if [ -L "$BASE" ] && [ ! -d "$BASE" ]; then
    echo "Image storage unavailable: $BASE" >&2
    exit 4
fi
TARGET="$BASE/run-$RUN_ID"
if [ -n "$LOCAL_ARTIFACT" ]; then
    # Import to a new directory only, after verifying compressed and raw
    # hashes. Never replace a CI cache or a previous local overlay.
    if [ ! -d "$BASE" ] || [ ! -L "$BASE" ]; then
        echo "Expected mounted experimental image storage symlink" >&2; exit 4
    fi
    if [ -L "$TARGET" ]; then
        echo "Refusing symlink as local build target" >&2; exit 4
    fi
    if [ ! -e "$TARGET" ]; then
        for name in haiku-regular-x86_64.raw.zst haiku-regular-x86_64.raw.zst.sha256 haiku-regular-x86_64.raw.sha256; do
            test -s "$LOCAL_ARTIFACT/$name" || {
                echo "Missing local artifact: $name" >&2; exit 4;
            }
        done
        stage=$(mktemp -d "$BASE/.local-import-$SHORT_SHA.XXXXXX")
        for name in provenance.txt haiku-regular-x86_64.raw.zst haiku-regular-x86_64.raw.zst.sha256 haiku-regular-x86_64.raw.sha256; do
            cp "$LOCAL_ARTIFACT/$name" "$stage/$name"
        done
        (
            cd "$stage" || exit 1
            expected=$(awk 'NR == 1 {print $1}' haiku-regular-x86_64.raw.zst.sha256)
            actual=$(shasum -a 256 haiku-regular-x86_64.raw.zst | awk '{print $1}')
            test -n "$expected" && test "$expected" = "$actual" || exit 1
            zstd -dc haiku-regular-x86_64.raw.zst > haiku-regular-x86_64.raw || exit 1
            expected=$(awk 'NR == 1 {print $1}' haiku-regular-x86_64.raw.sha256)
            actual=$(shasum -a 256 haiku-regular-x86_64.raw | awk '{print $1}')
            test -n "$expected" && test "$expected" = "$actual" || exit 1
        ) || { echo "Local import checksum failed; retained $stage" >&2; exit 4; }
        # mkdir reservation prevents concurrent imports from replacing a cache.
        mkdir "$TARGET" || { echo "Local target already exists" >&2; exit 4; }
        mv "$stage/"* "$TARGET/"
        rmdir "$stage"
    fi
    cmp -s "$LOCAL_ARTIFACT/provenance.txt" "$TARGET/provenance.txt" || {
        echo "Local cached provenance differs" >&2; exit 4;
    }
    for name in haiku-regular-x86_64.raw.zst.sha256 haiku-regular-x86_64.raw.sha256; do
        cmp -s "$LOCAL_ARTIFACT/$name" "$TARGET/$name" || {
            echo "Local cached hashes differ" >&2; exit 4;
        }
    done
else
    mkdir -p "$TARGET"
    # Reuse a complete cached artifact; checksum validation below is mandatory.
    if [ -f "$TARGET/haiku-regular-x86_64.raw.zst" ] &&
       [ -f "$TARGET/haiku-regular-x86_64.raw.zst.sha256" ] &&
       [ -f "$TARGET/haiku-regular-x86_64.raw.sha256" ]; then
        echo "Reusing cached CI artifact for run $RUN_ID"
    elif [ -e "$TARGET/haiku-regular-x86_64.raw.zst" ] ||
         [ -e "$TARGET/haiku-regular-x86_64.raw.zst.sha256" ] ||
         [ -e "$TARGET/haiku-regular-x86_64.raw.sha256" ]; then
        echo "Incomplete cached artifact; refusing to overwrite: $TARGET" >&2
        exit 4
    else
        gh run download "$RUN_ID" --repo cometarossa/haiku \
            --name haiku-ai-regular-x86_64 --dir "$TARGET"
    fi

fi

ZST="$TARGET/haiku-regular-x86_64.raw.zst"
RAW="$TARGET/haiku-regular-x86_64.raw"
OVERLAY="$TARGET/haiku-ai-regular-overlay.qcow2"
MONITOR="$TARGET/haiku-ai-regular-monitor.sock"
PIDFILE="$TARGET/haiku-ai-regular-qemu.pid"
VNC_PORTFILE="$TARGET/haiku-ai-regular-vnc-port"
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

if [ -n "$LOCAL_ARTIFACT" ] && [ "$(printenv HAIKU_LOCAL_IMPORT_ONLY 2>/dev/null || echo 0)" = 1 ]; then
    echo "Verified local artifact imported: $TARGET (no VM started)"
    exit 0
fi

if [ ! -f "$OVERLAY" ]; then
    qemu-img create -f qcow2 -F raw -b "$RAW" "$OVERLAY"
fi
test -s "$PASSFILE" || {
    echo "Missing pre-existing private VNC password on Mac" >&2
    exit 4
}

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Experimental Haiku VM already running with PID $(cat "$PIDFILE")"
    if [ -s "$VNC_PORTFILE" ]; then
        VNC_PORT=$(cat "$VNC_PORTFILE")
    else
        VNC_PORT=5913
    fi
    echo "Connect from the Mac: vnc://127.0.0.1:$VNC_PORT"
    exit 0
fi
if lsof -nP -iTCP:"$VNC_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "VNC port $VNC_PORT is already in use; refusing to collide." >&2
    exit 5
fi

rm -f "$MONITOR" "$PIDFILE"
qemu-system-x86_64 \
    -machine pc,accel=hvf,vmport=off -cpu Penryn \
    -smp 4 -m 8192 \
    -drive "file=$OVERLAY,format=qcow2,if=ide,index=0,media=disk" \
    -vga std -nic user,model=rtl8139 \
    -vnc "127.0.0.1:$VNC_DISPLAY,password=on" \
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

printf '%s\n' "$VNC_PORT" > "$VNC_PORTFILE"
echo "Booted experimental Haiku image via disposable QCOW2 overlay."
echo "VNC: vnc://127.0.0.1:$VNC_PORT"
echo "QEMU PID: $(cat "$PIDFILE")"
echo "Raw artifact: $RAW"
echo "Original beta6 disk: UNCHANGED"
