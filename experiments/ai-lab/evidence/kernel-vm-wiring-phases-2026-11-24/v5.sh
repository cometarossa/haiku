#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_8f8e7d06
curl -fsS http://10.0.2.2:8899/vmw -o vmw
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmw.sha256
sha256sum -c vmw.sha256
chmod +x vmw
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
curl -fsS -T vmw-errors.txt http://10.0.2.2:8899/v5-errors.txt
curl -fsS -T vmw.csv http://10.0.2.2:8899/v5.csv
