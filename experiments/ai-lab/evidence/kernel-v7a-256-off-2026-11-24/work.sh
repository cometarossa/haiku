#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_93d9c2d1
sha256sum -c vmt.sha256
printf 'repeat,mode,workers,pages,cpus,worker,cpu,create_us,touch_us,warm_us,clone_us,verify_us,delete_us,checked
' > v7small.csv
: > v7small-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='teams threads'; placements='4 1'; else modes='threads teams'; placements='1 4'; fi
 for c in $placements; do
  for m in $modes; do
   if ./vmt "$m" 256 "$c" > one-v7small.csv 2>>v7small-errors.txt; then
    sed "s/^/$rep,/" one-v7small.csv >> v7small.csv
   else
    echo "failed rep=$rep mode=$m cpus=$c" >> v7small-errors.txt
   fi
  done
 done
done
curl -fsS -T v7small-errors.txt http://10.0.2.2:8899/errors.txt
curl -fsS -T v7small.csv http://10.0.2.2:8899/results.csv
