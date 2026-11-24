#!/bin/sh
set -eu
cd /boot/home
uname -a > aff-uname.txt
grep ai_7d5672a7 aff-uname.txt
curl -fsS -T aff-uname.txt http://10.0.2.2:8899/uname.txt
curl -fsS http://10.0.2.2:8899/aff -o aff
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o aff.sha256
sha256sum -c aff.sha256
chmod +x aff
printf 'repeat,mode,placement,round,rtt_us\n' > aff.csv
for rep in 1 2 3; do
 for mode in sem port; do
  for placement in same split; do
   ./aff "$mode" "$placement" > one-aff.csv
   sed "s/^/$rep,/" one-aff.csv >> aff.csv
  done
 done
done
wc -l aff.csv
curl -fsS -T aff.csv http://10.0.2.2:8899/v3.csv
