#!/bin/sh
set -eu
cd /boot/home
mkdir v21-decode-repeat
cd v21-decode-repeat
base=http://10.0.2.2:8901
settings=/boot/home/config/settings
single="$settings/haiku-lab-h264-single-thread"
stats="$settings/haiku-lab-video-thread-stats"
check_markers() {
 for marker in "$single" "$stats" "$settings/haiku-lab-video-deferred" "$settings/haiku-lab-media-catchup" "$settings/haiku-lab-media-catchup-adaptive"; do
  if test -e "$marker" || test -L "$marker"; then exit 7; fi
 done
}
check_markers
own_single=0;own_stats=0
cleanup() {
 if test "$own_single" = 1; then rm -f "$single"; own_single=0; fi
 if test "$own_stats" = 1; then rm -f "$stats"; own_stats=0; fi
}
trap cleanup 0
trap 'exit 125' 1 2 15
if hey -o application/x-vnd.Haiku-MediaPlayer count Window >/dev/null 2>&1; then exit 4; fi
for f in frame-digest stream-a.mp4 SHA256SUMS; do curl -fsS "$base/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x frame-digest
uname -a > revision.txt
curl -fsS -T revision.txt "$base/revision.txt"
(set -C; : > "$stats"); own_stats=1
run=0
for state in off on on off off on on off; do
 tag=$(printf "%02d-%s" "$run" "$state")
 if test "$state" = on; then (set -C; : > "$single"); own_single=1; fi
 rc=0
 system_time > "$tag.start"
 ./frame-digest stream-a.mp4 > "$tag.stdout" 2> "$tag.stderr" || rc=$?
 system_time > "$tag.stop"
 printf '%s\n' "$rc" > "$tag.exit"
 for ext in start stop stdout stderr exit; do curl -fsS -T "$tag.$ext" "$base/$state.$ext"; done
 test "$rc" = 0
 if test "$own_single" = 1; then rm -f "$single"; own_single=0; fi
 run=$((run+1))
done
cleanup
check_markers
(set -C; printf '0\n' > done.txt)
curl -fsS -T done.txt "$base/done.txt"
