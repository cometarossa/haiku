#!/bin/sh
# AI-assisted experimental Haiku fork, regular desktop only.
# Run inside a terminal in the separate CI-built Haiku guest.
# The Mac host must serve only generated fixtures on 10.0.2.2:8899.
set -eu
BASE=http://10.0.2.2:8899
DEST=/boot/home
test -d "$DEST" || {
    echo "Not running inside expected Haiku home filesystem" >&2
    exit 2
}
cd "$DEST"
for f in cover_h264.mp4 cover_mpeg4.mp4 test_video_h264.mp4 SHA256SUMS; do
    curl -fsS --connect-timeout 5 "$BASE/$f" -o "$f"
done
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c SHA256SUMS
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 -c SHA256SUMS
else
    echo "No SHA256 checksum tool available inside this Haiku guest" >&2
    exit 2
fi
if ! test -f /boot/system/apps/MediaPlayer; then
    echo "MediaPlayer is not installed; this may be a minimal OS image" >&2
    exit 2
fi
echo "FORK_MEDIA_GUI_FIXTURES_READY"
uname -a
echo "Now open each one-frame video in the GUI, capture separate"
echo "QEMU screenshots, and play the 150-frame control."
