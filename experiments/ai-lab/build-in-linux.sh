#!/bin/sh
# AI-assisted. Run inside experimental Docker builder, not on production OS.
set -eu
ROOT=/work/haiku-ai
TOOLS=/work/buildtools
if [ "$#" -eq 0 ]; then mode=--check; else mode=$1; fi

test "$(uname -s)" = Linux || { echo "Linux builder required" >&2; exit 1; }
test -f "$ROOT/configure" || { echo "Missing Haiku source" >&2; exit 1; }
test -f "$TOOLS/jam/Makefile" || { echo "Missing buildtools" >&2; exit 1; }
branch=$(git -C "$ROOT" symbolic-ref --short HEAD)
test "$branch" = ai-experimental || {
  echo "Refusing to run outside ai-experimental branch" >&2; exit 1;
}
echo "Source: $(git -C "$ROOT" rev-parse --short=12 HEAD)"
echo "Buildtools: $(git -C "$TOOLS" rev-parse --short=12 HEAD)"
echo "Mode: $mode"
df -h "$ROOT" | tail -1

make -C "$TOOLS/jam" -j2
jam="$TOOLS/jam/bin.linuxx86/jam"
if [ ! -x "$jam" ]; then jam="$TOOLS/jam/bin.linuxx86_64/jam"; fi
test -x "$jam" || { echo "Jam executable not found at $jam" >&2; exit 1; }
"$jam" -v

if [ "$mode" = --check ]; then
  echo "Linux builder preflight PASS (no toolchain compilation attempted)"
  exit 0
fi
if [ "$mode" != --configure ]; then
  echo "Usage: build-in-linux.sh [--check|--configure]" >&2
  exit 2
fi

# Full GCC toolchain bootstrap is intentionally explicit.
# Container CPU/memory must be capped by host.
mkdir -p "$ROOT/generated"
cd "$ROOT/generated"
../configure --build-cross-tools x86_64 --cross-tools-source "$TOOLS" -j2
echo "Haiku x86_64 toolchain configured"
