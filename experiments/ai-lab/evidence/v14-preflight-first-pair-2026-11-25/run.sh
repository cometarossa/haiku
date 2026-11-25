#!/bin/sh
set -eu
cd /boot/home
mkdir v14-preflight-first-pair
cd v14-preflight-first-pair
marker=/boot/home/config/settings/haiku-lab-media-overlay-preflight
test ! -e "$marker" && test ! -L "$marker"
created=0
cleanup() { if test "$created" = 1; then rm -f "$marker"; created=0; fi; }
trap cleanup 0
trap 'exit 125' 1 2 15
curl -fsS http://10.0.2.2:8901/stream-a.mp4 -o stream-a.mp4
curl -fsS http://10.0.2.2:8901/SHA256SUMS -o SHA256SUMS
sha256sum -c SHA256SUMS
uname -a > revision.txt
curl -fsS -T revision.txt http://10.0.2.2:8901/revision.txt
app=application/x-vnd.Haiku-MediaPlayer
for st in off on; do
 test ! -e "$marker"
 if test "$st" = on; then (set -C; : > "$marker"); created=1; fi
 if hey -o "$app" count Window >/dev/null 2>&1; then echo "player unexpectedly exists"; exit 4; fi
 /boot/system/apps/MediaPlayer "$PWD/stream-a.mp4" > "$st.log" 2>&1 &
 pid=$!
 sleep 3
 {
  count=$(hey -o "$app" count Window)
  i=0; found=''
  while test "$i" -lt "$count"; do
   title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
   if test "$title" = stream-a.mp4; then test -z "$found"; found=$i; fi
   i=$((i+1))
  done
  test -n "$found"
  echo "WINDOW $found"
  for sample in 1 2 3; do
   echo "SAMPLE $sample"
   hey -o "$app" get IsPlaying of Window "$found"
   hey "$app" get Position of Window "$found"
   sleep 1
  done
 } > "$st.positions" 2>&1
 hey "$app" quit > "$st.quit" 2>&1
 for i in 1 2 3 4 5 6 7 8 9 10; do
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 1
 done
 if kill -0 "$pid" 2>/dev/null; then
  for f in "$st.log" "$st.positions" "$st.quit"; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
  exit 5
 fi
 rc=0;wait "$pid" || rc=$?
 printf '%s\n' "$rc" > "$st.exit"
 for f in "$st.log" "$st.positions" "$st.quit" "$st.exit"; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
 cleanup
 test "$rc" = 0
done
test ! -e "$marker" && test ! -L "$marker"
printf '0\n' > done.txt
curl -fsS -T done.txt http://10.0.2.2:8901/done.txt
