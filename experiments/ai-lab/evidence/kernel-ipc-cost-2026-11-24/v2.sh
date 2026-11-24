#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_d800dd54
curl -fsS http://10.0.2.2:8899/cost -o cost
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o cost.sha256
sha256sum -c cost.sha256
chmod +x cost
./cost > cost.csv
cat cost.csv
curl -fsS -T cost.csv http://10.0.2.2:8899/v2.csv
