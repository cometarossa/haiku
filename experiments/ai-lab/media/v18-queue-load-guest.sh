#!/bin/sh
# V18 staged persistent-query capacity test; no recovery treatment.
set -eu
cd /boot/home
mkdir v18-queue-load-ram
ramdir=/boot/home/v18-queue-load-ram
mount -t ramfs "$ramdir"
cd "$ramdir"
base=http://10.0.2.2:8901
stats=/boot/home/config/settings/haiku-lab-media-stats
preflight=/boot/home/config/settings/haiku-lab-media-overlay-preflight
catchup=/boot/home/config/settings/haiku-lab-video-view-stats
for m in "$stats" "$preflight" "$catchup" /boot/home/config/settings/haiku-lab-media-catchup /boot/home/config/settings/haiku-lab-media-catchup-adaptive; do
 test ! -e "$m" && test ! -L "$m"
done
s=0;p=0;c=0
cleanup() {
 if test "$c" = 1; then rm -f "$catchup"; c=0; fi
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
app=application/x-vnd.Haiku-MediaPlayer
(set -C; : > "$preflight"); p=1
(set -C; : > "$stats"); s=1
command -v listport >/dev/null
listport > teams.txt
curl -fsS -T teams.txt "$base/teams.txt"
server_team=$(awk '/^TEAM[[:space:]]+[0-9]+[[:space:]]+\(([^ ]*\/)?app_server\):$/ {print $2}' teams.txt)
case "$server_team" in ''|*[!0-9]*) exit 7;; esac
run=0
for spec in 8-on; do
 n=${spec%-*}; st=${spec#*-}
 tag=$(printf '%02d-n%s-%s' "$run" "$n" "$st")
 test ! -e "$catchup" && test ! -L "$catchup"
 if test "$st" = on; then (set -C; : > "$catchup"); c=1; fi
 if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
 for i in $(seq 1 "$n"); do cp stream-a.mp4 "$tag-$i.mp4"; cmp stream-a.mp4 "$tag-$i.mp4"; done
 system_time > "$tag.start"
 /boot/system/apps/MediaPlayer "$PWD/$tag-1.mp4" > "$tag.stdout" 2> "$tag.stderr" &
 pid=$!
 sleep 2
 hey "$app" do Stop of Window 0
 for i in $(seq 2 "$n"); do
  open "$app" "$PWD/$tag-$i.mp4"
  sleep 1
  currentCount=$(hey -o "$app" count Window)
  k=0
  found=0
  while test "$k" -lt "$currentCount"; do
   currentTitle=$(hey -o "$app" get Title of Window "$k" 2>/dev/null || true)
   if test "$currentTitle" = "$tag-$i.mp4"; then
    hey "$app" do Stop of Window "$k"
    found=1
    break
   fi
   k=$((k+1))
  done
  test "$found" = 1
 done
 sleep 1
 count=$(hey -o "$app" count Window)
 test "$count" -le 64
 i=0
 : > "$tag.windows"
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
  for ext in stdout stderr; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
  exit 6
 fi
 {
 while read j i; do
  x=$((10+((j-1)%4)*310)); y=$((35+((j-1)/4)*185))
  hey "$app" set Frame of Window "$i" to "BRect($x,$y,$((x+300)),$((y+180)))"
  hey "$app" do Stop of Window "$i"
 done < "$tag.windows"
 # A fresh probe per workload, independent of shell startup per query.
 while read j i; do printf '%s %s\n' "$i" "$tag-$j.mp4"; done < "$tag.windows" > "$tag.map"
 system_time > "$tag.dispatch"
 while read j i; do hey "$app" do Play of Window "$i"; done < "$tag.windows"
 system_time > "$tag.play"
 sleep 2
 # Dedicated sampling campaign: query and queue sampling overlap.
 # Capture team IDs and exact monotonic boundaries for every snapshot.
 printf '%s %s\n' "$server_team" "$pid" > "$tag.teams"
 (
  set -eu
  for k in $(seq 1 10); do
   f=$(printf '%s.port-%02d' "$tag" "$k")
   begin=$(system_time)
   listport "$server_team" "$pid" > "$f"
   end=$(system_time)
   printf '%s %s %s\n' "$k" "$begin" "$end" >> "$tag.ports"
   sleep .5
  done
 ) &
 sampler=$!
 probe_rc=0
 ./media-window-probe "$tag.map" 15 > "$tag.probe" 2> "$tag.probe-stderr" || probe_rc=$?
 printf '%s\n' "$probe_rc" > "$tag.probe-exit"
 wait "$sampler"
 system_time > "$tag.stop"
 for ext in teams ports; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
 for k in $(seq 1 10); do
  f=$(printf '%s.port-%02d' "$tag" "$k")
  curl -fsS -T "$f" "$base/$f"
 done
 # Upload query evidence before attempting teardown.
 for ext in dispatch play stop map probe probe-stderr probe-exit; do
  curl -fsS -T "$tag.$ext" "$base/$tag.$ext"
 done
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
 for ext in start quit-time windows positions stdout stderr exit; do curl -fsS -T "$tag.$ext" "$base/$tag.$ext"; done
 if test "$c" = 1; then rm -f "$catchup"; c=0; fi
 test "$rc" = 0
 for i in $(seq 1 "$n"); do rm -f "$tag-$i.mp4"; done
 run=$((run+1))
done
cleanup
for m in "$stats" "$preflight" "$catchup" /boot/home/config/settings/haiku-lab-media-catchup /boot/home/config/settings/haiku-lab-media-catchup-adaptive; do test ! -e "$m" && test ! -L "$m"; done
printf '0\n' > done.txt
# Copy completion marker off RAM before unmounting; use host upload only
# after successful unmount, so a complete run also verifies cleanup.
cd /boot/home
unmount "$ramdir"
# A regular file supplies Content-Length; stdin PUT uses chunked encoding.
(set -C; printf '0\n' > "$ramdir/done.txt")
curl -fsS -T "$ramdir/done.txt" "$base/done.txt"
