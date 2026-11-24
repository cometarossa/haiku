#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/vmf.cpp -o vmf.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o vmf vmf.cpp -lbe
curl -fsS -T vmf http://10.0.2.2:8899/vmf
printf 'repeat,cpus,pages,mode,worker,cpu,create_us,first_us,second_us,verify_us,delete_us,checked
' > vmf.csv
: > vmf-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='write read'; else modes='read write'; fi
 for p in 64 256 1024; do
  for c in 1 4; do
   for m in $modes; do
    if ./vmf "$c" "$p" "$m" > one-vmf.csv 2>> vmf-errors.txt; then
     sed "s/^/$rep,/" one-vmf.csv >> vmf.csv
    else
     echo "failed rep=$rep cpus=$c pages=$p mode=$m" >> vmf-errors.txt
    fi
   done
  done
 done
done
curl -fsS -T vmf-errors.txt http://10.0.2.2:8899/beta-errors.txt
curl -fsS -T vmf.csv http://10.0.2.2:8899/beta.csv
