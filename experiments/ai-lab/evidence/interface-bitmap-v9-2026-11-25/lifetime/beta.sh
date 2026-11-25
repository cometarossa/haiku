#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-v9-lab
cd bitmap-v9-lab
curl -fsS http://10.0.2.2:8899/bitmap.cpp -o bitmap.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o bitmap bitmap.cpp -lbe
curl -fsS -T bitmap http://10.0.2.2:8899/bitmap
uname -a > revision.txt
printf 'repeat,mode,draws,elapsed_us,checked,errors,exit
' > results.csv
: > errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='transaction direct'; else order='direct transaction'; fi
 for m in $order; do
  rc=0
  ./bitmap "$m" > one.csv 2>>errors.txt || rc=$?
  if test -s one.csv; then sed "s/^/$rep,/;s/$/,$rc/" one.csv >> results.csv; else echo "missing $rep $m rc=$rc" >> errors.txt; fi
 done
done
for f in revision.txt errors.txt results.csv; do curl -fsS -T "$f" "http://10.0.2.2:8899/beta-$f"; done
