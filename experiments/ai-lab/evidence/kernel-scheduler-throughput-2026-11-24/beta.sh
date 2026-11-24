#!/bin/sh
set -eu
cd /boot/home
curl -fsS -T fair.csv http://10.0.2.2:8899/initial-partial.csv
curl -fsS http://10.0.2.2:8899/fair.cpp -o fair.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o fair fair.cpp -lbe
curl -fsS -T fair http://10.0.2.2:8899/fair
printf 'repeat,cpus,worker,cpu,batches,digest,start_offset_us,end_offset_us\n' > fair.csv
: > fair-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then placements='4 1'; else placements='1 4'; fi
 for n in $placements; do
  if ./fair "$n" > one-fair.csv 2>> fair-errors.txt; then
   sed "s/^/$rep,/" one-fair.csv >> fair.csv
  else
   echo "failed rep=$rep cpus=$n" >> fair-errors.txt
  fi
 done
done
cat fair.csv
cat fair-errors.txt
curl -fsS -T fair-errors.txt http://10.0.2.2:8899/beta-errors.txt
curl -fsS -T fair.csv http://10.0.2.2:8899/beta.csv
