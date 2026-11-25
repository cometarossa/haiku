#!/bin/sh
# Same V15 image, independent files/windows, stats and preflight ON.
set -eu
cd /boot/home
mkdir v15-media-stats-concurrent-retry
cd v15-media-stats-concurrent-retry
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
(set -C; : > "$stats"); s=1
for n in 4 8; do
 tag="n$n"
 if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
 for i in $(seq 1 "$n"); do cp stream-a.mp4 "$tag-$i.mp4"; cmp stream-a.mp4 "$tag-$i.mp4"; done
 system_time > "$tag.start"
 /boot/system/apps/MediaPlayer "$PWD/$tag-1.mp4" > "$tag.log" 2>&1 &
 pid=$!
 sleep 2
 for i in $(seq 2 "$n"); do
  open "$app" "$PWD/$tag-$i.mp4"
  sleep 1
 done
 sleep 1
 count=$(hey -o "$app" count Window)
 test "$count" -le 40
 i=0
 while test "$i" -lt "$count"; do
  title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
  case "$title" in "$tag-"*.mp4)
    j=${title#"$tag-"}; j=${j%.mp4}
    echo "$j $i" >> "$tag.windows";;
  esac
  i=$((i+1))
 done
 if test "$(wc -l < "$tag.windows" | tr -d ' ')" != "$n"; then
  curl -fsS -T "$tag.windows" "$base/$tag.windows"
  hey "$app" quit || true
  wait "$pid" || true
  curl -fsS -T "$tag.log" "$base/$tag.log"
  exit 6
 fi
 {
 while read j i; do
  x=$((10+((j-1)%4)*310)); y=$((80+((j-1)/4)*340))
  hey "$app" set Frame of Window "$i" to "BRect($x,$y,$((x+300)),$((y+280)))"
  hey "$app" do Stop of Window "$i"
 done < "$tag.windows"
 system_time > "$tag.play"
 while read j i; do hey "$app" do Play of Window "$i"; done < "$tag.windows"
 for sample in 1 2 3; do
  echo "SAMPLE $sample"
  while read j i; do
   echo "WINDOW $i"
   hey -o "$app" get Title of Window "$i"
   hey -o "$app" get IsPlaying of Window "$i"
   hey "$app" get Position of Window "$i"
  done < "$tag.windows"
  sleep 1
 done
 sleep 2
 system_time > "$tag.stop"
 while read j i; do hey "$app" do Stop of Window "$i"; done < "$tag.windows"
 sleep 1
 system_time > "$tag.quit-time"
 hey "$app" quit || true
 } > "$tag.positions" 2>&1
 for j in 1 2 3 4 5 6 7 8 9 10; do
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 1
 done
 rc=125
 if ! kill -0 "$pid" 2>/dev/null; then rc=0; wait "$pid" || rc=$?; fi
 printf '%s\n' "$rc" > "$tag.exit"
 for ext in start play stop quit-time windows positions log exit; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
 test "$rc" = 0
done
cleanup
for m in "$stats" "$preflight"; do test ! -e "$m" && test ! -L "$m"; done
printf '0\n' > done.txt
curl -fsS -T done.txt "$base/done.txt"
