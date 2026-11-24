#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/handoff.cpp -o handoff.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o handoff handoff.cpp -lbe
curl -fsS -T handoff http://10.0.2.2:8899/handoff
printf 'repeat,mode,round,rtt_us\n' > handoff.csv
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='port sem'; else modes='sem port'; fi
 for mode in $modes; do
  ./handoff "$mode" > one.csv
  sed "s/^/$rep,/" one.csv >> handoff.csv
 done
done
wc -l handoff.csv
curl -fsS -T handoff.csv http://10.0.2.2:8899/beta.csv
