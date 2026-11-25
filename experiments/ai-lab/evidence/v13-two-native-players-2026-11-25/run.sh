#!/bin/sh
set -eu
cd /boot/home
app=application/x-vnd.Haiku-MediaPlayer
test "$(hey -o "$app" get Title of Window 3)" = stream-a.mp4
test "$(hey -o "$app" get Title of Window 5)" = stream-b.mp4
{
 hey "$app" set Frame of Window 3 to 'BRect(650,80,1000,370)'
 hey "$app" set Frame of Window 5 to 'BRect(650,420,1000,710)'
 hey "$app" do Stop of Window 3
 hey "$app" do Stop of Window 5
 hey "$app" do Play of Window 3
 hey "$app" do Play of Window 5
 for n in 1 2 3 4; do
  echo "SAMPLE $n"
  for i in 3 5; do
   echo "WINDOW $i"
   hey -o "$app" get Title of Window "$i"
   hey -o "$app" get IsPlaying of Window "$i"
   hey "$app" get Position of Window "$i"
  done
  sleep 1
 done
} > two-player.txt 2>&1
curl -fsS -T two-player.txt http://10.0.2.2:8901/two-player.txt
