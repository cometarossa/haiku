#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/topology -o topology-repro
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o topology.sha256
mkdir -p topology-lab
cp topology-repro topology-lab/topology
cd topology-lab
cp ../topology.sha256 SHA256SUMS
sha256sum -c SHA256SUMS
chmod +x topology
uname -a > revision.txt
printf 'repeat,mode,pairs,ports,verified,joined,errors,elapsed_us,exit
' > results.csv
: > errors.txt
for rep in 1 2 3 4 5 6 7 8 9 10; do
 for m in shared independent; do
  rc=0
  ./topology "$m" > one.csv 2>>errors.txt || rc=$?
  if test -s one.csv; then
   sed "s/^/$rep,/;s/$/,$rc/" one.csv >> results.csv
  else
   echo "missing row rep=$rep mode=$m rc=$rc" >> errors.txt
  fi
 done
done
for f in revision.txt results.csv errors.txt; do curl -fsS -T "$f" "http://10.0.2.2:8899/$1-$f"; done
