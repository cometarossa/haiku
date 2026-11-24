#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_8f8e7d06
curl -fsS http://10.0.2.2:8899/vmt -o vmt
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmt.sha256
sha256sum -c vmt.sha256
chmod +x vmt
printf 'repeat,mode,workers,pages,cpus,worker,cpu,create_us,touch_us,warm_us,clone_us,verify_us,delete_alias_us,checked
' > vmt.csv
: > vmt-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='teams threads'; else modes='threads teams'; fi
 for p in 64 256 1024; do
  for c in 1 4; do
   for m in $modes; do
    if ./vmt "$m" "$p" "$c" > one-vmt.csv 2>> vmt-errors.txt; then
     sed "s/^/$rep,/" one-vmt.csv >> vmt.csv
    else
     echo "failed rep=$rep mode=$m cpus=$c pages=$p" >> vmt-errors.txt
    fi
   done
  done
 done
done
curl -fsS -T vmt-errors.txt http://10.0.2.2:8899/v5-errors.txt
curl -fsS -T vmt.csv http://10.0.2.2:8899/v5.csv
