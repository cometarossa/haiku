#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/aff.cpp -o aff.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o aff aff.cpp -lbe
curl -fsS -T aff http://10.0.2.2:8899/aff
printf 'repeat,mode,placement,round,rtt_us\n' > aff.csv
for rep in 1 2 3; do
 for mode in sem port; do
  for placement in same split; do
   ./aff "$mode" "$placement" > one-aff.csv
   sed "s/^/$rep,/" one-aff.csv >> aff.csv
  done
 done
done
wc -l aff.csv
curl -fsS -T aff.csv http://10.0.2.2:8899/beta.csv
