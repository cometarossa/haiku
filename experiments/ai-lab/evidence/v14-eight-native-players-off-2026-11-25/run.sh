#!/bin/sh
set -eu
cd /boot/home
mkdir v14-eight-player-off
cd v14-eight-player-off
test ! -e /boot/home/config/settings/haiku-lab-media-overlay-preflight
curl -fsS http://10.0.2.2:8901/stream-a.mp4 -o stream-a.mp4
curl -fsS http://10.0.2.2:8901/SHA256SUMS -o SHA256SUMS
sha256sum -c SHA256SUMS
uname -a > revision.txt
app=application/x-vnd.Haiku-MediaPlayer
for n in 1 2 3 4 5 6 7 8; do
 cp stream-a.mp4 "lab-eight-$n.mp4"
 cmp stream-a.mp4 "lab-eight-$n.mp4"
 open "$app" "/boot/home/v14-eight-player-off/lab-eight-$n.mp4"
 sleep 1
done
count=$(hey -o "$app" count Window)
test "$count" -le 40
{
 for n in 1 2 3 4 5 6 7 8; do
  found=''
  i=0
  while test "$i" -lt "$count"; do
   title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
   if test "$title" = "lab-eight-$n.mp4"; then
    test -z "$found"
    found=$i
   fi
   i=$((i+1))
  done
  test -n "$found"
  echo "$n $found" >> windows.txt
  x=$((10+((n-1)%4)*310))
  y=$((80+((n-1)/4)*340))
  hey "$app" set Frame of Window "$found" to "BRect($x,$y,$((x+300)),$((y+280)))"
  hey "$app" do Stop of Window "$found"
 done
 while read n i; do hey "$app" do Play of Window "$i"; done < windows.txt
 for sample in 1 2 3 4; do
  echo "SAMPLE $sample"
  while read n i; do
   echo "WINDOW $i"
   hey -o "$app" get Title of Window "$i"
   hey -o "$app" get IsPlaying of Window "$i"
   hey "$app" get Position of Window "$i"
  done < windows.txt
  sleep 1
 done
} > eight-player.txt 2>&1
for f in revision.txt windows.txt eight-player.txt; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
