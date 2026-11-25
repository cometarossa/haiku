#!/bin/sh
# Native same-image V14 MediaPlayer startup proxy, not first-pixel latency.
set -eu
cd /boot/home
mkdir v14-preflight-repeat
cd v14-preflight-repeat
base=http://10.0.2.2:8901
marker=/boot/home/config/settings/haiku-lab-media-overlay-preflight
test ! -e "$marker" && test ! -L "$marker"
created=0
cleanup() { if test "$created" = 1; then rm -f "$marker"; created=0; fi; }
trap cleanup 0
trap 'exit 125' 1 2 15
for f in stream-a.mp4 SHA256SUMS; do curl -fsS "$base/$f" -o "$f"; done
sha256sum -c SHA256SUMS
uname -a > revision.txt
curl -fsS -T revision.txt "$base/revision.txt"
app=application/x-vnd.Haiku-MediaPlayer
i=0
for st in off on on off off on on off off on on off; do
 p=$(printf '%02d-%s' "$i" "$st")
 test ! -e "$marker" && test ! -L "$marker"
 if test "$st" = on; then (set -C; : > "$marker"); created=1; fi
 if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
 start=$(system_time)
 /boot/system/apps/MediaPlayer "$PWD/stream-a.mp4" > "$p.log" 2>&1 &
 pid=$!
 found=''; previous=$start
 printf 'before_us,after_us,position_us,playing\n' > "$p.poll"
 while :; do
  before=$(system_time)
  if test $((before-start)) -gt 15000000; then break; fi
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  if test -z "$found"; then
   count=$(hey -o "$app" count Window 2>/dev/null || true)
   case "$count" in ''|*[!0-9]*) count=0;; esac
   test "$count" -le 20
   j=0
   while test "$j" -lt "$count"; do
    title=$(hey -o "$app" get Title of Window "$j" 2>/dev/null || true)
    if test "$title" = stream-a.mp4; then found=$j; break; fi
    j=$((j+1))
   done
  fi
  playing=false; pos=-1
  if test -n "$found"; then
   playing=$(hey -o "$app" get IsPlaying of Window "$found" 2>/dev/null || true)
   case "$playing" in true|false) ;; *) playing=false;; esac
   pos=$(hey "$app" get Position of Window "$found" 2>/dev/null | sed -n 's/.*(B_INT64_TYPE) : \([0-9][0-9]*\) .*/\1/p' || true)
   case "$pos" in ''|*[!0-9]*) pos=-1;; esac
  fi
  after=$(system_time)
  printf '%s,%s,%s,%s\n' "$before" "$after" "$pos" "$playing" >> "$p.poll"
  if test "$playing" = true && test "$pos" -gt 0; then break; fi
  previous=$after
  sleep .1
 done
 valid=0
 if test "$playing" = true && test "$pos" -gt 0; then valid=1; fi
 printf '%s,%s,%s,%s,%s\n' "$start" "$previous" "$before" "$after" "$valid" > "$p.timing"
 sleep 4
 cp "$p.log" "$p.prequit"
 hey "$app" quit > "$p.quit" 2>&1 || true
 for j in 1 2 3 4 5 6 7 8 9 10; do
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 1
 done
 rc=125
 if ! kill -0 "$pid" 2>/dev/null; then rc=0; wait "$pid" || rc=$?; fi
 printf '%s\n' "$rc" > "$p.exit"
 for ext in poll timing log prequit quit exit; do curl -fsS -T "$p.$ext" "$base/$p.$ext"; done
 cleanup
 test "$rc" = 0 && test "$valid" = 1
 i=$((i+1))
done
test ! -e "$marker" && test ! -L "$marker"
printf '0\n' > done.txt
curl -fsS -T done.txt "$base/done.txt"
