#!/bin/sh
set -eu
cd /boot/home
mkdir -p drawing-white-lifecycle-lab
cd drawing-white-lifecycle-lab
for f in bitmap SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x bitmap
uname -a > revision.txt
test ! -e /boot/home/config/settings/haiku-lab-bitmap-warm
printf 'repeat,mode,workers,batch,worker,draws,start_us,end_us,makespan_us,checked,errors,setup_us,lifecycle_us,white_errors,exit\n' > results.csv
: > errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='4 2 1'; else order='1 2 4'; fi
 for m in threads teams; do
  for n in $order; do
   rc=0
   ./bitmap "$m" "$n" 64 > one.csv 2>>errors.txt || rc=$?
   if test -s one.csv; then sed "s/^/$rep,/;s/$/,$rc/" one.csv >> results.csv; else echo "missing $rep $m $n rc=$rc" >> errors.txt; fi
  done
 done
done
for f in revision.txt errors.txt results.csv; do curl -fsS -T "$f" "http://10.0.2.2:8899/v10-$f"; done
