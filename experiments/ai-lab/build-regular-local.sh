#!/bin/sh
# AI-assisted independent Haiku fork. Run in a dedicated Ubuntu 24.04 builder.
# No GitHub Actions API or runner registration required.
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TOOLS=$(cd "$ROOT/../buildtools" && pwd)
JOBS=${HAIKU_BUILD_JOBS:-2}
die() { echo "$*" >&2; exit 1; }
[ "$(uname -s):$(uname -m)" = Linux:x86_64 ] || die "Require Linux x86_64"
case "$JOBS" in 1|2|4|8|12|16) ;; *) die "Unsupported job count";; esac
[ "$(git -C "$ROOT" branch --show-current)" = ai-experimental ] || die "Wrong branch"
[ -z "$(git -C "$ROOT" status --porcelain)" ] || die "Dirty source"
[ "$(git -C "$ROOT" rev-parse --show-toplevel)" = "$ROOT" ] || die "Wrong source directory"
[ -f "$TOOLS/jam/Makefile" ] || die "Missing buildtools"
for tool in make gcc g++ python3 gawk bison flex nasm xorriso mtools zstd sha256sum flock; do
    command -v "$tool" >/dev/null || die "Missing dependency: $tool"
done
free_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[ "$free_kb" -ge 20971520 ] || die "Require at least 20 GiB available"
sha=$(git -C "$ROOT" rev-parse HEAD)
tools_sha=$(git -C "$TOOLS" rev-parse HEAD)
revision="hrev60465+ai_$(git -C "$ROOT" rev-parse --short HEAD)"
cd "$ROOT"
mkdir -p generated/local-artifacts
exec 9>generated/local-build.lock
flock -n 9 || die "Another local build is running"
out="$ROOT/generated/local-artifacts/$sha"
[ ! -e "$out" ] || die "Artifact already exists: $out"
stage=$(mktemp -d "$ROOT/generated/local-artifacts/.partial-$sha.XXXXXX")
echo "Partial build and logs: $stage"
printf 'source=%s\nbuildtools=%s\nrevision=%s\njobs=%s\n' "$sha" "$tools_sha" "$revision" "$JOBS" > "$stage/provenance.txt"
make -C "$TOOLS/jam" -j"$JOBS" >"$stage/jam.log" 2>&1 || { tail -n 80 "$stage/jam.log"; exit 1; }
jam="$TOOLS/jam/bin.linuxx86/jam"
[ -x "$jam" ] || jam="$TOOLS/jam/bin.linuxx86_64/jam"
[ -x "$jam" ] || die "Jam not produced"
cd "$ROOT/generated"
# Re-run configure using its retained toolchain objects.
../configure --build-cross-tools x86_64 --cross-tools-source "$TOOLS" -j"$JOBS" \
    >"$stage/configure.log" 2>&1 || { tail -n 100 "$stage/configure.log"; exit 1; }
test -x cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc
cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc --version >> "$stage/provenance.txt"
"$jam" -q -j"$JOBS" "-sHAIKU_REVISION=$revision" @nightly-raw \
    >"$stage/image.log" 2>&1 || { tail -n 100 "$stage/image.log"; exit 1; }
test "$(git -C "$ROOT" rev-parse HEAD)" = "$sha"
test "$(git -C "$TOOLS" rev-parse HEAD)" = "$tools_sha"
test -z "$(git -C "$ROOT" status --porcelain)"
image=$(find . -path './local-artifacts' -prune -o -type f -name haiku-nightly.image -print)
[ -n "$image" ] && [ -f "$image" ] && [ -s "$image" ] || die "Missing or ambiguous image"
cd "$stage"
cp "$ROOT/generated/$image" haiku-regular-x86_64.raw
sha256sum haiku-regular-x86_64.raw > haiku-regular-x86_64.raw.sha256
zstd -T2 -3 haiku-regular-x86_64.raw -o haiku-regular-x86_64.raw.zst
sha256sum haiku-regular-x86_64.raw.zst > haiku-regular-x86_64.raw.zst.sha256
sha256sum -c haiku-regular-x86_64.raw.sha256
sha256sum -c haiku-regular-x86_64.raw.zst.sha256
rm haiku-regular-x86_64.raw
cd "$ROOT"
mv "$stage" "$out"
echo "REGULAR_DESKTOP_IMAGE_COMPLETE $out"
