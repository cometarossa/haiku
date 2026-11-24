#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_8f8e7d06
curl -fsS http://10.0.2.2:8899/vmf -o vmf
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmf.sha256
sha256sum -c vmf.sha256
chmod +x vmf
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
curl -fsS -T vmf-errors.txt http://10.0.2.2:8899/v5-errors.txt
curl -fsS -T vmf.csv http://10.0.2.2:8899/v5.csv
