#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_d800dd54
curl -fsS http://10.0.2.2:8899/topology -o topology
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o topology.sha256
sha256sum -c topology.sha256
chmod +x topology
printf 'mode,pairs,ports,verified,joined,errors,elapsed_us\n' > topology.csv
for order in 'shared independent' 'independent shared' 'shared independent'; do
 for mode in $order; do
  ./topology "$mode" >> topology.csv
 done
done
cat topology.csv
curl -fsS -T topology.csv http://10.0.2.2:8899/v2.csv
