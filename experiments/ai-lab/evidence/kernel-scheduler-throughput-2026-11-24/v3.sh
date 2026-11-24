#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_7d5672a7
curl -fsS http://10.0.2.2:8899/fair -o fair
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o fair.sha256
sha256sum -c fair.sha256
chmod +x fair
printf 'repeat,cpus,worker,cpu,batches,digest,start_offset_us,end_offset_us\n' > fair.csv
: > fair-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then placements='4 1'; else placements='1 4'; fi
 for n in $placements; do
  if ./fair "$n" > one-fair.csv 2>> fair-errors.txt; then
   sed "s/^/$rep,/" one-fair.csv >> fair.csv
  else
   echo "failed rep=$rep cpus=$n" >> fair-errors.txt
  fi
 done
done
cat fair.csv
cat fair-errors.txt
curl -fsS -T fair-errors.txt http://10.0.2.2:8899/v3-errors.txt
curl -fsS -T fair.csv http://10.0.2.2:8899/v3.csv
