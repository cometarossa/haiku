#!/bin/sh
set -eu
cd /boot/home
curl -fsS -T vma.csv http://10.0.2.2:8899/initial-partial.csv
curl -fsS http://10.0.2.2:8899/vma.cpp -o vma.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o vma vma.cpp -lbe
curl -fsS -T vma http://10.0.2.2:8899/vma
printf 'repeat,workers,pages,worker,create_us,touch_us,clone_us,verify_us,delete_alias_us,checked
' > vma.csv
: > vma-errors.txt
for rep in 1 2 3; do
 for n in 1 4; do
  if test "$n" = 1; then sizes='64 256 1024 8192'; else sizes='64 256 1024'; fi
  for p in $sizes; do
   if ./vma "$n" "$p" > one-vma.csv 2>> vma-errors.txt; then
    sed "s/^/$rep,/" one-vma.csv >> vma.csv
   else
    echo "failed rep=$rep workers=$n pages=$p" >> vma-errors.txt
   fi
  done
 done
done
curl -fsS -T vma-errors.txt http://10.0.2.2:8899/beta-errors.txt
curl -fsS -T vma.csv http://10.0.2.2:8899/beta.csv
