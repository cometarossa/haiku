#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_35eca30c
curl -fsS http://10.0.2.2:8899/estimate -o estimate
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o estimate.sha256
sha256sum -c estimate.sha256
chmod +x estimate
printf 'priority,load_threads,round,estimate_us\n' > estimate.csv
for p in 5 10 15 20; do
 for n in 0 2; do
  ./estimate "$p" "$n" >> estimate.csv
 done
done
curl -fsS -T estimate.csv http://10.0.2.2:8899/v4.csv
