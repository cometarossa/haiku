#!/bin/sh
set -eu
cd /boot/home
mkdir -p drawing-lab
cd drawing-lab
for f in drawing topdiag SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x drawing topdiag
uname -a > revision.txt
printf 'repeat,batch,commands,syncs,elapsed_us,checked,errors,exit\n' > draw.csv
: > draw-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='2048 64 1'; else order='1 64 2048'; fi
 for b in $order; do
  rc=0
  ./drawing "$b" > one.csv 2>>draw-errors.txt || rc=$?
  if test -s one.csv; then sed "s/^/$rep,/;s/$/,$rc/" one.csv >> draw.csv; else echo "missing $rep $b rc=$rc" >> draw-errors.txt; fi
 done
done
printf 'mode,pairs,ports,verified,joined,errors,elapsed_us,exit\n' > topo.csv
: > topo-detail.txt
for m in shared independent; do
 rc=0
 ./topdiag "$m" > one.csv 2>>topo-detail.txt || rc=$?
 if test -s one.csv; then sed "s/$/,$rc/" one.csv >> topo.csv; else echo "missing $m rc=$rc" >> topo-detail.txt; fi
done
for f in revision.txt draw.csv draw-errors.txt topo.csv topo-detail.txt; do curl -fsS -T "$f" "http://10.0.2.2:8899/v5-$f"; done
