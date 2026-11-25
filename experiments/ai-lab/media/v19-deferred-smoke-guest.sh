#!/bin/sh
# Two independent one-window lifetimes, same image, deferred OFF/ON.
set -eu
cd /boot/home
mkdir v19-deferred-smoke
cd v19-deferred-smoke
base=http://10.0.2.2:8901
app=application/x-vnd.Haiku-MediaPlayer
settings=/boot/home/config/settings
stats="$settings/haiku-lab-media-stats"
preflight="$settings/haiku-lab-media-overlay-preflight"
view="$settings/haiku-lab-video-view-stats"
deferred="$settings/haiku-lab-video-deferred"
check_markers() {
 for m in "$stats" "$preflight" "$view" "$deferred" "$settings/haiku-lab-media-catchup" "$settings/haiku-lab-media-catchup-adaptive"; do
  test ! -e "$m" && test ! -L "$m"
 done
}
check_markers
s=0;p=0;v=0;d=0
cleanup() {
 if test "$d" = 1; then rm -f "$deferred"; d=0; fi
 if test "$v" = 1; then rm -f "$view"; v=0; fi
 if test "$s" = 1; then rm -f "$stats"; s=0; fi
 if test "$p" = 1; then rm -f "$preflight"; p=0; fi
}
trap cleanup 0
trap 'exit 125' 1 2 15
for f in stream-a.mp4 media-window-probe SHA256SUMS; do curl -fsS "$base/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x media-window-probe
uname -a > revision.txt
curl -fsS -T revision.txt "$base/revision.txt"
(set -C; : > "$stats"); s=1
(set -C; : > "$preflight"); p=1
(set -C; : > "$view"); v=1
run=0
for state in off on; do
 tag=$(printf '%02d-n1-%s' "$run" "$state")
 if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
 if test "$state" = on; then (set -C; : > "$deferred"); d=1; fi
 cp stream-a.mp4 "$tag.mp4"
 cmp stream-a.mp4 "$tag.mp4"
 system_time > "$tag.start"
 /boot/system/apps/MediaPlayer "$PWD/$tag.mp4" > "$tag.stdout" 2> "$tag.stderr" &
 pid=$!
 sleep 3
 count=$(hey -o "$app" count Window)
 test "$count" -le 40
 i=0
 : > "$tag.map"
 while test "$i" -lt "$count"; do
  title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
  if test "$title" = "$tag.mp4"; then printf '%s %s\n' "$i" "$title" >> "$tag.map"; fi
  i=$((i+1))
 done
 test "$(wc -l < "$tag.map" | tr -d ' ')" = 1
 i=$(cut -d ' ' -f 1 "$tag.map")
 (
 set -eu
 hey "$app" do Stop of Window "$i"
 sleep 1
 printf 'STOP\n'
 hey -o "$app" get IsPlaying of Window "$i"
 hey "$app" get Position of Window "$i"
 hey "$app" set Position of Window "$i" to 'int64(30000000)'
 sleep 1
 printf 'SEEK\n'
 hey -o "$app" get IsPlaying of Window "$i"
 hey "$app" get Position of Window "$i"
 system_time > "$tag.play"
 hey "$app" do Play of Window "$i"
 sleep 1
 ) > "$tag.lifecycle" 2>&1
 probe_rc=0
 ./media-window-probe "$tag.map" 10 > "$tag.probe" 2> "$tag.probe-stderr" || probe_rc=$?
 printf '%s\n' "$probe_rc" > "$tag.probe-exit"
 system_time > "$tag.stop"
 for ext in map lifecycle play stop probe probe-stderr probe-exit; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
 hey "$app" do Pause of Window "$i"
 sleep 1
 {
 printf 'PAUSE\n'
 hey -o "$app" get IsPlaying of Window "$i"
 hey "$app" get Position of Window "$i"
 sleep 1
 printf 'PAUSE_LATER\n'
 hey "$app" get Position of Window "$i"
 } > "$tag.pause" 2>&1
 curl -fsS -T "$tag.pause" "$base/$tag.pause"
 system_time > "$tag.quit-time"
 hey "$app" quit || true
 for j in $(seq 1 10); do if ! kill -0 "$pid" 2>/dev/null; then break; fi; sleep 1; done
 rc=125
 if ! kill -0 "$pid" 2>/dev/null; then rc=0; wait "$pid" || rc=$?; fi
 printf '%s\n' "$rc" > "$tag.exit"
 for ext in start quit-time stdout stderr exit; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
 if test "$d" = 1; then rm -f "$deferred"; d=0; fi
 test "$rc" = 0
 run=$((run+1))
done
cleanup
check_markers
(set -C; printf '0\n' > done.txt)
curl -fsS -T done.txt "$base/done.txt"
