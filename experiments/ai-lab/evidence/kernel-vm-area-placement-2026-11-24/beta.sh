#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/vmp.cpp -o vmp.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o vmp vmp.cpp -lbe
curl -fsS -T vmp http://10.0.2.2:8899/vmp
printf 'repeat,workers,pages,cpus,worker,cpu,create_us,touch_us,warm_us,clone_us,verify_us,delete_alias_us,checked
' > vmp.csv
: > vmp-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then placements='4 1'; else placements='1 4'; fi
 for p in 64 256 1024; do
  for c in $placements; do
   if ./vmp 4 "$p" "$c" > one-vmp.csv 2>> vmp-errors.txt; then
    sed "s/^/$rep,/" one-vmp.csv >> vmp.csv
   else
    echo "failed rep=$rep cpus=$c pages=$p" >> vmp-errors.txt
   fi
  done
 done
done
curl -fsS -T vmp-errors.txt http://10.0.2.2:8899/beta-errors.txt
curl -fsS -T vmp.csv http://10.0.2.2:8899/beta.csv
