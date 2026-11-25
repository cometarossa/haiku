#!/bin/sh
set -eu
cd /boot/home
mkdir -p drawing-prefault-lab
cd drawing-prefault-lab
for f in bitmap SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x bitmap
uname -a > revision.txt
test ! -e /boot/home/config/settings/haiku-lab-appserver-profile
printf 'repeat,warm,mode,workers,batch,worker,draws,start_us,end_us,makespan_us,checked,errors,warm_us,first_us,exit\n' > results.csv
: > errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='server client cold'; else order='cold client server'; fi
 for m in threads teams; do
  for w in $order; do
   rc=0
   ./bitmap "$m" 4 64 "$w" > one.csv 2>>errors.txt || rc=$?
   if test -s one.csv; then sed "s/^/$rep,$w,/;s/$/,$rc/" one.csv >> results.csv; else echo "missing $rep $m $w rc=$rc" >> errors.txt; fi
  done
 done
done
for f in revision.txt errors.txt results.csv; do curl -fsS -T "$f" "http://10.0.2.2:8899/v10-$f"; done
