#!/bin/sh
set -eu
cd /boot/home
printf 'mode,workers,pages,cpus,worker,cpu,create_us,touch_us,warm_us,clone_us,verify_us,delete_us,checked
' > v8row.csv
: > v8err.txt
for p in 256 1024; do
 for c in 1 4; do
  for m in threads teams; do
   if ./vmt "$m" "$p" "$c" > v8one.csv 2>>v8err.txt; then
    cat v8one.csv >> v8row.csv
   else
    echo "failed $m $p $c" >> v8err.txt
   fi
  done
 done
done
curl -fsS -T v8err.txt "http://10.0.2.2:8899/$1-errors.txt"
curl -fsS -T v8row.csv "http://10.0.2.2:8899/$1.csv"
