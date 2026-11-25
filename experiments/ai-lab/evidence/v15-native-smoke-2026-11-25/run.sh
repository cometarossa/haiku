#!/bin/sh
# V15 instrumentation smoke. One player, preflight fixed ON in both runs.
set -eu
cd /boot/home
mkdir v15-media-stats-smoke
cd v15-media-stats-smoke
base=http://10.0.2.2:8901
stats=/boot/home/config/settings/haiku-lab-media-stats
preflight=/boot/home/config/settings/haiku-lab-media-overlay-preflight
for m in "$stats" "$preflight"; do test ! -e "$m" && test ! -L "$m"; done
s=0;p=0
cleanup() {
 if test "$s" = 1; then rm -f "$stats"; s=0; fi
 if test "$p" = 1; then rm -f "$preflight"; p=0; fi
}
trap cleanup 0
trap 'exit 125' 1 2 15
for f in stream-a.mp4 SHA256SUMS; do curl -fsS "$base/$f" -o "$f"; done
sha256sum -c SHA256SUMS
uname -a > revision.txt
curl -fsS -T revision.txt "$base/revision.txt"
app=application/x-vnd.Haiku-MediaPlayer
(set -C; : > "$preflight"); p=1
for st in off on; do
 if test "$st" = on; then (set -C; : > "$stats"); s=1; fi
 if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
 system_time > "$st.start"
 /boot/system/apps/MediaPlayer "$PWD/stream-a.mp4" > "$st.log" 2>&1 &
 pid=$!
 sleep 3
 valid=1
 {
 count=$(hey -o "$app" count Window)
 found='';i=0
 while test "$i" -lt "$count"; do
  title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
  if test "$title" = stream-a.mp4; then test -z "$found"; found=$i; fi
  i=$((i+1))
 done
 test -n "$found"
 for n in 1 2 3; do
  echo "SAMPLE $n"
  hey -o "$app" get IsPlaying of Window "$found"
  hey "$app" get Position of Window "$found"
  sleep 1
 done
 } > "$st.positions" 2>&1 || valid=0
 system_time > "$st.stop"
 hey "$app" quit > "$st.quit" 2>&1 || true
 for i in 1 2 3 4 5 6 7 8 9 10; do
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 1
 done
 rc=125
 if ! kill -0 "$pid" 2>/dev/null; then rc=0; wait "$pid" || rc=$?; fi
 printf '%s\n' "$rc" > "$st.exit"
 for ext in start stop log positions quit exit; do curl -fsS -T "$st.$ext" "$base/$st.$ext"; done
 test "$valid" = 1 && test "$rc" = 0
done
cleanup
for m in "$stats" "$preflight"; do test ! -e "$m" && test ! -L "$m"; done
printf '0\n' > done.txt
curl -fsS -T done.txt "$base/done.txt"
