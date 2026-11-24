#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/vmw.cpp -o vmw.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o vmw vmw.cpp -lbe
curl -fsS -T vmw http://10.0.2.2:8899/vmw
printf 'repeat,cpus,pages,mode,worker,cpu,create_us,first_us,second_us,verify_us,delete_us,checked
' > vmw.csv
: > vmw-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='full demand'; else modes='demand full'; fi
 for p in 64 256 1024; do
  for c in 1 4; do
   for m in $modes; do
    if ./vmw "$c" "$p" "$m" > one-vmw.csv 2>> vmw-errors.txt; then
     sed "s/^/$rep,/" one-vmw.csv >> vmw.csv
    else
     echo "failed rep=$rep cpus=$c pages=$p mode=$m" >> vmw-errors.txt
    fi
   done
  done
 done
done
curl -fsS -T vmw-errors.txt http://10.0.2.2:8899/beta-errors.txt
curl -fsS -T vmw.csv http://10.0.2.2:8899/beta.csv
