#!/bin/sh
set -eu
cd /boot/home/concurrent-gui
app=application/x-vnd.Haiku-MediaPlayer
for n in 1 2 3 4; do
 cp stream-a.mp4 "lab-dynamic-$n.mp4"
 cmp stream-a.mp4 "lab-dynamic-$n.mp4"
 open "$app" "/boot/home/concurrent-gui/lab-dynamic-$n.mp4"
 sleep 1
done
test ! -e lab-four-windows.txt
count=$(hey -o "$app" count Window)
test "$count" -le 40
{
 for n in 1 2 3 4; do
  found=''
  i=0
  while test "$i" -lt "$count"; do
   title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
   if test "$title" = "lab-dynamic-$n.mp4"; then
    test -z "$found"
    found=$i
   fi
   i=$((i+1))
  done
  test -n "$found"
  echo "$n $found" >> /boot/home/concurrent-gui/lab-four-windows.txt
  case "$n" in
   1) rect='BRect(10,80,340,360)';;
   2) rect='BRect(360,80,690,360)';;
   3) rect='BRect(710,80,1040,360)';;
   4) rect='BRect(710,420,1040,700)';;
  esac
  hey "$app" set Frame of Window "$found" to "$rect"
  hey "$app" do Stop of Window "$found"
 done
 while read n i; do hey "$app" do Play of Window "$i"; done < lab-four-windows.txt
 for sample in 1 2 3 4; do
  echo "SAMPLE $sample"
  while read n i; do
   echo "WINDOW $i"
   hey -o "$app" get Title of Window "$i"
   hey -o "$app" get IsPlaying of Window "$i"
   hey "$app" get Position of Window "$i"
  done < lab-four-windows.txt
  sleep 1
 done
} > four-player.txt 2>&1
curl -fsS -T four-player.txt http://10.0.2.2:8901/four-player.txt
curl -fsS -T lab-four-windows.txt http://10.0.2.2:8901/lab-four-windows.txt
