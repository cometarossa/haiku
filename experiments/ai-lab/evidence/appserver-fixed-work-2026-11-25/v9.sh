#!/bin/sh
set -eu
cd /boot/home
mkdir -p drawing-fixed-work-lab
cd drawing-fixed-work-lab
for f in bitmap SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x bitmap
uname -a > revision.txt
printf 'repeat,mode,workers,batch,worker,draws,start_us,end_us,makespan_us,checked,errors,exit\n' > results.csv
: > errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='4 2 1'; else order='1 2 4'; fi
 for n in $order; do
  for m in threads teams; do
  for b in 1 64 1024; do
   rc=0
   ./bitmap "$m" "$n" "$b" > one.csv 2>>errors.txt || rc=$?
   if test -s one.csv; then sed "s/^/$rep,/;s/$/,$rc/" one.csv >> results.csv; else echo "missing $rep $m $n $b rc=$rc" >> errors.txt; fi
  done
  done
 done
done
for f in revision.txt errors.txt results.csv; do curl -fsS -T "$f" "http://10.0.2.2:8899/v9-$f"; done
