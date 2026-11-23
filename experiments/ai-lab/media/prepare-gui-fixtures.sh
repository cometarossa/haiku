#!/bin/sh
# Independent AI-assisted Haiku research fork.
# Generate reproducible, tiny GUI test videos without network access.
set -eu
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <locally-owned-H264-MP4> <output-directory>" >&2
    exit 2
fi
SRC=$1
DEST=$2
for command in ffmpeg ffprobe shasum; do
    command -v "$command" >/dev/null 2>&1 || {
        echo "Missing command: $command" >&2; exit 2;
    }
done
test -s "$SRC" || {
    echo "Input MP4 not found: $SRC" >&2; exit 2;
}
if ! ffmpeg -hide_banner -version >/dev/null 2>&1; then
    echo "FFmpeg exists but is not executable (broken local dependency)." >&2
    echo "Use a working isolated FFmpeg host instead; do not alter the Mac globally." >&2
    exit 2
fi
if ! ffprobe -hide_banner -version >/dev/null 2>&1; then
    echo "FFprobe exists but cannot be executed." >&2
    exit 2
fi
mkdir -p "$DEST"
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$SRC" \
    -frames:v 1 -map 0:v:0 -an -c:v copy "$DEST/cover_h264.mp4"
ffmpeg -nostdin -hide_banner -loglevel error -y -ss 2 -i "$SRC" \
    -frames:v 1 -map 0:v:0 -an -c:v mpeg4 -q:v 4 \
    -pix_fmt yuv420p "$DEST/cover_mpeg4.mp4"
cp "$SRC" "$DEST/test_video_h264.mp4"
for video in "$DEST"/*.mp4; do
    test -s "$video"
    echo "$(basename "$video")"
    ffprobe -v error -select_streams v:0 -show_entries \
        stream=codec_name,width,height,nb_frames -of csv=p=0 "$video"
done
(
    cd "$DEST"
    shasum -a 256 *.mp4 > SHA256SUMS
)
echo "GUI_FIXTURES_READY=$DEST"
