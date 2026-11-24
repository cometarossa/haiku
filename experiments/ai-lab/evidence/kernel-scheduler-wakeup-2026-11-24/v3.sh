#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_7d5672a7
curl -fsS http://10.0.2.2:8899/wake -o wake
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o wake.sha256
sha256sum -c wake.sha256
chmod +x wake
printf 'repeat,scheduler_mode,priority,load_threads,round,lateness_us\n' > wake.csv
for rep in 1 2 3; do
 if test "$rep" = 2; then priorities='15 10'; else priorities='10 15'; fi
 for p in $priorities; do
  for n in 0 2; do
   ./wake "$p" "$n" > one-wake.csv
   sed "s/^/$rep,/" one-wake.csv >> wake.csv
  done
 done
done
wc -l wake.csv
curl -fsS -T wake.csv http://10.0.2.2:8899/v3.csv
