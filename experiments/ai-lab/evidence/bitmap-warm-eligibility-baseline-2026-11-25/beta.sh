#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-warm-eligibility-lab
cd bitmap-warm-eligibility-lab
curl -fsS http://10.0.2.2:8899/bitmap.cpp -o bitmap.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o bitmap bitmap.cpp -lbe
curl -fsS -T bitmap http://10.0.2.2:8899/bitmap
uname -a > revision.txt
printf 'mode,case,bytes,initial_bytes,pixels,errors,exit\n' > results.csv
: > errors.txt
marker=/boot/home/config/settings/haiku-lab-bitmap-warm
test ! -e "$marker" && test ! -L "$marker"
for m in lab ordinary; do
 rc=0
 ./bitmap "$m" > one.csv 2>>errors.txt || rc=$?
 if test -s one.csv; then sed "s/^/$m,/;s/$/,$rc/" one.csv >> results.csv; else echo "missing $m rc=$rc" >> errors.txt; fi
done
for f in revision.txt errors.txt results.csv; do curl -fsS -T "$f" "http://10.0.2.2:8899/beta-$f"; done
