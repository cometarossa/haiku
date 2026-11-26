#!/bin/sh
set -eu
cd /boot/home
settings=/boot/home/config/settings
single="$settings/haiku-lab-h264-single-thread"
stats="$settings/haiku-lab-video-thread-stats"
check_markers() {
 for marker in "$single" "$stats" "$settings/haiku-lab-video-deferred" "$settings/haiku-lab-video-deferred-timing" "$settings/haiku-lab-media-catchup" "$settings/haiku-lab-media-catchup-adaptive" "$settings/haiku-lab-video-proxy-stats" "$settings/haiku-lab-video-view-stats" "$settings/haiku-lab-media-stats"; do
  if test -e "$marker" || test -L "$marker"; then exit 7; fi
 done
}
check_markers
if hey -o application/x-vnd.Haiku-MediaPlayer count Window >/dev/null 2>&1; then exit 4; fi
mkdir v22-gop-decode-ram
ramdir=/boot/home/v22-gop-decode-ram
mount -t ramfs "$ramdir"
cd "$ramdir"
base=http://10.0.2.2:8901
own_single=0;own_stats=0
cleanup() {
 if test "$own_single" = 1; then rm -f "$single"; own_single=0; fi
 if test "$own_stats" = 1; then rm -f "$stats"; own_stats=0; fi
}
trap cleanup 0
trap 'exit 125' 1 2 15
for f in frame-digest gop-120.mp4 gop-15.mp4 SHA256SUMS; do curl -fsS "$base/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x frame-digest
uname -a > revision.txt
curl -fsS -T revision.txt "$base/revision.txt"
(set -C; : > "$stats"); own_stats=1
(set -C; : > "$single"); own_single=1
run=0
for g in 120 15 15 120; do
 tag=$(printf '%02d-gop-%s' "$run" "$g")
 rc=0
 system_time > "$tag.start"
 ./frame-digest "gop-$g.mp4" > "$tag.stdout" 2> "$tag.stderr" || rc=$?
 system_time > "$tag.stop"
 printf '%s\n' "$rc" > "$tag.exit"
 for ext in start stop stdout stderr exit; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
 test "$rc" = 0
 run=$((run+1))
done
cleanup
check_markers
cd /boot/home
unmount "$ramdir"
(set -C; printf '0\n' > "$ramdir/done.txt")
curl -fsS -T "$ramdir/done.txt" "$base/done.txt"
