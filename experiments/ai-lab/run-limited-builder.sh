#!/bin/sh
# AI-assisted local research fork tool. Does not change host OS.
set -eu

if [ "$#" -eq 0 ]; then MODE=--check; else MODE=$1; fi
case "$MODE" in
    --check|--configure) ;;
    *) echo "Usage: run-limited-builder.sh [--check|--configure]" >&2; exit 2 ;;
esac

LAB_ROOT=$(pwd)
if printenv HAIKU_LAB_ROOT >/dev/null 2>&1; then
    LAB_ROOT=$(printenv HAIKU_LAB_ROOT)
fi
IMAGE=haiku-ai-builder:ubuntu24
case "$LAB_ROOT" in
    /*) ;;
    *) echo "HAIKU_LAB_ROOT must be an absolute path" >&2; exit 2 ;;
esac
test -d "$LAB_ROOT/haiku-ai/.git" || {
    echo "Missing fork checkout in $LAB_ROOT" >&2; exit 2;
}
test -d "$LAB_ROOT/buildtools/.git" || {
    echo "Missing buildtools in $LAB_ROOT" >&2; exit 2;
}
if [ "$MODE" = --configure ]; then
    DURATION=600
else
    DURATION=60
fi
if ! command -v docker >/dev/null; then
    echo "Docker CLI not present" >&2; exit 2
fi

# Run timeout INSIDE the container. Never kill only a detached docker CLI:
# a killed client can leave a resource-consuming build container running.
# This is a bounded interactive operation, not a background service.
docker run --rm --init --network none \
    --cpus=2 --memory=4g --memory-swap=4g \
    --pids-limit=256 --security-opt=no-new-privileges --cap-drop=ALL \
    --user "$(id -u):$(id -g)" \
    -v "$LAB_ROOT:/work" -w /work \
    "$IMAGE" \
    timeout --signal=TERM --kill-after=15s "$DURATION" \
    sh /work/haiku-ai/experiments/ai-lab/build-in-linux.sh "$MODE"
