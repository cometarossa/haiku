#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_d800dd54
for f in sweep copyerr; do curl -fsS http://10.0.2.2:8899/$f -o "$f"; chmod +x "$f"; done
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o sweep.sha256
sha256sum -c sweep.sha256
./copyerr > copyerr.csv || test "$?" = 1
cat copyerr.csv
curl -fsS -T copyerr.csv http://10.0.2.2:8899/v2-copyerr.csv
for c in 16 64 256; do
 for n in 4 8; do
  ./sweep "$n" "$c" > sweep.csv
  cat sweep.csv
  curl -fsS -T sweep.csv http://10.0.2.2:8899/v2-$c-$n.csv
 done
done
echo SWEEP_V2_DONE
