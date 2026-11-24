#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/estimate.cpp -o estimate.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o estimate estimate.cpp -lbe
curl -fsS -T estimate http://10.0.2.2:8899/estimate
printf 'priority,load_threads,round,estimate_us\n' > estimate.csv
for p in 5 10 15 20; do
 for n in 0 2; do
  ./estimate "$p" "$n" >> estimate.csv
 done
done
curl -fsS -T estimate.csv http://10.0.2.2:8899/beta.csv
