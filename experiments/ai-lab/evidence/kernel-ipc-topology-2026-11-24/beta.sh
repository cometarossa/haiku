#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/topology.cpp -o topology.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o topology topology.cpp -lbe
curl -fsS -T topology http://10.0.2.2:8899/topology
printf 'mode,pairs,ports,verified,joined,errors,elapsed_us\n' > topology.csv
for order in 'shared independent' 'independent shared' 'shared independent'; do
 for mode in $order; do
  ./topology "$mode" >> topology.csv
 done
done
cat topology.csv
curl -fsS -T topology.csv http://10.0.2.2:8899/beta.csv
